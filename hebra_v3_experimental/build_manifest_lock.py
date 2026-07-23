# -*- coding: utf-8 -*-
"""Manifest + lock de HEBRA v3 EXPERIMENTAL. Verifica ademas, por hash,
que hebra_v2_experimental sigue exactamente como se congelo."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
V2_DIR = HERE.parent / "hebra_v2_experimental"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


with open(V2_DIR / "FROZEN.json", encoding="utf-8") as f:
    frozen = json.load(f)
v2_check = {}
for rel_path, expected in frozen["archivos_congelados"].items():
    actual = sha256_file(V2_DIR / rel_path)
    v2_check[rel_path] = {"coincide": actual == expected, "sha256_actual": actual}

DELIVERABLES = [
    "GENERAL_EXTRACTOR_DESIGN_2026_07_23.md",
    "OUT_OF_SAMPLE_VALIDATION_V3_2026_07_23.md",
    "README.md",
    "src/general_extractor.py",
    "src/build_general_subthreads.py",
    "src/run_v3_validation.py",
    "tests/test_v3.py",
    "artifacts/v3_validation_summary.json",
    "artifacts/v3_node_assignment_all_threads.csv",
]

manifest = {
    "generated_by": "hebra_v3_experimental/build_manifest_lock.py",
    "v2_congelado_intacto": all(c["coincide"] for c in v2_check.values()),
    "v2_verificacion_detalle": v2_check,
    "files": {name: sha256_file(HERE / name) for name in DELIVERABLES if (HERE / name).exists()},
    "faltantes": [name for name in DELIVERABLES if not (HERE / name).exists()],
}
with open(HERE / "MANIFEST_V3.json", "w", encoding="utf-8") as f:
    json.dump(manifest, f, ensure_ascii=False, indent=2)

lock = {
    "experimento": "hebra_v3_experimental_extractor_general",
    "v2_no_modificado": manifest["v2_congelado_intacto"],
    "reglas_manuales_por_macrohilo_usadas": False,
    "fuente_de_las_5_categorias": "columnas llm_*/geo_* ya extraidas para todo el corpus (3742 docs), no vocabulario especifico de ningun hilo",
    "hilos_evaluados": 19,
    "cobertura_h0000": "ver artifacts/v3_validation_summary.json",
    "cobertura_promedio_fuera_de_muestra": "ver artifacts/v3_validation_summary.json",
    "pureza_validada_por_adjudicacion_ciega": False,
    "superioridad_v3_sobre_v2_declarada": False,
    "superioridad_v3_sobre_ftd_declarada": False,
    "nota": "v3 mejora cobertura fuera de muestra respecto a v2 (0% -> ~98.8% promedio) pero produce subhilos mas fragmentados en los mismos hilos conocidos, sin validacion de pureza contra gold. Ver OUT_OF_SAMPLE_VALIDATION_V3_2026_07_23.md.",
}
with open(HERE / "EXPERIMENT_LOCK_V3.json", "w", encoding="utf-8") as f:
    json.dump(lock, f, ensure_ascii=False, indent=2)

print("Manifest y lock de v3 escritos. v2 intacto:", manifest["v2_congelado_intacto"])
