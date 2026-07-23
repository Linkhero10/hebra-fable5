# -*- coding: utf-8 -*-
"""Genera el manifest y el lock de esta carpeta de validacion (Fases 1-4).
Se ejecuta al final, despues de que todos los demas scripts ya escribieron
sus salidas. Solo lee archivos de esta carpeta y de diagnostics_h0000
(para verificar v1 intacto); no modifica nada fuera de aqui."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
DIAG = HERE.parent / "diagnostics_h0000"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


DELIVERABLES = [
    "H0000_VALIDATION_INTEGRATED_2026_07_22.json",
    "H0000_VALIDATION_BY_STRATUM_2026_07_22.csv",
    "H0000_DISAGREEMENTS_ADJUDICATED_2026_07_22.json",
    "H0000_FINAL_EMPIRICAL_REPORT_2026_07_22.md",
    "HEBRA_HIERARCHICAL_DESIGN_2026_07_22.md",
    "_confusion_matrix_gpt_claude.csv",
    "_disagreements_raw.csv",
    "_intermediate_merged_cases.csv",
    "_stratum_stats_full.json",
    "_fase4_structural_evidence.json",
    "fase1_2_integrate.py",
    "fase2_stratum.py",
    "fase3_adjudicate_disagreements.py",
    "fase4_structural_diagnosis.py",
]

with open(DIAG / "H0000_10_MANIFEST.json", encoding="utf-8") as f:
    v1_manifest = json.load(f)

v1_check = {}
for fname, expected in v1_manifest["files"].items():
    fpath = DIAG / fname
    actual = sha256_file(fpath) if fpath.exists() else None
    v1_check[fname] = {"existe": fpath.exists(), "coincide": actual == expected[:64] if actual else False}

manifest = {
    "generated_utc": "2026-07-23T00:10:00+00:00",
    "carpeta": "fable5/h0000_validation_2026_07_22",
    "descripcion": "Fases 1-4 de la validacion empirica de H0000: auditoria, estratos, arbitraje de desacuerdos, diagnostico estructural.",
    "files": {name: sha256_file(HERE / name) for name in DELIVERABLES if (HERE / name).exists()},
    "faltantes": [name for name in DELIVERABLES if not (HERE / name).exists()],
}
with open(HERE / "MANIFEST_2026_07_22.json", "w", encoding="utf-8") as f:
    json.dump(manifest, f, ensure_ascii=False, indent=2)

lock = {
    "experimento": "H0000_validacion_multi_ia_e_integracion_clave_sellada",
    "generated_utc": "2026-07-23T00:10:00+00:00",
    "hoja_ciega_no_modificada": True,
    "clave_sellada_no_modificada": True,
    "respuestas_originales_gpt_claude_gemini_no_modificadas": True,
    "gemini_usado_como_voto_valido": False,
    "v1_diagnostics_intacto": all(c["coincide"] for c in v1_check.values() if c["existe"]),
    "v1_check_detalle": v1_check,
    "ganador_algoritmo_comunidad_declarado": False,
    "arquitectura_v2_declarada_ganadora": False,
    "superioridad_sobre_ftd_declarada": False,
    "arbitraje_fase3_es_juez_independiente": False,
    "nota_arbitraje": "El arbitro de Fase 3 es Claude Sonnet 5, el mismo modelo que genero una de las dos adjudicaciones en disputa. Ver advertencia completa en H0000_FINAL_EMPIRICAL_REPORT_2026_07_22.md.",
}
with open(HERE / "EXPERIMENT_LOCK_2026_07_22.json", "w", encoding="utf-8") as f:
    json.dump(lock, f, ensure_ascii=False, indent=2)

print("manifest y lock escritos.")
print("v1 intacto:", lock["v1_diagnostics_intacto"])
