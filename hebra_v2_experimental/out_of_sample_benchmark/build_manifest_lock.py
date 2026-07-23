# -*- coding: utf-8 -*-
"""Manifest + lock de esta carpeta (validacion fuera de muestra + spec FTD).
Solo lee/escribe dentro de out_of_sample_benchmark/. Verifica ademas que
HEBRA v2 sigue congelado (mismos hashes que ../FROZEN.json)."""
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "src"))
import verify_frozen  # noqa: E402

verify_frozen.assert_frozen()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


DELIVERABLES = [
    "OUT_OF_SAMPLE_BENCHMARK_REPORT.md",
    "FTD_HEBRA_COMMON_BENCHMARK_SPEC.md",
    "README.md",
    "src/prepare_thread_inputs.py",
    "src/run_benchmark.py",
    "src/compare_with_ftd_skeleton.py",
    "artifacts/out_of_sample_summary.json",
    "artifacts/out_of_sample_node_assignment.csv",
]

manifest = {
    "generated_by": "out_of_sample_benchmark/build_manifest_lock.py",
    "hebra_v2_frozen_verificado": True,
    "files": {name: sha256_file(HERE / name) for name in DELIVERABLES if (HERE / name).exists()},
    "faltantes": [name for name in DELIVERABLES if not (HERE / name).exists()],
}
with open(HERE / "MANIFEST_OUT_OF_SAMPLE.json", "w", encoding="utf-8") as f:
    json.dump(manifest, f, ensure_ascii=False, indent=2)

lock = {
    "experimento": "hebra_v2_out_of_sample_benchmark",
    "hebra_v2_experimental_congelado": True,
    "reglas_nuevas_anadidas_al_diccionario": False,
    "hilos_evaluados": 18,
    "criterio_seleccion": ">=15 documentos, excluyendo H0000",
    "cobertura_observada": "0% en 18/18 hilos (ver OUT_OF_SAMPLE_BENCHMARK_REPORT.md)",
    "ftd_benchmark_ejecutado": False,
    "ftd_benchmark_gold_ciego_ejecutado": False,
    "superioridad_hebra_declarada": False,
    "superioridad_ftd_declarada": False,
}
with open(HERE / "EXPERIMENT_LOCK_OUT_OF_SAMPLE.json", "w", encoding="utf-8") as f:
    json.dump(lock, f, ensure_ascii=False, indent=2)

print("manifest y lock de out_of_sample_benchmark escritos. HEBRA v2 congelado: verificado.")
