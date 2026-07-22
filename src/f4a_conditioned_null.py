# F4-A — Nulo condicionado para compactacion/coherencia (HEBRA).
#
# DISENO PREINSCRITO (unica opcion principal, elegida antes de ejecutar):
# pseudo-hilos "igualados por tamano, periodo aproximado y distribucion de
# intervalos elegibles", construidos por CRECIMIENTO ALEATORIO TEMPORALMENTE
# RESTRINGIDO:
#   - semilla: doc uniforme del mismo semestre del primer doc del hilo real
#     (si <5 candidatos, mismo anno);
#   - crecimiento hasta tamano k: elegir un miembro actual al azar y agregar
#     un doc uniforme dentro de su ventana temporal: <=365 dias, o <=1095
#     con probabilidad p_long = fraccion de brechas consecutivas >365 dias
#     del hilo real (acota la elegibilidad de enlaces largos del algoritmo);
#   - sin uso de referentes ni similitud: rompe la identidad referencial;
#   - conserva no estacionariedad (muestrea del corpus real fechado).
# Fuente NO se restringe (desviacion menor registrada: restringir fuente en
# ventanas tempranas vacia el candidato; se reporta la mezcla de fuentes
# real vs nula como diagnostico, no como constraint).
#
# ESTADISTICOS PREINSCRITOS (tres, BH por familia, B=200, semilla fija):
#   duration      (cola less: compactacion ADICIONAL a la mecanica temporal)
#   coherence     media de coseno por pares de embeddings (cola greater:
#                 identidad semantica mas alla de la proximidad temporal)
#   max_gap       (cola greater: latencia bajo nulo condicionado; exploracion
#                 N2b-lite unica, sin variantes adicionales)
# Si ninguna familia da senal, se registra el negativo y duration_corta de
# F3 queda solo como sanity check (sin forzar nulos adicionales).

import csv
import hashlib
import json
import random
from bisect import bisect_left, bisect_right
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[4].parent
CORPUS = ROOT / "01_bases_de_datos/03_refiltro_api_qwen_y_base_actual/06_base_actual_fusionada_3742_incluidas.csv"
EMB = ROOT / "04_embeddings/01_embeddings_canonicos/active_corpus_embeddings_3742.npz"
OUT_DIR = Path(__file__).resolve().parents[1] / "outputs"
THREADS = OUT_DIR / "f2b_idf_v2_L2_threads.csv"

B = 200
SEED = 20260741
ALPHA_FDR = 0.05
D1, D2 = 365, 1095


def p_emp(null_vals, real, tail):
    a = np.asarray(null_vals, dtype=float)
    if tail == "greater":
        return (1 + np.sum(a >= real)) / (len(a) + 1)
    return (1 + np.sum(a <= real)) / (len(a) + 1)


def bh(pvals):
    idx = np.argsort(pvals)
    n = len(pvals)
    q = np.empty(n)
    prev = 1.0
    for rank in range(n - 1, -1, -1):
        i = idx[rank]
        val = pvals[i] * n / (rank + 1)
        prev = min(prev, val)
        q[i] = prev
    return q


def main() -> None:
    rng = random.Random(SEED)
    ids_order, fecha, fuente = [], {}, {}
    with open(CORPUS, encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            ids_order.append(row["id"])
            d = (row.get("fecha_iso") or "")[:10]
            try:
                fecha[row["id"]] = datetime.strptime(d, "%Y-%m-%d").date()
            except ValueError:
                continue
            fuente[row["id"]] = (row.get("fuente") or "desconocida").strip().lower()
    row_of = {d: k for k, d in enumerate(ids_order)}
    emb = np.load(EMB)["arr_0"].astype(np.float32)
    emb /= np.linalg.norm(emb, axis=1, keepdims=True)

    dated = sorted((fecha[i].toordinal(), i) for i in fecha)
    days_sorted = [d for d, _ in dated]
    ids_sorted = [i for _, i in dated]
    day = {i: fecha[i].toordinal() for i in fecha}
    sem_of = {i: (fecha[i].year, (fecha[i].month - 1) // 6) for i in fecha}
    by_sem = defaultdict(list)
    by_year = defaultdict(list)
    for i in fecha:
        by_sem[sem_of[i]].append(i)
        by_year[fecha[i].year].append(i)

    threads = defaultdict(list)
    with open(THREADS, encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            if row["doc_id"] in fecha:
                threads[row["thread_id"]].append(row["doc_id"])
    threads = {t: ds for t, ds in threads.items() if len(ds) >= 3}

    def window_candidates(center_day, horizon):
        lo = bisect_left(days_sorted, center_day - horizon)
        hi = bisect_right(days_sorted, center_day + horizon)
        return lo, hi

    def grow_pseudo(k, seed_pool, p_long):
        for _attempt in range(20):
            cur = [rng.choice(seed_pool)]
            cur_set = {cur[0]}
            fail = False
            while len(cur) < k:
                added = False
                for _try in range(30):
                    m = rng.choice(cur)
                    horizon = D2 if rng.random() < p_long else D1
                    lo, hi = window_candidates(day[m], horizon)
                    if hi <= lo:
                        continue
                    j = ids_sorted[rng.randrange(lo, hi)]
                    if j not in cur_set:
                        cur.append(j)
                        cur_set.add(j)
                        added = True
                        break
                if not added:
                    fail = True
                    break
            if not fail:
                return cur
        return None

    def stats(doc_list):
        dd = sorted(day[i] for i in doc_list)
        dur = dd[-1] - dd[0]
        gaps = [b - a for a, b in zip(dd, dd[1:])]
        mg = max(gaps) if gaps else 0
        rows = [row_of[i] for i in doc_list]
        E = emb[rows]
        m = len(rows)
        coh = float((E @ E.T).sum() - m) / (m * (m - 1)) if m > 1 else 1.0
        return dur, mg, coh

    real, nulls, src_mix = {}, {}, {}
    tids = sorted(threads)
    for t in tids:
        ds = threads[t]
        k = len(ds)
        dd = sorted(day[i] for i in ds)
        gaps = [b - a for a, b in zip(dd, dd[1:])]
        p_long = (sum(1 for g in gaps if g > D1) / len(gaps)) if gaps else 0.0
        first_id = min(ds, key=lambda i: day[i])
        pool = by_sem[sem_of[first_id]]
        if len(pool) < 5:
            pool = by_year[fecha[first_id].year]
        real[t] = stats(ds)
        nd, nm, nc = [], [], []
        fails = 0
        for _ in range(B):
            p = grow_pseudo(k, pool, p_long)
            if p is None:
                fails += 1
                continue
            d_, m_, c_ = stats(p)
            nd.append(d_)
            nm.append(m_)
            nc.append(c_)
        nulls[t] = {"duration": nd, "max_gap": nm, "coherence": nc, "fails": fails}
        src_real = Counter(fuente[i] for i in ds)
        src_mix[t] = {"fuentes_reales": len(src_real),
                      "top_fuente_share": round(max(src_real.values()) / k, 3)}

    fams = {"duration": "less", "coherence": "greater", "max_gap": "greater"}
    pv = defaultdict(dict)
    for fam, tail in fams.items():
        st_idx = {"duration": 0, "max_gap": 1, "coherence": 2}[fam]
        ps_ = [p_emp(nulls[t][fam], real[t][st_idx], tail) for t in tids]
        qs = bh(np.array(ps_))
        for t, p, q in zip(tids, ps_, qs):
            pv[t][fam] = {"p": round(float(p), 5), "q": round(float(q), 5),
                          "sig": bool(q <= ALPHA_FDR)}

    per_family = {f: sum(1 for t in tids if pv[t][f]["sig"]) for f in fams}
    result = {
        "schema_version": 1,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "threads": THREADS.name,
            "threads_sha256": hashlib.sha256(THREADS.read_bytes()).hexdigest(),
            "corpus_sha256": hashlib.sha256(CORPUS.read_bytes()).hexdigest(),
            "embeddings_sha256": hashlib.sha256(EMB.read_bytes()).hexdigest(),
            "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        },
        "config": {"B": B, "seed": SEED, "alpha_fdr": ALPHA_FDR,
                   "design": "crecimiento aleatorio temporalmente restringido; ver encabezado",
                   "familias": fams},
        "desviaciones": [
            "fuente no restringida en el crecimiento (ver encabezado); se reporta mezcla de fuentes como diagnostico",
        ],
        "resumen": {"threads": len(tids), "por_familia": per_family,
                    "sin_senal": sum(1 for t in tids
                                     if not any(pv[t][f]["sig"] for f in fams))},
        "per_thread": {
            t: {"n": len(threads[t]),
                "real": {"duration": real[t][0], "max_gap": real[t][1],
                         "coherence": round(real[t][2], 4)},
                "null_median": {
                    "duration": float(np.median(nulls[t]["duration"])) if nulls[t]["duration"] else None,
                    "max_gap": float(np.median(nulls[t]["max_gap"])) if nulls[t]["max_gap"] else None,
                    "coherence": round(float(np.median(nulls[t]["coherence"])), 4) if nulls[t]["coherence"] else None,
                },
                "grow_fails": nulls[t]["fails"],
                "tests": pv[t], **src_mix[t]}
            for t in tids
        },
    }
    (OUT_DIR / "f4a_conditioned_null.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
    np.savez_compressed(
        OUT_DIR / "f4a_null_distributions.npz",
        **{f"{t}__{s}": np.array(nulls[t][s])
           for t in tids for s in ("duration", "max_gap", "coherence")})
    print(json.dumps(result["resumen"], indent=1))


if __name__ == "__main__":
    main()
