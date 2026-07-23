# HEBRA v2 EXPERIMENTAL — validación fuera de muestra (18 macrohilos ≠ H0000)

Fecha: 2026-07-23. **HEBRA v2 experimental está congelado** (ver
`../FROZEN.json`, hashes verificados por `../src/verify_frozen.py`, llamado
al inicio de `run_benchmark.py`). Este informe NO agrega ninguna regla al
diccionario de canonización; corre exactamente el mismo código y
diccionario ya validados en H0000, aplicados a datos que nunca vieron.

**No se declara superioridad de HEBRA sobre nada en este informe.**

## 1. Selección de hilos (criterio objetivo, no cherry-picking)

Todos los `thread_id` con ≥15 documentos en
`fable5/outputs/f2b_idf_v2_L2_threads.csv`, **excluyendo H0000**: 18 hilos,
de H0001 (162 docs) a H0018 (15 docs) — 918 documentos en total. El umbral
de 15 se fijó porque es el mismo orden de magnitud mínimo con el que H0000
mostró estructura interna interpretable; no se ajustó después de ver
resultados.

De estos, tres (**H0001, H0002, H0004**) tienen evidencia estructural
*independiente y previa* de ser procesos únicos coherentes: el addendum
`H0000_14_ADDENDUM_HETEROGENEITY_BASELINE.json` ya los reportó con **0%
de pares heterogéneos** en objeto+territorio (Dominga, Fundición Ventanas,
Bocamina, respectivamente). Sirven como prueba directa —no proxy— de
fragmentación: si el diccionario los partiera en varios subhilos no
triviales, eso sería evidencia real de sobre-fragmentación.

## 2. Método (reutiliza el mismo procedimiento que h0000_diagnostics.py, sin inventar nada)

Para cada hilo: se toman sus documentos de
`f2b_idf_v2_L2_threads.csv`, sus aristas inducidas de
`f2b_idf_v2_L2_edges.csv`, y sus referentes de `f1v2_referents.csv`. El
campo `objeto` por documento y el campo `ref_objeto`/`puente` por arista se
construyen con el **mismo método** que v1 ya usó para H0000 (unión/
intersección de referentes por tipo, puentes de teoría de grafos estándar
vía `networkx.bridges`) — ver
`out_of_sample_benchmark/src/prepare_thread_inputs.py`. Después, se
llaman **sin modificar** `build_primary_assignment`,
`add_secondary_assignments` y `detect_bridge_crossings`, importadas
directamente de `hebra_v2_experimental/src/build_hierarchy.py`.

## 3. Resultado observado

| Hilo | n_docs | Objeto real (referencia) | Cobertura | Subhilos distintos | Índice fragmentación | Riesgo sobreagregación (proxy) |
|---|---:|---|---:|---:|---:|---:|
| H0001 | 162 | Dominga (baseline coherente) | **0%** | 0 | n/a | n/a |
| H0002 | 148 | Fundición Ventanas (baseline coherente) | **0%** | 0 | n/a | n/a |
| H0003 | 100 | H2 Magallanes | **0%** | 0 | n/a | n/a |
| H0004 | 87 | Bocamina (baseline coherente) | **0%** | 0 | n/a | n/a |
| H0005 | 85 | Alto Maipo | **0%** | 0 | n/a | n/a |
| H0006 | 51 | HidroAysén | **0%** | 0 | n/a | n/a |
| H0007–H0018 | 35→15 | El Mauro, Faro del Sur, ENAP Aconcagua, otros | **0%** | 0 | n/a | n/a |

**Cobertura = 0% en los 18/18 hilos evaluados. Ningún documento fuera de
H0000 recibió un subhilo propio.** Detalle completo (incluye la lista de
todos los `objeto` distintos vistos por hilo) en
`artifacts/out_of_sample_summary.json` y
`artifacts/out_of_sample_node_assignment.csv`.

### Verificación de que no es un error de la adaptación de datos

Se verificó explícitamente (no se asumió) que la ausencia de cobertura no
es un bug del adaptador: de los 918 documentos evaluados, solo 8 tienen
campo `objeto` vacío (no la causa principal); 123 valores de `objeto`
distintos y no vacíos existen en la muestra; y **12 documentos mencionan
literalmente "Codelco"** (por la Fundición Ventanas, filial de Codelco
para *cobre*, en H0002) — pero ninguno matchea la regla
`codelco.{0,15}sqm|sqm.{0,15}codelco` porque, correctamente, nunca aparece
junto a "SQM": es una instalación de cobre no relacionada con el acuerdo
de litio de H0000. **El diccionario no genera falsos positivos por la sola
mención de "Codelco"** — comportamiento correcto, no accidental.

## 4. Interpretación

El resultado no es "HEBRA falla out-of-sample" en un sentido genérico: es
la consecuencia **esperable y correcta** de que
`subthread_dictionary.py` es, tal como está congelado, **un diccionario
específico del vocabulario de H0000** (Codelco-SQM, Maricunga, Salar
Blanco, CEOL por salar, Salar Futuro) — no un método general de extracción
de subprocesos. Aplicado a corpus temáticamente distintos (minería
portuaria, fundición de cobre, hidrógeno verde, termoeléctricas,
hidroeléctricas, relaves, energía eólica, refinerías), abstiene
correctamente en el 100% de los casos en lugar de inventar coincidencias
espurias.

Esto permite distinguir **tres modos de falla posibles**, de los cuales
solo uno se observó:

1. **Fragmentación** (partir un proceso único conocido en subhilos
   espurios): **no observada** — los tres baselines coherentes (H0001,
   H0002, H0004) recibieron 0 subhilos, no múltiples subhilos falsos.
2. **Sobreagregación** (unir procesos distintos bajo la misma clave):
   **no observada** — no hubo ninguna asignación no-abstención sobre la
   que pudiera ocurrir.
3. **Abstención total / subgeneralización** (el mecanismo no produce
   ninguna señal en absoluto sobre datos nuevos): **es exactamente lo que
   se observó**, en el 100% de los 18 hilos.

**Esto no demuestra que el mecanismo de subhilo (objeto normalizado +
abstención explícita) sea incorrecto como *arquitectura*** — de hecho, la
arquitectura funcionó como se diseñó: prefirió abstenerse en vez de forzar
asignaciones sin respaldo léxico. **Sí demuestra que el diccionario
concreto congelado no generaliza a otros macrohilos sin trabajo adicional**
(escribir un diccionario análogo para cada macrohilo nuevo, o diseñar un
mecanismo de extracción de `objeto` menos dependiente de vocabulario
prefijado) — trabajo explícitamente fuera de alcance aquí porque el
congelamiento lo prohíbe.

## 5. Pureza real (pendiente, no ejecutada)

Con cobertura 0%, no existe ningún par intra-subhilo que evaluar para
pureza fuera de H0000: no tiene sentido generar una muestra ciega nueva
para pares que no existen. Este paso queda formalmente pendiente **hasta
que exista una decisión explícita** (fuera de este congelamiento) sobre
extender el diccionario a otros macrohilos.

## 6. Qué esto habilita para el benchmark contra FTD

Vea `FTD_HEBRA_COMMON_BENCHMARK_SPEC.md` en esta misma carpeta. El hallazgo
central de este informe (cobertura 0% fuera de H0000) implica que, **con
el diccionario actual**, el benchmark común contra FTD solo puede
compararse de forma significativa sobre **macrohilos donde HEBRA v2
produce alguna asignación real** — es decir, H0000 mismo, o macrohilos
futuros para los que alguien decida explícitamente escribir un
diccionario propio. La especificación del benchmark se deja lista para
ambos escenarios sin ejecutar ninguno.
