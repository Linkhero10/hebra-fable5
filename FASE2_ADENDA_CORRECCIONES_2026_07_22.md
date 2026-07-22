# Adenda congelada a la réplica Fase 2 — Fable 5 (correcciones del auditor)

Fecha: 2026-07-22. `FASE2_REPLICA_FABLE5_2026_07_22.md` queda intacta; esta
adenda corrige sus afirmaciones donde el auditor lo exige. Nada se
implementa hasta conocer la réplica independiente de GPT-5.6.

## 1. Reclasificación de F4-A

Donde la réplica dice "el único resultado de identidad no circular", debe
leerse:

> **F4-A aporta evidencia de consistencia semántica interna frente a un
> nulo temporal condicionado.**

F4-A usa los mismos embeddings que participan en la construcción del grafo:
no es validación externa, no es prueba independiente y no mide identidad
procesual. El claim "138/178 hilos demuestran identidad" queda **retirado**
de los claims permitidos. Lo que queda permitido: "la coherencia interna de
los hilos no se explica solo por la restricción temporal del algoritmo,
según un nulo condicionado construido con los mismos embeddings".

## 2. Alcance real de HN50-B

HN50-B demuestra únicamente:

> La similitud semántica elevada, en ausencia del anclaje definido por
> HEBRA, no garantiza por sí sola identidad procesual.

**No** demuestra la tasa de error de la puerta estricta de FTD-Core:
(a) 0,80 ≠ 0,84; (b) ausencia de referentes HEBRA no implica ausencia de
firmas FTD; (c) la muestra vive en el espacio de candidatos de HEBRA, no en
el de la puerta estricta de FTD; (d) las etiquetas son provisionales sobre
títulos. Evaluar esa puerta requiere extraer del propio FTD los pares que
pasaron exclusivamente por `strict_semantic`, estratificarlos por similitud
y adjudicarlos a ciegas con texto completo. La crítica a la puerta queda
como **riesgo estructural identificado en código**, con frecuencia real no
medida.

## 3. Fragmentación vs mezcla: reformulación

Se retira "el error dominante es fragmentación, no mezcla". Formulación
autorizada:

> La muestra revela fragmentación importante en la frontera (R30) y no
> detectó falsos positivos duros entre los enlaces aceptados auditados; la
> importancia global de la mezcla sigue sin determinarse.

Razones: 21/110 `relacionado` (19 %) puede contener mezcla real
(macro-controversia, territorio, actores amplios, fases indebidamente
unidas); la evidencia fue título/snippet; y en un sistema de componentes
conexos **una sola arista mezcladora fusiona comunidades enteras por
transitividad**, de modo que pocos falsos positivos pueden pesar más que
muchos falsos negativos individuales. La comparación de daños esperados
entre ambos tipos de error queda pendiente de E1–E3 y del conjunto sellado
de Fase 2.

## 4. ISO20 no demuestra sobreabstención del mecanismo

Reformulación autorizada:

> ISO20 diagnostica posibles omisiones de continuidad entre documentos
> aislados; no demuestra una tasa de sobreabstención de 0,846 del
> mecanismo.

Que un documento pertenezca sustantivamente a un proceso no implica que
existiera en el corpus un par candidato con referentes normalizados
compartidos que el umbral rechazó. Demostrar sobreabstención exige, por
documento aislado: identificar el hilo destino, verificar existencia de
candidatura, y clasificar la causa (sin referente extraído / sin candidato
temporal / arista rechazada por umbral). Ese análisis causal queda diseñado
como extensión de E5 y no se ha ejecutado.

## 5. v2 descompuesta en ablaciones secuenciales A–D

La propuesta v2 de la réplica se reclasifica como **hipótesis de desarrollo
derivada de la auditoría v1** (usa R30 como insumo de diseño; se declara).
No es preinscripción en sentido fuerte. Secuencia autorizada:

- **V2-A:** solo τ 0,45→0,40; DSU, referentes y todo lo demás intactos.
- **V2-B:** solo agrupamiento; τ=0,45 fijo; DSU vs partición comunitaria
  (algoritmo según E4).
- **V2-C:** combinación, solo si A y B muestran beneficios complementarios
  y atribuibles.
- **V2-D:** incertidumbre estructural, después, porque la abstención cambia
  la cobertura y contamina la atribución de efectos.

Advertencia de percolación aceptada: el salto gigante 170 (τ=0,45) → 2.047
(τ=0,35) implica una transición de conectividad abrupta en (0,35, 0,45);
V2-A debe barrer τ∈{0,40; 0,42; 0,44} con diagnósticos estructurales antes
de fijar valor, y ninguna métrica de éxito puede computarse sobre R30 ni
sobre muestra v1 alguna.

## 6. Guardrail del gigante reemplazado

"Gigante ≤30 %" fue una barrera anti-colapso de F2, no un criterio de
calidad. Para V2-A/B/C se sustituye por el panel:

- proporción del componente gigante (reportada, sin umbral único);
- distribución completa de tamaños (p50/p90/máx);
- número de referentes dominantes por hilo grande;
- diversidad territorial por hilo grande;
- proporción de aristas puente;
- adjudicación ciega intercomunidad (E1) para todo hilo >100 docs;
- concentración por proyecto (share del referente objeto top-1).

Un hilo de ~1.100 documentos no sería defendible como "proceso" bajo ningún
umbral aritmético; la defensa exige el panel completo.

## 7. Corrección de lenguaje sobre la adjudicación v1

Donde el veredicto personal dice "precisión adjudicada alta con cero FP
duros", debe leerse:

> La evaluación exploratoria de aristas aceptadas fue favorable y no
> encontró pares categorizados como `no_relacionado`, pero no establece una
> precisión poblacional ni un gold externo.

## 8. Adición al registro de incertidumbre (E5)

La métrica propuesta en E5 se denomina **incertidumbre estructural de
membresía**, no "incertidumbre individual": un documento puede ser estable
en una comunidad incorrecta (baja u_i, error real) o correcto pero
inestable por fase de transición. Se complementará con: dependencia de
arista única, diversidad de referentes, diferencia de evidencia hacia dos
comunidades, estabilidad temporal y coherencia con el referente dominante.

## 9. Estado

- Réplica original: intacta, con esta adenda como corrección vinculante.
- Experimentos aprobados como diagnósticos: E1–E5.
- Arquitectura v2: NO autorizada; espera falsación estructural congelada y
  la réplica independiente de GPT-5.6.
- Sobre el bug de margen de FTD: se mantiene como defecto de consistencia
  interna demostrado por lectura; su magnitud (cuántas de las 1.501
  abstenciones explica) queda explícitamente no demostrada hasta reejecutar
  FTD corregido.

— Fable 5.
