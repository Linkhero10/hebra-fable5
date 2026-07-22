# F0 — Auditoria de cobertura de referentes para HEBRA (solo lectura).
# Entrada: corpus canonico 3.742. Salidas: outputs/f0_referent_coverage.json
# y outputs/f0_referent_coverage_report.md. Determinista, sin LLM, sin red.

import csv
import hashlib
import json
import unicodedata
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4].parent  # .../01_proyecto_universidad
CORPUS = ROOT / "01_bases_de_datos/03_refiltro_api_qwen_y_base_actual/06_base_actual_fusionada_3742_incluidas.csv"
OUT_DIR = Path(__file__).resolve().parents[1] / "outputs"

NULL_TOKENS = {
    "", "null", "none", "n/a", "na", "no", "no aplica", "no especificado",
    "no especificada", "desconocido", "desconocida", "sin informacion",
    "sin información", "no identificado", "no identificada", "-", "unknown",
}

# Actores genericos: cuentan como presencia pero se reportan aparte porque
# no anclan identidad por si solos (F1 decidira su tratamiento).
GENERIC_ACTOR_PREFIXES = (
    "comunidades", "comunidad local", "vecinos", "habitantes", "pobladores",
    "ciudadanos", "organizaciones", "agrupaciones", "trabajadores", "pescadores",
    "autoridades", "gobierno local", "empresas", "la comunidad", "residentes",
)


def norm(value: str) -> str:
    v = (value or "").strip()
    if v.lower() in NULL_TOKENS:
        return ""
    return v


def norm_key(value: str) -> str:
    # Clave de conteo: minusculas sin tildes, espacios colapsados.
    v = unicodedata.normalize("NFKD", norm(value).lower())
    v = "".join(c for c in v if not unicodedata.combining(c))
    return " ".join(v.split())


def is_generic_actor(key: str) -> bool:
    return any(key.startswith(p) for p in GENERIC_ACTOR_PREFIXES)


def parse_year(fecha_iso: str) -> str:
    v = norm(fecha_iso)
    if len(v) >= 4 and v[:4].isdigit():
        return v[:4]
    return ""


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    sha = hashlib.sha256(CORPUS.read_bytes()).hexdigest()

    rows = 0
    dates_ok = 0
    per_year = Counter()
    per_year_ref = Counter()
    cov = Counter()  # componentes presentes
    objeto_c, lugar_c, actor_c = Counter(), Counter(), Counter()
    generic_actor_docs = 0
    n_components_hist = Counter()
    worst = []  # docs sin ningun referente

    with open(CORPUS, encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            rows += 1
            year = parse_year(row.get("fecha_iso", ""))
            if year:
                dates_ok += 1
                per_year[year] += 1

            objeto = norm(row.get("llm_project_name", ""))
            lugar = (
                norm(row.get("llm_main_conflict_place_name", ""))
                or norm(row.get("geo_comuna", ""))
                or norm(row.get("geo_region", ""))
            )
            a1 = norm(row.get("llm_demandant_actor_name", ""))
            a2 = norm(row.get("llm_demanded_actor_name", ""))
            actors = [a for a in (a1, a2) if a]

            if objeto:
                cov["objeto"] += 1
                objeto_c[norm_key(objeto)] += 1
            if lugar:
                cov["territorio"] += 1
                lugar_c[norm_key(lugar)] += 1
            for a in actors:
                actor_c[norm_key(a)] += 1
            if actors:
                cov["actores"] += 1
            specific = [a for a in actors if not is_generic_actor(norm_key(a))]
            if actors and not specific:
                generic_actor_docs += 1

            n = sum(1 for x in (objeto, lugar, bool(actors)) if x)
            n_components_hist[n] += 1
            if n >= 1:
                cov["ge1"] += 1
                if year:
                    per_year_ref[year] += 1
            if n >= 2:
                cov["ge2"] += 1
            if n == 0:
                worst.append({
                    "id": row.get("id", ""),
                    "titulo": (row.get("titulo") or "")[:120],
                    "source_run": row.get("source_run", ""),
                    "conflict_type": norm(row.get("llm_conflict_type", "")),
                })

    def top(counter, k=20):
        return [{"key": key, "docs": n} for key, n in counter.most_common(k)]

    result = {
        "schema_version": 1,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "corpus": str(CORPUS.relative_to(ROOT)),
        "corpus_sha256": sha,
        "documents": rows,
        "valid_dates": dates_ok,
        "coverage": {
            "objeto_de_disputa": cov["objeto"],
            "territorio": cov["territorio"],
            "actores": cov["actores"],
            "docs_ge1_componente": cov["ge1"],
            "docs_ge2_componentes": cov["ge2"],
            "pct_ge1": round(100 * cov["ge1"] / rows, 2),
            "pct_ge2": round(100 * cov["ge2"] / rows, 2),
            "docs_solo_actores_genericos": generic_actor_docs,
        },
        "n_components_histogram": dict(sorted(n_components_hist.items())),
        "cardinality": {
            "objetos_unicos": len(objeto_c),
            "territorios_unicos": len(lugar_c),
            "actores_unicos": len(actor_c),
        },
        "top_objetos": top(objeto_c),
        "top_territorios": top(lugar_c),
        "top_actores": top(actor_c),
        "per_year": {
            y: {"docs": per_year[y], "docs_ge1_ref": per_year_ref[y]}
            for y in sorted(per_year)
        },
        "worst_cases_sin_referente": worst[:20],
        "worst_cases_total": len(worst),
        "gate_f0": {
            "threshold_pct_ge1": 70.0,
            "observed_pct_ge1": round(100 * cov["ge1"] / rows, 2),
            "pass": (100 * cov["ge1"] / rows) >= 70.0,
        },
    }

    (OUT_DIR / "f0_referent_coverage.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8"
    )

    g = result["gate_f0"]
    c = result["coverage"]
    lines = [
        "# F0 — Cobertura de referentes (HEBRA)",
        "",
        f"Generado: {result['generated_utc']}  ",
        f"Corpus: `{result['corpus']}`  ",
        f"SHA-256: `{sha[:16]}…`  ",
        f"Documentos: {rows}; fechas válidas: {dates_ok}",
        "",
        f"## Puerta F0: {'PASS' if g['pass'] else 'FAIL'}",
        "",
        f"- ≥1 componente de referente: {c['docs_ge1_componente']} docs"
        f" ({c['pct_ge1']} %) — umbral 70 %.",
        f"- ≥2 componentes (enlazables): {c['docs_ge2_componentes']} docs"
        f" ({c['pct_ge2']} %).",
        f"- Objeto de disputa: {c['objeto_de_disputa']}"
        f" ({round(100*c['objeto_de_disputa']/rows,1)} %);"
        f" territorio: {c['territorio']}"
        f" ({round(100*c['territorio']/rows,1)} %);"
        f" actores: {c['actores']}"
        f" ({round(100*c['actores']/rows,1)} %).",
        f"- Docs cuyo único actor es genérico: {c['docs_solo_actores_genericos']}.",
        f"- Únicos: {result['cardinality']['objetos_unicos']} objetos,"
        f" {result['cardinality']['territorios_unicos']} territorios,"
        f" {result['cardinality']['actores_unicos']} actores"
        " (antes de canonicalización F1).",
        "",
        "## Top 10 por componente",
        "",
    ]
    for name, data in (
        ("Objetos", result["top_objetos"]),
        ("Territorios", result["top_territorios"]),
        ("Actores", result["top_actores"]),
    ):
        lines.append(f"### {name}")
        lines += [f"- {e['key']} — {e['docs']}" for e in data[:10]]
        lines.append("")
    lines.append("## Cobertura por año (docs / con ≥1 referente)")
    lines.append("")
    for y, d in result["per_year"].items():
        lines.append(f"- {y}: {d['docs']} / {d['docs_ge1_ref']}")
    lines += [
        "",
        f"## Peores casos (sin referente): {result['worst_cases_total']} docs",
        "",
    ]
    for wc in result["worst_cases_sin_referente"]:
        lines.append(
            f"- id={wc['id']} [{wc['source_run']}] {wc['titulo']}"
            f" (tipo: {wc['conflict_type'] or 's/d'})"
        )
    (OUT_DIR / "f0_referent_coverage_report.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )
    print(json.dumps(g, indent=1))
    print("coverage:", json.dumps(c, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
