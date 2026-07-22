# Propuesta independiente Fable5 — HEBRA: Hilos de disputa Estables Basados en Referentes Anclados

Fecha: 2026-07-22
Autor: Claude (Fable 5), rol investigador metodológico FARO independiente.
Estado FARO: **Exploratorio** (propuesta preinscrita; nada implementado ni ejecutado).

## Declaración de aislamiento

No se leyó, abrió, buscó ni resumió:

1. `09_metodologia/faro_model_research/FTD_DOSSIER_AUDITABLE_2026_07_22.md`
2. `docs/superpowers/specs/2026-07-22-faro-trajectory-discovery-design.md`
3. Los commits `e01b6da` y `a05be3d` ni sus diffs.
4. Ningún documento que describa la propuesta competidora.

El listado de `09_metodologia/faro_model_research/` se filtró con `grep -v` para
excluir el dossier antes de mostrarlo. No se usaron subagentes.

---

## 1. Fuentes y rutas leídas

Todas relativas a `D:/Analisis conflictos/01_proyecto_universidad`. Hashes
SHA-256 truncados a 16 hex.

| Ruta | Hash (16) | Uso |
|---|---|---|
| `START_HERE.md`, `AGENTS.md`, `FARO.md` | — | protocolo |
| `memory-bank/current-handoff.md` | — | estado puente |
| `config/project_paths.yaml` | — | rutas canónicas |
| `config/artifact_contracts.yaml` | — | contratos vigentes |
| `repo_index/artifact_map.yaml` | — | inventario |
| `repo_index/pipeline_dag.yaml` | — | DAG y puertas |
| `09_metodologia/faro_model_research/MODEL_BENCHMARK_FINAL.md` | `85550efaff3d3217` | veredicto modelos |
| `09_metodologia/faro_model_research/EXTERNAL_GPU_BENCHMARK_ANALYSIS.md` | `ced6736d22a4dd6b` | benchmark GPU |
| `09_metodologia/faro_model_research/CONTINUAR_AQUI.md` | — | programa |
| `09_metodologia/faro_model_research/RESEARCH_FRONTIER_ROLLINGBERT_OTVMF.md` | — | frontera previa |
| `09_metodologia/faro_model_research/omegaevolve/FINAL_REPORT.md` | `1ad1786a2ede6e95` | OmegaEvolve-S |
| `09_metodologia/faro_model_research/benchmark_corpus_contract.json` | `6b146227bbf8d07a` | contrato corpus 3.742 |
| `09_metodologia/faro_model_research/otvmf_finalist_stability.json` | `2be986d64e4ec426` | estabilidad OTVMF |
| `09_metodologia/faro_model_research/bertopic_natural_multiseed_evaluation.json` | — | backbone multisemilla |
| `09_metodologia/faro_model_research/omegaevolve/cobweb_evaluation.json` | `6e1ae3035fe4ddc9` | CobwebTM |
| `05_modelos_topicos/12_evaluacion_formal_modelos/formal_evaluation_report.md` | — | evaluación legacy (7.372 docs, **no comparable**) |
| `01_bases_de_datos/.../06_base_actual_fusionada_3742_incluidas.csv` | `1caf340dfd44622d` | corpus activo (hash registrado, no abierto en pesado) |
| `01_bases_de_datos/.../07_auditoria_y_base_candidata_qwen_2026_06_22.xlsx` | `61d2d01d30f9a92d` | base candidata 3.909 (hash registrado; contenido auditado vía `artifact_map.yaml`, no promovida) |

Contrato de corpus verificado: 3.742 documentos, embeddings 1024-d, 3.725
fechas de publicación válidas, 17 faltantes, columna `fecha_iso`, orden de IDs
congelado.

---

## 2. Literatura reciente (últimos 12 meses)

Separación explícita: **[R]** revisado por pares / actas oficiales; **[P]** preprint.

| Fuente | Tipo | Relevancia |
|---|---|---|
| [Evaluating Dynamic Topic Models (James et al., ACL 2024)](https://aclanthology.org/2024.acl-long.11/) | [R] | ya en bibliografía local; calidad local + consistencia temporal deben medirse juntas |
| [Continual Neural Topic Model (CoNTM)](https://arxiv.org/pdf/2508.15612) | [P→R] (EACL 2026 según bibliografía local) | continual learning de tópicos; confirma que la identidad temporal es el problema abierto |
| [CobwebTM: Probabilistic Concept Formation for Lifelong Topic Modeling](https://arxiv.org/pdf/2604.14489) | [P] | ya evaluado localmente y rechazado (ARI 0,222) |
| [Dynamic Topic Evolution with Temporal Decay and Attention in LLMs](https://arxiv.org/abs/2510.10613) | [P] | decaimiento temporal sobre embeddings LLM; mecanismo, no unidad de proceso |
| [LLM Reading Tea Leaves: Automatically Evaluating Topic Models with LLMs (TACL 2025)](https://direct.mit.edu/tacl/article/doi/10.1162/tacl_a_00744/128942/) | [R] | WALM: evaluación LLM alineada con juicio humano; útil como métrica complementaria, no gold |
| [Toward Purpose-oriented Topic Model Evaluation enabled by LLMs](https://arxiv.org/abs/2509.07142) | [P] | 9 métricas LLM en 4 dimensiones; detecta redundancia y drift semántico |
| [Bridging the Evaluation Gap: LLMs for Topic Model Evaluation](https://arxiv.org/abs/2502.07352) | [P] | evaluación LLM de coherencia/diversidad/alineación |
| [Mapping News Narratives Using LLMs and Narrative-Structured Text Embeddings (ACM WebSci 2025)](https://dl.acm.org/doi/10.1145/3717867.3717868) | [R] | representación sensible a actantes + estructura narrativa; la evidencia más cercana a la unidad que propongo |
| [Synergizing Unsupervised Episode Detection with LLMs for Large-Scale News Events](https://arxiv.org/pdf/2408.04873) | [P→R] | "episodios" como unidad intermedia entre tópico y evento |
| [Disaster Storylines and KGs from Global News with LLMs y RAG (Scientific Data 2026)](https://www.nature.com/articles/s41597-026-07036-2) | [R] | storylines por evento-desastre; identidad definida por el referente del evento, no por partición |
| [S2WTM: Spherical Sliced-Wasserstein Autoencoder for Topic Modeling](https://arxiv.org/pdf/2507.12451) | [P] | geometría esférica; ruta ya explorada localmente vía OTVMF, no repetir |
| [Streaming Continual Learning, ESANN 2025 special session](https://www.esann.org/proceedings/2025) | [R] | ARI entre lotes y Topic Centroid Drift como métricas de estabilidad temporal estándar |

**Chequeo contra bibliografía local:** BERTrend, ANTM, CFDTM, D-ETM, FASTopic,
Evaluating-DTM y CobwebTM ya están registrados en
`RESEARCH_FRONTIER_ROLLINGBERT_OTVMF.md` y `omegaevolve/FINAL_REPORT.md`. Lo
nuevo de los últimos 12 meses converge en dos puntos que la investigación local
todavía no incorpora: (a) la identidad temporal anclada en **referentes del
mundo** (actantes, eventos, lugares) en vez de en la partición del modelo
(WebSci 2025, Disaster Storylines, Episode Detection); (b) evaluación LLM
estructurada como capa provisional auditable (WALM, purpose-oriented), que
encaja con la figura FARO `expert_review_provisional_ai`.

Filtro de adopción (problema → evidencia local → costo):

1. *Narrative-structured embeddings*: resuelve identidad trans-partición; el
   problema existe (ver §4); evidencia justificatoria: prueba de estabilidad de
   hilos vs. estados por familia; costo bajo (reutiliza extracciones ya
   producidas por el pipeline de filtrado). **Adoptar como inspiración.**
2. *Decay/attention LLM (2510.10613)*: resuelve suavizado temporal; localmente
   el suavizado no es el cuello de botella (RollingBERT ya es reproducible,
   ARI 1,0); costo GPU. **Descartar.**
3. *S2WTM / nueva geometría esférica*: OTVMF completo ya fue despromovido por
   complejidad sin ganancia atribuible. **Descartar.**
4. *WALM / evaluación LLM*: complementa la revisión ciega humana obligatoria;
   costo bajo. **Adoptar solo como métrica secundaria etiquetada
   `expert_review_provisional_ai`.**

---

## 3. Inventario crítico de modelos existentes

Evidencia con el corpus canónico de 3.742 salvo indicación.

| Modelo | Estado local | Evidencia clave | Diagnóstico crítico |
|---|---|---|---|
| BERTopic natural multisemilla | backbone provisional | ARI 0,837; cohesión 0,865–867; margen 0,030–0,032; 28–30 tópicos brutos → 24 familias | Contenedores semánticos estables. **No representa procesos**: un documento de 2019 y otro de 2025 caen en la misma familia sin estructura temporal interna. Margen absoluto bajo (≈0,03): las fronteras semánticas son delgadas. |
| RollingBERT R1 online | tracker promovido | cobertura 98,77 %, 20 estados, ARI 1,000, margen bajo | Reproducible pero la identidad global se obtiene agrupando centroides locales *a posteriori* con KMeans: la continuidad puede ser un artefacto del alineador, no del corpus. |
| RollingBERT retrospectivo | solo análisis | ARI 0,624; posible uso de futuro | Riesgo de fuga temporal documentado. |
| OTVMF completo | despromovido | ablación: solo el consenso multisemilla aporta; anclas empeoran cohesión | Experimento negativo valioso: acumular mecanismos (OT, anclas, kernels) sin pregunta previa no rinde. |
| OTVMF O1 esférico | candidato simplificado | ARI 0,677 multisemilla (vs 0,562 de O0) | Inferior a BERTopic en estabilidad; sin ventaja demostrada. |
| RollingLDA/TTTA | baseline léxico | estable, legible; 3.678 docs comparables | Sin embeddings; útil como control léxico barato. |
| OmegaRollingLDA v4 | despromovido | ARI 0,175 | Negativo confirmado. |
| FASTopic | baseline externo principal | cohesión 0,863 ≈ BERTopic; ARI multisemilla 0,384; residuos editoriales (`La Izquierda Diario`, `MundoMarítimo`…) | La inestabilidad entre semillas reorganiza litio/salmueras/comunidades de formas distintas: señal de que la granularidad "correcta" no está determinada por los datos. |
| ECRTM | baseline secundario | margen −0,0053; 1 semilla; ARI 0,193 vs BERTopic | Tópicos sustantivos pero asignación forzada (sin abstención). |
| EnCOT / HiCOT | no promovidos | margen ≈0/negativo; corridas truncadas | Evidencia insuficiente. |
| OmegaEvolve autónomo (E0–E5) | rechazado | ARI 0,408; cobertura 0,70–0,85 | Modelo autónomo añade inestabilidad. |
| **OmegaEvolve-S (selectivo)** | componente promovido experimental | estados por familia: ARI 0,838, cobertura de estados 67,79 %, 20/37 estados pasan puertas; solo la familia carbón muestra dos corrientes concurrentes reproducibles | El hallazgo más informativo del proyecto: **cuando se exige evidencia, casi todas las familias colapsan a una sola trayectoria**. La segmentación semestral dentro de familias fijas produce poca estructura procesual real. |
| CobwebTM | rechazado | ARI 0,222; margen 0,008; sensible al orden | Jerárquico rápido pero no separa este corpus. |
| Atlas temporal FARO | vigente | matriz trimestral, estados semestrales, 25–26 relaciones no causales, 3.725 fechas | Es una capa **descriptiva** construida sobre la partición; hereda la identidad de las familias. |
| Evaluación formal `12_evaluacion_formal_modelos` | legacy | corre sobre 7.372/7.351 docs | **No comparable** con el corpus canónico; no usar para decidir. |

**Síntesis crítica.** El sistema local ya resolvió: (a) familias semánticas
estables; (b) tracking temporal reproducible; (c) subestados con puertas de
evidencia; (d) capa descriptiva de eventos/territorio. Lo que ningún artefacto
resuelve: **ningún objeto del sistema tiene identidad procesual propia**. La
identidad siempre la impone la partición del modelo (familia o estado), y los
procesos sociales reales — el conflicto del litio que migra de negociación
corporativa a disputa hídrica comunitaria; Quintero-Puchuncaví que alterna
latencia y crisis — cruzan familias, cambian de vocabulario y reaparecen. La
evidencia interna lo confirma: OmegaEvolve-S, al condicionar por familia, solo
encontró corrientes concurrentes en carbón; FASTopic reorganiza litio de forma
distinta en cada semilla. La estructura procesual existe en el corpus pero es
**ortogonal a la partición temática**.

---

## 4. Problema no resuelto

**Los tópicos son contenedores; los procesos son hilos.** Formalmente: sea
`P` una partición temática (familias) y sea `H` el conjunto de procesos
sociales que un lector experto reconstruiría (p. ej. "disputa por el Salar de
Atacama", "cierre de Ventanas", "H2 verde en Magallanes"). El proyecto ha
optimizado `P` durante meses (benchmark de 12+ modelos) y ha demostrado con
sus propios experimentos que refinar `P` no recupera `H`:

1. La segmentación temporal dentro de familias (OmegaEvolve-S) produce
   mayoritariamente trayectorias únicas triviales: la variación intra-familia
   no es donde vive el proceso.
2. La inestabilidad entre semillas de FASTopic y el margen ≈0,03 de BERTopic
   muestran que las fronteras de `P` son convencionales, no naturales.
3. El Atlas describe la temporalidad *de la partición* (cobertura trimestral
   por familia), no la temporalidad *de los conflictos*.

Ningún modelo local puede responder hoy, con evidencia y abstención: *"¿cuándo
emergió este conflicto, cuánto estuvo latente, cuándo reapareció, cómo cambió
su vocabulario y sus actores, y con qué confianza?"* — que es la pregunta
sociológica de la tesis.

---

## 5. Alternativas consideradas y descartadas

| Alternativa | Por qué se descarta |
|---|---|
| A. Otro backbone (S2WTM, CoNTM, decay-attention) | El benchmark local demostró que mejorar `P` marginalmente no responde §4. Riesgo de repetir el error OTVMF: mecanismo antes que pregunta. |
| B. Mezcla vMF probabilística completa (ruta B de la frontera local) | Contribución matemática sin resolver identidad procesual; el propio documento de frontera reconoce que "por sí solo no resuelve ciclo de vida". |
| C. Storyline detection con LLM end-to-end (tipo Disaster Storylines) | El LLM decidiría qué es un proceso: no auditable, no reproducible entre corridas, viola límites FARO de uso de LLM y el presupuesto local (API/GPU). |
| D. Knowledge graph de eventos + razonamiento LLM | Costo de extracción alto; los grafos de eventos existentes localmente (genealogía) ya demostraron 0 derivaciones sólidas; el salto a KG completo multiplica supuestos sin puerta de evidencia intermedia. |
| E. Segmentar más fino la capa OmegaEvolve-S (trimestre en vez de semestre) | Menos soporte por celda → más abstención; la evidencia ya muestra colapso a trayectoria única con semestres. |
| F. Cambiar unidad a "evento" puro (episode detection) | Los eventos ya existen como capa descriptiva del Atlas; un evento aislado no representa latencia ni reaparición: se necesita el hilo que los une. |

---

## 6. Propuesta final mínima — HEBRA

**Unidad principal: el *hilo de disputa* (`hebra`)** — una secuencia temporal
de documentos unida por la persistencia de un **referente anclado**, no por
pertenencia a un tópico. Un referente anclado es la tupla parcial:

```
r = (objeto_de_disputa, territorio, actores_núcleo)
```

donde las tres componentes provienen de capas ya existentes y auditadas del
proyecto (extracciones estructuradas del pipeline de refiltro, geocodificación
BCN con evidencia textual, familias como covariable). El tópico deja de ser
identidad y pasa a ser **evidencia** del estado del hilo.

**Contribución central única:** un método de descubrimiento de hilos
**calibrado contra nulos temporales**: toda afirmación procesual (emergencia,
latencia, reaparición, cambio de vocabulario, expansión territorial,
fragmentación) se declara solo si supera lo que produciría el mismo corpus con
fechas permutadas dentro de estratos. La abstención es el resultado por
defecto; el hilo es publicable solo con evidencia que sobreviva perturbación.

Esto es una sola idea falsable — *la identidad procesual anclada en referentes
supera a la identidad impuesta por partición* — y no una arquitectura
acumulativa. No reemplaza BERTopic, RollingBERT, OmegaEvolve-S ni el Atlas:
añade una capa nueva con salidas propias, preservando las capas raw, limpias y
validadas.

**Hipótesis principal (H1):** los hilos anclados en referentes reconstruyen
procesos conocidos (evaluación, no entrenamiento) con mayor estabilidad ante
perturbaciones y mayor utilidad en revisión ciega que la mejor alternativa
basada en partición (familias + estados OmegaEvolve-S).

**Hipótesis nula (H0):** las señales procesuales de los hilos (emergencia,
latencia, reaparición) no superan los percentiles 95 de los nulos de fechas
permutadas, o los hilos no superan a la capa de estados existente en revisión
ciega. Si H0 no se rechaza, HEBRA queda registrado como experimento negativo y
la arquitectura vigente se conserva (criterio de reemplazo FARO).

---

## 7. Especificación técnica reproducible

### 7.1 Entradas (todas existentes; ninguna se modifica)

- Corpus canónico: `06_base_actual_fusionada_3742_incluidas.csv`
  (hash `1caf340dfd44622d…`), 3.725 fechas válidas, columna `fecha_iso`.
- Embeddings canónicos 1024-d alineados
  (`04_embeddings/01_embeddings_canonicos/`, contrato de orden verificado).
- Extracciones estructuradas del refiltro (actores, acciones, tipo de
  conflicto, vínculo de transición) del pipeline
  `02_filtrado_llm/03_pipeline_refiltro_api_qwen_actual`.
- Evidencia espacial: `outputs/included_spatial_evidence.csv` + diccionario
  BCN (coordenadas como evidencia, nunca ubicación exacta).
- Familias promovidas: `promoted_family_assignments.csv` (covariable).

### 7.2 Algoritmo (4 pasos, todos CPU)

**Paso 1 — Normalización de referentes.** Canonicalizar actores (alias,
mayúsculas, siglas) y objetos de disputa contra un diccionario construido por
frecuencia + revisión; territorios ya vienen normalizados por BCN. Salida:
tabla `documento × referente` con evidencia textual por celda. Sin LLM en
línea: el LLM solo puede proponer fusiones de alias que un humano (o una capa
`expert_review_provisional_ai` separada) acepta en lote, con registro.

**Paso 2 — Grafo documental anclado.** Grafo con nodos = documentos (con
fecha), aristas solo hacia el **pasado** (procesamiento online, sin futuro),
con peso:

```
w(i,j) = α·s_ref(i,j) + β·s_emb(i,j),  con s_ref > 0 requerido
```

- `s_ref`: solapamiento ponderado de referentes (Jaccard sobre
  objeto/territorio/actores, con pesos aprendidos NO — fijos y preinscritos:
  objeto 0,5, territorio 0,3, actores 0,2; ablación en §8).
- `s_emb`: coseno de embeddings, usado solo como modulador (β < α).
- Regla dura: sin solapamiento de referente no hay arista. Esto impide que la
  similitud temática fabrique continuidad — la falla ya observada en
  RollingBERT.

**Paso 3 — Hilos por percolación temporal.** Componentes conexos del grafo
umbralizado, con ventana máxima de enlace `Δ` (parámetro, default 12 meses:
enlaces más lejanos exigen mayor `s_ref`). Cada hilo obtiene un perfil:
serie temporal de densidad documental, vocabulario por periodo (c-TF-IDF
dentro del hilo), conjunto de territorios y actores por periodo, y familias
tocadas (para medir si el hilo cruza particiones).

**Paso 4 — Calibración contra nulos y estados del hilo.** Para cada hilo y
cada señal procesual, comparar contra `N=200` corpus nulos donde `fecha_iso`
se permuta dentro de estratos año×fuente (preserva volumen y sesgo editorial,
destruye orden procesual):

- **emergencia**: primera ventana con densidad > p95 nulo (etiqueta operativa:
  "primera observación respaldada", nunca "nacimiento");
- **latencia**: brecha interna > p95 de brechas nulas;
- **reaparición**: densidad post-brecha > p95 nulo;
- **cambio de vocabulario**: distancia coseno entre c-TF-IDF de periodos
  adyacentes > p95 nulo;
- **expansión/fragmentación**: cambio en territorios activos / división del
  hilo en subcomponentes estables.

Señal que no supera el nulo → el hilo se abstiene de esa afirmación y lo
registra. Incertidumbre reportada como percentil contra el nulo, no como
probabilidad calibrada (límite honesto).

### 7.3 Salidas

- `hebra_threads.parquet`: hilo × documento × evidencia de enlace.
- `hebra_profiles.json`: perfil temporal/territorial/actoral por hilo con
  percentiles vs. nulo y abstenciones explícitas.
- `hebra_null_manifest.json`: semillas, estratos y hashes de los 200 nulos.
- Todo bajo `09_metodologia/faro_model_research/competition/fable5/outputs/`
  (capa nueva; no toca Atlas ni contratos vigentes).

### 7.4 Fuga temporal, LLM y reproducibilidad

- Aristas solo hacia el pasado; ninguna estadística global usa el futuro del
  documento al asignarlo; los nulos se generan una vez y se congelan con hash.
- LLM: prohibido en el bucle de descubrimiento. Permitido solo para (a) fusión
  de alias en lote auditada, (b) etiquetado post-hoc de hilos, (c) métrica
  WALM-style secundaria — siempre `expert_review_provisional_ai`.
- Semillas fijas (42, 123, 2024) para todo componente estocástico; manifiestos
  con hashes de entradas; parámetros preinscritos en `config` versionada.
- Los casos conocidos (Quintero-Puchuncaví, HidroAysén, cierre del carbón,
  litio/Atacama, H2 Magallanes) se usan **solo** en evaluación (§8), jamás
  como reglas de construcción del grafo.

---

## 8. Evaluación preinscrita

Baselines (mismo corpus, mismos IDs, mismo orden):

1. Familias BERTopic + estados OmegaEvolve-S (arquitectura vigente).
2. RollingBERT R1 online (tracker).
3. Hilos "solo embeddings" (mismo pipeline con `s_ref` desactivado): aísla la
   contribución del anclaje — la ablación central.
4. Hilos "solo referentes" (sin `s_emb`): mide cuánto aporta la semántica.
5. RollingLDA/TTTA como control léxico.

Métricas preinscritas:

- **Estabilidad por perturbación real** (no solo semilla): bootstrap
  eliminando 10 % de documentos ×20; jitter de fechas ±7 días; ARI/NMI de la
  partición en hilos entre réplicas. Éxito: ARI ≥ 0,80 (nivel del backbone).
- **Recuperación de procesos conocidos**: para los 5 casos preinscritos, ¿el
  sistema produce un hilo mayoritario por caso (pureza y fragmentación
  medidas contra una lista cerrada de documentos-ancla adjudicada ANTES de
  correr el modelo)? Éxito: ≥4/5 casos con pureza > 0,7 y fragmentación < 3
  hilos.
- **Tasa de falsos procesos**: señales declaradas en los corpus nulos (por
  construcción ≈5 %); si en datos reales las señales no exceden claramente esa
  tasa, H0 gana.
- **Revisión humana ciega**: 30 hilos (10 fuertes, 10 fronterizos, 10
  abstenidos) presentados junto a 30 estados OmegaEvolve-S sin identificar el
  sistema; el revisor juzga coherencia procesual, utilidad sociológica y
  errores de mezcla. Protocolo idéntico al de adjudicación ciega ya usado en
  el proyecto (insumo ciego, capas selladas, reconciliación posterior).
- **Diagnósticos**: residuos editoriales por hilo, cobertura (se espera
  cobertura parcial — un documento sin referente extraíble queda fuera, y eso
  es abstención correcta, no fallo), tamaño del componente gigante (si >30 %
  de documentos caen en un solo hilo, el umbral falla → criterio de descarte).

Criterios de descarte explícitos: componente gigante >30 %; ARI de
perturbación <0,6; <3/5 casos conocidos recuperados; revisión ciega sin
diferencia frente a estados. Cualquiera de ellos → experimento negativo
registrado, arquitectura vigente conservada.

---

## 9. Plan de implementación por fases

| Fase | Contenido | Costo estimado | Puerta de salida |
|---|---|---|---|
| F0 | Auditar cobertura de extracciones estructuradas sobre los 3.742 (¿qué % tiene objeto/territorio/actores utilizables?) | horas, CPU | ≥70 % de documentos con ≥1 referente; si no, detener y reportar |
| F1 | Normalización de referentes + diccionario de alias | 1–2 días | tabla documento×referente con evidencia |
| F2 | Grafo + hilos + perfiles (pasos 2–3) | 1 día, CPU (3.742 nodos es trivial) | `hebra_threads` + diagnósticos |
| F3 | Nulos ×200 + calibración (paso 4) | horas, CPU paralelizable | señales con percentiles |
| F4 | Ablaciones (baselines 3–4) + perturbaciones | 1 día | tabla comparativa |
| F5 | Revisión humana ciega | dependiente de Felipe | dictamen |
| F6 | Solo si F2–F5 pasan: integración de lectura en Atlas como capa nueva | 1–2 días | contrato + dashboard |

GPU: **nada de este plan la requiere.** Experimentos que la justificarían solo
después de F5 positivo: re-embedding con modelo de embeddings narrativos
(WebSci 2025) para comparar `s_emb` narrativo vs. semántico; y transferencia a
un segundo corpus (base externa alemana de 46.799 con NER ya disponible:
`01_bases_de_datos/04_base_externa_47k_alemanes/`), que además responde la
pregunta de generalización pendiente del programa.

**Transferencia a otros dominios:** el método solo asume (a) documentos
fechados, (b) un extractor de referentes (objeto/lugar/actores — NER estándar
basta como degradación aceptable), (c) embeddings. Nada es específico de
conflictos chilenos; los pesos del referente son el único punto de ajuste y
quedan preinscritos por dominio.

## 10. Visualización prevista

Solo una, y porque evalúa: un **panel de hilo** (serie de densidad con bandas
del nulo, vocabulario por periodo, mapa de territorios activos por periodo,
familias cruzadas) usado como instrumento de la revisión ciega F5 — el mismo
artefacto sirve para evaluar y, si se promueve, para el Atlas. No se
construye dashboard general antes del dictamen.

## 11. Siguiente experimento mínimo

**F0**: un script de solo lectura que mida, sobre el corpus canónico, la
cobertura y cardinalidad de referentes extraíbles (objeto de disputa,
territorio con evidencia BCN, actores canonicalizables) por documento y por
año. Costo: una sesión. Decide si HEBRA es viable antes de escribir una sola
línea del grafo. Entregable: `f0_referent_coverage_report.md` con distribución
y los 20 peores casos.

## 12. Registro de afirmaciones

**Confirmadas (evidencia local reproducible):**
- Corpus canónico 3.742/1024-d/3.725 fechas (contrato leído y hasheado).
- Veredictos de benchmark: BERTopic backbone (ARI 0,837), FASTopic inestable
  (0,384), OTVMF completo/OmegaRollingLDA v4/CobwebTM despromovidos.
- OmegaEvolve-S: estados ARI 0,838 con cobertura 67,79 %; colapso mayoritario
  a trayectoria única por familia.
- La evaluación formal de `12_evaluacion_formal_modelos` usa un corpus legacy
  no comparable (7.372).

**Inferidas (consistentes, sin validación independiente):**
- Que la estructura procesual es ortogonal a la partición temática (se infiere
  del colapso de OmegaEvolve-S + inestabilidad FASTopic + margen bajo; F0–F4
  la ponen a prueba).
- Que las extracciones del refiltro tienen cobertura suficiente de referentes
  (F0 lo decide; es el riesgo principal de la propuesta).
- La clasificación [P]/[R] de dos preprints recientes puede haber cambiado.

**Pendientes:**
- Todo resultado de HEBRA (nada se ejecutó).
- Revisión humana de `semantic_family_human_review.xlsx` y revisión ciega
  BERTopic–FASTopic–ECRTM, que siguen siendo prerequisitos del programa
  general y no son sustituidas por esta propuesta.

---

*Fin de la propuesta. Ningún artefacto existente fue modificado; no se
implementó, entrenó, instaló ni reejecutó nada. Detención aquí conforme a la
instrucción.*
