# F4-D A2 — Ablacion "solo embeddings" (HEBRA sin referentes).
# Candidatos: para cada doc, sus 15 vecinos mas cercanos por coseno dentro de
# +-365 dias (sin referentes; no hay tier largo porque no hay s_ref).
# w = s_emb; grid preinscrito tau in {0.60, 0.70, 0.80}; misma regla de
# seleccion estructural (menor tau con gigante <= 30%).
# Escala de tau NO comparable con HEBRA; la comparacion valida es sobre
# recuperacion de gold, mezcla y fragmentacion, no sobre tau.

import csv
import hashlib
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[4].parent
CORPUS = ROOT / "01_bases_de_datos/03_refiltro_api_qwen_y_base_actual/06_base_actual_fusionada_3742_incluidas.csv"
EMB = ROOT / "04_embeddings/01_embeddings_canonicos/active_corpus_embeddings_3742.npz"
OUT_DIR = Path(__file__).resolve().parents[1] / "outputs"

KNN = 15
TAUS = [0.60, 0.70, 0.80]
GIANT_MAX = 0.30
D1 = 365


class DSU:
    def __init__(self, n):
        self.p = list(range(n))

    def find(self, x):
        while self.p[x] != x:
            self.p[x] = self.p[self.p[x]]
            x = self.p[x]
        return x

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.p[rb] = ra


def main() -> None:
    ids, day = [], {}
    from datetime import date
    with open(CORPUS, encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            ids.append(row["id"])
            fx = (row.get("fecha_iso") or "")[:10]
            try:
                y, m, d = map(int, fx.split("-"))
                day[row["id"]] = date(y, m, d).toordinal()
            except ValueError:
                pass
    n = len(ids)
    emb = np.load(EMB)["arr_0"].astype(np.float32)
    emb /= np.linalg.norm(emb, axis=1, keepdims=True)
    dated_idx = [k for k, d in enumerate(ids) if d in day]
    days_arr = np.array([day[ids[k]] for k in dated_idx])

    # KNN por bloques dentro de ventana temporal
    E = emb[dated_idx]
    pairs = {}
    for bi in range(0, len(dated_idx), 256):
        block = E[bi:bi + 256] @ E.T  # (b, N)
        for r in range(block.shape[0]):
            gi = bi + r
            mask = np.abs(days_arr - days_arr[gi]) <= D1
            mask[gi] = False
            sims = np.where(mask, block[r], -1.0)
            top = np.argpartition(-sims, KNN)[:KNN]
            for j in top:
                if sims[j] <= 0:
                    continue
                a, b = sorted((gi, int(j)))
                pairs[(a, b)] = float(sims[j])

    def build(tau):
        dsu = DSU(len(dated_idx))
        edges = 0
        for (a, b), s in pairs.items():
            if s >= tau:
                dsu.union(a, b)
                edges += 1
        comp = defaultdict(list)
        for k in range(len(dated_idx)):
            comp[dsu.find(k)].append(k)
        threads = sorted((sorted(m) for m in comp.values()), key=len, reverse=True)
        multi = [t for t in threads if len(t) >= 3]
        giant = len(threads[0]) if threads else 0
        return {
            "tau": tau, "edges": edges, "threads_ge3": len(multi),
            "coverage_ge3_pct": round(100 * sum(map(len, multi)) / len(dated_idx), 2),
            "giant_share_pct": round(100 * giant / len(dated_idx), 2),
            "_multi": multi,
        }

    grid = [build(t) for t in TAUS]
    chosen = next((g for g in grid if g["giant_share_pct"] <= 100 * GIANT_MAX), grid[-1])

    with open(OUT_DIR / "f4d_onlyemb_threads.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["thread_id", "doc_id"])
        for k, t in enumerate(chosen["_multi"]):
            for gi in t:
                w.writerow([f"E{k:04d}", ids[dated_idx[gi]]])

    summary = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "design": "solo embeddings; KNN15 en ventana +-365d; w=s_emb",
        "inputs_sha256": {
            "corpus": hashlib.sha256(CORPUS.read_bytes()).hexdigest(),
            "embeddings": hashlib.sha256(EMB.read_bytes()).hexdigest(),
            "script": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        },
        "grid": [{k: v for k, v in g.items() if k != "_multi"} for g in grid],
        "chosen_tau": chosen["tau"],
    }
    (OUT_DIR / "f4d_onlyemb_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(summary["grid"], indent=1))
    print("chosen", chosen["tau"])


if __name__ == "__main__":
    main()
