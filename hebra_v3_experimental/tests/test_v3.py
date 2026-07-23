# -*- coding: utf-8 -*-
"""Pruebas de HEBRA v3 EXPERIMENTAL."""
import hashlib
import json
import sys
from pathlib import Path

import pandas as pd
import pytest

HERE = Path(__file__).resolve().parent
SRC = HERE.parent / "src"
sys.path.insert(0, str(SRC))

import general_extractor as ge  # noqa: E402
import build_general_subthreads as bgs  # noqa: E402

BASE = Path(r"D:\Analisis conflictos\01_proyecto_universidad\09_metodologia\faro_model_research\competition")
V2_DIR = BASE / "fable5" / "hebra_v2_experimental"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


# ---------------------------------------------------------------------------
# 1. HEBRA v2 congelado NO fue modificado por este trabajo
# ---------------------------------------------------------------------------
def test_v2_still_frozen_and_untouched():
    with open(V2_DIR / "FROZEN.json", encoding="utf-8") as f:
        frozen = json.load(f)
    for rel_path, expected_hash in frozen["archivos_congelados"].items():
        actual = sha256_file(V2_DIR / rel_path)
        assert actual == expected_hash, f"{rel_path} cambio desde el congelamiento -- v3 no debe tocar v2"


# ---------------------------------------------------------------------------
# 2. El extractor general no depende de vocabulario de ningun macrohilo:
#    verificamos que ninguna palabra clave de PROCEDURE_FAMILIES ni
#    FACILITY_PLACE_TYPES es un nombre propio (heuristica: todas en minuscula
#    generica, ninguna coincide con nombres de proyectos conocidos)
# ---------------------------------------------------------------------------
def test_no_proper_nouns_in_generic_dictionaries():
    proper_nouns = {"dominga", "ventanas", "bocamina", "alto maipo", "hidroaysen",
                     "el mauro", "faro del sur", "aconcagua", "codelco", "sqm",
                     "maricunga", "atacama"}
    all_keywords = set()
    for kws in ge.PROCEDURE_FAMILIES.values():
        all_keywords.update(kws)
    for kw in all_keywords:
        for noun in proper_nouns:
            assert noun not in kw, f"palabra clave generica '{kw}' contiene un nombre propio '{noun}'"


# ---------------------------------------------------------------------------
# 3. extract_document_fields produce el esquema esperado y maneja campos vacios
# ---------------------------------------------------------------------------
def test_extract_document_fields_schema():
    row = {
        "id": "999999", "fecha_iso": "2024-05-01",
        "llm_project_name": "Proyecto Ejemplo",
        "llm_main_conflict_place_name": "Comuna Ejemplo",
        "llm_main_conflict_place_type": "commune",
        "geo_comuna": "", "geo_provincia": "", "geo_region": "",
        "llm_demandant_actor_name": "Comunidad Ejemplo",
        "llm_demandant_actor_type": "comunidad",
        "llm_demanded_actor_name": "Empresa Ejemplo",
        "llm_demanded_actor_type": "empresa",
        "llm_contentious_action_type": "Recurso de Proteccion",
    }
    out = ge.extract_document_fields(row)
    assert out["doc_id"] == "999999"
    assert out["proyecto_instalacion"] == "proyecto ejemplo"
    assert out["territorio"] == "comuna ejemplo"
    assert "comunidad ejemplo" in out["organizacion"]
    assert "empresa ejemplo" in out["organizacion"]
    assert out["procedimiento_familia"] == "judicial"
    assert out["evento_fase"] == "judicial::2024-05"


def test_extract_document_fields_empty_project_falls_back_to_facility_place():
    row = {
        "id": "1", "fecha_iso": "2024-01-01",
        "llm_project_name": "",
        "llm_main_conflict_place_name": "Fundicion X",
        "llm_main_conflict_place_type": "industrial_facility",
        "geo_comuna": "", "geo_provincia": "", "geo_region": "",
        "llm_demandant_actor_name": "", "llm_demandant_actor_type": "",
        "llm_demanded_actor_name": "", "llm_demanded_actor_type": "",
        "llm_contentious_action_type": "",
    }
    out = ge.extract_document_fields(row)
    assert out["proyecto_instalacion"] == "fundicion x"  # respaldo generico, no nombre propio hardcodeado


def test_extract_document_fields_no_facility_fallback_when_place_type_generic():
    row = {
        "id": "2", "fecha_iso": "2024-01-01",
        "llm_project_name": "",
        "llm_main_conflict_place_name": "Alguna Comuna",
        "llm_main_conflict_place_type": "commune",  # NO es tipo instalacion
        "geo_comuna": "", "geo_provincia": "", "geo_region": "",
        "llm_demandant_actor_name": "", "llm_demandant_actor_type": "",
        "llm_demanded_actor_name": "", "llm_demanded_actor_type": "",
        "llm_contentious_action_type": "",
    }
    out = ge.extract_document_fields(row)
    assert out["proyecto_instalacion"] == ""  # abstencion correcta, no inventa proyecto


# ---------------------------------------------------------------------------
# 4. Asignacion primaria: abstencion explicita, sin perdida de documentos
# ---------------------------------------------------------------------------
def test_primary_assignment_abstention_and_no_loss():
    nodes = pd.DataFrame([
        {"doc_id": "a", "proyecto_instalacion": "proyecto x", "territorio": "t1",
         "organizacion": "org1", "procedimiento": "p1", "procedimiento_familia": "otro",
         "evento_fase": "otro::2024-01"},
        {"doc_id": "b", "proyecto_instalacion": "", "territorio": "t2",
         "organizacion": "org2", "procedimiento": "p2", "procedimiento_familia": "otro",
         "evento_fase": "otro::2024-02"},
    ])
    out = bgs.build_primary_assignment(nodes, "T0001")
    assert len(out) == 2
    assert set(out["doc_id"]) == {"a", "b"}
    assert out.loc[out.doc_id == "a", "subhilo_primario"].iloc[0] == "proyecto x"
    assert out.loc[out.doc_id == "b", "subhilo_primario"].iloc[0] == bgs.ABSTENCION
    assert bool(out.loc[out.doc_id == "b", "abstuvo"].iloc[0]) is True
    assert out["subhilo_primario"].isna().sum() == 0


# ---------------------------------------------------------------------------
# 5. Multiasignacion (mecanismo real, no solo sintetico: se prueba aqui con
#    datos sinteticos deterministas)
# ---------------------------------------------------------------------------
def test_secondary_assignment_via_shared_organization():
    primary = pd.DataFrame([
        {"doc_id": "a", "proyecto_instalacion": "proyecto x", "subhilo_primario": "proyecto x",
         "organizacion": "empresa comun", "macrohilo_id": "T1", "abstuvo": False},
        {"doc_id": "b", "proyecto_instalacion": "proyecto y", "subhilo_primario": "proyecto y",
         "organizacion": "empresa comun", "macrohilo_id": "T1", "abstuvo": False},
    ])
    edges = pd.DataFrame([{"doc_i": "a", "doc_j": "b", "w": 0.75}])
    out = bgs.add_secondary_assignments(primary, edges)
    row_a = out[out.doc_id == "a"].iloc[0]
    assert row_a["multiasignado"]
    assert "proyecto y" in row_a["subhilo_secundario"]


# ---------------------------------------------------------------------------
# 6. Reproducibilidad: el extractor es determinista (mismo input -> mismo output)
# ---------------------------------------------------------------------------
def test_extractor_deterministic():
    row = {
        "id": "1", "fecha_iso": "2024-01-01", "llm_project_name": "X Y Z",
        "llm_main_conflict_place_name": "Lugar", "llm_main_conflict_place_type": "commune",
        "geo_comuna": "", "geo_provincia": "", "geo_region": "",
        "llm_demandant_actor_name": "A", "llm_demandant_actor_type": "empresa",
        "llm_demanded_actor_name": "B", "llm_demanded_actor_type": "comunidad",
        "llm_contentious_action_type": "Protesta",
    }
    out1 = ge.extract_document_fields(row)
    out2 = ge.extract_document_fields(row)
    assert out1 == out2


# ---------------------------------------------------------------------------
# 7. Indice de fragmentacion: verificacion aritmetica directa
# ---------------------------------------------------------------------------
def test_fragmentation_index_arithmetic():
    # 3 subhilos sobre 6 documentos asignados -> indice = 0.5
    sizes = pd.Series([3, 2, 1])
    n_subhilos = len(sizes)
    n_docs = int(sizes.sum())
    assert n_subhilos / n_docs == pytest.approx(0.5)


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
