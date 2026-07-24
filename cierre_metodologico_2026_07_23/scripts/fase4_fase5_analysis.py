# -*- coding: utf-8 -*-
"""READ-ONLY. Fase 4 (reconstruccion Nivel B con desglose) + insumos Fase 5.
Solo usa etiquetas ya publicadas + clave sellada ya publicada. No adjudica."""
import json
from pathlib import Path
import pandas as pd

BASE = Path(r"D:\Analisis conflictos\01_proyecto_universidad\09_metodologia\faro_model_research\competition")
HERE = Path(__file__).parent
df = pd.read_csv(HERE / "reconstructed_nivel_b.csv")

print("="*70)
print("FASE 4 — TASAS RECONSTRUIDAS vs PUBLICADAS, POR MACROHILO")
print("="*70)

for model in ["claude", "gpt"]:
    print(f"\n--- {model.upper()} ---")
    for m in ["H0001", "H0002", "H0004", "TOTAL"]:
        sub = df if m == "TOTAL" else df[df.macrohilo == m]
        inter = sub[sub.estrato_real == "inter_subhilo"]
        intra = sub[sub.estrato_real == "intra_subhilo"]
        frag = (inter[f"nivel_b_reconstruido_{model}"] == "fragmentacion_falsa").sum()
        over = (intra[f"nivel_b_reconstruido_{model}"] == "sobreagregacion").sum()
        frag_pub = (inter[f"nivel_b_{model}"] == "fragmentacion_falsa").sum()
        over_pub = (intra[f"nivel_b_{model}"] == "sobreagregacion").sum()
        print(f"  {m}: frag reconstruida {frag}/{len(inter)}"
              f" (publicada {frag_pub}/{len(inter)}) | "
              f"sobreagreg reconstruida {over}/{len(intra)} (publicada {over_pub}/{len(intra)})")

print("\n" + "="*70)
print("FASE 5 — INSUMOS: como parte cada sistema los mismos casos")
print("="*70)

# HEBRA v3 subhilos por macrohilo
v3 = pd.read_csv(BASE / "fable5" / "hebra_v3_experimental" / "artifacts" /
                 "v3_node_assignment_all_threads.csv", dtype=str)
ABST = "SIN_PROYECTO_INSTALACION_IDENTIFICADO"
for tid, name in [("H0000", "litio/gobernanza nacional"), ("H0001", "Dominga"),
                  ("H0002", "Ventanas"), ("H0004", "Bocamina")]:
    sub = v3[v3.macrohilo_id == tid]
    con = sub[sub.subhilo_primario != ABST]
    print(f"\nHEBRA v3 {tid} ({name}): {len(sub)} docs, "
          f"{con.subhilo_primario.nunique()} subhilos, {len(sub)-len(con)} abstenciones")

# FTD: que trayectorias cubren esos mismos casos
ftd_dir = BASE / "gpt5.6sol_github_public" / "entrega_ftd_para_revision" / "v1" / "outputs" / "selected"
a = pd.read_csv(ftd_dir / "assignments.csv", dtype={"id": str})
sig = pd.read_csv(ftd_dir / "signatures.csv", dtype={"id": str})
mg = a[a.status == "assigned"].merge(sig, on="id", how="left")

def traj_for_keyword(kw):
    hit = mg[mg["named_phrases"].str.contains(kw, case=False, na=False) |
             mg["places"].str.contains(kw, case=False, na=False)]
    return hit["trajectory_id"].value_counts()

for kw, name in [("dominga", "Dominga"), ("bocamina", "Bocamina"),
                 ("ventanas", "Ventanas"), ("maricunga", "Maricunga")]:
    vc = traj_for_keyword(kw)
    print(f"\nFTD — docs que mencionan '{kw}' ({name}), por trayectoria (top 6):")
    print("   " + ", ".join(f"{t}:{n}" for t, n in vc.head(6).items()) +
          f"   [total {vc.sum()} docs en {len(vc)} trayectorias]")

# Cuanto del corpus asignado esta en las 3 trayectorias mas grandes
tot = len(mg)
print(f"\nFTD: {tot} docs asignados en {mg.trajectory_id.nunique()} trayectorias")
print("  top5 trayectorias:", mg.trajectory_id.value_counts().head(5).to_dict())
