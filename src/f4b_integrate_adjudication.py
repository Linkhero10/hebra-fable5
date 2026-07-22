# F4-B v1 — Integracion de la adjudicacion externa (GPT-5.6 Thinking) con la
# clave sellada. Capa de evidencia: independent_expert_ai_adjudication
# (NO validacion humana). No modifica parametros, codigo del modelo, umbrales,
# referentes ni clustering: solo analisis.
#
# Definiciones preinscritas:
#  - ESTRICTO: solo "mismo_proceso" cuenta como identidad positiva.
#  - "relacionado" se reporta por separado, nunca como acierto.
#  - "indeterminado" queda fuera del denominador principal; sensibilidad
#    aparte contandolo como error.
#  - ISO20: "aislado_correcto" vs "pertenece_a_un_proceso" (sobreabstencion).
#  - IC 95% Wilson para proporciones.
# Roles por estrato (del diseno sellado):
#  positivos del sistema: P50, L30, U30 (aristas aceptadas)
#  negativos del sistema: R30 (rechazo cercano), HN50 (negativos dificiles),
#                         FN30 (candidatos a falso negativo)
#  abstencion:            ISO20

import hashlib
import json
import math
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
ADJ = BASE / "validacion" / "HEBRA_F4B_EXPERT_AI_ADJUDICATION_BLIND.json"
KEY = BASE / "outputs" / "f4b_blind_key_DO_NOT_OPEN.json"
SHEET_SEAL = BASE / "outputs" / "f4b_blind_sheet_SEAL.txt"
OUT_JSON = BASE / "outputs" / "f4b_v1_performance.json"
OUT_MD = BASE / "V1_PERFORMANCE_FINAL_2026_07_22.md"

POS_STRATA = ["P50", "L30", "U30"]
NEG_STRATA = ["R30", "HN50", "FN30"]


def wilson(k, n, z=1.96):
    if n == 0:
        return (None, None)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (round(c - h, 3), round(c + h, 3))


def main() -> None:
    adj_sha = hashlib.sha256(ADJ.read_bytes()).hexdigest()
    adj = json.loads(ADJ.read_text(encoding="utf-8"))
    key = json.loads(KEY.read_text(encoding="utf-8"))
    verdict = {it["item_id"]: it["expert_ai_verdict"] for it in adj["items"]}
    conf = {it["item_id"]: it.get("expert_ai_confidence", "") for it in adj["items"]}
    assert len(verdict) == 240

    by_stratum = defaultdict(Counter)
    hn_subtype = defaultdict(Counter)
    for iid, meta in key.items():
        s = meta["strato"]
        by_stratum[s][verdict[iid]] += 1
        if s == "HN50":
            hn_subtype[meta.get("tipo", "?")][verdict[iid]] += 1

    def block(c: Counter, positive_label="mismo_proceso"):
        n_total = sum(c.values())
        ind = c.get("indeterminado", 0)
        n_det = n_total - ind
        pos = c.get(positive_label, 0)
        rel = c.get("relacionado", 0)
        neg = c.get("no_relacionado", 0)
        out = {
            "n": n_total, "indeterminado": ind,
            "mismo_proceso": pos, "relacionado": rel, "no_relacionado": neg,
            "prec_estricta_det": round(pos / n_det, 3) if n_det else None,
            "ic95_det": wilson(pos, n_det),
            "sens_indet_como_error": round(pos / n_total, 3) if n_total else None,
            "ic95_sens": wilson(pos, n_total),
        }
        return out

    res = {"positivos": {}, "negativos": {}, "aislados": {}}
    pooled_pos = Counter()
    for s in POS_STRATA:
        res["positivos"][s] = block(by_stratum[s])
        pooled_pos += by_stratum[s]
    res["positivos"]["POOLED_P50_L30_U30"] = block(pooled_pos)

    for s in NEG_STRATA:
        c = by_stratum[s]
        n_total = sum(c.values())
        ind = c.get("indeterminado", 0)
        n_det = n_total - ind
        fn = c.get("mismo_proceso", 0)  # identidad real que el sistema NO enlazo
        res["negativos"][s] = {
            "n": n_total, "indeterminado": ind,
            "mismo_proceso_FN": fn, "relacionado": c.get("relacionado", 0),
            "no_relacionado_ok": c.get("no_relacionado", 0),
            "tasa_FN_det": round(fn / n_det, 3) if n_det else None,
            "ic95": wilson(fn, n_det),
        }
    res["negativos"]["HN50_subtipos"] = {k: dict(v) for k, v in hn_subtype.items()}

    ciso = by_stratum["ISO20"]
    n_iso = sum(ciso.values())
    res["aislados"]["ISO20"] = {
        "n": n_iso,
        "aislado_correcto": ciso.get("aislado_correcto", 0),
        "pertenece_a_un_proceso": ciso.get("pertenece_a_un_proceso", 0),
        "indeterminado": ciso.get("indeterminado", 0),
        "sobreabstencion_det": (
            round(ciso.get("pertenece_a_un_proceso", 0)
                  / max(1, n_iso - ciso.get("indeterminado", 0)), 3)),
    }

    # Sintesis de errores
    pool = res["positivos"]["POOLED_P50_L30_U30"]
    sintesis = {
        "falsos_positivos_confirmados": pool["no_relacionado"],
        "mezcla_potencial_relacionado": pool["relacionado"],
        "falsos_negativos_confirmados": sum(
            res["negativos"][s]["mismo_proceso_FN"] for s in NEG_STRATA),
        "sobreabstencion_docs": ciso.get("pertenece_a_un_proceso", 0),
        "nota_fragmentacion": (
            "FN en R30/HN50/FN30 + sobreabstencion ISO son la evidencia de "
            "fragmentacion/sobreabstencion; los FP y 'relacionado' en "
            "positivos son la evidencia de mezcla."),
    }

    out = {
        "schema_version": 1,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "evidence_layer": "independent_expert_ai_adjudication",
        "reviewer": adj.get("reviewer"),
        "status_original": adj.get("status"),
        "hashes": {
            "adjudicacion_original_sha256": adj_sha,
            "hoja_sellada": SHEET_SEAL.read_text(encoding="utf-8").split()[0],
            "clave_sha256": hashlib.sha256(KEY.read_bytes()).hexdigest(),
            "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        },
        "confianza_reviewer": dict(Counter(conf.values())),
        "resultados": res,
        "sintesis_errores": sintesis,
        "reglas": [
            "estricto: solo mismo_proceso es positivo",
            "relacionado reportado aparte",
            "indeterminado fuera del denominador principal; sensibilidad aparte",
            "sin cambios de parametros/codigo/umbrales/referentes/clustering",
        ],
    }
    OUT_JSON.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({"positivos_pooled": pool,
                      "negativos": {s: res["negativos"][s] for s in NEG_STRATA},
                      "aislados": res["aislados"]["ISO20"],
                      "sintesis": sintesis}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
