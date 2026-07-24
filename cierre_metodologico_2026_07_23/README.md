# Cierre metodológico HEBRA v3 + FTD-Core v1 — 2026-07-23

Carpeta **aditiva**: no modifica ningún artefacto previo de este repositorio ni del repositorio de FTD. Ni HEBRA ni FTD fueron ejecutados de nuevo; no se cambiaron modelos, parámetros ni umbrales.

## Por qué este paquete está en el repositorio de HEBRA

El análisis abarca los dos sistemas, pero se aloja aquí porque:

- el repositorio raíz del proyecto (donde se produjo, `competition/comparativa/`) **no tiene remoto de GitHub**;
- el repositorio de FTD (`Linkhero10/gpt5.6sol-ftd-core`) está en la rama `codex/ftd-candidate-recall`, aparentemente en trabajo activo, y escribir ahí podría interferir;
- esta línea metodológica (validación ciega, reconstrucción de Nivel B, ontología) se ha venido publicando en este repositorio.

**La procedencia de cada artefacto está declarada en el informe.** Si se prefiere, los artefactos específicos de FTD pueden espejarse al repositorio de FTD sin cambiar nada aquí.

## Contenido

| Archivo | Qué es |
|---|---|
| `INFORME_CIERRE_METODOLOGICO_2026_07_23.md` | Informe completo, 10 secciones. **Empezar aquí.** |
| `ftd_segunda_adjudicacion/FTD_BLIND_SHEET_STRIPPED_60.csv` | Hoja ciega de FTD despojada de `source_id`/`target_id` (cierra un vector de fuga real). sha256 `4bce6ce2…` |
| `ftd_segunda_adjudicacion/FTD_SEGUNDA_ADJUDICACION_CLAUDE_2026_07_23.json` | **Segunda adjudicación ciega e independiente de los 60 pares de FTD**, sellada. sha256 `eac01445b239417386bce8f52d486bd31ff1609b1e1ecc966a3a073a8647a73f` |
| `ftd_segunda_adjudicacion/FTD_INTEGRACION_DOS_ADJUDICACIONES.csv` | Cruce de ambas adjudicaciones con la clave sellada |
| `ftd_segunda_adjudicacion/FTD_DESACUERDOS_CLASIFICADOS.csv` | Los 15 desacuerdos con su clasificación de causa |
| `ftd_segunda_adjudicacion/FTD_INTEGRACION_RESUMEN.json` | Métricas de integración |
| `scripts/` | Los cuatro scripts de solo lectura que produjeron los cálculos |

## Advertencia sobre la clave sellada de FTD

`FTD_INTEGRACION_DOS_ADJUDICACIONES.csv` incorpora las columnas de la clave sellada de FTD (`sample_stratum`, `trajectory_id_a/b`, `score`). Esa clave **ya estaba publicada** en el repositorio de FTD (`v1/outputs/private/human_review_answer_key.csv`), de modo que esto no la expone por primera vez. Pero implica que **los 60 pares de esa muestra ya no sirven para una tercera adjudicación ciega**.

## Resultados principales

**FTD — segunda adjudicación (nueva):**
- Acuerdo inter-adjudicador κ = **0,477**, acuerdo bruto 75 % (45/60).
- Acuerdo por estrato: `internal` 90 %, `abstention` 85 %, **`boundary` 50 %**.
- **Sobreabstención replicada y peor**: 75 % (adjudicador 1) → **90 %** (adjudicador 2).
- **13 de 15 desacuerdos son de escala** (macroproceso vs. proceso específico), ninguno error de adjudicador.
- 6 de 15 desacuerdos se concentran en una sola frontera: T0002 ↔ T0115.
- `PAIR-0004` tiene **ambos textos vacíos** y aun así recibió veredicto en la primera adjudicación.

**HEBRA — reconstrucción del Nivel B:**
- La etiqueta `fragmentacion_falsa` **nunca se emitió** en 104 respuestas; la reconstrucción determinista indica 24/24 (Claude) y 18/24 (GPT).
- `sobreagregacion` reconstruida **coincide exactamente** con la publicada: ese lado del instrumento sí funcionaba.
- La tasa reconstruida es una **cota superior condicionada**: el estrato se muestreó sobre el 0,4–2 % de los pares cross-subhilo, los más similares.
- La abstención requiere juzgar **4 documentos**, no re-adjudicar 52 pares.

**Comparación estructural:**
- HEBRA y FTD particionan los mismos documentos de forma casi independiente: ARI 0,024 (Dominga), 0,141 (Ventanas), 0,000 (Bocamina).
- En Bocamina fallan en direcciones **opuestas**; en Dominga, en la **misma** dirección.
- La complementariedad **no está demostrada**.

## Reproducción

Los scripts son de solo lectura y no escriben en ningún repositorio congelado. Rutas absolutas al proyecto local; ajustar `BASE` si se ejecutan en otra máquina.
