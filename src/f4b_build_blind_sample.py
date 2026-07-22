# F4-B — Muestra ciega sellada para evaluacion independiente de identidad.
# Estratos (preinscritos):
#   P50  50 aristas positivas por quintil de w (10 c/u)
#   L30  30 enlaces largos aceptados (dias>365)
#   U30  30 aristas aceptadas cercanas al umbral (w in [0.45,0.47))
#   R30  30 candidatos rechazados cercanos al umbral (dt<=365, w in [0.40,0.45))
#   HN50 50 negativos dificiles: comparten territorio o actor con w<0.40 (25)
#        o alta similitud semantica sin referente compartido (25, dt<=365)
#   FN30 30 falsos negativos candidatos: pares adjudicados al mismo caso del
#        gold externo sellado, sin arista y en hilos distintos
#   ISO20 20 documentos aislados (sin hilo >=3)
# La hoja oculta: sistema, puntajes, umbrales y condicion. Muestra titulo,
# snippet y fechas. La clave estrato->item queda en archivo separado.
# Todo se sella con SHA-256 antes de cualquier revision.

import csv
import hashlib
import json
import math
import random
import re
import unicodedata
from bisect import bisect_left, bisect_right
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[4].parent
CORPUS = ROOT / "01_bases_de_datos/03_refiltro_api_qwen_y_base_actual/06_base_actual_fusionada_3742_incluidas.csv"
EMB = ROOT / "04_embeddings/01_embeddings_canonicos/active_corpus_embeddings_3742.npz"
OUT_DIR = Path(__file__).resolve().parents[1] / "outputs"
EDGES = OUT_DIR / "f2b_idf_v2_L2_edges.csv"
THREADS = OUT_DIR / "f2b_idf_v2_L2_threads.csv"
REFS = OUT_DIR / "f1v2_referents.csv"
GOLD = OUT_DIR / "f4c_external_gold_SEALED.json"

SEED = 20260750
W_REF = {"objeto": 0.5, "territorio": 0.3, "actor": 0.2}
ALPHA, BETA = 0.7, 0.3
MAX_DF = 400


def deacc(s):
    s = unicodedata.normalize("NFKD", s.lower())
    return "".join(c for c in s if not unicodedata.combining(c))


def main() -> None:
    rng = random.Random(SEED)
    ids, meta = [], {}
    with open(CORPUS, encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            ids.append(row["id"])
            meta[row["id"]] = {
                "fecha": (row.get("fecha_iso") or "")[:10],
                "titulo": (row.get("titulo") or "")[:160],
                "snippet": (row.get("snippet") or "")[:260],
            }
    row_of = {d: k for k, d in enumerate(ids)}
    emb = np.load(EMB)["arr_0"].astype(np.float32)
    emb /= np.linalg.norm(emb, axis=1, keepdims=True)

    refs = defaultdict(lambda: defaultdict(set))
    with open(REFS, encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            refs[row["doc_id"]][row["tipo"]].add(row["referente"])

    inv = defaultdict(list)
    for d, by_t in refs.items():
        for t, rs in by_t.items():
            for r in rs:
                inv[(t, r)].append(d)
    n_dated = sum(1 for d in ids if meta[d]["fecha"])
    idf_ref = math.log(n_dated / 5)
    IDF = {k: min(1.0, math.log(n_dated / len(v)) / idf_ref) for k, v in inv.items()}

    day = {}
    for d in ids:
        f_ = meta[d]["fecha"]
        if f_:
            y, m, dd_ = map(int, f_.split("-"))
            from datetime import date
            day[d] = date(y, m, dd_).toordinal()

    def s_ref_pair(a, b):
        s = 0.0
        for t, wt in W_REF.items():
            inter = refs[a][t] & refs[b][t]
            if inter:
                s += wt * min(1.0, sum(IDF.get((t, r), 0) for r in inter))
        return s

    with open(EDGES, encoding="utf-8", newline="") as f:
        edges = list(csv.DictReader(f))
    edge_set = {frozenset((e["doc_i"], e["doc_j"])) for e in edges}

    doc2t = {}
    with open(THREADS, encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            doc2t[row["doc_id"]] = row["thread_id"]

    items = []

    def add(strato, a, b=None, extra=None):
        items.append({"strato": strato, "a": a, "b": b, "extra": extra or {}})

    # P50: quintiles de w
    ws = sorted(float(e["w"]) for e in edges)
    qs = [ws[int(len(ws) * k / 5)] for k in range(1, 5)]
    by_q = defaultdict(list)
    for e in edges:
        w = float(e["w"])
        qi = sum(w >= q for q in qs)
        by_q[qi].append(e)
    for qi in range(5):
        for e in rng.sample(by_q[qi], 10):
            add("P50", e["doc_i"], e["doc_j"], {"w": e["w"], "quintil": qi})

    # L30
    longs = [e for e in edges if int(e["dias"]) > 365]
    for e in rng.sample(longs, 30):
        add("L30", e["doc_i"], e["doc_j"], {"w": e["w"], "dias": e["dias"]})

    # U30
    near = [e for e in edges if 0.45 <= float(e["w"]) < 0.47]
    for e in rng.sample(near, min(30, len(near))):
        add("U30", e["doc_i"], e["doc_j"], {"w": e["w"]})

    # R30 y HN50-A: recomputo de candidatos por referente compartido
    r30, hnA = [], []
    seen = set()
    keys = list(inv.items())
    rng.shuffle(keys)
    for (t, r), ds in keys:
        if len(ds) > MAX_DF or len(ds) < 2:
            continue
        ds2 = [d for d in ds if d in day]
        rng.shuffle(ds2)
        for i in range(min(len(ds2), 8)):
            for j in range(i + 1, min(len(ds2), 8)):
                a, b = ds2[i], ds2[j]
                fs = frozenset((a, b))
                if fs in seen or fs in edge_set:
                    continue
                dt = abs(day[a] - day[b])
                if dt == 0 or dt > 365:
                    continue
                seen.add(fs)
                sr = s_ref_pair(a, b)
                if sr <= 0:
                    continue
                se = float(emb[row_of[a]] @ emb[row_of[b]])
                w = ALPHA * sr + BETA * se
                if 0.40 <= w < 0.45 and len(r30) < 200:
                    r30.append((a, b, w))
                elif w < 0.40 and t in ("territorio", "actor") and len(hnA) < 400:
                    hnA.append((a, b, w))
        if len(r30) >= 200 and len(hnA) >= 400:
            break
    for a, b, w in rng.sample(r30, min(30, len(r30))):
        add("R30", a, b, {"w": round(w, 3)})
    for a, b, w in rng.sample(hnA, min(25, len(hnA))):
        add("HN50", a, b, {"w": round(w, 3), "tipo": "referente_compartido_bajo_w"})

    # HN50-B: alta similitud semantica sin referente compartido
    hnB = []
    dated_ids = [d for d in ids if d in day]
    tries = 0
    while len(hnB) < 25 and tries < 300000:
        tries += 1
        a, b = rng.sample(dated_ids, 2)
        if abs(day[a] - day[b]) > 365:
            continue
        if s_ref_pair(a, b) > 0:
            continue
        se = float(emb[row_of[a]] @ emb[row_of[b]])
        if se >= 0.80:
            fs = frozenset((a, b))
            if fs not in seen:
                seen.add(fs)
                hnB.append((a, b, se))
    for a, b, se in hnB:
        add("HN50", a, b, {"s_emb": round(se, 3), "tipo": "alta_semantica_sin_referente"})

    # FN30: mismo caso gold, sin arista, hilos distintos (adjudicacion por tokens)
    gold = json.loads(GOLD.read_text(encoding="utf-8"))
    fn = []
    for c in gold["casos"]:
        if c.get("flag_contaminado_desarrollo"):
            continue
        toks = [w for w in re.findall(r"[a-zñ]{5,}", deacc(
            c["titulo_aprox"] + " " + c["localizacion"]))
            if w not in ("region", "provincia", "comuna", "chile", "nacional",
                         "parque", "reserva", "central", "proyecto", "minera")]
        if not toks:
            continue
        matched = [d for d in dated_ids if any(
            tk in deacc(meta[d]["titulo"]) for tk in toks[:6])]
        if len(matched) < 2 or len(matched) > 200:
            continue
        rng.shuffle(matched)
        for a, b in [(matched[i], matched[i + 1]) for i in range(0, len(matched) - 1, 2)][:2]:
            fs = frozenset((a, b))
            if fs in edge_set or doc2t.get(a) == doc2t.get(b) and doc2t.get(a):
                continue
            fn.append((a, b, c["case_idx"]))
    for a, b, ci in rng.sample(fn, min(30, len(fn))):
        add("FN30", a, b, {"gold_case_idx": ci})

    # ISO20: documentos sin hilo
    iso = [d for d in dated_ids if d not in doc2t]
    for d in rng.sample(iso, 20):
        add("ISO20", d)

    # Hoja ciega: barajar, ocultar estrato
    rng.shuffle(items)
    sheet_items, key = [], {}
    for k, it in enumerate(items):
        iid = f"X{k:03d}"
        key[iid] = {"strato": it["strato"], **it["extra"],
                    "a": it["a"], "b": it["b"]}
        entry = {"item_id": iid,
                 "doc_a": {**meta[it["a"]], "id": it["a"]}}
        if it["b"]:
            entry["doc_b"] = {**meta[it["b"]], "id": it["b"]}
            entry["pregunta"] = "mismo_proceso | relacionado | no_relacionado"
        else:
            entry["pregunta"] = "aislado_correcto | pertenece_a_un_proceso | indeterminado"
        entry["veredicto"] = ""
        sheet_items.append(entry)

    sheet = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "seed": SEED,
        "instrucciones": (
            "Revision ciega: no se revela sistema, puntajes, umbrales ni si el par "
            "fue aceptado o rechazado. Juzgar con titulo+snippet; si no basta, "
            "marcar indeterminado y anotar. Capa humana independiente; cualquier "
            "revision IA es piloto separado."),
        "n_items": len(sheet_items),
        "items": sheet_items,
    }
    payload = json.dumps(sheet, ensure_ascii=False, indent=1)
    (OUT_DIR / "f4b_blind_sheet_SEALED.json").write_text(payload, encoding="utf-8")
    (OUT_DIR / "f4b_blind_key_DO_NOT_OPEN.json").write_text(
        json.dumps(key, ensure_ascii=False, indent=1), encoding="utf-8")
    sha = hashlib.sha256(payload.encode()).hexdigest()
    (OUT_DIR / "f4b_blind_sheet_SEAL.txt").write_text(
        f"{sha}  f4b_blind_sheet_SEALED.json\nsellado_utc: "
        f"{datetime.now(timezone.utc).isoformat()}\n", encoding="utf-8")
    from collections import Counter
    print("items:", len(sheet_items), "| por estrato:",
          dict(Counter(v["strato"] for v in key.values())))
    print("SEAL", sha[:16])


if __name__ == "__main__":
    main()
