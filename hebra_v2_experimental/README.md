# HEBRA v2 EXPERIMENTAL — macrohilo / subhilo

Implementación **experimental** de la arquitectura jerárquica descrita en
`fable5/h0000_validation_2026_07_22/HEBRA_HIERARCHICAL_DESIGN_2026_07_22.md`.

**No sobrescribe HEBRA v1.** Solo lee (modo lectura) los artefactos
congelados de `fable5/diagnostics_h0000/` y el resultado de la validación
ciega en `fable5/h0000_validation_2026_07_22/`. Todo lo que se genera vive
en `artifacts/`.

## Qué hace

1. Toma cada documento del macrohilo H0000 (`H0000_02_NODE_METRICS.csv`,
   170 docs) y su campo `objeto` ya extraído por el pipeline v1.
2. Normaliza ese campo contra un diccionario corto y auditable de reglas de
   subcadena (`src/subthread_dictionary.py`) para asignar un
   `subhilo_primario` (p. ej. `acuerdo_codelco_sqm`,
   `proyecto_maricunga_salar_blanco`, `consulta_ceol_laguna_verde`) o dejar
   el documento en abstención explícita (`SIN_SUBHILO_ESPECIFICO`) si el
   objeto es el macro-label genérico o no matchea ninguna regla.
3. Busca asignaciones secundarias (multiasignación) vía aristas de peso
   alto (w≥0.60) cuyo `ref_objeto` compartido apunte a un subhilo distinto
   del primario del documento.
4. Detecta qué puentes estructurales (`H0000_03_EDGE_METRICS.csv`,
   columna `puente`) cruzan entre subhilos distintos.
5. Calcula cobertura y pureza usando la validación ciega ya resuelta
   (`H0000_VALIDATION_INTEGRATED_2026_07_22.json` +
   `H0000_DISAGREEMENTS_ADJUDICATED_2026_07_22.json`), **sin volver a
   adjudicar nada**.
6. Verifica, recalculando hashes, que ningún archivo de v1 fue modificado.

## Cómo reproducir

```bash
cd fable5/hebra_v2_experimental/src
python build_hierarchy.py                 # corrida canonica, seed=20260780
python build_hierarchy.py --seed 42        # otra semilla (resultado identico: el metodo es determinista, no estocastico)
python build_hierarchy.py --shuffle-input  # prueba de estabilidad ante orden de entrada
```

Salidas en `../artifacts/`:

- `node_subhilo_assignment.csv` — un renglón por documento con
  `macrohilo_id`, `subhilo_primario`, `subhilo_secundario`,
  `regla_aplicada`, `abstuvo`, `multiasignado`.
- `bridge_crossings.csv` — cada arista puente de v1 con los subhilos de
  sus dos extremos y si cruza subhilos distintos.
- `subhilo_purity_coverage.json` — cobertura, pureza estricta de subhilo,
  retención amplia entre subhilos distintos, y verificación de que v1
  sigue intacto (hashes).
- `HIERARCHY_MANIFEST.json` / `HIERARCHY_EXPERIMENT_LOCK.json` — hashes de
  todo lo generado + hashes de los inputs v1 leídos, y banderas explícitas
  (`reemplaza_v1: false`, `ganador_empirico_declarado: false`,
  `algoritmos_de_comunidad_usados_para_asignar_subhilo: false`).

## Pruebas

```bash
cd fable5/hebra_v2_experimental
python -m pytest tests/ -v
```

10 pruebas, correspondientes 1:1 a los requisitos de la Fase 6 del encargo:
reproducibilidad con semilla fija, no modificación de v1, integridad de
IDs, forma de la asignación macro/subproceso, mecanismo de multiasignación
(probado con datos sintéticos), abstenciones explícitas, ausencia de
pérdida silenciosa de documentos, estabilidad ante orden de entrada,
generación de manifest/lock, y comparación reproducible con v1 (mismo
conteo de documentos y mismo `macrohilo_id`).

## Resultado de la corrida canónica (seed=20260780) sobre H0000

- 170/170 documentos preservados, ninguno perdido.
- 112/170 (65.9%) reciben un `subhilo_primario` concreto; 58/170 (34.1%)
  quedan en abstención explícita (objeto genérico "estrategia nacional del
  litio" o no reconocido por el diccionario).
- 9 subhilos distintos detectados (más la abstención).
- **Pureza estricta de subhilo = 93.6%** sobre los 40 pares de la muestra
  ciega evaluables (ambos documentos con subhilo propio) que comparten
  subhilo — muy por encima del 66-68% que lograba el mejor algoritmo de
  comunidad (Leiden-CPM/Louvain/Infomap) usado como proxy de subproceso.
- **Retención amplia entre subhilos distintos = 100%** sobre los 9 pares
  evaluables que caen en subhilos diferentes: ninguno cae por debajo de
  `mismo_macroproceso`. La partición en subhilos no destruye la
  continuidad amplia ya demostrada a nivel de macrohilo.
- 3 de 23 puentes estructurales cruzan entre subhilos distintos, y los 3
  son cruces entre categorías muy cercanas (p. ej.
  `acuerdo_codelco_sqm` ↔ `atacama_extraccion_generica`), consistente con
  la lectura del diseño (sección 2.4): los puentes que cruzan subhilos son
  candidatos a que el diccionario esté sobre-dividiendo, no evidencia de
  error estructural.
- 0 documentos con multiasignación real en el corpus H0000 actual al
  umbral w≥0.60 (hallazgo empírico honesto, no un defecto: en este grafo,
  las aristas de peso alto con referente compartido no divergen del objeto
  propio del nodo). El mecanismo de multiasignación se prueba de forma
  aislada con datos sintéticos en la suite de pruebas.

## Qué esto NO demuestra

- No demuestra que el diccionario de normalización sea completo o libre de
  sesgo. Advertencia de contaminación explícita: quien escribió las reglas
  de `subthread_dictionary.py` (Claude Sonnet 5) es el mismo modelo que ya
  había leído y adjudicado los 104 pares ciegos en las Fases 1-3 de esta
  misma sesión. Aunque las reglas se derivan del campo `objeto` (extraído
  por v1 de forma independiente a esta arbitración) y no se ajustó ningún
  umbral mirando qué maximizaba la pureza, no puede garantizarse
  independencia total. La pureza de 93.6% debe leerse como **evidencia
  confirmatoria preliminar sobre la misma muestra**, no como validación
  fuera de muestra; una prueba real requeriría una segunda muestra ciega
  construida y adjudicada después de fijar el diccionario.
- No declara ganador frente a HEBRA v1, ni frente a FTD, ni frente a
  ninguna arquitectura previa.
- No es una solución de producción: es explícitamente `experimental`.
