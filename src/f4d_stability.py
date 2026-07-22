# F4-D — Estabilidad por perturbacion (HEBRA, config congelada L2).
# Exacto sin re-puntuar: los puntajes por par (s_ref, w) no dependen de la
# fecha; solo la elegibilidad temporal (dt<=365 / <=1095) depende de dt.
# Se usa el volcado completo de pares puntuados (f2b_idf_v2_L2_scored_pairs).
# Perturbaciones preinscritas:
#   D: eliminacion aleatoria del 10% de documentos, 20 replicas;
#   J: jitter de fechas +-7 dias uniformes, 20 replicas.
# Limite declarado: pares con dt real > 1095+14 nunca entran al volcado, asi
# que el jitter no puede crear pares fuera de ese margen (efecto nulo real:
# el volcado incluye todo par con dt<=1095, y el jitter mueve la frontera a
# lo sumo 14 dias; los pares con dt en (1095, 1109] que podrian entrar por
# jitter no estan observados — subestimacion marginal documentada).
# Orden de entrada: el algoritmo es determinista sobre conjuntos (DSU con
# resultado independiente del orden de union para componentes); no hay
# dependencia de orden que probar.
# Metricas por replica vs congelado: Jaccard de aristas aceptadas; acuerdo de
# pares co-hilo (docs comunes en hilos >=3); recall por hilo -> hilos fragiles.

import csv
import json
import random
from collections import defaultdict
from datetime import datetime, timezone
from itertools import combinations
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[4].parent
CORPUS = ROOT / "01_bases_de_datos/03_refiltro_api_qwen_y_base_actual/06_base_actual_fusionada_3742_incluidas.csv"
OUT_DIR = Path(__file__).resolve().parents[1] / "outputs"
SCORED = OUT_DIR / "f2b_idf_v2_L2_scored_pairs.csv"
THREADS = OUT_DIR / "f2b_idf_v2_L2_threads.csv"

TAU, SREF_STRONG, D1, D2 = 0.45, 0.5, 365, 1095
R = 20
SEED_D, SEED_J = 20260760, 20260761
FRAGILE_RECALL, FRAGILE_FRac = 0.5, 0.25


def components(edges_iter, docs=None):
    parent = {}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        for x in (a, b):
            if x not in parent:
                parent[x] = x
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    for a, b in edges_iter:
        if docs is not None and (a not in docs or b not in docs):
            continue
        union(a, b)
    comp = defaultdict(set)
    for x in parent:
        comp[find(x)].add(x)
    return [c for c in comp.values() if len(c) >= 3]


def pair_set(threads):
    ps = set()
    for c in threads:
        for p in combinations(sorted(c), 2):
            ps.add(p)
    return ps


def main() -> None:
    from datetime import date
    day = {}
    with open(CORPUS, encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            fx = (row.get("fecha_iso") or "")[:10]
            try:
                y, m, d = map(int, fx.split("-"))
                day[row["id"]] = date(y, m, d).toordinal()
            except ValueError:
                pass

    scored = []
    with open(SCORED, encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            scored.append((row["doc_i"], row["doc_j"], int(row["dias"]),
                           float(row["s_ref"]), float(row["w"])))

    def accepted(dt, s_ref, w):
        if dt <= D1:
            return w >= TAU
        if dt <= D2:
            return s_ref >= SREF_STRONG and w >= TAU
        return False

    base_edges = [(a, b) for a, b, dt, sr, w in scored if accepted(dt, sr, w)]
    base_threads = components(base_edges)
    base_pairs = pair_set(base_threads)
    base_docs = set().union(*base_threads) if base_threads else set()
    all_docs = sorted({a for a, b, *_ in scored} | {b for a, b, *_ in scored})

    frozen = defaultdict(set)
    with open(THREADS, encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            frozen[row["thread_id"]].add(row["doc_id"])

    def replica_metrics(rep_edges, kept_docs=None):
        rep_threads = components(rep_edges, kept_docs)
        rp = pair_set(rep_threads)
        # comparar sobre docs presentes en ambos lados
        common = (base_docs if kept_docs is None else base_docs & kept_docs)
        bp = {p for p in base_pairs if p[0] in common and p[1] in common}
        rp = {p for p in rp if p[0] in common and p[1] in common}
        ej = len(set(map(frozenset, rep_edges)) & set(map(frozenset, base_edges))) / max(
            1, len(set(map(frozenset, base_edges)) | set(map(frozenset, rep_edges))))
        pj = len(bp & rp) / max(1, len(bp | rp))
        # recall por hilo congelado
        rec = {}
        for t, docs in frozen.items():
            dd = docs if kept_docs is None else docs & kept_docs
            tp = {p for p in combinations(sorted(dd), 2)}
            if not tp:
                rec[t] = None
                continue
            rec[t] = len(tp & rp) / len(tp)
        return ej, pj, rec

    results = {"D": [], "J": []}
    fragile_counts = defaultdict(int)
    fragile_evals = defaultdict(int)

    rngd = random.Random(SEED_D)
    for r in range(R):
        kept = set(all_docs)
        drop = set(rngd.sample(all_docs, int(0.10 * len(all_docs))))
        kept -= drop
        edges = [(a, b) for a, b, dt, sr, w in scored
                 if accepted(dt, sr, w) and a in kept and b in kept]
        ej, pj, rec = replica_metrics(edges, kept)
        results["D"].append({"edge_jaccard": round(ej, 4), "pair_jaccard": round(pj, 4)})
        for t, v in rec.items():
            if v is not None:
                fragile_evals[t] += 1
                if v < FRAGILE_RECALL:
                    fragile_counts[t] += 1

    rngj = random.Random(SEED_J)
    for r in range(R):
        jit = {d: rngj.randint(-7, 7) for d in all_docs}
        edges = []
        for a, b, dt, sr, w in scored:
            ndt = abs((day[a] + jit[a]) - (day[b] + jit[b]))
            if ndt == 0:
                continue
            if accepted(ndt, sr, w):
                edges.append((a, b))
        ej, pj, rec = replica_metrics(edges)
        results["J"].append({"edge_jaccard": round(ej, 4), "pair_jaccard": round(pj, 4)})
        for t, v in rec.items():
            if v is not None:
                fragile_evals[t] += 1
                if v < FRAGILE_RECALL:
                    fragile_counts[t] += 1

    fragile = sorted(
        (t for t in fragile_evals
         if fragile_counts[t] / fragile_evals[t] >= FRAGILE_FRac),
        key=lambda t: -fragile_counts[t] / fragile_evals[t])

    out = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "config": {"R": R, "seed_drop": SEED_D, "seed_jitter": SEED_J,
                   "tau": TAU, "tier": "L2",
                   "fragile_def": "recall de pares <0.5 en >=25% de replicas"},
        "nota_orden": "algoritmo determinista sobre conjuntos; sin dependencia de orden de entrada",
        "limite_jitter": "pares dt en (1095,1109] no observados en el volcado; subestimacion marginal",
        "drop10": {
            "edge_jaccard_media": round(float(np.mean([x["edge_jaccard"] for x in results["D"]])), 4),
            "pair_jaccard_media": round(float(np.mean([x["pair_jaccard"] for x in results["D"]])), 4),
            "replicas": results["D"],
        },
        "jitter7": {
            "edge_jaccard_media": round(float(np.mean([x["edge_jaccard"] for x in results["J"]])), 4),
            "pair_jaccard_media": round(float(np.mean([x["pair_jaccard"] for x in results["J"]])), 4),
            "replicas": results["J"],
        },
        "hilos_fragiles": fragile,
        "n_hilos_fragiles": len(fragile),
    }
    (OUT_DIR / "f4d_stability.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({k: out[k] for k in ("drop10", "jitter7") for k2 in ()}, indent=1) if False else "")
    print("drop10 pair_jaccard:", out["drop10"]["pair_jaccard_media"],
          "| jitter7 pair_jaccard:", out["jitter7"]["pair_jaccard_media"],
          "| hilos fragiles:", out["n_hilos_fragiles"])


if __name__ == "__main__":
    main()
