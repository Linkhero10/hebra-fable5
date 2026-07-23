# Validación ciega estratificada de HEBRA v3 — Dominga, Ventanas, Bocamina

**No se ajustó `general_extractor.py` ni `build_general_subthreads.py`
para construir esta muestra.** Se usó únicamente la asignación ya
calculada y congelada en
`hebra_v3_experimental/artifacts/v3_node_assignment_all_threads.csv`
(producida en el turno anterior). Este directorio solo *muestrea* pares
desde esa asignación existente; no vuelve a correr el extractor.

## Archivos

- `V3B_BLIND_REVIEW_SHEET.json` — 52 pares ciegos con texto completo. Sin
  ninguna metadata de subhilo/estrato/macrohilo/peso (verificado por
  `test_blind_sample_v3.py::test_no_metadata_leak_in_blind_sheet`).
- `V3B_BLIND_KEY_DO_NOT_OPEN.json` — clave sellada: por `case_id`,
  macrohilo, estrato (`intra_subhilo`/`inter_subhilo`/`abstencion`), los
  dos `doc_id`, el peso de la arista, y los dos `subhilo_primario` que v3
  les asignó. **No abrir antes de completar la adjudicación ciega.**
- `V3B_MANIFEST.json` — hashes de la hoja, la clave y el prompt; conteo de
  estratificación por macrohilo; nota explícita sobre por qué el estrato
  `abstencion` solo tiene casos de H0002.
- `PROMPT_V3B_ADJUDICACION_2026_07_23.md` — prompt para GPT-5.6/Claude,
  con el codebook de dos niveles (identidad procesual + diagnóstico de
  agrupamiento v3: `asignacion_correcta` / `fragmentacion_falsa` /
  `sobreagregacion` / `abstencion_correcta` / `abstencion_incorrecta`).
- `build_blind_sample_v3.py` — script que generó todo lo anterior
  (semilla fija `SEED = 20260781`, reproducible — ver
  `test_blind_sample_v3.py`).
- `test_blind_sample_v3.py` — 5 pruebas: reproducibilidad de contenido
  (no del hash crudo, que incluye un timestamp), unicidad de `case_id`,
  ausencia de fuga de metadata en la hoja ciega, que `abstencion` solo
  venga de H0002, y tamaños de estrato correctos por hilo.

## Estratificación (52 pares, 3 macrohilos)

| Macrohilo | intra_subhilo (sobreagregación) | inter_subhilo (fragmentación falsa) | abstención |
|---|---:|---:|---:|
| H0001 Dominga | 8 | 8 | 0 (cobertura 100%, no aplica) |
| H0002 Fundición Ventanas | 8 | 8 | 4 (único hilo con documentos abstenidos: 4/148) |
| H0004 Bocamina | 8 | 8 | 0 (cobertura 100%, no aplica) |

`inter_subhilo` se estratificó además por similitud léxica entre los dos
nombres de subhilo (mitad de alta similitud — candidatos directos a
fragmentación falsa, p. ej. "minera dominga" vs. "dominga" — mitad de baja
similitud, como control).

## Siguiente paso (no ejecutado aquí)

Enviar `V3B_BLIND_REVIEW_SHEET.json` + el prompt a sesiones nuevas e
independientes de GPT-5.6 y Claude Sonnet 5 (una por modelo, sin
compartir contexto de esta sesión), guardar sus JSON de respuesta sin
editar, y solo entonces cruzar contra `V3B_BLIND_KEY_DO_NOT_OPEN.json`
— exactamente el mismo protocolo de integración usado para H0000.
