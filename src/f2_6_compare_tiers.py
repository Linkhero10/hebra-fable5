# F2.6 — Comparacion L1/L2/L3 del tier de enlaces largos (HEBRA).
# Solo lectura de outputs propios. No usa los cinco casos contaminados para
# seleccionar: reporta metricas estructurales y estabilidad de perfiles.

import csv
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from itertools import combinations
from pathlib import Path

OUT_DIR = Path(__file__).resolve().parents[1] / "outputs"
TIERS = ["L1", "L2", "L3"]
BASE = "f2b_idf_v2"


def load_threads(tier: str):
    doc2t, t2docs = {}, defaultdict(set)
    with open(OUT_DIR / f"{BASE}_{tier}_threads.csv", encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            doc2t[row["doc_id"]] = row["thread_id"]
            t2docs[row["thread_id"]].add(row["doc_id"])
    return doc2t, t2docs


def load_summary(tier: str):
    d = json.loads((OUT_DIR / f"{BASE}_{tier}_threads_summary.json").read_text(encoding="utf-8"))
    g = next(x for x in d["grid"] if x["tau"] == d["chosen_tau"])
    return d, g


def load_edges(tier: str):
    with open(OUT_DIR / f"{BASE}_{tier}_edges.csv", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def pairwise_agreement(map_a, map_b):
    # Sobre docs presentes en ambos mapas (hilos >=3): pares co-hilo.
    common = sorted(set(map_a) & set(map_b))
    idx = {d: k for k, d in enumerate(common)}
    pa = {frozenset(p) for t, docs in _group(map_a, common).items()
          for p in combinations(sorted(docs), 2)}
    pb = {frozenset(p) for t, docs in _group(map_b, common).items()
          for p in combinations(sorted(docs), 2)}
    inter = len(pa & pb)
    return {
        "docs_common": len(common),
        "pairs_a": len(pa), "pairs_b": len(pb),
        "pairs_shared": inter,
        "jaccard_pairs": round(inter / len(pa | pb), 4) if (pa | pb) else 1.0,
    }


def _group(m, universe):
    g = defaultdict(set)
    for d in universe:
        g[m[d]].add(d)
    return g


def main() -> None:
    result = {"generated_utc": datetime.now(timezone.utc).isoformat(), "base": BASE, "tiers": {}}
    maps, summaries = {}, {}
    for t in TIERS:
        doc2t, t2docs = load_threads(t)
        d, g = load_summary(t)
        edges = load_edges(t)
        long_e = [e for e in edges if int(e["dias"]) > 365]
        maps[t] = doc2t
        summaries[t] = (d, g)
        # proporcion de enlaces largos por hilo (top 12 por tamano)
        e_by_thread = Counter()
        long_by_thread = Counter()
        # una arista pertenece a un hilo si ambos extremos estan en el
        for e in edges:
            ta, tb = doc2t.get(e["doc_i"]), doc2t.get(e["doc_j"])
            if ta and ta == tb:
                e_by_thread[ta] += 1
                if int(e["dias"]) > 365:
                    long_by_thread[ta] += 1
        top12 = sorted(t2docs, key=lambda x: -len(t2docs[x]))[:12]
        result["tiers"][t] = {
            "chosen_tau": d["chosen_tau"],
            "edges_total": g["edges"],
            "long_edges": g.get("long_edges"),
            "long_edges_dumped": len(long_e),
            "threads_ge3": g["threads_ge3"],
            "coverage_ge3_pct": g["coverage_ge3_pct"],
            "giant_share_pct": g["giant_share_pct"],
            "singletons": g["singletons"],
            "size_p50_ge3": g["size_p50_ge3"],
            "long_edge_share_top12": {
                t_id: {
                    "docs": len(t2docs[t_id]),
                    "edges": e_by_thread[t_id],
                    "long": long_by_thread[t_id],
                    "pct_long": round(100 * long_by_thread[t_id] / e_by_thread[t_id], 1)
                    if e_by_thread[t_id] else 0,
                }
                for t_id in top12
            },
        }

    # Cambios de hilo y splits L1 -> L2 / L3
    for other in ("L2", "L3"):
        a, b = maps["L1"], maps[other]
        moved_out = sorted(set(a) - set(b))          # en hilo >=3 en L1, no en other
        _, t2a = load_threads("L1")
        _, t2b = load_threads(other)
        splits = {}
        top12 = sorted(t2a, key=lambda x: -len(t2a[x]))[:12]
        for t_id in top12:
            targets = Counter(b.get(d, "_fuera_") for d in t2a[t_id])
            best = targets.most_common(1)[0]
            splits[t_id] = {
                "docs_l1": len(t2a[t_id]),
                "n_destinos": len(targets),
                "mejor_destino_docs": best[1],
                "jaccard_mejor": round(
                    best[1] / len(t2a[t_id] | t2b.get(best[0], set())), 3
                ) if best[0] != "_fuera_" else 0.0,
                "docs_fuera_de_hilos": targets.get("_fuera_", 0),
            }
        result[f"L1_vs_{other}"] = {
            "docs_que_salen_de_hilos_ge3": len(moved_out),
            "acuerdo_pares": pairwise_agreement(a, b),
            "splits_top12_L1": splits,
        }

    (OUT_DIR / "f2_6_tier_comparison.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8"
    )
    slim = {t: {k: v for k, v in result["tiers"][t].items() if k != "long_edge_share_top12"}
            for t in TIERS}
    print(json.dumps(slim, indent=1))
    for other in ("L2", "L3"):
        r = result[f"L1_vs_{other}"]
        print(f"L1 vs {other}: salen {r['docs_que_salen_de_hilos_ge3']} docs; "
              f"acuerdo pares {r['acuerdo_pares']['jaccard_pairs']}")


if __name__ == "__main__":
    main()
