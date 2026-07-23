Actúa como adjudicador independiente de procesos socioambientales longitudinales.

FUENTE
Recibirás `V3B_BLIND_REVIEW_SHEET.json`, con 52 pares ciegos tomados de
tres macrohilos distintos (proyecto minero-portuario Dominga, cierre de la
Fundición de cobre de Ventanas, y las centrales termoeléctricas Bocamina).
No se te dice a qué macrohilo pertenece cada par, ni qué categoría le
asignó ningún sistema automático, ni el peso de ninguna arista. No uses la
clave sellada, informes de topología, ni respuestas de otros evaluadores.

OBJETIVO
Para cada par de documentos (doc_a, doc_b), responde DOS preguntas
independientes usando únicamente el texto completo entregado.

NIVEL A — IDENTIDAD PROCESUAL (igual criterio que en la validación de H0000)
- `mismo_proceso_especifico`: mismo proyecto, instalación, unidad/fase de
  una instalación, contrato, consulta, litigio, procedimiento administrativo
  o controversia territorial reconocible.
- `mismo_macroproceso`: mismo complejo o política amplia (p. ej. el mismo
  complejo industrial), pero unidad, instalación, contrato o procedimiento
  específico distinto (p. ej. Bocamina I vs. Bocamina II si son unidades
  con historial propio; el cierre de la fundición vs. una central
  termoeléctrica distinta en el mismo complejo).
- `relacionado_tematicamente`: comparten sector o ubicación general sin
  continuidad suficiente en un macroproceso identificable.
- `no_relacionado`: procesos sustantivamente distintos (p. ej. una central
  termoeléctrica en una comuna distinta que solo comparte el tema
  "cierre de termoeléctricas a carbón").
- `indeterminado`: la evidencia textual no permite decidir.

NIVEL B — DIAGNÓSTICO DE AGRUPAMIENTO (específico de esta validación)
Independientemente de tu respuesta en el Nivel A, indica cuál de estas
describe mejor lo que un sistema automático de agrupamiento debería haber
hecho con este par:
- `asignacion_correcta`: la forma en que un sistema razonable agruparía
  (o separaría) a A y B coincide con tu juicio del Nivel A — es decir, si
  dijiste `mismo_proceso_especifico`, un sistema correcto los habría
  agrupado juntos; si dijiste `no_relacionado` o `mismo_macroproceso`
  (unidades distintas), un sistema correcto los habría separado.
- `fragmentacion_falsa`: A y B son el MISMO proceso específico (Nivel A =
  `mismo_proceso_especifico`), pero es plausible que un sistema automático
  los hubiera separado en dos grupos distintos solo por usar nombres de
  proyecto escritos de forma diferente (p. ej. "Dominga" vs. "Proyecto
  Dominga" vs. "Minera Dominga" refiriéndose exactamente al mismo
  proyecto).
- `sobreagregacion`: A y B NO son el mismo proceso específico ni el mismo
  macroproceso (Nivel A = `relacionado_tematicamente` o `no_relacionado`,
  o `mismo_macroproceso` si se trata de instalaciones/unidades claramente
  distintas), pero es plausible que un sistema automático los hubiera
  agrupado juntos por compartir un nombre de proyecto parecido o el mismo
  complejo industrial.
- `abstencion_correcta`: al menos uno de los dos documentos NO permite
  identificar con confianza un proyecto o instalación específico (el texto
  es demasiado genérico, ambiguo, o trata el tema a nivel de política
  general) — un sistema que se abstuviera de asignarle un proyecto
  concreto a ese documento actuaría correctamente.
- `abstencion_incorrecta`: al menos uno de los dos documentos SÍ permite
  identificar con confianza un proyecto o instalación específico a partir
  del texto — un sistema que se abstuviera de asignarle un proyecto
  concreto a ese documento estaría subestimando la evidencia disponible.
- `indeterminado`: no se puede evaluar el agrupamiento con la evidencia
  disponible.

CRITERIO PARA NIVEL B
- Usa `fragmentacion_falsa` y `sobreagregacion` únicamente cuando tengas
  una hipótesis textualmente fundamentada de POR QUÉ un sistema automático
  podría confundirse (nombres parecidos, mismo complejo, mismo sector) —
  no los uses como categorías por defecto.
- `abstencion_correcta`/`abstencion_incorrecta` se refieren a la
  IDENTIFICABILIDAD del proyecto/instalación en el texto de UNO o AMBOS
  documentos, no a si A y B son el mismo proceso entre sí. Si ambos
  documentos identifican claramente proyectos (aunque sean distintos),
  usa `asignacion_correcta` o `indeterminado` según corresponda, no la
  pareja abstención.

CONFIANZA
- alta
- media
- baja

REGLAS
1. Usa exclusivamente los textos entregados.
2. Lee el texto completo de ambos documentos.
3. Evalúa cada par independientemente; no asumas relación por pertenecer a
   la misma muestra.
4. No busques información externa.
5. No infieras a qué macrohilo, estrato o sistema pertenece cada par.
6. Conserva `indeterminado` cuando falte evidencia, en cualquiera de los
   dos niveles.
7. Devuelve exactamente 52 casos y conserva los `case_id`.
8. No escribas markdown ni explicación fuera del JSON.

SALIDA
{
  "reviewer_model": "NOMBRE_DEL_MODELO",
  "evidence_class": "independent_ai_adjudication",
  "human_gold": false,
  "cases": [
    {
      "case_id": "ID EXACTO",
      "nivel_a": "mismo_proceso_especifico | mismo_macroproceso | relacionado_tematicamente | no_relacionado | indeterminado",
      "nivel_b_v3": "asignacion_correcta | fragmentacion_falsa | sobreagregacion | abstencion_correcta | abstencion_incorrecta | indeterminado",
      "confidence": "alta | media | baja",
      "justification": "Explicación breve y específica citando evidencia textual concreta."
    }
  ]
}
