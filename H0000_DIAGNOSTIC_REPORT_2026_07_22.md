# Fase 3B — Diagnóstico estructural congelado de H0000

Fecha: 2026-07-22. Configuración v1 intacta (`f2b_idf_v2_L2`, τ=0,45, tier
L2). Git HEAD `cf5ab5e1e6bf22622641970f476367fbd55ba0a3`. Ningún parámetro,
umbral, candidato ni arista fue recomputado o modificado. Algoritmos de
partición ejecutados únicamente en modo diagnóstico. **No se declara
ganador ni se selecciona arquitectura v2.**

## 1. Resumen ejecutivo

H0000 no es una cadena delgada ni un núcleo homogéneo: es un **núcleo
denso de 148 documentos con 22 satélites** unido por 23 puentes, de los
cuales 15 tienen w<0,50. Los puentes se distinguen estructuralmente de las
aristas internas por **ausencia total de apoyo triangular** (mediana 0
triángulos vs 10; embeddedness 0 vs 0,56; ambos p<10⁻¹⁵ tras BH), pero —
hallazgo contraintuitivo — tienen **similitud semántica más alta** (s_emb
mediana 0,90 vs 0,86) y **distancia temporal mucho menor** (17 vs 113
días) que las aristas internas. Es decir: los puentes no son enlaces
débiles y antiguos, sino conexiones semánticamente fuertes y recientes que
carecen de corroboración estructural (sin triángulos). Las cinco
particiones diagnósticas (DSU, Louvain, Leiden-CPM, Leiden-modularidad,
Infomap) convergen en **9-27 comunidades** con alta estabilidad
inter-semilla (ARI≥0,92) pero difieren en granularidad; ninguna se elige
aquí. 4.345 pares de documentos dependen exclusivamente de los 23 puentes
para estar conectados, y 5.637 pares transitivos son heterogéneos en
territorio y objeto simultáneamente — evidencia de riesgo de chaining, no
de mezcla confirmada. **Conclusión provisional: estructura mixta** (núcleo
legítimo + satélites + zona de riesgo de chaining vía puentes), pendiente
de adjudicación ciega externa de la muestra sellada de 104 pares.

## 2. Verificación del subgrafo

| Cifra congelada | Observado | Coincide |
|---|---:|---|
| Documentos | 170 | ✅ |
| Aristas | 889 | ✅ |
| Puentes | 23 | ✅ |
| Puentes w<0,50 | 15 | ✅ |
| Núcleo tras podar puentes débiles | 148 | ✅ (`[148,4,4,2,1,1,1,1]`) |

Hashes de threads/edges v1 verificados contra `outputs/F4_MANIFEST.json`
antes de ejecutar (`diagnostics_h0000/verify_preservation.py`). Discrepancia
de trabajo detectada y registrada (no relacionada con H0000): el working
tree tenía `outputs/f2_threads_summary.json` y `F4_MANIFEST.json`
modificados por regeneración de timestamps post-commit; los CSV/edge files
usados en este diagnóstico coinciden exactamente con el manifest committeado
(ver `H0000_11_EXPERIMENT_LOCK.json`).

## 3. Topología

- Densidad 0,062; grado min 1 / mediana 9 / máx 29; clustering medio 0,651.
- Diámetro 11; camino medio 4,15.
- k-core máximo 15 (23 documentos en el núcleo más denso).
- 29 componentes biconexos; **23 nodos de articulación**.
- 28 documentos con grado ≤2 (satélites potenciales); 16 con grado
  exactamente 1 (dependientes de una sola arista).
- 19,5 % de aristas son "largas" (dt>365 días) — 173 de 889.
- Cronología: 1 doc (2022), 37 (2023), 40 (2024), 79 (2025), 13 (2026) — el
  hilo es predominantemente reciente, coherente con el crecimiento del
  corpus post-2022 ya documentado en F3.

## 4. Puentes y articulaciones (E2)

| Rasgo | Puentes (mediana) | No-puentes (mediana) | p (MW) | q (BH) |
|---|---:|---:|---:|---:|
| w | 0,489 | 0,551 | 0,041 | 0,041 |
| s_ref | 0,312 | 0,448 | 0,0018 | 0,0025 |
| **s_emb** | **0,903** | 0,856 | 2·10⁻⁵ | 5·10⁻⁵ |
| **días** | **17** | 113 | 2,2·10⁻⁴ | 3,8·10⁻⁴ |
| triángulos | 0 | 10 | <10⁻¹⁵ | 0,0000 |
| embeddedness | 0 | 0,56 | <10⁻¹⁵ | 0,0000 |
| IDF máx. referente | 1,0 | 0,824 | 0,011 | 0,013 |

Todas las diferencias sobreviven corrección BH (q≤0,05). Lectura
diagnóstica, no conclusión procesual: los puentes se sostienen en un
enlace único de alta semántica y referente muy específico (IDF alto),
reciente, sin ningún triángulo de apoyo. Esto **no implica que sean
erróneos** — pueden ser la evidencia correcta de una reactivación puntual
— pero sí que son estructuralmente el punto de mayor fragilidad del hilo.

Daño potencial por puente (top 3 de 23, por documentos que quedarían
separados si se elimina esa arista): (1938,1943) w=0,452 → separa 11 docs;
(1108,1943) w=0,483 → separa 5; (1943,1945) w=0,455 → separa 5. El
documento 1943 concentra el mayor riesgo estructural individual.

## 5. Condiciones de poda (E3, diagnóstico, no adoptado)

| Condición | Cortadas | Componentes | Tamaños top | Retención de pares | Objeto dominante mayor |
|---|---:|---:|---|---:|---|
| P0 solo puentes | 23 | 24 | 142,4,3,1,1,1 | 0,698 | estrategia nacional del litio |
| P1 sin triángulos + q1 w | 18 | 15 | 137,12,5,4,2,1 | 0,654 | ídem |
| P2 top-5% betweenness + w bajo | 33 | 8 | 141,14,5,3,2,2 | 0,695 | ídem |
| Puente∧w<0,48 | 8 | 9 | 153,5,5,2,1,1 | 0,811 | ídem |
| Puente∧w<0,50 | 15 | 16 | 148,4,4,2,1,1 | 0,758 | ídem |
| Puente∧w<0,52 | 16 | 17 | 148,4,3,2,1,1 | 0,758 | ídem |

Ninguna poda disuelve el núcleo: el mayor componente resultante conserva
82-90 % del tamaño original en todos los escenarios. El objeto dominante
del componente mayor es siempre "estrategia nacional del litio" —
consistente con un núcleo temático estable. Las aristas cortadas quedan
identificadas en `H0000_07_PRUNING_DIAGNOSTICS.csv`/código para revisión
ciega futura; **no se declara que ninguna poda mejore HEBRA** sin esa
adjudicación.

## 6. Comparación de particiones (E4)

| Algoritmo | N comunidades | Tamaños top5 | ARI inter-semilla | ARI drop10% |
|---|---:|---|---:|---:|
| DSU (actual) | 1 | [170] | 1,000 | 0,050 |
| Louvain | ~10 | variable | 0,918 | 0,876 |
| Leiden-CPM | ~27 | variable | 0,989 | 0,966 |
| Leiden-modularidad | ~10 | 32,27,23,19,19 | 1,000 | 0,936 |
| Infomap | ~20 | 32,19,16,14,14 | 1,000 | 0,955 |

DSU es perfectamente estable entre semillas (no depende de aleatoriedad)
pero **colapsa bajo edge-drop 10 % (ARI 0,05)** — un componente conexo es
extremadamente sensible a la eliminación de pocas aristas, justo por su
dependencia de puentes. Los cuatro algoritmos comunitarios son
sustancialmente más estables bajo perturbación (ARI 0,88-0,97) que DSU bajo
la misma perturbación, aunque DSU "gana" en estabilidad inter-semilla
trivialmente (no es estocástico). Ningún algoritmo se elige por esta tabla
sola, conforme al guardrail. Detalle completo con enlaces largos divididos
y referentes dominantes por comunidad en `H0000_05_PARTITION_COMPARISON.csv`.

## 7. Estabilidad

Ver tabla del punto 6 y `H0000_06_STABILITY_REPORT.md` (jitter ±7d: ARI=1,0
para todos los algoritmos — ningún enlace del subgrafo congelado cruza la
frontera de 1.095 días bajo jitter, por lo que el jitter no perturba esta
subestructura; límite ya documentado en F4-D). El hallazgo más relevante de
estabilidad es la fragilidad de DSU frente a drop10% comparada con
cualquier partición comunitaria — evidencia diagnóstica a favor de
considerar particiones comunitarias en el futuro, **no una decisión tomada
aquí**.

## 8. Riesgo de chaining

- Pares totales posibles: 14.365. Pares con arista directa: 889. **Pares
  solo conectados transitivamente: 13.476.**
- **4.345 pares dependen exclusivamente de los 23 puentes** para estar en
  el mismo componente (desconectados si se remueven todos los puentes).
- **5.637 pares transitivos son heterogéneos** en territorio Y objeto
  simultáneamente (sin territorio ni objeto compartido) — candidatos a
  posible mezcla vía transitividad, pero esto es un conteo estructural, no
  evidencia textual de mezcla real.
- Longitudes de camino transitivo disponibles en
  `H0000_04_TOPOLOGY_REPORT.md` (distribución completa).

**No se declara mezcla real**: eso requiere la adjudicación ciega de §9.

## 9. Muestra ciega construida

Sellada en `H0000_08_BLIND_REVIEW_SHEET.json` /
`H0000_09_BLIND_KEY_DO_NOT_OPEN.json` (semilla 20260780). **104 de 120
ítems objetivo** (40 intra-comunidad, 40 inter-comunidad, 20 cruzando
puentes, **4 de 20** enlaces largos potencialmente fragmentables). La
desviación es honesta y estructural, no un error: solo existen **4 aristas
largas (dt>365) con embeddedness≤0,05** en todo H0000 (de 173 aristas
largas totales) — es decir, casi todas las aristas largas del hilo SÍ están
apoyadas en triángulos, lo cual es información relevante en sí misma (las
aristas largas de este hilo no son en su mayoría puentes frágiles). No se
amplió el criterio para completar la cuota porque eso habría introducido
sesgo de selección post-hoc. Ítems muestran título+texto completo (hasta
6.000 caracteres); no revelan algoritmo, comunidad, puntaje ni motivo de
selección. Protocolo de integración en la clave: adjudicadores externos
(≥2 IA + humano si disponible) completan sin ver la clave; se congela con
hash; solo entonces se cruza.

## 10. Claims permitidos

- H0000 tiene un núcleo denso (~148 docs) con 22-28 satélites de grado
  bajo y 23 puentes, 15 de ellos con w<0,50.
- Los puentes difieren de las aristas internas en un patrón estructural
  específico (sin triángulos, sin embeddedness) que persiste incluso
  siendo semánticamente fuertes y temporalmente cercanos — hallazgo
  robusto tras corrección por comparaciones múltiples.
- Ninguna condición de poda diagnóstica disuelve el núcleo por completo.
- Los algoritmos comunitarios son más robustos que DSU ante eliminación de
  aristas, como propiedad estructural medida.
- 4.345 pares y 5.637 pares heterogéneos dependen de puentes o son
  transitivos heterogéneos — cifras estructurales verificadas.

## 11. Claims NO permitidos

- Que H0000 contiene "varios procesos" (requiere adjudicación de §9).
- Que los puentes son "erróneos" por tener w bajo (el análisis muestra que
  tienen s_emb alto; el riesgo es la ausencia de triángulos, no el peso).
- Que alguna partición comunitaria "mejora" HEBRA (ninguna fue adoptada).
- Que la poda "mejora" el hilo (no evaluado con adjudicación externa).
- Cualquier selección de τ, algoritmo o arquitectura v2.
- Uso de "componente gigante ≤30 %", F4-A, HN50-B o ISO20 como evidencia de
  identidad, tasa de error o sobreabstención (guardrails respetados: no se
  invocaron en este diagnóstico).

## 12. Conclusión provisional

**Estructura mixta**: un núcleo denso, temáticamente coherente (litio /
Salar de Atacama, consistente en todas las condiciones de poda), con
satélites de grado bajo y una zona de riesgo real de chaining concentrada
en 23 puentes recientes y semánticamente fuertes pero sin apoyo triangular.
Ni "proceso único" ni "varios procesos" está demostrado: ambas hipótesis
son consistentes con distintas partes de la evidencia estructural. La
adjudicación ciega de los 104 pares sellados (§9) es el siguiente paso
necesario y no ejecutado.

---

## Artefactos generados (11)

`H0000_01_SUBGRAPH_CANONICAL.csv`, `H0000_02_NODE_METRICS.csv`,
`H0000_03_EDGE_METRICS.csv`, `H0000_04_TOPOLOGY_REPORT.md`,
`H0000_05_PARTITION_COMPARISON.csv`, `H0000_06_STABILITY_REPORT.md`,
`H0000_07_PRUNING_DIAGNOSTICS.csv`, `H0000_08_BLIND_REVIEW_SHEET.json`,
`H0000_09_BLIND_KEY_DO_NOT_OPEN.json`, `H0000_10_MANIFEST.json`,
`H0000_11_EXPERIMENT_LOCK.json` — todos en `diagnostics_h0000/`.

Nota técnica: Leiden y Infomap se ejecutaron vía `python-igraph`
(`community_leiden`, `community_infomap`); los paquetes standalone
`leidenalg`/`infomap` no estaban instalados. Resolución CPM = densidad del
subgrafo (0,062), documentado en el lock.

— Fable 5. Sin selección de arquitectura v2. Sin ganador declarado.
