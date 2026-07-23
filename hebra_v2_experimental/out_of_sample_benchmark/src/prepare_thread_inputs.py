# -*- coding: utf-8 -*-
"""
Adaptador de datos para hilos FUERA de muestra (cualquier thread_id != H0000).

NO modifica ni reimplementa la logica de canonizacion/asignacion (eso vive,
congelado, en hebra_v2_experimental/src/{subthread_dictionary,build_hierarchy}.py).
Este modulo unicamente reconstruye, para un thread_id cualquiera, los mismos
insumos (`nodes` con columna `objeto`, `edges` con columnas `w`, `ref_objeto`,
`puente`) que h0000_diagnostics.py ya calculo para H0000 -- usando el MISMO
metodo (interseccion de referentes por tipo, puentes de teoria de grafos
estandar via networkx), sobre los archivos globales del pipeline v1:

  - fable5/outputs/f2b_idf_v2_L2_threads.csv   (doc_id -> thread_id)
  - fable5/outputs/f2b_idf_v2_L2_edges.csv     (doc_i, doc_j, w, s_ref, s_emb, dias)
  - fable5/outputs/f1v2_referents.csv          (doc_id, tipo, referente)

Esto es deliberadamente una replica fiel del metodo, no una regla nueva: no
se anade vocabulario, no se ajusta ningun umbral, no se toca el diccionario.
"""
from __future__ import annotations

from pathlib import Path

import networkx as nx
import pandas as pd

BASE = Path(r"D:\Analisis conflictos\01_proyecto_universidad\09_metodologia\faro_model_research\competition")
OUTPUTS = BASE / "fable5" / "outputs"

THREADS_PATH = OUTPUTS / "f2b_idf_v2_L2_threads.csv"
EDGES_PATH = OUTPUTS / "f2b_idf_v2_L2_edges.csv"
REFS_PATH = OUTPUTS / "f1v2_referents.csv"


def list_candidate_threads(min_docs: int = 15, exclude=("H0000",)) -> pd.DataFrame:
    """Todos los thread_id con >= min_docs documentos, excluyendo los de `exclude`.
    Criterio de seleccion objetivo (no cherry-picking): un umbral minimo de
    tamano para que el hilo tenga estructura interna no trivial que evaluar."""
    threads = pd.read_csv(THREADS_PATH, dtype=str)
    counts = threads["thread_id"].value_counts()
    counts = counts[~counts.index.isin(exclude)]
    counts = counts[counts >= min_docs]
    return counts.sort_values(ascending=False).rename_axis("thread_id").reset_index(name="n_docs")


def build_thread_nodes_edges(thread_id: str):
    """Devuelve (nodes_df, edges_df) para `thread_id`, con el MISMO esquema
    que build_hierarchy.py espera (nodes: doc_id, objeto; edges: doc_i, doc_j,
    w, ref_objeto, puente), construidos con el mismo metodo que
    h0000_diagnostics.py uso para H0000."""
    threads = pd.read_csv(THREADS_PATH, dtype=str)
    docs = set(threads.loc[threads["thread_id"] == thread_id, "doc_id"])
    if not docs:
        raise ValueError(f"thread_id {thread_id!r} no tiene documentos en {THREADS_PATH.name}")

    edges_all = pd.read_csv(EDGES_PATH, dtype={"doc_i": str, "doc_j": str})
    edges_all["w"] = edges_all["w"].astype(float)
    induced = edges_all[edges_all["doc_i"].isin(docs) & edges_all["doc_j"].isin(docs)].copy()

    refs = pd.read_csv(REFS_PATH, dtype=str)
    refs_thread = refs[refs["doc_id"].isin(docs)]
    # sets de referentes por (doc_id, tipo), igual que refs[d][tipo] en h0000_diagnostics.py
    ref_sets: dict[tuple[str, str], set[str]] = {}
    for (doc_id, tipo), grp in refs_thread.groupby(["doc_id", "tipo"]):
        ref_sets[(doc_id, tipo)] = set(grp["referente"].dropna())

    def refs_for(doc_id: str, tipo: str) -> set[str]:
        return ref_sets.get((doc_id, tipo), set())

    # --- nodes: doc_id, objeto (= ";".join(sorted(referentes objeto)), igual que v1) ---
    node_rows = []
    for d in sorted(docs):
        node_rows.append({
            "doc_id": d,
            "objeto": ";".join(sorted(refs_for(d, "objeto"))),
            "territorio": ";".join(sorted(refs_for(d, "territorio"))),
        })
    nodes_df = pd.DataFrame(node_rows)

    # --- puentes: teoria de grafos estandar (nx.bridges), sobre el subgrafo inducido ---
    G = nx.Graph()
    G.add_nodes_from(docs)
    for _, e in induced.iterrows():
        G.add_edge(e["doc_i"], e["doc_j"], weight=e["w"])
    bridge_set = set(frozenset(b) for b in nx.bridges(G))

    # --- edges: ref_objeto = interseccion de referentes 'objeto', puente = bridge real ---
    edge_rows = []
    for _, e in induced.iterrows():
        i, j = e["doc_i"], e["doc_j"]
        shared_objeto = sorted(refs_for(i, "objeto") & refs_for(j, "objeto"))
        edge_rows.append({
            "doc_i": i, "doc_j": j,
            "w": float(e["w"]),
            "ref_objeto": ";".join(shared_objeto),
            "puente": frozenset((i, j)) in bridge_set,
        })
    edges_df = pd.DataFrame(edge_rows)

    return nodes_df, edges_df, G


if __name__ == "__main__":
    cands = list_candidate_threads()
    print(cands.to_string(index=False))
