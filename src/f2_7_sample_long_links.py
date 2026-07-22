# F2.7 — Revision ciega de enlaces largos (HEBRA).
# Nota: el conjunto "L1 aceptado y L2 rechazado" resulto VACIO (L1==L2 con
# 9981 aristas identicas). Se audita la zona de riesgo real del tier largo:
# aristas largas con s_ref en [0.5, 0.6) — exactamente las que L3 rechaza —
# estratificadas 15/15 por 366-730 y 731-1095 dias. Hoja ciega: titulos,
# snippet y referentes compartidos; sin s_ref/s_emb/w.

import csv
import json
import random
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4].parent
CORPUS = ROOT / "01_bases_de_datos/03_refiltro_api_qwen_y_base_actual/06_base_actual_fusionada_3742_incluidas.csv"
OUT_DIR = Path(__file__).resolve().parents[1] / "outputs"
EDGES = OUT_DIR / "f2b_idf_v2_L2_edges.csv"
REFS = OUT_DIR / "f1v2_referents.csv"
SEED = 20260722


def main() -> None:
    rng = random.Random(SEED)
    titles, fechas, snippets = {}, {}, {}
    with open(CORPUS, encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            titles[row["id"]] = (row.get("titulo") or "")[:160]
            fechas[row["id"]] = (row.get("fecha_iso") or "")[:10]
            snippets[row["id"]] = (row.get("snippet") or "")[:220]

    doc_refs = defaultdict(set)
    with open(REFS, encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            doc_refs[row["doc_id"]].add((row["tipo"], row["referente"]))

    strata = {"366-730": [], "731-1095": []}
    with open(EDGES, encoding="utf-8", newline="") as f:
        for e in csv.DictReader(f):
            dias, s_ref = int(e["dias"]), float(e["s_ref"])
            if dias > 365 and 0.5 <= s_ref < 0.6:
                strata["366-730" if dias <= 730 else "731-1095"].append(e)

    sample, key = [], {}
    k = 0
    for name, pool in strata.items():
        for e in rng.sample(pool, min(15, len(pool))):
            pid = f"LL{k:03d}"
            shared = sorted(doc_refs[e["doc_i"]] & doc_refs[e["doc_j"]])
            sample.append({
                "pair_id": pid, "estrato_dias": name,
                "doc_a": {"id": e["doc_i"], "fecha": fechas[e["doc_i"]],
                          "titulo": titles[e["doc_i"]], "snippet": snippets[e["doc_i"]]},
                "doc_b": {"id": e["doc_j"], "fecha": fechas[e["doc_j"]],
                          "titulo": titles[e["doc_j"]], "snippet": snippets[e["doc_j"]]},
                "referentes_compartidos": [f"{t}:{r}" for t, r in shared],
                "veredicto": "",
            })
            key[pid] = {kk: e[kk] for kk in ("s_ref", "s_emb", "w", "dias")}
            k += 1

    sheet = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "seed": SEED,
        "definicion_muestra": (
            "aristas largas (dias>365) con s_ref en [0.5,0.6): zona que L3 "
            "rechaza y L1/L2 aceptan; el conjunto L1-aceptado/L2-rechazado es vacio"
        ),
        "strata_sizes": {n: len(p) for n, p in strata.items()},
        "edges": sample,
    }
    (OUT_DIR / "f2_7_long_links_review_sheet.json").write_text(
        json.dumps(sheet, ensure_ascii=False, indent=1), encoding="utf-8")
    (OUT_DIR / "f2_7_long_links_key_DO_NOT_OPEN.json").write_text(
        json.dumps(key, indent=1), encoding="utf-8")
    print("muestra:", len(sample), "| poblacion por estrato:", sheet["strata_sizes"])


if __name__ == "__main__":
    main()
