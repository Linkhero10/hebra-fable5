# Fase 3B - ADENDA diagnostica (correcciones del auditor).
# Solo lectura de artefactos v1 y del diagnostico previo H0000_*.
# No modifica v1 ni el informe original. Todo lo aqui computado es
# diagnostico E1-E4 (sin seleccion de arquitectura v2).

import csv
import json
import math
import random
from collections import Counter, defaultdict
from datetime import datetime, timezone
from itertools import combinations
from pathlib import Path

import networkx as nx
import numpy as np
import igraph as ig

BASE = Path(__file__).resolve().parents[1]
OUT = Path(__file__).resolve().parent
ROOT = BASE.parents[3]
CORPUS = ROOT / "01_bases_de_datos/03_refiltro_api_qwen_y_base_actual/06_base_actual_fusionada_3742_incluidas.csv"
THREADS = BASE / "outputs/f2b_idf_v2_L2_threads.csv"
EDGES = BASE / "outputs/f2b_idf_v2_L2_edges.csv"
REFS = BASE / "outputs/f1v2_referents.csv"

SEEDS = list(range(20))
NULL_B = 300


def load_thread(tid):
    docs = set()
    with open(THREADS, encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            if r["thread_id"] == tid:
                docs.add(r["doc_id"])
    edges = []
    with open(EDGES, encoding="utf-8", newline="") as f:
        for e in csv.DictReader(f):
            if e["doc_i"] in docs and e["doc_j"] in docs:
                edges.append((e["doc_i"], e["doc_j"], float(e["w"]), int(e["dias"])))
    return sorted(docs), edges


def vi(labels_a, labels_b):
    n = len(labels_a)
    ca, cb = Counter(labels_a), Counter(labels_b)
    joint = Counter(zip(labels_a, labels_b))
    Ha = -sum((c / n) * math.log(c / n) for c in ca.values())
    Hb = -sum((c / n) * math.log(c / n) for c in cb.values())
    Hab = -sum((c / n) * math.log(c / n) for c in joint.values())
    return 2 * Hab - Ha - Hb


def main() -> None:
    docs, edges_raw = load_thread("H0000")
    n = len(docs)
    idx = {d: i for i, d in enumerate(docs)}
    G = nx.Graph()
    G.add_nodes_from(docs)
    for i, j, w, dt in edges_raw:
        G.add_edge(i, j, weight=w, dias=dt)
    m = G.number_of_edges()
    bridges = [tuple(sorted(b)) for b in nx.bridges(G)]
    total_pairs = n * (n - 1) // 2

    refs = defaultdict(lambda: defaultdict(set))
    with open(REFS, encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            if r["doc_id"] in G:
                refs[r["doc_id"]][r["tipo"]].add(r["referente"])

    # ================= 1. Definiciones de satelite y componentes completos =================
    deg = dict(G.degree())
    grado_le2 = [d for d in docs if deg[d] <= 2]
    grado_eq1 = [d for d in docs if deg[d] == 1]
    art_points = set(nx.articulation_points(G))
    bicomp = list(nx.biconnected_components(G))
    small_bicomp_nodes = sorted({v for c in bicomp if len(c) <= 2 for v in c})

    Gp0 = G.copy()
    Gp0.remove_edges_from(bridges)
    comps_p0 = sorted((len(c) for c in nx.connected_components(Gp0)), reverse=True)

    weak_bridges = [b for b in bridges if G.edges[b]["weight"] < 0.50]
    Gwk = G.copy()
    Gwk.remove_edges_from(weak_bridges)
    comps_wk = sorted((len(c) for c in nx.connected_components(Gwk)), reverse=True)

    satellite_defs = {
        "advertencia": (
            "El auditor detecto que 'satelite' no tenia definicion operacional "
            "estable y que las listas de tamanos de componentes estaban "
            "truncadas a los primeros 8 al imprimirse, sin sumar 170. Se listan "
            "aqui las distribuciones COMPLETAS y cinco definiciones distintas, "
            "sin declarar ninguna 'canonica'."
        ),
        "grado_le2_n": len(grado_le2), "grado_le2_ids": grado_le2,
        "grado_eq1_n": len(grado_eq1), "grado_eq1_ids": grado_eq1,
        "nodos_articulacion_n": len(art_points),
        "nodos_en_bicomponentes_pequenos_le2_n": len(small_bicomp_nodes),
        "componentes_tras_cortar_TODOS_los_puentes_23": {
            "n_componentes": len(comps_p0), "tamanos_completos": comps_p0,
            "suma_verificacion": sum(comps_p0),
        },
        "componentes_tras_cortar_puentes_debiles_w050_15": {
            "n_componentes": len(comps_wk), "tamanos_completos": comps_wk,
            "suma_verificacion": sum(comps_wk),
        },
    }

    # ================= 2. Tautologia de triangulos/embeddedness en puentes =================
    triangulos_por_arista = {}
    for i, j, w, dt in edges_raw:
        cn = len(set(G[i]) & set(G[j]))
        triangulos_por_arista[frozenset((i, j))] = cn
    bridge_triangles = [triangulos_por_arista[frozenset(b)] for b in bridges]
    nonbridge_triangles = [v for k, v in triangulos_por_arista.items()
                           if tuple(sorted(k)) not in set(bridges)]
    tautologia_nota = {
        "afirmacion_corregida": (
            "Un puente topologico no puede pertenecer a un ciclo (definicion de "
            "puente), por lo que triangulos=0 y embeddedness=0 en TODO puente es "
            "consecuencia matematica directa de la definicion, no un hallazgo "
            "estadistico independiente. Los tests Mann-Whitney sobre estas dos "
            "variables se retiran como evidencia sustantiva; se conservan solo "
            "como verificacion de consistencia (deben dar exactamente 0)."
        ),
        "puentes_triangulos_max_esperado_0": max(bridge_triangles),
        "no_puentes_triangulos_min": min(nonbridge_triangles) if nonbridge_triangles else None,
        "variables_sustantivas_no_tautologicas": [
            "s_emb (mas alta en puentes)", "s_ref (mas baja en puentes)",
            "dias (mucho menor en puentes)", "idf_max_ref_compartido (mas alta)",
        ],
    }

    # ================= 3. Perfil de dano por puente (bridge tree) =================
    Gnb = G.copy()
    Gnb.remove_edges_from(bridges)
    block_of = {}
    for k, comp in enumerate(nx.connected_components(Gnb)):
        for v in comp:
            block_of[v] = k
    BT = nx.Graph()
    BT.add_nodes_from(set(block_of.values()))
    for b in bridges:
        u, v = b
        BT.add_edge(block_of[u], block_of[v], puente=b)
    bt_dist = dict(nx.all_pairs_shortest_path_length(BT))

    per_bridge_damage = []
    for b in bridges:
        u, v = b
        w = G.edges[b]["weight"]
        Hcopy = G.copy()
        Hcopy.remove_edge(u, v)
        sizes = sorted((len(c) for c in nx.connected_components(Hcopy)), reverse=True)
        separated = sizes[1] if len(sizes) > 1 else 0
        per_bridge_damage.append({
            "puente": [u, v], "w": round(w, 4),
            "dano_docs_separados_individual": separated,
        })
    per_bridge_damage.sort(key=lambda x: -x["dano_docs_separados_individual"])

    # clasificar pares dependientes por longitud de camino en el arbol de puentes
    path_len_counts = Counter()
    sole_bridge_pairs = Counter()  # puente -> n pares con ese puente como UNICO separador
    multi_bridge_pairs = 0
    for i, j in combinations(docs, 2):
        bi, bj = block_of[i], block_of[j]
        if bi == bj:
            continue
        L = bt_dist[bi][bj]
        path_len_counts[L] += 1
        if L == 1:
            path = nx.shortest_path(BT, bi, bj)
            edge_data = BT.edges[path[0], path[1]]
            sole_bridge_pairs[tuple(edge_data["puente"])] += 1
        else:
            multi_bridge_pairs += 1

    for row in per_bridge_damage:
        b_key = tuple(row["puente"])
        row["pares_donde_es_UNICO_separador"] = sole_bridge_pairs.get(b_key, 0)

    top3_sole = sorted(sole_bridge_pairs.values(), reverse=True)[:3]
    total_sole = sum(sole_bridge_pairs.values())
    dano_profile = {
        "pares_dependientes_totales": sum(path_len_counts.values()),
        "distribucion_longitud_camino_en_arbol_de_puentes": dict(sorted(path_len_counts.items())),
        "pares_con_UN_solo_puente_como_separador": total_sole,
        "pares_que_requieren_2_o_mas_puentes_en_su_camino": multi_bridge_pairs,
        "concentracion_top3_puentes_pct_de_pares_de_unico_separador": (
            round(100 * sum(top3_sole) / total_sole, 1) if total_sole else None
        ),
        "nota": (
            "path_len=1 significa que existe un UNICO puente cuya remocion "
            "desconecta ese par (dependencia simple); path_len>=2 significa que "
            "el par depende de una CADENA de puentes en el arbol de bloques."
        ),
        "perfil_completo_por_puente": per_bridge_damage,
    }

    # ================= 4. Baseline de heterogeneidad =================
    def hetero(i, j):
        return (bool(refs[i]["territorio"]) and bool(refs[j]["territorio"])
                and not (refs[i]["territorio"] & refs[j]["territorio"])
                and bool(refs[i]["objeto"]) and bool(refs[j]["objeto"])
                and not (refs[i]["objeto"] & refs[j]["objeto"]))

    direct_pairs = {frozenset((i, j)) for i, j, *_ in edges_raw}
    n_direct_hetero = sum(1 for i, j, *_ in edges_raw if hetero(i, j))
    all_pairs_hetero_h0000 = sum(1 for i, j in combinations(docs, 2) if hetero(i, j))
    transitive_only_hetero = sum(
        1 for i, j in combinations(docs, 2)
        if frozenset((i, j)) not in direct_pairs and hetero(i, j)
    )

    def thread_baseline(tid):
        tdocs, _ = load_thread(tid)
        if len(tdocs) < 3:
            return None
        allp = list(combinations(tdocs, 2))
        h = sum(1 for i, j in allp if hetero(i, j))
        return {"thread": tid, "n_docs": len(tdocs), "n_pares": len(allp),
                "pct_heterogeneo": round(100 * h / len(allp), 2)}

    baselines_threads = [thread_baseline(t) for t in ("H0001", "H0002", "H0004")]
    baselines_threads = [b for b in baselines_threads if b]

    rng = random.Random(20260790)
    node_list = docs
    ref_pool = {d: (frozenset(refs[d]["territorio"]), frozenset(refs[d]["objeto"])) for d in docs}
    null_counts = []
    for _ in range(NULL_B):
        perm = node_list[:]
        rng.shuffle(perm)
        assign = dict(zip(node_list, perm))  # nodo real -> nodo donante de referentes
        cnt = 0
        for i, j in combinations(docs, 2):
            if frozenset((i, j)) in direct_pairs:
                continue
            ti, oi = ref_pool[assign[i]]
            tj, oj = ref_pool[assign[j]]
            if ti and tj and not (ti & tj) and oi and oj and not (oi & oj):
                cnt += 1
        null_counts.append(cnt)
    null_arr = np.array(null_counts)
    p_emp = (1 + np.sum(null_arr >= transitive_only_hetero)) / (len(null_arr) + 1)

    heterogeneidad = {
        "aristas_directas_heterogeneas_pct": round(100 * n_direct_hetero / m, 2),
        "todas_las_parejas_dentro_H0000_heterogeneas_pct": round(
            100 * all_pairs_hetero_h0000 / total_pairs, 2),
        "solo_transitivas_heterogeneas_pct": round(
            100 * transitive_only_hetero / (total_pairs - m), 2),
        "solo_transitivas_heterogeneas_n": transitive_only_hetero,
        "baseline_hilos_conocidos_grandes": baselines_threads,
        "nulo_permutacion_referentes_preservando_grafo": {
            "B": NULL_B, "seed": 20260790,
            "media_nula": round(float(np.mean(null_arr)), 1),
            "p95_nulo": round(float(np.percentile(null_arr, 95)), 1),
            "observado": transitive_only_hetero,
            "p_empirico_mayor_igual": round(float(p_emp), 4),
        },
        "interpretacion": (
            "El conteo bruto de 5.637 no es evidencia cuantitativa de mezcla "
            "por si solo. Se compara contra: (a) tasa en aristas directas "
            "(deberian ser mayormente NO heterogeneas si el enlace exige "
            "referente compartido); (b) tasa en TODOS los pares del propio "
            "H0000 y de hilos grandes conocidos como referencia descriptiva; "
            "(c) un nulo de permutacion que baraja que documento tiene que "
            "conjunto de referentes, preservando el grafo, para estimar la "
            "tasa esperada por azar dada la topologia."
        ),
    }

    # ================= 5. DSU vs comunidades: robustez comparable =================
    def perturb_edges(seed, frac):
        rng2 = random.Random(seed)
        keep = rng2.sample(range(m), int(round(m * (1 - frac))))
        return [edges_raw[i] for i in keep]

    def labels_from_components(edge_subset):
        H = nx.Graph()
        H.add_nodes_from(docs)
        for i, j, w, dt in edge_subset:
            H.add_edge(i, j)
        lab = {}
        for k, c in enumerate(nx.connected_components(H)):
            for v in c:
                lab[v] = k
        return [lab[d] for d in docs]

    def labels_community(edge_subset, kind, seed):
        H = nx.Graph()
        H.add_nodes_from(docs)
        for i, j, w, dt in edge_subset:
            H.add_edge(i, j, weight=w)
        if kind == "louvain":
            comms = nx.community.louvain_communities(H, weight="weight", seed=seed)
            lab = {}
            for k, c in enumerate(comms):
                for v in c:
                    lab[v] = k
            return [lab[d] for d in docs]
        h_ig = ig.Graph(n=n, edges=[(idx[a], idx[b]) for a, b, *_ in edge_subset])
        h_ig.es["weight"] = [w for _, _, w, _ in edge_subset]
        random.seed(seed)
        ig.set_random_number_generator(random)
        if kind == "leiden_mod":
            p = h_ig.community_leiden(objective_function="modularity",
                                      weights="weight", n_iterations=5)
        elif kind == "infomap":
            p = h_ig.community_infomap(edge_weights="weight", trials=5)
        return p.membership

    base_dsu = [0] * n  # una sola clase
    base_louvain_runs = [labels_community(edges_raw, "louvain", s) for s in SEEDS]
    base_leiden_runs = [labels_community(edges_raw, "leiden_mod", s) for s in SEEDS]
    base_infomap_runs = [labels_community(edges_raw, "infomap", s) for s in SEEDS]

    def coassigned_pairs(labels):
        groups = defaultdict(list)
        for i, lab in enumerate(labels):
            groups[lab].append(i)
        pairs = set()
        for g in groups.values():
            for a, b in combinations(sorted(g), 2):
                pairs.add((a, b))
        return pairs

    def retention_and_vi(base_labels_list, kind, frac):
        base_pairs_list = [coassigned_pairs(bl) for bl in base_labels_list]
        retentions, vis, main_sizes, n_comms = [], [], [], []
        for s in SEEDS:
            sub = perturb_edges(s, frac)
            if kind == "dsu":
                pert_labels = labels_from_components(sub)
            else:
                pert_labels = labels_community(sub, kind, s)
            base_pairs = base_pairs_list[s] if kind != "dsu" else set(combinations(range(n), 2))
            pert_pairs = coassigned_pairs(pert_labels)
            ret = len(base_pairs & pert_pairs) / len(base_pairs) if base_pairs else 1.0
            retentions.append(ret)
            base_lab = base_labels_list[s] if kind != "dsu" else base_dsu
            vis.append(vi(base_lab, pert_labels))
            sizes = Counter(pert_labels)
            main_sizes.append(max(sizes.values()))
            n_comms.append(len(sizes))
        return {
            "retencion_pares_media": round(float(np.mean(retentions)), 4),
            "VI_media": round(float(np.mean(vis)), 4),
            "componente_o_comunidad_principal_media": round(float(np.mean(main_sizes)), 1),
            "n_comunidades_media": round(float(np.mean(n_comms)), 1),
        }

    robustez = {"advertencia": (
        "DSU produce una sola clase en el grafo original (todos coasignados "
        "trivialmente); comparar su ARI bajo perturbacion contra Louvain/Leiden/"
        "Infomap (que ya parten de multiples comunidades) no es una comparacion "
        "simetrica. Aqui se reportan metricas comparables: retencion de pares "
        "originalmente coasignados, VI, tamano de la clase/comunidad principal "
        "y numero de comunidades, bajo drop 5% y 10%, para las 4 configuraciones."
    )}
    for frac, tag in ((0.05, "drop5"), (0.10, "drop10")):
        robustez[tag] = {
            "dsu": retention_and_vi([base_dsu] * len(SEEDS), "dsu", frac),
            "louvain": retention_and_vi(base_louvain_runs, "louvain", frac),
            "leiden_mod": retention_and_vi(base_leiden_runs, "leiden_mod", frac),
            "infomap": retention_and_vi(base_infomap_runs, "infomap", frac),
        }
    robustez["formulacion_corregida"] = (
        "La conectividad de H0000 bajo DSU es sensible al edge-drop (retencion "
        "de pares y tamano de componente principal caen mas que en las "
        "particiones comunitarias bajo la misma perturbacion). Esto NO se "
        "interpreta como 'los algoritmos comunitarios son metodologicamente "
        "mejores'; es una propiedad de sensibilidad estructural, pendiente de "
        "adjudicacion para decidir su relevancia procesual."
    )

    # ================= 6. Nucleo "tematico" no "procesual" =================
    core_note = {
        "correccion": (
            "El objeto dominante 'estrategia nacional del litio' identifica "
            "estabilidad de un MACROTEMA/marco politico bajo todas las podas, "
            "no que los 148 documentos del nucleo constituyan un unico proceso. "
            "El macrotema puede abarcar multiples salares, proyectos, empresas "
            "y procesos de consulta distintos. Esta distincion solo puede "
            "resolverse con la adjudicacion ciega de la muestra sellada."
        ),
    }

    # ================= 7. Grid de resolucion Leiden-CPM =================
    grid_solicitado = [0.25, 0.5, 1.0, 1.5, 2.0]
    g_ig = ig.Graph(n=n, edges=[(idx[i], idx[j]) for i, j, *_ in edges_raw])
    g_ig.es["weight"] = [w for _, _, w, _ in edges_raw]
    density = 2 * m / (n * (n - 1))
    grid_rows = []
    for res in [density] + grid_solicitado:
        random.seed(42)
        ig.set_random_number_generator(random)
        p = g_ig.community_leiden(objective_function="CPM", resolution=res,
                                  weights="weight", n_iterations=5)
        sizes = sorted(Counter(p.membership).values(), reverse=True)
        grid_rows.append({
            "resolucion": res, "es_default_densidad": res == density,
            "n_comunidades": len(sizes), "tamanos_top5": sizes[:5],
            "singletons": sum(1 for s in sizes if s == 1),
        })
    leiden_grid_note = (
        "El informe original solo probo resolucion=densidad (0.062) sin grid "
        "explicito. Las instrucciones de Fase 3B recibidas por este agente no "
        "especificaban un grid numerico; el auditor sugirio {0.25,0.5,1,1.5,2}, "
        "que se ejecuta aqui integramente junto al valor por defecto, sin "
        "adoptar ninguno como eleccion final."
    )

    # ================= escritura =================
    (OUT / "H0000_13_ADDENDUM_SATELLITE_DEFINITIONS.json").write_text(
        json.dumps(satellite_defs, ensure_ascii=False, indent=1), encoding="utf-8")
    (OUT / "H0000_12_ADDENDUM_BRIDGE_DAMAGE_PROFILE.json").write_text(
        json.dumps(dano_profile, ensure_ascii=False, indent=1), encoding="utf-8")
    (OUT / "H0000_14_ADDENDUM_HETEROGENEITY_BASELINE.json").write_text(
        json.dumps(heterogeneidad, ensure_ascii=False, indent=1), encoding="utf-8")
    (OUT / "H0000_15_ADDENDUM_DSU_VS_COMMUNITY_ROBUSTNESS.json").write_text(
        json.dumps(robustez, ensure_ascii=False, indent=1), encoding="utf-8")
    with open(OUT / "H0000_16_ADDENDUM_LEIDEN_CPM_GRID.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(grid_rows[0].keys()))
        w.writeheader()
        for r in grid_rows:
            w.writerow({k: (json.dumps(v) if isinstance(v, list) else v) for k, v in r.items()})

    print(json.dumps({
        "satelites": {k: satellite_defs[k] for k in (
            "grado_le2_n", "grado_eq1_n", "nodos_articulacion_n")},
        "componentes_p0_suma": satellite_defs["componentes_tras_cortar_TODOS_los_puentes_23"]["suma_verificacion"],
        "componentes_wk_suma": satellite_defs["componentes_tras_cortar_puentes_debiles_w050_15"]["suma_verificacion"],
        "tautologia": tautologia_nota["afirmacion_corregida"][:80] + "...",
        "dano_perfil_top3": dano_profile["perfil_completo_por_puente"][:3],
        "concentracion_top3": dano_profile["concentracion_top3_puentes_pct_de_pares_de_unico_separador"],
        "heterogeneidad": {
            "directas_pct": heterogeneidad["aristas_directas_heterogeneas_pct"],
            "transitivas_pct": heterogeneidad["solo_transitivas_heterogeneas_pct"],
            "nulo_p": heterogeneidad["nulo_permutacion_referentes_preservando_grafo"]["p_empirico_mayor_igual"],
            "baselines": heterogeneidad["baseline_hilos_conocidos_grandes"],
        },
        "robustez_drop10": robustez["drop10"],
        "leiden_grid": grid_rows,
    }, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
