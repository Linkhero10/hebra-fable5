# F1.5 — Renormalizacion conservadora de referentes (HEBRA v2).
# Correccion del hallazgo del checkpoint F1.5-F2.5: la regla v1 "nombre (x)"
# fusionaba relaciones (afiliacion, propietario, tecnologia, cargo) como si
# fueran sinonimos (pc->persona, barrick->pascua lama, etc.).
#
# Reglas v2 (preinscritas):
#   R1/R2/R5 iguales a v1 (normalizacion, articulos, puntuacion).
#   R3v2 "nombre (acr)" se acepta como sigla SOLO si acr coincide con las
#        iniciales de las palabras de contenido del nombre, o con las
#        iniciales de todas las palabras. Sin coincidencia -> NO fusion:
#        el string completo "nombre (x)" se conserva como referente propio
#        y la no-fusion queda registrada para revision humana.
#   R4v2 sigla suelta -> canonico solo para siglas aceptadas por R3v2 y
#        con expansion unica en el corpus.
#   G1   el canonico no puede ser un termino generico/rol (stoplist).
# Ninguna fusion por frecuencia ni por distancia de edicion.
# Salidas nuevas (v1 se conserva como experimento historico):
#   outputs/f1v2_referents.csv, outputs/f1v2_alias_audit.json

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
STOPWORDS = {"de", "del", "la", "el", "los", "las", "y", "e", "en", "para", "por", "al", "a"}
GENERIC_CANONICALS = {
    "persona", "personas", "empresa", "empresas", "proyecto", "proyectos",
    "diputado", "diputada", "senador", "senadora", "alcalde", "alcaldesa",
    "ministro", "ministra", "gobierno", "comunidad", "organizacion", "acuerdo",
}
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


def initials_match(name: str, acr: str) -> bool:
    acr_letters = re.sub(r"[^a-z0-9]", "", acr)
    if len(acr_letters) < 2:
        return False
    words = name.split()
    content = [w for w in words if w not in STOPWORDS]
    for seq in (content, words):
        if seq and "".join(w[0] for w in seq) == acr_letters:
            return True
    return False


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    sha = hashlib.sha256(CORPUS.read_bytes()).hexdigest()

    raw_values = defaultdict(Counter)
    paren_forms = defaultdict(Counter)  # tipo -> full_key -> count
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
                    if PAREN_RE.match(v):
                        paren_forms[tipo][v] += 1

    # Adjudicar cada forma con parentesis: sigla valida vs relacion.
    accepted, rejected = [], []
    alias_map = defaultdict(dict)   # tipo -> alias -> canonical
    acr_owner = defaultdict(dict)   # tipo -> acr -> canonical (para R4v2)
    acr_conflict = defaultdict(set)
    for tipo, forms in paren_forms.items():
        for full, cnt in sorted(forms.items()):
            m = PAREN_RE.match(full)
            name = base_key(m.group("name"))
            acr = m.group("acr").replace(".", "").strip()
            if name in GENERIC_CANONICALS:
                rejected.append({"tipo": tipo, "form": full, "reason": "G1-canonico-generico",
                                 "docs": cnt})
                continue
            if initials_match(name, acr):
                alias_map[tipo][full] = name
                accepted.append({"tipo": tipo, "form": full, "canonical": name,
                                 "acr": acr, "rule": "R3v2-iniciales", "docs": cnt})
                if acr in acr_owner[tipo] and acr_owner[tipo][acr] != name:
                    acr_conflict[tipo].add(acr)
                else:
                    acr_owner[tipo][acr] = name
            else:
                rejected.append({"tipo": tipo, "form": full,
                                 "reason": "R3v2-parentesis-relacional-se-conserva-distinto",
                                 "docs": cnt})
    # R4v2: sigla suelta -> canonico si unica y aceptada.
    for tipo, owners in acr_owner.items():
        for acr, canonical in owners.items():
            if acr in acr_conflict[tipo]:
                rejected.append({"tipo": tipo, "form": acr, "reason": "R4v2-sigla-ambigua"})
                continue
            if acr in raw_values[tipo] and acr != canonical:
                alias_map[tipo][acr] = canonical
                accepted.append({"tipo": tipo, "form": acr, "canonical": canonical,
                                 "rule": "R4v2-sigla-suelta",
                                 "docs": raw_values[tipo][acr]})

    def canon(tipo: str, key: str) -> str:
        return alias_map[tipo].get(key, key) if key else ""

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

    with open(OUT_DIR / "f1v2_referents.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["doc_id", "fecha_iso", "tipo", "referente", "raw"])
        w.writeheader()
        w.writerows(out_rows)

    audit = {
        "schema_version": 1,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "corpus_sha256": sha,
        "documents": len(docs),
        "referent_rows": len(out_rows),
        "cardinality_after": {t: len(c) for t, c in canon_counts.items()},
        "paren_forms_total": sum(len(f) for f in paren_forms.values()),
        "merges_accepted": len(accepted),
        "merges_rejected_kept_distinct": len(rejected),
        "accepted": accepted,
        "rejected": rejected,
        "note": (
            "Las formas rechazadas no se colapsan al nombre: se conservan como "
            "referentes distintos y quedan disponibles para revision humana. "
            "v1 (f1_referents.csv) se conserva como experimento historico."
        ),
    }
    (OUT_DIR / "f1v2_alias_audit.json").write_text(
        json.dumps(audit, ensure_ascii=False, indent=1), encoding="utf-8"
    )
    print(json.dumps({k: audit[k] for k in (
        "documents", "referent_rows", "cardinality_after", "paren_forms_total",
        "merges_accepted", "merges_rejected_kept_distinct")}, indent=1))
    print("aceptadas (muestra):", json.dumps(accepted[:8], ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
