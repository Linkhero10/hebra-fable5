# F4-C — Gold externo sellado desde INDH 2015 (HEBRA).
# Fuente: "Mapa de Conflictos Socioambientales en Chile", INDH, version 2015
# (118 casos), PDF publico (copia CSIRO). Extraccion MECANICA por bloques:
# ningun caso se agrega ni descarta a mano; el filtro es "SECTOR PRODUCTIVO
# contiene Energia o Mineria". Los cinco casos de desarrollo contaminados se
# marcan (flag) pero NO se excluyen del archivo: se excluyen del conjunto
# confirmatorio en el analisis.
# La lista se SELLA (SHA-256) antes de cualquier interseccion con hilos HEBRA.
# Limitaciones registradas: corte temporal 2015 (el corpus llega a 2026);
# definicion INDH de conflicto != definicion HEBRA de proceso; titulos
# aproximados por heuristica de extraccion PDF.

import hashlib
import json
import re
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

OUT_DIR = Path(__file__).resolve().parents[1] / "outputs"
FULLTEXT = OUT_DIR / "_indh2015_fulltext.txt"
PDF = Path(r"C:\Users\felip\.claude\projects\D--\72b93b75-e0e0-4d44-9eb3-9531e5d2d842\tool-results\webfetch-1784731495896-u2nkbz.pdf")

TITLE_RE = re.compile(
    r"(?:Central(?:es)?|Proyecto|Planta|Minera|Miner[ií]a|Parque|"
    r"Termoel[eé]ctrica|Hidroel[eé]ctrica|Embalse|Fundici[oó]n|"
    r"Explotaci[oó]n|Extracci[oó]n|Contaminaci[oó]n|Relaves?|Ampliaci[oó]n|"
    r"Instalaci[oó]n|Vertedero|Ducto|L[ií]nea|Puerto|Complejo|Bater[ií]a)"
    r"[^\n]{3,80}")
CONTAMINATED_TOKENS = [
    "quintero", "puchuncavi", "ventanas", "hidroaysen", "bocamina", "coronel",
    "salar de atacama", "litio", "magallanes",
]


def deacc(s):
    s = unicodedata.normalize("NFKD", s)
    return "".join(c for c in s if not unicodedata.combining(c))


def field(block, label, stop_labels):
    m = re.search(re.escape(label) + r"(.{0,300})", block, re.S)
    if not m:
        return ""
    seg = m.group(1)
    for sl in stop_labels:
        k = seg.find(sl)
        if k >= 0:
            seg = seg[:k]
    return " ".join(seg.split()).strip(" :")


def main() -> None:
    txt = FULLTEXT.read_text(encoding="utf-8")
    txt = re.sub(r"=== PAGE \d+ ===", "\n", txt)
    # bloques por ANO DE INICIO (ancla presente en cada caso)
    anchors = [m.start() for m in re.finditer(r"A.O DE INICIO", txt)]
    stops = ["LOCALIZACI", "ESTADO DEL", "SECTOR PRODUCTIVO", "NIVEL DE",
             "INVOLUCRA", "ACTORES", "DERECHOS", "CAUSA DEL", "PERFIL",
             "TIPO DE", "RESULTADO", "Mapa de conflictos"]
    cases = []
    for k, a in enumerate(anchors):
        b_end = anchors[k + 1] if k + 1 < len(anchors) else len(txt)
        blk = txt[max(0, a - 2500):b_end]
        core = txt[a:min(a + 1200, b_end)]
        anio = (re.search(r"A.O DE INICIO\s*([0-9]{4})", core) or [None, ""])[1]
        loc = field(core, "LOCALIZACI", stops[1:])
        estado = field(core, "ESTADO DEL CONFLICTO", [s for s in stops if not s.startswith("ESTADO")])
        sector = field(core, "SECTOR PRODUCTIVO", [s for s in stops if not s.startswith("SECTOR")])
        region_m = re.search(r"Regi[oó]n (?:de |del |Metropolitana)?[A-Za-zÁ-úñÑ ]{0,40}", loc)
        region = region_m.group(0).strip() if region_m else ""
        # titulo aproximado: ultima linea tipo-titulo del contexto previo
        prev = blk[: blk.find("A") if False else 2500]
        titles = TITLE_RE.findall(deacc(prev))
        titulo = titles[-1].strip() if titles else ""
        cases.append({
            "case_idx": k, "titulo_aprox": titulo[:90], "anio_inicio": anio,
            "localizacion": loc[:120], "region": region[:60],
            "estado_2015": estado[:40], "sector": sector[:120],
        })

    energia_mineria = [
        c for c in cases
        if re.search(r"Energ|Miner", c["sector"], re.I)
    ]
    for c in energia_mineria:
        blob = deacc((c["titulo_aprox"] + " " + c["localizacion"]).lower())
        c["flag_contaminado_desarrollo"] = any(t in blob for t in CONTAMINATED_TOKENS)

    gold = {
        "schema_version": 1,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "fuente": {
            "nombre": "INDH Mapa de Conflictos Socioambientales en Chile 2015",
            "url": "https://research.csiro.au/gestionrapel/wp-content/uploads/sites/79/2016/11/Mapa-de-conflictos-socioambientales-en-Chile-INDH-2015.pdf",
            "pdf_sha256": hashlib.sha256(PDF.read_bytes()).hexdigest(),
            "casos_declarados": 118,
        },
        "metodo": "extraccion mecanica por bloques 'ANO DE INICIO'; filtro sector Energia|Mineria; sin seleccion manual",
        "limitaciones": [
            "corte temporal 2015; el corpus llega a 2026 (litio/H2 verde post-2015 subrepresentados)",
            "definicion INDH de conflicto != definicion HEBRA de proceso",
            "titulos aproximados por heuristica de extraccion PDF; adjudicar contra corpus antes de medir recuperacion",
            "INDH no es verdad perfecta: cobertura y criterios propios",
        ],
        "bloques_detectados": len(cases),
        "casos_energia_mineria": len(energia_mineria),
        "flag_contaminado_desarrollo_n": sum(1 for c in energia_mineria if c["flag_contaminado_desarrollo"]),
        "casos": energia_mineria,
    }
    payload = json.dumps(gold, ensure_ascii=False, indent=1)
    out = OUT_DIR / "f4c_external_gold_SEALED.json"
    out.write_text(payload, encoding="utf-8")
    sha = hashlib.sha256(payload.encode()).hexdigest()
    (OUT_DIR / "f4c_external_gold_SEAL.txt").write_text(
        f"{sha}  f4c_external_gold_SEALED.json\nsellado_utc: "
        f"{datetime.now(timezone.utc).isoformat()}\n"
        "regla: este archivo se sello ANTES de cualquier interseccion con hilos HEBRA;\n"
        "los casos flag_contaminado_desarrollo=true se excluyen del conjunto confirmatorio.\n",
        encoding="utf-8")
    print(json.dumps({k: gold[k] for k in (
        "bloques_detectados", "casos_energia_mineria",
        "flag_contaminado_desarrollo_n")}, indent=1))
    print("SEAL", sha[:16])
    print("muestra:", json.dumps(gold["casos"][:6], ensure_ascii=False, indent=1)[:900])


if __name__ == "__main__":
    main()
