# HEBRA v3 EXPERIMENTAL — validación fuera de muestra (H0000 + 18 macrohilos)

Fecha: 2026-07-23. **HEBRA v2 experimental NO fue modificado** (ver
verificación de hash en la sección 5). Este informe corre el extractor
general nuevo (v3) sobre los mismos 18 macrohilos del benchmark de v2 más
H0000 (como control de cordura), usando exactamente los mismos criterios
de selección y las mismas métricas ya definidas.

**No se declara que v3 sea superior a v2, a FTD, ni a nada.** El resultado
es un intercambio real (más cobertura, menos precisión de agrupación), no
una mejora limpia — se reporta explícitamente así.

## 1. Resultado principal: cobertura

| Sistema | Cobertura en H0000 | Cobertura promedio fuera de muestra (18 hilos) |
|---|---:|---:|
| **v2** (diccionario regex de H0000) | 65.9% | **0%** |
| **v3** (extractor general, columnas `llm_*` del corpus) | 92.9% | **98.8%** |

Detalle completo por hilo en `artifacts/v3_validation_summary.json`. Rango
de cobertura fuera de muestra: 93.3% (H0018) a 100% (10 de los 18 hilos).

Esto confirma la hipótesis del diseño: al basarse en columnas ya
extraídas de forma general para los 3.742 documentos del corpus (no en
vocabulario de H0000), v3 generaliza donde v2 no podía por construcción.

## 2. Pero: fragmentación mucho mayor que v2 en los mismos hilos conocidos

| Hilo (baseline conocido coherente) | v2: n_subhilos | v3: n_subhilos | v3: top-3 subhilos (tamaño) |
|---|---:|---:|---|
| H0001 Dominga | 0 (abstuvo 100%) | **5** | dominga (121), proyecto dominga (26), minera dominga (11) |
| H0002 Fundición Ventanas | 0 (abstuvo 100%) | **16** | fundicion ventanas (109), fundicion codelco ventanas (9), cierre fundicion ventanas (5) |
| H0004 Bocamina | 0 (abstuvo 100%) | **23** | bocamina i (14), bocamina ii (13), central bocamina (9)... hasta "central termoelectrica bocamina i" (3) |
| H0000 (control) | 9 | **44** | estrategia nacional del litio (43, el label generico), acuerdo codelco-sqm (16), salar futuro (14)... |

**Causa identificada, no oculta**: `base_key()` (reutilizada de
`f1_5_normalize_referents_v2.py`) normaliza mayúsculas/tildes/puntuación,
pero **no colapsa paráfrasis** — "central bocamina", "central
termoelectrica bocamina", "bocamina i y ii", "bocamina 1" y "bocamina 2"
son, para `base_key()`, cinco cadenas distintas, aunque un lector humano
reconoce que describen la misma instalación (con matices: "Bocamina I" y
"Bocamina II" sí podrían ser unidades específicas legítimamente distintas
dentro de la misma central). v2 lograba una agrupación más gruesa en
H0000 **precisamente porque su diccionario fue escrito a mano para
colapsar estas variantes** — el mismo trabajo manual que ahora está
prohibido repetir por hilo.

**Índice de fragmentación** (n_subhilos / n_docs_con_subhilo, 0=nada
fragmentado, 1=máximamente fragmentado):

| Hilo | v3 índice fragmentación |
|---|---:|
| H0006 HidroAysén | 0.020 (1 solo subhilo — proyecto realmente unificado) |
| H0001 Dominga | 0.031 |
| H0002 Ventanas | 0.111 |
| H0004 Bocamina | 0.264 |
| H0000 | 0.279 |
| H0017 (refinería ENAP Biobío/Hualpén) | **0.733** (el más fragmentado de los 19 hilos) |

No hay un patrón limpio por tamaño de hilo: HidroAysén (51 docs) fragmenta
casi nada porque casi todos sus documentos usan literalmente "hidroaysen"
como `llm_project_name`; H0017 (16 docs) fragmenta mucho porque el mismo
complejo se nombra de 11 formas distintas ("refineria bio bio", "refineria
de enap en hualpen", "refineria de hualpen", "planta de enap en hualpen",
"chimenea de enap"...). La fragmentación depende de la **variabilidad de
redacción del `llm_project_name` original**, no de una propiedad de v3 en
sí.

## 3. Sobreagregación (proxy estructural, con una limitación real)

Proxy usado: subhilos con ≥2 documentos que agrupan >1 `territorio`
distinto. Resultado: entre 0 (H0013, H0017) y 8 (H0003) subhilos con
riesgo por hilo — ver `artifacts/v3_validation_summary.json` para el
detalle completo.

**Limitación honesta de este proxy**: se observó que H0001 (Dominga) tiene
4 de sus 5 subhilos marcados con "riesgo" de sobreagregación, pese a que
Dominga es un proyecto único conocido en una sola comuna (La Higuera). Al
inspeccionar, esto sugiere que el proxy de territorio es demasiado
sensible a variantes de redacción del propio campo `territorio` (p. ej.
"la higuera" vs. una variante con comuna/región explícita), no
necesariamente evidencia real de que el subhilo mezcle proyectos
distintos. **El proxy de sobreagregación, tal como está implementado
aquí, sobre-reporta riesgo y necesita su propia normalización genérica
antes de tratarse como una métrica confiable** — se deja consignado como
limitación abierta, no se corrige aquí (evitar ajustar métricas después
de verlas).

## 4. Multiasignación y puentes

11 documentos multiasignados en H0000 (vs. 0 en v2, que nunca disparó el
mecanismo en el corpus real). 3 de los 18 hilos fuera de muestra (H0003,
H0007, H0009... ver tabla completa) muestran multiasignación real, todos
vía organización compartida entre proyectos — el mecanismo, que en v2 solo
se había probado con datos sintéticos, **aquí sí se activa con datos
reales**, lo cual es información nueva y relevante: sugiere que la
multiasignación es más una propiedad de corpus con documentos que ligan
más de un proyecto (frecuente cuando una misma empresa aparece en
múltiples proyectos) que un caso raro.

Puentes que cruzan subhilos: entre 0% y 100% de los puentes de cada hilo,
sin patrón consistente — no se puede aún generalizar la lectura de v2
("los puentes de H0000 son mayormente correctos") a otros hilos sin
validación externa.

## 5. Verificación de que HEBRA v2 no fue tocado

```
hebra_v2_experimental/src/subthread_dictionary.py: SHA-256 sin cambios respecto a FROZEN.json
hebra_v2_experimental/src/build_hierarchy.py:      SHA-256 sin cambios respecto a FROZEN.json
```

(ver verificación ejecutable en `tests/test_v3.py`, que incluye un test dedicado a esto)

## 6. Interpretación honesta (ni v2 ni v3 "ganan")

- **v2** (diccionario manual de H0000): alta precisión de agrupación en
  H0000 (93.6% de pureza confirmada por adjudicación ciega GPT-5.6/Claude),
  pero **cobertura cero fuera de su corpus de origen** — no generaliza,
  por diseño.
- **v3** (extractor general): generaliza (92.9%-100% de cobertura en los
  19 hilos evaluados), pero **la granularidad de sus subhilos es
  demostrablemente más fina y ruidosa** que la de v2 en los mismos hilos
  conocidos (Dominga: 5 vs 0 evaluable; Bocamina: 23 vs 0 evaluable) — y
  **no tiene todavía ninguna validación de pureza por adjudicación ciega**
  (a diferencia de v2/H0000, que sí la tiene). No sabemos aún si esos 23
  subhilos de Bocamina son 23 procesos genuinamente distintos o son 3-4
  procesos reales fragmentados en exceso por variabilidad de redacción.
- **Ninguno de los dos resuelve el problema completo**: v2 es preciso pero
  no generaliza; v3 generaliza pero su precisión no está medida contra
  gold. El siguiente paso lógico (fuera de alcance de este ejercicio) es
  una ronda de adjudicación ciega GPT-5.6/Claude sobre una muestra de
  pares de v3 en Dominga/Ventanas/Bocamina, análoga a la de H0000, antes
  de decidir si v3 reemplaza algo.
