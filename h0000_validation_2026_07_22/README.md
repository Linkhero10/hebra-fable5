# Validación empírica de H0000 — README de reproducción

Esta carpeta contiene las Fases 1-4 del encargo de cierre de H0000
(auditoría e integración con la clave sellada, resultados por estrato,
resolución de desacuerdos, diagnóstico estructural). La arquitectura
jerárquica (Fases 5-6) vive en `../hebra_v2_experimental/` con su propio
README.

**Ningún script de esta carpeta modifica**: la hoja ciega
(`diagnostics_h0000/H0000_08_BLIND_REVIEW_SHEET.json`), la clave sellada
(`H0000_09_BLIND_KEY_DO_NOT_OPEN.json`), ni las respuestas originales de
los modelos en `PAQUETE_VALIDACION_MULTI_IA_COMPLETO_2026_07_22/`. Todos
son de solo lectura.

## Orden de ejecución (cada script depende del anterior)

```bash
cd fable5/h0000_validation_2026_07_22

python fase1_2_integrate.py                 # Fase 1: audita conteos, calcula kappa/matriz de confusion,
                                             # cruza con la clave sellada y las metricas de grafo.
                                             # -> H0000_VALIDATION_INTEGRATED_2026_07_22.json

python fase2_stratum.py                     # Fase 2: resultados por estrato/algoritmo, estricta vs amplia.
                                             # -> H0000_VALIDATION_BY_STRATUM_2026_07_22.csv

python fase3_adjudicate_disagreements.py     # Fase 3: arbitraje razonado de los 23 desacuerdos.
                                             # -> H0000_DISAGREEMENTS_ADJUDICATED_2026_07_22.json

python fase4_structural_diagnosis.py         # Fase 4: recalcula estratos post-arbitraje + junta addenda
                                             # de topologia ya congelados. -> _fase4_structural_evidence.json

python build_manifest_lock.py                # genera MANIFEST_2026_07_22.json y EXPERIMENT_LOCK_2026_07_22.json
```

Luego, para la arquitectura jerárquica experimental:

```bash
cd ../hebra_v2_experimental/src
python build_hierarchy.py
cd ..
python -m pytest tests/ -v
```

## Mapa de archivos

| Archivo | Fase | Contenido |
|---|---|---|
| `H0000_VALIDATION_INTEGRATED_2026_07_22.json` | 1 | Los 104 casos con decisión GPT/Claude, estrato/detalle de la clave, metadatos de arista y comunidad, distribución, kappa, matriz de confusión, lista de desacuerdos. |
| `H0000_VALIDATION_BY_STRATUM_2026_07_22.csv` | 2 | % estricto/amplio con IC95 Wilson por estrato, algoritmo, tipo de arista. |
| `H0000_DISAGREEMENTS_ADJUDICATED_2026_07_22.json` | 3 | Los 23 desacuerdos con decisión de cada modelo, decisión arbitral, confianza, razón conceptual, justificación textual. |
| `_fase4_structural_evidence.json` | 4 | Estratos recalculados post-arbitraje + evidencia de puentes/satélites/heterogeneidad/DSU ya congelada. |
| `H0000_FINAL_EMPIRICAL_REPORT_2026_07_22.md` | 1-4 | Informe integrador con todas las cifras, el diagnóstico A/B/C/D razonado, y el resumen de cierre. |
| `HEBRA_HIERARCHICAL_DESIGN_2026_07_22.md` | 5 | Diseño de la arquitectura macrohilo/subhilo (no código). |
| `MANIFEST_2026_07_22.json` / `EXPERIMENT_LOCK_2026_07_22.json` | — | Hashes de todos los entregables de esta carpeta + verificación de que v1 sigue intacto + banderas de guardrail (Gemini no usado como voto, ningún ganador declarado, árbitro no independiente declarado explícitamente). |
| `_intermediate_merged_cases.csv`, `_disagreements_raw.csv`, `_confusion_matrix_gpt_claude.csv`, `_stratum_stats_full.json` | 1-2 | Artefactos intermedios (prefijo `_`) usados por los scripts posteriores; se conservan por trazabilidad. |

## Limitaciones declaradas (léanse antes de citar cualquier cifra)

1. El árbitro de Fase 3 (Claude Sonnet 5) no es independiente de una de las
   dos adjudicaciones originales — ver advertencia completa en el informe
   final.
2. GPT-5.6 nunca usó categorías por debajo de `mismo_macroproceso` en los
   104 casos; Claude sí (6 veces). Esta asimetría de calibración no se
   corrige aquí, solo se reporta.
3. Ningún algoritmo de comunidad (Louvain/Leiden-CPM/Leiden-mod/Infomap) se
   declara ganador. DSU se muestra como no discriminativo, no como
   "peor" en sentido normativo.
4. No hay gold humano en ninguna cifra de este informe.
