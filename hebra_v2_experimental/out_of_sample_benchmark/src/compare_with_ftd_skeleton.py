# -*- coding: utf-8 -*-
"""
ESQUELETO del benchmark comun HEBRA v2 <-> FTD. Ver
../FTD_HEBRA_COMMON_BENCHMARK_SPEC.md para el contexto completo.

ESTADO: escrito pero DELIBERADAMENTE NO EJECUTADO como parte de este
congelamiento. Requiere que alguien resuelva antes:

  1. FTD_UNIT: si "trajectory_id" de FTD es la unidad correcta a comparar
     contra "macrohilo_id" de HEBRA, o si existe una sub-agrupacion FTD mas
     fina que no se ha localizado (Seccion 2 de la especificacion).
  2. Si se quiere tambien una comparacion con gold ciego (Seccion 4.2 de la
     especificacion) -- eso requeriria correr una ronda de adjudicacion
     ciega de FTD, que no se ejecuta aqui.

Este script SOLO calcula comparaciones puramente estructurales (cobertura,
ARI, NMI) entre dos particiones ya existentes, sobre el mismo universo de
documentos. No emite ningun veredicto de "cual sistema es mejor": ARI/NMI
altos significan que las dos particiones coinciden mucho, bajos que
difieren -- ninguna de las dos lecturas implica que una sea mas correcta
que la otra sin una validacion externa (ground truth), que esta fuera de
alcance de este script.
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
from sklearn.metrics import adjusted_rand_score, normalized_mutual_info_score

BASE = Path(r"D:\Analisis conflictos\01_proyecto_universidad\09_metodologia\faro_model_research\competition")
FTD_ASSIGNMENTS = BASE / "gpt5.6sol" / "outputs" / "threshold_0p58_assignments.csv"
HEBRA_THREADS = BASE / "fable5" / "outputs" / "f2b_idf_v2_L2_threads.csv"

# Parametro explicito, NO default silencioso: quien ejecute esto debe decidir
# y declarar por que eligio este valor (ver Seccion 2 de la especificacion).
FTD_UNIT = "trajectory_id"  # unica opcion disponible hoy en los artefactos revisados
HEBRA_UNIT = "macrohilo_id"  # = thread_id de f2b_idf_v2_L2_threads.csv


def load_partitions():
    ftd = pd.read_csv(FTD_ASSIGNMENTS, dtype=str)
    hebra = pd.read_csv(HEBRA_THREADS, dtype=str).rename(columns={"thread_id": "macrohilo_id"})
    return ftd, hebra


def structural_comparison() -> dict:
    ftd, hebra = load_partitions()

    common_ids = set(ftd["id"]) & set(hebra["doc_id"])
    ftd_common = ftd[ftd["id"].isin(common_ids)].set_index("id")
    hebra_common = hebra[hebra["doc_id"].isin(common_ids)].set_index("doc_id")

    # cobertura comparada (no-abstencion) en el universo compartido
    ftd_assigned = ftd_common["status"] == "assigned"
    cobertura_ftd = float(ftd_assigned.mean())
    # HEBRA no tiene "abstencion" a nivel de macrohilo (todo doc en un hilo
    # esta "asignado" a ese hilo por construccion); la abstencion de HEBRA
    # vive al nivel de SUBHILO, que FTD no tiene equivalente documentado.
    cobertura_hebra_macrohilo = 1.0

    # ARI/NMI solo sobre documentos donde AMBOS sistemas asignan (FTD no abstiene)
    both_assigned_ids = sorted(set(ftd_common.index[ftd_assigned]) & set(hebra_common.index))
    labels_ftd = ftd_common.loc[both_assigned_ids, FTD_UNIT].tolist()
    labels_hebra = hebra_common.loc[both_assigned_ids, HEBRA_UNIT].tolist()

    ari = adjusted_rand_score(labels_ftd, labels_hebra) if both_assigned_ids else None
    nmi = normalized_mutual_info_score(labels_ftd, labels_hebra) if both_assigned_ids else None

    return {
        "unidad_ftd": FTD_UNIT,
        "unidad_hebra": HEBRA_UNIT,
        "n_docs_universo_compartido": len(common_ids),
        "n_docs_ambos_asignados": len(both_assigned_ids),
        "cobertura_ftd_status_assigned": round(cobertura_ftd, 4),
        "cobertura_hebra_macrohilo": cobertura_hebra_macrohilo,
        "ari_ftd_trajectory_vs_hebra_macrohilo": round(ari, 4) if ari is not None else None,
        "nmi_ftd_trajectory_vs_hebra_macrohilo": round(nmi, 4) if nmi is not None else None,
        "advertencia": (
            "ARI/NMI miden SOLO acuerdo estructural entre dos particiones ya existentes. "
            "No implican que una particion sea 'mas correcta' que la otra: eso requiere "
            "validacion externa (ground truth ciego) que no se ejecuta en este script. "
            "No se declara ganador. Ver FTD_HEBRA_COMMON_BENCHMARK_SPEC.md seccion 6."
        ),
    }


def ground_truth_comparison_NOT_IMPLEMENTED():
    """Requiere una ronda de adjudicacion ciega de FTD (ver Seccion 4.2 de la
    especificacion) que no existe todavia. Se deja como stub explicito en
    vez de inventar un resultado."""
    raise NotImplementedError(
        "Comparacion contra gold ciego pendiente: requiere una validacion ciega "
        "de FTD (GPT-5.6/Claude, mismo protocolo que H0000) sobre los mismos pares "
        "o documentos, que aun no se ha ejecutado. Ver seccion 4.2 de "
        "FTD_HEBRA_COMMON_BENCHMARK_SPEC.md."
    )


if __name__ == "__main__":
    print("Este script esta escrito pero NO se ejecuta automaticamente como parte "
          "del congelamiento de HEBRA v2. Si decides correrlo, revisa primero "
          "FTD_HEBRA_COMMON_BENCHMARK_SPEC.md seccion 2 (decision de FTD_UNIT) y "
          "recuerda: el resultado es descriptivo (ARI/NMI), no un veredicto de "
          "cual sistema es mejor.")
    result = structural_comparison()
    print(json.dumps(result, ensure_ascii=False, indent=2))
