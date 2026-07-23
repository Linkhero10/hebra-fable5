# -*- coding: utf-8 -*-
"""Pruebas de la muestra ciega v3. Nota: el archivo de salida incluye un
timestamp `generated_utc` que cambia en cada corrida por diseno (para
saber cuando se genero); por eso la prueba de reproducibilidad compara el
CONTENIDO sustantivo (pares muestreados, estratificacion), no el hash
crudo del archivo completo."""
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _load_key_pairs():
    with open(HERE / "V3B_BLIND_KEY_DO_NOT_OPEN.json", encoding="utf-8") as f:
        key = json.load(f)["clave"]
    return sorted((v["macrohilo"], v["estrato"], v["a"], v["b"]) for v in key.values())


def test_reproducible_content_same_seed():
    before = _load_key_pairs()
    subprocess.run([sys.executable, str(HERE / "build_blind_sample_v3.py")],
                   check=True, cwd=HERE, capture_output=True)
    after = _load_key_pairs()
    assert before == after, "la misma semilla debe producir exactamente los mismos 52 pares"


def test_52_unique_case_ids():
    with open(HERE / "V3B_BLIND_REVIEW_SHEET.json", encoding="utf-8") as f:
        sheet = json.load(f)
    ids = [it["case_id"] for it in sheet["items"]]
    assert len(ids) == 52
    assert len(set(ids)) == 52
    with open(HERE / "V3B_BLIND_KEY_DO_NOT_OPEN.json", encoding="utf-8") as f:
        key = json.load(f)["clave"]
    assert set(key.keys()) == set(ids)


def test_no_metadata_leak_in_blind_sheet():
    with open(HERE / "V3B_BLIND_REVIEW_SHEET.json", encoding="utf-8") as f:
        sheet = json.load(f)
    for item in sheet["items"]:
        assert set(item.keys()) == {"case_id", "doc_a", "doc_b", "pregunta", "veredicto"}
        assert set(item["doc_a"].keys()) == {"id", "fecha", "titulo", "texto"}


def test_abstencion_only_from_h0002():
    with open(HERE / "V3B_BLIND_KEY_DO_NOT_OPEN.json", encoding="utf-8") as f:
        key = json.load(f)["clave"]
    abst = [v for v in key.values() if v["estrato"] == "abstencion"]
    assert len(abst) > 0
    assert all(v["macrohilo"] == "H0002" for v in abst)


def test_stratum_sizes_per_macrohilo():
    with open(HERE / "V3B_MANIFEST.json", encoding="utf-8") as f:
        manifest = json.load(f)
    for m in ("H0001", "H0002", "H0004"):
        s = manifest["estratificacion"][m]
        assert s["n_intra_muestreadas"] == 8
        assert s["n_inter_muestreadas"] == 8
    assert manifest["estratificacion"]["H0001"]["n_abstencion_muestreadas"] == 0
    assert manifest["estratificacion"]["H0004"]["n_abstencion_muestreadas"] == 0
    assert manifest["estratificacion"]["H0002"]["n_abstencion_muestreadas"] == 4


if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-v"]))
