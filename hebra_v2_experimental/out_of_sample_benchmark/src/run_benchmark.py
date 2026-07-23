# -*- coding: utf-8 -*-
"""
Benchmark fuera de muestra de HEBRA v2 EXPERIMENTAL (congelado).

Corre el codigo y diccionario YA CONGELADOS (importados sin modificar) sobre
hilos distintos de H0000, y mide cobertura, pureza (proxy estructural; la
pureza real requiere una nueva muestra ciega, ver seccion 5), fragmentacion,
sobreagregacion y abstencion.

Guardrails:
- Llama verify_frozen.assert_frozen() antes de correr nada: si alguien toco
  subthread_dictionary.py o build_hierarchy.py despues del congelamiento,
  esto aborta con error.
- No se anade NINGUNA regla nueva al diccionario aqui ni en ningun otro
  archivo de esta carpeta.
- No declara ganador ni superioridad de HEBRA sobre nada.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
V2_SRC = HERE.parent.parent / "src"
sys.path.insert(0, str(V2_SRC))
sys.path.insert(0, str(HERE))

import verify_frozen  # noqa: E402
verify_frozen.assert_frozen()

from build_hierarchy import (  # noqa: E402  (importado SIN modificar)
    build_primary_assignment,
    add_secondary_assignments,
    detect_bridge_crossings,
)
from subthread_dictionary import SIN_SUBHILO  # noqa: E402

from prepare_thread_inputs import list_candidate_threads, build_thread_nodes_edges  # noqa: E402

ARTIFACTS = HERE.parent / "artifacts"
MIN_DOCS = 15

# Hilos con heterogeneidad transitiva conocida = 0% (H0000_14_ADDENDUM), es
# decir, independientemente confirmados como UN solo proceso coherente. Sirven
# de prueba directa de fragmentacion: si el diccionario los parte en varios
# subhilos no triviales, eso es evidencia real de sobre-fragmentacion (no un
# proxy), porque la coherencia de referencia ya estaba establecida antes de
# este benchmark.
KNOWN_COHERENT_BASELINES = {"H0001": "dominga", "H0002": "fundicion_ventanas", "H0004": "bocamina"}


def run_thread(thread_id: str) -> dict:
    nodes, edges, G = build_thread_nodes_edges(thread_id)

    primary = build_primary_assignment(nodes)  # funcion congelada, sin cambios
    full = add_secondary_assignments(primary, edges)  # funcion congelada, sin cambios
    full["macrohilo_id"] = thread_id  # override cosmetico post-hoc; NO toca la logica de asignacion

    # detect_bridge_crossings (congelada) asume que existe >=1 arista puente y
    # falla con KeyError sobre un DataFrame vacio sin columnas si el subgrafo
    # inducido de este hilo no tiene NINGUNA arista puente (caso que nunca
    # ocurrio en H0000, donde habia 23). Esto es un caso limite pre-existente
    # de la funcion congelada, no algo que debamos arreglar tocandola: se
    # evita la llamada y se construye a mano el DataFrame vacio con el mismo
    # esquema de columnas que la funcion congelada produce en el caso normal.
    if not edges["puente"].any():
        bridges = pd.DataFrame(columns=["doc_i", "doc_j", "w", "subhilo_i", "subhilo_j", "cruza_subhilos_distintos"])
    else:
        bridges = detect_bridge_crossings(full, edges)  # funcion congelada, sin cambios

    n_docs = len(full)
    con_subhilo = full[full["subhilo_primario"] != SIN_SUBHILO]
    n_con_subhilo = len(con_subhilo)
    cobertura = n_con_subhilo / n_docs if n_docs else float("nan")
    abstencion = 1 - cobertura if n_docs else float("nan")

    subhilo_sizes = con_subhilo["subhilo_primario"].value_counts()
    n_subhilos = int(len(subhilo_sizes))
    # indice de fragmentacion: 1 = cada documento asignado es su propio subhilo
    # (maxima fragmentacion), 0 = todos los documentos asignados caen en un
    # solo subhilo (minima fragmentacion). No definido si no hay documentos
    # asignados.
    fragmentation_index = (n_subhilos / n_con_subhilo) if n_con_subhilo else None

    # sobreagregacion (proxy estructural, NO validado por IA/humano): para
    # cada subhilo con >=2 documentos, cuantos territorios DISTINTOS agrupa.
    # Un subhilo que mezcla >1 territorio sin relacion es candidato a
    # sobreagregacion (esta uniendo documentos de lugares distintos bajo la
    # misma clave), aunque territorios compartidos no bastan por si solos
    # para declarar pureza (ver limitaciones en el informe).
    overagg_rows = []
    nodes_terr = nodes.set_index("doc_id")["territorio"] if "territorio" in nodes.columns else None
    for subhilo, grp in con_subhilo.groupby("subhilo_primario"):
        docs_in = grp["doc_id"].tolist()
        territorios = set()
        if nodes_terr is not None:
            for d in docs_in:
                t = nodes_terr.get(d, "")
                if t:
                    territorios.update(t.split(";"))
        overagg_rows.append({
            "subhilo": subhilo, "n_docs": len(docs_in),
            "n_territorios_distintos": len(territorios),
            "territorios": sorted(territorios),
            "posible_sobreagregacion": len(docs_in) >= 2 and len(territorios) > 1,
        })
    n_subhilos_con_riesgo_sobreagregacion = sum(1 for r in overagg_rows if r["posible_sobreagregacion"])

    n_puentes = int(len(bridges))
    n_puentes_cruzan = int(bridges["cruza_subhilos_distintos"].sum()) if n_puentes else 0

    return {
        "thread_id": thread_id,
        "es_baseline_conocido_coherente": thread_id in KNOWN_COHERENT_BASELINES,
        "objeto_baseline": KNOWN_COHERENT_BASELINES.get(thread_id),
        "n_docs": n_docs,
        "n_docs_con_subhilo": n_con_subhilo,
        "cobertura": round(cobertura, 4) if n_docs else None,
        "abstencion": round(abstencion, 4) if n_docs else None,
        "n_subhilos_distintos_no_abstencion": n_subhilos,
        "distribucion_subhilos": subhilo_sizes.to_dict(),
        "indice_fragmentacion": round(fragmentation_index, 4) if fragmentation_index is not None else None,
        "n_subhilos_con_riesgo_sobreagregacion_proxy": n_subhilos_con_riesgo_sobreagregacion,
        "detalle_subhilos": overagg_rows,
        "n_puentes_totales": n_puentes,
        "n_puentes_que_cruzan_subhilos": n_puentes_cruzan,
        "n_documentos_multiasignados": int(full["multiasignado"].sum()),
        "_full_assignment": full,  # se descarta antes de serializar el resumen agregado
    }


def main():
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    candidates = list_candidate_threads(min_docs=MIN_DOCS)
    results = []
    all_assignments = []
    for thread_id in candidates["thread_id"]:
        r = run_thread(thread_id)
        full = r.pop("_full_assignment")
        full_out = full.copy()
        full_out["subhilo_secundario"] = full_out["subhilo_secundario"].map(lambda l: ";".join(l))
        full_out["subhilo_secundario_evidencia"] = full_out["subhilo_secundario_evidencia"].map(
            lambda l: json.dumps(l, ensure_ascii=False))
        all_assignments.append(full_out)
        results.append(r)
        print(f"[OK] {thread_id}: n_docs={r['n_docs']} cobertura={r['cobertura']} "
              f"n_subhilos={r['n_subhilos_distintos_no_abstencion']} "
              f"fragmentacion={r['indice_fragmentacion']}")

    pd.concat(all_assignments, ignore_index=True).to_csv(
        ARTIFACTS / "out_of_sample_node_assignment.csv", index=False, encoding="utf-8-sig")

    summary = {
        "seleccion_hilos": {
            "criterio": f"todos los thread_id con >= {MIN_DOCS} documentos, excluyendo H0000",
            "n_hilos_evaluados": len(results),
            "hilos": candidates["thread_id"].tolist(),
        },
        "advertencia_principal": (
            "El diccionario de subhilo (subthread_dictionary.py) fue construido a partir del "
            "vocabulario propio de H0000 (litio, Codelco-SQM, Maricunga, CEOL, Salar de Atacama). "
            "Los hilos evaluados aqui son sobre conflictos socioambientales TOTALMENTE distintos "
            "(Dominga, Fundicion Ventanas, H2 Magallanes, Bocamina, Alto Maipo, HidroAysen, El Mauro, "
            "Faro del Sur, ENAP Aconcagua, entre otros) y no comparten vocabulario con H0000. Por "
            "diseno del congelamiento, NO se anadio ninguna regla nueva para reconocer los objetos "
            "especificos de estos hilos. El resultado esperable -y observado- es cobertura muy baja "
            "o nula en la mayoria: eso NO es un fallo del mecanismo, es la consecuencia directa y "
            "correcta de aplicar un diccionario especifico de un corpus a un corpus distinto sin "
            "extenderlo. Ver H0000_FINAL_EMPIRICAL_REPORT y OUT_OF_SAMPLE_BENCHMARK_REPORT para la "
            "interpretacion completa."
        ),
        "resultados_por_hilo": results,
        "baselines_conocidos_coherentes": {
            tid: next((r for r in results if r["thread_id"] == tid), None)
            for tid in KNOWN_COHERENT_BASELINES
        },
    }
    with open(ARTIFACTS / "out_of_sample_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2, default=str)

    print("\n[OK] Resumen escrito en artifacts/out_of_sample_summary.json")


if __name__ == "__main__":
    main()
