# F3 — Calibracion contra nulos temporales (HEBRA).
# Configuracion congelada: hilos de outputs/f2b_idf_v2_L2_threads.csv
# (variante IDF, referentes F1v2, tau=0.45, tier largo L2; ver
# F2_6_LONG_TIER_DECISION_2026_07_22.md).
#
# Nulos:
#  N1 (intraanual): permutacion de fechas dentro de estratos anno x fuente.
#     Solo licencia afirmaciones de rafaga, orden intranual y brechas cortas.
#     NO es prueba de emergencia ni reaparicion multianual.
#  N2 (interanual): pseudo-hilos igualados por tamano, muestreados uniforme
#     del corpus fechado, usando fechas reales. Es un nulo CONJUNTO de
#     referentes+tiempo: falsa "este perfil difiere de un agrupamiento
#     arbitrario del mismo tamano bajo el mismo corpus no estacionario".
#     No permite afirmar que la temporalidad por si sola explica el resultado.
#     N2b (igualado por grado de referente) queda registrado como extension
#     futura; no se selecciona ahora.
#
# Senales y estadisticos (preinscritos):
#  intra (N1): burst30 = max docs del hilo en ventana movil de 30 dias dentro
#              de su anno pico; gap_corto = max brecha entre docs consecutivos
#              del hilo dentro de un mismo anno calendario.
#  inter (N2): peak_share_q = max cuota trimestral (docs hilo / docs corpus);
#              peak_share_s = idem semestral (sensibilidad de unidad);
#              max_gap = max brecha interna en dias;
#              duration = extension total en dias (dos colas);
#              reaparicion = derivada: max_gap significativo (BH) y >=3 docs
#              posteriores a esa brecha.
#  Mensual no se evalua: mediana de hilo = 4 docs, celdas casi vacias.
#
# Significacion: p empirico con correccion +1 (Phipson-Smyth); BH-FDR por
# familia de senal (q<=0.05). Dos colas para duration.
# B=200 permutaciones/muestras por nulo; semillas fijas.

import csv
import json
import hashlib
import random
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[4].parent
CORPUS = ROOT / "01_bases_de_datos/03_refiltro_api_qwen_y_base_actual/06_base_actual_fusionada_3742_incluidas.csv"
OUT_DIR = Path(__file__).resolve().parents[1] / "outputs"
THREADS = OUT_DIR / "f2b_idf_v2_L2_threads.csv"

B = 200
SEED_N1, SEED_N2 = 20260731, 20260732
ALPHA_FDR = 0.05
MIN_SIZE = 3
LOW_COVERAGE_DOCS = 50


def p_emp(null_vals, real, tail="greater"):
    a = np.asarray(null_vals, dtype=float)
    if tail == "greater":
        return (1 + np.sum(a >= real)) / (len(a) + 1)
    return (1 + np.sum(a <= real)) / (len(a) + 1)


def bh(pvals):
    idx = np.argsort(pvals)
    n = len(pvals)
    q = np.empty(n)
    prev = 1.0
    for rank, i in enumerate(reversed(idx), 1):
        pos = n - rank
        val = pvals[idx[pos]] * n / (pos + 1)
        prev = min(prev, val)
        q[idx[pos]] = prev
    return q


def burst30(days):
    days = sorted(days)
    best, j = 1, 0
    for i in range(len(days)):
        while days[i] - days[j] > 30:
            j += 1
        best = max(best, i - j + 1)
    return best


def stats_intra(days_by_year):
    # anno pico y burst30 dentro de el; gap corto max dentro de un mismo anno
    peak_year = max(days_by_year, key=lambda y: len(days_by_year[y]))
    b = burst30(days_by_year[peak_year])
    gap = 0
    for y, ds in days_by_year.items():
        ds = sorted(ds)
        for a, c in zip(ds, ds[1:]):
            gap = max(gap, c - a)
    return b, gap, peak_year


def stats_inter(days, quarters_all, semesters_all, q_of, s_of):
    days = sorted(days)
    qc = Counter(q_of[d] for d in days)
    sc = Counter(s_of[d] for d in days)
    peak_q = max(qc[q] / quarters_all[q] for q in qc)
    peak_s = max(sc[s] / semesters_all[s] for s in sc)
    gaps = [c - a for a, c in zip(days, days[1:])]
    max_gap = max(gaps) if gaps else 0
    dur = days[-1] - days[0]
    # docs despues de la brecha maxima
    after = 0
    if gaps:
        gi = gaps.index(max_gap)
        after = len(days) - gi - 1
    return peak_q, peak_s, max_gap, dur, after


def main() -> None:
    # --- carga ---
    fecha, fuente = {}, {}
    with open(CORPUS, encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            d = (row.get("fecha_iso") or "")[:10]
            try:
                fecha[row["id"]] = datetime.strptime(d, "%Y-%m-%d").date()
            except ValueError:
                continue
            fuente[row["id"]] = (row.get("fuente") or "desconocida").strip().lower()

    threads = defaultdict(list)
    with open(THREADS, encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            if row["doc_id"] in fecha:
                threads[row["thread_id"]].append(row["doc_id"])
    threads = {t: ds for t, ds in threads.items() if len(ds) >= MIN_SIZE}

    all_ids = sorted(fecha)
    day = {i: fecha[i].toordinal() for i in all_ids}
    year = {i: fecha[i].year for i in all_ids}
    q_of = {d: (fecha[i].year, (fecha[i].month - 1) // 3) for i, d in day.items()}
    # map por ordinal de dia -> etiquetas de periodo (via id)
    q_of = {day[i]: (fecha[i].year, (fecha[i].month - 1) // 3) for i in all_ids}
    s_of = {day[i]: (fecha[i].year, (fecha[i].month - 1) // 6) for i in all_ids}
    quarters_all = Counter(q_of[day[i]] for i in all_ids)
    semesters_all = Counter(s_of[day[i]] for i in all_ids)
    year_counts = Counter(year[i] for i in all_ids)
    low_cov_years = sorted(y for y, c in year_counts.items() if c < LOW_COVERAGE_DOCS)

    # --- estadisticos reales ---
    real = {}
    for t, ds in threads.items():
        dd = [day[i] for i in ds]
        dby = defaultdict(list)
        for i in ds:
            dby[year[i]].append(day[i])
        b30, gapc, peak_year = stats_intra(dby)
        pq, ps, mg, dur, after = stats_inter(dd, quarters_all, semesters_all, q_of, s_of)
        real[t] = {"n": len(ds), "burst30": b30, "gap_corto": gapc,
                   "peak_year": peak_year, "peak_share_q": pq, "peak_share_s": ps,
                   "max_gap": mg, "duration": dur, "docs_despues_gap": after}

    # --- N1: permutacion anno x fuente (fechas re-asignadas dentro de estrato) ---
    rng1 = random.Random(SEED_N1)
    strata = defaultdict(list)
    for i in all_ids:
        strata[(year[i], fuente[i])].append(i)
    null_n1 = {t: {"burst30": [], "gap_corto": []} for t in threads}
    for b in range(B):
        newday = {}
        for key, members in strata.items():
            ds = [day[i] for i in members]
            rng1.shuffle(ds)
            for i, d in zip(members, ds):
                newday[i] = d
        for t, ds_t in threads.items():
            dby = defaultdict(list)
            for i in ds_t:
                dby[year[i]].append(newday[i])  # anno no cambia bajo N1
            b30, gapc, _ = stats_intra(dby)
            null_n1[t]["burst30"].append(b30)
            null_n1[t]["gap_corto"].append(gapc)

    # --- N2: pseudo-hilos igualados por tamano ---
    rng2 = random.Random(SEED_N2)
    sizes = sorted({len(ds) for ds in threads.values()})
    null_n2_by_size = {k: {"peak_share_q": [], "peak_share_s": [],
                           "max_gap": [], "duration": []} for k in sizes}
    for k in sizes:
        for b in range(B):
            ds = rng2.sample(all_ids, k)
            dd = [day[i] for i in ds]
            pq, ps, mg, dur, _ = stats_inter(dd, quarters_all, semesters_all, q_of, s_of)
            null_n2_by_size[k]["peak_share_q"].append(pq)
            null_n2_by_size[k]["peak_share_s"].append(ps)
            null_n2_by_size[k]["max_gap"].append(mg)
            null_n2_by_size[k]["duration"].append(dur)

    # --- p-valores y BH por familia ---
    tids = sorted(threads)
    fams = {
        "burst30": ("N1", "greater"), "gap_corto": ("N1", "greater"),
        "peak_share_q": ("N2", "greater"), "peak_share_s": ("N2", "greater"),
        "max_gap": ("N2", "greater"),
        "duration_corta": ("N2", "less"), "duration_larga": ("N2", "greater"),
    }
    pv, qv = defaultdict(dict), {}
    for fam, (nul, tail) in fams.items():
        stat = "duration" if fam.startswith("duration") else fam
        ps_ = []
        for t in tids:
            nv = (null_n1[t][stat] if nul == "N1"
                  else null_n2_by_size[len(threads[t])][stat])
            ps_.append(p_emp(nv, real[t][stat], tail))
        qs = bh(np.array(ps_))
        for t, p, q in zip(tids, ps_, qs):
            pv[t][fam] = {"p": round(float(p), 5), "q": round(float(q), 5),
                          "sig": bool(q <= ALPHA_FDR)}

    # reaparicion: derivada de max_gap significativo + >=3 docs posteriores
    for t in tids:
        pv[t]["reaparicion"] = {
            "sig": bool(pv[t]["max_gap"]["sig"] and real[t]["docs_despues_gap"] >= 3),
            "derivada_de": "max_gap(BH) y docs_despues_gap>=3",
        }

    # resumen
    sig_any = [t for t in tids if any(
        v.get("sig") for k, v in pv[t].items())]
    no_signal = [t for t in tids if t not in sig_any]
    per_family = {f: sum(1 for t in tids if pv[t][f].get("sig")) for f in fams}
    per_family["reaparicion"] = sum(1 for t in tids if pv[t]["reaparicion"]["sig"])

    result = {
        "schema_version": 1,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "threads": THREADS.name,
            "threads_sha256": hashlib.sha256(THREADS.read_bytes()).hexdigest(),
            "corpus_sha256": hashlib.sha256(CORPUS.read_bytes()).hexdigest(),
            "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        },
        "config": {
            "B": B, "seed_n1": SEED_N1, "seed_n2": SEED_N2,
            "criterio": "p empirico Phipson-Smyth; BH-FDR q<=0.05 por familia",
            "min_size": MIN_SIZE,
            "familias": {f: {"nulo": n, "cola": c} for f, (n, c) in fams.items()},
            "unidades_sensibilidad": ["trimestre", "semestre"],
            "mensual_omitido": "mediana de hilo 4 docs; celdas casi vacias",
        },
        "advertencias": {
            "n1_alcance": "solo rafagas/orden/brechas intranuales",
            "n2_alcance": "nulo conjunto referentes+tiempo, no temporal puro",
            "n2b": "extension futura registrada, no seleccionada",
            "anos_baja_cobertura": low_cov_years,
            "crecimiento_corpus": "docs/anno se triplican 2022->2025; toda cuota es proporcion del periodo",
            "casos_contaminados": "ningun parametro se modifico mirando los 5 casos de desarrollo",
        },
        "threads_evaluados": len(tids),
        "resumen": {
            "con_alguna_senal": len(sig_any),
            "sin_senal_respaldada": len(no_signal),
            "pct_sin_senal": round(100 * len(no_signal) / len(tids), 1),
            "por_familia": per_family,
        },
        "per_thread": {
            t: {"real": real[t], "tests": pv[t]} for t in tids
        },
    }
    (OUT_DIR / "f3_null_calibration.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")

    np.savez_compressed(
        OUT_DIR / "f3_null_distributions.npz",
        **{f"n1__{t}__{s}": np.array(null_n1[t][s])
           for t in tids for s in ("burst30", "gap_corto")},
        **{f"n2__size{k}__{s}": np.array(null_n2_by_size[k][s])
           for k in sizes for s in ("peak_share_q", "peak_share_s", "max_gap", "duration")},
    )
    print(json.dumps(result["resumen"], ensure_ascii=False, indent=1))
    print("advertencias:", json.dumps(result["advertencias"]["anos_baja_cobertura"]))


if __name__ == "__main__":
    main()
