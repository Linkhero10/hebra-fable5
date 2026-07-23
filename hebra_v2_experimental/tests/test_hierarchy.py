# -*- coding: utf-8 -*-
"""
Pruebas de HEBRA v2 EXPERIMENTAL. Cubre los 10 requisitos de la Fase 6:
1. reproducibilidad con semilla fija
2. no modificacion de v1
3. integridad de IDs
4. asignacion macro/subproceso
5. casos multiasignados (probado con datos sinteticos: en el corpus REAL de
   H0000, el umbral w>=0.60 no produce divergencias node-vs-arista, lo cual
   es un hallazgo empirico honesto -ver informe final-, no un defecto; el
   mecanismo en si se prueba de forma aislada aqui)
6. abstenciones
7. ausencia de perdida silenciosa de documentos
8. estabilidad ante orden de entrada
9. generacion de manifests y hashes
10. comparacion reproducible con HEBRA v1
"""
import hashlib
import json
import sys
from pathlib import Path

import pandas as pd
import pytest

SRC = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(SRC))

import build_hierarchy as bh  # noqa: E402
from subthread_dictionary import canonicalize, SIN_SUBHILO  # noqa: E402

DIAG = bh.DIAG
ARTIFACTS = bh.ARTIFACTS


# ---------------------------------------------------------------------------
# 1. Reproducibilidad con semilla fija
# ---------------------------------------------------------------------------
def test_reproducible_with_fixed_seed():
    r1 = bh.run(seed=20260780, shuffle_input=False)
    h1 = hashlib.sha256(r1["full"].to_csv(index=False).encode("utf-8")).hexdigest()
    r2 = bh.run(seed=20260780, shuffle_input=False)
    h2 = hashlib.sha256(r2["full"].to_csv(index=False).encode("utf-8")).hexdigest()
    assert h1 == h2, "la misma semilla debe producir exactamente el mismo resultado"


# ---------------------------------------------------------------------------
# 2. No modificacion de v1 (verifica contra el manifest v1 congelado)
# ---------------------------------------------------------------------------
def test_v1_not_modified():
    check = bh.verify_v1_untouched()
    assert check["todos_los_archivos_v1_intactos"] is True
    for fname, detail in check["detalle"].items():
        assert detail["existe"], f"{fname} deberia existir intacto en diagnostics_h0000/"
        assert detail["coincide"], f"{fname} no coincide con el hash del manifest v1 -- posible modificacion"


# ---------------------------------------------------------------------------
# 3. Integridad de IDs (todos los doc_id de node_metrics aparecen exactamente
#    una vez en la asignacion; ningun id inventado)
# ---------------------------------------------------------------------------
def test_id_integrity():
    nodes = pd.read_csv(DIAG / "H0000_02_NODE_METRICS.csv", dtype={"doc_id": str})
    result = bh.run(seed=1)
    full = result["full"]
    assert set(full["doc_id"]) == set(nodes["doc_id"]), "los IDs asignados deben ser exactamente los 170 de v1"
    assert full["doc_id"].is_unique, "no debe haber doc_id duplicados en la asignacion"
    assert (full["macrohilo_id"] == "H0000").all(), "todo documento de H0000 debe heredar el macrohilo_id v1"


# ---------------------------------------------------------------------------
# 4. Asignacion macro/subproceso: cada documento tiene macrohilo_id y
#    subhilo_primario, y subhilo_primario es una de las claves del diccionario
#    o la abstencion
# ---------------------------------------------------------------------------
def test_macro_subhilo_assignment_shape():
    result = bh.run(seed=1)
    full = result["full"]
    assert "macrohilo_id" in full.columns
    assert "subhilo_primario" in full.columns
    # comprobacion directa: cada subhilo_primario debe venir de canonicalize()
    for _, row in full.sample(min(30, len(full)), random_state=1).iterrows():
        key, _ = canonicalize(row["objeto_original"])
        assert row["subhilo_primario"] == key


# ---------------------------------------------------------------------------
# 5. Casos multiasignados (mecanismo probado con datos sinteticos, aislado
#    del corpus real, para no depender de si el corpus real dispara el caso)
# ---------------------------------------------------------------------------
def test_multi_assignment_mechanism_synthetic():
    primary = pd.DataFrame([
        {"doc_id": "A", "macrohilo_id": "H0000", "objeto_original": "estrategia nacional del litio",
         "subhilo_primario": "SIN_SUBHILO_ESPECIFICO", "regla_aplicada": None, "abstuvo": True},
        {"doc_id": "B", "macrohilo_id": "H0000", "objeto_original": "proyecto blanco",
         "subhilo_primario": "proyecto_maricunga_salar_blanco", "regla_aplicada": "x", "abstuvo": False},
    ])
    edges = pd.DataFrame([
        {"doc_i": "A", "doc_j": "B", "w": 0.75, "ref_objeto": "proyecto blanco", "puente": False},
    ])
    out = bh.add_secondary_assignments(primary, edges)
    row_a = out[out.doc_id == "A"].iloc[0]
    assert row_a["multiasignado"] is True or len(row_a["subhilo_secundario"]) > 0
    assert "proyecto_maricunga_salar_blanco" in row_a["subhilo_secundario"]


# ---------------------------------------------------------------------------
# 6. Abstenciones: documentos con objeto generico deben quedar en
#    SIN_SUBHILO_ESPECIFICO, no en una clave inventada
# ---------------------------------------------------------------------------
def test_abstention_for_generic_object():
    key, pattern = canonicalize("estrategia nacional del litio")
    assert key == SIN_SUBHILO
    assert pattern is None
    result = bh.run(seed=1)
    full = result["full"]
    generic_docs = full[full["objeto_original"] == "estrategia nacional del litio"]
    assert (generic_docs["subhilo_primario"] == SIN_SUBHILO).all()
    assert (generic_docs["abstuvo"] == True).all()  # noqa: E712


# ---------------------------------------------------------------------------
# 7. Ausencia de perdida silenciosa de documentos (170 documentos de entrada
#    -> 170 filas de salida, siempre, incluidos los que abstienen)
# ---------------------------------------------------------------------------
def test_no_silent_document_loss():
    nodes = pd.read_csv(DIAG / "H0000_02_NODE_METRICS.csv", dtype={"doc_id": str})
    result = bh.run(seed=1)
    full = result["full"]
    assert len(full) == len(nodes) == 170
    assert full["subhilo_primario"].isna().sum() == 0, "ningun documento debe quedar sin valor (abstencion es explicita, no NaN)"


# ---------------------------------------------------------------------------
# 8. Estabilidad ante orden de entrada: barajar node/edge metrics de entrada
#    no debe cambiar el resultado final (la salida se ordena por doc_id)
# ---------------------------------------------------------------------------
def test_stable_under_input_order():
    r_normal = bh.run(seed=42, shuffle_input=False)
    r_shuffled = bh.run(seed=42, shuffle_input=True)
    a = r_normal["full"][["doc_id", "subhilo_primario"]].sort_values("doc_id").reset_index(drop=True)
    b = r_shuffled["full"][["doc_id", "subhilo_primario"]].sort_values("doc_id").reset_index(drop=True)
    pd.testing.assert_frame_equal(a, b)


# ---------------------------------------------------------------------------
# 9. Generacion de manifests y hashes
# ---------------------------------------------------------------------------
def test_manifest_and_lock_generated():
    bh.run(seed=1)
    manifest_path = ARTIFACTS / "HIERARCHY_MANIFEST.json"
    lock_path = ARTIFACTS / "HIERARCHY_EXPERIMENT_LOCK.json"
    assert manifest_path.exists()
    assert lock_path.exists()
    with open(manifest_path, encoding="utf-8") as f:
        manifest = json.load(f)
    assert "files" in manifest and len(manifest["files"]) == 3
    assert "v1_inputs_read_only" in manifest
    with open(lock_path, encoding="utf-8") as f:
        lock = json.load(f)
    assert lock["v1_no_modificado"] is True
    assert lock["reemplaza_v1"] is False
    assert lock["ganador_empirico_declarado"] is False


# ---------------------------------------------------------------------------
# 10. Comparacion reproducible con HEBRA v1: el macrohilo_id producido debe
#     ser exactamente el hilo v1 (H0000), y el numero de documentos debe
#     coincidir con el subgrafo v1 congelado (170)
# ---------------------------------------------------------------------------
def test_reproducible_comparison_with_v1():
    subgraph = pd.read_csv(DIAG / "H0000_01_SUBGRAPH_CANONICAL.csv")
    v1_doc_count = len(pd.read_csv(DIAG / "H0000_02_NODE_METRICS.csv"))
    result = bh.run(seed=1)
    full = result["full"]
    assert len(full) == v1_doc_count
    assert full["macrohilo_id"].nunique() == 1
    assert full["macrohilo_id"].iloc[0] == "H0000"
    # el v2 no debe declarar mas ni menos documentos que el v1 congelado
    nodes_v1 = pd.read_csv(DIAG / "H0000_02_NODE_METRICS.csv", dtype={"doc_id": str})
    assert set(full["doc_id"]) == set(nodes_v1["doc_id"])


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
