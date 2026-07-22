# Fase 3B - Verificacion de preservacion v1 antes del diagnostico H0000.
import hashlib
import importlib
import json
import subprocess
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
man = json.loads((BASE / "outputs/F4_MANIFEST.json").read_text(encoding="utf-8"))
files = {k.replace("\\", "/"): v for k, v in man["files"].items()}

result = {"git_head": subprocess.run(
    ["git", "rev-parse", "HEAD"], cwd=BASE, capture_output=True, text=True
).stdout.strip()}

checks = {}
for f in [
    "outputs/f2b_idf_v2_L2_threads.csv",
    "outputs/f2b_idf_v2_L2_edges.csv",
    "outputs/f2b_idf_v2_L2_threads_summary.json",
    "outputs/f1v2_referents.csv",
]:
    cur = hashlib.sha256((BASE / f).read_bytes()).hexdigest()
    reg = files.get(f)
    checks[f] = {"ok": cur == reg, "cur": cur[:16], "reg": (reg or "")[:16]}
result["hash_checks"] = checks

libs = {}
for m in ["networkx", "scipy", "igraph", "leidenalg", "infomap"]:
    try:
        importlib.import_module(m)
        libs[m] = True
    except ImportError:
        libs[m] = False
result["libs"] = libs
print(json.dumps(result, indent=1))
