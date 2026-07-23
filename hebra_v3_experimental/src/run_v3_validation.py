# -*- coding: utf-8 -*-
"""
Corre HEBRA v3 (extractor general + agrupacion) sobre H0000 y los mismos 18
macrohilos usados en el benchmark fuera de muestra de v2, y calcula las
mismas metricas (cobertura, fragmentacion, sobreagregacion-proxy,
abstencion) para comparacion directa con el resultado de v2 (0% en los 18).

No modifica hebra_v2_experimental/. No declara ganador entre v2 y v3 ni
frente a FTD -- solo reporta metricas.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from general_extractor import extract_corpus  # noqa: E402
from build_general_subthreads import (  # noqa: E402
    build_primary_assignment, add_secondary_assignments, detect_bridge_crossings,
    build_thread_nodes, build_thread_edges, ABSTENCION,
)

ARTIFACTS = HERE.parent / "artifacts"
THREADS_PATH = HERE.parent.parent / "outputs" / "f2b_idf_v2_L2_threads.csv"

KNOWN_COHERENT_BASELINES = {"H0001": "dominga", "H0002": "fundicion_ventanas", "H0004": "bocamina"}


def list_threads(min_docs: int = 15, include_h0000: bool = True):
    threads = pd.read_csv(THREADS_PATH, dtype=str)
    counts = threads["thread_id"].value_counts()
    counts = counts[counts >= min_docs]
    if not include_h0000:
        counts = counts[counts.index != "H0000"]
    return counts.sort_values(ascending=False)


def run_thread(thread_id: str, extracted_by_doc: dict) -> dict:
    nodes = build_thread_nodes(thread_id, extracted_by_doc)
    edges, docs = build_thread_edges(thread_id)

    primary = build_primary_assignment(nodes, thread_id)
    full = add_secondary_assignments(primary, edges)
    bridges = detect_bridge_crossings(full, edges, docs)

    n_docs = len(full)
    con_subhilo = full[full["subhilo_primario"] != ABSTENCION]
    n_con_subhilo = len(con_subhilo)
    cobertura = n_con_subhilo / n_docs if n_docs else float("nan")

    subhilo_sizes = con_subhilo["subhilo_primario"].value_counts()
    n_subhilos = int(len(subhilo_sizes))
    fragmentation_index = (n_subhilos / n_con_subhilo) if n_con_subhilo else None

    # sobreagregacion proxy: subhilos con >1 territorio distinto entre sus miembros
    overagg_rows = []
    nodes_terr = nodes.set_index("doc_id")["territorio"] if "territorio" in nodes.columns else None
    for subhilo, grp in con_subhilo.groupby("subhilo_primario"):
        docs_in = grp["doc_id"].tolist()
        territorios = set()
        if nodes_terr is not None:
            for d in docs_in:
                t = nodes_terr.get(d, "")
                if t:
                    territorios.add(t)
        overagg_rows.append({
            "subhilo": subhilo, "n_docs": len(docs_in),
            "n_territorios_distintos": len(territorios),
            "posible_sobreagregacion": len(docs_in) >= 2 and len(territorios) > 1,
        })
    n_riesgo_sobreagregacion = sum(1 for r in overagg_rows if r["posible_sobreagregacion"])

    n_puentes = int(len(bridges))
    n_puentes_cruzan = int(bridges["cruza_subhilos_distintos"].sum()) if n_puentes else 0

    return {
        "thread_id": thread_id,
        "es_baseline_conocido_coherente": thread_id in KNOWN_COHERENT_BASELINES,
        "n_docs": n_docs,
        "n_docs_con_subhilo": n_con_subhilo,
        "cobertura": round(cobertura, 4) if n_docs else None,
        "abstencion": round(1 - cobertura, 4) if n_docs else None,
        "n_subhilos_distintos": n_subhilos,
        "distribucion_subhilos_top10": subhilo_sizes.head(10).to_dict(),
        "indice_fragmentacion": round(fragmentation_index, 4) if fragmentation_index is not None else None,
        "n_subhilos_con_riesgo_sobreagregacion_proxy": n_riesgo_sobreagregacion,
        "n_puentes_totales": n_puentes,
        "n_puentes_que_cruzan_subhilos": n_puentes_cruzan,
        "n_documentos_multiasignados": int(full["multiasignado"].sum()),
        "_full": full,
    }


def main():
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    print("[..] extrayendo campos generales de los 3742 documentos del corpus (una sola vez)")
    extracted = extract_corpus()
    extracted_by_doc = {r["doc_id"]: r for r in extracted}

    threads = list_threads(min_docs=15, include_h0000=True)
    results = []
    all_full = []
    for thread_id in threads.index:
        r = run_thread(thread_id, extracted_by_doc)
        full = r.pop("_full")
        full_out = full.copy()
        full_out["subhilo_secundario"] = full_out["subhilo_secundario"].map(lambda l: ";".join(l))
        full_out["subhilo_secundario_evidencia"] = full_out["subhilo_secundario_evidencia"].map(
            lambda l: json.dumps(l, ensure_ascii=False))
        all_full.append(full_out)
        results.append(r)
        print(f"[OK] {thread_id}: n_docs={r['n_docs']} cobertura={r['cobertura']} "
              f"n_subhilos={r['n_subhilos_distintos']} fragmentacion={r['indice_fragmentacion']} "
              f"multiasignados={r['n_documentos_multiasignados']}")

    pd.concat(all_full, ignore_index=True).to_csv(
        ARTIFACTS / "v3_node_assignment_all_threads.csv", index=False, encoding="utf-8-sig")

    h0000_result = next(r for r in results if r["thread_id"] == "H0000")
    out_of_sample_results = [r for r in results if r["thread_id"] != "H0000"]
    cobertura_promedio_fuera_muestra = (
        sum(r["cobertura"] for r in out_of_sample_results) / len(out_of_sample_results)
        if out_of_sample_results else None
    )

    summary = {
        "n_hilos_evaluados": len(results),
        "h0000_sanity_check": h0000_result,
        "cobertura_promedio_fuera_de_muestra_18_hilos": round(cobertura_promedio_fuera_muestra, 4)
            if cobertura_promedio_fuera_muestra is not None else None,
        "comparacion_con_v2": {
            "v2_cobertura_fuera_de_muestra": 0.0,
            "v3_cobertura_fuera_de_muestra_promedio": round(cobertura_promedio_fuera_muestra, 4)
                if cobertura_promedio_fuera_muestra is not None else None,
            "nota": "v2 uso un diccionario de regex especifico de H0000 (cobertura 0% fuera de muestra). "
                    "v3 usa columnas LLM ya extraidas de forma general para todo el corpus, sin vocabulario "
                    "de ningun macrohilo. La comparacion es puramente descriptiva; no se declara que v3 sea "
                    "'mejor' sin validar la PUREZA de sus asignaciones (ver limitaciones en el informe).",
        },
        "resultados_por_hilo": results,
        "baselines_conocidos_coherentes": {
            tid: next((r for r in results if r["thread_id"] == tid), None)
            for tid in KNOWN_COHERENT_BASELINES
        },
    }
    with open(ARTIFACTS / "v3_validation_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2, default=str)

    print("\n[OK] Resumen escrito en artifacts/v3_validation_summary.json")
    print(f"Cobertura H0000 (sanity check): {h0000_result['cobertura']}")
    print(f"Cobertura promedio fuera de muestra (18 hilos): {cobertura_promedio_fuera_muestra}")


if __name__ == "__main__":
    main()
