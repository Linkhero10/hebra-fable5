# -*- coding: utf-8 -*-
"""
Fase 2: resultados por escala (estricta/amplia) y por estrato/algoritmo.
Lee el CSV intermedio producido por fase1_2_integrate.py (no vuelve a tocar
la hoja ciega, la clave ni las respuestas originales).
"""
import json
import math
from collections import Counter

import numpy as np
import pandas as pd

BASE = r"D:\Analisis conflictos\01_proyecto_universidad\09_metodologia\faro_model_research\competition"
OUT = BASE + r"\fable5\h0000_validation_2026_07_22"

df = pd.read_csv(OUT + r"\_intermediate_merged_cases.csv", dtype={"doc_a": str, "doc_b": str})

STRICT = {"mismo_proceso_especifico"}
BROAD = {"mismo_proceso_especifico", "mismo_macroproceso"}


def wilson_ci(k, n, z=1.96):
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    denom = 1 + z ** 2 / n
    center = (p + z ** 2 / (2 * n)) / denom
    half = (z * math.sqrt((p * (1 - p) / n) + (z ** 2 / (4 * n ** 2)))) / denom
    return (max(0.0, center - half), min(1.0, center + half))


def strict_flag(series):
    return series.isin(STRICT)


def broad_flag(series):
    return series.isin(BROAD)


def tematico_flag(series):
    return series.isin({"relacionado_tematicamente", "no_relacionado", "indeterminado"})


def row_stats(sub, label):
    n = len(sub)
    if n == 0:
        return None
    gpt_strict = strict_flag(sub["decision_gpt"])
    claude_strict = strict_flag(sub["decision_claude"])
    gpt_broad = broad_flag(sub["decision_gpt"])
    claude_broad = broad_flag(sub["decision_claude"])
    consenso_strict = gpt_strict & claude_strict
    consenso_broad = gpt_broad & claude_broad
    union_strict = gpt_strict | claude_strict
    union_broad = gpt_broad | claude_broad
    acuerdo = (sub["decision_gpt"] == sub["decision_claude"])
    solo_tematico_gpt = tematico_flag(sub["decision_gpt"])
    solo_tematico_claude = tematico_flag(sub["decision_claude"])
    solo_tematico_consenso = solo_tematico_gpt & solo_tematico_claude

    disagreement_pairs = Counter()
    for _, r in sub.loc[~acuerdo].iterrows():
        pair = tuple(sorted([r["decision_gpt"], r["decision_claude"]]))
        disagreement_pairs[" vs ".join(pair)] += 1

    def pct_ci(mask):
        k = int(mask.sum())
        p = k / n
        lo, hi = wilson_ci(k, n)
        return {"k": k, "n": n, "pct": round(p, 4), "ic95": [round(lo, 4), round(hi, 4)]}

    return {
        "estrato_o_grupo": label,
        "N": n,
        "positivo_estricto_gpt": pct_ci(gpt_strict),
        "positivo_estricto_claude": pct_ci(claude_strict),
        "positivo_estricto_consenso_ambos": pct_ci(consenso_strict),
        "positivo_estricto_union_alguno": pct_ci(union_strict),
        "positivo_amplio_gpt": pct_ci(gpt_broad),
        "positivo_amplio_claude": pct_ci(claude_broad),
        "positivo_amplio_consenso_ambos": pct_ci(consenso_broad),
        "positivo_amplio_union_alguno": pct_ci(union_broad),
        "acuerdo_gpt_claude": pct_ci(acuerdo),
        "solo_tematico_o_peor_gpt": pct_ci(solo_tematico_gpt),
        "solo_tematico_o_peor_claude": pct_ci(solo_tematico_claude),
        "solo_tematico_o_peor_consenso_ambos": pct_ci(solo_tematico_consenso),
        "distribucion_desacuerdos": dict(disagreement_pairs),
    }


rows = []

# --- Por estrato de muestreo (puente / intra / inter / largo) ---
for estrato, sub in df.groupby("estrato"):
    r = row_stats(sub, f"estrato={estrato}")
    if r:
        rows.append(r)

# --- Por algoritmo (detalle), solo para intra/inter (puente/largo tienen 'detalle' no-algoritmico) ---
for detalle, sub in df.groupby("detalle"):
    r = row_stats(sub, f"detalle={detalle}")
    if r:
        rows.append(r)

# --- Aristas directas vs pares sin arista directa (transitivos) ---
for val, sub in df.groupby("tiene_arista_directa"):
    label = "arista_directa" if val else "sin_arista_directa_transitivo"
    r = row_stats(sub, label)
    if r:
        rows.append(r)

# --- Bridge estructural real (columna 'puente' de edge_metrics) entre quienes SI tienen arista directa ---
sub_edges = df[df["tiene_arista_directa"] == True]
for val, sub in sub_edges.groupby("puente_estructural"):
    label = "arista_es_puente_estructural" if val else "arista_no_es_puente"
    r = row_stats(sub, label)
    if r:
        rows.append(r)

# --- Intra/inter cruzado por CADA algoritmo (no solo el que definio el estrato de muestreo) ---
for algo in ["louvain", "leiden_cpm", "leiden_mod", "infomap"]:
    col = f"intra_{algo}"
    for val, sub in df.groupby(col):
        if pd.isna(val):
            continue
        label = f"{algo}:{'intra' if val else 'inter'}"
        r = row_stats(sub, label)
        if r:
            rows.append(r)

# --- Total general ---
rows.insert(0, row_stats(df, "TOTAL_104"))

out_json_path = OUT + r"\_stratum_stats_full.json"
with open(out_json_path, "w", encoding="utf-8") as f:
    json.dump(rows, f, ensure_ascii=False, indent=2)

# --- CSV plano para el entregable pedido ---
flat_rows = []
for r in rows:
    flat_rows.append({
        "grupo": r["estrato_o_grupo"],
        "N": r["N"],
        "pct_estricto_gpt": r["positivo_estricto_gpt"]["pct"],
        "pct_estricto_claude": r["positivo_estricto_claude"]["pct"],
        "pct_estricto_consenso": r["positivo_estricto_consenso_ambos"]["pct"],
        "ic95_estricto_consenso_lo": r["positivo_estricto_consenso_ambos"]["ic95"][0],
        "ic95_estricto_consenso_hi": r["positivo_estricto_consenso_ambos"]["ic95"][1],
        "pct_amplio_gpt": r["positivo_amplio_gpt"]["pct"],
        "pct_amplio_claude": r["positivo_amplio_claude"]["pct"],
        "pct_amplio_consenso": r["positivo_amplio_consenso_ambos"]["pct"],
        "ic95_amplio_consenso_lo": r["positivo_amplio_consenso_ambos"]["ic95"][0],
        "ic95_amplio_consenso_hi": r["positivo_amplio_consenso_ambos"]["ic95"][1],
        "acuerdo_gpt_claude_pct": r["acuerdo_gpt_claude"]["pct"],
        "pct_solo_tematico_o_peor_consenso": r["solo_tematico_o_peor_consenso_ambos"]["pct"],
        "distribucion_desacuerdos": "; ".join(f"{k}:{v}" for k, v in r["distribucion_desacuerdos"].items()),
    })

flat_df = pd.DataFrame(flat_rows)
flat_df.to_csv(OUT + r"\H0000_VALIDATION_BY_STRATUM_2026_07_22.csv", index=False, encoding="utf-8-sig")

print("[OK] Fase 2 escrita: H0000_VALIDATION_BY_STRATUM_2026_07_22.csv y _stratum_stats_full.json")
print(flat_df.to_string())
