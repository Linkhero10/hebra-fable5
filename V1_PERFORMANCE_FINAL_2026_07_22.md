# Informe final de desempeño HEBRA v1 — CONGELADO

Fecha: 2026-07-22. Capa de evidencia: **independent_expert_ai_adjudication**
(GPT-5.6 Thinking; NO validación humana). v1 y el commit publicado quedan
congelados; ningún parámetro, código, umbral, referente ni clustering fue
modificado para este informe.

## Procedencia y hashes

- Adjudicación original (conservada intacta):
  `validacion/HEBRA_F4B_EXPERT_AI_ADJUDICATION_BLIND.json`,
  SHA-256 `fd5a7a222e65c631…` (completo en `outputs/f4b_v1_performance.json`).
- Hoja sellada: `bc73256e44f0175f…` (240 ítems, sellada antes de toda revisión).
- Integración: `src/f4b_integrate_adjudication.py`; resultados completos con
  IC en `outputs/f4b_v1_performance.json`.
- Confianza del revisor: alta 120, media 73, baja 47.

Definición estricta: solo `mismo_proceso` es positivo; `relacionado` se
reporta aparte; `indeterminado` fuera del denominador principal (sensibilidad
contándolo como error entre paréntesis).

## Positivos del sistema (aristas aceptadas; n=110)

| Estrato | n | mismo | relac. | no_rel | indet | Precisión estricta [IC95] |
|---|---:|---:|---:|---:|---:|---|
| P50 (quintiles de w) | 50 | 37 | 13 | 0 | 0 | 0,740 [0,604-0,841] |
| L30 (enlaces largos) | 30 | 27 | 3 | 0 | 0 | 0,900 [0,744-0,965] |
| U30 (borde aceptado) | 30 | 24 | 5 | 0 | 1 | 0,828 [0,655-0,924] |
| **Pooled** | 110 | 88 | 21 | **0** | 1 | **0,807 [0,723-0,870]** (sens. 0,800) |

Por quintil de w (P50): q0 7/10, q1 6/10, q2 7/10, q3 8/10, q4 9/10 — la
precisión estricta crece monotónicamente con w (los `relacionado` se
concentran en los quintiles bajos).

**Cero falsos positivos duros** (`no_relacionado`) en 110 aristas: la mezcla
observable se limita a 21 `relacionado` (19 %), mayormente en w bajo.

## Negativos del sistema

| Estrato | n | mismo (=FN) | relac. | no_rel (ok) | indet | Tasa FN det. [IC95] |
|---|---:|---:|---:|---:|---:|---|
| R30 (rechazo cercano) | 30 | **18** | 8 | 1 | 3 | **0,667 [0,478-0,814]** |
| HN50 (neg. difíciles) | 50 | 9 | 23 | 11 | 7 | 0,209 [0,114-0,352] |
| FN30 (mismo caso gold) | 30 | 2 | 4 | 24 | 0 | 0,067 [0,018-0,213] |

- **R30 es el hallazgo central: dos tercios de los candidatos rechazados
  justo bajo τ=0,45 son procesos reales.** El umbral produce fragmentación
  medible.
- FN30 valida a la inversa: 24/30 pares del mismo caso INDH son
  `no_relacionado` según el experto — confirma que la adjudicación mecánica
  del gold sobre-agrupa (un "caso" INDH no es un proceso).
- HN50 por subtipo en el JSON.

## Abstención (ISO20, documentos aislados)

n=20: `aislado_correcto` 2, `pertenece_a_un_proceso` 11, `indeterminado` 7.
**Sobreabstención determinada: 0,846** — la gran mayoría de los aislados
adjudicables pertenece a un proceso existente.

## Síntesis de errores v1

| Tipo | Evidencia |
|---|---|
| Falsos positivos duros | **0** confirmados |
| Mezcla | 21 `relacionado` en positivos (19 %), decrece con w |
| Falsos negativos | 29 confirmados (18 R30 + 9 HN50 + 2 FN30) |
| Fragmentación | tasa FN 0,667 en el borde del umbral |
| Sobreabstención | 11/13 aislados determinados pertenecen a procesos |

**Diagnóstico v1 congelado: sistema de alta precisión y recall
insuficiente.** El error dominante no es mezcla sino fragmentación y
sobreabstención inducidas por el umbral conservador y la exigencia de
referente. Cualquier v2 que ataque esto exigirá un nuevo conjunto sellado;
esta muestra queda quemada para ajuste.

— Fin del informe congelado. SHA-256 de este archivo en
`outputs/F4_MANIFEST.json` (regenerado tras el congelamiento).
