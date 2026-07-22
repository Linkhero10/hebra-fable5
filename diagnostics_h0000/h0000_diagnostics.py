# Fase 3B — Diagnostico estructural congelado de H0000 (E1-E4).
# Solo lectura de artefactos v1; escribe unicamente en diagnostics_h0000/.
# No modifica codigo v1, umbral, candidatos ni grafo. Algoritmos de
# particion en modo diagnostico. Sin adjudicacion propia.

import csv
import hashlib
import json
import math
import random
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from itertools import combinations
from pathlib import Path

import networkx as nx
import numpy as np
import igraph as ig
from scipy.stats import mannwhitneyu
from sklearn.metrics import adjusted_rand_score, normalized_mutual_info_score

BASE = Path(__file__).resolve().parents[1]
OUT = Path(__file__).resolve().parent
ROOT = BASE.parents[3]
CORPUS = ROOT / "01_bases_de_datos/03_refiltro_api_qwen_y_base_actual/06_base_actual_fusionada_3742_incluidas.csv"
THREADS = BASE / "outputs/f2b_idf_v2_L2_threads.csv"
EDGES = BASE / "outputs/f2b_idf_v2_L2_edges.csv"
REFS = BASE / "outputs/f1v2_referents.csv"

SEEDS = list(range(20))
BLIND_SEED = 20260780
FROZEN = {"docs": 170, "edges": 889, "bridges": 23, "weak_bridges_w050": 15}


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def load_subgraph():
    docs = set()
    with open(THREADS, encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            if r["thread_id"] == "H0000":
                docs.add(r["doc_id"])
    edges = []
    with open(EDGES, encoding="utf-8", newline="") as f:
        for e in csv.DictReader(f):
            if e["doc_i"] in docs and e["doc_j"] in docs:
                edges.append({
                    "doc_i": e["doc_i"], "doc_j": e["doc_j"],
                    "w": float(e["w"]), "s_ref": float(e["s_ref"]),
                    "s_emb": float(e["s_emb"]), "dias": int(e["dias"]),
                })
    return sorted(docs), edges


def main() -> None:
    docs, edges = load_subgraph()
    n, m = len(docs), len(edges)
    G = nx.Graph()
    G.add_nodes_from(docs)
    for e in edges:
        G.add_edge(e["doc_i"], e["doc_j"], weight=e["w"], **e)

    bridges = set(frozenset(b) for b in nx.bridges(G))
    weak_bridges = {b for b in bridges
                    if G.edges[tuple(b)]["w"] < 0.50}
    observed = {"docs": n, "edges": m, "bridges": len(bridges),
                "weak_bridges_w050": len(weak_bridges)}
    discrepancias = {k: {"frozen": FROZEN[k], "observed": observed[k]}
                     for k in FROZEN if FROZEN[k] != observed[k]}
    if discrepancias:
        print("DISCREPANCIA con cifras congeladas:", json.dumps(discrepancias))
        sys.exit(2)

    # ---- metadatos por nodo ----
    meta = {}
    with open(CORPUS, encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            if row["id"] in G:
                meta[row["id"]] = {
                    "fecha": (row.get("fecha_iso") or "")[:10],
                    "titulo": (row.get("titulo") or "")[:200],
                    "texto": (row.get("contenido_completo") or "")[:6000],
                }
    refs = defaultdict(lambda: defaultdict(set))
    with open(REFS, encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            if r["doc_id"] in G:
                refs[r["doc_id"]][r["tipo"]].add(r["referente"])
    ref_df = Counter()
    with open(REFS, encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            ref_df[(r["tipo"], r["referente"])] += 1
    n_dated_corpus = 3725
    idf_ref = math.log(n_dated_corpus / 5)

    def idf(t, r):
        return min(1.0, math.log(n_dated_corpus / ref_df[(t, r)]) / idf_ref)

    # ---- topologia ----
    art_points = set(nx.articulation_points(G))
    bicomp = list(nx.biconnected_components(G))
    bicomp_of = defaultdict(list)
    for k, comp in enumerate(sorted(bicomp, key=len, reverse=True)):
        for v in comp:
            bicomp_of[v].append(k)
    ebc = nx.edge_betweenness_centrality(G, weight=None)
    core = nx.core_number(G)
    clustering = nx.clustering(G)
    G_weakpruned = G.copy()
    G_weakpruned.remove_edges_from(tuple(b) for b in weak_bridges)
    wp_sizes = sorted((len(c) for c in nx.connected_components(G_weakpruned)),
                      reverse=True)

    # ---- particiones (E1/E4) ----
    idx = {d: i for i, d in enumerate(docs)}
    g_ig = ig.Graph(n=n, edges=[(idx[e["doc_i"]], idx[e["doc_j"]]) for e in edges])
    g_ig.es["weight"] = [e["w"] for e in edges]
    density = 2 * m / (n * (n - 1))

    def part_labels(kind, seed):
        if kind == "dsu":
            return [0] * n  # un componente
        if kind == "louvain":
            comms = nx.community.louvain_communities(G, weight="weight", seed=seed)
            lab = {}
            for k, c in enumerate(comms):
                for v in c:
                    lab[v] = k
            return [lab[d] for d in docs]
        random.seed(seed)
        ig.set_random_number_generator(random)
        if kind == "leiden_cpm":
            p = g_ig.community_leiden(objective_function="CPM",
                                      resolution=density, weights="weight",
                                      n_iterations=5)
        elif kind == "leiden_mod":
            p = g_ig.community_leiden(objective_function="modularity",
                                      weights="weight", n_iterations=5)
        elif kind == "infomap":
            p = g_ig.community_infomap(edge_weights="weight", trials=5)
        return p.membership

    ALGOS = ["dsu", "louvain", "leiden_cpm", "leiden_mod", "infomap"]
    runs = {a: [part_labels(a, s) for s in SEEDS] for a in ALGOS}

    # perturbaciones: edge-drop 5/10%, jitter retencion (dias>1081 en riesgo)
    def perturbed_labels(kind, seed, mode):
        rng = random.Random(seed)
        if mode.startswith("drop"):
            frac = 0.05 if mode == "drop5" else 0.10
            keep = rng.sample(range(m), int(round(m * (1 - frac))))
            sub = [edges[i] for i in keep]
        else:  # jitter +-7d por doc: arista muere si dias' > 1095
            jit = {d: rng.randint(-7, 7) for d in docs}
            sub = [e for e in edges
                   if abs(e["dias"] + jit[e["doc_j"]] - jit[e["doc_i"]]) <= 1095]
        H = nx.Graph()
        H.add_nodes_from(docs)
        for e in sub:
            H.add_edge(e["doc_i"], e["doc_j"], weight=e["w"])
        if kind == "dsu":
            lab = {}
            for k, c in enumerate(nx.connected_components(H)):
                for v in c:
                    lab[v] = k
            return [lab[d] for d in docs]
        if kind == "louvain":
            comms = nx.community.louvain_communities(H, weight="weight", seed=seed)
        else:
            h_ig = ig.Graph(n=n, edges=[(idx[a], idx[b]) for a, b in H.edges()])
            h_ig.es["weight"] = [H.edges[a, b]["weight"] for a, b in H.edges()]
            random.seed(seed)
            ig.set_random_number_generator(random)
            if kind == "leiden_cpm":
                p = h_ig.community_leiden(objective_function="CPM",
                                          resolution=density, weights="weight",
                                          n_iterations=5)
            elif kind == "leiden_mod":
                p = h_ig.community_leiden(objective_function="modularity",
                                          weights="weight", n_iterations=5)
            else:
                p = h_ig.community_infomap(edge_weights="weight", trials=5)
            return p.membership
        lab = {}
        for k, c in enumerate(comms):
            for v in c:
                lab[v] = k
        return [lab[d] for d in docs]

    stability = {}
    coassign = {}
    for a in ALGOS:
        base_runs = runs[a]
        pert = {mode: [perturbed_labels(a, s, mode) for s in SEEDS]
                for mode in ("drop5", "drop10", "jitter")}
        pairs_ari = [adjusted_rand_score(base_runs[i], base_runs[j])
                     for i, j in combinations(range(len(SEEDS)), 2)]
        stability[a] = {
            "n_comms_median": float(np.median([len(set(r)) for r in base_runs])),
            "seed_ari_mean": round(float(np.mean(pairs_ari)), 4) if pairs_ari else 1.0,
            "seed_ari_min": round(float(np.min(pairs_ari)), 4) if pairs_ari else 1.0,
        }
        for mode, pruns in pert.items():
            aris = [adjusted_rand_score(base_runs[s], pruns[s]) for s in range(len(SEEDS))]
            nmis = [normalized_mutual_info_score(base_runs[s], pruns[s]) for s in range(len(SEEDS))]
            stability[a][f"{mode}_ari_mean"] = round(float(np.mean(aris)), 4)
            stability[a][f"{mode}_nmi_mean"] = round(float(np.mean(nmis)), 4)
        M = np.zeros((n, n))
        allruns = base_runs + pert["drop5"] + pert["drop10"] + pert["jitter"]
        for lab in allruns:
            arr = np.array(lab)
            for c in set(lab):
                members = np.where(arr == c)[0]
                M[np.ix_(members, members)] += 1
        M /= len(allruns)
        coassign[a] = M
        # consenso: componentes del grafo de coasignacion >= 0.5
        C = nx.Graph()
        C.add_nodes_from(range(n))
        for i in range(n):
            for j in range(i + 1, n):
                if M[i, j] >= 0.5:
                    C.add_edge(i, j)
        cons = {v: k for k, comp in enumerate(nx.connected_components(C)) for v in comp}
        runs[a + "_consensus"] = [[cons[i] for i in range(n)]]

    # comparacion contra DSU (todo un componente): pares separados
    partition_rows = []
    total_pairs = n * (n - 1) // 2
    for a in ALGOS:
        lab = runs[a + "_consensus"][0] if a != "dsu" else runs["dsu"][0]
        arr = np.array(lab)
        sizes = sorted(Counter(lab).values(), reverse=True)
        same = sum(s * (s - 1) // 2 for s in sizes)
        # referentes dominantes y diversidad territorial por comunidad top-5
        doms = []
        for c, _ in Counter(lab).most_common(5):
            members = [docs[i] for i in np.where(arr == c)[0]]
            obj = Counter(r for d in members for r in refs[d]["objeto"])
            terr = Counter(r for d in members for r in refs[d]["territorio"])
            doms.append({"size": len(members),
                         "objeto_top": obj.most_common(1)[0][0] if obj else "",
                         "territorios_distintos": len(terr)})
        long_split = sum(1 for e in edges if e["dias"] > 365
                         and lab[idx[e["doc_i"]]] != lab[idx[e["doc_j"]]])
        partition_rows.append({
            "algoritmo": a, "n_comunidades": len(sizes),
            "tamanos_top5": sizes[:5],
            "pares_coasignados": same,
            "pares_separados_vs_dsu": total_pairs - same,
            "enlaces_largos_divididos": long_split,
            "comunidades_top": doms,
            **stability[a],
        })

    # ---- E2: puentes vs no puentes ----
    def edge_feats(e):
        i, j = e["doc_i"], e["doc_j"]
        cn = len(set(G[i]) & set(G[j]))
        deg_i, deg_j = G.degree(i), G.degree(j)
        emb_ratio = cn / max(1, (deg_i - 1) + (deg_j - 1) - cn)
        shared = {t: sorted(refs[i][t] & refs[j][t]) for t in ("objeto", "territorio", "actor")}
        idf_max = max((idf(t, r) for t, rs in shared.items() for r in rs), default=0.0)
        return cn, emb_ratio, shared, idf_max, deg_i, deg_j

    edge_rows = []
    for e in edges:
        cn, emb_ratio, shared, idf_max, deg_i, deg_j = edge_feats(e)
        b = frozenset((e["doc_i"], e["doc_j"])) in bridges
        edge_rows.append({
            **{k: e[k] for k in ("doc_i", "doc_j", "w", "s_ref", "s_emb", "dias")},
            "largo": e["dias"] > 365,
            "grado_i": deg_i, "grado_j": deg_j,
            "triangulos": cn, "embeddedness": round(emb_ratio, 4),
            "edge_betweenness": round(ebc[(e["doc_i"], e["doc_j"])] if (e["doc_i"], e["doc_j"]) in ebc else ebc[(e["doc_j"], e["doc_i"])], 6),
            "puente": b,
            "articulacion_adyacente": e["doc_i"] in art_points or e["doc_j"] in art_points,
            "ref_objeto": ";".join(shared["objeto"]),
            "ref_territorio": ";".join(shared["territorio"]),
            "ref_actor": ";".join(shared["actor"]),
            "idf_max_ref_compartido": round(idf_max, 4),
        })

    br_rows = [r for r in edge_rows if r["puente"]]
    nb_rows = [r for r in edge_rows if not r["puente"]]
    e2 = {}
    feats = ["w", "s_ref", "s_emb", "dias", "triangulos", "embeddedness",
             "idf_max_ref_compartido"]
    pvals = []
    for ft in feats:
        a_ = [r[ft] for r in br_rows]
        b_ = [r[ft] for r in nb_rows]
        u = mannwhitneyu(a_, b_, alternative="two-sided")
        rng = np.random.default_rng(7)
        boot = [np.mean(rng.choice(a_, len(a_))) - np.mean(rng.choice(b_, len(b_)))
                for _ in range(2000)]
        e2[ft] = {
            "puentes_mediana": float(np.median(a_)),
            "no_puentes_mediana": float(np.median(b_)),
            "mw_p": float(u.pvalue),
            "diff_media_ic95": [float(np.percentile(boot, 2.5)),
                                float(np.percentile(boot, 97.5))],
        }
        pvals.append((ft, u.pvalue))
    # BH
    pv_sorted = sorted(pvals, key=lambda x: x[1])
    for rank, (ft, p) in enumerate(pv_sorted, 1):
        e2[ft]["bh_q"] = round(min(1.0, p * len(pvals) / rank), 5)

    # ---- E3: poda diagnostica ----
    w_vals = sorted(e["w"] for e in edges)
    q1 = w_vals[m // 4]
    med_w = w_vals[m // 2]
    bet_thresh = np.percentile([r["edge_betweenness"] for r in edge_rows], 95)

    def prune(cond_name, keep_fn):
        H = nx.Graph()
        H.add_nodes_from(docs)
        cut = []
        for r in edge_rows:
            if keep_fn(r):
                H.add_edge(r["doc_i"], r["doc_j"])
            else:
                cut.append(r)
        comps = sorted(nx.connected_components(H), key=len, reverse=True)
        sizes = [len(c) for c in comps]
        big = comps[0] if comps else set()
        pair_ret = sum(s * (s - 1) // 2 for s in sizes) / total_pairs
        long_kept = sum(1 for r in edge_rows if keep_fn(r) and r["largo"])
        obj = Counter(x for d in big for x in refs[d]["objeto"])
        terr = Counter(x for d in big for x in refs[d]["territorio"])
        fechas = sorted(meta[d]["fecha"] for d in big if meta[d]["fecha"])
        return {
            "condicion": cond_name, "aristas_cortadas": len(cut),
            "n_componentes": len(sizes), "tamanos_top6": sizes[:6],
            "docs_separados_del_mayor": n - sizes[0] if sizes else n,
            "pair_retention": round(pair_ret, 4),
            "enlaces_largos_conservados": long_kept,
            "objeto_dominante_mayor": obj.most_common(1)[0][0] if obj else "",
            "territorios_mayor": len(terr),
            "rango_temporal_mayor": f"{fechas[0]}..{fechas[-1]}" if fechas else "",
        }, cut

    prune_results = []
    cut_samples = {}
    conds = [
        ("P0_puentes", lambda r: not r["puente"]),
        ("P1_sin_triangulos_q1w", lambda r: not (r["triangulos"] == 0 and r["w"] <= q1)),
        ("P2_bet_top5_w_bajo", lambda r: not (r["edge_betweenness"] >= bet_thresh and r["w"] <= med_w)),
        ("S_puente_w048", lambda r: not (r["puente"] and r["w"] < 0.48)),
        ("S_puente_w050", lambda r: not (r["puente"] and r["w"] < 0.50)),
        ("S_puente_w052", lambda r: not (r["puente"] and r["w"] < 0.52)),
    ]
    for name, fn in conds:
        res, cut = prune(name, fn)
        prune_results.append(res)
        cut_samples[name] = cut

    # ---- chaining ----
    direct = {frozenset((e["doc_i"], e["doc_j"])) for e in edges}
    spl = dict(nx.all_pairs_shortest_path_length(G))
    trans_lengths = Counter()
    hetero_trans = 0
    for i, j in combinations(docs, 2):
        if frozenset((i, j)) in direct:
            continue
        L = spl[i][j]
        trans_lengths[L] += 1
        if (refs[i]["territorio"] and refs[j]["territorio"]
                and not (refs[i]["territorio"] & refs[j]["territorio"])
                and refs[i]["objeto"] and refs[j]["objeto"]
                and not (refs[i]["objeto"] & refs[j]["objeto"])):
            hetero_trans += 1
    bridge_damage = []
    for b in bridges:
        H = G.copy()
        H.remove_edge(*tuple(b))
        sizes = sorted((len(c) for c in nx.connected_components(H)), reverse=True)
        bridge_damage.append({"puente": sorted(b), "w": G.edges[tuple(b)]["w"],
                              "dano_docs_separados": sizes[1] if len(sizes) > 1 else 0})
    bridge_damage.sort(key=lambda x: -x["dano_docs_separados"])
    # pares dependientes de puentes: desconectados al quitar todos los puentes
    Hnb = G.copy()
    Hnb.remove_edges_from(tuple(b) for b in bridges)
    comp_nb = {v: k for k, c in enumerate(nx.connected_components(Hnb)) for v in c}
    bridge_dep_pairs = sum(1 for i, j in combinations(docs, 2)
                           if comp_nb[i] != comp_nb[j])

    chaining = {
        "pares_totales": total_pairs, "pares_directos": m,
        "pares_solo_transitivos": total_pairs - m,
        "longitud_caminos_transitivos": dict(sorted(trans_lengths.items())),
        "pares_dependientes_de_puentes": bridge_dep_pairs,
        "pares_heterogeneos_transitivos_obj_y_terr": hetero_trans,
        "dano_por_puente_top10": bridge_damage[:10],
    }

    # ---- muestra ciega E1 ----
    rng = random.Random(BLIND_SEED)
    lab_by_algo = {a: runs[a + "_consensus"][0] for a in ALGOS if a != "dsu"}

    def pair_strata():
        intra, inter = [], []
        for a, lab in lab_by_algo.items():
            arr = np.array(lab)
            for i, j in combinations(range(n), 2):
                same_comm = lab[i] == lab[j]
                has_edge = frozenset((docs[i], docs[j])) in direct
                if same_comm and has_edge:
                    intra.append((docs[i], docs[j], a))
                elif not same_comm and spl[docs[i]][docs[j]] <= 2:
                    inter.append((docs[i], docs[j], a))
        return intra, inter

    intra_pool, inter_pool = pair_strata()
    bridge_pool = [(tuple(b)[0], tuple(b)[1], "puente") for b in bridges]
    longfrag_pool = [(r["doc_i"], r["doc_j"], "largo_bajo_embed")
                     for r in edge_rows if r["largo"] and r["embeddedness"] <= 0.05]

    def sample_unique(pool, k):
        seen, out = set(), []
        rng.shuffle(pool)
        for a_, b_, tag in pool:
            fs = frozenset((a_, b_))
            if fs in seen:
                continue
            seen.add(fs)
            out.append((a_, b_, tag))
            if len(out) == k:
                break
        return out

    sel = (
        [("intra",) + p for p in sample_unique(intra_pool, 40)]
        + [("inter",) + p for p in sample_unique(inter_pool, 40)]
        + [("puente",) + p for p in sample_unique(bridge_pool, 20)]
        + [("largo",) + p for p in sample_unique(longfrag_pool, 20)]
    )
    rng.shuffle(sel)
    sheet, key = [], {}
    for k_, (stratum, a_, b_, tag) in enumerate(sel):
        iid = f"H{k_:03d}"
        key[iid] = {"estrato": stratum, "detalle": tag, "a": a_, "b": b_}
        sheet.append({
            "item_id": iid,
            "doc_a": {"id": a_, "fecha": meta[a_]["fecha"],
                      "titulo": meta[a_]["titulo"], "texto": meta[a_]["texto"]},
            "doc_b": {"id": b_, "fecha": meta[b_]["fecha"],
                      "titulo": meta[b_]["titulo"], "texto": meta[b_]["texto"]},
            "pregunta": "mismo_proceso | relacionado | no_relacionado | indeterminado",
            "veredicto": "",
        })
    blind = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "seed": BLIND_SEED,
        "instrucciones": (
            "Revision ciega H0000. No se revela algoritmo, comunidad, puntaje, "
            "motivo de seleccion ni hipotesis. Juzgar identidad procesual con "
            "texto completo. Adjudicacion EXTERNA; el desarrollador no adjudica."),
        "n_items": len(sheet), "items": sheet,
    }
    protocolo = {
        "integracion": (
            "1) adjudicadores externos (>=2 IA + humano si disponible) completan "
            "la hoja sin la clave; 2) se congelan veredictos con hash; 3) solo "
            "entonces se cruza con la clave; 4) intra vs inter por algoritmo "
            "decide H_split/H_keep; 5) desacuerdos van a cola focalizada."),
    }

    # ---- escritura de artefactos ----
    def wcsv(name, rows, fields):
        with open(OUT / name, "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fields)
            w.writeheader()
            w.writerows(rows)

    wcsv("H0000_01_SUBGRAPH_CANONICAL.csv", edge_rows, list(edge_rows[0].keys()))
    node_rows = []
    for d in docs:
        i = idx[d]
        node_rows.append({
            "doc_id": d, "fecha": meta[d]["fecha"],
            "objeto": ";".join(sorted(refs[d]["objeto"])),
            "territorio": ";".join(sorted(refs[d]["territorio"])),
            "actores": ";".join(sorted(refs[d]["actor"])),
            "grado": G.degree(d),
            "weighted_degree": round(sum(G.edges[d, nb]["weight"] for nb in G[d]), 3),
            **{f"comunidad_{a}": runs[a + "_consensus"][0][i] for a in ALGOS if a != "dsu"},
            "bicomponentes": len(bicomp_of[d]),
            "articulacion": d in art_points,
            "grado1_dependiente": G.degree(d) == 1,
            "kcore": core[d],
        })
    wcsv("H0000_02_NODE_METRICS.csv", node_rows, list(node_rows[0].keys()))
    wcsv("H0000_03_EDGE_METRICS.csv", edge_rows, list(edge_rows[0].keys()))
    wcsv("H0000_05_PARTITION_COMPARISON.csv",
         [{k: json.dumps(v, ensure_ascii=False) if isinstance(v, (list, dict)) else v
           for k, v in r.items()} for r in partition_rows],
         list(partition_rows[0].keys()))
    wcsv("H0000_07_PRUNING_DIAGNOSTICS.csv",
         [{k: json.dumps(v) if isinstance(v, list) else v for k, v in r.items()}
          for r in prune_results], list(prune_results[0].keys()))

    (OUT / "H0000_08_BLIND_REVIEW_SHEET.json").write_text(
        json.dumps(blind, ensure_ascii=False, indent=1), encoding="utf-8")
    (OUT / "H0000_09_BLIND_KEY_DO_NOT_OPEN.json").write_text(
        json.dumps({"protocolo": protocolo, "clave": key}, ensure_ascii=False, indent=1),
        encoding="utf-8")

    deg = [G.degree(d) for d in docs]
    topo = {
        "verificacion": {"frozen": FROZEN, "observed": observed, "match": not discrepancias},
        "densidad": round(density, 4),
        "grado": {"min": min(deg), "p50": float(np.median(deg)), "max": max(deg)},
        "clustering_medio": round(float(np.mean(list(clustering.values()))), 4),
        "diametro": nx.diameter(G),
        "camino_medio": round(nx.average_shortest_path_length(G), 3),
        "kcore_max": max(core.values()),
        "docs_kcore_max": sum(1 for v in core.values() if v == max(core.values())),
        "bicomponentes": len(bicomp),
        "articulaciones": len(art_points),
        "aristas_largas": sum(1 for e in edges if e["dias"] > 365),
        "pct_largas": round(100 * sum(1 for e in edges if e["dias"] > 365) / m, 1),
        "poda_puentes_debiles_tamanos": wp_sizes[:8],
        "docs_por_ano": dict(sorted(Counter(
            meta[d]["fecha"][:4] for d in docs if meta[d]["fecha"]).items())),
        "e2_puentes_vs_no_puentes": e2,
        "chaining": chaining,
    }
    (OUT / "H0000_04_TOPOLOGY_REPORT.md").write_text(
        "# H0000 — Topologia y diagnostico (Fase 3B)\n\n```json\n"
        + json.dumps(topo, ensure_ascii=False, indent=1) + "\n```\n",
        encoding="utf-8")
    (OUT / "H0000_06_STABILITY_REPORT.md").write_text(
        "# H0000 — Estabilidad de particiones (Fase 3B)\n\n```json\n"
        + json.dumps(stability, ensure_ascii=False, indent=1) + "\n```\n",
        encoding="utf-8")

    lock = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "git_head": subprocess.run(["git", "rev-parse", "HEAD"], cwd=BASE,
                                   capture_output=True, text=True).stdout.strip(),
        "codigo_v1_no_modificado": True,
        "umbral_no_modificado": True,
        "candidatos_no_modificados": True,
        "grafo_congelado": {"threads_sha256": sha(THREADS), "edges_sha256": sha(EDGES)},
        "algoritmos_solo_diagnosticos": True,
        "adjudicacion_no_ejecutada": True,
        "arquitectura_v2_no_seleccionada": True,
        "ganador_empirico_no_declarado": True,
        "discrepancias_registradas": {
            "summaries_legacy_working_vs_commit": (
                "outputs/f2_threads_summary.json y F4_MANIFEST.json difieren del "
                "commit cf5ab5e1 por campos de trazabilidad regenerados post-commit; "
                "los CSV congelados coinciden con el manifest (verify_preservation)."),
        },
        "leiden_infomap_via": "python-igraph (leidenalg/infomap standalone no instalados)",
        "leiden_cpm_resolution": density,
    }
    (OUT / "H0000_11_EXPERIMENT_LOCK.json").write_text(
        json.dumps(lock, ensure_ascii=False, indent=1), encoding="utf-8")

    manifest = {"generated_utc": datetime.now(timezone.utc).isoformat(), "files": {}}
    for p in sorted(OUT.glob("H0000_*")):
        manifest["files"][p.name] = sha(p)
    manifest["files"]["verify_preservation.py"] = sha(OUT / "verify_preservation.py")
    manifest["files"]["h0000_diagnostics.py"] = sha(Path(__file__))
    (OUT / "H0000_10_MANIFEST.json").write_text(
        json.dumps(manifest, indent=1), encoding="utf-8")

    print(json.dumps({
        "verificacion": observed,
        "topologia": {k: topo[k] for k in ("densidad", "diametro", "camino_medio",
                                           "kcore_max", "docs_kcore_max",
                                           "articulaciones", "pct_largas")},
        "particiones": [{k: r[k] for k in ("algoritmo", "n_comunidades",
                                           "tamanos_top5", "seed_ari_mean",
                                           "drop10_ari_mean")} for r in partition_rows],
        "e2_resumen": {ft: {"p": e2[ft]["mw_p"], "q": e2[ft]["bh_q"]} for ft in e2},
        "chaining_resumen": {k: chaining[k] for k in (
            "pares_solo_transitivos", "pares_dependientes_de_puentes",
            "pares_heterogeneos_transitivos_obj_y_terr")},
        "muestra_ciega": len(sheet),
    }, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
