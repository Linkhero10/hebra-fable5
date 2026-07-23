# Especificación del benchmark común HEBRA v2 ↔ FTD

Estado: **especificación y andamiaje de scripts únicamente. No se ejecuta
ninguna comparación numérica en este documento ni en el script asociado
(`compare_with_ftd_skeleton.py`). No se declara ni se insinúa qué sistema
es mejor.**

## 1. Hallazgo de compatibilidad ya verificado (hecho, no hipotético)

Se verificó por intersección directa de IDs que **ambos sistemas operan
sobre el mismo espacio de documentos**:

- FTD (`gpt5.6sol/outputs/threshold_0p58_assignments.csv`, columna `id`):
  3.742 documentos, el corpus completo.
- HEBRA (`fable5/outputs/f2b_idf_v2_L2_threads.csv`, columna `doc_id`):
  1.853 documentos (los que caen en algún hilo de tamaño ≥1).
- **Intersección: 1.853 / 1.853** — todo documento que HEBRA agrupa en un
  hilo también existe en el universo de FTD. La comparación es factible
  sin necesidad de reconciliar IDs.

## 2. Unidad de análisis: el problema central a resolver antes de comparar

FTD y HEBRA v2 NO tienen la misma granularidad nativa:

| | Unidad más gruesa | Unidad más fina | Mecanismo de abstención propio |
|---|---|---|---|
| **FTD** | `trajectory_id` (53 en todo el corpus, `threshold_0p58_assignments.csv`) | no hay nivel 2 documentado en los artefactos revisados | sí: `status` ∈ {assigned, abstain_low_margin, abstain_low_support} |
| **HEBRA v2** | `macrohilo_id` (178 hilos, uno de ellos H0000) | `subhilo_id` (dentro de un macrohilo) | sí: `subhilo_primario = SIN_SUBHILO_ESPECIFICO` |

Los 53 `trajectory_id` de FTD sobre 3.742 documentos (~70 docs/trayectoria
en promedio) son estructuralmente mucho más parecidos, en granularidad, al
**macrohilo** de HEBRA (178 hilos sobre 1.853 docs, ~10 docs/hilo en
promedio — hilos más chicos, pero del mismo orden conceptual: "todos los
documentos de un mismo proceso/controversia amplia") que al subhilo (un
concepto que FTD, por lo que se ha revisado, no tiene).

**Decisión que este documento deja explícitamente ABIERTA, no tomada:**
¿se compara FTD-trajectory vs. HEBRA-macrohilo (comparación directa,
mismo nivel conceptual aproximado) o existe en el repositorio de FTD algún
artefacto de sub-agrupación más fino que no se ha localizado todavía? Antes
de ejecutar cualquier métrica de acuerdo entre ambos sistemas, alguien con
contexto de FTD debe confirmar esto. El script esqueleto (sección 4) deja
un parámetro explícito para esta decisión (`FTD_UNIT`) que no se auto-
completa.

## 3. Mapeo de categorías (para cuando exista validación ciega de ambos lados)

El prompt de validación FTD-Core (`PROMPT_FTD_*_2026_07_22.md`) usa un
codebook de dos niveles + decisión final:

- Nivel A (identidad local): `si | parcial | no | indeterminado`
- Nivel B (homogeneidad comunitaria): `homogenea | mezclada | incierta`
- Decisión final: `asignacion_correcta | asignacion_incorrecta | debe_abstener | indeterminado`

HEBRA usa un codebook de identidad procesual directa:

- `mismo_proceso_especifico | mismo_macroproceso | relacionado_tematicamente | no_relacionado | indeterminado`

**Mapeo propuesto (a validar antes de usarlo, no auto-adoptado):**

| FTD decisión final | HEBRA equivalente aproximado |
|---|---|
| `asignacion_correcta` | `mismo_proceso_especifico` **o** `mismo_macroproceso` (FTD no distingue esta subdivisión; requiere decisión) |
| `asignacion_incorrecta` | `relacionado_tematicamente` o `no_relacionado`, según el caso |
| `debe_abstener` | `indeterminado`, o el documento cae en `SIN_SUBHILO_ESPECIFICO`/`abstain_*` de cada sistema |
| `indeterminado` | `indeterminado` |

Esta tabla es una **primera aproximación de traducción semántica**, no una
identidad matemática — FTD evalúa "¿pertenece el documento objetivo a ESTA
comunidad candidata?" (una pregunta de membresía de a un doc contra un
grupo ya formado), mientras HEBRA evalúa "¿son estos DOS documentos el
mismo proceso?" (una pregunta pairwise). Convertir de uno a otro requiere
decidir, por ejemplo, si "correcta" en FTD se traduce a nivel de par
(todos los pares docto-objetivo × miembro-de-comunidad) o se dejan como
juicios de membresía no pareados. **No se resuelve aquí.**

## 4. Qué falta del lado FTD antes de poder ejecutar algo

1. Confirmar si existe una sub-agrupación de FTD más fina que
   `trajectory_id` (ver sección 2). Si no existe, la comparación de
   "subhilo" queda forzosamente limitada a comparar HEBRA-subhilo contra
   nada (no hay equivalente FTD) — solo HEBRA-macrohilo vs FTD-trajectory
   sería comparable.
2. Una validación ciega de FTD sobre los MISMOS 104 pares de H0000 (o
   sobre pares nuevos de los 18 hilos de este benchmark) con el codebook
   de FTD, análoga a la que ya se hizo para HEBRA con GPT-5.6/Claude —
   sin esto, no hay "ground truth" comparable de ambos lados, solo
   estructura.
3. Decisión explícita (de quien mantiene FTD, no de este ejercicio) sobre
   si `status=abstain_low_margin`/`abstain_low_support` de FTD debe
   tratarse como una sola categoría de abstención o dos distintas al
   compararlas con `SIN_SUBHILO_ESPECIFICO` de HEBRA.

## 5. Métricas que SÍ se pueden calcular en cuanto se resuelva la sección 2

Una vez fijada la unidad de análisis común:

- **ARI / NMI entre la partición FTD y la partición HEBRA**, sobre el
  subconjunto de documentos donde ambos sistemas asignan (no abstienen).
- **Tasa de acuerdo de abstención**: de los documentos donde HEBRA abstiene
  (`SIN_SUBHILO_ESPECIFICO`), qué fracción FTD también marca
  `abstain_*`, y viceversa.
- **Cobertura comparada**: % de documentos con asignación no-abstención en
  cada sistema, sobre el mismo universo de documentos.
- Si existe validación ciega de ambos lados (sección 4.2): acuerdo con
  gold, kappa, y matriz de confusión **por sistema**, exactamente como se
  hizo para HEBRA en `H0000_FINAL_EMPIRICAL_REPORT_2026_07_22.md` — nunca
  un "ganador" único sin decidir antes las secciones 2-4.

## 6. Restricciones que este documento respeta explícitamente

- No se ejecuta ninguna de las métricas de la sección 5 todavía.
- No se declara que HEBRA sea superior a FTD, ni viceversa.
- No se fuerza la decisión de unidad de análisis (sección 2): se deja
  como parámetro explícito, no como default silencioso.
- No se modifica ningún artefacto de FTD (`gpt5.6sol/`,
  `gpt5.6sol_v1_postcompetition/`, etc.) ni de HEBRA v1/v2.
