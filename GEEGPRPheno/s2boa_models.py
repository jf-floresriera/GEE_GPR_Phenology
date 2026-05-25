# -*- coding: utf-8 -*-
"""
S2BOAModels — Modelos GPR pre-entrenados para variables biofísicas Sentinel-2 BOA.
Equivalente Python/NumPy del script GEE S2BOAModels.js
"""
import numpy as np

SCALE_FACTOR   = 10000
SENTINEL2_BANDS = ['B2','B3','B4','B5','B6','B7','B8','B8A','B11','B12']

def _gf_hp(ell2, sigf, sign):
    crops = ['maiz','trigo','cebada','girasol','colza',
             'guisante','alfalfa','remolacha','patata','media']
    return {c: {'ell2ts': ell2[i], 'sigfts': sigf[i], 'signts': sign[i]}
            for i, c in enumerate(crops)}

def _model(n, mx, sx, mm, hypell, hypsig, hypsign, gfhp, vi, mod, units):
    return dict(
        Xtrain=np.zeros((n, 10)),
        alpha_coefficients=np.zeros(n),
        mx=np.array(mx), sx=np.array(sx),
        meanmodel=mm,
        hypell=np.array(hypell),
        hypsig=hypsig,
        hypsign=np.array([hypsign]),
        XDXprecalc=np.zeros(n),
        gf_hyperparams=gfhp,
        scale_factor=SCALE_FACTOR,
        vegindex=vi, model=mod, units=units
    )

# ── Hiperparámetros de gapfilling compartidos ──────────────────────────────
_ELL = [0.0291,0.0257,0.0302,0.0482,0.0318,0.0438,0.0252,0.0218,0.0377,0.0316]
_SIG = [0.2629,0.1865,0.2005,0.1134,0.2918,0.1807,0.1847,0.3486,0.3048,0.2189]
_NOI = [0.0704,0.0610,0.0545,0.0374,0.0951,0.0543,0.1180,0.1002,0.0785,0.0703]
_GFP = _gf_hp(_ELL, _SIG, _NOI)

# ── Bandas Sentinel-2: mx y sx de normalización ────────────────────────────
_MX_STD = [0.0510,0.0961,0.0709,0.1434,0.3219,0.3981,0.4145,0.4207,0.2337,0.1520]
_SX_STD = [0.0451,0.0624,0.0729,0.0807,0.0821,0.0985,0.0998,0.1022,0.0896,0.0888]
_HEL    = [2.758e-4,0.1506,0.3552,0.0037,0.0105,0.0052,0.0795,3.891e-4,3.276e-5,0.0163]

MODELS = {
    'LAI': _model(
        161,
        [0.0534,0.0920,0.0692,0.1404,0.3138,0.3840,0.3978,0.4044,0.2244,0.1454],
        [0.0463,0.0601,0.0720,0.0775,0.0806,0.0969,0.0983,0.1010,0.0882,0.0852],
        1.447,
        [0.0004,0.1731,0.5180,0.0042,0.0143,0.0049,0.0703,0.0006,0.00004,0.0226],
        3.024, 0.00581,
        _gf_hp(
            [0.0337]*10,
            [144.7,86.99,99.30,40.99,308.9,89.14,66.35,307.4,195.0,138.4],
            [43.03,26.68,32.09,17.40,111.2,27.44,49.75,118.6,64.60,50.11]
        ),
        'LAI','MLRAmodelLAIBOArefGPRALEBD161samplesS210BMNI','m²/m²'
    ),
    'Cab': _model(
        248, _MX_STD, _SX_STD, 36.62, _HEL, 0.1811, 0.002449, _GFP,
        'Cab','MLRAmodelCabBOArefGPRALEBD248samplesS210BMNI','µg/cm²'
    ),
    'Cw': _model(
        248, _MX_STD, _SX_STD, 0.01328, _HEL, 0.1811, 0.002449, _GFP,
        'Cw','MLRAmodelCwBOArefGPRALEBD248samplesS210BMNI','cm'
    ),
    'Cm': _model(
        100, _MX_STD, _SX_STD, 0.00612, _HEL, 0.1811, 0.002449, _GFP,
        'Cm','MLRAmodelCmBOArefGPRALEBDS210BMNI','g/cm²'
    ),
    'FVC': _model(
        161, _MX_STD, _SX_STD, 0.6575, _HEL, 0.1811, 0.002449, _GFP,
        'FVC','MLRAmodelFVCBOArefGPRALEBD243samplesS210BMNI',''
    ),
    'laiCab': _model(
        191, _MX_STD, _SX_STD, 52.8, _HEL, 5.12, 0.00244, _GFP,
        'laiCab','MLRAmodellaiCabBOArefGPRALEBD191samplesS210BMNI','g/m²'
    ),
    'laiCm': _model(
        161, _MX_STD, _SX_STD, 3.14, _HEL, 0.42, 0.00244, _GFP,
        'laiCm','MLRAmodellaiCmBOArefGPRALEBDS210BMNI','g/m²'
    ),
    'laiCw': _model(
        183, _MX_STD, _SX_STD, 0.2148, _HEL, 0.1811, 0.002449,
        _gf_hp(
            [0.0337,0.0311,0.0336,0.0474,0.0351,0.0543,0.0288,0.0252,0.0408,0.0357],
            [239.35,128.99,146.11,53.42,429.09,132.91,104.64,431.19,268.04,176.50],
            [70.60,41.82,46.04,23.91,171.55,37.70,86.73,139.97,70.14,63.95]
        ),
        'laiCw','MLRAmodellaiCwBOArefGPRALEBD183samplesS210BMNI','g/m²'
    ),
}
