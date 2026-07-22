# Nota metodológica F3 (adenda; F3 se conserva íntegro como experimento histórico)

Fecha: 2026-07-22. Esta nota corrige la interpretación de
`f3_report.md` y `f3_null_calibration.json` sin modificar sus archivos,
hashes ni distribuciones (`f3_null_distributions.npz`).

## 1. Desviación de implementación registrada

El checkpoint F2.5 describía N2 como pseudo-hilos "estratificados por
fuente". La implementación final (`src/f3_null_calibration.py`, línea
`rng2.sample(all_ids, k)`) usa **muestreo uniforme de k documentos del
corpus fechado, sin estratificación por fuente**. La fuente periodística
tiene distribución temporal propia y puede afectar duración, densidad y
cobertura de los pseudo-hilos; la versión estratificada queda para el nulo
condicionado de F4-A.

## 2. Reclasificación de `duration_corta`

`duration_corta` (120/178 hilos) queda reclasificado como **diagnóstico
estructural / sanity check**, no como claim procesual publicable. Motivo:
HEBRA construye componentes mediante enlaces locales con dt ≤ 365/1095
días, de modo que sus componentes están parcialmente predispuestos a ser
más compactos que k documentos uniformes de 2000–2026. El resultado
demuestra compactación frente a agrupamientos completamente aleatorios,
pero **no separa identidad procesual de la restricción temporal del
algoritmo** (circularidad parcial). La interpretación autorizada es:
"los componentes construidos mediante enlaces temporalmente restringidos
son más compactos que agrupaciones aleatorias de igual tamaño". La
separación entre compactación mecánica e identidad procesual real es el
objeto del nulo condicionado F4-A.

## 3. Corrección terminológica

Donde `f3_report.md` dice que `peak_share` es "anticonservador", debe
leerse **conservador / de baja potencia**: los valores extremos que los
años de baja cobertura (2000–2013) generan en el nulo hacen la prueba de
cola superior difícil de superar y reducen falsos positivos, no los
aumentan. Los cálculos no cambian.

## 4. Sin cambios de parámetros

Ningún parámetro de F2/F3 fue modificado a raíz de esta nota. La
configuración congelada (`f2b_idf_v2_L2`, τ=0,45, tier L2) sigue vigente
para F4.
