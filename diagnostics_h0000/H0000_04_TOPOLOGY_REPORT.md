# H0000 — Topologia y diagnostico (Fase 3B)

```json
{
 "verificacion": {
  "frozen": {
   "docs": 170,
   "edges": 889,
   "bridges": 23,
   "weak_bridges_w050": 15
  },
  "observed": {
   "docs": 170,
   "edges": 889,
   "bridges": 23,
   "weak_bridges_w050": 15
  },
  "match": true
 },
 "densidad": 0.0619,
 "grado": {
  "min": 1,
  "p50": 9.0,
  "max": 29
 },
 "clustering_medio": 0.6506,
 "diametro": 11,
 "camino_medio": 4.145,
 "kcore_max": 15,
 "docs_kcore_max": 23,
 "bicomponentes": 29,
 "articulaciones": 23,
 "aristas_largas": 173,
 "pct_largas": 19.5,
 "poda_puentes_debiles_tamanos": [
  148,
  4,
  4,
  2,
  1,
  1,
  1,
  1
 ],
 "docs_por_ano": {
  "2022": 1,
  "2023": 37,
  "2024": 40,
  "2025": 79,
  "2026": 13
 },
 "e2_puentes_vs_no_puentes": {
  "w": {
   "puentes_mediana": 0.4889,
   "no_puentes_mediana": 0.5511999999999999,
   "mw_p": 0.04110178764644894,
   "diff_media_ic95": [
    -0.06201557498242789,
    0.046882830730996986
   ],
   "bh_q": 0.0411
  },
  "s_ref": {
   "puentes_mediana": 0.3123,
   "no_puentes_mediana": 0.4479,
   "mw_p": 0.0017603688616916848,
   "diff_media_ic95": [
    -0.11695604767044869,
    0.03877280713425047
   ],
   "bh_q": 0.00246
  },
  "s_emb": {
   "puentes_mediana": 0.9025,
   "no_puentes_mediana": 0.8556,
   "mw_p": 1.982680511814515e-05,
   "diff_media_ic95": [
    0.04711430741038256,
    0.08227411110553261
   ],
   "bh_q": 5e-05
  },
  "dias": {
   "puentes_mediana": 17.0,
   "no_puentes_mediana": 113.0,
   "mw_p": 0.00021658253349036792,
   "diff_media_ic95": [
    -187.3059167587107,
    -28.50649287077035
   ],
   "bh_q": 0.00038
  },
  "triangulos": {
   "puentes_mediana": 0.0,
   "no_puentes_mediana": 10.0,
   "mw_p": 3.409969737970037e-16,
   "diff_media_ic95": [
    -10.793360277136259,
    -9.998787528868359
   ],
   "bh_q": 0.0
  },
  "embeddedness": {
   "puentes_mediana": 0.0,
   "no_puentes_mediana": 0.56,
   "mw_p": 4.005839338851656e-16,
   "diff_media_ic95": [
    -0.568354994226328,
    -0.5336938221709007
   ],
   "bh_q": 0.0
  },
  "idf_max_ref_compartido": {
   "puentes_mediana": 1.0,
   "no_puentes_mediana": 0.8241,
   "mw_p": 0.0108800391350244,
   "diff_media_ic95": [
    -0.004977372979214553,
    0.14260777337082026
   ],
   "bh_q": 0.01269
  }
 },
 "chaining": {
  "pares_totales": 14365,
  "pares_directos": 889,
  "pares_solo_transitivos": 13476,
  "longitud_caminos_transitivos": {
   "2": 1780,
   "3": 3074,
   "4": 2955,
   "5": 2438,
   "6": 1693,
   "7": 846,
   "8": 463,
   "9": 188,
   "10": 37,
   "11": 2
  },
  "pares_dependientes_de_puentes": 4345,
  "pares_heterogeneos_transitivos_obj_y_terr": 5637,
  "dano_por_puente_top10": [
   {
    "puente": [
     "1938",
     "1943"
    ],
    "w": 0.4519,
    "dano_docs_separados": 11
   },
   {
    "puente": [
     "1108",
     "1943"
    ],
    "w": 0.4826,
    "dano_docs_separados": 5
   },
   {
    "puente": [
     "1943",
     "1945"
    ],
    "w": 0.4555,
    "dano_docs_separados": 5
   },
   {
    "puente": [
     "1232",
     "1233"
    ],
    "w": 0.6355,
    "dano_docs_separados": 2
   },
   {
    "puente": [
     "1936",
     "1945"
    ],
    "w": 0.5013,
    "dano_docs_separados": 2
   },
   {
    "puente": [
     "1275",
     "271"
    ],
    "w": 0.4584,
    "dano_docs_separados": 2
   },
   {
    "puente": [
     "1946",
     "6384"
    ],
    "w": 0.4894,
    "dano_docs_separados": 2
   },
   {
    "puente": [
     "1862",
     "1899"
    ],
    "w": 0.4694,
    "dano_docs_separados": 1
   },
   {
    "puente": [
     "105",
     "73"
    ],
    "w": 0.4721,
    "dano_docs_separados": 1
   },
   {
    "puente": [
     "1773",
     "188"
    ],
    "w": 0.4503,
    "dano_docs_separados": 1
   }
  ]
 }
}
```
