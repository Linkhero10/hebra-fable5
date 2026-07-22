# F1 — Normalizacion de referentes y diccionario de alias (HEBRA).
# Determinista, sin LLM. Solo lectura del corpus; escribe en outputs/.
# Reglas de fusion (preinscritas):
#   R1 norm_key: minusculas, sin tildes, espacios colapsados.
#   R2 articulo inicial removido (el/la/los/las) si quedan >=2 palabras.
#   R3 "nombre (sigla)" -> canonico "nombre"; la sigla se registra como alias
#      solo si es no ambigua (una unica expansion observada).
#   R4 sigla suelta ya observada en R3 -> canonico correspondiente.
#   R5 comillas y puntuacion marginal removidas.
# Ninguna fusion por distancia de edicion: riesgo de sobre-fusion no auditable.

import csv
import hashlib
import json
import re
import unicodedata
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4].parent
CORPUS = ROOT / "01_bases_de_datos/03_refiltro_api_qwen_y_base_actual/06_base_actual_fusionada_3742_incluidas.csv"
OUT_DIR = Path(__file__).resolve().parents[1] / "outputs"

NULL_TOKENS = {
    "", "null", "none", "n/a", "na", "no", "no aplica", "no especificado",
    "no especificada", "desconocido", "desconocida", "sin informacion",
    "sin información", "no identificado", "no identificada", "-", "unknown",
}
ARTICLES = ("el ", "la ", "los ", "las ")
PAREN_RE = re.compile(r"^(?P<name>.+?)\s*\((?P<acr>[a-z0-9\-\. ]{2,15})\)\s*$")


def base_key(value: str) -> str:
    v = (value or "").strip()
    if v.lower() in NULL_TOKENS:
        return ""
    v = unicodedata.normalize("NFKD", v.lower())
    v = "".join(c for c in v if not unicodedata.combining(c))
    v = v.replace('"', " ").replace("'", " ").replace("“", " ").replace("”", " ")
    v = re.sub(r"[;|]+", " ", v)
    v = " ".join(v.split())
    v = v.rstrip(" .,")
    for art in ARTICLES:
        if v.startswith(art) and len(v.split()) >= 3:
            v = v[len(art):]
            break
    return v


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    sha = hashlib.sha256(CORPUS.read_bytes()).hexdigest()

    # Pasada 1: recolectar claves y expansiones de siglas por tipo.
    raw_values = defaultdict(Counter)  # tipo -> key -> count
    acr_expansions = defaultdict(lambda: defaultdict(Counter))  # tipo -> sigla -> nombre -> count
    docs = []

    with open(CORPUS, encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            rec = {"doc_id": row.get("id", ""), "fecha_iso": (row.get("fecha_iso") or "")[:10]}
            objeto = base_key(row.get("llm_project_name", ""))
            lugar = (
                base_key(row.get("llm_main_conflict_place_name", ""))
                or base_key(row.get("geo_comuna", ""))
                or base_key(row.get("geo_region", ""))
            )
            actores = [
                base_key(row.get("llm_demandant_actor_name", "")),
                base_key(row.get("llm_demanded_actor_name", "")),
            ]
            rec["objeto"], rec["territorio"] = objeto, lugar
            rec["actores"] = [a for a in actores if a]
            docs.append(rec)
            for tipo, vals in (
                ("objeto", [objeto] if objeto else []),
                ("territorio", [lugar] if lugar else []),
                ("actor", rec["actores"]),
            ):
                for v in vals:
                    raw_values[tipo][v] += 1
                    m = PAREN_RE.match(v)
                    if m:
                        acr = m.group("acr").replace(".", "").strip()
                        acr_expansions[tipo][acr][base_key(m.group("name"))] += 1

    # Construir mapa de alias por tipo (R3/R4, solo siglas no ambiguas).
    alias_map = defaultdict(dict)  # tipo -> alias_key -> canonical
    merge_log = []
    for tipo, accs in acr_expansions.items():
        for acr, names in accs.items():
            if len(names) == 1:
                canonical = next(iter(names))
                full_form = f"{canonical} ({acr})"
                for alias in (full_form, acr):
                    if alias != canonical:
                        alias_map[tipo][alias] = canonical
                merge_log.append({
                    "tipo": tipo, "canonical": canonical,
                    "aliases": [full_form, acr],
                    "rule": "R3/R4", "evidence_docs": sum(names.values()),
                })
            else:
                merge_log.append({
                    "tipo": tipo, "acronym": acr,
                    "expansions": dict(names),
                    "rule": "R3-ambiguous-no-merge",
                })

    def canon(tipo: str, key: str) -> str:
        # Aplica alias; ademas colapsa "nombre (sigla)" no registrado a "nombre".
        if not key:
            return ""
        if key in alias_map[tipo]:
            return alias_map[tipo][key]
        m = PAREN_RE.match(key)
        if m:
            return base_key(m.group("name"))
        return key

    # Pasada 2: tabla normalizada documento x referente.
    canon_counts = defaultdict(Counter)
    out_rows = []
    for rec in docs:
        for tipo, vals in (
            ("objeto", [rec["objeto"]] if rec["objeto"] else []),
            ("territorio", [rec["territorio"]] if rec["territorio"] else []),
            ("actor", rec["actores"]),
        ):
            for raw in vals:
                c = canon(tipo, raw)
                if not c:
                    continue
                canon_counts[tipo][c] += 1
                out_rows.append({
                    "doc_id": rec["doc_id"], "fecha_iso": rec["fecha_iso"],
                    "tipo": tipo, "referente": c, "raw": raw,
                })

    with open(OUT_DIR / "f1_referents.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["doc_id", "fecha_iso", "tipo", "referente", "raw"])
        w.writeheader()
        w.writerows(out_rows)

    summary = {
        "schema_version": 1,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "corpus_sha256": sha,
        "rules": ["R1 norm", "R2 articles", "R3 name(acr)", "R4 bare-acr", "R5 punct"],
        "documents": len(docs),
        "referent_rows": len(out_rows),
        "cardinality_before": {t: len(c) for t, c in raw_values.items()},
        "cardinality_after": {t: len(c) for t, c in canon_counts.items()},
        "unambiguous_acronym_merges": sum(1 for e in merge_log if e["rule"] == "R3/R4"),
        "ambiguous_acronyms_kept_separate": sum(
            1 for e in merge_log if e["rule"] == "R3-ambiguous-no-merge"
        ),
        "top_after": {
            t: [{"key": k, "docs": n} for k, n in c.most_common(15)]
            for t, c in canon_counts.items()
        },
    }
    (OUT_DIR / "f1_alias_dictionary.json").write_text(
        json.dumps({"summary": summary, "alias_map": {t: dict(m) for t, m in alias_map.items()},
                    "merge_log": merge_log}, ensure_ascii=False, indent=1),
        encoding="utf-8",
    )
    print(json.dumps({k: summary[k] for k in (
        "documents", "referent_rows", "cardinality_before", "cardinality_after",
        "unambiguous_acronym_merges", "ambiguous_acronyms_kept_separate")}, indent=1))


if __name__ == "__main__":
    main()
