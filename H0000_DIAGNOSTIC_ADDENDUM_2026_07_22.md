# Fase 3B — Addendum diagnóstico correctivo de H0000

Fecha: 2026-07-22. `H0000_DIAGNOSTIC_REPORT_2026_07_22.md` y sus 11
artefactos quedan **intactos** como diagnóstico histórico. Este addendum
corrige siete puntos señalados por el auditor mediante cómputo adicional
(archivos `H0000_12` a `H0000_16` en `diagnostics_h0000/`), siempre en modo
diagnóstico E1-E4. **Ninguna arquitectura v2 se selecciona; ningún ganador
se declara.**

## 1. Satélites: definición operacional y listas completas

El auditor detectó que "22 satélites" no tenía definición estable y que las
listas de tamaños de componentes estaban truncadas al imprimirse (sumaban
162, no 170). Confirmado: era **truncamiento de impresión** (`[:8]`), no un
error de cómputo. Listas completas ahora en
`H0000_13_ADDENDUM_SATELLITE_DEFINITIONS.json`:

- Grado ≤2: **28** documentos. Grado exactamente 1: **16**.
- Cortar los **23 puentes completos**: 24 componentes, tamaños
  `[142,4,3,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1]` — suma **170** ✓.
- Cortar solo los **15 puentes débiles (w<0,50)**: 16 componentes, tamaños
  `[148,4,4,2,1,1,1,1,1,1,1,1,1,1,1,1]` — suma **170** ✓.

Se retira "22 satélites" como cifra única; se reportan las cinco
definiciones (grado≤2, grado=1, articulación, bloques biconexos pequeños,
componentes tras poda) por separado, sin declarar ninguna canónica.

## 2. Triángulos/embeddedness en puentes: tautología reconocida

Correcto: un puente no puede pertenecer a un ciclo, así que
triángulos=0 y embeddedness=0 en **todo** puente es consecuencia directa de
la definición, no un hallazgo estadístico. **Se retiran** los tests
Mann-Whitney sobre triángulos/embeddedness como evidencia sustantiva; se
conservan solo como verificación de consistencia (deben dar exactamente 0,
y así fue: máximo de triángulos en puentes = 0). La formulación válida del
mecanismo de unión usa únicamente las variables no tautológicas:

> Los puentes son los puntos necesarios de conectividad y, además, muestran
> semántica más alta (s_emb mediana 0,903 vs 0,856), referente más
> específico (IDF 1,0 vs 0,824) y menor distancia temporal (17 vs 113
> días) que las aristas internas — no menor s_ref (0,312 vs 0,448, en la
> dirección esperada).

## 3. Perfil completo de daño por puente (árbol de bloques)

Construido el árbol de bloques (bloques = componentes tras cortar los 23
puentes; aristas = los propios puentes) y calculada la distancia en ese
árbol para cada uno de los 4.345 pares dependientes:

| Longitud del camino (n° de puentes) | Pares |
|---|---:|
| 1 (un solo puente separador) | 2.148 |
| 2 | 1.542 |
| 3 | 432 |
| 4 | 199 |
| 5 | 21 |
| 6 | 3 |

**49,4 % de los pares dependen de un único puente; 50,6 % requiere una
cadena de 2 o más.** Concentración: los 3 puentes con más pares de
dependencia única cubren solo el **19,8 %** de esos pares — el daño **no**
está fuertemente concentrado en 1-2 puentes críticos; está distribuido.
Perfil completo (23 puentes × daño individual × pares de dependencia única)
en `H0000_12_ADDENDUM_BRIDGE_DAMAGE_PROFILE.json`.

## 4. Heterogeneidad transitiva: con línea base, no como indicador aislado

| Medida | Valor |
|---|---:|
| Aristas directas heterogéneas (sin territorio+objeto compartido) | **0,0 %** |
| Todos los pares dentro de H0000 heterogéneos | 39,2 % |
| Solo pares transitivos (sin arista) heterogéneos | 41,8 % (5.637) |

Líneas base de hilos grandes conocidos (mismo criterio, TODOS los pares,
no solo transitivos): **H0001 (Dominga, 162 docs) = 0,0 %; H0002
(Ventanas, 148 docs) = 0,0 %; H0004 (Alto Maipo, 87 docs) = 0,0 %.** Estos
hilos de un solo proyecto no tienen heterogeneidad objeto+territorio
porque casi todos comparten el mismo objeto — contraste fuerte con el
39,2 % de H0000, y evidencia adicional (no la única) de que H0000 opera a
escala de macrotema, no de proyecto único.

Nulo de permutación (B=300, referentes barajados entre nodos preservando
el grafo): media nula 5.286,9, p95=5.330, **observado 5.637, p=0,0033**.
El nivel de heterogeneidad transitiva observado es **significativamente
mayor** que el esperado por azar dado el grafo — los caminos transitivos de
H0000 conectan preferentemente documentos con referentes distintos más de
lo que la topología por sí sola predeciría. Esto es evidencia estructural a
favor de vigilar el chaining, pero **sigue sin ser evidencia textual de
mezcla real**: queda como prioridad de auditoría, no como tasa de error.

## 5. DSU vs comunidades: métrica comparable (retracción parcial)

Corrección crítica aceptada: comparar el ARI de DSU (una sola clase)
contra particiones ya fragmentadas es una comparación asimétrica. Con la
métrica correcta —retención de pares originalmente coasignados, VI,
tamaño de clase/comunidad principal, todo dentro de la propia partición de
cada algoritmo—:

| | drop 5% retención | drop 10% retención | VI drop10 | Componente/comunidad ppal. drop10 |
|---|---:|---:|---:|---:|
| **DSU** | **0,974** | **0,951** | 0,132 | 165,7 |
| Louvain | 0,923 | 0,886 | 0,336 | 31,8 |
| Leiden-mod | 0,966 | 0,928 | 0,201 | 31,7 |
| Infomap | 0,972 | 0,948 | 0,146 | 31,2 |

**Se retira la afirmación "DSU colapsa (ARI 0,05) / los algoritmos
comunitarios son más robustos".** Con la métrica comparable, **DSU tiene la
retención de pares más alta de las cuatro configuraciones** bajo ambas
perturbaciones (0,951 vs 0,886-0,948). El ARI=0,05 del informe original era
un artefacto de comparar una clase única contra una partición fragmentada,
exactamente como señaló el auditor. Formulación corregida:

> La conectividad interna de H0000 bajo DSU (medida por retención de pares
> y VI) es al menos tan estable como la de las particiones comunitarias
> ante edge-drop del 5-10 %. Esto no determina si esa estabilidad
> representa un proceso legítimo o un artefacto de sobre-conexión; sigue
> pendiente de la adjudicación ciega.

## 6. Núcleo "temáticamente estable", no "procesualmente legítimo"

Aceptado sin reservas: "estrategia nacional del litio" como objeto
dominante en todas las podas demuestra estabilidad de un **macrotema**, que
puede abarcar salares, proyectos, empresas y procesos de consulta distintos
(consistente con §4: heterogeneidad muy superior a hilos de un solo
proyecto). No se afirma legitimidad procesual del núcleo de 148 documentos
como unidad única.

## 7. Grid de resolución Leiden-CPM

Aclaración: las instrucciones de Fase 3B recibidas por este agente no
especificaban un grid numérico explícito para CPM; se usó solo la
resolución por defecto (densidad=0,062). Se ejecuta ahora el grid sugerido
por el auditor **{0,25; 0,5; 1,0; 1,5; 2,0}** además del valor por defecto:

| Resolución | N comunidades | Top-5 tamaños | Singletons |
|---:|---:|---|---:|
| 0,062 (densidad, default) | 27 | 26,18,18,14,10 | 6 |
| 0,25 | 43 | 24,18,16,14,10 | 17 |
| 0,50 | 67 | 13,12,11,10,8 | 36 |
| 1,00 | 170 | todos 1 | 170 |
| 1,50 | 170 | todos 1 | 170 |
| 2,00 | 170 | todos 1 | 170 |

A resolución ≥1,0 el objetivo CPM penaliza cualquier agrupamiento dado que
los pesos de arista (0,4-0,9) quedan por debajo del umbral de densidad
requerido, y la partición colapsa a singletons completos (170/170) — el
grid confirma que solo resoluciones bajas (≤0,5) son informativas para
este subgrafo; no se elige ninguna como definitiva.

## Estado

Todos los guardrails de Fase 3B se mantienen: no se seleccionó τ, DSU,
Louvain, Leiden ni Infomap como arquitectura; no se declaró ganador; no se
usó F4-A, HN50-B ni ISO20 como evidencia. La adjudicación ciega de los 104
pares sellados (`H0000_08/09`) sigue siendo el paso pendiente decisivo,
ahora informada por un perfil de daño distribuido (no concentrado), una
línea base de heterogeneidad con contraste real (0 % en hilos de un
proyecto vs 39-42 % en H0000) y una comparación DSU/comunidades
metodológicamente correcta.

— Fable 5.
