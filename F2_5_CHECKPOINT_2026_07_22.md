# Checkpoint F1.5–F2.5 — HEBRA

Fecha: 2026-07-22. Estado FARO: Exploratorio. Las salidas v1 se conservan
intactas como experimentos históricos (`f1_referents.csv`, `f2_threads*`,
`f2b_idf_threads*`); todo lo corregido usa sufijo `v2`.

## 1–2. Auditoría y corrección F1 (identidad ≠ relación)

Hallazgo confirmado en `f1_alias_dictionary.json`: la regla v1 `nombre (x)`
fusionó paréntesis relacionales como sinónimos. Los 9 casos señalados
(pc→diputada Nathalie Castillo, ps→Nelson Venegas, litio→explotación de
salmuera, diputado→Cristián Tapia, colbún→Termoeléctrica Santa María,
engie→Central Las Arcillas, barrick→Pascua Lama, sqm-codelco→acuerdo,
dominga→Puerto Cruz Grande/Andes Iron) existían, todos con 1 doc de
evidencia. Lección registrada: **"no ambiguo en el corpus" no es criterio de
identidad**; el paréntesis codifica afiliación, propietario, cargo,
tecnología o instrumento.

Corrección (`src/f1_5_normalize_referents_v2.py`, reglas preinscritas en el
encabezado del script):

- R3v2: una sigla solo se acepta si coincide con las iniciales de las
  palabras del nombre (con y sin stopwords). Sin coincidencia no hay fusión:
  la forma completa `nombre (x)` se conserva como referente **distinto**.
- R4v2: sigla suelta → canónico solo para siglas aceptadas y de expansión
  única.
- G1: un término genérico/rol (persona, empresa, diputado, acuerdo…) no puede
  ser canónico de fusión.

Resultado (`outputs/f1v2_alias_audit.json`): de 417 formas con paréntesis,
**101 fusiones aceptadas** (todas con evidencia de iniciales) y **336
conservadas como referentes distintos** con motivo registrado. Los 9 casos
inválidos quedan rechazados. Costo conocido de la conservaduría: siglas
silábicas legítimas (p. ej. codelco como sigla de su razón social) no se
fusionan automáticamente; quedan en la lista de rechazadas para revisión
humana futura, nunca fusión silenciosa.

## 3. Reejecución F2/F2b sobre F1v2

(Ver `outputs/f2_v2_threads_summary.json` y
`outputs/f2b_idf_v2_threads_summary.json`; comparación al final de este
documento, sección "Δ v1→v2".)

## 4. Revisión ciega de enlaces e hilos

`src/f2_5_sample_links.py` (semilla 42) genera
`outputs/f2_5_blind_review_sheet.json`: 60 enlaces y 12 hilos aleatorios con
ids, fechas, títulos — **sin puntajes ni umbrales** (la clave queda en un
archivo separado que no se abre durante la revisión). La revisión se etiqueta
`expert_review_provisional_ai` y queda preparada para repetición humana.
Resultados en la sección "Revisión ciega" al final.

## 5. Estado de los cinco casos preinscritos

**Registro de contaminación:** Quintero-Puchuncaví, HidroAysén, cierre del
carbón (Bocamina/Coronel), litio/Salar de Atacama e H2 Magallanes **ya fueron
inspeccionados** en los perfiles top de F2/F2b durante el desarrollo
(2026-07-22). No son un holdout virgen. Reglas desde ahora:

1. Ningún parámetro nuevo (τ, pesos, Δ, IDF, reglas de alias) puede
   seleccionarse mirando el desempeño en esos cinco casos.
2. Siguen siendo utilizables solo como *smoke test* descriptivo, etiquetado
   como desarrollo.
3. La evaluación independiente usará: (a) adjudicación humana ciega de una
   muestra aleatoria de hilos (la de §4 u otra semilla nueva sellada); (b) una
   lista externa de casos construida sin mirar salidas de HEBRA, p. ej.
   conflictos del mapa INDH / EJAtlas-Chile del periodo del corpus,
   intersectada con el corpus por un script determinista y **sellada con hash
   antes** de correr F4. La lista se adjudica primero contra el corpus (¿hay
   documentos suficientes?) y solo después contra los hilos.

## 6. Nulo temporal: justificación y rediseño (sin ejecutar)

Objeción aceptada: permutar `fecha_iso` dentro de año×fuente **preserva la
estructura interanual** (los volúmenes anuales del corpus y de cada hilo
quedan casi intactos), de modo que no puede falsar emergencia multianual,
latencia larga ni reaparición. Además el corpus es fuertemente no
estacionario (F0: 405→919 docs/año entre 2022 y 2025), así que cualquier
señal de densidad absoluta confunde crecimiento del corpus con crecimiento
del proceso.

Diseño de calibración en dos niveles (preinscrito, pendiente de ejecución):

- **Normalización previa:** toda densidad de hilo se expresa como *proporción
  del volumen del corpus en el periodo* (share), nunca conteo absoluto, tanto
  en datos reales como en nulos.
- **Nivel intraanual** — nulo N1: permutación de fechas dentro de año×fuente.
  Calibra: ráfagas, brechas cortas (<12 meses), orden interno de un año.
  Válido porque solo destruye el orden fino.
- **Nivel interanual** — nulo N2 (*pseudo-hilos*): para cada hilo real de
  tamaño k, muestrear B=200 conjuntos de k documentos del corpus
  estratificados por fuente, tomando sus fechas reales. Calibra: fecha de
  primera observación condicionada al tamaño, duración de latencias
  multianuales, probabilidad de reaparición tras ausencia. Falsa la
  pregunta correcta: "¿este perfil temporal difiere del de un agrupamiento
  arbitrario del mismo tamaño bajo el mismo corpus no estacionario?".
- **Guardas:** las señales interanuales se reportan condicionadas al tamaño
  del hilo (los hilos chicos tardíos son esperables bajo N2); N1 y N2 se
  congelan con semillas y hashes antes de mirar resultados; ninguna señal se
  publica si no supera el percentil 95 de su nulo correspondiente.
- **Límite declarado:** N2 no controla la dependencia referencial (los
  pseudo-hilos no comparten referentes); por eso mide el efecto conjunto
  "referentes+tiempo", no tiempo puro. Se documentará como tal; una variante
  N2b (pseudo-hilos igualados por grado de referente) queda como extensión
  opcional si N2 resulta demasiado laxo.

---

## Δ v1→v2

τ elegido por la regla estructural no cambia (F2 base 0,35; F2b 0,45). La
estructura es robusta a la corrección de alias:

| Métrica (config elegida) | F2 base v1→v2 | F2b IDF v1→v2 |
|---|---|---|
| aristas | 48.696 → 48.588 | 10.229 → 9.981 |
| hilos ≥3 | 105 → 106 | 177 → 178 |
| cobertura ≥3 (%) | 78,23 → 78,09 | 50,42 → 49,74 |
| gigante (%) | 24,99 → **21,99** | 4,97 → **4,56** |
| hilos multifamilia (%) | 81,9 → 82,1 | 70,6 → 69,1 |
| vida mediana (años) | 1,23 → 1,23 | 0,92 → 0,91 |

Los perfiles top son los mismos procesos, ahora sin alias inválidos
(`outputs/f2_v2_threads_summary.json`, `outputs/f2b_idf_v2_threads_summary.json`).

## Revisión ciega (expert_review_provisional_ai)

Muestra semilla 42 sobre F2b v2; veredictos congelados antes de desciegar
(`outputs/f2_5_blind_review_verdicts.json`, SHA-256 `80247516f5e1c6ba…`):

- **Enlaces (60):** 57 mismo proceso, 3 relacionados sin certeza (E032
  transmisión, E033 panorama H2V, E046 glaciares), 0 no relacionados.
  **Alcance estricto de esta cifra:** es una evaluación provisional IA de
  *enlaces positivos* (muestreo aleatorio simple sobre aristas aceptadas,
  juzgando solo títulos, sin referentes ni cuerpos). El 0,95 NO es precisión
  general del sistema: no mide falsos negativos, documentos aislados ni
  enlaces rechazados, y no pondera por estrato de puntaje o distancia
  temporal. La evaluación independiente de F4 cubre esos estratos.
  Post-descegado: los 3 dudosos tienen w 0,50–0,65 — no son casos de borde
  del umbral; la imprecisión residual viene de referentes de grano grueso.
- **Hilos (12):** 11 coherentes, 0 mezclas, 1 fragmento (H0162, multas
  Bocamina 2016-17 separado del hilo principal Bocamina). El modo de fallo
  observado de la variante conservadora es **fragmentación**, no mezcla —
  consistente con el diseño (la fusión de fragmentos es tarea de la revisión
  humana de alias, nunca automática).

Límites: revisión hecha por IA sobre títulos; debe repetirse por humano antes
de cualquier promoción. La muestra de 12 hilos excluye por azar los 5 casos
grandes de desarrollo; eso la hace más representativa de los hilos típicos.

## Veredicto del checkpoint

F1.5–F2.5 cumplido: alias corregidos con auditoría completa, estructura
robusta al cambio, precisión de enlaces alta bajo revisión ciega provisional,
contaminación de los 5 casos registrada, y nulo temporal rediseñado en dos
niveles (N1 intraanual / N2 pseudo-hilos interanual) pendiente de ejecución.
F3 queda bloqueado hasta aprobación explícita.
