# Adjudicación experta independiente por IA

Fecha: 2026-07-22
Revisor: GPT-5.6 Thinking
Estatus: **evaluación experta por IA; no validación humana**

## Alcance

- HEBRA F4-B: 240 ítems ciegos.
- FTD-Core: 60 pares ciegos.
- Las decisiones se formularon sin usar la clave de estrato, puntaje, umbral o decisión del sistema.
- Se mantuvo la categoría `indeterminado` cuando título/snippet no permitían resolver identidad.
- Se produjeron subconjuntos de alta confianza para análisis confirmatorio provisional.

## Definiciones

- `mismo_proceso`: mismo proyecto, instalación, controversia o procedimiento con continuidad documental.
- `relacionado`: mismo territorio, política o campo, pero identidad procesual insuficiente.
- `no_relacionado`: procesos distintos.
- `indeterminado`: evidencia textual insuficiente.
- `pertenece_a_un_proceso`: un documento aislado tiene continuidad procesual clara.
- `aislado_correcto`: no hay proceso identificable o está fuera del dominio.

## Uso permitido

- auditoría externa por IA;
- detección de mezcla, fragmentación y sobreabstención;
- comparación provisional;
- insumo para réplica cruzada.

## Uso no permitido

- presentarlo como validación humana;
- calcular acuerdo interhumano;
- afirmar promoción científica definitiva;
- ajustar una versión v1 y evaluarla con la misma muestra.

## Conteos

HEBRA:
{
  "aislado_correcto": 2,
  "indeterminado": 18,
  "mismo_proceso": 117,
  "no_relacionado": 36,
  "pertenece_a_un_proceso": 11,
  "relacionado": 56
}

FTD-Core:
{
  "mismo_proceso": 36,
  "no_relacionado": 2,
  "relacionado": 22
}

## Protocolo de desciegue

1. Conservar estos archivos y registrar SHA-256.
2. Abrir las claves originales.
3. Calcular métricas por estrato, no un único porcentaje agregado.
4. Excluir o reportar aparte los indeterminados.
5. Congelar el veredicto v1 antes de permitir modificaciones.
6. Permitir después la réplica cruzada entre agentes.
