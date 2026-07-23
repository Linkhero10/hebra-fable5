# -*- coding: utf-8 -*-
"""
Fase 3: resolucion de los 23 desacuerdos GPT-5.6 vs Claude Sonnet 5.

IMPORTANTE (limitacion metodologica declarada, no oculta): el arbitro que
ejecuta este script es el mismo modelo (Claude Sonnet 5) que produjo una de
las dos adjudicaciones originales. No es un tercer juez independiente. Se
releyeron ambos textos completos de cada par (desde H0000_08_BLIND_REVIEW_SHEET.json)
y ambas justificaciones antes de fijar cada decision, aplicando el codebook
jerarquico del prompt HEBRA, pero el sesgo de auto-confirmacion no puede
descartarse y se reporta explicitamente en el informe final (ver conteo de
cuantas veces el arbitro coincidio con cada adjudicador original).
"""
import json

BASE = r"D:\Analisis conflictos\01_proyecto_universidad\09_metodologia\faro_model_research\competition"
DIAG = BASE + r"\fable5\diagnostics_h0000"
PKG = BASE + r"\PAQUETE_VALIDACION_MULTI_IA_COMPLETO_2026_07_22"
OUT = BASE + r"\fable5\h0000_validation_2026_07_22"

with open(PKG + r"\RESPUESTA_HEBRA_GPT_5_6_2026_07_22.json", encoding="utf-8") as f:
    gpt = {c["case_id"]: c for c in json.load(f)["cases"]}
with open(PKG + r"\RESPUESTA_HEBRA_CLAUDE_SONNET_5_2026_07_22.json", encoding="utf-8") as f:
    claude = {c["case_id"]: c for c in json.load(f)["cases"]}

# Decision final razonada tras releer ambos textos completos de la hoja ciega
# (ver H0000_08_BLIND_REVIEW_SHEET.json por case_id para el texto integro).
ARBITRATIONS = {
    "H006": dict(decision="mismo_macroproceso", confianza="media",
        razon="GPT extiende identidad especifica a partir de continuidad politico-institucional general (mismo gobierno, mismo marco ENL), pero el texto B (reunion Boric-CPA) trata demandas territoriales (restitucion de tierras, agua potable) que el propio texto no vincula al tramite especifico de Contraloria del acuerdo Codelco-SQM que es objeto de A. No hay objeto/procedimiento textualmente compartido, solo el marco sectorial comun.",
        justificacion="A es la toma de razon de Contraloria sobre el acuerdo Codelco-SQM (objeto especifico: ese contrato). B es una rendicion de cuentas territorial de Boric al CPA sobre tierras, agua e infraestructura, enmarcada en la ENL en general pero sin referirse al tramite de Contraloria ni a los terminos del contrato. Comparten macropolitica (ENL/Codelco-SQM como eje), no el mismo procedimiento reconocible."),
    "H008": dict(decision="mismo_macroproceso", confianza="baja",
        razon="Ninguno de los dos adjudicadores originales acierta plenamente: GPT sobreextiende a 'mismo conflicto especifico de Maricunga' sin que B mencione el Proyecto Blanco ni el litigio; Claude subestima que B se autodefine explicitamente como parte del 'primer hito de la Estrategia Nacional del Litio', el mismo marco institucional que rige el proyecto de A.",
        justificacion="A es el fallo del Segundo Tribunal Ambiental que confirma el Proyecto Blanco (procedimiento judicial-administrativo especifico de Maricunga). B es la demanda de 2023 de Pai Ote por representacion en el directorio de la futura Empresa Nacional del Litio, explicitamente enmarcada como el primer hito de la ENL. Ambos son posiciones institucionales reales dentro de la misma politica nombrada (ENL), pero sobre componentes distintos (litigio ambiental de un proyecto puntual vs. diseno de gobernanza nacional); no hay proyecto, contrato o procedimiento compartido."),
    "H011": dict(decision="mismo_proceso_especifico", confianza="media",
        razon="Claude penaliza la distancia temporal (20 meses) y el cambio de genero discursivo (cronica de protesta vs. cobertura electoral) por encima de la identidad textual del objeto. Al releer, ambos textos tienen como objeto central explicito el mismo pacto nombrado ('el acuerdo Codelco-SQM' / 'este pacto... hasta 2060'), igual que en H034, H100 y H003 (ya resueltos como especifico por ambos adjudicadores). Mantener a H011 en macro habria sido inconsistente con ese criterio ya aplicado en pares no disputados.",
        justificacion="A narra el bloqueo de enero de 2024 de Toconao contra el acuerdo Codelco-SQM. B es la cobertura de octubre de 2025 sobre el rechazo de los candidatos presidenciales al MISMO pacto ('el acuerdo entre la estatal Codelco y la minera SQM... hasta 2060'). El objeto especifico (ese contrato nombrado) es identico en ambos, aunque los actores y el momento difieran; el criterio de continuidad de contrato reconocible se cumple."),
    "H021": dict(decision="mismo_macroproceso", confianza="media",
        razon="Claude clasifico como solo tematico, pero ambos textos se autodefinen explicitamente como acciones dentro de la Estrategia Nacional del Litio nombrada (la red de salares protegidos por un lado, el primer hito de dialogo por el otro), lo que supera el umbral de 'comparten sector' para constituir episodios reales de la misma macropolitica.",
        justificacion="A es la entrevista de la ministra Rojas defendiendo la red de salares protegidos como componente ambiental de la ENL. B es la demanda de Pai Ote por representacion en el directorio, enmarcada como el primer hito de la misma ENL. Ambas son posturas institucionales reales sobre componentes distintos de una politica sectorial amplia explicitamente nombrada; no hay proyecto o procedimiento comun."),
    "H029": dict(decision="mismo_macroproceso", confianza="media",
        razon="GPT sobreextiende a especifico tratando la anulacion del acuerdo y la demanda de gobernanza de Socaire como 'la misma implementacion desde escalas distintas'; Claude subestima que la reunion de Socaire es una audiencia institucional real (en La Moneda, con respuesta presidencial) explicitamente enmarcada en el plan de trabajo de la ENL, no un comentario generico.",
        justificacion="A es el informe y voto de la Camara de Diputados para dejar sin efecto el acuerdo Codelco-SQM (objeto especifico: ese contrato). B es la Audiencia Ampliada de Comunidades Atacamenas en La Moneda donde Socaire exige gobernanza diferenciada dentro de la ENL. Ambos son episodios institucionales reales de la misma politica sectorial, sobre asuntos especificos distintos (anulacion contractual vs. gobernanza territorial diferenciada)."),
    "H034": dict(decision="mismo_proceso_especifico", confianza="alta",
        razon="GPT trata el analisis de sostenibilidad electoral y el voto de anulacion como 'politica sectorial' generica: al releer, el propio texto A discute explicitamente 'la oposicion al acuerdo entre la estatal Codelco y la privada local SQM... hasta 2060' -el mismo pacto que la Camara vota anular en B-, por lo que el objeto especifico compartido es inequivoco.",
        justificacion="A (BNamericas, julio 2025) analiza explicitamente la oposicion politica al mismo acuerdo Codelco-SQM que B (Camara de Diputados, junio 2025) vota anular. Mismo contrato nombrado como objeto central de ambos textos."),
    "H035": dict(decision="mismo_macroproceso", confianza="media",
        razon="GPT afirma que 'la alerta hidrica de 2025 prolonga el conflicto... iniciado en 2023' sin que el texto A haga referencia alguna a la reunion cancelada de 2023; es una continuidad narrativa asumida, no textual.",
        justificacion="A (Hugo Flores, nov-dic 2025) denuncia vicios en la consulta indigena vigente y tacticas de division de Corfo. B (junio 2023) es la cancelacion de una reunion multietnica con Boric. Son episodios de oposicion indigena a la ENL en momentos y con objetos especificos distintos (consulta indigena 2025 vs. reunion 2023), sin procedimiento compartido explicito en el texto."),
    "H053": dict(decision="mismo_macroproceso", confianza="media",
        razon="GPT trata dos expedientes regulatorios distintos como 'el mismo escrutinio'; al releer, B situa el origen del conflicto CCHEN-Albemarle en 2019-2020 por un procedimiento propio (revision de reservas bajo normativa CCHEN), mientras A es la revision de RCA ante el SEA/Coeva iniciada en 2024 por niveles de acuifero -bases legales, reguladores e historiales distintos.",
        justificacion="A es la apertura de revision de RCA de Albemarle por el Coeva de Antofagasta (procedimiento ambiental, SEA). B es la exigencia de la CCHEN sobre datos de reservas de litio (procedimiento regulatorio distinto, con historia propia desde 2019). Mismo territorio y empresa, distinto procedimiento administrativo especifico."),
    "H058": dict(decision="mismo_proceso_especifico", confianza="media",
        razon="GPT afirma que 'no se identifica una misma organizacion, consulta o evento', lo cual es inexacto: el CPA (via su asesor juridico) participa explicitamente en ambos hitos, separados por solo un mes, dentro del mismo proceso de acercamiento inaugural instituido por la ENL.",
        justificacion="B (mayo 2023) es el rechazo inicial publico del CPA a la ENL. A (junio 2023) es el primer encuentro formal de dialogo entre esas mismas comunidades (CPA, Pai Ote) y las empresas Codelco/SQM/ENAMI, un mes despues, donde se expresa la misma desconfianza. Es la misma secuencia inaugural de acercamiento, no dos episodios inconexos."),
    "H060": dict(decision="mismo_macroproceso", confianza="media",
        razon="Mismo patron que H006/H077/H083: GPT extiende identidad especifica a partir de proximidad temporal y actores comunes, pero B no trata el tramite de Contraloria ni los terminos del contrato, sino demandas territoriales historicas.",
        justificacion="A es el cierre del ultimo tramite de Contraloria del acuerdo Codelco-SQM. B es la reunion de Boric con el CPA sobre demandas historicas de tierras y agua. Comparten la ENL como marco, no el procedimiento contractual especifico."),
    "H074": dict(decision="mismo_proceso_especifico", confianza="alta",
        razon="GPT exige que sea 'el mismo acto institucional' para calificar como especifico, un estandar mas estricto que el codebook, que admite 'controversia... reconocible'; el anuncio y su reaccion inmediata al dia siguiente constituyen un unico episodio reconocible.",
        justificacion="A es el discurso de anuncio de la ENL (20 abril 2023). B es la reaccion critica de Vladimir Reyes al dia siguiente (21 abril 2023), especificamente sobre ese anuncio y la falta de consulta previa a el. Continuidad directa de un mismo hecho noticioso."),
    "H075": dict(decision="mismo_proceso_especifico", confianza="alta",
        razon="Identico al par anterior (mismos documentos A/B); mismo razonamiento aplica.",
        justificacion="Duplicado de H074: mismo anuncio del 20 de abril de 2023 y la misma reaccion critica del dia siguiente."),
    "H077": dict(decision="mismo_macroproceso", confianza="media",
        razon="Mismo patron que H006/H060/H083: GPT trata 'secuencia de implementacion y legitimacion' como identidad especifica sin que B mencione el litigio Tianqi ni el fallo de la Corte de Apelaciones.",
        justificacion="A es el rechazo del reclamo de Tianqi contra el acuerdo Codelco-SQM. B es la reunion de Boric con el CPA sobre la ENL en general (restitucion de tierras, agua, infraestructura). Comparten la ENL como marco, no el litigio especifico."),
    "H079": dict(decision="mismo_proceso_especifico", confianza="media",
        razon="GPT no reconoce que ambos documentos son actos del MISMO actor (CPA, mismo presidente Vladimir Reyes) en una ventana de siete semanas, dentro de una campana continua de rechazo inicial a la ENL en 2023 -el mismo patron ya aceptado sin disputa en H038/H057/H092.",
        justificacion="A (30 junio 2023) es la negativa del CPA a reunirse con Boric. B (8 mayo 2023) es el rechazo publico inicial del CPA a la ENL, mismo dirigente. Es la misma secuencia de oposicion temprana del CPA, no dos actos inconexos."),
    "H080": dict(decision="mismo_proceso_especifico", confianza="media",
        razon="GPT separa 'compromiso corporativo' de 'condiciones juridicas' como si fueran procedimientos distintos, pero el propio texto A situa el compromiso de cero agua continental explicitamente 'dentro del proyecto definido con Codelco', es decir, como parte del mismo contrato que B formaliza juridicamente.",
        justificacion="A es el compromiso tecnico de SQM de cero agua continental, presentado ante el Senado como parte del acuerdo con Codelco. B es la toma de razon final de ese mismo acuerdo Codelco-SQM. Mismo contrato nombrado."),
    "H081": dict(decision="relacionado_tematicamente", confianza="media",
        razon="GPT y, en menor medida, la reconsideracion de este arbitraje para casos analogos (H021/H029) podrian sugerir macroproceso porque ambos mencionan la ENL; la diferencia es que A es un articulo tecnico generico (explicador del proceso productivo del litio) sin postura institucional propia, no un episodio o accion de un actor dentro de la ENL, a diferencia de H021/H029 donde ambos lados son posturas institucionales reales.",
        justificacion="A es un articulo explicativo generico sobre el proceso productivo de extraccion de litio y su uso de agua, que menciona el anuncio de la ENL solo como contexto. B es una convocatoria especifica de movilizacion del CPA. No hay continuidad de un macroproceso identificable, solo un tema compartido (agua y litio)."),
    "H083": dict(decision="mismo_macroproceso", confianza="media",
        razon="Mismo patron que H006/H060/H077: GPT trata el cierre juridico del litigio Tianqi y la reunion territorial como 'el mismo cierre social', pero B no se refiere al litigio ni a la Corte Suprema.",
        justificacion="A es la valoracion del CDE del fallo de la Corte Suprema sobre el litigio Tianqi. B es la reunion de Boric con el CPA sobre tierras y agua. Comparten la ENL como marco, no el litigio especifico."),
    "H086": dict(decision="mismo_proceso_especifico", confianza="media",
        razon="GPT trata el parrafo de Maricunga en B como 'aplicacion territorial generica' de la estrategia nacional, pero ese parrafo continua explicita y especificamente la misma linea narrativa de A (adquisicion de Salar Blanco por Codelco, seguida de consulta indigena para modificar el CEOL), no una mencion generica.",
        justificacion="A es la aceptacion de Codelco de modificar el proyecto de explotacion en Maricunga tras comprar Salar Blanco (nov 2023). B (marzo 2024) actualiza explicitamente ese mismo proceso: 'Codelco ha consolidado su posicion mediante la adquisicion del proyecto Salar Blanco, y prontamente se iniciara un proceso de Consulta Indigena para la modificacion del CEOL'. Continuidad textual directa del mismo proyecto especifico."),
    "H088": dict(decision="relacionado_tematicamente", confianza="media",
        razon="Igual que H081: GPT ve macroproceso porque ambos mencionan la ENL y los CEOL, pero B es un articulo panoramico generico sobre la politica de CEOL en multiples salares, sin postura institucional propia ni referencia a la disputa especifica de A (vicios de consulta indigena, division de comunidades por Corfo).",
        justificacion="A es una denuncia especifica de Hugo Flores sobre vicios de la consulta indigena y tacticas de division de comunidades por Corfo, con recursos de proteccion en curso. B es un articulo generico sobre el plan de CEOL de Chile en varios salares. No hay continuidad de proceso, solo tema compartido."),
    "H093": dict(decision="mismo_proceso_especifico", confianza="media",
        razon="Reconsideracion: en un primer analisis se penalizo la distancia temporal (2.5 anos) y que la reunion de 2023 nunca se realizo. Sin embargo, el propio texto B (2023) documenta que Boric se comprometio categoricamente en abril 2023 a reunirse personalmente con el CPA -compromiso especifico distinto del encuentro multietnico que el CPA declino-, y A (2026) es exactamente el cumplimiento de ESE compromiso especifico y nombrado. Hay un objeto reconocible (el compromiso presidencial de reunion directa con el CPA) que se rastrea de un texto al otro.",
        justificacion="B narra que el CPA declina asistir a una reunion multietnica en junio de 2023, pero documenta el compromiso presidencial especifico de reunirse directamente con el CPA. A es esa misma reunion directa Boric-CPA, cumplida en enero de 2026. Continuidad de un compromiso institucional especifico y nombrado, no solo de 'la relacion' en general."),
    "H097": dict(decision="mismo_proceso_especifico", confianza="media",
        razon="Mismo razonamiento que H093 (documentos equivalentes): el compromiso presidencial especifico de reunirse con el CPA, frustrado en 2023, se cumple en el texto A.",
        justificacion="Ver H093: mismo compromiso presidencial especifico rastreable entre ambos textos."),
    "H099": dict(decision="mismo_macroproceso", confianza="media",
        razon="GPT afirma que la alerta de Flores 'antecede y da contexto directo' a la reunion de Boric, pero el texto de la reunion (B) no menciona ni responde a la consulta indigena cuestionada ni a las tacticas de division de Corfo denunciadas en A; los temas de la reunion son otros (tierras, agua potable).",
        justificacion="A es la denuncia de Hugo Flores sobre la consulta indigena y division de comunidades por Corfo. B es la reunion de Boric con el CPA sobre restitucion de tierras y agua potable rural, sin referirse a la disputa de A. Comparten la ENL como marco, no el mismo procedimiento."),
    "H101": dict(decision="relacionado_tematicamente", confianza="media",
        razon="Igual que H081: A es un articulo tecnico generico, no una postura institucional o accion de un actor especifico dentro de la ENL.",
        justificacion="A es el mismo articulo tecnico generico de H081/H021 sobre el proceso productivo del litio y el agua. B es la demanda especifica de Pai Ote sobre diversidad de actores en Maricunga. Comparten tema (agua/litio), no continuidad de proceso."),
}

assert set(ARBITRATIONS.keys()) == {
    "H006","H008","H011","H021","H029","H034","H035","H053","H058","H060",
    "H074","H075","H077","H079","H080","H081","H083","H086","H088","H093",
    "H097","H099","H101",
}, "faltan o sobran casos en la tabla de arbitraje (deben ser exactamente los 23 desacuerdos)"

records = []
matches_gpt = matches_claude = matches_neither = 0
for cid, arb in ARBITRATIONS.items():
    g = gpt[cid]
    c = claude[cid]
    final = arb["decision"]
    if final == g["decision"] and final != c["decision"]:
        matches_gpt += 1
        tipo_consenso = "coincide_con_gpt"
    elif final == c["decision"] and final != g["decision"]:
        matches_claude += 1
        tipo_consenso = "coincide_con_claude"
    elif final == g["decision"] == c["decision"]:
        tipo_consenso = "coincide_con_ambos"  # no deberia pasar (son desacuerdos por definicion)
    else:
        matches_neither += 1
        tipo_consenso = "sintesis_nueva_no_coincide_con_ninguno"

    records.append({
        "case_id": cid,
        "decision_gpt": g["decision"], "confidence_gpt": g["confidence"],
        "decision_claude": c["decision"], "confidence_claude": c["confidence"],
        "decision_arbitro": final,
        "confidence_arbitro": arb["confianza"],
        "tipo_resolucion": tipo_consenso,
        "razon_diferencia_conceptual": arb["razon"],
        "justificacion_arbitro": arb["justificacion"],
    })

summary = {
    "advertencia_metodologica": (
        "El arbitro (Claude Sonnet 5) es el mismo modelo que genero una de las dos "
        "adjudicaciones originales. No es un tercer juez independiente. Se releyeron "
        "ambos textos completos y ambas justificaciones antes de cada decision, pero "
        "el sesgo de auto-confirmacion no puede descartarse: de 23 desacuerdos, la "
        f"decision arbitral coincidio con Claude en {matches_claude}, con GPT-5.6 en "
        f"{matches_gpt}, y fue una sintesis distinta a ambas en {matches_neither}. "
        "Se recomienda una arbitracion futura con un tercer modelo o revisor humano "
        "no involucrado en la ronda original antes de tratar esta resolucion como "
        "definitiva."
    ),
    "n_desacuerdos": 23,
    "coincide_con_claude": matches_claude,
    "coincide_con_gpt": matches_gpt,
    "sintesis_nueva": matches_neither,
    "casos": records,
}

with open(OUT + r"\H0000_DISAGREEMENTS_ADJUDICATED_2026_07_22.json", "w", encoding="utf-8") as f:
    json.dump(summary, f, ensure_ascii=False, indent=2)

print(f"[OK] Fase 3 escrita. coincide_claude={matches_claude} coincide_gpt={matches_gpt} sintesis={matches_neither}")
