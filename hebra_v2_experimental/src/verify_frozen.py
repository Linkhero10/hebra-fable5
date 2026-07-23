# -*- coding: utf-8 -*-
"""
Guardia de congelamiento. Cualquier script que use build_hierarchy.py o
subthread_dictionary.py para un benchmark fuera de muestra DEBE llamar
`assert_frozen()` primero. Si alguien modifico esos archivos despues del
congelamiento (ver ../FROZEN.json), esto falla ruidosamente en vez de
correr silenciosamente contra reglas distintas a las validadas en H0000.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
FROZEN_MANIFEST = HERE.parent / "FROZEN.json"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def assert_frozen() -> None:
    with open(FROZEN_MANIFEST, encoding="utf-8") as f:
        frozen = json.load(f)
    for rel_path, expected_hash in frozen["archivos_congelados"].items():
        actual = sha256_file(HERE.parent / rel_path)
        assert actual == expected_hash, (
            f"CONGELAMIENTO VIOLADO: {rel_path} cambio desde el congelamiento "
            f"({FROZEN_MANIFEST}). Hash esperado {expected_hash}, actual {actual}. "
            "No se puede correr el benchmark fuera de muestra contra un diccionario "
            "o codigo distinto del validado en H0000 sin decirlo explicitamente."
        )


if __name__ == "__main__":
    assert_frozen()
    print("[OK] subthread_dictionary.py y build_hierarchy.py coinciden con FROZEN.json")
