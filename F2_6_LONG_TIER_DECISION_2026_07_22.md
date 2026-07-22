# Decisión congelada: tier de enlaces largos — HEBRA

Fecha: 2026-07-22. Estado FARO: decisión de diseño registrada antes de F3.

## Regla congelada (PROMOVIDA: L2)

- `dt ≤ 365` días: arista si `w ≥ τ`.
- `365 < dt ≤ 1095` días: arista si `s_ref ≥ 0,5` **y** `w ≥ τ`
  ("reactivación anclada en referentes", doble compuerta explícita).
- `dt > 1095`: nunca.

## Evidencia de la miniablación (`outputs/f2_6_tier_comparison.json`)

| Métrica | L1 | L2 | L3 |
|---|---|---|---|
| aristas totales | 9.981 | 9.981 | 9.069 |
| aristas largas | 1.424 | 1.424 | 512 |
| hilos ≥3 | 178 | 178 | 176 |
| cobertura ≥3 (%) | 49,74 | 49,74 | 48,21 |
| gigante (%) | 4,56 | 4,56 | 4,54 |
| docs que salen de hilos vs L1 | — | 0 | 57 |
| acuerdo de pares vs L1 | — | 1,000 | 0,952 |

**L1 ≡ L2 empíricamente** (aristas idénticas, acuerdo 1,0). Explicación
mecánica: bajo puntuación IDF, `s_ref ≥ 0,5` implica
`w = 0,7·s_ref + 0,3·s_emb ≥ 0,35 + 0,3·s_emb`, y ningún par observado tiene
`s_emb < 0,33`, así que todo enlace largo L1 ya cumple `w ≥ τ = 0,45`.

Decisión por el criterio preinscrito del checkpoint: *"si L2 conserva
resultados comparables con menor riesgo, promueve L2"*. Se promueve **L2**:
resultado idéntico hoy, con la garantía explícita `w ≥ τ` que protege ante
futuros cambios de embeddings o de τ. No se eligió por atractivo de
biografías (el resultado es literalmente el mismo que L1).

**L3 queda solo como sensibilidad**, no seleccionada: elimina el 64 % de las
aristas largas y solo mueve 57 docs, pero la revisión ciega de la banda que
L3 descartaría (`s_ref ∈ [0,5, 0,6)`, 912 aristas) dio **29/30 mismo
proceso, 1 relacionado, 0 no relacionados**
(`outputs/f2_7_long_links_verdicts.json`, veredictos congelados antes de
desciegar; capa `expert_review_provisional_ai`, títulos+snippets+referentes,
no precisión general). L3 descartaría mayoritariamente enlaces válidos de
reactivación.

Nota de vacuidad: el conjunto pedido "30 enlaces L1 que L2 rechaza" es
**vacío** (L1≡L2). La muestra auditada es la zona de riesgo real más cercana:
aristas largas con `s_ref ∈ [0,5, 0,6)`, estratificadas 15/15 por 366–730 y
731–1095 días (semilla 20260722; poblaciones 578 y 334).

## Trazabilidad

Los JSON de resumen registran ahora: archivo de referentes real
(`f1v2_referents.csv`) y SHA-256 de corpus, embeddings, referentes y script
(`inputs.*_sha256` en `outputs/f2b_idf_v2_L*_threads_summary.json`).
Salidas L1/L2/L3 conservadas sin sobrescribir.

Configuración congelada para F3:
`outputs/f2b_idf_v2_L2_threads.csv` + `..._threads_summary.json`
(variante IDF, referentes F1v2, τ=0,45, tier L2).
