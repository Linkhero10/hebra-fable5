# H0000 — Informe empírico final de validación multi-IA e integración con clave sellada

Fecha: 2026-07-22/23. Autor de este informe: Claude Sonnet 5, actuando como
integrador y árbitro sobre evidencia ya congelada. **Adjudicadores válidos:
GPT-5.6 Thinking y Claude Sonnet 5. Gemini se conserva como artefacto
histórico y NO se usa como voto en ningún cálculo de este informe.**

Todos los cálculos son reproducibles desde
`fable5/h0000_validation_2026_07_22/fase1_2_integrate.py`,
`fase2_stratum.py`, `fase3_adjudicate_disagreements.py` y
`fase4_structural_diagnosis.py`. Ninguno de esos scripts modifica la hoja
ciega, la clave sellada ni las respuestas originales de los modelos
(ver verificación de hashes en Fase 1 y en `hebra_v2_experimental`).

---

## Fase 1 — Auditoría e integración

### 1.1 Verificación de conteos

- GPT-5.6: 104/104 casos, sin duplicados, IDs H000–H103 completos.
- Claude Sonnet 5: 104/104 casos, sin duplicados, IDs completos.
- Gemini (histórico, no usado como voto): 104/104 casos, sin duplicados.
- Hoja ciega (`H0000_08_BLIND_REVIEW_SHEET.json`): 104 ítems.
- Clave sellada (`H0000_09_BLIND_KEY_DO_NOT_OPEN.json`): 104 entradas,
  cubre H000–H103.
- Los `doc_id` de cada par en la hoja ciega coinciden exactamente con los
  `a`/`b` de la clave para los 104 casos (verificación cruzada automática
  en el script, sin excepciones).

### 1.2 Distribución por modelo

| Categoría | GPT-5.6 | Claude Sonnet 5 | Gemini (histórico, no usado) |
|---|---:|---:|---:|
| mismo_proceso_especifico | 61 | 56 | 52 |
| mismo_macroproceso | 43 | 42 | 51 |
| relacionado_tematicamente | 0 | 6 | 1 |
| no_relacionado | 0 | 0 | 0 |
| indeterminado | 0 | 0 | 0 |

Nota metodológica: **GPT-5.6 nunca usó las categorías más débiles**
(relacionado_tematicamente / no_relacionado / indeterminado) en ninguno de
los 104 casos. Esto no es necesariamente un error, pero es una asimetría de
calibración real entre los dos adjudicadores que conviene declarar: GPT-5.6
fue sistemáticamente más "generoso" (nunca degradó un par a una categoría
por debajo de macroproceso), mientras que Claude usó
relacionado_tematicamente en 6 casos. Como se ve en la Fase 3, esos 6 casos
concentran una fracción real de los desacuerdos.

### 1.3 Acuerdo, kappa y matriz de confusión (GPT-5.6 vs Claude, N=104)

- **Acuerdo porcentual bruto: 77.9% (81/104)**
- **Cohen's kappa: 0.572** (acuerdo moderado-sustancial según Landis &
  Koch; sustancialmente por encima del azar, pero lejos de acuerdo casi
  perfecto — hay una fracción real de discrepancia conceptual, no solo
  ruido).

Matriz de confusión (filas = GPT-5.6, columnas = Claude):

| GPT \ Claude | especifico | macroproceso | tematico | no_relacionado | indeterminado |
|---|---:|---:|---:|---:|---:|
| **especifico** | 49 | 10 | 2 | 0 | 0 |
| **macroproceso** | 7 | 32 | 4 | 0 | 0 |
| **tematico** | 0 | 0 | 0 | 0 | 0 |
| **no_relacionado** | 0 | 0 | 0 | 0 | 0 |
| **indeterminado** | 0 | 0 | 0 | 0 | 0 |

La casi totalidad del desacuerdo (21 de 23 casos) es un desplazamiento de
**un solo nivel** en la jerarquía (especifico↔macroproceso, o
macroproceso↔tematico); solo 2 casos saltan dos niveles
(especifico↔tematico). Ningún desacuerdo cruza a no_relacionado o
indeterminado. Esto sugiere que el desacuerdo es de **calibración de
umbral** dentro de una jerarquía compartida, no de interpretación
fundamentalmente distinta del corpus.

### 1.4 Lista de desacuerdos

23 casos (ver detalle completo y arbitraje en Fase 3):
`H006, H008, H011, H021, H029, H034, H035, H053, H058, H060, H074, H075,
H077, H079, H080, H081, H083, H086, H088, H093, H097, H099, H101`.

Archivo: `H0000_VALIDATION_INTEGRATED_2026_07_22.json` (contiene los 104
casos completos, cruzados con estrato/detalle de la clave y con metadatos
de arista/comunidad).

---

## Fase 2 — Resultados por escala (estricta vs. amplia) y por estrato

**Definiciones**: estricta = solo `mismo_proceso_especifico`. Amplia =
`mismo_proceso_especifico` + `mismo_macroproceso`. Todas las cifras de esta
sección usan el **consenso GPT-Claude** (ambos deben coincidir en
"positivo") antes de la resolución de desacuerdos de Fase 3; la tabla
post-arbitraje está en Fase 4. Intervalos de confianza: Wilson 95%.

| Grupo | N | % estricto (consenso) | IC95 | % amplio (consenso) | IC95 | Acuerdo GPT-Claude |
|---|---:|---:|---|---:|---|---:|
| **TOTAL** | 104 | 47.1% | [37.8%, 56.6%] | 94.2% | [88.0%, 97.3%] | 77.9% |
| estrato=puente | 20 | 80.0% | [58.4%, 91.9%] | 100% | [83.9%, 100%] | 85.0% |
| estrato=intra | 40 | 47.5% | [32.9%, 62.5%] | 95.0% | [83.5%, 98.6%] | 77.5% |
| estrato=inter | 40 | 30.0% | [18.1%, 45.4%] | 90.0% | [77.0%, 96.0%] | 72.5% |
| estrato=largo | 4 | 50.0% | [15.0%, 85.0%] | 100% | [51.0%, 100%] | 100% |
| arista_es_puente_estructural (n=24, según `edge_metrics.puente`) | 24 | 79.2% | [59.5%, 90.8%] | 100% | [86.2%, 100%] | 83.3% |
| sin_arista_directa (solo transitivo) | 35 | 31.4% | [18.6%, 48.0%] | 88.6% | [74.1%, 95.5%] | 74.3% |
| louvain: intra / inter | 62 / 42 | 54.8% / 35.7% | — | 95.2% / 92.9% | — | 77.4% / 78.6% |
| leiden_cpm: intra / inter | 50 / 54 | 58.0% / 37.0% | — | 96.0% / 92.6% | — | 82.0% / 74.1% |
| leiden_mod: intra / inter | 62 / 42 | 54.8% / 35.7% | — | 95.2% / 92.9% | — | 77.4% / 78.6% |
| infomap: intra / inter | 59 / 45 | 52.5% / 40.0% | — | 94.9% / 93.3% | — | 76.3% / 80.0% |

Tabla completa (32 grupos, incluidos "solo temático") en
`H0000_VALIDATION_BY_STRATUM_2026_07_22.csv`.

**Lecturas principales (antes de arbitraje):**

1. **El nivel amplio (macroproceso) es robusto en absolutamente todos los
   cortes**: 88.6%–100% según el grupo, sin un solo corte por debajo de
   88%. H0000 es un macroproceso empíricamente sólido bajo cualquier
   definición de estrato o algoritmo.
2. **El nivel estricto muestra una brecha intra/inter real y consistente**
   en los cuatro algoritmos de comunidad (Louvain, Leiden-CPM,
   Leiden-modularidad, Infomap): intra siempre 15–23 puntos porcentuales
   por encima de inter. Esto es señal genuina de que la partición
   comunitaria correlaciona con identidad de proceso específico, aunque de
   forma imperfecta (inter nunca cae a 0%: 30–40% de los pares
   inter-comunidad siguen siendo el mismo proceso específico).
3. **Los puentes NO son el punto débil que la intuición sugeriría**: el
   estrato puente (80% estricto, 100% amplio) y las aristas puente reales
   de `edge_metrics` (79.2% estricto) tienen tasas de identidad específica
   *más altas* que el promedio general, consistente con el hallazgo de
   topología previo (F3B): los puentes de H0000 son mayormente
   continuaciones/duplicados casi inmediatos del mismo evento, no enlaces
   espurios de baja evidencia.
4. **El riesgo real de "mezcla por chaining" está en los pares sin arista
   directa** (31.4% estricto, el valor más bajo de toda la tabla) — la
   zona exactamente identificada por el análisis de topología previo como
   de mayor riesgo transitivo.
5. **0% de "solo temático o peor" por consenso en cualquier estrato**:
   nunca ambos modelos coinciden en degradar un par a
   relacionado_tematicamente/no_relacionado/indeterminado. La preocupación
   de "mezcla sustantiva" (opción D de Fase 4) no encuentra apoyo en el
   consenso, aunque sí aparece como desacuerdo individual (Claude usó
   tematico 6 veces, ver Fase 3).

---

## Fase 3 — Resolución de los 23 desacuerdos

**Advertencia metodológica explícita (no un detalle menor):** quien arbitra
es Claude Sonnet 5, el mismo modelo que generó una de las dos adjudicaciones
en disputa. **No es un tercer juez independiente.** Se releyeron los dos
textos completos de cada par (desde la hoja ciega) y ambas justificaciones
antes de fijar cada decisión, aplicando estrictamente el codebook
jerárquico del prompt HEBRA, y se buscó activamente el argumento más fuerte
a favor de GPT-5.6 en cada caso antes de resolver. Aun así, el resultado
agregado es:

- **17/23 (74%)** de las resoluciones finales coinciden con la adjudicación
  original de Claude.
- **4/23 (17%)** coinciden con GPT-5.6 (H011, H021, H093, H097 — dos de
  ellos, H093/H097, tras una reconsideración explícita del argumento de
  GPT-5.6 sobre continuidad de un compromiso presidencial específico).
- **2/23 (9%)** son una síntesis nueva, distinta de ambas originales (H008,
  H029 → mismo_macroproceso, cuando GPT decía especifico y Claude decía
  temático).

**Esta tasa de auto-coincidencia (74%) es un límite real de esta fase, no
un resultado a ignorar.** Se recomienda explícitamente que cualquier uso
posterior de esta resolución como "definitiva" pase primero por un tercer
modelo o un revisor humano no involucrado en la ronda original. El detalle
completo de los 23 casos —decisión de cada modelo, decisión final,
confianza, razón conceptual de la diferencia y justificación textual— está
en `H0000_DISAGREEMENTS_ADJUDICATED_2026_07_22.json`.

### Patrón conceptual dominante en los desacuerdos

De los 21 desacuerdos de un solo nivel, el patrón más frecuente
(9 de 23 casos: H006, H011, H060, H077, H083, H093, H097, y en menor medida
H035/H099) es que **GPT-5.6 trata la pertenencia al mismo macroproceso
institucional (mismos actores generales, mismo gobierno, misma relación
política de largo plazo) como si fuera identidad de procedimiento
específico**, mientras que el codebook exige continuidad de un objeto
textualmente reconocible (el mismo contrato, proyecto, consulta o
litigio nombrado), no solo continuidad de la relación entre las partes. El
segundo patrón (7 casos: H034, H058, H074, H075, H079, H080, H086) es el
inverso: **GPT-5.6 subestimó la continuidad de una campaña o proceso
específico continuo** protagonizado por el mismo actor en una ventana
corta de tiempo (p. ej. la campaña de rechazo del CPA a la ENL en 2023, o
el mismo contrato nombrado discutido desde ángulos distintos). Un tercer
patrón, más sutil (H021/H029/H008 vs H081/H088/H101), distingue entre
documentos que son posturas institucionales reales dentro de la ENL
nombrada (→ macroproceso) de artículos explicativos genéricos sin postura
institucional propia (→ solo temático) — una distinción que ninguno de los
dos modelos originales trazó de forma explícita y consistente.

---

## Fase 4 — Diagnóstico estructural de H0000

**Recalculando con la decisión final post-arbitraje** (consenso donde no
hubo desacuerdo + resolución de Fase 3 donde sí lo hubo):

| Grupo | N | % estricto final | IC95 | % amplio final | IC95 |
|---|---:|---:|---|---:|---|
| **TOTAL** | 104 | **56.7%** | [47.1%, 65.9%] | **97.1%** | [91.9%, 99.0%] |
| estrato=puente | 20 | **95.0%** | [76.4%, 99.1%] | 100% | [83.9%, 100%] |
| estrato=intra | 40 | 60.0% | [44.6%, 73.7%] | 95.0% | [83.5%, 98.6%] |
| estrato=inter | 40 | 35.0% | [22.1%, 50.5%] | 97.5% | [87.1%, 99.6%] |
| louvain / leiden_cpm / leiden_mod / infomap: intra | 62/50/62/59 | 67.7% / 68.0% / 67.7% / 66.1% | — | 96.8%–97.7% | — |
| louvain / leiden_cpm / leiden_mod / infomap: inter | 42/54/42/45 | 40.5% / 46.3% / 40.5% / 44.4% | — | 97.6%–98.2% | — |
| arista_es_puente_estructural | 24 | **95.8%** | [79.8%, 99.3%] | 100% | [86.2%, 100%] |
| sin_arista_directa (transitivo) | 35 | 31.4% | [18.6%, 48.0%] | 97.1% | [85.5%, 99.5%] |

La resolución de Fase 3 **acentúa** el patrón ya visible en el consenso
crudo: sube el nivel estricto en casi todos los grupos (porque varios
desacuerdos se resolvieron hacia "especifico" al reconocer continuidad
real de un mismo contrato/campaña), y el estrato puente pasa de 80% a
**95%** estricto — el hallazgo más fuerte de todo el ejercicio: los
puentes de H0000 son, en la gran mayoría de los casos, la conexión
*correcta* entre partes del mismo proceso específico, no un artefacto de
mezcla.

### Evidencia estructural complementaria (addenda de topología, ya congelados)

- **DSU (todo el grafo = 1 clase) no aporta señal discriminativa**: es
  perfectamente estable entre semillas (trivialmente, al no ser
  estocástico) pero colapsa bajo *edge-drop* del 10% (ARI=0.05, retención
  de pares=0.95 vs 0.886 de Louvain) — es decir, es *menos* robusto que las
  particiones comunitarias frente a perturbación, no más
  (`H0000_15_ADDENDUM_DSU_VS_COMMUNITY_ROBUSTNESS.json`). Tratar "todo
  H0000 conectado" como evidencia de identidad procesual no tiene respaldo.
- **Comunidades interpretables**: el objeto textual dominante por
  comunidad (`H0000_05_PARTITION_COMPARISON.csv`) muestra etiquetas reales
  y distintas — "acuerdo codelco-sqm", "salar futuro", "proyecto blanco",
  "estrategia nacional del litio" — no ruido. Las comunidades no son cajas
  vacías: corresponden a objetos textualmente reconocibles.
- **Heterogeneidad transitiva significativa pero acotada**: 0% de aristas
  DIRECTAS son heterogéneas en objeto+territorio, pero 39.2% de TODOS los
  pares dentro de H0000 (41.8% de los pares solo transitivos) lo son —
  significativamente por encima de un nulo de permutación que preserva la
  topología (observado=5637, media nula=5286.9, p=0.0033,
  `H0000_14_ADDENDUM_HETEROGENEITY_BASELINE.json`). Esto confirma que el
  riesgo de mezcla por *chaining* es real y no solo un artefacto del
  tamaño del grafo, pero está concentrado en los pares sin evidencia
  directa (consistente con el 31.4% estricto de esos pares en la tabla de
  arriba), no en las aristas observadas.
- **Puentes con perfil de dependencia**: 2,148 de 4,345 pares
  dependientes-de-puente dependen de un ÚNICO puente separador (sin
  cadena), y 3 puentes concentran el 19.8% de esos pares de dependencia
  única (`H0000_12_ADDENDUM_BRIDGE_DAMAGE_PROFILE.json`) — el documento
  1943 (parte del cluster de bloqueo de enero 2024) es el nodo de mayor
  riesgo estructural individual, pero también, empíricamente, parte de
  pares mayoritariamente válidos como mismo proceso específico.

### Determinación: ¿A, B, C o D?

**Interpretación B — H0000 es un macroproceso sectorial válido, compuesto
por varios subprocesos identificables — con la salvedad explícita de que
la zona alcanzable solo por cadenas transitivas (sin evidencia directa)
se comporta de forma más parecida a C** (mayor riesgo, menor pureza
estricta, aunque sin caer nunca en D).

Razonamiento, punto por punto contra las cuatro opciones:

- **No es A (proceso único)**: el 43-45% de pares que NO son
  mismo_proceso_especifico (consenso o post-arbitraje) descarta
  homogeneidad total al nivel estricto. Los objetos dominantes por
  comunidad son textualmente distintos entre sí (acuerdo Codelco-SQM ≠
  Proyecto Blanco/Maricunga ≠ Salar Futuro ≠ consultas CEOL individuales).
- **No es D (mezclado sustantivamente)**: el nivel amplio se sostiene en
  ≥88% en CUALQUIER corte, incluidos los pares sin evidencia directa
  (97.1% amplio incluso ahí) y el consenso de "0% solo temático o peor" en
  todo estrato. No hay evidencia de que H0000 mezcle procesos
  sustantivamente distintos sin relación sectorial.
- **Parcialmente C (núcleo válido + enlaces periféricos incorrectos)**:
  esto describiría bien la zona transitiva (31.4% estricto, la más débil
  de la tabla), pero es **engañoso aplicado a los puentes**: los 23
  puentes estructurales del grafo (la definición operacional de "enlace
  periférico" en el diseño F3B) tienen la tasa estricta MÁS ALTA de toda
  la tabla (95.8%), no la más baja. Llamar "periféricos e incorrectos" a
  los puentes sería contradicho directamente por la evidencia ciega.
- **B con matiz**: la brecha intra/inter consistente en los 4 algoritmos
  (60% vs 35% post-arbitraje) y la interpretabilidad textual de las
  comunidades (objetos dominantes distintos y reconocibles) apoyan que
  existen subprocesos reales dentro del macroproceso, aproximables —
  imperfectamente— por partición comunitaria. El matiz honesto es que la
  imperfección de esa aproximación (35-46% de los pares inter-comunidad
  siguen siendo el mismo proceso específico) significa que ninguna
  partición comunitaria puede usarse *directamente* como subhilo sin
  agregar un criterio semántico adicional — exactamente lo que motiva el
  diseño de Fase 5/6 (subhilo por objeto normalizado, no por comunidad de
  grafo).

**Lo que esto NO demuestra**: no demuestra que la arquitectura jerárquica
de Fase 5-6 (o ninguna otra) sea la única forma correcta de capturar estos
subprocesos; no demuestra que el diccionario de normalización usado en el
v2 experimental esté libre de contaminación por conocimiento previo de la
muestra (ver advertencia en `hebra_v2_experimental/README.md`); no declara
qué algoritmo de comunidad es "mejor" (ninguno se elige aquí, igual que en
F3B); no es una validación humana.

---

## Fase 5 y 6 — Arquitectura jerárquica y su implementación experimental

Diseño completo: `HEBRA_HIERARCHICAL_DESIGN_2026_07_22.md` (mismo
directorio). Implementación: `fable5/hebra_v2_experimental/` (carpeta
nueva, separada, no sobrescribe v1). Resumen de resultados de esa
implementación (detalle completo en su propio README):

- **Cobertura**: 112/170 documentos (65.9%) reciben un subhilo concreto;
  58/170 quedan en abstención explícita.
- **Pureza estricta de subhilo (sobre la muestra ciega, evaluación
  confirmatoria, no fuera de muestra — ver advertencia de contaminación):
  93.6%**, muy por encima del 60-68% que lograba usar directamente
  cualquier algoritmo de comunidad como proxy de subproceso.
- **Retención amplia entre subhilos distintos: 100%** sobre los pares
  evaluables — dividir en subhilos no destruyó ninguna continuidad amplia
  observada.
- 3 de 23 puentes cruzan entre subhilos distintos, y los 3 son cruces
  entre categorías textualmente muy cercanas — consistente con la lectura
  de que los puentes de H0000 son mayormente correctos.
- Todas las pruebas automatizadas (10/10) pasan: reproducibilidad,
  no-modificación de v1, integridad de IDs, forma de la asignación,
  mecanismo de multiasignación (sintético), abstenciones, no pérdida de
  documentos, estabilidad ante orden de entrada, manifest/hashes,
  comparación con v1.

---

## Cumplimiento de restricciones explícitas del encargo

- ✅ No se sobrescribió ningún artefacto sellado (verificado por hash en
  cada corrida de `build_hierarchy.py` y en Fase 1).
- ✅ Gemini no se usó como voto válido en ningún cálculo (kappa, matriz de
  confusión, estratos, arbitraje) — solo se reporta su distribución como
  referencia histórica.
- ✅ No se declara superioridad global sobre FTD (no se menciona FTD en
  ningún cálculo sustantivo de este informe).
- ✅ No se ajustaron parámetros del diccionario de subhilo mirando qué
  maximizaba el acuerdo con los 104 pares y reportando eso como
  evaluación independiente — pero se declara explícitamente el riesgo de
  contaminación por conocimiento previo (ver advertencia en Fase 4 y en el
  README de `hebra_v2_experimental`), y la pureza del 93.6% se etiqueta
  como evidencia confirmatoria preliminar, no validación fuera de muestra.
- ✅ Confirmatorio (Fases 1-2, con datos y kappa ya fijados antes de leer
  los textos en detalle) vs. exploratorio (Fase 3, releer y arbitrar) vs.
  decisiones de diseño (Fase 5) están en documentos y secciones separadas.
- ✅ La implementación de Fase 6 se llama explícitamente "experimental" en
  su carpeta, README, manifest y lock.
- ✅ No hubo optimización cosmética antes de cerrar las métricas
  sustantivas (el diccionario de subhilo se escribió una sola vez a partir
  de los valores de `objeto`, sin iterar buscando mejorar la pureza).

---

## Resumen de cierre

**1. Qué demuestra la validación.** Que GPT-5.6 y Claude Sonnet 5,
trabajando ciegos e independientes sobre 104 pares de H0000, concuerdan
sustancialmente (77.9%, κ=0.57) en que H0000 es válido como macroproceso
(94-97% amplio en todo corte) y concuerdan parcialmente (47-57% estricto,
con una brecha intra/inter real y replicada en 4 algoritmos de comunidad)
en que dentro de ese macroproceso hay múltiples procesos específicos
distinguibles. Los puentes estructurales del grafo son, empíricamente, la
parte MÁS confiable del hilo al nivel estricto (80-95.8%), no la más
débil. El riesgo real de sobre-conexión está concentrado en los pares
sin evidencia textual directa (31.4% estricto).

**2. Qué NO demuestra.** No demuestra cuál es "la" partición correcta de
subprocesos (ningún algoritmo de comunidad fue elegido); no valida el
diccionario de subhilo del v2 experimental fuera de muestra; no involucra
gold humano; la resolución de los 23 desacuerdos de Fase 3 tiene un sesgo
de auto-confirmación declarado (74% coincide con la adjudicación Claude
original) que requiere un tercer revisor antes de tratarse como definitiva;
no compara ni declara ganador frente a FTD.

**3. ¿Es H0000 válido como macroproceso?** Sí, con alta confianza y
consistencia across todos los cortes analizados (≥88% amplio siempre,
97.1% global post-arbitraje).

**4. ¿Qué subprocesos fueron identificados?** Con evidencia textual
directa (campo `objeto` ya extraído por v1, mapeado a un diccionario
auditable): acuerdo/alianza Codelco-SQM (2025-2060), Proyecto Salar
Blanco/Maricunga (incluida su fase Rio Tinto/CEOL), Salar Futuro
(subproyecto tecnológico), consultas indígenas CEOL específicas por salar
(Laguna Verde, Agua Amarga, Hilaricos), y cumplimiento/sanción ambiental de
SQM-Albemarle en Atacama — más una categoría residual de "extracción
genérica en Salar de Atacama" sin contrato/procedimiento nombrado. 34% de
los documentos no calzan en ninguna categoría específica y quedan en
abstención explícita a nivel de subhilo (siguen perteneciendo al
macrohilo).

**5. Qué cambios se implementaron.** Ninguno sobre HEBRA v1 (permanece
intacto y verificado por hash). Se creó, en carpetas nuevas y separadas:
(a) la validación integrada de Fases 1-4
(`fable5/h0000_validation_2026_07_22/`), y (b) una arquitectura jerárquica
experimental de dos niveles (macrohilo = hilo v1 sin cambios; subhilo =
agrupación por objeto normalizado) en
`fable5/hebra_v2_experimental/`, con su propio manifest, lock y pruebas.

**6. Qué pruebas pasaron.** Las 10 pruebas automatizadas de
`hebra_v2_experimental/tests/test_hierarchy.py` pasan: reproducibilidad
con semilla fija, no modificación de v1 (verificado por hash contra el
manifest v1 congelado), integridad de IDs (170/170 sin pérdidas ni
duplicados), forma correcta de la asignación macro/subproceso, mecanismo
de multiasignación (probado con datos sintéticos, ya que el corpus real no
lo dispara al umbral elegido), abstenciones explícitas (nunca `NaN`
silencioso), ausencia de pérdida silenciosa de documentos, estabilidad
ante orden de entrada de los CSV de entrada, generación de manifest/lock
con hashes verificables, y comparación reproducible con v1 (mismo
`macrohilo_id`, mismo conteo de documentos).

**7. Qué queda pendiente antes de comparar formalmente con FTD.** (a) Una
segunda ronda de arbitraje de los 23 desacuerdos con un tercer modelo o
revisor humano no involucrado en la ronda original, dado el sesgo de
auto-confirmación declarado. (b) Validación del diccionario de subhilo
sobre una muestra ciega *nueva*, construida después de fijar las reglas
(la actual es confirmatoria, no fuera de muestra). (c) Una decisión
explícita — que este ejercicio deliberadamente no toma — sobre si el
`subhilo` de HEBRA v2 debe tratarse como equivalente estructural a un
`community`/`thread` de FTD antes de intentar cualquier comparación de
métricas entre ambos sistemas; mezclar unidades de análisis distintas sin
esa decisión invalidaría cualquier comparación numérica directa.
