# F2 — Grafo documental anclado e hilos por percolacion temporal (HEBRA).
# Determinista. Solo lectura de capas canonicas; escribe en outputs/.
#
# Parametros preinscritos (ver FABLE5_INDEPENDENT_PROPOSAL_2026_07_22.md §7.2):
#   pesos referente: objeto 0.5, territorio 0.3, actores 0.2 (Jaccard c/u)
#   w = ALPHA*s_ref + BETA*s_emb, ALPHA=0.7 > BETA=0.3
#   ventana corta DELTA1=365 dias con w >= tau
#   ventana larga DELTA2=1095 dias solo si s_ref >= SREF_STRONG=0.5
#   grid preinscrito tau in {0.35, 0.45, 0.55}
#   regla de seleccion estructural (sin mirar casos conocidos):
#     el menor tau cuyo componente gigante <= 30% de los documentos con fecha.
#   arista solo hacia el pasado (j se enlaza a i si fecha_i < fecha_j).

import csv
import hashlib
import json
import math
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

# Variante F2b (--idf): Jaccard ponderado por IDF dentro de cada tipo, para
# que referentes ubicuos (reguladores como SMA/SEA) no fabriquen continuidad
# entre conflictos distintos. Registrada como variante; F2 base se conserva.
USE_IDF = "--idf" in sys.argv
SUFFIX = "b_idf" if USE_IDF else ""
# --refs <archivo en outputs/> permite correr sobre F1v2 sin tocar salidas v1.
REFS_NAME = "f1_referents.csv"
if "--refs" in sys.argv:
    REFS_NAME = sys.argv[sys.argv.index("--refs") + 1]
if "--tag" in sys.argv:
    SUFFIX += "_" + sys.argv[sys.argv.index("--tag") + 1]

# Tier de enlaces largos (365 < dt <= 1095), decision central del modelo:
#   L1: s_ref >= SREF_STRONG basta (regla original; "reactivacion anclada").
#   L2: s_ref >= SREF_STRONG y ademas w >= tau.
#   L3: s_ref >= 0.6 y w >= tau (solo sensibilidad predefinida).
LONG_TIER = "L1"
if "--tier" in sys.argv:
    LONG_TIER = sys.argv[sys.argv.index("--tier") + 1]
    assert LONG_TIER in ("L1", "L2", "L3"), LONG_TIER
    SUFFIX += "_" + LONG_TIER
L3_SREF = 0.6


def long_edge_ok(s_ref: float, w: float, tau: float) -> bool:
    if LONG_TIER == "L1":
        return True  # scored ya exige s_ref >= SREF_STRONG
    if LONG_TIER == "L2":
        return w >= tau
    return s_ref >= L3_SREF and w >= tau

ROOT = Path(__file__).resolve().parents[4].parent
CORPUS = ROOT / "01_bases_de_datos/03_refiltro_api_qwen_y_base_actual/06_base_actual_fusionada_3742_incluidas.csv"
EMB = ROOT / "04_embeddings/01_embeddings_canonicos/active_corpus_embeddings_3742.npz"
FAMILIES = ROOT / "09_metodologia/faro_model_research/promoted_family_assignments.csv"
OUT_DIR = Path(__file__).resolve().parents[1] / "outputs"
REFS = OUT_DIR / REFS_NAME

ALPHA, BETA = 0.7, 0.3
# Ablaciones F4-D preinscritas: --alpha/--beta (solo referentes: 1.0/0.0);
# --no-long (DELTA2=365); --dump-scored (todos los pares puntuados, para
# estabilidad exacta drop/jitter sin re-puntuar).
if "--alpha" in sys.argv:
    ALPHA = float(sys.argv[sys.argv.index("--alpha") + 1])
if "--beta" in sys.argv:
    BETA = float(sys.argv[sys.argv.index("--beta") + 1])
W_REF = {"objeto": 0.5, "territorio": 0.3, "actor": 0.2}
DELTA1, DELTA2 = 365, 1095
if "--no-long" in sys.argv:
    DELTA2 = 365
SREF_STRONG = 0.5
TAU_GRID = [0.35, 0.45, 0.55]
GIANT_MAX_SHARE = 0.30
MAX_REFERENT_DF = 400  # referentes en mas docs no generan pares (hubs; log)


IDF = {}  # (tipo, referente) -> peso normalizado idf(r)/idf_ref; ver abajo.
# F2b no usa razon tipo Jaccard: cualquier razon vale 1.0 cuando ambos docs
# comparten exactamente el mismo referente ubicuo (p. ej. actores == {sma}).
# En su lugar, fuerza de ancla absoluta: s_t = min(1, sum_{r in inter} w_r),
# con w_r = min(1, idf(r) / idf_ref), idf(r) = ln(N/df(r)), idf_ref = ln(N/5):
# un referente con df<=5 ancla con peso 1; un regulador con df~130 ancla ~0.5.


def jacc(t: str, a: frozenset, b: frozenset) -> float:
    if not a or not b:
        return 0.0
    inter = a & b
    if not inter:
        return 0.0
    if not USE_IDF:
        return len(inter) / len(a | b)
    return min(1.0, sum(IDF.get((t, r), 0.0) for r in inter))


class DSU:
    def __init__(self, n: int):
        self.p = list(range(n))

    def find(self, x: int) -> int:
        while self.p[x] != x:
            self.p[x] = self.p[self.p[x]]
            x = self.p[x]
        return x

    def union(self, a: int, b: int) -> None:
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.p[rb] = ra


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # Corpus: ids en orden canonico (= orden de filas del npz) y fechas.
    doc_ids, dates = [], []
    with open(CORPUS, encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            doc_ids.append(row["id"])
            d = (row.get("fecha_iso") or "")[:10]
            try:
                dates.append(datetime.strptime(d, "%Y-%m-%d").date())
            except ValueError:
                dates.append(None)
    n = len(doc_ids)
    idx_of = {d: i for i, d in enumerate(doc_ids)}
    day = [None if d is None else d.toordinal() for d in dates]

    emb = np.load(EMB)["arr_0"].astype(np.float32)
    assert emb.shape == (n, 1024), emb.shape
    emb /= np.linalg.norm(emb, axis=1, keepdims=True)

    # Referentes F1.
    refs = {t: defaultdict(frozenset) for t in W_REF}
    tmp = {t: defaultdict(set) for t in W_REF}
    with open(REFS, encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            i = idx_of.get(row["doc_id"])
            if i is not None:
                tmp[row["tipo"]][i].add(row["referente"])
    for t in W_REF:
        refs[t] = {i: frozenset(s) for i, s in tmp[t].items()}

    # Indice invertido -> pares candidatos (referentes con df <= MAX_REFERENT_DF).
    inv = defaultdict(list)
    for t in W_REF:
        for i, s in refs[t].items():
            for r in s:
                inv[(t, r)].append(i)
    hubs = [
        {"tipo": t, "referente": r, "df": len(ds)}
        for (t, r), ds in inv.items() if len(ds) > MAX_REFERENT_DF
    ]
    if USE_IDF:
        n_dated = sum(1 for d in day if d is not None)
        idf_ref = math.log(n_dated / 5)
        for (t, r), ds in inv.items():
            IDF[(t, r)] = min(1.0, math.log(n_dated / len(ds)) / idf_ref)
    pairs = set()
    for (t, r), ds in inv.items():
        if len(ds) > MAX_REFERENT_DF:
            continue
        ds = sorted(ds)
        for ii in range(len(ds)):
            for jj in range(ii + 1, len(ds)):
                pairs.add((ds[ii], ds[jj]))
    pairs = sorted(pairs)

    # Puntuar pares una sola vez (s_ref, s_emb, dias) — independiente de tau.
    scored = []
    for i, j in pairs:
        if day[i] is None or day[j] is None:
            continue
        dt = abs(day[i] - day[j])
        if dt == 0 or dt > DELTA2:
            continue
        s_ref = sum(
            W_REF[t] * jacc(t, refs[t].get(i, frozenset()), refs[t].get(j, frozenset()))
            for t in W_REF
        )
        if s_ref <= 0.0:
            continue
        if dt > DELTA1 and s_ref < SREF_STRONG:
            continue
        s_emb = float(emb[i] @ emb[j])
        scored.append((i, j, dt, s_ref, s_emb, ALPHA * s_ref + BETA * s_emb))

    dated_docs = sum(1 for d in day if d is not None)

    # Familias (covariable, no identidad).
    fam = {}
    with open(FAMILIES, encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            fam[row["id"]] = row.get("family_topic", "")

    def build(tau: float):
        dsu = DSU(n)
        edges = 0
        long_edges = 0
        for i, j, dt, s_ref, s_emb, w in scored:
            ok = (w >= tau) if dt <= DELTA1 else long_edge_ok(s_ref, w, tau)
            if ok:
                dsu.union(i, j)
                edges += 1
                if dt > DELTA1:
                    long_edges += 1
        comp = defaultdict(list)
        for i in range(n):
            if day[i] is None:
                continue
            comp[dsu.find(i)].append(i)
        threads = [sorted(m, key=lambda x: day[x]) for m in comp.values()]
        threads.sort(key=len, reverse=True)
        sizes = [len(t) for t in threads]
        multi = [t for t in threads if len(t) >= 3]
        giant = sizes[0] if sizes else 0
        fams_crossed = [
            len({fam.get(doc_ids[i], "") for i in t if fam.get(doc_ids[i], "")})
            for t in multi
        ]
        spans = [(day[t[-1]] - day[t[0]]) / 365.25 for t in multi]
        return {
            "tau": tau,
            "edges": edges,
            "long_edges": long_edges,
            "threads_total": len(threads),
            "threads_ge3": len(multi),
            "docs_in_threads_ge3": sum(len(t) for t in multi),
            "coverage_ge3_pct": round(100 * sum(len(t) for t in multi) / dated_docs, 2),
            "giant_size": giant,
            "giant_share_pct": round(100 * giant / dated_docs, 2),
            "singletons": sum(1 for s in sizes if s == 1),
            "size_p50_ge3": float(np.median([len(t) for t in multi])) if multi else 0,
            "size_max": giant,
            "mean_families_crossed_ge3": round(float(np.mean(fams_crossed)), 2) if fams_crossed else 0,
            "pct_threads_ge3_multifamily": round(
                100 * sum(1 for c in fams_crossed if c >= 2) / len(fams_crossed), 1
            ) if fams_crossed else 0,
            "span_years_p50": round(float(np.median(spans)), 2) if spans else 0,
            "_threads": threads,
        }

    grid = [build(t) for t in TAU_GRID]
    chosen = next((g for g in grid if g["giant_share_pct"] <= 100 * GIANT_MAX_SHARE), None)
    rule = "menor tau con componente gigante <= 30%"
    if chosen is None:
        chosen = grid[-1]
        rule += " (ninguno cumplio; se toma el mayor tau del grid y la puerta FALLA)"

    # Materializar hilos elegidos (>=3 docs) con referentes dominantes.
    thread_rows = []
    profile = []
    for k, t in enumerate(g_t for g_t in chosen["_threads"] if len(g_t) >= 3):
        tid = f"H{k:04d}"
        rc = {typ: Counter() for typ in W_REF}
        for i in t:
            for typ in W_REF:
                for r in refs[typ].get(i, frozenset()):
                    rc[typ][r] += 1
            thread_rows.append({
                "thread_id": tid, "doc_id": doc_ids[i],
                "fecha": dates[i].isoformat(),
                "familia": fam.get(doc_ids[i], ""),
            })
        profile.append({
            "thread_id": tid, "docs": len(t),
            "desde": dates[t[0]].isoformat(), "hasta": dates[t[-1]].isoformat(),
            "top_objeto": [x for x, _ in rc["objeto"].most_common(3)],
            "top_territorio": [x for x, _ in rc["territorio"].most_common(3)],
            "top_actores": [x for x, _ in rc["actor"].most_common(3)],
            "familias": sorted({fam.get(doc_ids[i], "") for i in t if fam.get(doc_ids[i], "")}),
        })

    if "--dump-scored" in sys.argv:
        with open(OUT_DIR / f"f2{SUFFIX}_scored_pairs.csv", "w", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            w.writerow(["doc_i", "doc_j", "dias", "s_ref", "w"])
            for i, j, dt, s_ref, s_emb, wv in scored:
                w.writerow([doc_ids[i], doc_ids[j], dt, round(s_ref, 4), round(wv, 4)])

    if "--dump-edges" in sys.argv:
        with open(OUT_DIR / f"f2{SUFFIX}_edges.csv", "w", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            w.writerow(["doc_i", "doc_j", "dias", "s_ref", "s_emb", "w"])
            for i, j, dt, s_ref, s_emb, wv in scored:
                ok = (wv >= chosen["tau"]) if dt <= DELTA1 else long_edge_ok(s_ref, wv, chosen["tau"])
                if ok:
                    w.writerow([doc_ids[i], doc_ids[j], dt,
                                round(s_ref, 4), round(s_emb, 4), round(wv, 4)])

    with open(OUT_DIR / f"f2{SUFFIX}_threads.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["thread_id", "doc_id", "fecha", "familia"])
        w.writeheader()
        w.writerows(thread_rows)

    summary = {
        "schema_version": 1,
        "variant": "f2b_idf_anchor_strength" if USE_IDF else "f2_base_jaccard",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "corpus": str(CORPUS.name),
            "corpus_sha256": hashlib.sha256(CORPUS.read_bytes()).hexdigest(),
            "embeddings": str(EMB.name),
            "embeddings_sha256": hashlib.sha256(EMB.read_bytes()).hexdigest(),
            "referents": REFS_NAME,
            "referents_sha256": hashlib.sha256(REFS.read_bytes()).hexdigest(),
            "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        },
        "params": {
            "ALPHA": ALPHA, "BETA": BETA, "W_REF": W_REF,
            "DELTA1": DELTA1, "DELTA2": DELTA2, "SREF_STRONG": SREF_STRONG,
            "TAU_GRID": TAU_GRID, "GIANT_MAX_SHARE": GIANT_MAX_SHARE,
            "MAX_REFERENT_DF": MAX_REFERENT_DF,
            "LONG_TIER": LONG_TIER, "L3_SREF": L3_SREF, "USE_IDF": USE_IDF,
        },
        "dated_docs": dated_docs,
        "candidate_pairs": len(pairs),
        "scored_pairs": len(scored),
        "hub_referents_excluded": hubs,
        "grid": [{k: v for k, v in g.items() if k != "_threads"} for g in grid],
        "selection_rule": rule,
        "chosen_tau": chosen["tau"],
        "gate_f2_giant": chosen["giant_share_pct"] <= 100 * GIANT_MAX_SHARE,
        "threads_ge3_profiles_top40": profile[:40],
    }
    (OUT_DIR / f"f2{SUFFIX}_threads_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8"
    )
    print(json.dumps({
        "chosen_tau": chosen["tau"], "gate_giant": summary["gate_f2_giant"],
        "grid": summary["grid"],
    }, indent=1))


if __name__ == "__main__":
    main()
