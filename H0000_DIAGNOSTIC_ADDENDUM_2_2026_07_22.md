# Fase 3B — Addendum 2 (correcciones finas, sin nuevo cómputo topológico)

Fecha: 2026-07-22. `H0000_DIAGNOSTIC_REPORT_2026_07_22.md`,
`H0000_DIAGNOSTIC_ADDENDUM_2026_07_22.md` y los 16 artefactos `H0000_*`
quedan **intactos**. Este segundo addendum corrige dos formulaciones y una
inconsistencia interna; no ejecuta topología nueva ni adjudicación,
conforme a la recomendación del auditor de no seguir acumulando análisis
antes de adjudicar.

## 1. La comparación DSU vs comunidades queda condicionada por granularidad

Aceptado. Retener el 95,1 % de 14.365 pares (una sola clase de 170) no es
la misma prueba que retener el 88,6-94,8 % de pares dentro de particiones
en 10-27 comunidades pequeñas: el denominador y la dificultad de la prueba
difieren radicalmente. **Se retira** "DSU es al menos tan estable" del
Addendum 1. Formulación válida:

> DSU mantiene la mayor proporción de su coasignación original bajo
> edge-drop, pero la comparación está condicionada por su granularidad de
> una sola clase. Esta estabilidad relativa no establece validez procesual
> ni superioridad sobre las particiones comunitarias.

Correcto también que un componente principal de 165,7/170 tras drop10% es
compatible con dos lecturas opuestas (robustez legítima vs
sobreconectividad que fusiona procesos distintos) y la métrica actual no
distingue entre ellas. Distinguirlas exige la prueba que propone el
auditor: sobre los 104 pares **ya adjudicados** (cuando exista esa
adjudicación), medir tasa de conservación de `mismo_proceso` y tasa de
separación de `no_relacionado` bajo las mismas perturbaciones — unidad
común: el par sustantivo, no la partición de cada algoritmo. Esa prueba
**no se ejecuta aquí** porque depende de la adjudicación pendiente.

## 2. El nulo de heterogeneidad se reclasifica como exploratorio

Aceptado sin reservas. Barajar los conjuntos de referentes entre nodos
preservando el grafo rompe la relación entre referentes y aristas que el
propio mecanismo de HEBRA usó para construir esas aristas: el nulo
responde "¿hay más heterogeneidad que si los referentes se asignaran al
azar sobre el grafo ya construido?", no "¿hay más heterogeneidad de la
esperable bajo la regla generativa de HEBRA?". Se retira "evidencia
estadística de chaining"; formulación autorizada:

> H0000 muestra mucha más heterogeneidad objeto-territorio que tres hilos
> centrados en proyectos específicos (0 % vs 39,2-41,8 %). El nulo
> exploratorio también sugiere que esa heterogeneidad no se distribuye
> aleatoriamente entre los nodos dado el grafo, pero el nulo no reproduce
> la mecánica de generación referencial de HEBRA y debe tratarse como
> exploratorio, no confirmatorio.

Un nulo que sí condicionara correctamente preservaría: grado, frecuencia de
cada referente, referentes por documento, tipo de referente compartido por
arista, estructura temporal y distribución territorial/de objeto —
mediante *rewiring* condicionado o reaplicando la regla de enlace de HEBRA
sobre referentes permutados. **No se ejecuta aquí** para no seguir
acumulando análisis topológico antes de la adjudicación, siguiendo la
recomendación explícita del auditor.

También aceptado: los tres baselines de 0 % (Dominga, Ventanas, Alto
Maipo) comparan una escala de proyecto único contra una escala de
macroproceso sectorial (Estrategia Nacional del Litio); el contraste
demuestra que H0000 opera a mayor escala, **no** que esté incorrectamente
mezclado. Esa distinción de escala es precisamente la pregunta pendiente
de la sección 4.

## 3. Errata en artefacto sellado (no se sobrescribe)

El campo `robustez["formulacion_corregida"]` dentro de
`H0000_15_ADDENDUM_DSU_VS_COMMUNITY_ROBUSTNESS.json` quedó con una
redacción que contradice las propias cifras del archivo (dice que la
retención de DSU "cae más" cuando los números muestran lo contrario). Ese
campo de texto se declara **inválido/superado** por este addendum; el
archivo no se modifica para preservar la cadena de hashes. Lectura correcta
del archivo: usar únicamente los campos numéricos (`retencion_pares_media`,
`VI_media`, etc.), no la nota narrativa embebida.

## 4. Pregunta jerárquica para la futura adjudicación (diseño, no ejecutado)

Se acepta el encuadre del auditor: la pregunta relevante no es solo
"¿mezclado sí/no?" sino en qué **nivel de escala** se define "mismo
proceso". Se deja registrado como esquema propuesto para cuando se ejecute
la adjudicación de los 104 pares sellados (`H0000_08/09`, sin modificar):

1. ¿Mismo macroproceso sectorial (p. ej. Estrategia Nacional del Litio)?
2. ¿Mismo proceso territorial/proyecto específico (mismo salar, mismo
   contrato, misma consulta)?
3. ¿Solo relacionados temáticamente (litio en general, sin proceso
   compartido)?
4. ¿No relacionados?

Este esquema es una propuesta de codebook para la adjudicación futura, no
una ejecución de la misma; no se adjudica nada en este documento.

## Estado

Sin nuevo cómputo topológico. Sin selección de arquitectura. Sin
adjudicación ejecutada. Los tres documentos H0000 (informe, addendum 1,
addendum 2) se leen juntos como cadena de corrección; el addendum 2 tiene
precedencia interpretativa sobre las dos formulaciones señaladas del
addendum 1.

— Fable 5.
