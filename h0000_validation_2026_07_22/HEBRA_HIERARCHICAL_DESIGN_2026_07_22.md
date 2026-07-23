# HEBRA jerárquico (macrohilo / subhilo) — diseño v2, experimental

Fecha: 2026-07-22. Este documento **diseña** una arquitectura nueva; **no
sobrescribe HEBRA v1**. La implementación vive en
`fable5/hebra_v2_experimental/`, separada de `diagnostics_h0000/` (sellado)
y de cualquier artefacto v1. Ningún parámetro, umbral, hilo o candidato de
v1 se recalcula ni se modifica aquí.

## 0. Por qué esta arquitectura (evidencia que la motiva)

La validación ciega de H0000 (104 pares, GPT-5.6 + Claude Sonnet 5, ver
`H0000_FINAL_EMPIRICAL_REPORT_2026_07_22.md`) mostró un patrón consistente:

| Nivel de agregación | % positivo amplio (macroproceso o más) | % positivo estricto (proceso específico) |
|---|---:|---:|
| Todo H0000 (post-arbitraje) | 97.1 % | 56.7 % |
| Pares intra-comunidad (cualquier algoritmo) | 95–97 % | 66–68 % |
| Pares inter-comunidad (cualquier algoritmo) | 97–98 % | 40–46 % |
| Pares sin arista directa (solo transitivos) | 97.1 % | 31.4 % |
| Aristas que son puentes estructurales | 100 % | 95.8 % |
| DSU (todo el grafo = 1 clase) | trivial, sin discriminación | no aplica (1 sola clase) |

Lectura: **un solo nivel no puede representar honestamente esta evidencia**.
Al nivel amplio, H0000 es un macroproceso genuinamente coherente (>95% en
todos los cortes, incluidos los pares sin evidencia directa). Al nivel
estricto, hay una señal real pero imperfecta de que existen subprocesos
distintos dentro de ese macroproceso: la brecha intra/inter (~20-25 puntos,
replicada en Louvain, Leiden-mod, Leiden-CPM e Infomap) es consistente,
pero ningún algoritmo comunitario alcanza pureza cercana al 100% intra ni
0% inter — ninguno debe adoptarse ciegamente como "la" partición procesual.
DSU no aporta nada a esta pregunta (colapsa todo en una clase y es frágil
bajo *edge-drop*, ARI 0.05 al 10%, ver `H0000_15_ADDENDUM...json`).

Por eso: dos niveles, no una partición única.

## 1. Nivel 1 — Macrohilo

**Definición**: el macrohilo es exactamente el hilo H0000 actual (el
componente conexo bajo el grafo/umbral congelados de v1, equivalente a la
clase DSU). No se recalcula, no se renombra, no se subdivide en este nivel.

**Semántica validada**: conectividad amplia de un macroproceso sectorial
("estrategia nacional del litio en Chile / Salar de Atacama-Maricunga"),
soportada por ≥95% de positivos amplios en *todos* los cortes evaluados,
incluidos los pares sin evidencia textual directa (transitivos).

**Identificador**: `macrohilo_id = "H0000"` (idéntico al v1; no se inventa
un id nuevo). Si en el futuro se corren otros hilos por el mismo método,
`macrohilo_id` es simplemente el id de hilo v1 ya existente.

## 2. Nivel 2 — Subhilo procesual

**Definición**: agrupación de documentos por objeto/proyecto/salar/contrato/
consulta indígena/litigio/procedimiento ambiental/controversia territorial
**explícitamente nombrado en el texto**, no por comunidad de grafo per se.

### 2.1 Por qué NO usar directamente Louvain/Leiden/Infomap como subhilo

Los cuatro algoritmos comunitarios muestran la misma brecha intra/inter
(evidencia convergente de que *hay* señal), pero:

- Ninguno fue seleccionado como ganador por los guardrails del experimento
  (`arquitectura_v2_no_seleccionada: true` en el lock).
- La pureza intra máxima observada es ~68% (Leiden-CPM), es decir, incluso
  la mejor partición comunitaria clasificaría mal ~32% de los pares que
  declara "misma comunidad" si se usara comunidad = subproceso directamente.
- Leiden-CPM es muy sensible a la resolución (27 comunidades a la
  resolución de densidad, pero 170 "comunidades" triviales de tamaño 1 en
  cuanto resolución≥1.0 — ver `H0000_16_ADDENDUM_LEIDEN_CPM_GRID.csv`), lo
  que la hace fràgil como fuente única de verdad.

### 2.2 Regla de pertenencia elegida (parsimoniosa)

El pipeline v1 **ya extrae** por documento un campo `objeto` y `territorio`
dominantes (`H0000_02_NODE_METRICS.csv`), y por arista un `ref_objeto` /
`ref_territorio` compartido (`H0000_03_EDGE_METRICS.csv`). Esos campos ya
son textualmente interpretables (ver `comunidades_top` en
`H0000_05_PARTITION_COMPARISON.csv`: "acuerdo codelco-sqm", "proyecto
blanco", "salar futuro" aparecen como objetos dominantes reales, no
ruido). En vez de introducir un algoritmo nuevo, el subhilo se construye
por **normalización de ese campo ya existente**:

1. Se normaliza `objeto` (minúsculas, sin tildes, colapsando sinónimos
   conocidos del propio corpus: p. ej. "acuerdo codelco-sqm", "alianza
   codelco-sqm", "explotacion de litio en el salar de atacama (acuerdo
   codelco-sqm)" → una sola clave canónica `acuerdo_codelco_sqm`).
2. Si el `objeto` normalizado es el macro-label genérico ("estrategia
   nacional del litio" sin más especificación) el documento **no** recibe
   subhilo propio: queda en abstención de nivel 2 (pertenece solo al
   macrohilo). Esto es intencional: ese documento realmente no declara un
   proyecto/contrato/consulta/litigio específico, y forzar un subhilo
   inventado violaría el principio de "no asignar por autoridad de
   algoritmo" que rige todo este ejercicio.
3. Las claves canónicas reconocidas quedan en un diccionario corto y
   auditable (`subthread_dictionary.py`, ver Fase 6) que mapea variantes
   textuales → subhilo. El diccionario es un artefacto legible y editable,
   no un modelo entrenado — así se prioriza parsimonia y trazabilidad
   sobre generalidad automática.

### 2.3 Documentos multiasignados

Un documento puede pertenecer a más de un subhilo si:
- su `objeto` normalizado mapea a la clave canónica A (primaria), **y**
- tiene al menos una arista de peso alto (`w >= 0.60`) cuyo `ref_objeto`
  compartido mapea a una clave canónica B distinta.

En ese caso se registra `subhilo_secundario = [B, ...]` sin fusionar A y B
ni forzar una sola pertenencia. Esto responde directamente al requisito de
que "dos documentos pertenezcan al mismo macrohilo pero a subhilos
diferentes" y también cubre el caso de un documento que és realmente
puente semántico entre dos subhilos válidos (ver 2.5).

### 2.4 Puentes entre subhilos

Un puente (arista `puente=True` en `H0000_03_EDGE_METRICS.csv`) que conecta
dos documentos de **distinto** subhilo primario no se trata como error: la
evidencia ciega mostró que el 95.8% de esas aristas puente son, de hecho,
`mismo_proceso_especifico` — es decir, en la mayoría de los casos ambos
documentos *deberían* terminar en el mismo subhilo, y una discrepancia
puente-cruza-subhilos es una señal de que el diccionario de normalización
(2.2) probablemente está subdividiendo lo que en realidad es un solo
proyecto/contrato con dos redacciones distintas del campo `objeto`. Regla
operativa: **todo puente que cruce subhilos se loguea explícitamente**
(trazabilidad, ver 2.7) para revisión humana/experta posterior del
diccionario; no se fusiona automáticamente sin esa revisión.

### 2.5 Abstención

Dos formas de abstención, ambas explícitas en el esquema de datos (nunca
un `null` silencioso):
- **Abstención de nivel 2 (documento)**: `objeto` normalizado = macro-label
  genérico → `subhilo_primario = "SIN_SUBHILO_ESPECIFICO"`. El documento
  sigue perteneciendo al macrohilo.
- **Abstención de pertenencia (par)**: cuando se evalúa un par de
  documentos para pureza/cobertura y al menos uno de los dos está en
  abstención de nivel 2, el par se marca `evaluable_subhilo = False` y se
  excluye de las métricas de pureza estricta de subhilo (no se cuenta como
  ni acierto ni error).

### 2.6 Identificadores

- `macrohilo_id`: idéntico al id de hilo v1 (p. ej. `"H0000"`).
- `subhilo_id`: `f"{macrohilo_id}::{clave_canonica}"`, p. ej.
  `"H0000::acuerdo_codelco_sqm"`, `"H0000::proyecto_blanco_maricunga"`,
  `"H0000::consulta_ceol_laguna_verde"`, `"H0000::SIN_SUBHILO_ESPECIFICO"`.
  El prefijo del macrohilo hace que el id de subhilo sea único incluso si
  en el futuro dos macrohilos distintos comparten una clave canónica
  parecida (p. ej. otro hilo que también mencione "consulta indígena").

### 2.7 Trazabilidad

Cada asignación de subhilo guarda: `doc_id`, `objeto_original` (sin
normalizar), `clave_canonica`, `regla_aplicada` (cuál entrada del
diccionario matcheó), y `fuente` (`"nodo"` o `"arista_secundaria"` con el
`doc_j` y peso que la originó, si aplica). Todo puente cruza-subhilos se
registra en una lista aparte (`bridge_crossings.csv`) con los dos subhilos,
el peso de la arista y el resultado ciego observado si el par estaba en la
muestra de 104 (para trazar directamente la evidencia que sostiene o
contradice esa asignación).

## 3. Métricas de cobertura y pureza

- **Cobertura de subhilo** = % de documentos del macrohilo con
  `subhilo_primario != "SIN_SUBHILO_ESPECIFICO"`.
- **Pureza estricta de subhilo** = de los pares evaluables (2.5) que
  comparten `subhilo_primario`, qué fracción fue juzgada
  `mismo_proceso_especifico` en la validación ciega (usa
  `H0000_VALIDATION_INTEGRATED_2026_07_22.json` como fuente empírica; no
  inventa una nueva muestra).
- **Retención amplia** = % de pares que, aunque queden en subhilos
  distintos, siguen siendo al menos `mismo_macroproceso` — debe permanecer
  ≥ la tasa amplia observada a nivel de macrohilo (~97%), porque dividir en
  subhilos nunca debe *destruir* la continuidad amplia ya demostrada.

Estas tres métricas son exactamente las que decidirán, con datos, si el
subhilo mejora la pureza estricta (objetivo) sin destruir la continuidad
amplia (restricción) — el criterio que Fase 4 pidió evaluar explícitamente.

## 4. Compatibilidad con artefactos existentes

- Lee (solo lectura) `H0000_01..07` y `H0000_09` (clave, ya desellada para
  este análisis) desde `diagnostics_h0000/`.
- No escribe nada dentro de `diagnostics_h0000/`.
- Todo output nuevo vive en `hebra_v2_experimental/artifacts/` con su
  propio manifest de hashes y `experiment_lock` que referencia los hashes
  de v1 de los que depende (para probar, por hash, que no se modificaron).
- El esquema de subhilo es aditivo: un consumidor que solo entienda
  `macrohilo_id` (v1) sigue funcionando exactamente igual; `subhilo_id` es
  una columna adicional, no un reemplazo.

## 5. Lo que esta versión NO hace (por diseño, no por omisión)

- No declara un algoritmo de comunidad "ganador".
- No fusiona ni divide el macrohilo H0000 v1.
- No usa NLP/embeddings nuevos para inferir objeto: reutiliza el campo
  `objeto` que el pipeline v1 ya calculó.
- No pretende resolver el 100% de los documentos en subhilos específicos:
  la abstención explícita es preferible a una asignación inventada.
- No se declara superior a FTD ni a ninguna arquitectura previa.
