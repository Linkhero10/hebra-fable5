# -*- coding: utf-8 -*-
# READ-ONLY analysis for critical review. Does not write anything into either repo.
import json
from collections import Counter
from pathlib import Path

import pandas as pd
from sklearn.metrics import cohen_kappa_score

BASE = Path(r"D:\Analisis conflictos\01_proyecto_universidad\09_metodologia\faro_model_research\competition")
V3_BLIND = BASE / "fable5" / "hebra_v3_experimental" / "blind_validation"
REVIEW = BASE / "fable5" / "entrega_hebra_para_revision"

with open(V3_BLIND / "V3B_BLIND_KEY_DO_NOT_OPEN.json", encoding="utf-8") as f:
    key = json.load(f)["clave"]

with open(REVIEW / "V3B_CLAUDE_ADJUDICACION_2026_07_23.json", encoding="utf-8") as f:
    claude = {c["case_id"]: c for c in json.load(f)["cases"]}

with open(REVIEW / "V3B_GPT56_ADJUDICACION_2026_07_23.json", encoding="utf-8") as f:
    gpt = {c["case_id"]: c for c in json.load(f)["cases"]}

assert set(claude.keys()) == set(key.keys()) == set(gpt.keys()), "case_id mismatch"
print(f"n cases: {len(key)} (both adjudicators, sealed key all match)")

rows = []
for cid, k in key.items():
    c = claude[cid]
    g = gpt[cid]
    rows.append({
        "case_id": cid, "macrohilo": k["macrohilo"], "estrato_real": k["estrato"],
        "subhilo_a": k["subhilo_a"], "subhilo_b": k["subhilo_b"],
        "nivel_a_claude": c["nivel_a"], "nivel_b_claude": c["nivel_b_v3"], "conf_claude": c["confidence"],
        "nivel_a_gpt": g["nivel_a"], "nivel_b_gpt": g["nivel_b_v3"], "conf_gpt": g["confidence"],
    })
df = pd.DataFrame(rows)

print("\n=== Distribución nivel_a ===")
print("Claude:", Counter(df.nivel_a_claude))
print("GPT   :", Counter(df.nivel_a_gpt))

print("\n=== Distribución nivel_b_v3 ===")
print("Claude:", Counter(df.nivel_b_claude))
print("GPT   :", Counter(df.nivel_b_gpt))

print("\n=== Acuerdo nivel_a ===")
agree_a = (df.nivel_a_claude == df.nivel_a_gpt)
print(f"acuerdo bruto: {agree_a.mean():.4f} ({agree_a.sum()}/{len(df)})")
labels_a = ["mismo_proceso_especifico","mismo_macroproceso","relacionado_tematicamente","no_relacionado","indeterminado"]
print("kappa:", cohen_kappa_score(df.nivel_a_claude, df.nivel_a_gpt, labels=labels_a))

print("\n=== Acuerdo nivel_b_v3 ===")
agree_b = (df.nivel_b_claude == df.nivel_b_gpt)
print(f"acuerdo bruto: {agree_b.mean():.4f} ({agree_b.sum()}/{len(df)})")
labels_b = ["asignacion_correcta","fragmentacion_falsa","sobreagregacion","abstencion_correcta","abstencion_incorrecta","indeterminado"]
print("kappa:", cohen_kappa_score(df.nivel_b_claude, df.nivel_b_gpt, labels=labels_b))

print("\n=== Matriz de confusion nivel_a (filas=Claude, cols=GPT) ===")
print(pd.crosstab(df.nivel_a_claude, df.nivel_a_gpt))

print("\n=== Matriz de confusion nivel_b (filas=Claude, cols=GPT) ===")
print(pd.crosstab(df.nivel_b_claude, df.nivel_b_gpt))

print("\n=== Cruce estrato_real x nivel_b (Claude) ===")
print(pd.crosstab(df.estrato_real, df.nivel_b_claude))

print("\n=== Cruce estrato_real x nivel_b (GPT) ===")
print(pd.crosstab(df.estrato_real, df.nivel_b_gpt))

print("\n=== Cruce estrato_real x nivel_a (Claude) ===")
print(pd.crosstab(df.estrato_real, df.nivel_a_claude))

print("\n=== Cruce estrato_real x nivel_a (GPT) ===")
print(pd.crosstab(df.estrato_real, df.nivel_a_gpt))

print("\n=== Por macrohilo: acuerdo nivel_a y nivel_b ===")
for m, sub in df.groupby("macrohilo"):
    aa = (sub.nivel_a_claude == sub.nivel_a_gpt).mean()
    ab = (sub.nivel_b_claude == sub.nivel_b_gpt).mean()
    print(f"{m}: n={len(sub)} acuerdo_nivel_a={aa:.3f} acuerdo_nivel_b={ab:.3f}")

# --- CLAVE: cuantos pares inter_subhilo (v3 los separo) fueron juzgados
# mismo_proceso_especifico por CADA modelo (candidatos reales a fragmentacion_falsa,
# independientemente de si el modelo etiqueto nivel_b como tal) ---
print("\n=== inter_subhilo: nivel_a = mismo_proceso_especifico (candidato real a fragmentacion falsa) ===")
inter = df[df.estrato_real == "inter_subhilo"]
print("n inter_subhilo:", len(inter))
print("Claude dice mismo_proceso_especifico en inter_subhilo:", (inter.nivel_a_claude=="mismo_proceso_especifico").sum(), "/", len(inter))
print("  de esos, cuantos etiqueto 'fragmentacion_falsa' en nivel_b:",
      ((inter.nivel_a_claude=="mismo_proceso_especifico") & (inter.nivel_b_claude=="fragmentacion_falsa")).sum())
print("GPT dice mismo_proceso_especifico en inter_subhilo:", (inter.nivel_a_gpt=="mismo_proceso_especifico").sum(), "/", len(inter))
print("  de esos, cuantos etiqueto 'fragmentacion_falsa' en nivel_b:",
      ((inter.nivel_a_gpt=="mismo_proceso_especifico") & (inter.nivel_b_gpt=="fragmentacion_falsa")).sum())

print("\n=== intra_subhilo: nivel_a != mismo_proceso_especifico (candidato real a sobreagregacion) ===")
intra = df[df.estrato_real == "intra_subhilo"]
print("n intra_subhilo:", len(intra))
for name, sub in [("Claude", intra), ("GPT", intra)]:
    pass
c_not_especifico = intra.nivel_a_claude != "mismo_proceso_especifico"
g_not_especifico = intra.nivel_a_gpt != "mismo_proceso_especifico"
print("Claude dice NO-especifico en intra_subhilo:", c_not_especifico.sum(), "/", len(intra),
      "| de esos, etiqueto sobreagregacion:", (c_not_especifico & (intra.nivel_b_claude=="sobreagregacion")).sum())
print("GPT dice NO-especifico en intra_subhilo:", g_not_especifico.sum(), "/", len(intra),
      "| de esos, etiqueto sobreagregacion:", (g_not_especifico & (intra.nivel_b_gpt=="sobreagregacion")).sum())

df.to_csv(Path(__file__).parent / "crosscheck_table.csv", index=False, encoding="utf-8-sig")
print("\n[OK] tabla completa escrita en crosscheck_table.csv (scratchpad, no en ningun repo)")
