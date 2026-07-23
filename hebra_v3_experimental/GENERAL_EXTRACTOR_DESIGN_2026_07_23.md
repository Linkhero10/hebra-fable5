# HEBRA v3 EXPERIMENTAL — extractor general de objetos procesuales

Fecha: 2026-07-23. **No modifica HEBRA v2** (congelado en
`../hebra_v2_experimental/FROZEN.json`) ni la clave sellada, la hoja ciega,
ni ningún artefacto de v1. Vive enteramente en `fable5/hebra_v3_experimental/`.

**No contiene ninguna regla escrita a mano por macrohilo.** Todo lo que
sigue se explica.

## 0. El problema que este diseño resuelve

`subthread_dictionary.py` (v2, congelado) es, honestamente, un diccionario
de vocabulario propio de H0000 (regex sobre "codelco", "sqm", "maricunga",
"ceol", "salar futuro"...). El benchmark fuera de muestra ya mostró que
esto produce **0% de cobertura** en 18 macrohilos de otros temas (Dominga,
Ventanas, Bocamina, Alto Maipo, etc.) — correcto por diseño, pero inútil
para generalizar. Escribir un diccionario nuevo para cada macrohilo sería
repetir el mismo patrón a mayor escala: seguiría siendo "reglas manuales
por macrohilo", solo que con más macrohilos. El encargo pide explícitamente
lo contrario: un extractor que funcione de la misma forma en cualquier
hilo, sin enumerar sus entidades de antemano.

## 1. Hallazgo clave: el corpus YA tiene extracción general, hecha una sola vez para los 3.742 documentos

El CSV base
(`01_bases_de_datos/03_refiltro_api_qwen_y_base_actual/06_base_actual_fusionada_3742_incluidas.csv`)
contiene columnas `llm_*` que son el resultado de un proceso de anotación
por LLM corrido **una sola vez sobre todo el corpus**, antes de que
existiera H0000 o cualquier hilo — no son específicas de ningún macrohilo:

| Columna(s) del corpus | Cobertura (3.742 docs) | Categoría objetivo |
|---|---:|---|
| `llm_project_name` | 79.7% no vacío | proyecto o instalación |
| `llm_main_conflict_place_name` (+ `geo_comuna`/`geo_provincia`/`geo_region` como respaldo) | 98.5% no vacío | territorio |
| `llm_main_conflict_place_type` | mayormente poblado (locality, commune, salar, river, mine, thermoelectric, industrial_facility, company_facility, ...) | tipo de territorio (y pista secundaria de instalación cuando el lugar ES la instalación) |
| `llm_demandant_actor_name` + `llm_demandant_actor_type` | alto | organización (parte demandante) |
| `llm_demanded_actor_name` + `llm_demanded_actor_type` | alto | organización (parte demandada) |
| `llm_contentious_action_type` | 100% no vacío | contrato/consulta/litigio/procedimiento |
| `llm_contentious_action_type` + `fecha_iso` | 100% (fecha siempre presente) | evento o fase procesual (compuesto, ver §5) |

**Diseño central**: el "extractor general" no es un nuevo modelo de NLP ni
un diccionario nuevo — es un **mapeo transparente y auditable de estas
columnas ya generales a las 5 categorías pedidas**, con la MISMA
normalización determinista y genérica que `fable5/src/f1_5_normalize_referents_v2.py`
ya usa (y que ya está validada: solo funde "Nombre (SIGLA)" cuando la
sigla realmente coincide con las iniciales del nombre, con una lista de
roles genéricos como "empresa"/"proyecto"/"ministro" que nunca se aceptan
como canónico por sí solos). Se **importa esa función**, no se reimplementa
ni se modifica.

## 2. Las 5 categorías, definidas sin vocabulario de ningún macrohilo

1. **`proyecto_instalacion`**: `base_key(llm_project_name)`. Si vacío y
   `llm_main_conflict_place_type` ∈ {mine, thermoelectric,
   industrial_facility, company_facility} (tipos que indican que el LUGAR
   ES la instalación, no solo su entorno), se usa
   `base_key(llm_main_conflict_place_name)` como respaldo genérico —
   ninguna de estas reglas menciona un proyecto específico.
2. **`territorio`**: `base_key(llm_main_conflict_place_name)` con
   respaldo `geo_comuna` → `geo_provincia` → `geo_region` (idéntico al
   fallback que v1/v2 ya usaban, generalizado a cualquier documento).
   `territorio_tipo` = `llm_main_conflict_place_type` (auxiliar).
3. **`organizacion`**: conjunto de `base_key(llm_demandant_actor_name)` y
   `base_key(llm_demanded_actor_name)`, cada uno con su
   `_type` (empresa, comunidad, comunidad indígena, ONG, institución
   estatal, municipio, sindicato...) ya provisto por el LLM upstream —
   sin inventar clasificación nueva.
4. **`procedimiento`**: `llm_contentious_action_type` normalizado y
   agrupado en una **familia genérica cerrada** (no nombres propios):
   `judicial` (recurso judicial, demanda, reclamación judicial, recurso de
   protección), `administrativo_autorizatorio` (aprobación ambiental,
   permiso, resolución de calificación), `administrativo_sancionatorio`
   (sanción, multa, procedimiento sancionatorio), `participativo`
   (consulta indígena, consulta ciudadana, participación ciudadana),
   `manifestacion_publica` (protesta, declaración pública, rechazo
   formal), `acuerdo_contractual` (acuerdo, contrato, memorando,
   convenio), `otro`. Estas familias son géneros de acción administrativa
   /judicial reconocidos en cualquier conflicto socioambiental chileno,
   no vocabulario de un proyecto en particular — ver
   `src/general_extractor.py::PROCEDURE_FAMILIES` para la lista completa
   y auditable de palabras clave por familia.
5. **`evento_fase`**: campo compuesto **documentado como limitación, no
   resuelto de forma fuerte**: no existe en el corpus una columna
   dedicada de "fase procesual". Se aproxima como
   `f"{familia_procedimiento}::{fecha_iso[:7]}"` (familia + año-mes), que
   permite distinguir instancias temporales de un mismo tipo de
   procedimiento dentro de un proyecto, pero **no es una extracción
   semántica de fase real** (p. ej. no distingue "primera audiencia" de
   "sentencia final" dentro de un mismo litigio). Se dejó así en vez de
   inventar una taxonomía de fases sin respaldo en los datos.

## 3. Por qué esto NO es "reglas manuales por macrohilo"

- Ninguna palabra clave usada (en la lista de familias de `procedimiento`
  o en el fallback de `proyecto_instalacion`) es un nombre propio de
  proyecto, empresa, salar o comuna. Son sustantivos comunes del español
  administrativo/judicial chileno ("recurso", "sanción", "consulta",
  "protesta", "acuerdo"...), aplicables idénticamente a Dominga, Ventanas,
  Bocamina, el acuerdo Codelco-SQM, o cualquier hilo futuro.
- La canonización de `proyecto_instalacion`/`territorio`/`organizacion`
  reutiliza `base_key()` + la lógica de aceptación de siglas por
  iniciales de f1v2 — ya validada de forma general sobre los 3.742
  documentos, no reescrita para este ejercicio.
- No se abre ni se lee ningún archivo de un macrohilo específico para
  decidir las reglas: el módulo se escribe una sola vez contra el
  esquema de columnas del corpus, no contra el contenido de H0000, Dominga
  o Ventanas.

## 4. Agrupación (subhilo general)

Reemplaza la función de `subthread_dictionary.canonicalize()` (v2) por
`proyecto_instalacion` ya canonizado como clave de subhilo — sin tabla de
regex. Un documento sin `proyecto_instalacion` (ni respaldo de
`territorio_tipo`) abstiene explícitamente
(`SIN_PROYECTO_INSTALACION_IDENTIFICADO`), igual que en v2, por el mismo
principio: preferir abstención a asignación inventada.

## 5. Limitaciones declaradas de este diseño

- Depende enteramente de la calidad de las columnas `llm_*` ya presentes
  en el corpus. Si esas columnas tienen sesgos o errores de la extracción
  LLM original (fuera del control de este ejercicio), el extractor v3 los
  hereda. No se auditó aquí la calidad de esa extracción upstream.
- `evento_fase` es la categoría más débil (ver §2.5): un compuesto
  familia+fecha, no una fase semántica real.
- `organizacion` no distingue todavía "empresa privada" de "empresa
  estatal" más allá de lo que el propio `_type` del LLM ya distinga.
- Este extractor NO reemplaza ni reinterpreta ninguna decisión de v2 sobre
  H0000 — es una vía paralela, evaluada de forma independiente en la
  Fase de validación fuera de muestra (ver
  `OUT_OF_SAMPLE_VALIDATION_V3_2026_07_23.md`).
