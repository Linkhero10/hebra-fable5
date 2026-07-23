# Benchmark fuera de muestra de HEBRA v2 (congelado)

Ver primero `../FROZEN.json` — HEBRA v2 experimental (código +
diccionario) está congelado desde el commit `7fa8d37`. Nada en esta
carpeta lo modifica; todo lo de aquí solo **importa y reutiliza** las
funciones ya congeladas.

## Contenido

- `OUT_OF_SAMPLE_BENCHMARK_REPORT.md` — resultado de correr HEBRA v2
  (sin cambios) sobre 18 macrohilos distintos de H0000: **0% de cobertura
  en los 18**, con interpretación completa de por qué y qué significa.
- `FTD_HEBRA_COMMON_BENCHMARK_SPEC.md` — especificación de lo que haría
  falta para comparar HEBRA v2 contra FTD de forma común (unidad de
  análisis, mapeo de categorías, datos faltantes). No ejecutada.
- `src/prepare_thread_inputs.py` — adaptador de datos: construye, para
  cualquier `thread_id`, los mismos insumos (`nodes`/`edges`) que
  `build_hierarchy.py` espera, replicando el método de
  `h0000_diagnostics.py` (sin inventar reglas nuevas).
- `src/run_benchmark.py` — corre el código congelado sobre los 18 hilos
  seleccionados y calcula cobertura, fragmentación, sobreagregación
  (proxy) y abstención.
- `src/compare_with_ftd_skeleton.py` — esqueleto del benchmark contra FTD.
  **No se ejecuta como parte de este entregable** (requiere decisiones
  documentadas en la especificación); se deja listo para correr cuando
  esas decisiones se tomen.

## Reproducción

```bash
cd fable5/hebra_v2_experimental/out_of_sample_benchmark/src
python run_benchmark.py            # verifica el congelamiento y corre los 18 hilos
python compare_with_ftd_skeleton.py  # opcional: comparacion estructural descriptiva
                                       # FTD-trajectory vs HEBRA-macrohilo (no un veredicto)
cd ..
python build_manifest_lock.py       # manifest + lock de esta carpeta
```

## Resultado en una frase

Con el diccionario congelado en H0000, **HEBRA v2 no generaliza a
macrohilos de otro tema**: cobertura 0% en los 18 hilos probados (Dominga,
Fundición Ventanas, H2 Magallanes, Bocamina, Alto Maipo, HidroAysén, El
Mauro, Faro del Sur, ENAP Aconcagua y otros). Esto es el comportamiento
correcto de un diccionario específico de corpus frente a vocabulario que
nunca vio — no un error — pero significa que **no hay todavía evidencia de
que el mecanismo de subhilo generalice**, y por lo tanto no hay base para
declarar a HEBRA superior a nada fuera de H0000.
