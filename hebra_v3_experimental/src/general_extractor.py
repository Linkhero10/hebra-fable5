# -*- coding: utf-8 -*-
"""
Extractor GENERAL de objetos procesuales (HEBRA v3 EXPERIMENTAL).

No contiene vocabulario de ningun macrohilo especifico. Mapea columnas
`llm_*` / `geo_*` ya extraidas (una sola vez, por un proceso de anotacion
LLM previo sobre TODO el corpus de 3.742 documentos, antes de que
existieran H0000 o cualquier hilo) a 5 categorias generales:

  1. proyecto_instalacion
  2. territorio (+ territorio_tipo)
  3. organizacion (+ tipos)
  4. procedimiento (+ familia generica)
  5. evento_fase (compuesto familia+fecha, ver limitaciones en el diseno)

Reutiliza `base_key()` de fable5/src/f1_5_normalize_referents_v2.py por
importacion directa (no se reimplementa ni se modifica esa funcion).

Ver ../GENERAL_EXTRACTOR_DESIGN_2026_07_23.md para la justificacion
completa de por que esto no son "reglas manuales por macrohilo".
"""
from __future__ import annotations

import csv
import importlib.util
import sys
from pathlib import Path

BASE = Path(r"D:\Analisis conflictos\01_proyecto_universidad\09_metodologia\faro_model_research\competition")
F1_5_MODULE_PATH = BASE / "fable5" / "src" / "f1_5_normalize_referents_v2.py"
CORPUS = Path(r"D:\Analisis conflictos\01_proyecto_universidad\01_bases_de_datos"
              r"\03_refiltro_api_qwen_y_base_actual\06_base_actual_fusionada_3742_incluidas.csv")


def _import_base_key():
    """Importa base_key() del modulo f1v2 SIN copiar su codigo ni ejecutar
    su main(). Es la unica funcion que se reutiliza de ese archivo."""
    spec = importlib.util.spec_from_file_location("f1_5_normalize_referents_v2", F1_5_MODULE_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # define funciones/constantes de modulo; no llama a main()
    return mod.base_key


base_key = _import_base_key()

# Tipos de lugar que indican que el LUGAR ES la instalacion (no solo su
# entorno geografico). Genericos: cualquier corpus de conflictos
# socioambientales chilenos usa esta misma tipologia de lugar, ya provista
# por la extraccion LLM upstream (llm_main_conflict_place_type), no algo
# que hayamos inventado mirando un macrohilo en particular.
FACILITY_PLACE_TYPES = {"mine", "thermoelectric", "industrial_facility", "company_facility"}

# Familias GENERICAS de procedimiento. Ninguna palabra clave es un nombre
# propio de proyecto/empresa/salar: son sustantivos comunes del espanol
# administrativo-judicial chileno, iguales para cualquier hilo.
PROCEDURE_FAMILIES: dict[str, list[str]] = {
    "judicial": ["recurso judicial", "recurso de proteccion", "demanda", "reclamacion judicial",
                 "apelacion", "casacion", "tribunal ambiental", "corte suprema", "corte de apelaciones"],
    "administrativo_autorizatorio": ["aprobacion ambiental", "permiso", "resolucion de calificacion",
                                      "calificacion ambiental", "autorizacion", "concesion"],
    "administrativo_sancionatorio": ["sancion", "multa", "procedimiento sancionatorio", "infraccion",
                                      "incumplimiento"],
    "participativo": ["consulta indigena", "consulta ciudadana", "participacion ciudadana",
                       "consulta previa", "dialogo"],
    "manifestacion_publica": ["protesta", "declaracion publica", "rechazo formal", "denuncia publica",
                               "manifestacion", "toma", "bloqueo", "paro"],
    "acuerdo_contractual": ["acuerdo", "contrato", "memorando", "convenio", "alianza", "asociacion"],
    "administrativo_general": ["denuncia", "reclamacion", "reclamacion formal", "fiscalizacion"],
}
FAMILY_ORDER = list(PROCEDURE_FAMILIES.keys()) + ["otro"]


def classify_procedure_family(action_type_raw: str) -> str:
    """Clasifica un `llm_contentious_action_type` normalizado en una de las
    familias genericas de PROCEDURE_FAMILIES. Primera coincidencia por
    orden de especificidad (judicial/sancionatorio antes que generico)."""
    key = base_key(action_type_raw)
    if not key:
        return "otro"
    for family in FAMILY_ORDER[:-1]:
        for kw in PROCEDURE_FAMILIES[family]:
            if kw in key:
                return family
    return "otro"


def extract_document_fields(row: dict) -> dict:
    """Mapea una fila del corpus base (dict de columnas del CSV) a las 5
    categorias generales. No lee nada especifico de un macrohilo: solo usa
    los nombres de columna del esquema del corpus."""
    doc_id = row.get("id", "")
    fecha = (row.get("fecha_iso") or "")[:10]

    proyecto = base_key(row.get("llm_project_name", ""))
    lugar_tipo = (row.get("llm_main_conflict_place_type") or "").strip()
    if not proyecto and lugar_tipo in FACILITY_PLACE_TYPES:
        proyecto = base_key(row.get("llm_main_conflict_place_name", ""))

    territorio = (
        base_key(row.get("llm_main_conflict_place_name", ""))
        or base_key(row.get("geo_comuna", ""))
        or base_key(row.get("geo_provincia", ""))
        or base_key(row.get("geo_region", ""))
    )

    org_demandante = base_key(row.get("llm_demandant_actor_name", ""))
    org_demandada = base_key(row.get("llm_demanded_actor_name", ""))
    organizaciones = sorted({o for o in (org_demandante, org_demandada) if o})

    accion_raw = row.get("llm_contentious_action_type", "")
    procedimiento = base_key(accion_raw)
    familia = classify_procedure_family(accion_raw)

    evento_fase = f"{familia}::{fecha[:7]}" if fecha else f"{familia}::sin_fecha"

    return {
        "doc_id": doc_id,
        "fecha_iso": fecha,
        "proyecto_instalacion": proyecto,
        "territorio": territorio,
        "territorio_tipo": lugar_tipo,
        "organizacion": ";".join(organizaciones),
        "organizacion_demandante_tipo": (row.get("llm_demandant_actor_type") or "").strip(),
        "organizacion_demandada_tipo": (row.get("llm_demanded_actor_type") or "").strip(),
        "procedimiento": procedimiento,
        "procedimiento_familia": familia,
        "evento_fase": evento_fase,
    }


def extract_corpus(corpus_path: Path = CORPUS) -> list[dict]:
    rows = []
    with open(corpus_path, encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            rows.append(extract_document_fields(row))
    return rows


if __name__ == "__main__":
    out = extract_corpus()
    print(f"[OK] {len(out)} documentos procesados desde el corpus base.")
    n_con_proyecto = sum(1 for r in out if r["proyecto_instalacion"])
    print(f"proyecto_instalacion no vacio: {n_con_proyecto}/{len(out)} "
          f"({n_con_proyecto/len(out):.1%})")
