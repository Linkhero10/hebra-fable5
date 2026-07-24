# -*- coding: utf-8 -*-
"""FASE 3 — Integracion de las dos adjudicaciones ciegas de FTD.
Se ejecuta SOLO despues de que la segunda adjudicacion este sellada (hash calculado).
Lectura de la clave sellada permitida a partir de este punto.
No modifica ningun repositorio: escribe solo en comparativa/."""
import hashlib
import json
from pathlib import Path

import pandas as pd
from sklearn.metrics import cohen_kappa_score, confusion_matrix

BASE = Path(r"D:\Analisis conflictos\01_proyecto_universidad\09_metodologia\faro_model_research\competition")
OUT = BASE / "comparativa" / "FTD_segunda_adjudicacion_2026_07_23"
ADJ2_PATH = OUT / "FTD_SEGUNDA_ADJUDICACION_CLAUDE_2026_07_23.json"

FTD4 = ["mismo_proceso", "relacionado", "no_relacionado", "indeterminado"]


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


# --- 1. Sellado: hash de la segunda adjudicacion ANTES de abrir la clave ---
adj2_hash = sha(ADJ2_PATH)
with open(ADJ2_PATH, encoding="utf-8") as f:
    adj2_raw = json.load(f)
adj2 = pd.DataFrame(adj2_raw["cases"]).rename(columns={"pair_id": "review_item_id"})
assert len(adj2) == 60 and adj2.review_item_id.nunique() == 60, "la segunda adjudicacion debe tener 60 ids unicos"

# --- 2. Ahora si: clave sellada + primera adjudicacion ---
key = pd.read_csv(BASE / "gpt5.6sol/outputs/private/human_review_answer_key.csv", dtype=str)
adj1 = pd.read_csv(BASE / "gpt5.6sol/validacion/FTD_CORE_EXPERT_AI_ADJUDICATION_BLIND.csv", dtype=str)

df = (key.merge(adj1[["review_item_id", "expert_ai_verdict", "expert_ai_confidence"]], on="review_item_id")
         .merge(adj2, on="review_item_id"))
df = df.rename(columns={"expert_ai_verdict": "v1_gpt", "relacion_ftd4": "v2_claude"})
assert len(df) == 60

print(f"segunda adjudicacion sha256 = {adj2_hash}")
print(f"n casos integrados = {len(df)}\n")

# --- 3. Acuerdo bruto y kappa en la escala ORIGINAL de 4 categorias ---
agree = (df.v1_gpt == df.v2_claude)
kappa = cohen_kappa_score(df.v1_gpt, df.v2_claude, labels=FTD4)
print("=== ACUERDO INTER-ADJUDICADOR (escala FTD original, 4 categorias) ===")
print(f"acuerdo bruto : {agree.mean():.4f} ({agree.sum()}/60)")
print(f"Cohen's kappa : {kappa:.4f}\n")

print("distribucion v1 (GPT-5.6 Thinking):", df.v1_gpt.value_counts().to_dict())
print("distribucion v2 (Claude frio)     :", df.v2_claude.value_counts().to_dict())
print("distribucion v2 escala fina       :", df.relacion_fina5.value_counts().to_dict(), "\n")

print("=== MATRIZ DE CONFUSION (filas v1_gpt, cols v2_claude) ===")
print(pd.crosstab(df.v1_gpt, df.v2_claude), "\n")

# --- 4. Acuerdo por estrato ---
print("=== ACUERDO POR ESTRATO SELLADO ===")
for est, sub in df.groupby("sample_stratum"):
    a = (sub.v1_gpt == sub.v2_claude)
    print(f"  {est:12s} n={len(sub):3d}  acuerdo={a.mean():.3f} ({a.sum()}/{len(sub)})")
    print(f"     v1: {sub.v1_gpt.value_counts().to_dict()}")
    print(f"     v2: {sub.v2_claude.value_counts().to_dict()}")

# --- 5. Acuerdo por tipo de relacion declarada por el sistema ---
print("\n=== ACUERDO POR system_relation ===")
for rel, sub in df.groupby("system_relation"):
    a = (sub.v1_gpt == sub.v2_claude)
    print(f"  {rel:22s} n={len(sub):3d} acuerdo={a.mean():.3f}")

# --- 6. Estrato abstencion: sobreabstencion segun cada adjudicador ---
print("\n=== SOBREABSTENCION (estrato abstention, n=20) ===")
ab = df[df.sample_stratum == "abstention"]
for lab, col in [("v1_gpt", "v1_gpt"), ("v2_claude", "v2_claude")]:
    n_same = (ab[col] == "mismo_proceso").sum()
    print(f"  {lab}: {n_same}/20 juzgados 'mismo_proceso' -> sobreabstencion = {n_same/20:.1%}")
print("  juicio_abstencion explicito de v2:", ab.juicio_abstencion.value_counts().to_dict())

# --- 7. Desacuerdos: concentracion por trayectoria y clasificacion ---
dis = df[~agree].copy()
print(f"\n=== DESACUERDOS: {len(dis)} ===")
print("por estrato:", dis.sample_stratum.value_counts().to_dict())
pares_tray = dis.apply(lambda r: tuple(sorted([str(r.trajectory_id_a), str(r.trajectory_id_b)])), axis=1)
print("concentracion por par de trayectorias (top 6):")
for t, n in pares_tray.value_counts().head(6).items():
    print(f"   {t}: {n}")

# clasificacion determinista parcial (el resto es juicio del agente principal)
def clasifica(r):
    if r.v1_gpt == "indeterminado" or r.v2_claude == "indeterminado":
        return "evidencia_realmente_insuficiente"
    if r.problema_granularidad:
        return "diferencia_macroproceso_vs_proceso_especifico"
    par = {r.v1_gpt, r.v2_claude}
    if par == {"mismo_proceso", "relacionado"}:
        return "insuficiencia_del_codebook_frontera_identidad"
    if par == {"relacionado", "no_relacionado"}:
        return "ambiguedad_textual"
    return "revisar_manualmente"

dis["clasificacion"] = dis.apply(clasifica, axis=1)
print("\nclasificacion de desacuerdos:", dis.clasificacion.value_counts().to_dict())

cols = ["review_item_id", "sample_stratum", "system_relation", "trajectory_id_a", "trajectory_id_b",
        "v1_gpt", "v2_claude", "relacion_fina5", "confianza", "problema_granularidad",
        "riesgo_fragmentacion", "riesgo_sobreagregacion", "clasificacion"]
dis[cols].to_csv(OUT / "FTD_DESACUERDOS_CLASIFICADOS.csv", index=False, encoding="utf-8-sig")
df.to_csv(OUT / "FTD_INTEGRACION_DOS_ADJUDICACIONES.csv", index=False, encoding="utf-8-sig")

resumen = {
    "segunda_adjudicacion_sha256": adj2_hash,
    "n": 60,
    "acuerdo_bruto": round(float(agree.mean()), 4),
    "cohen_kappa_escala_ftd4": round(float(kappa), 4),
    "distribucion_v1_gpt": df.v1_gpt.value_counts().to_dict(),
    "distribucion_v2_claude": df.v2_claude.value_counts().to_dict(),
    "distribucion_v2_fina5": df.relacion_fina5.value_counts().to_dict(),
    "acuerdo_por_estrato": {e: round(float((s.v1_gpt == s.v2_claude).mean()), 4)
                             for e, s in df.groupby("sample_stratum")},
    "sobreabstencion_v1": int((df[df.sample_stratum == "abstention"].v1_gpt == "mismo_proceso").sum()),
    "sobreabstencion_v2": int((df[df.sample_stratum == "abstention"].v2_claude == "mismo_proceso").sum()),
    "n_desacuerdos": int(len(dis)),
    "clasificacion_desacuerdos": dis.clasificacion.value_counts().to_dict(),
}
with open(OUT / "FTD_INTEGRACION_RESUMEN.json", "w", encoding="utf-8") as f:
    json.dump(resumen, f, ensure_ascii=False, indent=2)
print("\n[OK] escritos FTD_INTEGRACION_*.csv/.json en comparativa/")
