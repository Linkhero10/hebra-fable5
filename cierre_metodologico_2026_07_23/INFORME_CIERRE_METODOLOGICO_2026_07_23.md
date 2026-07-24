# Informe de cierre metodológico — HEBRA v3 y FTD-Core v1

Fecha: 2026-07-23. Agente principal: Claude Opus 5.
Repositorios congelados, **no modificados**: `Linkhero10/hebra-fable5` (paquete `entrega_hebra_para_revision/`, adjudicación GPT en `6d2cdef`) y `Linkhero10/gpt5.6sol-ftd-core` (paquete `entrega_ftd_para_revision/`, commit `4b92cc548acebf55697e60686d4023b56af37712`).

Todo lo producido en este informe se escribió **fuera de ambos repositorios**, en `competition/comparativa/`. No se ejecutó HEBRA ni FTD, no se cambiaron parámetros ni se generaron resultados experimentales nuevos.

## Convención de estatus epistémico

Cada afirmación de este informe está marcada con uno de estos cinco estados:

- **[EV]** evidencia observada — leída directamente de un artefacto publicado.
- **[CD]** cálculo determinista — recuento o mapeo reproducible sobre artefactos publicados; no introduce juicio.
- **[INF]** inferencia — conclusión razonada a partir de [EV]/[CD], podría ser discutida.
- **[DT]** decisión teórica — elección conceptual que otro revisor competente podría tomar distinta.
- **[REC]** recomendación — propuesta de acción, no un hallazgo.

---

## 1. Protocolo de subagentes y trazabilidad

### 1.1 Por qué el agente principal NO podía adjudicar FTD

**[EV]** En el turno anterior de esta misma conversación, el agente principal leyó:

- `phase2_replica/04_FTD_CORE_V1_FINAL_PERFORMANCE_REPORT.md`, que contiene (§3) la distribución completa de veredictos por estrato sellado y (§4) **la lista literal de los 15 `review_item_id` cuya abstención resultó ser el mismo proceso** (`PAIR-0002, 0006, 0007, 0010, 0013, 0016, 0030, 0040, 0041, 0044, 0045, 0046, 0047, 0049, 0059`), más los 5 pares de error nombrados (`PAIR-0009, 0015, 0018, 0019, 0060`).
- `phase2_replica/01_integrated_adjudication.csv`, del que imprimió los registros completos de 5 pares, incluyendo `expert_ai_verdict`, `sample_stratum`, `trajectory_id_a/b` y `error_class`.

**[CD]** Eso significa que el agente principal conoce el veredicto esperado de **20 de los 60 pares (33 %)**, su estrato, y la distribución total de respuestas por estrato.

**[INF]** Una "segunda adjudicación ciega" hecha por el agente principal habría producido un kappa inflado y no interpretable. Sería **peor que no tener segunda adjudicación**, porque generaría confianza falsa en la métrica que precisamente se quería controlar. Por eso la Fase 2 se delegó a un subagente de contexto frío.

**[DT]** Se asume que un subagente lanzado en esta sesión no hereda el contexto conversacional del agente principal, y que por tanto su ceguera depende únicamente de (a) los archivos que se le permiten abrir y (b) que el prompt no contenga información contaminante. Ambas condiciones se controlaron explícitamente; la primera es verificable por los archivos que declaró haber leído, la segunda es verificable leyendo el prompt.

### 1.2 Tabla de trazabilidad de subagentes

| Subagente | Tarea delimitada | Archivos que se le permitió leer | Archivos explícitamente prohibidos | Resultado | Incertidumbres declaradas |
|---|---|---|---|---|---|
| **S1 — Adjudicador ciego FTD** (contexto frío) | Adjudicar los 60 pares de FTD sin acceso a clave, estrato ni adjudicación previa | Únicamente `comparativa/FTD_segunda_adjudicacion_2026_07_23/FTD_BLIND_SHEET_STRIPPED_60.csv` (hoja despojada, sha256 `4bce6ce2…`) | `outputs/private/**` (clave), `human_review_blind.csv` con IDs, `selected/assignments.csv`, `links.csv`, `trajectory_summaries.csv`, `signatures.csv`, todo `validacion/**`, todo `phase2_replica/**`, todo archivo con `ADJUDICACION`/`PERFORMANCE`/`integrated`/`answer_key`/`KEY`/`metrics`/`stratum` en el nombre, y todo el repositorio `hebra-fable5` | Ver §2 | Ver §2 |

**Subagentes NO lanzados, y por qué.** Se descartó un subagente auditor de trayectorias FTD (esa auditoría se cerró en el turno anterior) y un subagente verificador de la reconstrucción de Nivel B (es un mapeo determinista que el agente principal ejecutó y reprodujo dos veces; una verificación independiente no habría añadido información). Se prefirió **un solo subagente con la responsabilidad donde la independencia es indispensable** —la adjudicación ciega— en lugar de multiplicar agentes sobre los mismos artefactos, conforme a la regla de no reinterpretar un mismo resultado sin dejar constancia.

### 1.3 Control de cegamiento aplicado (Fase 1)

**[EV] Verificación de hashes contra los declarados** en `04_FTD_CORE_V1_FINAL_PERFORMANCE_REPORT.md` §1:

| Artefacto | Ruta canónica | SHA-256 recalculado | ¿Coincide con el declarado? |
|---|---|---|---|
| Muestra ciega | `gpt5.6sol/outputs/human_review_blind.csv` | `3eae0f8180d081b5a9be7ece59f322a0bea7296e16201bc0562ba0d7e0db61b9` | ✅ |
| Clave sellada | `gpt5.6sol/outputs/private/human_review_answer_key.csv` | `8c6dce40a129446ff775cbbd7a7e8877b2a2e4579e86c9d824491921122c3713` | ✅ |
| Primera adjudicación | `gpt5.6sol/validacion/FTD_CORE_EXPERT_AI_ADJUDICATION_BLIND.csv` | `3a36097571e9b31ebbcc861f1c350946a798c5741eeae955018a6a27f0ed7fd5` | ✅ |

**[EV] Discrepancia menor detectada, no bloqueante.** La copia publicada en el repositorio (`gpt5.6sol_github_public/v1/outputs/human_review_blind.csv`) tiene hash distinto (`99d0b0ec…`). **[CD]** La diferencia afecta 59 de 60 filas en los campos de texto y consiste **exclusivamente en la inserción de retornos de carro `\r`** (similitud de secuencia 0.999; longitud media 972 vs 977 caracteres). Es una diferencia de fin de línea CRLF/LF, no de contenido. **[REC]** Debe documentarse en el paquete para que un revisor externo que recalcule hashes sobre la copia de GitHub no concluya que la muestra fue alterada.

**[EV] La hoja ciega original está correctamente cegada en cuanto a etiquetas**: sus columnas son `review_item_id`, `source_id`, `titulo_a`, `texto_revision_a`, `fecha_iso_a`, `fecha_publicacion_a`, `fuente_a`, y los homólogos `_b`, más tres columnas de respuesta vacías. **No contiene** estrato, `trajectory_id` ni `score`.

**[INF] Pero contenía un vector de fuga real:** `source_id` y `target_id` son los identificadores reales de documento, y `selected/assignments.csv` está publicado en el mismo paquete. Cualquier adjudicador con acceso al repositorio podía cruzar ambos y recuperar la trayectoria de cada documento, y de ahí el estrato. Esto no implica que el primer adjudicador lo hiciera —declara `blind_at_decision=true` en las 60 filas—, pero significa que **su ceguera dependía de su propia disciplina, no del diseño del artefacto**.

**[CD] Mitigación aplicada a la segunda adjudicación:** se generó una hoja despojada (`FTD_BLIND_SHEET_STRIPPED_60.csv`, sha256 `4bce6ce2…`) eliminando `source_id`, `target_id`, `fecha_publicacion_*` y las columnas de respuesta. El subagente recibió únicamente esa hoja. La reunión posterior con la clave se hace por `review_item_id`, que no revela nada.

**Archivos ABIERTOS para la Fase 2:** solo la hoja despojada.
**Archivos CERRADOS durante la Fase 2:** clave sellada, hoja con IDs, todos los outputs de `selected/`, toda la carpeta `validacion/`, toda la carpeta `phase2_replica/`, y el repositorio HEBRA completo.

**[EV] Limitación del material que ningún control puede corregir:** los textos de la hoja ciega están truncados a **1.000 caracteres** (longitud media observada 972). La hoja ciega de HEBRA v3, en cambio, entrega hasta 6.000. **[INF]** Cualquier comparación entre la calidad de adjudicación de FTD y la de HEBRA está confundida por esta diferencia de material: el adjudicador de FTD trabaja con seis veces menos texto por documento.

---

## 2. Adjudicación ciega sellada de FTD

### 2.1 Registro de sellado

| Campo | Valor |
|---|---|
| Archivo | `comparativa/FTD_segunda_adjudicacion_2026_07_23/FTD_SEGUNDA_ADJUDICACION_CLAUDE_2026_07_23.json` |
| SHA-256 | `eac01445b239417386bce8f52d486bd31ff1609b1e1ecc966a3a073a8647a73f` |
| Fecha | 2026-07-23 |
| Adjudicador | Subagente Claude de contexto frío (S1) — **no** "segundo evaluador experto independiente" (§2.1.b) |
| Insumo único | `FTD_BLIND_SHEET_STRIPPED_60.csv`, sha256 `4bce6ce2…f7f3e18` |
| Casos | 60 (`PAIR-0001`…`PAIR-0060`), sin duplicados ni omisiones |

**[EV]** El hash se calculó **antes** de abrir la clave sellada; la clave se abrió solo en la Fase 3.

**[EV] Declaración de aislamiento de S1:** informa no haber abierto ningún archivo distinto de la hoja despojada; sus únicas operaciones sobre el proyecto fueron un `ls` del directorio de adjudicación, el cálculo del SHA-256 del CSV y lecturas del propio CSV.

### 2.1.b Denominación correcta de esta adjudicación

**[DT]** Esta adjudicación debe llamarse **"segunda adjudicación ciega por un subagente aislado de Claude"**, y no "segundo evaluador experto independiente". Tres razones:

1. La separación de contexto entre agente principal y subagente es una **propiedad del sistema que se asume**, no que se demuestre desde dentro (ya declarado como `[DT]` en §1.1).
2. Sigue siendo acuerdo **IA–IA**, no validación humana. Ningún κ de este informe es un acuerdo inter-humano.
3. Adjudicador 1 (GPT-5.6 Thinking) y adjudicador 2 (Claude) son modelos distintos, lo que sí aporta variación real de evaluador — pero no equivale a independencia de dos expertos humanos.

**[REC]** Toda cifra de acuerdo de este informe debe reportarse con esa etiqueta explícita.

### 2.2 Distribuciones

**[EV]** Escala original de FTD (4 categorías): `mismo_proceso` 46, `relacionado` 10, `no_relacionado` 2, `indeterminado` 2.
**[EV]** Escala fina (5 categorías): `mismo_proceso_especifico` 33, `mismo_macroproceso` 23, `relacion_tematica` 0, `no_relacionados` 2, `evidencia_insuficiente` 2.
**[EV]** Confianza: alta 35, media 20, baja 5.
**[EV]** Banderas: `problema_granularidad` 24, `riesgo_fragmentacion` 3, `riesgo_sobreagregacion` 9.

**[INF]** El dato más informativo de esta adjudicación es interno: **23 de los 46 `mismo_proceso` de la escala de 4 bajan a `mismo_macroproceso` en la escala fina**. Es decir, la mitad de lo que la escala original de FTD cuenta como "identidad de proceso" es, bajo una definición estricta, identidad de *macroproceso*. La escala de 4 categorías de FTD **no distingue esas dos cosas**.

### 2.3 Calidad del material — hallazgo no anticipado

**[EV]** S1 reportó pares donde el texto no permitía decidir. Verificación independiente del agente principal sobre la hoja canónica:

- **`PAIR-0004`: ambos textos completamente vacíos (0 caracteres).** Confirmado: es el único par con longitud 0 y el único con menos de 300 caracteres en `texto_revision_a`; la mediana y el percentil 25 son ambos 1.000.
- **[EV, no verificado independientemente]** S1 reporta además que `PAIR-0019`, `PAIR-0015`, `PAIR-0023` y `PAIR-0051` tienen cuerpos compuestos únicamente por menús de navegación del medio (boilerplate), decidibles solo por titular. Esta caracterización es de contenido, no de longitud, y no fue verificada por el agente principal.

**[INF]** Un par con texto vacío que aun así recibió veredicto en la primera adjudicación es un problema de control de calidad del instrumento de FTD, independiente del rendimiento del modelo.

---

## 3. Integración de las dos adjudicaciones

### 3.1 Acuerdo inter-adjudicador (escala original de FTD, 4 categorías)

**[CD]**

| Métrica | Valor |
|---|---|
| Acuerdo bruto | **75,0 %** (45/60) |
| Cohen's kappa | **0,477** (moderado) |

**[EV]** Distribuciones comparadas: v1 (GPT-5.6 Thinking) `mismo_proceso` 36 / `relacionado` 22 / `no_relacionado` 2; v2 (Claude frío) 46 / 10 / 2, más 2 `indeterminado`.

**[CD] Matriz de confusión** (filas v1, columnas v2):

| v1 ↓ / v2 → | indeterminado | mismo_proceso | no_relacionado | relacionado |
|---|---:|---:|---:|---:|
| **mismo_proceso** | 1 | 34 | 0 | 1 |
| **no_relacionado** | 0 | 0 | 2 | 0 |
| **relacionado** | 1 | **12** | 0 | 9 |

**[INF]** El desacuerdo es asimétrico y de un solo tipo: **12 pares que v1 llamó `relacionado`, v2 los llamó `mismo_proceso`**. v2 es sistemáticamente más inclusivo en la frontera de identidad. No hay ningún caso de inversión grave (nadie dijo `mismo_proceso` donde el otro dijo `no_relacionado`).

### 3.2 Acuerdo por estrato sellado

**[CD]**

| Estrato | n | Acuerdo | v1 | v2 |
|---|---:|---:|---|---|
| `internal` (misma trayectoria) | 20 | **90 %** | 18 mismo / 2 rel. | 17 mismo / 1 rel. / 2 indet. |
| `abstention` | 20 | **85 %** | 15 mismo / 4 rel. / 1 no-rel. | 18 mismo / 1 rel. / 1 no-rel. |
| `boundary` (trayectorias distintas) | 20 | **50 %** | 16 rel. / 3 mismo / 1 no-rel. | 11 mismo / 8 rel. / 1 no-rel. |

**[INF]** El acuerdo se desploma exactamente en la frontera entre trayectorias (50 %), y es alto donde el sistema afirma identidad (90 %) o abstiene (85 %). **La frontera de trayectoria de FTD es el punto donde dos adjudicadores expertos dejan de coincidir**, que es el mismo diagnóstico que la reconstrucción de HEBRA arrojó para su propio estrato `inter_subhilo`.

### 3.3 Sobreabstención: hallazgo replicado

**[CD]**

| Adjudicador | Pares del estrato `abstention` juzgados `mismo_proceso` | Tasa |
|---|---:|---:|
| v1 GPT-5.6 Thinking | 15/20 | 75,0 % |
| v2 Claude frío | 18/20 | **90,0 %** |

**[INF]** Este es el resultado más sólido de toda la integración: **la sobreabstención de FTD v1 queda replicada por un segundo adjudicador independiente, y la estimación empeora**. Deja de ser el juicio de un solo modelo. Es la única métrica de rendimiento de FTD que ahora tiene control inter-evaluador.

### 3.4 Clasificación de los 15 desacuerdos

**[CD]** Distribución por estrato: `boundary` 10, `abstention` 3, `internal` 2.

**[CD]** Concentración por par de trayectorias: **(T0002, T0115) concentra 6 de los 15 desacuerdos** — es decir, la frontera entre "Quintero-Puchuncaví/crisis de contaminación" y "Fundición Ventanas". Le sigue (T0001, T0115) con 2. Ningún otro par supera 1.

### 3.4.1 CORRECCIÓN — la primera clasificación era circular

**La versión inicial de este informe afirmaba que "13 de 15 desacuerdos son de escala y ninguno es error de adjudicador". Esa afirmación era inválida y se retira.**

**[EV] El defecto.** La regla de clasificación era:

```python
if r.problema_granularidad:
    return "diferencia_macroproceso_vs_proceso_especifico"
```

`problema_granularidad` es una **bandera que el propio adjudicador 2 se auto-asignó**. La cadena era: (1) Claude adjudica el par como macroproceso; (2) Claude marca la bandera; (3) el script usa la bandera para concluir que el desacuerdo con GPT es de granularidad; (4) el informe lo presentaba como clasificación determinista de la causa.

**[INF] Consecuencias del defecto:**
- La clasificación no era una determinación independiente de la causa, sino **una reexpresión estructurada del juicio de un adjudicador**. Estaba mal etiquetada como `[CD]`; en el mejor de los casos era `[INF]`.
- La afirmación "ninguno es error de adjudicador" era un **artefacto del orden de las reglas**: la bandera de granularidad cortocircuitaba antes de que cualquier caso pudiera clasificarse como error. Por construcción, la categoría "error de adjudicador" **no podía salir nunca**.

**[REC] Corrección aplicada:** los 15 desacuerdos se sometieron a un **arbitraje ciego por un tercer adjudicador** (subagente de contexto frío, S2), que recibió los textos y las dos etiquetas en disputa **anonimizadas y con el orden aleatorizado por fila** (8 casos con v1 como "X", 7 con v2 como "X"), y **sin** las banderas ni las justificaciones de ninguno de los dos. Resultado en §3.4.2.

### 3.4.2 Arbitraje ciego de los 15 desacuerdos

*(Pendiente — se completa con el resultado de S2.)*

**[EV] Lo que sí se sostiene sin arbitraje:** S1 declaró espontáneamente la tensión de escala en su informe final —en la familia Quintero-Puchuncaví-Concón trató la contaminación de la bahía como una sola controversia en la escala de 4 y reservó la distinción para la escala fina—, y **23 de sus 46 `mismo_proceso` bajan a `mismo_macroproceso`** en la escala fina. Eso es evidencia directa de que **el codebook de 4 categorías de FTD no puede expresar la distinción**, con independencia de cuál sea la causa de cada desacuerdo concreto. Esa conclusión no depende de la clasificación retirada.

---

## 4. Reconstrucción corregida del Nivel B de HEBRA

### 4.1 ¿Es reconstruible determinísticamente? Sí, para 48 de 52 pares

**[DT]** La regla de reconstrucción es la definición literal del propio codebook, aplicada de forma consistente. No introduce juicio nuevo: usa el `nivel_a` que cada modelo ya publicó y el estrato real de la clave sellada.

| Estrato real (lo que HEBRA hizo) | `nivel_a` ya publicado | Nivel B correcto |
|---|---|---|
| `intra_subhilo` (los agrupó) | `mismo_proceso_especifico` | `asignacion_correcta` |
| `intra_subhilo` | cualquier otro | `sobreagregacion` |
| `inter_subhilo` (los separó) | `mismo_proceso_especifico` | `fragmentacion_falsa` |
| `inter_subhilo` | cualquier otro | `asignacion_correcta` |
| `abstencion` | — | **no reconstruible** (§4.3) |

### 4.2 Resultado: la etiqueta de fragmentación estaba sistemáticamente ausente

**[CD]** Tasas reconstruidas frente a las publicadas, por macrohilo:

| Macrohilo | Fragmentación reconstruida / publicada — Claude | Fragmentación reconstruida / publicada — GPT | Sobreagregación reconstruida / publicada (ambos) |
|---|---|---|---|
| H0001 Dominga | **8/8** vs 0/8 | **8/8** vs 0/8 | 0/8 vs 0/8 |
| H0002 Ventanas | **8/8** vs 0/8 | **8/8** vs 0/8 | 0/8 vs 0/8 |
| H0004 Bocamina | **8/8** vs 0/8 | **2/8** vs 0/8 | Claude 3/8, GPT 4/8 (idénticas a lo publicado) |
| **Total** | **24/24** vs 0/24 | **18/24** vs 0/24 | Claude 3/24, GPT 4/24 (idénticas) |

**[INF] Tres conclusiones:**

1. La etiqueta `fragmentacion_falsa` no se emitió **ni una sola vez** en 104 respuestas (52 pares × 2 modelos), pese a que la reconstrucción indica 24 y 18 casos respectivamente. El instrumento no la detectaba.
2. En cambio, `sobreagregacion` reconstruida **coincide exactamente** con la publicada en ambos modelos (3/3 y 4/4). Ese lado del instrumento sí funcionaba.
3. La divergencia entre modelos se concentra **enteramente en Bocamina** (Claude 8/8, GPT 2/8); en Dominga y Ventanas coinciden perfectamente (8/8 ambos). Es un desacuerdo sustantivo localizado, no ruido difuso.

### 4.3 Por qué falló: la asimetría explicada

**[INF]** Detectar **sobreagregación** no requiere conocer el mecanismo del sistema: si dos documentos comparten nombre de instalación pero narran expedientes distintos, el adjudicador lo ve en el texto. La pregunta "¿son el mismo proceso?" y la pregunta "¿un sistema que agrupe por nombre los uniría mal?" coinciden.

Detectar **fragmentación falsa** exige lo contrario: sospechar que dos documentos que usan **nombres distintos** ("Dominga" / "Minera Dominga") fueron tratados como proyectos distintos por un sistema que agrupa por coincidencia literal de cadena. Eso es una inferencia sobre el mecanismo interno, no sobre el texto — **y el codebook nunca le dijo al adjudicador que el mecanismo real era coincidencia de cadena**. Sin ese dato, no había forma de saber que debía sospechar fragmentación precisamente ahí.

El defecto de raíz es que el Nivel B fusiona dos preguntas distintas bajo un solo nombre: una normativa-contrafáctica ("¿sería razonable agruparlos?", respondible a ciegas) y una de verificación ("¿coincide lo que el sistema hizo con mi juicio?", **imposible** de responder sin la clave). Ambos modelos, independientemente, respondieron la primera y la reportaron con el nombre de la segunda.

### 4.4 Advertencia crítica: la tasa reconstruida NO es una tasa poblacional

**[CD]** El estrato `inter_subhilo` se muestreó **exclusivamente sobre pares unidos por una arista del grafo**. Cobertura real respecto del universo de pares cross-subhilo:

| Macrohilo | Pares cross-subhilo posibles | Con arista (universo muestreado) | % del universo |
|---|---:|---:|---:|
| H0001 Dominga | 5.398 | 22 | **0,41 %** |
| H0002 Ventanas | 4.352 | 86 | **1,98 %** |
| H0004 Bocamina | 3.453 | 57 | **1,65 %** |

**[INF]** Los pares cross-subhilo conectados por arista son, por construcción, los **semánticamente más similares** — es decir, precisamente los más propensos a ser el mismo proceso. La cifra "24/24 fragmentación" describe el 0,4–2 % más favorable del universo.

**[DT] Precisión sobre el estatus de esa cifra.** No debe llamarse "cota superior" sin más: eso sugiere un límite demostrado. Es una **tasa condicionada a una submuestra de alta similitud**. Que sea además una cota superior de la tasa poblacional requiere asumir que P(mismo proceso | similitud) es monótona creciente —plausible, pero es un supuesto, no un teorema—. La formulación admisible es: *entre los pares cross-subhilo más similares, la fragmentación es de 24/24 (Claude) y 18/24 (GPT); la tasa poblacional no está estimada.*

### 4.5 Abstención: el problema es la unidad, y el arreglo es pequeño

**[CD]** Los 4 pares del estrato de abstención involucran exactamente **4 documentos abstenidos distintos** (`2938`, `3134`, `3237`, `6832`; el `6832` aparece dos veces) — y esos 4 son **el universo completo** de documentos abstenidos en H0002 (4/4, cobertura 100 %).

**[INF]** El problema no es de cobertura muestral, sino de **unidad de la pregunta**: la abstención de HEBRA v3 es una propiedad **por documento**, pero el instrumento solo preguntó por pares. La consecuencia es visible en `V3B017`, donde **ambos** documentos abstuvieron: Claude respondió `mismo_proceso_especifico` / `asignacion_correcta` sin mencionar la abstención, aunque por su propio juicio ambas abstenciones deberían haberse marcado incorrectas; GPT, para el mismo par, respondió `mismo_macroproceso` / `abstencion_correcta`.

**[REC]** Evaluar la abstención requiere juzgar **4 documentos**, no re-adjudicar 52 pares. Es la corrección de menor costo de todo este informe.

### 4.6 Procedimiento corregido propuesto

**[REC]** Tres cambios, ninguno de los cuales exige re-adjudicar los 52 pares:

1. **Separar las dos preguntas.** El adjudicador ciego responde solo **identidad sustantiva** (el actual Nivel A) más una pregunta puramente textual: *"¿hay indicios en el texto de que estos documentos nombren el mismo objeto de formas distintas, o de que compartan nombre sin ser el mismo expediente?"*. Ambas son respondibles sin la clave.
2. **Derivar el diagnóstico después.** `asignacion_correcta` / `fragmentacion_falsa` / `sobreagregacion` se calcula en la fase de integración cruzando ese juicio con el comportamiento real del sistema — exactamente el cruce determinista de §4.1. **Nunca debe pedírsele al adjudicador ciego.**
3. **Cambiar la unidad de la abstención.** Preguntar, por cada documento por separado: *"¿este texto, por sí solo, permite identificar un proyecto/instalación/expediente concreto?"*.

**[REC] Cuarto cambio, sobre el muestreo (§4.4):** para obtener una tasa de fragmentación interpretable, el estrato `inter_subhilo` debe incluir pares cross-subhilo **no condicionados a la existencia de arista**.

---

## 5. Ontología procesual operacional

**[DT]** Toda esta sección es una propuesta conceptual. Cada concepto lleva una **regla provisional falsable**: una condición que, de no cumplirse en los datos, obligaría a revisar la definición.

### 5.1 Los once conceptos

| Concepto | Definición | Unidad de análisis | Evidencia de UNIÓN | Evidencia de SEPARACIÓN | Caso limítrofe observado | Regla provisional falsable |
|---|---|---|---|---|---|---|
| **Documento** | Una pieza de prensa fechada, con fuente y texto | El registro | — (es el átomo) | — | `V3B007`: mismo artículo con dos fechas de captura; `PAIR-0002`: "duplicado sustantivo del mismo evento y texto" | Dos registros con texto casi idéntico y misma fecha nominal son **un** documento observado dos veces, no dos observaciones independientes |
| **Episodio** | Un acto discreto y fechado: una votación, un fallo, una toma, un anuncio | Conjunto de documentos que reportan el mismo acto | Mismo acto nombrado + ventana temporal corta + mismos actores centrales | Actos distintos aunque emanen del mismo órgano | Anuncio del cierre de Ventanas (17-18 jun 2022) y la reacción sindical del mismo día | Si un documento se refiere al otro acto como ocurrido "ayer/hoy", ambos pertenecen al mismo episodio |
| **Proceso específico** | Secuencia de episodios ligados por un mismo objeto administrativo-jurídico rastreable (un proyecto y su RCA, un contrato, una consulta, un expediente) | El expediente u objeto | Continuidad del mismo expediente: misma causa, misma RCA, mismo contrato nombrado | Expedientes distintos aunque compartan empresa y territorio | Bocamina I vs. Bocamina II | **Si el desenlace de A modifica el estado jurídico de B, son el mismo proceso específico** |
| **Macroproceso** | Política sectorial o complejo industrial que articula varios procesos específicos | El instrumento de política o el complejo | Los procesos comparten un instrumento nombrado, un titular institucional o un régimen regulatorio, y algún documento los invoca conjuntamente | No hay instrumento común, solo tema compartido | T0009 / T0006 (ENL vs. acuerdo Codelco-SQM) | **Existe al menos un documento que trata ambos procesos específicos como partes del mismo instrumento nombrado** |
| **Campo temático** | Dominio de política pública al que pertenece el corpus | El corpus | Pertenencia al mismo dominio | Dominios distintos | ¿Litio es "transición energética" o "minería extractiva"? | No sirve para identidad; solo para definir el marco muestral. Si se usa para agrupar, produce agregaciones sin objeto (ver T0092) |
| **Relación temática** | Dos unidades comparten campo pero no macroproceso identificable | Par de unidades | Vocabulario o sector compartido | Ningún instrumento, actor central ni territorio común | `V3B016`: estudio académico sobre Quintero-Puchuncaví vs. columna sobre el cierre de Ventanas | Si no puede nombrarse el instrumento o el complejo que comparten, es relación temática, no macroproceso |
| **Continuidad** | Propiedad de un proceso: cadena de episodios donde cada uno es consecuencia jurídica o práctica del anterior | El proceso | Encadenamiento explícito en el texto ("tras el fallo…", "en cumplimiento de…") | Salto temporal sin referencia al episodio previo | T0092 abarca 13,6 años | **La cadena debe sobrevivir al retirar los enlaces que solo se sostienen en similitud semántica: si el proceso se desconecta, la continuidad era artefactual** |
| **Reactivación** | Un proceso vuelve a producir episodios tras un intervalo sin ellos, sobre el mismo objeto | El proceso | El nuevo episodio invoca el expediente antiguo por su identificador | Es un objeto nuevo que solo se parece | Dominga: rechazo 2017 → 2021 → rechazo 2023 → revocación 2024 → 2025 | Hay reactivación si el documento nuevo **cita el acto administrativo anterior**; no basta que trate el mismo tema |
| **Latencia** | Intervalo sin episodios dentro de un proceso que después se reactiva | Intervalo temporal | Ausencia de documentos + reactivación posterior **verificada** | — | Dominga 2018-2020 | **La latencia es una categoría retrospectiva**: *ex ante* es indistinguible del cierre. Un sistema que declare latencia en tiempo real está afirmando lo que no puede observar |
| **Cierre** | Acto firme que agota el objeto del proceso | El expediente | Resolución final sin recurso pendiente | Siguen apareciendo episodios que invocan el mismo expediente | Ventanas "cerró" el 31 may 2023, pero siguieron episodios de fiscalización del cierre | **Si tras el acto siguen apareciendo episodios que invocan el mismo expediente, no hubo cierre sino cambio de fase** |
| **Abstención** | El sistema declara que un documento no permite anclar un proceso específico | **El documento** (nunca el par) | — | — | Documentos `2938`, `3134`, `3237`, `6832` en H0002 | La abstención es correcta si **dos lectores independientes que leen solo ese documento no pueden nombrar el mismo objeto** |

### 5.1.b CORRECCIÓN — "proceso específico" no puede reducirse al expediente

**[DT]** La definición de §5.1 ata "proceso específico" a un **objeto administrativo-jurídico rastreable** (un expediente, una RCA, un contrato). Esa definición es operativa pero **sociológicamente insuficiente**: un conflicto social puede conservar su identidad aunque cambie el expediente, se abran varias causas judiciales en paralelo, se sustituyan los instrumentos administrativos o se transforme el objeto de la demanda. Aplicada sin corrección, fragmentaría artificialmente una controversia prolongada en tantas unidades como expedientes genere.

**[DT] Corrección: el nivel intermedio requiere dos tipos de identidad, no uno.**

| Tipo | Definición | Criterio de unión | Ejemplo donde diverge del otro tipo |
|---|---|---|---|
| **Identidad institucional** (expediente) | Continuidad de un mismo objeto administrativo-jurídico | Mismo expediente, RCA, contrato o causa | El vertedero de cenizas de Bocamina y el cierre de la unidad I son **expedientes distintos** |
| **Identidad contenciosa** (conflicto social) | Continuidad de una misma disputa entre las mismas partes sobre el mismo bien en disputa, aunque cambie el vehículo institucional | Persisten actores, territorio y objeto de la demanda; los actores tratan los episodios como una misma lucha | Ambos son **el mismo conflicto** entre la comunidad de Coronel y Enel por el pasivo ambiental |

**[INF]** Estos dos tipos **no coinciden**, y esa no-coincidencia explica buena parte de los desacuerdos observados: Dominga tiene una identidad contenciosa clara y una identidad institucional fragmentada en múltiples causas (Comité de Ministros, Tribunal Ambiental, Corte Suprema, Tribunal Constitucional); Bocamina tiene una identidad contenciosa unificada (comunidad vs. Enel) y al menos cinco identidades institucionales.

**[REC]** Un modelo que solo represente una de las dos fallará sistemáticamente en la otra dirección. La regla falsable de §5.1 ("si el desenlace de A modifica el estado jurídico de B") es un criterio de **identidad institucional**; falta su equivalente para la identidad contenciosa. Propuesta provisional: *hay identidad contenciosa si los mismos actores invocan el episodio anterior como parte de su propia lucha, aunque el vehículo institucional sea otro.*

### 5.2 Aplicación a los seis casos

**[CD]** Cómo particiona cada sistema los mismos documentos:

| Caso | HEBRA v3 | FTD-Core v1 | Lectura ontológica |
|---|---|---|---|
| **Dominga** | 162 docs → **5 subhilos**, 0 abstenciones | 136 docs con mención → **11 trayectorias** (T0089:66, T0207:37) | **Un** proceso específico con ≥2 reactivaciones. **Ambos** sistemas lo fragmentan, y por líneas distintas |
| **Bocamina I y II** | 87 docs → **23 subhilos** | 151 docs con mención → **1 trayectoria dominante** (T0092:146) | Un macroproceso (complejo Enel-Coronel) con ≥5 procesos específicos: cierre unidad I, cierre unidad II, expediente del vertedero, demanda laboral por asbesto, causa penal por vertimiento marino. HEBRA **sobre-fragmenta**, FTD **sobre-agrega** |
| **Ventanas** | 148 docs → **16 subhilos** + 4 abstenciones | 303 docs con mención → **13 trayectorias** (T0115:164) | Macroproceso = complejo Quintero-Puchuncaví-Ventanas; procesos específicos = cierre de la Fundición Codelco (Ley 21.546), crisis de intoxicaciones, termoeléctrica Ventanas II de AES Andes (**otra empresa**) |
| **T0092** | — | 203 docs, 2012→2026 | **No es un proceso específico ni un macroproceso: es una agregación de campo temático.** 165 docs de Bocamina/Coronel, 27 de Ventanas/Puchuncaví (otro complejo), 26 sin ninguno de los dos (Tarapacá, Mejillones, Arauco, Chiloé) |
| **T0009 / T0006** | — | 149 y 140 docs | La frontera **no es ontológicamente interpretable**: ambas mezclan Maricunga y Atacama en proporción casi idéntica (35,6 % y 36,4 %), y los tres casos de fragmentación citados por el propio reporte de FTD cruzan esta única frontera |
| **Gobernanza nacional del litio (H0000)** | 170 docs → **44 subhilos** + 12 abstenciones (v3); 9 subhilos (v2, con diccionario manual) | repartido al menos entre T0009, T0006 y T0017 | Macroproceso ENL con varios procesos específicos. v3 sobre-fragmenta masivamente respecto de la ontología |

### 5.3 La prueba más fuerte: las dos particiones no se parecen

**[CD]** Comparación descriptiva entre la partición de subhilos de HEBRA v3 y la de trayectorias de FTD, sobre los documentos que **ambos** sistemas asignan:

| Caso | Docs en común | Subhilos HEBRA | Trayectorias FTD | ARI | NMI |
|---|---:|---:|---:|---:|---:|
| Dominga | 122 | 5 | 9 | **0,024** | 0,110 |
| Ventanas | 139 | 16 | 5 | **0,141** | 0,209 |
| Bocamina | 81 | 23 | 1 | **0,000** | 0,000 |

**[INF]** Las dos particiones muestran **muy bajo acuerdo plano**. **[DT] No debe decirse que son "independientes"**: un ARI cercano a cero significa ausencia de acuerdo por encima del azar *bajo esta representación de particiones*, no independencia estadística entre los sistemas ni entre las señales que usan. Matices obligatorios: el ARI penaliza fuertemente la discrepancia de granularidad, de modo que un ARI≈0 refleja sobre todo desacuerdo de **escala**; y el 0,000 de Bocamina es **degenerado** (FTD tiene una sola clase, así que la información mutua es cero por definición, no por desacuerdo de contenido). El caso informativo es **Dominga**: NMI = 0,11 con ambos sistemas fragmentando el mismo proceso por líneas diferentes.

---

## 6. Decisiones cerradas

1. **[CD]** El Nivel B de HEBRA v3, tal como se administró, es incapaz de detectar fragmentación falsa. Ninguna cifra de fragmentación derivada de él es publicable.
2. **[CD]** La reconstrucción determinista del Nivel B es válida para 48 de 52 pares y se documenta en §4.1–4.2.
3. **[CD]** El estrato `inter_subhilo` cubre 0,4–2 % del universo de pares cross-subhilo, y precisamente el extremo más similar. Cualquier tasa derivada es una cota superior condicionada.
4. **[CD]** La evaluación de abstención de HEBRA requiere 4 juicios por documento, no 52 por par; los 4 documentos del universo están ya en la muestra.
5. **[CD]** T0092 contiene ~13 % de documentos de un complejo industrial distinto y ~13 % sin relación con ninguno de los dos.
6. **[CD]** Las particiones de HEBRA y FTD sobre los mismos documentos son mutuamente casi independientes (ARI 0,00–0,14).
7. **[EV]** Los tres hashes declarados por FTD (muestra ciega, clave, primera adjudicación) se verificaron y coinciden. La copia publicada en GitHub difiere solo en fines de línea.
8. **[INF]** El agente principal está contaminado para adjudicar FTD y no puede actuar como segundo adjudicador (§1.1).
9. **[CD]** FTD ya tiene control inter-evaluador: κ = 0,477 sobre 60 pares, acuerdo bruto 75 %. **[DT] No es comparable con el κ = 0,246 de HEBRA v3**: distinto codebook, distinto número de categorías, distinta muestra, distintos adjudicadores y 1.000 vs. 6.000 caracteres de material. La formulación admisible es "FTD obtuvo κ = 0,477 en su instrumento y HEBRA κ = 0,246 en el suyo", no que uno tenga mayor confiabilidad que el otro.
10. **[CD]** La sobreabstención de FTD queda **replicada** por un segundo adjudicador aislado y empeora: 75 % (v1) → 90 % (v2). **[DT] Con dos supuestos declarados**: que un juicio por pares implique que la abstención del documento individual fue incorrecta, y que 1.000 caracteres basten. Por coherencia con el argumento que este mismo informe hace para HEBRA (§4.5), **la abstención de FTD también debería evaluarse por documento**. Es una señal replicada de posible sobreabstención, no una medición cerrada.
11. **[RETIRADA]** La afirmación "13 de los 15 desacuerdos son de escala y ninguno es error de adjudicador" **se retira por circular** (§3.4.1). Lo que sí se sostiene es que el codebook de 4 categorías de FTD no puede expresar la distinción macroproceso/proceso específico: 23 de los 46 `mismo_proceso` del adjudicador 2 bajan a `mismo_macroproceso` en la escala fina.
12. **[EV]** `PAIR-0004` de la muestra ciega de FTD tiene **ambos cuerpos de texto vacíos** (0 caracteres), aunque **sus dos titulares sí existen y son sustantivos** ("Comunidades mapuche-williche impugnan recomendación del SEA…" / "Comunidades mapuche anuncian acciones judiciales tras aprobación del Parque Eólico Ovejera Sur en La Unión"). **[INF]** El fallo de control de calidad no es que se emitiera un veredicto —era adjudicable desde los titulares— sino que **el instrumento no distingue una adjudicación con texto completo de una hecha solo con titular**.
13. **[CD]** En ambos sistemas, el acuerdo inter-adjudicador colapsa en el **mismo lugar**: la frontera entre unidades (FTD `boundary` 50 %; HEBRA Bocamina 37,5 % en Nivel A).

## 7. Decisiones provisionales

1. **[DT]** La regla de mapeo entre la escala de 5 categorías y la de 4 de FTD (particularmente `mismo_macroproceso` → `relacionado`) es defendible a partir de la definición literal de FTD, pero es una decisión teórica. Por eso se pidió al subagente **ambas escalas de forma independiente**, y el kappa se calcula sobre la escala original de 4.
2. **[DT]** La ontología de §5 es una propuesta. Su punto más discutible es el estatus de Bocamina I y II como procesos específicos distintos dentro de un macroproceso común.
3. **[DT]** La regla falsable de continuidad (§5.1) exige que la cadena sobreviva al retiro de los enlaces meramente semánticos. El umbral de qué cuenta como "meramente semántico" no está fijado.
4. **[INF]** La interpretación de T0009/T0006 como "macroproceso vs. proceso específico" es **una** lectura posible; la otra es que sea fragmentación espuria. La evidencia disponible no discrimina entre ambas.

## 8. Qué evidencia existe realmente sobre complementariedad

**No está demostrada.** Lo que existe:

- **[CD] A favor:** en Bocamina los dos sistemas fallan en direcciones **opuestas** (HEBRA 23 subhilos para 87 docs; FTD 1 trayectoria para 146 docs). Errores anti-correlacionados son la condición **necesaria** de la complementariedad.
- **[CD] En contra:** en Dominga **ambos** fragmentan el mismo proceso único (5 y 9 unidades respectivamente), o sea que ahí los errores son del **mismo signo**, no complementarios.
- **[CD] En contra:** ARI 0,00–0,14 indica que no hay validación convergente: no se están confirmando mutuamente en ningún caso.
- **[INF] Decisivo:** que dos sistemas se equivoquen en direcciones opuestas **no implica** que combinarlos recupere la unidad correcta. Es igualmente compatible con que **ninguno de los dos tenga la unidad de análisis adecuada**, que es lo que sugiere la aplicación de la ontología de §5.2.
- **[EV]** El propio dossier de FTD (§15.4) fija la condición correcta —evaluación en un holdout que ninguno usó para ajustar, superando a ambos por separado— y esa evaluación **no existe**.

- **[CD] Nuevo, tras la Fase 3:** el acuerdo inter-adjudicador de **ambos** sistemas colapsa en el mismo punto estructural: la frontera entre unidades (FTD `boundary` 50 %; HEBRA Bocamina 37,5 %). **[INF]** Es un hallazgo convergente sobre la *dificultad del objeto*: ambos tropiezan con la misma distinción no resuelta entre macroproceso y proceso específico.

**Conclusión [INF]:** la complementariedad es hoy una **hipótesis con evidencia mixta**, no un hecho. Afirmarla en una publicación sería injustificado con los artefactos actuales.

**[DT] Precisión sobre lo que NO se puede concluir.** Una versión anterior de este informe sostuvo que "combinarlos heredaría el problema en vez de cancelarlo". **Eso va más allá de la evidencia y se retira como afirmación.** Es una hipótesis plausible, no una consecuencia de los resultados: una arquitectura jerárquica que representara explícitamente macroproceso, proceso específico y episodio podría, en principio, resolver precisamente la distinción con la que ambos tropiezan. Determinarlo exige el experimento de combinación en holdout que el propio dossier de FTD (§15.4) especifica y que no existe. Lo que sí se sostiene: **ambos sistemas comparten una carencia ontológica —ninguno representa el nivel intermedio— y esa carencia, no la elección entre ellos, es el problema a resolver.**

## 9. Problemas que aún requieren revisión de GPT

Solo se listan puntos donde **la evidencia disponible no decide** y dos revisores competentes podrían discrepar de buena fe.

**P1 — ¿Bocamina I y Bocamina II son el mismo proceso específico o dos procesos específicos del mismo macroproceso?**
Es el locus exacto de la divergencia entre adjudicadores: Claude reconstruye 8/8 fragmentaciones en H0004, GPT solo 2/8, mientras en Dominga y Ventanas coinciden 8/8. El criterio implícito de Claude es continuidad de actor y sitio (Enel-Coronel); el de GPT, continuidad de expediente. La regla falsable propuesta en §5.1 ("si el desenlace de A modifica el estado jurídico de B") no ha sido aplicada a los expedientes reales. **De esta respuesta depende la tasa de fragmentación de HEBRA en un tercio de la muestra.**

**P2 — ¿La frontera T0009/T0006 es una separación macroproceso/proceso-específico legítima o fragmentación espuria?**
En contra de que sea territorial: ambas mezclan Maricunga y Atacama en proporción casi idéntica (35,6 % y 36,4 %). A favor de que sea legítima: sus vocabularios dominantes son distinguibles (consulta indígena vs. contrato Codelco-SQM). En contra: los tres únicos casos de fragmentación citados por el propio reporte de FTD cruzan esta única frontera.

**P3 — ¿Es admisible el mapeo `mismo_macroproceso` → `relacionado` para calcular kappa entre las dos escalas?**
Se deriva de la definición literal de FTD (`relacionado` = "mismo territorio, política o campo, pero identidad procesual insuficiente"), pero fusiona una distinción que la escala fina separa. Por eso se pidieron ambas escalas de forma independiente; queda por decidir cuál debe reportarse como resultado principal.

**P4 — ¿La reconstrucción determinista del Nivel B (§4.1) es una medición válida o solo un diagnóstico de fallo del instrumento?**
A favor de "medición válida": combina un juicio emitido a ciegas con la clave sellada, que es el protocolo estándar de desciegue. En contra: la regla de mapeo la fijó el agente principal **después** de observar el patrón de fallo, aunque se derive de definiciones que preceden a los datos. Un revisor estricto podría exigir que la regla se hubiese preinscrito.

**P5 — ¿ARI ≈ 0 entre HEBRA y FTD es evidencia contra la complementariedad, o solo un artefacto de granularidad?**
El ARI penaliza fuertemente la discrepancia de escala, y el 0,000 de Bocamina es degenerado (FTD tiene una sola clase). El caso limpio es Dominga (NMI = 0,11 con ambos fragmentando). Queda por decidir si existe alguna métrica de acuerdo entre particiones de granularidad muy distinta que sea informativa aquí.

**P6 — ¿Invalida la comparación entre sistemas que las hojas ciegas ofrezcan 1.000 caracteres (FTD) frente a 6.000 (HEBRA)?**
Cualquier diferencia observada en calidad de adjudicación entre ambos ejercicios está confundida con esta diferencia de material. Queda por decidir si las métricas de FTD y HEBRA pueden compararse en absoluto sin re-adjudicar con material equiparado.

**P7 — ¿Debe un sistema poder declarar latencia en tiempo real, o es la latencia necesariamente retrospectiva?**
La regla propuesta en §5.1 sostiene que *ex ante* la latencia es indistinguible del cierre, y que declararla en línea es afirmar lo inobservable. Un revisor podría sostener que una probabilidad de reactivación estimada es una declaración legítima. La respuesta determina si "latencia" puede ser una salida del modelo o solo una etiqueta de análisis posterior.

## 10. Cambios que podrían implementarse después — **sin implementarlos ahora**

Ninguno de estos se ejecuta en este informe. Se listan con su justificación empírica.

| # | Cambio | Justificado por |
|---|---|---|
| C1 | Reescribir el Nivel B: adjudicador ciego responde solo identidad + indicios textuales; el diagnóstico se deriva en integración | §4.3 — el instrumento actual no puede detectar fragmentación |
| C2 | Cambiar la unidad de la pregunta de abstención de par a documento | §4.5 — `V3B017` es inevaluable con la unidad actual |
| C3 | Añadir al estrato `inter_subhilo` pares no condicionados a la existencia de arista | §4.4 — cobertura actual de 0,4–2 % del universo |
| C4 | Documentar en el paquete de FTD la diferencia CRLF entre la copia canónica y la publicada | §1.3 — un revisor externo podría concluir que la muestra fue alterada |
| C5 | Suprimir `source_id`/`target_id` de toda hoja ciega futura | §1.3 — vector de fuga vía `assignments.csv` publicado |
| C6 | Aplicar la regla falsable de continuidad (§5.1) a T0092 antes de describirla como trayectoria de 14 años | §5.2 — T0092 mezcla dos complejos y un 13 % ajeno |
| C7 | Igualar la longitud de texto de las hojas ciegas de ambos sistemas (1.000 vs 6.000 caracteres) antes de comparar calidad de adjudicación | §1.3 — la comparación actual está confundida por el material |
| C8 | Evaluar la abstención de FTD **por documento**, no por pares, igual que se propone para HEBRA | §6.10 — inconsistencia interna del informe detectada en revisión externa |
| C9 | Marcar en el instrumento de FTD qué pares se adjudicaron con texto completo y cuáles solo con titular | §6.12 — `PAIR-0004` era adjudicable, pero el instrumento no lo distingue |
| C10 | Incorporar la distinción identidad institucional / identidad contenciosa a la ontología | §5.1.b — la definición actual fragmentaría artificialmente conflictos prolongados |

---

## 11. Registro de correcciones tras revisión externa (2026-07-24)

Una revisión externa independiente (GPT) examinó el commit `6dc2474` y señaló sobreafirmaciones. Se aceptaron y aplicaron las siguientes correcciones. **Se registran en lugar de editarse en silencio** para que la trazabilidad del proceso quede visible.

| # | Afirmación original | Estado | Corrección aplicada |
|---|---|---|---|
| R1 | "13 de 15 desacuerdos son de escala; ninguno es error de adjudicador" | **RETIRADA** | Era circular: usaba la auto-bandera del propio adjudicador 2 como si fuera clasificación independiente, y el orden de las reglas impedía por construcción que saliera "error de adjudicador". Se sometieron los 15 a arbitraje ciego por un tercer adjudicador (§3.4.1–3.4.2) |
| R2 | "FTD tiene mejor confiabilidad inter-evaluador que HEBRA" (κ 0,477 > 0,246) | **RETIRADA** | Kappas no comparables: distinto codebook, categorías, muestra, adjudicadores y material (1.000 vs 6.000 caracteres) |
| R3 | "Las particiones son esencialmente independientes" | **REFORMULADA** | ARI≈0 indica ausencia de acuerdo sobre el azar bajo esa representación, no independencia estadística. Ahora: "muy bajo acuerdo plano, en parte por diferencias extremas de granularidad" |
| R4 | "Combinarlos heredaría el problema en vez de cancelarlo" | **RETIRADA** | Hipótesis, no consecuencia de los resultados. Requiere el experimento de combinación en holdout |
| R5 | "Cota superior condicionada" (fragmentación de HEBRA) | **REFORMULADA** | Es una tasa condicionada a alta similitud; que además sea cota superior exige asumir monotonía de P(mismo proceso \| similitud) |
| R6 | Sobreabstención de FTD = 90 % | **CONDICIONADA** | Señal replicada, no medición cerrada: depende de que un juicio por pares implique abstención documental incorrecta y de que 1.000 caracteres basten. Debe evaluarse por documento (C8) |
| R7 | `PAIR-0004` no podía adjudicarse | **CORREGIDA** | Los cuerpos están vacíos pero **los titulares existen y son sustantivos**; era adjudicable desde titulares. El fallo real es que el instrumento no distingue ambos casos |
| R8 | "Segunda adjudicación independiente" | **RENOMBRADA** | "Segunda adjudicación ciega por un subagente aislado de Claude"; sigue siendo acuerdo IA–IA (§2.1.b) |
| R9 | Ontología: "proceso específico" = expediente | **AMPLIADA** | Se añade la distinción identidad institucional / identidad contenciosa (§5.1.b) |

**[INF] Qué sobrevive intacto a la revisión externa:** la contaminación del agente principal y su detección; el vector de fuga por identificadores documentales; el sellado con hash previo al desciegue; κ = 0,477 y acuerdo bruto 75 % como cifras de este instrumento; la caída del acuerdo a 50 % en `boundary`; la señal replicada de sobreabstención; el fallo estructural del Nivel B de HEBRA y su reconstrucción como diagnóstico; el muestreo condicionado del estrato `inter_subhilo`; y que la complementariedad no está demostrada.
