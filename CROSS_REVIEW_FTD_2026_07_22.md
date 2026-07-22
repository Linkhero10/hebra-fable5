# Réplica cruzada: FTD-Core (GPT-5.6 Sol) vista desde HEBRA v1 — Fable 5

Fecha: 2026-07-22. Escrito DESPUÉS de congelar
`V1_PERFORMANCE_FINAL_2026_07_22.md` (SHA `1b87cc42642bfcef…`). Sin
modificar código, parámetros ni resultados. Sin diseñar ni ejecutar
ensemble. La adjudicación v1 no se usará para ajustar una v2 evaluada en la
misma muestra.

## 1. Reconstrucción fiel del método rival

**FTD-Core** (`gpt5.6sol/`; config sellada `ftd_core_v1_selected.json`):

1. **Firmas documentales literales por documento**: frases capitalizadas del
   texto (entidades nominales sin NER ni LLM), lugares por gazetteer
   literal, términos TF-IDF (max 6.000 features). Todo con span de origen;
   sin relleno generativo.
2. **Candidatos**: 48 vecinos semánticos más cercanos por embedding, con
   ventana temporal máxima de 1.095 días.
3. **Puntuación de enlace**: `0,55·semántica + 0,15·nombres + 0,15·lugar +
   0,10·léxico + 0,05·proximidad temporal`; umbral de arista 0,58.
4. **Partición**: comunidades **Louvain** sobre el grafo (semilla 123), no
   componentes conexos; `family_gate=false` (BERTopic solo diagnóstico).
5. **Abstención por documento**: soporte <5 o margen <0,02 → no asignado.

Resultado seleccionado: 53 trayectorias, cobertura 0,599 (1.501
abstenciones), cohesión 0,891, margen 0,029; ARI perturbado (semillas 3× +
edge-drop 5 % 3×, 15 pares) 0,868–0,986. Su revisión ciega provisional
(propia): 19/20 pares internos mismo proceso; frontera 6/20; abstinentes
15/20 mismo proceso. Adjudicación externa GPT-5.6 sobre sus 60 pares: 36
mismo / 22 relacionado / 2 no relacionado (estratos mezclados; no comparable
1:1 con mis 110 positivos puros — muestreos distintos).

Auditoría valiosa colateral suya: el ARI=1,0 de RollingBERT está inflado por
semillas internas fijas (`[42,123,456,789,…]`) — refutación correcta de una
métrica publicada del proyecto.

## 2. Tres aspectos donde FTD-Core supera a HEBRA v1

1. **Firmas independientes del pipeline LLM.** Sus referentes salen del
   texto crudo (capitalización + gazetteer + TF-IDF). HEBRA depende de las
   columnas `llm_*` del refiltro: si un corpus nuevo no tiene esa
   extracción, HEBRA necesita F0–F1 completos. FTD transfiere a cualquier
   corpus fechado sin dependencia previa — mi requisito de transferencia
   (§9 de la propuesta) lo cumple mejor él.
2. **Partición por comunidades en vez de componentes conexos.** Louvain
   corta puentes dentro de componentes densos; mi único control del efecto
   cadena fue IDF + umbral, y me costó el gigante del 22–25 % en F2 base.
   Además su margen documento-nivel produce una abstención graduada; mi
   abstención es binaria (sin referente o bajo umbral).
3. **Perturbación de estructura, no solo de datos.** Su estabilidad incluye
   edge-drop 5 % (perturbación del grafo mismo) además de semillas; yo
   perturbé documentos y fechas pero no aristas. Y su hallazgo sobre
   RollingBERT demuestra mejor olfato para métricas infladas.

## 3. Tres debilidades o riesgos metodológicos de FTD-Core

1. **Selección de umbral por inspección sustantiva de casos conocidos.** El
   0,58 se eligió mirando si Bocamina se mezclaba con la trayectoria
   carbonera (§5 y §11 de su informe, declarado honestamente). Eso es
   ajuste contra los casos reservados que su propio dossier prohíbe (§13.1).
   Mi τ salió de una regla estructural preinscrita ciega a contenido.
2. **Firmas literales sin canonicalización ni ponderación por ubicuidad.**
   Cobertura nominal 0,9995 con frases capitalizadas admite ruido (medios,
   secciones, instituciones transversales). No hay auditoría de alias ni
   IDF sobre firmas — exactamente el fallo que en HEBRA produjo el
   mega-hilo SMA/SEA y que corregí en F1.5/F2b. Su peso semántico dominante
   (0,55) agrava el riesgo: mis HN50 tipo B mostraron pares con s_emb≥0,80
   sin relación procesual alguna.
3. **Sin calibración contra nulos.** Ninguna de sus 53 trayectorias tiene
   contraparte nula (ni simple ni condicionada); sus "ablaciones" son de
   configuración y él mismo reconoce que no aíslan contribución causal. La
   cohesión 0,891 no distingue identidad procesual de proximidad
   semántico-temporal mecánica — la crítica que F4-A me obligó a resolver.

## 4. Qué errores de mi v1 podría resolver FTD

- **Fragmentación por umbral (mi error dominante: FN 0,667 en R30).**
  Louvain tolera umbrales más bajos sin fusión en gigante: la zona R30
  (w∈[0,40-0,45)) podría entrar al grafo y ser separada por comunidades en
  vez de excluida.
- **Sobreabstención en aislados (0,846).** Muchos de mis aislados
  probablemente carecen de referente extraído por el refiltro; sus firmas
  literales (capitalización/gazetteer) les darían canal de anclaje.
- **Dependencia del pipeline LLM para transferencia.**

## 5. Qué errores introduciría

- **Mezcla campo-de-conflicto vs proceso**: su frontera adjudicada y sus
  propias trayectorias largas ("pueden representar campos de conflicto, no
  un proceso único", §11) — el precio del peso semántico 0,55. Mi v1 tiene
  0 falsos positivos duros; adoptar su puntuación los reintroduciría.
- **Puentes por entidades ubicuas no ponderadas** (riesgo SMA/SEA).
- **No determinismo de Louvain** (mitigable con semillas, pero mis
  componentes son deterministas por construcción).

## 6. Un componente que vale la pena adoptar

**La partición por comunidades (Louvain/Leiden) con margen documento-nivel,
aplicada sobre MI grafo anclado en referentes.** Ataca directamente mi error
dominante (fragmentación por umbral) sin ceder la regla dura `s_ref>0` que
me dio 0 FP duros. Es un solo componente, mecánico, auditable y compatible
con mi calibración de nulos.

## 7. Un componente que debe rechazarse

**La selección de umbral por inspección de casos conocidos.** Es la vía más
directa de contaminación: convierte los casos de evaluación en reglas de
diseño. Cualquier v2 mía mantiene selección por regla estructural
preinscrita o por conjunto de desarrollo sellado, nunca "miré si Bocamina se
mezclaba".

## 8. Propuesta v2 mínima y falsable (NO ejecutada)

**HEBRA v2 = grafo F1v2/IDF idéntico + τ reducido a 0,40 + partición
Louvain multisemilla (consenso) en lugar de componentes + abstención por
margen de pertenencia a comunidad.** Un solo cambio estructural (partición)
y un solo cambio de parámetro (τ), ambos motivados por errores medidos en
v1 (R30, ISO20) — no por estética.

- **H1(v2):** v2 recupera ≥50 % de los falsos negativos de borde (tasa tipo
  R30 baja de 0,667 a ≤0,33) manteniendo FP duros ≤5 % en positivos y
  gigante ≤30 %.
- **H0(v2):** la recuperación no ocurre o la mezcla sube sobre 5 %.
- **Evaluación:** EXCLUSIVAMENTE sobre un conjunto sellado nuevo (semilla
  nueva, estratos análogos a F4-B, sellado antes de correr v2). La muestra
  v1 queda quemada: solo sirve como diagnóstico, jamás como métrica de
  mejora.
- Los nulos F3/F4-A se recalculan para v2 con las mismas reglas congeladas.

## 9. Condiciones de decisión

| Decisión | Condición |
|---|---|
| **Mantener HEBRA** | La prioridad es precisión de identidad y trazabilidad por referente estructurado (0 FP duros; auditoría de alias completa) y el dominio tiene extracciones disponibles; la validación humana confirma la precisión IA (≥0,75 estricta). |
| **Adoptar FTD** | La prioridad es transferencia inmediata a corpus sin pipeline de extracción, o la revisión humana muestra que su precisión interna real ≈ la mía con su cobertura mayor (0,599 vs 0,497) y su mezcla de frontera resulta aceptable tras canonicalizar firmas. |
| **Combinar** | Solo si la matriz de complementariedad documento-a-documento (sus mezclas de frontera vs mis FN de borde) muestra errores disjuntos, y el combinado supera a AMBOS en un holdout que ninguno usó. No antes; no está diseñada aquí. |
| **Descartar ambos** | Si la validación humana (no IA) da precisión estricta <0,7 para los dos, o si ninguno supera en utilidad sociológica a familias+OmegaEvolve-S en revisión ciega de trayectorias. |

## 10. Nota de simetría

Ambos sistemas convergieron independientemente en: unidad = proceso (no
tópico), enlaces documentales auditables, ventana 1.095 días, abstención
explícita, sin LLM en el bucle, casos conocidos solo para evaluación. Esa
convergencia es evidencia (débil pero real) de que el desplazamiento
tópico→proceso es la decisión correcta del problema, cualquiera sea el
ganador. Diferencia esencial: FTD apuesta a firmas literales +
comunidades semánticas; HEBRA a referentes estructurados + nulos de
calibración. Son complementarios por diseño, pero probar eso exige el
protocolo del §9, no un ensemble prematuro.
