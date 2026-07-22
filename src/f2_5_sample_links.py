# F2.5 — Muestreo ciego de enlaces e hilos para revision de precision (HEBRA).
# Semilla fija. La hoja de revision NO incluye puntajes (s_ref/s_emb/w) ni
# umbrales: solo ids, fechas, titulos y referentes, para juzgar si el par
# pertenece al mismo proceso. La clave puntaje->par queda en un archivo
# separado que no debe abrirse durante la revision.

import csv
import json
import random
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4].parent
CORPUS = ROOT / "01_bases_de_datos/03_refiltro_api_qwen_y_base_actual/06_base_actual_fusionada_3742_incluidas.csv"
OUT_DIR = Path(__file__).resolve().parents[1] / "outputs"

EDGES = OUT_DIR / "f2b_idf_v2_edges.csv"
THREADS = OUT_DIR / "f2b_idf_v2_threads.csv"
N_EDGES, N_THREADS, SEED = 60, 12, 42


def main() -> None:
    rng = random.Random(SEED)
    titles, fechas = {}, {}
    with open(CORPUS, encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            titles[row["id"]] = (row.get("titulo") or "")[:160]
            fechas[row["id"]] = (row.get("fecha_iso") or "")[:10]

    with open(EDGES, encoding="utf-8", newline="") as f:
        edges = list(csv.DictReader(f))
    sample_e = rng.sample(edges, min(N_EDGES, len(edges)))

    threads = {}
    with open(THREADS, encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            threads.setdefault(row["thread_id"], []).append(row["doc_id"])
    tids = sorted(threads)
    sample_t = rng.sample(tids, min(N_THREADS, len(tids)))

    review = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "seed": SEED,
        "edges": [
            {
                "pair_id": f"E{k:03d}",
                "doc_a": {"id": e["doc_i"], "fecha": fechas.get(e["doc_i"], ""),
                          "titulo": titles.get(e["doc_i"], "")},
                "doc_b": {"id": e["doc_j"], "fecha": fechas.get(e["doc_j"], ""),
                          "titulo": titles.get(e["doc_j"], "")},
                "veredicto": "",  # mismo_proceso | relacionado | no_relacionado
            }
            for k, e in enumerate(sample_e)
        ],
        "threads": [
            {
                "thread_id": t,
                "docs": [
                    {"id": d, "fecha": fechas.get(d, ""), "titulo": titles.get(d, "")}
                    for d in sorted(threads[t], key=lambda x: fechas.get(x, ""))
                ][:25],
                "docs_total": len(threads[t]),
                "veredicto": "",  # coherente | mezcla | fragmento
            }
            for t in sample_t
        ],
    }
    (OUT_DIR / "f2_5_blind_review_sheet.json").write_text(
        json.dumps(review, ensure_ascii=False, indent=1), encoding="utf-8"
    )
    key = {f"E{k:03d}": {kk: e[kk] for kk in ("s_ref", "s_emb", "w", "dias")}
           for k, e in enumerate(sample_e)}
    (OUT_DIR / "f2_5_blind_review_key_DO_NOT_OPEN.json").write_text(
        json.dumps(key, indent=1), encoding="utf-8"
    )
    print(f"hoja: {len(review['edges'])} enlaces, {len(review['threads'])} hilos")


if __name__ == "__main__":
    main()
