# -*- coding: utf-8 -*-
# READ-ONLY reconstruction. Uses ONLY already-published data (nivel_a answers
# from both models' already-published adjudications, and estrato_real from the
# already-published sealed key). Does not re-read source documents, does not
# form new textual judgments about identity. Writes only to scratchpad.
import json
from pathlib import Path

import pandas as pd

BASE = Path(r"D:\Analisis conflictos\01_proyecto_universidad\09_metodologia\faro_model_research\competition")
V3_BLIND = BASE / "fable5" / "hebra_v3_experimental" / "blind_validation"
REVIEW = BASE / "fable5" / "entrega_hebra_para_revision"

df = pd.read_csv(Path(__file__).parent / "crosscheck_table.csv")

# Also need the abstention-side detail: which of doc_a/doc_b actually abstained
with open(V3_BLIND / "V3B_BLIND_KEY_DO_NOT_OPEN.json", encoding="utf-8") as f:
    key = json.load(f)["clave"]

ABST = "SIN_PROYECTO_INSTALACION_IDENTIFICADO"
BROAD = {"mismo_proceso_especifico", "mismo_macroproceso"}


def reconstruct(row, nivel_a_col):
    estrato = row["estrato_real"]
    a = row[nivel_a_col]
    k = key[row["case_id"]]
    if estrato == "intra_subhilo":
        if a == "mismo_proceso_especifico":
            return "asignacion_correcta"
        elif a == "indeterminado":
            return "indeterminado"
        else:
            return "sobreagregacion"
    elif estrato == "inter_subhilo":
        if a == "mismo_proceso_especifico":
            return "fragmentacion_falsa"
        elif a == "indeterminado":
            return "indeterminado"
        else:
            return "asignacion_correcta"
    else:  # abstencion
        # document-level phenomenon evaluated with a pair-level instrument:
        # report as ambiguous-by-design rather than force a label
        return "requiere_juicio_por_documento_no_por_par"


for model, col_a, col_b in [("claude", "nivel_a_claude", "nivel_b_claude"),
                              ("gpt", "nivel_a_gpt", "nivel_b_gpt")]:
    df[f"nivel_b_reconstruido_{model}"] = df.apply(lambda r: reconstruct(r, col_a), axis=1)
    df[f"coincide_reconstruccion_{model}"] = df[col_b] == df[f"nivel_b_reconstruido_{model}"]

print("=== Cuantos nivel_b PUBLICADOS coinciden con el nivel_b RECONSTRUIDO (a partir del propio nivel_a + estrato real) ===")
for model in ["claude", "gpt"]:
    sub = df[df.estrato_real != "abstencion"]  # abstencion no tiene reconstruccion de pares forzable
    match = sub[f"coincide_reconstruccion_{model}"]
    print(f"{model}: {match.sum()}/{len(sub)} coinciden ({match.mean():.1%})")
    mismatch = sub[~match]
    print(f"  discrepancias por estrato:")
    print(mismatch.groupby("estrato_real").size())
    print(f"  distribucion de lo publicado vs lo reconstruido en las discrepancias:")
    print(mismatch[[f"nivel_b_{model}", f"nivel_b_reconstruido_{model}"]].value_counts())
    print()

print("=== Detalle: casos inter_subhilo con nivel_a=mismo_proceso_especifico (reconstruido=fragmentacion_falsa) pero publicado=asignacion_correcta ===")
for model in ["claude", "gpt"]:
    col_a, col_b = f"nivel_a_{model}", f"nivel_b_{model}"
    sub = df[(df.estrato_real == "inter_subhilo") & (df[col_a] == "mismo_proceso_especifico")]
    print(f"{model}: {len(sub)} casos -> publicado nivel_b:", sub[col_b].value_counts().to_dict())

print()
print("=== Estrato abstencion: detalle completo (requiere lectura de justificacion ya publicada, no nueva) ===")
abst = df[df.estrato_real == "abstencion"]
print(abst[["case_id", "subhilo_a", "subhilo_b", "nivel_a_claude", "nivel_b_claude", "nivel_a_gpt", "nivel_b_gpt"]].to_string())

df.to_csv(Path(__file__).parent / "reconstructed_nivel_b.csv", index=False, encoding="utf-8-sig")
print("\n[OK] tabla escrita en reconstructed_nivel_b.csv (scratchpad, no en ningun repo)")
