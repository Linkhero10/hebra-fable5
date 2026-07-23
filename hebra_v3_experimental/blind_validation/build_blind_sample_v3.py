# -*- coding: utf-8 -*-
"""
Construccion de la muestra ciega estratificada de HEBRA v3 sobre Dominga
(H0001), Fundicion Ventanas (H0002) y Bocamina (H0004).

NO ejecuta ni ajusta el extractor general (general_extractor.py) de nuevo:
usa UNICAMENTE la asignacion ya calculada y congelada en
`hebra_v3_experimental/artifacts/v3_node_assignment_all_threads.csv`
(generada por run_v3_validation.py en el turno anterior). Este script solo
MUESTREA pares desde esa asignacion ya existente y desde las aristas
inducidas de cada hilo (fable5/outputs/f2b_idf_v2_L2_edges.csv, la misma
fuente generica ya usada en el benchmark de v2).

Estratos por macrohilo:
  - intra_subhilo:  ambos documentos con el MISMO subhilo_primario no-abstencion
                    -> prueba SOBREAGREGACION (v3 los junto: es correcto?)
  - inter_subhilo:  ambos con subhilo_primario DISTINTO, ninguno abstencion
                    -> prueba FRAGMENTACION FALSA (v3 los separo: deberian
                       estar juntos?). Se estratifica ademas por similitud
                       lexica de las dos cadenas canonicas (alta/baja) para
                       no sesgar la muestra solo hacia los casos ambiguos.
  - abstencion:     al menos un documento abstuvo (SIN_PROYECTO_INSTALACION_IDENTIFICADO)
                    -> prueba ABSTENCION CORRECTA/INCORRECTA. Solo existe en
                       H0002 (unico de los 3 hilos con documentos abstenidos
                       en esta asignacion; H0001 y H0004 tienen cobertura 100%,
                       ver v3_validation_summary.json) -- se documenta asi,
                       no se fuerza una muestra donde no hay datos.

Semilla fija para reproducibilidad: ver SEED abajo.
"""
from __future__ import annotations

import csv
import hashlib
import json
import random
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

BASE = Path(r"D:\Analisis conflictos\01_proyecto_universidad\09_metodologia\faro_model_research\competition")
V3_ARTIFACTS = BASE / "fable5" / "hebra_v3_experimental" / "artifacts"
EDGES_PATH = BASE / "fable5" / "outputs" / "f2b_idf_v2_L2_edges.csv"
CORPUS = Path(r"D:\Analisis conflictos\01_proyecto_universidad\01_bases_de_datos"
              r"\03_refiltro_api_qwen_y_base_actual\06_base_actual_fusionada_3742_incluidas.csv")
OUT_DIR = Path(__file__).resolve().parent

SEED = 20260781
MACROHILOS = ["H0001", "H0002", "H0004"]
N_INTRA_PER_THREAD = 8
N_INTER_PER_THREAD = 8
N_ABSTENCION_MAX_PER_THREAD = 6
TEXT_CHAR_LIMIT = 6000

ABSTENCION_LABEL = "SIN_PROYECTO_INSTALACION_IDENTIFICADO"


def jaccard(a: str, b: str) -> float:
    sa, sb = set(a.split()), set(b.split())
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


def load_corpus_meta() -> dict:
    meta = {}
    with open(CORPUS, encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            meta[row["id"]] = {
                "fecha": (row.get("fecha_iso") or "")[:10],
                "titulo": (row.get("titulo") or "")[:200],
                "texto": (row.get("contenido_completo") or "")[:TEXT_CHAR_LIMIT],
            }
    return meta


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    rng = random.Random(SEED)
    assignment = pd.read_csv(V3_ARTIFACTS / "v3_node_assignment_all_threads.csv", dtype=str)
    edges_all = pd.read_csv(EDGES_PATH, dtype={"doc_i": str, "doc_j": str})
    edges_all["w"] = edges_all["w"].astype(float)

    sampled = []  # list of dicts: case_id, macrohilo, estrato, doc_a, doc_b, w, subhilo_a, subhilo_b, detalle
    stratum_stats = {}

    for macrohilo in MACROHILOS:
        docs_meta = assignment[assignment.macrohilo_id == macrohilo].set_index("doc_id")
        doc_set = set(docs_meta.index)
        induced = edges_all[edges_all.doc_i.isin(doc_set) & edges_all.doc_j.isin(doc_set)].copy()

        intra_edges, inter_edges, abst_edges = [], [], []
        for _, e in induced.iterrows():
            i, j, w = e["doc_i"], e["doc_j"], float(e["w"])
            si, sj = docs_meta.loc[i, "subhilo_primario"], docs_meta.loc[j, "subhilo_primario"]
            if si == ABSTENCION_LABEL or sj == ABSTENCION_LABEL:
                abst_edges.append((i, j, w, si, sj))
            elif si == sj:
                intra_edges.append((i, j, w, si, sj))
            else:
                inter_edges.append((i, j, w, si, sj))

        # --- intra_subhilo: muestreo aleatorio simple con semilla fija ---
        rng.shuffle(intra_edges)
        chosen_intra = intra_edges[:N_INTRA_PER_THREAD]

        # --- inter_subhilo: estratificar por similitud lexica alta/baja ---
        inter_scored = [(jaccard(si, sj), (i, j, w, si, sj)) for (i, j, w, si, sj) in inter_edges]
        inter_scored.sort(key=lambda x: -x[0])
        n_half = N_INTER_PER_THREAD // 2
        high_sim = [t for _, t in inter_scored[:max(1, len(inter_scored) // 3)]]
        low_sim = [t for _, t in inter_scored[max(1, 2 * len(inter_scored) // 3):]]
        rng.shuffle(high_sim)
        rng.shuffle(low_sim)
        chosen_inter = high_sim[:n_half] + low_sim[:N_INTER_PER_THREAD - n_half]
        if len(chosen_inter) < N_INTER_PER_THREAD:
            remaining = [t for _, t in inter_scored if t not in chosen_inter]
            rng.shuffle(remaining)
            chosen_inter += remaining[:N_INTER_PER_THREAD - len(chosen_inter)]

        # --- abstencion: todas las disponibles hasta el maximo ---
        rng.shuffle(abst_edges)
        chosen_abst = abst_edges[:N_ABSTENCION_MAX_PER_THREAD]

        stratum_stats[macrohilo] = {
            "n_docs": len(doc_set),
            "n_edges_inducidas": len(induced),
            "n_intra_disponibles": len(intra_edges), "n_intra_muestreadas": len(chosen_intra),
            "n_inter_disponibles": len(inter_edges), "n_inter_muestreadas": len(chosen_inter),
            "n_abstencion_disponibles": len(abst_edges), "n_abstencion_muestreadas": len(chosen_abst),
        }

        for estrato, chosen in (("intra_subhilo", chosen_intra),
                                 ("inter_subhilo", chosen_inter),
                                 ("abstencion", chosen_abst)):
            for (i, j, w, si, sj) in chosen:
                sampled.append({
                    "macrohilo": macrohilo, "estrato": estrato,
                    "doc_a": i, "doc_b": j, "w": w,
                    "subhilo_a": si, "subhilo_b": sj,
                })

    # asignar case_id deterministico (orden fijo: por macrohilo, luego estrato, luego doc ids)
    sampled.sort(key=lambda r: (r["macrohilo"], r["estrato"], r["doc_a"], r["doc_b"]))
    for idx, r in enumerate(sampled):
        r["case_id"] = f"V3B{idx:03d}"

    print(f"[OK] {len(sampled)} pares muestreados en total.")
    for m, s in stratum_stats.items():
        print(f"  {m}: {s}")

    # --- construir hoja ciega (con texto completo) y clave sellada ---
    meta = load_corpus_meta()
    sheet_items = []
    key = {}
    for r in sampled:
        a, b = r["doc_a"], r["doc_b"]
        sheet_items.append({
            "case_id": r["case_id"],
            "doc_a": {"id": a, "fecha": meta.get(a, {}).get("fecha", ""),
                      "titulo": meta.get(a, {}).get("titulo", ""),
                      "texto": meta.get(a, {}).get("texto", "")},
            "doc_b": {"id": b, "fecha": meta.get(b, {}).get("fecha", ""),
                      "titulo": meta.get(b, {}).get("titulo", ""),
                      "texto": meta.get(b, {}).get("texto", "")},
            "pregunta": ("nivel_a: mismo_proceso_especifico | mismo_macroproceso | "
                         "relacionado_tematicamente | no_relacionado | indeterminado  ||  "
                         "nivel_b_v3: asignacion_correcta | fragmentacion_falsa | "
                         "sobreagregacion | abstencion_correcta | abstencion_incorrecta | indeterminado"),
            "veredicto": "",
        })
        key[r["case_id"]] = {
            "macrohilo": r["macrohilo"], "estrato": r["estrato"],
            "a": a, "b": b, "w": r["w"],
            "subhilo_a": r["subhilo_a"], "subhilo_b": r["subhilo_b"],
        }

    blind_sheet = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "seed": SEED,
        "fuente": "hebra_v3_experimental/artifacts/v3_node_assignment_all_threads.csv (sin re-ejecutar el extractor)",
        "macrohilos": MACROHILOS,
        "instrucciones": (
            "Revision ciega HEBRA v3. No se revela subhilo, estrato, peso de arista, "
            "macrohilo ni motivo de seleccion. Juzgar identidad procesual y diagnostico "
            "v3 con el texto completo. Adjudicacion EXTERNA; el desarrollador no adjudica."
        ),
        "n_items": len(sheet_items),
        "items": sheet_items,
    }
    sealed_key = {
        "protocolo": {
            "integracion": (
                "1) adjudicadores externos (>=2 IA) completan la hoja sin la clave; "
                "2) se congelan veredictos con hash; 3) solo entonces se cruza con la clave; "
                "4) intra/inter/abstencion por hilo decide fragmentacion_falsa/sobreagregacion/"
                "abstencion correcta o incorrecta; 5) desacuerdos van a arbitraje, igual que en H0000."
            ),
        },
        "seed": SEED,
        "clave": key,
    }

    sheet_path = OUT_DIR / "V3B_BLIND_REVIEW_SHEET.json"
    key_path = OUT_DIR / "V3B_BLIND_KEY_DO_NOT_OPEN.json"
    with open(sheet_path, "w", encoding="utf-8") as f:
        json.dump(blind_sheet, f, ensure_ascii=False, indent=1)
    with open(key_path, "w", encoding="utf-8") as f:
        json.dump(sealed_key, f, ensure_ascii=False, indent=1)

    prompt_path = OUT_DIR / "PROMPT_V3B_ADJUDICACION_2026_07_23.md"
    manifest = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "seed": SEED,
        "n_items": len(sheet_items),
        "estratificacion": stratum_stats,
        "files": {
            "V3B_BLIND_REVIEW_SHEET.json": sha256_file(sheet_path),
            "V3B_BLIND_KEY_DO_NOT_OPEN.json": sha256_file(key_path),
            **({"PROMPT_V3B_ADJUDICACION_2026_07_23.md": sha256_file(prompt_path)}
               if prompt_path.exists() else {}),
        },
        "nota_abstencion": (
            "H0001 (Dominga) y H0004 (Bocamina) tienen cobertura 100% en la asignacion v3 "
            "(cero documentos abstenidos): no aportan pares al estrato 'abstencion' por "
            "construccion, no por omision. Solo H0002 (Fundicion Ventanas) tiene documentos "
            "abstenidos (4 de 148) y por lo tanto es la unica fuente de ese estrato."
        ),
    }
    with open(OUT_DIR / "V3B_MANIFEST.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    print(f"[OK] Hoja ciega, clave sellada y manifest escritos en {OUT_DIR}")


if __name__ == "__main__":
    main()
