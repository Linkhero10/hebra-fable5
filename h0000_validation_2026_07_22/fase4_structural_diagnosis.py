# -*- coding: utf-8 -*-
"""
Fase 4: diagnostico estructural de H0000 usando (a) la validacion integrada
post-arbitraje y (b) los addenda de topologia ya generados (puentes, satelites,
heterogeneidad, DSU vs comunidades, grid de Leiden CPM). No recalcula el grafo
ni ejecuta algoritmos de particion nuevos: solo lee artefactos congelados y el
resultado de las Fases 1-3.
"""
import json
import math
from collections import Counter

import pandas as pd

BASE = r"D:\Analisis conflictos\01_proyecto_universidad\09_metodologia\faro_model_research\competition"
DIAG = BASE + r"\fable5\diagnostics_h0000"
OUT = BASE + r"\fable5\h0000_validation_2026_07_22"

df = pd.read_csv(OUT + r"\_intermediate_merged_cases.csv", dtype={"doc_a": str, "doc_b": str})
with open(OUT + r"\H0000_DISAGREEMENTS_ADJUDICATED_2026_07_22.json", encoding="utf-8") as f:
    arb = {c["case_id"]: c["decision_arbitro"] for c in json.load(f)["casos"]}

# decision final post-fase3: si hubo desacuerdo, usa el arbitraje; si no, el consenso (= decision_gpt = decision_claude)
def final_decision(row):
    if row["case_id"] in arb:
        return arb[row["case_id"]]
    assert row["decision_gpt"] == row["decision_claude"]
    return row["decision_gpt"]

df["decision_final"] = df.apply(final_decision, axis=1)

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


def stats_for(mask_col_or_series, label, base=df):
    if isinstance(mask_col_or_series, str):
        sub = base[base[mask_col_or_series] == True]
    else:
        sub = base[mask_col_or_series]
    n = len(sub)
    if n == 0:
        return {"grupo": label, "N": 0}
    strict = sub["decision_final"].isin(STRICT).sum()
    broad = sub["decision_final"].isin(BROAD).sum()
    lo_s, hi_s = wilson_ci(strict, n)
    lo_b, hi_b = wilson_ci(broad, n)
    return {
        "grupo": label, "N": n,
        "pct_estricto_final": round(strict / n, 4), "ic95_estricto": [round(lo_s, 4), round(hi_s, 4)],
        "pct_amplio_final": round(broad / n, 4), "ic95_amplio": [round(lo_b, 4), round(hi_b, 4)],
    }


post_arb_rows = [stats_for(pd.Series([True] * len(df)), "TOTAL_104_post_arbitraje")]
for estrato, sub in df.groupby("estrato"):
    post_arb_rows.append(stats_for(df["estrato"] == estrato, f"estrato={estrato}"))
for algo in ["louvain", "leiden_cpm", "leiden_mod", "infomap"]:
    col = f"intra_{algo}"
    post_arb_rows.append(stats_for(df[col] == True, f"{algo}:intra"))
    post_arb_rows.append(stats_for(df[col] == False, f"{algo}:inter"))
post_arb_rows.append(stats_for(df["puente_estructural"] == True, "arista_es_puente_estructural"))
post_arb_rows.append(stats_for((df["tiene_arista_directa"] == True) & (df["puente_estructural"] != True), "arista_no_puente"))
post_arb_rows.append(stats_for(df["tiene_arista_directa"] == False, "sin_arista_directa_transitivo"))

# ---------------------------------------------------------------------------
# Interpretabilidad de comunidades: objeto dominante por comunidad (de H0000_05)
# ---------------------------------------------------------------------------
part = pd.read_csv(DIAG + r"\H0000_05_PARTITION_COMPARISON.csv")
comunidades_interpretables = {}
for _, row in part.iterrows():
    try:
        tops = json.loads(row["comunidades_top"].replace("'", '"'))
    except Exception:
        tops = []
    comunidades_interpretables[row["algoritmo"]] = {
        "n_comunidades": int(row["n_comunidades"]),
        "top5_objetos": [t.get("objeto_top") for t in tops],
        "top5_tamanos": [t.get("size") for t in tops],
        "top5_territorios_distintos": [t.get("territorios_distintos") for t in tops],
    }

# ---------------------------------------------------------------------------
# Evidencia de puentes / satelites / heterogeneidad (addenda ya generados)
# ---------------------------------------------------------------------------
with open(DIAG + r"\H0000_12_ADDENDUM_BRIDGE_DAMAGE_PROFILE.json", encoding="utf-8") as f:
    bridge_profile = json.load(f)
with open(DIAG + r"\H0000_13_ADDENDUM_SATELLITE_DEFINITIONS.json", encoding="utf-8") as f:
    satellites = json.load(f)
with open(DIAG + r"\H0000_14_ADDENDUM_HETEROGENEITY_BASELINE.json", encoding="utf-8") as f:
    heterogeneity = json.load(f)
with open(DIAG + r"\H0000_15_ADDENDUM_DSU_VS_COMMUNITY_ROBUSTNESS.json", encoding="utf-8") as f:
    dsu_robustness = json.load(f)

diagnosis = {
    "post_arbitraje_por_grupo": post_arb_rows,
    "comunidades_interpretables_objeto_dominante": comunidades_interpretables,
    "evidencia_puentes": {
        "puentes_totales": 23,
        "puentes_w_menor_050": 15,
        "pares_muestra_estrato_puente_n": 20,
        "pct_estricto_consenso_estrato_puente": 0.80,
        "pct_amplio_consenso_estrato_puente": 1.00,
        "lectura": "Los 23 puentes estructurales (aristas cuya remocion desconecta el grafo) NO concentran relaciones solo tematicas: en la muestra ciega, el 80% de los pares en estrato puente fueron juzgados mismo_proceso_especifico por consenso GPT-Claude y el 100% al menos mismo_macroproceso. Los puentes son, en su mayoria, pares de documentos casi-duplicados o de continuidad directa del mismo evento (ver top-3 por dano: 1938-1943, 1108-1943, 1943-1945, todos del cluster de bloqueo de enero 2024), no enlaces espurios de bajo peso.",
    },
    "bridge_damage_profile_resumen": {
        "pares_dependientes_de_puentes": bridge_profile["pares_dependientes_totales"],
        "pares_con_un_solo_puente_separador": bridge_profile["pares_con_UN_solo_puente_como_separador"],
        "pares_que_requieren_cadena_de_2_o_mas_puentes": bridge_profile["pares_que_requieren_2_o_mas_puentes_en_su_camino"],
        "concentracion_top3_puentes_pct": bridge_profile["concentracion_top3_puentes_pct_de_pares_de_unico_separador"],
    },
    "satelites": satellites,
    "heterogeneidad_transitiva": heterogeneity,
    "dsu_vs_comunidades": dsu_robustness,
}

with open(OUT + r"\_fase4_structural_evidence.json", "w", encoding="utf-8") as f:
    json.dump(diagnosis, f, ensure_ascii=False, indent=2, default=str)

print("[OK] Fase 4 evidencia estructural escrita en _fase4_structural_evidence.json")
for r in post_arb_rows:
    print(r)
