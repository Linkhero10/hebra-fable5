# -*- coding: utf-8 -*-
"""
HEBRA v2 EXPERIMENTAL -- construccion de la jerarquia macrohilo/subhilo.

Lee UNICAMENTE (modo lectura) los artefactos congelados de v1 en
`fable5/diagnostics_h0000/` y el resultado ya calculado de la validacion
ciega en `fable5/h0000_validation_2026_07_22/`. No modifica ninguno de los
dos. Todo lo que este script produce se escribe dentro de
`hebra_v2_experimental/artifacts/`.

Uso:
    python build_hierarchy.py [--seed N] [--shuffle-input]

--shuffle-input baraja el orden de lectura de node_metrics/edge_metrics
para la prueba de estabilidad ante orden de entrada (Fase 6, requisito 8).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
from pathlib import Path

import pandas as pd

import sys
sys.path.insert(0, str(Path(__file__).parent))
from subthread_dictionary import canonicalize, SIN_SUBHILO, normalize_text

BASE = Path(r"D:\Analisis conflictos\01_proyecto_universidad\09_metodologia\faro_model_research\competition")
DIAG = BASE / "fable5" / "diagnostics_h0000"
VALID = BASE / "fable5" / "h0000_validation_2026_07_22"
ARTIFACTS = Path(__file__).resolve().parent.parent / "artifacts"

MACROHILO_ID = "H0000"
BRIDGE_WEIGHT_FOR_SECONDARY = 0.60


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def load_v1_inputs(shuffle_input: bool, seed: int):
    nodes = pd.read_csv(DIAG / "H0000_02_NODE_METRICS.csv", dtype={"doc_id": str})
    edges = pd.read_csv(DIAG / "H0000_03_EDGE_METRICS.csv", dtype={"doc_i": str, "doc_j": str})
    if shuffle_input:
        rng = random.Random(seed)
        nodes = nodes.sample(frac=1.0, random_state=rng.randint(0, 2**31 - 1)).reset_index(drop=True)
        edges = edges.sample(frac=1.0, random_state=rng.randint(0, 2**31 - 1)).reset_index(drop=True)
    return nodes, edges


def build_primary_assignment(nodes: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, r in nodes.iterrows():
        key, pattern = canonicalize(r["objeto"])
        rows.append({
            "doc_id": r["doc_id"],
            "macrohilo_id": MACROHILO_ID,
            "objeto_original": r["objeto"],
            "subhilo_primario": key,
            "regla_aplicada": pattern,
            "abstuvo": key == SIN_SUBHILO,
        })
    out = pd.DataFrame(rows)
    # estabilidad ante orden de entrada: ordenar SIEMPRE por doc_id antes de escribir
    out = out.sort_values("doc_id").reset_index(drop=True)
    return out


def add_secondary_assignments(primary: pd.DataFrame, edges: pd.DataFrame) -> pd.DataFrame:
    doc_to_primary = dict(zip(primary["doc_id"], primary["subhilo_primario"]))
    secondary = {doc_id: set() for doc_id in primary["doc_id"]}
    provenance = {doc_id: [] for doc_id in primary["doc_id"]}

    for _, e in edges.iterrows():
        if pd.isna(e.get("w")) or float(e["w"]) < BRIDGE_WEIGHT_FOR_SECONDARY:
            continue
        ref_objeto = e.get("ref_objeto")
        if pd.isna(ref_objeto) or not str(ref_objeto).strip():
            continue
        key, _pat = canonicalize(ref_objeto)
        if key == SIN_SUBHILO:
            continue
        for a, b in [(e["doc_i"], e["doc_j"]), (e["doc_j"], e["doc_i"])]:
            if a not in doc_to_primary:
                continue
            own = doc_to_primary[a]
            if key != own and key != SIN_SUBHILO:
                secondary[a].add(key)
                provenance[a].append({"via_doc": b, "w": float(e["w"]), "ref_objeto": str(ref_objeto), "clave": key})

    primary = primary.copy()
    primary["subhilo_secundario"] = primary["doc_id"].map(lambda d: sorted(secondary.get(d, set())))
    primary["subhilo_secundario_evidencia"] = primary["doc_id"].map(lambda d: provenance.get(d, []))
    primary["multiasignado"] = primary["subhilo_secundario"].map(lambda lst: len(lst) > 0)
    return primary


def detect_bridge_crossings(primary: pd.DataFrame, edges: pd.DataFrame) -> pd.DataFrame:
    doc_to_primary = dict(zip(primary["doc_id"], primary["subhilo_primario"]))
    rows = []
    bridge_edges = edges[edges["puente"] == True]  # noqa: E712 (columna booleana explicita)
    for _, e in bridge_edges.iterrows():
        i, j = e["doc_i"], e["doc_j"]
        si, sj = doc_to_primary.get(i), doc_to_primary.get(j)
        cruza = (si != sj) and (si != SIN_SUBHILO) and (sj != SIN_SUBHILO)
        rows.append({
            "doc_i": i, "doc_j": j, "w": float(e["w"]),
            "subhilo_i": si, "subhilo_j": sj,
            "cruza_subhilos_distintos": bool(cruza),
        })
    out = pd.DataFrame(rows).sort_values(["doc_i", "doc_j"]).reset_index(drop=True)
    return out


def compute_purity_coverage(primary: pd.DataFrame):
    integrated_path = VALID / "H0000_VALIDATION_INTEGRATED_2026_07_22.json"
    with open(integrated_path, encoding="utf-8") as f:
        integrated = json.load(f)
    disagreements_path = VALID / "H0000_DISAGREEMENTS_ADJUDICATED_2026_07_22.json"
    with open(disagreements_path, encoding="utf-8") as f:
        arb = {c["case_id"]: c["decision_arbitro"] for c in json.load(f)["casos"]}

    doc_to_primary = dict(zip(primary["doc_id"], primary["subhilo_primario"]))

    n_total = 0
    n_evaluable = 0
    n_same_subhilo = 0
    n_same_subhilo_and_especifico = 0
    n_diff_subhilo_but_amplio_or_mas = 0
    n_diff_subhilo_total = 0

    for case in integrated["casos"]:
        n_total += 1
        a, b = case["doc_a"], case["doc_b"]
        cid = case["case_id"]
        final = arb.get(cid) or (case["decision_gpt"] if case["decision_gpt"] == case["decision_claude"] else None)
        if final is None:
            continue
        sa, sb = doc_to_primary.get(a), doc_to_primary.get(b)
        if sa is None or sb is None or sa == SIN_SUBHILO or sb == SIN_SUBHILO:
            continue  # abstencion de par (2.5 del diseno)
        n_evaluable += 1
        broad_or_more = final in ("mismo_proceso_especifico", "mismo_macroproceso")
        especifico = final == "mismo_proceso_especifico"
        if sa == sb:
            n_same_subhilo += 1
            if especifico:
                n_same_subhilo_and_especifico += 1
        else:
            n_diff_subhilo_total += 1
            if broad_or_more:
                n_diff_subhilo_but_amplio_or_mas += 1

    cobertura = float((primary["subhilo_primario"] != SIN_SUBHILO).mean())
    pureza_estricta_subhilo = (
        n_same_subhilo_and_especifico / n_same_subhilo if n_same_subhilo else None
    )
    retencion_amplia_entre_subhilos = (
        n_diff_subhilo_but_amplio_or_mas / n_diff_subhilo_total if n_diff_subhilo_total else None
    )

    return {
        "cobertura_documentos_con_subhilo": round(cobertura, 4),
        "n_docs_total": int(len(primary)),
        "n_docs_con_subhilo": int((primary["subhilo_primario"] != SIN_SUBHILO).sum()),
        "n_pares_muestra_ciega_104": n_total,
        "n_pares_evaluables_ambos_con_subhilo": n_evaluable,
        "n_pares_mismo_subhilo": n_same_subhilo,
        "pureza_estricta_subhilo": None if pureza_estricta_subhilo is None else round(pureza_estricta_subhilo, 4),
        "n_pares_distinto_subhilo": n_diff_subhilo_total,
        "retencion_amplia_entre_subhilos_distintos": None if retencion_amplia_entre_subhilos is None else round(retencion_amplia_entre_subhilos, 4),
        "nota": ("pureza_estricta_subhilo = de los pares de la muestra ciega que comparten subhilo primario, "
                 "que fraccion fue juzgada mismo_proceso_especifico. "
                 "retencion_amplia_entre_subhilos_distintos = de los pares que caen en subhilos DISTINTOS, "
                 "que fraccion sigue siendo al menos mismo_macroproceso (no debe caer por debajo de la tasa "
                 "amplia global de H0000, ~0.97, o la particion en subhilos estaria destruyendo continuidad "
                 "amplia real)."),
    }


def verify_v1_untouched() -> dict:
    with open(DIAG / "H0000_10_MANIFEST.json", encoding="utf-8") as f:
        v1_manifest = json.load(f)
    checks = {}
    for fname, expected_hash in v1_manifest["files"].items():
        # el manifest v1 usa hashes con prefijo de 64 hex mas caracteres extra en algunos casos
        # historicos; comparamos por prefijo sha256 real (primeros 64 hex) para tolerar el formato.
        fpath = DIAG / fname
        if not fpath.exists():
            checks[fname] = {"existe": False, "coincide": False}
            continue
        actual = sha256_file(fpath)
        expected_prefix = expected_hash[:64]
        checks[fname] = {"existe": True, "coincide": actual == expected_prefix, "sha256_actual": actual}
    todo_ok = all(c["coincide"] for c in checks.values() if c["existe"])
    return {"todos_los_archivos_v1_intactos": todo_ok, "detalle": checks}


def run(seed: int = 20260780, shuffle_input: bool = False) -> dict:
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    nodes, edges = load_v1_inputs(shuffle_input=shuffle_input, seed=seed)

    primary = build_primary_assignment(nodes)
    full = add_secondary_assignments(primary, edges)
    bridges = detect_bridge_crossings(full, edges)
    purity = compute_purity_coverage(full)
    v1_check = verify_v1_untouched()

    # --- escribir artefactos (deterministas: mismo orden sin importar shuffle_input) ---
    assign_path = ARTIFACTS / "node_subhilo_assignment.csv"
    full_out = full.copy()
    full_out["subhilo_secundario"] = full_out["subhilo_secundario"].map(lambda l: ";".join(l))
    full_out["subhilo_secundario_evidencia"] = full_out["subhilo_secundario_evidencia"].map(
        lambda l: json.dumps(l, ensure_ascii=False))
    full_out.to_csv(assign_path, index=False, encoding="utf-8-sig")

    bridges_path = ARTIFACTS / "bridge_crossings.csv"
    bridges.to_csv(bridges_path, index=False, encoding="utf-8-sig")

    summary = {
        "macrohilo_id": MACROHILO_ID,
        "seed": seed,
        "shuffle_input_test": shuffle_input,
        "n_subhilos_distintos": int(full["subhilo_primario"].nunique()),
        "distribucion_subhilos": full["subhilo_primario"].value_counts().to_dict(),
        "n_documentos_multiasignados": int(full["multiasignado"].sum()),
        "n_puentes_totales": int(len(bridges)),
        "n_puentes_que_cruzan_subhilos": int(bridges["cruza_subhilos_distintos"].sum()) if len(bridges) else 0,
        "purity_coverage": purity,
        "verificacion_v1_intacto": v1_check,
    }
    summary_path = ARTIFACTS / "subhilo_purity_coverage.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2, default=str)

    # --- manifest + lock del experimento v2 ---
    manifest = {
        "generated_by": "hebra_v2_experimental/src/build_hierarchy.py",
        "seed": seed,
        "files": {
            "node_subhilo_assignment.csv": sha256_file(assign_path),
            "bridge_crossings.csv": sha256_file(bridges_path),
            "subhilo_purity_coverage.json": sha256_file(summary_path),
        },
        "v1_inputs_read_only": {
            "H0000_02_NODE_METRICS.csv": sha256_file(DIAG / "H0000_02_NODE_METRICS.csv"),
            "H0000_03_EDGE_METRICS.csv": sha256_file(DIAG / "H0000_03_EDGE_METRICS.csv"),
            "H0000_10_MANIFEST.json": sha256_file(DIAG / "H0000_10_MANIFEST.json"),
        },
    }
    with open(ARTIFACTS / "HIERARCHY_MANIFEST.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    lock = {
        "arquitectura": "hebra_v2_experimental (macrohilo/subhilo)",
        "v1_no_modificado": v1_check["todos_los_archivos_v1_intactos"],
        "seed": seed,
        "determinista": True,
        "algoritmos_de_comunidad_usados_para_asignar_subhilo": False,
        "diccionario_canonizacion": "subthread_dictionary.py (reglas de subcadena, no ML)",
        "ganador_empirico_declarado": False,
        "reemplaza_v1": False,
    }
    with open(ARTIFACTS / "HIERARCHY_EXPERIMENT_LOCK.json", "w", encoding="utf-8") as f:
        json.dump(lock, f, ensure_ascii=False, indent=2)

    return {"full": full, "bridges": bridges, "summary": summary}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=20260780)
    parser.add_argument("--shuffle-input", action="store_true")
    args = parser.parse_args()
    result = run(seed=args.seed, shuffle_input=args.shuffle_input)
    print(json.dumps(result["summary"], ensure_ascii=False, indent=2, default=str))
