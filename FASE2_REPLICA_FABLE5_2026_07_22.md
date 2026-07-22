# Fase 2 — Informe de réplica cruzada (Fable 5 / HEBRA)

Fecha: 2026-07-22. Bajo memorando canónico Fase 2. Código v1 intacto; sin
ensemble; sin copia de componentes; sin ajuste sobre la adjudicación v1.
Desarrollado de forma independiente antes de la comparación cruzada.

---

## 1. Resumen ejecutivo

La inspección directa del código de FTD-Core confirma un sistema bien
ingenierizado con dos hallazgos de primera importancia: (a) un **defecto
demostrado en el cálculo de margen bajo Louvain** (`trajectories.py:215`
pasa todos los enlaces evaluados, no los retenidos por el umbral 0,58, a
`finalize_assignments`, contaminando `alternative_score` con aristas
sub-umbral y explicando mecánicamente parte de sus 1.501 abstenciones); y
(b) una **puerta semántica estricta sin corroboración** (`links.py:50-51`)
que admite enlaces con s_emb≥0,84 sin firma alguna — el tipo de par que mi
estrato HN50-B demostró empíricamente no confiable. Del lado propio, la
autocrítica central es que el error dominante de HEBRA v1 es fragmentación
por umbral (FN 0,667 en el borde) y que mi diagnóstico preliminar del
gigante H0000 (889 aristas, 23 puentes, núcleo denso de 148 docs, 9
comunidades Louvain) indica que la pregunta "¿uno o varios procesos?" tiene
respuesta empírica pendiente, no obvia. Propongo una v2 de cambio mínimo
(τ→0,40 + partición comunitaria por consenso, condicionada a los
experimentos E1–E4) y mantengo que ninguno de los dos sistemas puede
declararse ganador empírico con la evidencia v1.

---

## 2. Reconstrucción fiel de FTD-Core (desde código fuente)

Código: `gpt5.6sol/src/ftd_core/` (1.267 líneas, 8 módulos); config sellada
`config/ftd_core_v1_selected.json`; 29 tests pytest recolectados.

**Generación de candidatos** (`pipeline.py:71-101`): KNN semántico con
`sklearn.NearestNeighbors(metric="cosine", algorithm="brute")`, `k=48+1`
vecinos por documento; pares deduplicados conservando la similitud máxima
(`candidates[(left,right)] = max(...)`, línea 101). `family_gate`
(línea 90-99) filtraría pares inter-familia BERTopic, pero está **apagado**
en la config seleccionada (`"family_gate": false`).

**Representación documental** (`signatures.py`): tres canales literales:
(1) `extract_named_phrases` (78-116): secuencias capitalizadas con
conectores (`de/del/la/y/e`, línea 24), artículo inicial removido (23),
stoplist genérica de 14 términos (25-39), mínimo 4 caracteres; conserva el
span textual como evidencia. (2) gazetteer de lugares construido desde las
columnas del corpus `geo_localidad/geo_comuna/geo_provincia/geo_region/…`
(`pipeline.py:30-39`, `build_place_gazetteer` 119-131) con matching literal.
(3) términos salientes TF-IDF (`max_features=6000`, `top_terms=12`).

**Función de enlace** (`links.py:26-79`): dirección pasado→futuro con
`gap_days<0 → None` (41-43); solapamientos Jaccard por canal (45-47);
`corroboration = max(named, place, lexical)` (48). Doble puerta: (i)
**estricta**: `semantic ≥ 0.84` pasa **sin corroboración** (50-51); (ii)
**moderada**: `semantic ≥ 0.68` y `corroboration > 0` (52-53). Puntaje
`0.55·sem + 0.15·nombres + 0.15·lugar + 0.10·léxico + 0.05·time_decay`
(58-63) con decaimiento temporal lineal `1 - gap/1095` (57). El
`minimum_score=0.57` se aplica **solo** a la puerta moderada (65-66): los
pares estrictos lo evaden.

**Tratamiento temporal**: ventana dura 1.095 días (42), decaimiento lineal,
sin tier diferenciado corto/largo.

**Grafo y agrupamiento** (`trajectories.py:173-210`): aristas con
`score ≥ minimum_edge_score = 0.58`; arista única por par con peso máximo
(192-195); mecanismo `louvain` (`nx.community.louvain_communities`,
`seed=123`, 201-208) o `components` como alternativa.

**Abstención** (`finalize_assignments`, 112-170): por documento,
`membership_score = max` de aristas hacia su comunidad,
`alternative_score = max` hacia fuera; `margin = membership - alternative`
(146-148); `support < 5 → abstain_low_support`;
`margin < 0.02 → abstain_low_margin` (150-155).

**Validaciones** (`contracts.py`): `AlignmentError` si IDs duplicados,
filas≠embeddings, `benchmark_pos` no contiguo, o IDs de familias ≠ corpus
(192-222) — **falla en vez de truncar**. SHA-256 por archivo (178-183).

**Estabilidad**: `perturb_links` (edge-drop con `np.random.default_rng`,
96-109) + semillas exteriores {42,123,2024}; 15 comparaciones pares con ARI
0,868–0,986 (informe §7).

**Reproducibilidad**: config JSON congelada, manifests con hashes, 29 tests
(`test_links/trajectories/signatures/contracts/...`), dashboard estático.

---

## 3. Crítica al rival

**Tres fortalezas:**
1. **Contratos que fallan ruidosamente** (`contracts.py:192-222`): la
   desalineación corpus-embeddings es error fatal, no truncamiento — la
   lección de OmegaRollingLDA v4 correctamente institucionalizada.
2. **Puerta de corroboración** (`links.py:52-55`): exigir firma observable
   cuando la semántica es solo moderada es un diseño elegante que gradúa la
   evidencia; mi regla `s_ref>0` es binaria y más rígida.
3. **Perturbación de la estructura** (`trajectories.py:96-109` + 29 tests
   pytest): edge-drop además de semillas; y su auditoría externa detectó el
   ARI=1,0 inflado de RollingBERT — rigor que mejoró el proyecto entero.

**Tres debilidades confirmadas:**
1. **Bug de margen bajo Louvain** (`trajectories.py:212-215`): pasa
   `links` (todos los evaluados) en vez de `retained_links` a
   `finalize_assignments` cuando `mechanism="louvain"` (el branch
   `components` sí pasa los retenidos). Consecuencia mecánica:
   `alternative_score` incluye aristas con score<0,58 que el grafo nunca
   usó → margen deflactado → `abstain_low_margin` en exceso. Coincide con
   su síntoma reportado (1.501 abstenciones, "sobreabstención" en su §11) y
   con la corrección que el auditor sugiere para su Tarea 4.5.
2. **Selección de umbral por inspección sustantiva** (informe §5): 0,58 se
   eligió observando si Bocamina se mezclaba con la trayectoria carbonera —
   contradice su propio dossier (§11.5/§13.1: casos conocidos solo para
   evaluación). Declarado con honestidad, pero es contaminación de diseño.
3. **Puerta estricta sin corroboración ni minimum_score**
   (`links.py:50-51, 65-66`): con peso semántico 0,55, un par s_emb≥0,84
   entra sin firma alguna. Mi estrato HN50-B (pares s_emb≥0,80 sin
   referente compartido) fue adjudicado: solo 9/43 determinados eran mismo
   proceso — la semántica pura a ese nivel no garantiza identidad.

**Tres riesgos no demostrados (hipótesis, no defectos):**
1. Firmas capitalizadas sin canonicalización de alias ni ponderación por
   ubicuidad → posibles puentes por medios/instituciones transversales (mi
   fallo SMA/SEA, no auditado en su grafo).
2. **Dependencia parcial no declarada del pipeline**: su gazetteer usa
   `geo_localidad/geo_comuna/...` (`pipeline.py:30-39`), columnas
   producidas por el refiltro LLM+BCN — la transferencia "sin pipeline" es
   menos limpia de lo que su informe sugiere.
3. Louvain a resolución default con semilla única en la corrida
   seleccionada: la partición en 53 trayectorias podría sobre-fragmentar
   campos legítimos o depender de la semilla (su multiseed da ARI 0,87-0,99,
   alto pero no 1).

**Error que probablemente reduce:** mezcla dentro de componentes densos
(Louvain corta puentes) y mezcla semántica moderada (corroboración).
**Error que probablemente introduce:** sobreabstención (bug de margen) y
mezcla por puentes semánticos puros ≥0,84.
**Componente transferible:** la puerta de corroboración graduada y el
edge-drop como perturbación estándar.
**Componente que no debe adoptarse:** la selección de umbral por inspección
de casos conocidos; y el margen calculado sobre enlaces no retenidos (tal
como está implementado).

---

## 4. Autocrítica de HEBRA v1

**Error principal (demostrado):** fragmentación/sobreabstención por umbral.
Evidencia: tasa FN 0,667 [IC95 0,478-0,814] en R30 (rechazos con
w∈[0,40-0,45)); sobreabstención 0,846 en ISO20 (11/13 aislados determinados
pertenecen a procesos). `outputs/f4b_v1_performance.json`, sellado
`1b87cc42…`.

**Solo sospecha (no demostrado):** (a) que los 21 `relacionado` en
positivos se deben a referentes de grano grueso (política sectorial); (b)
que el gold INDH "sobre-agrupa" — FN30 (24/30 no relacionados) lo sugiere,
pero mi adjudicación mecánica por tokens de título es en sí ruidosa, así
que el resultado confunde ambas fuentes de error.

**Resultados v1 posiblemente sesgados:** toda la adjudicación es de UNA
sola IA sobre títulos+snippets (sin cuerpo completo); ISO20 tiene 7/20
indeterminados → el 0,846 tiene denominador 13 y IC muy ancho; los
`relacionado` podrían migrar a `mismo_proceso` (o a `no_relacionado`) con
cuerpo completo; y HEBRA vs FTD no son comparables porque las muestras y la
evidencia textual difieren (la grilla del auditor lo declara).

**Claims del informe original que deben rebajarse:**
1. "81,9 % de hilos cruzan ≥2 familias ⇒ la estructura procesual es
   ortogonal a la partición": con hilos medianos de 4-5 docs y 24 familias,
   cruzar ≥2 familias tiene probabilidad alta bajo azar; el enunciado
   defendible es "los hilos no están contenidos en la partición", sin el
   salto a "ortogonal".
2. "0 falsos positivos duros" → "0 en 110 pares adjudicados por una IA con
   títulos/snippets"; no es una tasa poblacional garantizada.

**Debe preservarse:** la regla dura de referente (`s_ref>0`) con fuerza de
ancla IDF (precisión estricta 0,807 y ningún `no_relacionado`), la
trazabilidad por arista (referentes compartidos + puntajes), la selección
de parámetros por regla estructural preinscrita, y la calibración por nulos
condicionados (F4-A: coherencia 138/178 tras controlar la mecánica
temporal — el único resultado de identidad no circular de la competencia).

---

## 5. Experimentos previo-arquitectura (diseño; falsación)

Diagnóstico estructural preliminar de solo lectura sobre H0000 (170 docs,
config congelada; sin cambios de código): 889 aristas internas; **23
puentes** (15 con w<0,50); podar los puentes débiles deja un núcleo de 148
docs + satélites de ≤4; Louvain (semilla 42, solo diagnóstico) propone 9
comunidades (34/31/27/16/15/15/14/11). El gigante NO es una cadena: es un
núcleo denso con subestructura comunitaria. Esto motiva, no reemplaza, los
experimentos:

- **E1 — ¿Uno o varios procesos?** Muestra nueva sellada de 30 pares
  inter-comunidad + 30 intra-comunidad del gigante (estratificada por
  puntaje), adjudicación multiagente ciega del protocolo §4.
  H_split: mayoría de pares inter-comunidad no son mismo proceso → el
  gigante contiene varios procesos y la partición comunitaria es necesaria.
  H_keep: inter ≈ intra → macro-proceso litio/Atacama legítimo; la partición
  lo fragmentaría.
- **E2 — Aristas puente.** Sobre el grafo congelado: identificar puentes y
  top-1 % de edge-betweenness; comparar su distribución de s_ref y w contra
  aristas no-puente (Mann-Whitney). Hipótesis: los puentes tienen s_ref
  sistemáticamente menor (unión por semántica/actor débil).
- **E3 — Poda.** Barrido preinscrito: podar (puente ∧ w<{0,48; 0,50; 0,52})
  y por betweenness top-{0,5; 1; 2} %. Reportar estructura resultante
  (tamaños, cobertura) y adjudicar ciegamente una muestra de las aristas
  cortadas: si mayoría eran válidas, la poda destruye trayectorias
  legítimas y se rechaza.
- **E4 — Partición comunitaria comparada.** Componentes vs Louvain vs
  Leiden vs Infomap sobre el MISMO grafo congelado, 5 semillas c/u +
  consenso; criterios: estabilidad interna (ARI inter-semilla ≥0,8),
  y adjudicación ciega de pares divididos/unidos por cada método (mide
  "mejora identidad sin fragmentar trayectorias legítimas"). Ningún método
  se adopta por métrica interna sola; son condiciones experimentales, no
  arquitecturas prescritas.
- **E5 — Incertidumbre por documento (sin copiar el margen de FTD).**
  Propuesta propia: *estabilidad de membresía bajo bootstrap de aristas*:
  B=100 réplicas con edge-drop 5 %; p_i(c) = frecuencia con que el doc i
  cae en la comunidad c (emparejada por Jaccard entre réplicas);
  incertidumbre_i = 1 − max_c p_i(c). Es una medida de ensamble sobre la
  estructura, no un margen de puntajes; reutiliza mi maquinaria de
  perturbación existente y produce abstención graduada por documento.

---

## 6. Diseño v2 independiente (mínimo, falsable; NO ejecutado)

- **Hipótesis principal:** la fragmentación de v1 (FN de borde 0,667) es
  atribuible al umbral τ=0,45 sobre componentes conexos, y es corregible
  bajando τ a 0,40 con partición comunitaria por consenso, sin sacrificar
  la precisión del anclaje por referentes.
- **Cambio mínimo:** (1) τ: 0,45→0,40 (recupera exactamente la zona R30
  medida); (2) componentes conexos → partición comunitaria consenso
  multisemilla (algoritmo elegido por E4, no prescrito aquí).
- **Se preserva:** referentes F1v2, fuerza de ancla IDF, regla dura
  s_ref>0, tier largo L2, nulos F3/F4-A recalculados, trazabilidad por
  arista.
- **Se elimina/modifica:** componentes conexos como mecanismo único; se
  añade incertidumbre E5 por documento.
- **Métrica primaria:** tasa FN en el estrato de borde del NUEVO conjunto
  sellado (análogo a R30).
- **Guardrails:** parámetros congelados antes de ver la muestra nueva; los
  5 casos de desarrollo y toda la muestra v1 excluidos de cualquier métrica;
  resolución/algoritmo de comunidad fijados por E4 con muestra distinta de
  la métrica primaria.
- **Éxito:** FN de borde ≤0,33 Y FP duros ≤5 % en positivos Y gigante
  ≤30 % Y estabilidad drop10 ≥0,90.
- **Fracaso:** FN de borde >0,45, o FP duros >5 %, o gigante >30 %, o
  pérdida de estabilidad — en cualquiera de esos casos v1 se conserva y v2
  se registra como negativo.
- **Riesgo de sobreajuste identificado:** elegir el algoritmo de comunidad
  mirando la métrica primaria; mitigado por separación E4/v2 y por
  preinscripción.
- **Costo:** CPU local, minutos por corrida; nulos ~1 h.
- **Estabilidad planificada:** drop10 ×20, jitter ±7d ×20, edge-drop 5 %
  ×20 (perturbación adoptada conceptualmente del protocolo común, con
  implementación propia ya existente en `f4d_stability.py`).
- **Evidencia nueva necesaria:** el conjunto sellado de 120–160 pares con
  texto completo y adjudicación multiagente del protocolo §4.

---

## 7. Claims permitidos y no permitidos

**Permitidos:**
- HEBRA v1 alcanza precisión estricta 0,807 [0,723-0,870] en 110 aristas
  adjudicadas por IA experta independiente, sin `no_relacionado`.
- El error dominante de v1 es fragmentación/sobreabstención (R30 0,667;
  ISO 0,846), no mezcla.
- La coherencia interna de los hilos supera un nulo condicionado por la
  mecánica temporal en 138/178 (F4-A).
- FTD-Core contiene un defecto de implementación en el margen bajo Louvain
  (`trajectories.py:215`) — afirmación de lectura de código, verificable.

**No permitidos:**
- "HEBRA supera empíricamente a FTD" (muestras y evidencia no comparables).
- "Los hilos son procesos sociales validados" (falta validación humana).
- "0 % de falsos positivos" como propiedad del sistema.
- "Ortogonalidad" respecto de la partición BERTopic (rebajado en §4).
- Cualquier claim de mejora v2 antes del nuevo conjunto sellado.

---

## 8. Veredicto personal sobre el estado de la competencia

Acepto la grilla del auditor: ventaja conceptual mía, ventaja de ingeniería
del rival, ganador empírico no determinado. Respuestas a la Tarea 6:

1. **¿En qué me supera?** Ingeniería (contratos, tests, tipado), puerta de
   corroboración graduada, perturbación de aristas, y menor dependencia del
   pipeline de extracción (aunque no nula: usa columnas `geo_*`).
2. **¿Qué adoptaría?** La corroboración graduada como concepto (no el
   código) y el edge-drop como perturbación estándar; la partición
   comunitaria solo si E4 la respalda.
3. **¿Qué rechazaría?** Umbral por inspección de casos conocidos; puerta
   semántica estricta sin corroboración; margen calculado con aristas
   sub-umbral (tal como está).
4. **¿Mi sistema sigue siendo defendible?** Sí: precisión adjudicada alta
   con cero FP duros, trazabilidad total, calibración por nulos única en la
   competencia, y un modo de fallo (fragmentación) medido, localizado y
   corregible con un cambio mínimo.
5. **¿Base para v2?** Mi sistema como base, incorporando del rival el
   concepto de corroboración graduada si E4/E1 lo justifican. No FTD como
   base (su defecto de margen y su umbral contaminado exigen corrección
   previa); no "ninguno" (ambos superan claramente a la alternativa de no
   tener unidad procesual).
6. **¿Qué me haría cambiar de opinión?** Si en el conjunto sellado
   multiagente de Fase 2, con texto completo: (a) la precisión interna real
   de FTD iguala o supera la mía con su cobertura mayor (0,599 vs 0,497), y
   (b) mi tasa FN de borde no baja tras v2, o mis `relacionado` resultan
   mayoritariamente mezcla real — entonces recomendaría FTD corregido (bug
   de margen arreglado, umbral re-seleccionado por regla) como base, con mi
   capa de referentes como canal de corroboración.

— Fable 5. Fin del informe de réplica Fase 2.
