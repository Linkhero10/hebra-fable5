# -*- coding: utf-8 -*-
"""
Diccionario corto y auditable de normalizacion objeto -> subhilo canonico.

Deliberadamente NO es un modelo entrenado ni un clasificador de texto libre:
son reglas de coincidencia de subcadenas sobre el campo `objeto` que el
pipeline v1 YA calculo por documento (H0000_02_NODE_METRICS.csv). Se aplican
en orden de prioridad (la primera regla que matchea gana). Cualquier persona
puede leer esta lista y saber exactamente por que un documento cayo en un
subhilo u otro (trazabilidad, ver HEBRA_HIERARCHICAL_DESIGN_2026_07_22.md
seccion 2.7).

Si ninguna regla especifica matchea, el documento queda en abstencion de
nivel 2 (SIN_SUBHILO_ESPECIFICO) y solo pertenece al macrohilo.
"""
from __future__ import annotations

import re
import unicodedata


def _strip_accents(s: str) -> str:
    nfkd = unicodedata.normalize("NFKD", s)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def normalize_text(s: str) -> str:
    if s is None:
        return ""
    s = _strip_accents(str(s)).lower().strip()
    s = re.sub(r"\s+", " ", s)
    return s


SIN_SUBHILO = "SIN_SUBHILO_ESPECIFICO"

# (patron_regex, clave_canonica). Orden = prioridad (primer match gana).
# Los patrones estan escritos contra texto YA normalizado (normalize_text).
RULES: list[tuple[str, str]] = [
    # Proyecto Salar Blanco / Maricunga (adquisicion de Codelco a LPI, CEOL Maricunga, Rio Tinto)
    (r"proyecto blanco|salar blanco|maricunga", "proyecto_maricunga_salar_blanco"),

    # Salar Futuro: subproyecto tecnologico especifico de SQM, nombrado explicitamente
    # como componente propio en varias comunidades detectadas (ver H0000_05_PARTITION_COMPARISON).
    (r"salar futuro", "salar_futuro"),

    # Consultas indigenas CEOL por salar especifico (cada una es un procedimiento
    # administrativo propio, con comunidades y plazos distintos)
    (r"ceol.*laguna verde|laguna verde.*ceol", "consulta_ceol_laguna_verde"),
    (r"ceol.*agua amarga|agua amarga.*ceol|eramet", "consulta_ceol_agua_amarga"),
    (r"ceol.*hilaricos|hilaricos.*ceol", "consulta_ceol_hilaricos"),
    (r"ceol.*piedra parada|piedra parada.*ceol", "consulta_ceol_piedra_parada"),

    # Cumplimiento/sancion ambiental de SQM o Albemarle en el Salar de Atacama
    # (procedimiento distinto del acuerdo Codelco-SQM: se origina en sanciones SMA/RCA)
    (r"programa de cumplimiento|planta cloruro de litio|proyectos de albemarle", "cumplimiento_ambiental_atacama"),

    # Acuerdo/alianza Codelco-SQM (el contrato 2025-2060, incluida su razon social NovaAndino)
    (r"codelco.{0,15}sqm|sqm.{0,15}codelco|novandino|soquimich.{0,15}codelco", "acuerdo_codelco_sqm"),
    (r"acuerdo.*produccion del litio entre el gobierno y sqm", "acuerdo_codelco_sqm"),

    # Extraccion/explotacion generica de litio en el Salar de Atacama, sin nombrar
    # un contrato o consulta especifico: mas especifico que la ENL nacional
    # (ancla territorial a un salar concreto) pero mas generico que un contrato.
    (r"explotacion de litio en (el )?salar de atacama|extraccion de litio en (el )?salar de atacama|"
     r"explotacion de litio en salar de atacama|^salar de atacama$", "atacama_extraccion_generica"),

    # Litio en Maricunga mencionado junto a "otros salares" de forma ambigua: no ancla
    # a un proyecto unico -> abstencion explicita (no se fuerza asignacion).
    # (dejar sin regla -> cae al fallback SIN_SUBHILO_ESPECIFICO)
]


def canonicalize(objeto: str) -> tuple[str, str | None]:
    """Devuelve (clave_canonica, patron_que_matcheo). Si no matchea nada
    especifico, clave_canonica = SIN_SUBHILO_ESPECIFICO y patron=None."""
    norm = normalize_text(objeto)
    if not norm:
        return SIN_SUBHILO, None
    for pattern, key in RULES:
        if re.search(pattern, norm):
            return key, pattern
    return SIN_SUBHILO, None
