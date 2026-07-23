# -*- coding: utf-8 -*-
"""
Fase 1-2: Auditoria e integracion de adjudicaciones GPT-5.6 y Claude Sonnet 5
sobre H0000, cruzadas con la clave sellada y las metricas de grafo.

No modifica: hoja ciega, clave sellada, respuestas originales de los modelos.
Solo LEE esos artefactos y ESCRIBE nuevos archivos en esta carpeta
(fable5/h0000_validation_2026_07_22/).
"""
import json
import math
from collections import Counter, defaultdict

import numpy as np
import pandas as pd
from sklearn.metrics import cohen_kappa_score, confusion_matrix

BASE = r"D:\Analisis conflictos\01_proyecto_universidad\09_metodologia\faro_model_research\competition"
DIAG = BASE + r"\fable5\diagnostics_h0000"
PKG = BASE + r"\PAQUETE_VALIDACION_MULTI_IA_COMPLETO_2026_07_22"
OUT = BASE + r"\fable5\h0000_validation_2026_07_22"

CATS = ["mismo_proceso_especifico", "mismo_macroproceso",
        "relacionado_tematicamente", "no_relacionado", "indeterminado"]

# ---------------------------------------------------------------------------
# 1. Carga de artefactos (solo lectura)
# ---------------------------------------------------------------------------
with open(DIAG + r"\H0000_08_BLIND_REVIEW_SHEET.json", encoding="utf-8") as f:
    sheet = json.load(f)

with open(DIAG + r"\H0000_09_BLIND_KEY_DO_NOT_OPEN.json", encoding="utf-8") as f:
    key = json.load(f)["clave"]

with open(PKG + r"\RESPUESTA_HEBRA_GPT_5_6_2026_07_22.json", encoding="utf-8") as f:
    gpt_raw = json.load(f)

with open(PKG + r"\RESPUESTA_HEBRA_CLAUDE_SONNET_5_2026_07_22.json", encoding="utf-8") as f:
    claude_raw = json.load(f)

with open(PKG + r"\RESPUESTA_HEBRA_GEMINI_2026_07_22.json", encoding="utf-8") as f:
    gemini_raw = json.load(f)  # solo se referencia como artefacto historico, NO se usa como voto

node_metrics = pd.read_csv(DIAG + r"\H0000_02_NODE_METRICS.csv", dtype={"doc_id": str})
node_metrics = node_metrics.set_index("doc_id")

edge_metrics = pd.read_csv(DIAG + r"\H0000_03_EDGE_METRICS.csv", dtype={"doc_i": str, "doc_j": str})
edge_lookup = {}
for _, row in edge_metrics.iterrows():
    edge_lookup[frozenset((row["doc_i"], row["doc_j"]))] = row

# ---------------------------------------------------------------------------
# 2. Verificacion de conteos (obligatoria antes de cualquier calculo)
# ---------------------------------------------------------------------------
def verify_104(name, cases):
    ids = [c["case_id"] for c in cases]
    assert len(ids) == 104, f"{name}: se esperaban 104 casos, hay {len(ids)}"
    assert len(set(ids)) == 104, f"{name}: hay case_id duplicados"
    expected = {f"H{n:03d}" for n in range(104)}
    assert set(ids) == expected, f"{name}: ids no coinciden con H000-H103: {expected ^ set(ids)}"
    for c in cases:
        assert c["decision"] in CATS, f"{name} {c['case_id']}: decision invalida {c['decision']}"
        assert c["confidence"] in {"alta", "media", "baja"}, f"{name} {c['case_id']}: confidence invalida"
    return True

verify_104("GPT-5.6", gpt_raw["cases"])
verify_104("Claude Sonnet 5", claude_raw["cases"])
verify_104("Gemini (historico, no usado como voto)", gemini_raw["cases"])
assert len(sheet["items"]) == 104, "hoja ciega no tiene 104 items"
assert set(key.keys()) == {f"H{n:03d}" for n in range(104)}, "clave sellada no cubre H000-H103"
print("[OK] Fase 1.1: 104/104 casos sin duplicados en GPT-5.6, Claude y Gemini (historico); "
      "104 items en hoja ciega; 104 entradas en la clave sellada.")

# ---------------------------------------------------------------------------
# 3. Indexado por case_id
# ---------------------------------------------------------------------------
gpt = {c["case_id"]: c for c in gpt_raw["cases"]}
claude = {c["case_id"]: c for c in claude_raw["cases"]}
gemini = {c["case_id"]: c for c in gemini_raw["cases"]}
sheet_items = {it["item_id"]: it for it in sheet["items"]}

ALGOS = ["comunidad_louvain", "comunidad_leiden_cpm", "comunidad_leiden_mod", "comunidad_infomap"]
ALGO_SHORT = {"comunidad_louvain": "louvain", "comunidad_leiden_cpm": "leiden_cpm",
              "comunidad_leiden_mod": "leiden_mod", "comunidad_infomap": "infomap"}

records = []
for cid in sorted(key.keys(), key=lambda x: int(x[1:])):
    k = key[cid]
    a, b = k["a"], k["b"]
    g = gpt[cid]
    c = claude[cid]
    it = sheet_items[cid]
    # doc ids from the blind sheet itself (must match the key's a/b, sanity check)
    doc_a_id = str(it["doc_a"]["id"])
    doc_b_id = str(it["doc_b"]["id"])
    assert {doc_a_id, doc_b_id} == {a, b}, f"{cid}: doc ids de la hoja ({doc_a_id},{doc_b_id}) no calzan con la clave ({a},{b})"

    rec = {
        "case_id": cid,
        "doc_a": a, "doc_b": b,
        "estrato": k["estrato"], "detalle": k["detalle"],
        "decision_gpt": g["decision"], "confidence_gpt": g["confidence"],
        "decision_claude": c["decision"], "confidence_claude": c["confidence"],
        "decision_gemini_historico": gemini[cid]["decision"],
    }

    # intra/inter por CADA algoritmo (no solo el que definio el estrato de muestreo)
    na = node_metrics.loc[a] if a in node_metrics.index else None
    nb = node_metrics.loc[b] if b in node_metrics.index else None
    for col in ALGOS:
        short = ALGO_SHORT[col]
        if na is not None and nb is not None:
            rec[f"intra_{short}"] = bool(na[col] == nb[col])
        else:
            rec[f"intra_{short}"] = None

    # metadatos de arista (si existe arista directa; muchos pares "largo"/inter son transitivos, sin arista)
    e = edge_lookup.get(frozenset((a, b)))
    if e is not None:
        rec["tiene_arista_directa"] = True
        rec["w"] = float(e["w"])
        rec["s_ref"] = float(e["s_ref"])
        rec["s_emb"] = float(e["s_emb"])
        rec["dias"] = float(e["dias"])
        rec["largo"] = bool(e["largo"])
        rec["puente_estructural"] = bool(e["puente"])
        rec["embeddedness"] = float(e["embeddedness"])
        rec["edge_betweenness"] = float(e["edge_betweenness"])
        rec["idf_max_ref_compartido"] = None if pd.isna(e["idf_max_ref_compartido"]) else float(e["idf_max_ref_compartido"])
    else:
        rec["tiene_arista_directa"] = False
        for fld in ["w", "s_ref", "s_emb", "dias", "largo", "puente_estructural",
                    "embeddedness", "edge_betweenness", "idf_max_ref_compartido"]:
            rec[fld] = None

    records.append(rec)

df = pd.DataFrame(records)

# ---------------------------------------------------------------------------
# 4. Distribuciones por modelo
# ---------------------------------------------------------------------------
dist_gpt = Counter(df["decision_gpt"])
dist_claude = Counter(df["decision_claude"])
dist_gemini = Counter(df["decision_gemini_historico"])

# ---------------------------------------------------------------------------
# 5. Acuerdo, kappa, matriz de confusion (SOLO GPT vs Claude; Gemini excluido como voto valido)
# ---------------------------------------------------------------------------
y_gpt = df["decision_gpt"].tolist()
y_claude = df["decision_claude"].tolist()

agreement_mask = df["decision_gpt"] == df["decision_claude"]
pct_agreement = float(agreement_mask.mean())
kappa = float(cohen_kappa_score(y_gpt, y_claude, labels=CATS))

cm = confusion_matrix(y_gpt, y_claude, labels=CATS)
cm_df = pd.DataFrame(cm, index=[f"gpt_{c}" for c in CATS], columns=[f"claude_{c}" for c in CATS])

disagreements = df.loc[~agreement_mask, ["case_id", "doc_a", "doc_b", "estrato", "detalle",
                                          "decision_gpt", "confidence_gpt",
                                          "decision_claude", "confidence_claude"]].copy()

print(f"[OK] Fase 1.2: acuerdo GPT-Claude = {pct_agreement:.4f} ({agreement_mask.sum()}/104); "
      f"Cohen's kappa = {kappa:.4f}; desacuerdos = {(~agreement_mask).sum()}")

# ---------------------------------------------------------------------------
# 6. Guardar integrado (Fase 1) -- el df completo se usara tambien en Fase 2/3
# ---------------------------------------------------------------------------
df.to_csv(OUT + r"\_intermediate_merged_cases.csv", index=False, encoding="utf-8-sig")

integrated = {
    "generated_from": {
        "hoja_ciega": "fable5/diagnostics_h0000/H0000_08_BLIND_REVIEW_SHEET.json",
        "clave_sellada": "fable5/diagnostics_h0000/H0000_09_BLIND_KEY_DO_NOT_OPEN.json",
        "gpt": "PAQUETE_VALIDACION_MULTI_IA_COMPLETO_2026_07_22/RESPUESTA_HEBRA_GPT_5_6_2026_07_22.json",
        "claude": "PAQUETE_VALIDACION_MULTI_IA_COMPLETO_2026_07_22/RESPUESTA_HEBRA_CLAUDE_SONNET_5_2026_07_22.json",
        "gemini_historico_no_usado_como_voto": "PAQUETE_VALIDACION_MULTI_IA_COMPLETO_2026_07_22/RESPUESTA_HEBRA_GEMINI_2026_07_22.json",
    },
    "verificacion_conteos": {
        "gpt_n": len(gpt_raw["cases"]), "claude_n": len(claude_raw["cases"]),
        "gemini_n": len(gemini_raw["cases"]), "hoja_n": len(sheet["items"]), "clave_n": len(key),
        "duplicados": False, "ausencias": False,
    },
    "distribucion_gpt": dict(dist_gpt),
    "distribucion_claude": dict(dist_claude),
    "distribucion_gemini_historico": dict(dist_gemini),
    "acuerdo_porcentual_gpt_claude": pct_agreement,
    "cohen_kappa_gpt_claude": kappa,
    "matriz_confusion_gpt_claude": cm_df.to_dict(),
    "n_desacuerdos": int((~agreement_mask).sum()),
    "desacuerdos": disagreements.to_dict(orient="records"),
    "casos": df.to_dict(orient="records"),
}

with open(OUT + r"\H0000_VALIDATION_INTEGRATED_2026_07_22.json", "w", encoding="utf-8") as f:
    json.dump(integrated, f, ensure_ascii=False, indent=2, default=str)

cm_df.to_csv(OUT + r"\_confusion_matrix_gpt_claude.csv", encoding="utf-8-sig")
disagreements.to_csv(OUT + r"\_disagreements_raw.csv", index=False, encoding="utf-8-sig")

print("[OK] Escrito H0000_VALIDATION_INTEGRATED_2026_07_22.json")
print("distribucion GPT:", dict(dist_gpt))
print("distribucion Claude:", dict(dist_claude))
print("distribucion Gemini (historico):", dict(dist_gemini))
