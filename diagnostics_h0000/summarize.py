import json
from collections import Counter
from pathlib import Path

OUT = Path(__file__).resolve().parent
txt = (OUT / "H0000_04_TOPOLOGY_REPORT.md").read_text(encoding="utf-8")
d = json.loads(txt[txt.find("{"): txt.rfind("}") + 1])
for k in ("densidad", "grado", "clustering_medio", "diametro", "camino_medio",
          "kcore_max", "docs_kcore_max", "bicomponentes", "articulaciones",
          "pct_largas", "poda_puentes_debiles_tamanos"):
    print(k, ":", d[k])
print("docs_por_ano:", d["docs_por_ano"])
print("dano_top3:", d["chaining"]["dano_por_puente_top10"][:3])
key = json.loads((OUT / "H0000_09_BLIND_KEY_DO_NOT_OPEN.json").read_text(encoding="utf-8"))
print("muestra por estrato:", Counter(v["estrato"] for v in key["clave"].values()))
stab = json.loads((OUT / "H0000_06_STABILITY_REPORT.md").read_text(encoding="utf-8").split("```json")[1].split("```")[0])
for a, s in stab.items():
    print(a, {k: s[k] for k in ("n_comms_median", "seed_ari_mean", "drop5_ari_mean", "drop10_ari_mean", "jitter_ari_mean")})
