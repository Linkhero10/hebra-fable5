# -*- coding: utf-8 -*-
"""
Agrupacion en subhilos generales (HEBRA v3 EXPERIMENTAL), a partir del
extractor general (general_extractor.py). Reemplaza el diccionario de v2
(subthread_dictionary.py, regex por macrohilo) por la clave canonica
`proyecto_instalacion` ya calculada de forma general -- sin tabla de
patrones especifica de ningun hilo.

No importa ni modifica nada de hebra_v2_experimental/. Es una via
paralela e independiente.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import networkx as nx
import pandas as pd

BASE = Path(r"D:\Analisis conflictos\01_proyecto_universidad\09_metodologia\faro_model_research\competition")
OUTPUTS = BASE / "fable5" / "outputs"
THREADS_PATH = OUTPUTS / "f2b_idf_v2_L2_threads.csv"
EDGES_PATH = OUTPUTS / "f2b_idf_v2_L2_edges.csv"

ABSTENCION = "SIN_PROYECTO_INSTALACION_IDENTIFICADO"
SECONDARY_WEIGHT_THRESHOLD = 0.60


def build_primary_assignment(nodes: pd.DataFrame, macrohilo_id: str) -> pd.DataFrame:
    """nodes debe tener doc_id + las columnas de general_extractor.py
    (proyecto_instalacion, territorio, organizacion, procedimiento,
    procedimiento_familia, evento_fase)."""
    out = nodes.copy()
    out["macrohilo_id"] = macrohilo_id
    out["subhilo_primario"] = out["proyecto_instalacion"].apply(
        lambda v: v if v else ABSTENCION)
    out["abstuvo"] = out["subhilo_primario"] == ABSTENCION
    out = out.sort_values("doc_id").reset_index(drop=True)
    return out


def add_secondary_assignments(primary: pd.DataFrame, edges: pd.DataFrame) -> pd.DataFrame:
    """Multiasignacion: si un documento comparte 'organizacion' con un
    vecino de peso alto cuyo proyecto_instalacion es distinto, se registra
    como subhilo secundario (sin fusionar ni forzar una unica pertenencia).
    Misma logica conceptual que v2, aplicada a la clave general en vez de
    a un diccionario de regex."""
    doc_to_primary = dict(zip(primary["doc_id"], primary["subhilo_primario"]))
    doc_to_org = dict(zip(primary["doc_id"], primary["organizacion"]))
    secondary = {d: set() for d in primary["doc_id"]}
    provenance = {d: [] for d in primary["doc_id"]}

    for _, e in edges.iterrows():
        if pd.isna(e.get("w")) or float(e["w"]) < SECONDARY_WEIGHT_THRESHOLD:
            continue
        i, j = e["doc_i"], e["doc_j"]
        if i not in doc_to_primary or j not in doc_to_primary:
            continue
        for a, b in [(i, j), (j, i)]:
            own = doc_to_primary[a]
            other_proj = doc_to_primary[b]
            if other_proj == ABSTENCION or other_proj == own:
                continue
            org_a = set(doc_to_org.get(a, "").split(";")) - {""}
            org_b = set(doc_to_org.get(b, "").split(";")) - {""}
            if org_a & org_b:  # organizacion compartida con un proyecto distinto
                secondary[a].add(other_proj)
                provenance[a].append({"via_doc": b, "w": float(e["w"]), "proyecto": other_proj,
                                       "organizacion_compartida": sorted(org_a & org_b)})

    out = primary.copy()
    out["subhilo_secundario"] = out["doc_id"].map(lambda d: sorted(secondary.get(d, set())))
    out["subhilo_secundario_evidencia"] = out["doc_id"].map(lambda d: provenance.get(d, []))
    out["multiasignado"] = out["subhilo_secundario"].map(lambda lst: len(lst) > 0)
    return out


def detect_bridge_crossings(full: pd.DataFrame, edges: pd.DataFrame, docs: set) -> pd.DataFrame:
    doc_to_primary = dict(zip(full["doc_id"], full["subhilo_primario"]))
    G = nx.Graph()
    G.add_nodes_from(docs)
    for _, e in edges.iterrows():
        G.add_edge(e["doc_i"], e["doc_j"], weight=float(e["w"]))
    bridge_set = set(frozenset(b) for b in nx.bridges(G))

    rows = []
    for _, e in edges.iterrows():
        i, j = e["doc_i"], e["doc_j"]
        if frozenset((i, j)) not in bridge_set:
            continue
        si, sj = doc_to_primary.get(i), doc_to_primary.get(j)
        cruza = (si != sj) and (si != ABSTENCION) and (sj != ABSTENCION)
        rows.append({"doc_i": i, "doc_j": j, "w": float(e["w"]),
                      "subhilo_i": si, "subhilo_j": sj,
                      "cruza_subhilos_distintos": bool(cruza)})
    if not rows:
        return pd.DataFrame(columns=["doc_i", "doc_j", "w", "subhilo_i", "subhilo_j", "cruza_subhilos_distintos"])
    return pd.DataFrame(rows).sort_values(["doc_i", "doc_j"]).reset_index(drop=True)


def build_thread_nodes(thread_id: str, extracted_by_doc: dict) -> pd.DataFrame:
    """Arma el DataFrame de nodos de un hilo a partir de la extraccion
    general ya calculada (extracted_by_doc: doc_id -> dict de
    general_extractor.extract_document_fields)."""
    threads = pd.read_csv(THREADS_PATH, dtype=str)
    docs = threads.loc[threads["thread_id"] == thread_id, "doc_id"].tolist()
    rows = [extracted_by_doc[d] for d in docs if d in extracted_by_doc]
    return pd.DataFrame(rows)


def build_thread_edges(thread_id: str) -> pd.DataFrame:
    threads = pd.read_csv(THREADS_PATH, dtype=str)
    docs = set(threads.loc[threads["thread_id"] == thread_id, "doc_id"])
    edges_all = pd.read_csv(EDGES_PATH, dtype={"doc_i": str, "doc_j": str})
    edges_all["w"] = edges_all["w"].astype(float)
    return edges_all[edges_all["doc_i"].isin(docs) & edges_all["doc_j"].isin(docs)].copy(), docs
