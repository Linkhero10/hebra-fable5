# HEBRA v3 EXPERIMENTAL — extractor general de objetos procesuales

**No modifica `hebra_v2_experimental/` (congelado).** Es una vía paralela
e independiente. Ver `GENERAL_EXTRACTOR_DESIGN_2026_07_23.md` para el
diseño completo y `OUT_OF_SAMPLE_VALIDATION_V3_2026_07_23.md` para el
resultado honesto (mejora fuerte en cobertura, empeora en fragmentación
frente a v2, sin validación de pureza aún).

## Idea central

En vez de un diccionario de regex escrito para el vocabulario de un
macrohilo (lo que hacía v2), v3 reutiliza columnas `llm_*`/`geo_*` **ya
extraídas de forma general por un proceso de anotación previo sobre los
3.742 documentos del corpus completo**, y las mapea a 5 categorías:
proyecto/instalación, territorio, organización, procedimiento
(contrato/consulta/litigio/administrativo), y evento/fase procesual
(compuesto, ver limitaciones).

## Archivos

- `src/general_extractor.py` — mapea una fila del corpus a las 5
  categorías. Reutiliza `base_key()` de
  `fable5/src/f1_5_normalize_referents_v2.py` por importación directa (no
  la copia ni la modifica).
- `src/build_general_subthreads.py` — agrupa documentos de un hilo por
  `proyecto_instalacion` canónico (abstención explícita si vacío),
  detecta multiasignación (vía organización compartida en aristas de peso
  alto) y cruces de puente entre subhilos — misma filosofía que v2, código
  independiente.
- `src/run_v3_validation.py` — corre lo anterior sobre H0000 + los 18
  hilos del benchmark de v2 y escribe `artifacts/v3_validation_summary.json`.
- `tests/test_v3.py` — 9 pruebas, incluida una que verifica por hash que
  `hebra_v2_experimental` sigue exactamente igual al congelamiento.

## Reproducción

```bash
cd fable5/hebra_v3_experimental/src
python run_v3_validation.py
cd ..
python -m pytest tests/ -v
python build_manifest_lock.py
```

## Resultado en una frase

Cobertura fuera de muestra: **0% (v2) → 98.8% promedio (v3)**. Pero en los
mismos hilos conocidos y coherentes (Dominga, Ventanas, Bocamina), v3
produce muchos más subhilos (5, 16 y 23 respectivamente, contra 0
evaluables en v2) porque agrupa por igualdad literal de
`llm_project_name` normalizado, sin colapsar paráfrasis ("central
bocamina" vs. "central termoelectrica bocamina" vs. "bocamina i y ii" son
subhilos distintos). **No se ha validado con adjudicación ciega si esa
fragmentación es real o excesiva** — ese es el paso pendiente antes de
decidir cualquier cosa sobre reemplazar v2 con v3.
