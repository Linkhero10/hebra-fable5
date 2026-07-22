# F3 — Informe de calibración contra nulos (HEBRA)

Fecha: 2026-07-22. Configuración congelada: hilos `f2b_idf_v2_L2` (IDF,
F1v2, τ=0,45, tier largo L2). Hilos evaluados: 178 (≥3 docs). B=200;
semillas N1=20260731, N2=20260732. Criterio: p empírico Phipson-Smyth,
BH-FDR q≤0,05 por familia de señal. Distribuciones nulas completas en
`f3_null_distributions.npz`; resultados por hilo y hashes de insumos en
`f3_null_calibration.json`.

## Resultado principal

| Familia | Nulo | Cola | Hilos significativos (BH) |
|---|---|---|---|
| duration_corta (concentración episódica) | N2 | less | **120 / 178 (67,4 %)** |
| duration_larga | N2 | greater | 0 |
| peak_share trimestral | N2 | greater | 0 |
| peak_share semestral (sensibilidad) | N2 | greater | 0 |
| max_gap (latencia) | N2 | greater | 0 |
| reaparición (derivada) | N2 | — | 0 |
| burst30 (ráfaga intranual) | N1 | greater | 0 |
| gap_corto intranual | N1 | greater | 0 |

**Positivo:** la única señal que sobrevive corrección es la concentración
temporal episódica: 120 hilos son significativamente más compactos que
pseudo-hilos aleatorios de igual tamaño, incluidos todos los procesos
grandes (H0000 litio q=0,010; H0001 Dominga q=0,010 pese a durar 9 años;
H0002 Ventanas; H0004 Bocamina; H0006 HidroAysén). Los hilos son procesos
temporalmente acotados, no agrupamientos difusos — el prerequisito de
cualquier lectura procesual.

**Negativos (igual de importantes):**

1. *Latencia y reaparición no son falsables contra N2 tal como se definió*:
   los pseudo-hilos aleatorios pequeños tienen brechas internas enormes, así
   que ninguna brecha real es significativamente *mayor* que el nulo. Una
   prueba de latencia necesitaría un nulo condicionado (duración fija o N2b
   por grado de referente, registrado como extensión futura, **no
   seleccionado ahora**).
2. *peak_share es anticonservador bajo crecimiento del corpus*: un doc nulo
   caído en un año de baja cobertura (2000–2013, <50 docs/año) produce
   cuotas enormes, mientras los hilos reales viven en años de alto volumen.
   La normalización por share evita confundir crecimiento con señal, pero a
   costa de potencia. Resultado negativo documentado, no ajustado post-hoc.
3. *Señales intranuales sin potencia al tamaño mediano* (4 docs): burst30 y
   gap_corto no separan del nulo N1 tras BH. Con hilos chicos, N1 no puede
   licenciar afirmaciones de ráfaga.

## Hilos sin señal respaldada

58 / 178 (32,6 %): tamaño mediano 3 docs, duración mediana 814 días. La
abstención es el comportamiento de diseño: esos hilos no soportan ninguna
afirmación procesual y quedan como agrupaciones documentales sin calificar.

## Sensibilidad de unidad

Trimestre y semestre producen el mismo veredicto (0 significativos en
peak_share). Mensual se omitió: mediana de hilo 4 docs, celdas casi vacías.

## Advertencias obligatorias

- N1 licencia solo afirmaciones intranuales; no prueba emergencia ni
  reaparición multianual.
- N2 es un nulo **conjunto** referentes+tiempo, no temporal puro; no se
  afirma que la temporalidad por sí sola explique nada.
- Años de baja cobertura (<50 docs): 2000–2013 completos.
- El corpus triplica su volumen 2022→2025; toda cuota es proporción del
  periodo.
- Ningún parámetro se modificó mirando los cinco casos contaminados; F3 no
  tuvo etapa de ajuste.

## Consecuencia para F4

Las afirmaciones publicables por hilo quedan limitadas por ahora a:
(a) existencia del hilo (enlaces auditables por referente), y (b)
concentración episódica significativa. Emergencia, latencia y reaparición
requieren el nulo condicionado (N2b) o evaluación humana — pasan a F4 como
preguntas abiertas, no como claims.
