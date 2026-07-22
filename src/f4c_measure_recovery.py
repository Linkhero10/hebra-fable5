# F4-C paso 3-4 — Adjudicacion documental y recuperacion del gold sellado.
# Regla de adjudicacion MECANICA (identica a la usada al construir FN30):
# tokens >=5 letras del titulo aproximado + localizacion del caso INDH,
# excluyendo genericos; un doc pertenece al caso si su titulo contiene algun
# token. Un caso es "documentado" si tiene >=3 docs adjudicados.
# Conjunto confirmatorio: casos documentados con flag_contaminado=false.
# Metricas por caso y por sistema (HEBRA L2, A1 solo-ref, A4 sin-largos,
# A2 solo-emb, familias BERTopic, OmegaEvolve-S):
#   pureza  = |docs_caso en mejor grupo| / |mejor grupo|
#   cobertura = |docs_caso en algun grupo del sistema| / |docs_caso|
#   fragmentos = numero de grupos con >=10% de los docs del caso
#   mejor_recall = |docs_caso en mejor grupo| / |docs_caso|
#   perdidos = docs_caso sin grupo
# INDH no es verdad perfecta: la adjudicacion por titulo es aproximada y se
# reporta como tal; los casos contaminados solo aparecen como smoke pero
# NO entran en los promedios confirmatorios.

import csv
import json
import re
import unicodedata
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4].parent
CORPUS = ROOT / "01_bases_de_datos/03_refiltro_api_qwen_y_base_actual/06_base_actual_fusionada_3742_incluidas.csv"
FAM = ROOT / "09_metodologia/faro_model_research/promoted_family_assignments.csv"
OMEGA = ROOT / "09_metodologia/faro_model_research/omegaevolve/selective_document_assignments.csv"
OUT_DIR = Path(__file__).resolve().parents[1] / "outputs"
GOLD = OUT_DIR / "f4c_external_gold_SEALED.json"

SYSTEMS = {
    "HEBRA_L2": OUT_DIR / "f2b_idf_v2_L2_threads.csv",
    "A1_solo_ref": OUT_DIR / "f2b_idf_v2ablA1_L2_threads.csv",
    "A4_sin_largos": OUT_DIR / "f2b_idf_v2ablA4_L2_threads.csv",
    "A2_solo_emb": OUT_DIR / "f4d_onlyemb_threads.csv",
}
GENERIC = {"region", "provincia", "comuna", "chile", "nacional", "parque",
           "reserva", "central", "proyecto", "minera", "mineria", "energia",
           "planta", "sector", "empresa", "termoelectrica", "hidroelectrica"}


def deacc(s):
    s = unicodedata.normalize("NFKD", s.lower())
    return "".join(c for c in s if not unicodedata.combining(c))


def main() -> None:
    titles = {}
    with open(CORPUS, encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            titles[row["id"]] = deacc(row.get("titulo") or "")

    def load_groups(path, id_col, grp_col):
        g = {}
        with open(path, encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                v = row.get(grp_col, "")
                if v not in ("", "-1", None):
                    g[row[id_col]] = v
        return g

    systems = {}
    for name, p in SYSTEMS.items():
        systems[name] = load_groups(p, "doc_id", "thread_id")
    systems["BERTopic_familias"] = load_groups(FAM, "id", "family_topic")
    systems["OmegaEvolve_S"] = load_groups(OMEGA, "id", "selective_state_id")

    gold = json.loads(GOLD.read_text(encoding="utf-8"))
    per_case, confirm = [], []
    for c in gold["casos"]:
        toks = [w for w in re.findall(r"[a-zñ]{5,}", deacc(
            c["titulo_aprox"] + " " + c["localizacion"])) if w not in GENERIC]
        toks = list(dict.fromkeys(toks))[:6]
        docs = [d for d, t in titles.items() if any(tk in t for tk in toks)]
        entry = {"case_idx": c["case_idx"], "tokens": toks,
                 "docs_adjudicados": len(docs),
                 "documentado": len(docs) >= 3,
                 "flag_contaminado": c["flag_contaminado_desarrollo"],
                 "sistemas": {}}
        if len(docs) >= 3 and len(docs) <= 400:
            dset = set(docs)
            for name, gmap in systems.items():
                grp = Counter(gmap[d] for d in docs if d in gmap)
                cov = sum(grp.values()) / len(docs)
                if grp:
                    best, best_n = grp.most_common(1)[0]
                    size_best = sum(1 for v in gmap.values() if v == best)
                    entry["sistemas"][name] = {
                        "cobertura": round(cov, 3),
                        "mejor_recall": round(best_n / len(docs), 3),
                        "pureza": round(best_n / size_best, 3),
                        "fragmentos": sum(1 for _, n in grp.items()
                                          if n >= 0.10 * len(docs)),
                        "perdidos": len(docs) - sum(grp.values()),
                    }
        per_case.append(entry)
        if entry["documentado"] and not entry["flag_contaminado"] and entry["sistemas"]:
            confirm.append(entry)

    def avg(name, key):
        vals = [e["sistemas"][name][key] for e in confirm if name in e["sistemas"]]
        return round(sum(vals) / len(vals), 3) if vals else None

    summary = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "gold_seal": (OUT_DIR / "f4c_external_gold_SEAL.txt").read_text(encoding="utf-8").split()[0],
        "casos_gold": len(gold["casos"]),
        "documentados": sum(1 for e in per_case if e["documentado"]),
        "confirmatorios": len(confirm),
        "advertencia": "adjudicacion mecanica por titulo; INDH 2015 no cubre litio/H2 post-2015; no es verdad perfecta",
        "promedios_confirmatorios": {
            name: {k: avg(name, k) for k in
                   ("cobertura", "mejor_recall", "pureza", "fragmentos", "perdidos")}
            for name in systems
        },
        "per_case": per_case,
    }
    (OUT_DIR / "f4c_recovery_results.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({k: summary[k] for k in
                      ("casos_gold", "documentados", "confirmatorios")}, indent=1))
    print(json.dumps(summary["promedios_confirmatorios"], indent=1))


if __name__ == "__main__":
    main()
