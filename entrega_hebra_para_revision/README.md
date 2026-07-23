# Entrega para revisión externa — Validación ciega HEBRA v3 (adjudicador: Claude / Sonnet 5)

Este directorio contiene el resultado final, ya cerrado, de una adjudicación ciega
independiente sobre la muestra `V3B_BLIND_REVIEW_SHEET.json` de
`hebra_v3_experimental/blind_validation/`. El adjudicador fue un modelo Claude
(Sonnet 5), operando exclusivamente sobre la hoja ciega de 52 pares y el
prompt/codebook de adjudicación, sin acceso a la clave sellada
(`V3B_BLIND_KEY_DO_NOT_OPEN.json`), sin ver adjudicaciones previas de otros
evaluadores, y sin ejecutar ni modificar el código de HEBRA.

## 1. Lista de archivos

- `README.md` — este documento.
- `V3B_CLAUDE_ADJUDICACION_2026_07_23.json` — archivo de resultados (único
  artefacto de salida producido por esta adjudicación).

No se generaron CSV, HTML, gráficos ni manifiestos adicionales durante este
ejercicio: la única salida del proceso de adjudicación es el archivo JSON
listado arriba. No se ha fabricado ni derivado ningún archivo adicional para
esta entrega; se copió tal cual el archivo final ya preparado, sin
modificarlo (hash SHA-256 idéntico al original conservado por el equipo de
investigación en `competition/comparativa/Claude/`).

## 2. Qué contiene cada archivo

### `V3B_CLAUDE_ADJUDICACION_2026_07_23.json`

Objeto JSON con la estructura de salida exigida por
`PROMPT_V3B_ADJUDICACION_2026_07_23.md`:

```json
{
  "reviewer_model": "claude-sonnet-5",
  "evidence_class": "independent_ai_adjudication",
  "human_gold": false,
  "cases": [
    {
      "case_id": "V3B000",
      "nivel_a": "mismo_proceso_especifico | mismo_macroproceso | relacionado_tematicamente | no_relacionado | indeterminado",
      "nivel_b_v3": "asignacion_correcta | fragmentacion_falsa | sobreagregacion | abstencion_correcta | abstencion_incorrecta | indeterminado",
      "confidence": "alta | media | baja",
      "justification": "..."
    }
  ]
}
```

Contiene los 52 casos (`V3B000`–`V3B051`) de la hoja ciega, cada uno con:

- **Nivel A** — identidad procesual entre `doc_a` y `doc_b` del par.
- **Nivel B (v3)** — diagnóstico de agrupamiento específico de esta
  validación (si un sistema automático razonable habría agrupado o separado
  correctamente ese par).
- **confidence** — confianza declarada del adjudicador (alta/media/baja).
- **justification** — justificación breve citando evidencia textual
  concreta de los documentos.

Se preservan todos los `case_id` originales de la hoja ciega, sin
duplicados ni omisiones (52/52).

## 3. Qué archivo debe revisarse primero

**`V3B_CLAUDE_ADJUDICACION_2026_07_23.json`** — es el único archivo de
resultados de esta entrega y debe revisarse en conjunto con el codebook
`hebra_v3_experimental/blind_validation/PROMPT_V3B_ADJUDICACION_2026_07_23.md`
(no incluido en esta carpeta; ver sección 6) para interpretar el significado
de cada etiqueta de Nivel A y Nivel B.

## 4. Versión de HEBRA

`hebra_v3_experimental` (extractor general v3), tal como quedó fijado en
`hebra_v3_experimental/MANIFEST_V3.json` y `hebra_v3_experimental/EXPERIMENT_LOCK_V3.json`
al momento de generarse la hoja ciega. Commit de referencia del repositorio
en el que se generó y adjudicó la muestra: `ff3fb8d` ("Muestra ciega
estratificada v3 sobre Dominga, Ventanas y Bocamina").

Esta entrega corresponde exclusivamente a la validación ciega v3
(`blind_validation/`) sobre los tres macrohilos Dominga, Fundición Ventanas
y Bocamina. No incluye ni evalúa FTD ni el benchmark comparativo.

## 5. Fecha de generación

Adjudicación realizada el **2026-07-23**. Esta carpeta de entrega fue
publicada en el repositorio el **2026-07-23**.

## 6. Dependencias entre archivos

- `V3B_CLAUDE_ADJUDICACION_2026_07_23.json` es una salida **derivada** de,
  y solo interpretable junto a, dos archivos que ya existen en el repositorio
  y que **no** se duplican en esta carpeta de entrega (para no crear copias
  redundantes ni alterar los artefactos originales de HEBRA):
  - `hebra_v3_experimental/blind_validation/V3B_BLIND_REVIEW_SHEET.json`
    (la hoja ciega de 52 pares que fue insumo de la adjudicación).
  - `hebra_v3_experimental/blind_validation/PROMPT_V3B_ADJUDICACION_2026_07_23.md`
    (el prompt/codebook que define las etiquetas de Nivel A y Nivel B usadas
    en el JSON de resultados).
- El archivo de resultados **no depende** de, ni fue generado con acceso a,
  `hebra_v3_experimental/blind_validation/V3B_BLIND_KEY_DO_NOT_OPEN.json`
  (la clave sellada permanece sin abrir).
- Para un análisis de acuerdo inter-adjudicador, este archivo es comparable
  1:1 (por `case_id`) con otras adjudicaciones ciegas independientes de la
  misma hoja producidas por otros modelos (por ejemplo, la entrega paralela
  de GPT en `competition/comparativa/`), y finalmente contra la clave
  sellada, que permanece fuera del alcance de este adjudicador.

## Restricciones respetadas en esta entrega

- No se modificó, regeneró ni volvió a ejecutar el archivo de resultados.
- No se ejecutó HEBRA nuevamente ni se cambiaron parámetros.
- No se subió ni referenció nada del repositorio de FTD-Core.
- No se incorporaron archivos de FTD.
- No se eliminó ni sobrescribió ningún otro resultado existente en el
  repositorio.
