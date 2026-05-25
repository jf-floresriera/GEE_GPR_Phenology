# -*- coding: utf-8 -*-
"""
gpr_algorithms.py
=================
Núcleo matemático del pipeline GPR. Equivalente Python/NumPy de:
  Script 2 — GPRGapfilling     → gpr_gapfilling_temporal()
  Script 3 — GPRPredictedMean  → gpr_spectral_prediction()
  Script 4 — LSPGeneration     → get_double_logistic_params(), double_logistic_fitting()
  Script 5 — PhenologyFunctions→ add_doy()
"""
import numpy as np
from datetime import datetime


# ══════════════════════════════════════════════════════════════════════════════
# SCRIPT 3 — Predicción espectral GPR pixel a pixel
# ══════════════════════════════════════════════════════════════════════════════
def gpr_spectral_prediction(bands_array, model):
    """
    bands_array : np.ndarray (n_pixels, 10) — bandas S2 ya escaladas [0,1]
    model       : dict  — modelo de s2boa_models.MODELS
    Retorna     : np.ndarray (n_pixels,) float32
    
    Matemática (fiel al script GEE):
      imnorm_ell2D = (X-mx)/sx * hypell
      imnorm_2D    = (X-mx)/sx
      PtTPt   = -0.5 * sum(imnorm_ell2D * imnorm_2D, axis=1)
      PtTDX   = Xtrain @ imnorm_ell2D.T
      arg1    = exp(PtTPt) * hypsig
      kstar   = exp(0.5 * (PtTDX - XDXprecalc))
      pred    = (alpha @ kstar) * arg1 + meanmodel
    """
    Xtrain    = model['Xtrain']
    alpha     = model['alpha_coefficients']
    mx        = model['mx']
    sx        = model['sx']
    hypell    = model['hypell']
    hypsig    = float(model['hypsig'])
    XDX       = model['XDXprecalc']
    meanmodel = float(model['meanmodel'])

    Xnorm     = (bands_array - mx) / sx           # (n_pix, 10)
    Xnorm_ell = Xnorm * hypell                     # (n_pix, 10)
    PtTPt     = -0.5 * np.sum(Xnorm_ell * Xnorm, axis=1)  # (n_pix,)
    arg1      = np.exp(PtTPt) * hypsig

    PtTDX     = Xtrain @ Xnorm_ell.T              # (n_train, n_pix)
    xdx_vec   = XDX if XDX.ndim == 1 else np.sum(XDX * Xtrain, axis=1)
    kstar     = np.exp(0.5 * (PtTDX - xdx_vec[:, None]))  # (n_train, n_pix)

    pred = (alpha @ kstar) * arg1 + meanmodel
    pred = np.where(pred < 0, 1e-5, pred)
    return pred.astype(np.float32)


# ══════════════════════════════════════════════════════════════════════════════
# SCRIPT 2 — Relleno temporal GPR con kernel RBF sobre tiempo
# ══════════════════════════════════════════════════════════════════════════════
def gpr_gapfilling_temporal(target_doy, obs_doys, obs_values, model, crop='media'):
    """
    target_doy  : float  — días desde epoch 1970-01-01 de la fecha objetivo
    obs_doys    : np.ndarray (n_obs,)
    obs_values  : np.ndarray (n_obs, n_pixels)
    model       : dict
    crop        : str  — clave en gf_hyperparams

    Kernel RBF temporal:
      K(t_i,t_j) = sigfts * exp(-0.5 * ell2ts * (t_i-t_j)²)
    Predicción:
      L      = cholesky(K + signts*I)
      alpha  = L.T⁻¹ @ (L⁻¹ @ y)
      k_star = sigfts * exp(-0.5 * ell2ts * (t*-t_obs)²)
      pred   = k_star.T @ alpha
    """
    hp     = model['gf_hyperparams'][crop]
    ell2ts = float(hp['ell2ts'])
    sigfts = float(hp['sigfts'])
    signts = float(hp['signts'])

    n_obs  = len(obs_doys)
    t_diff = obs_doys[:, None] - obs_doys[None, :]
    Kmat   = sigfts * np.exp(-0.5 * ell2ts * t_diff**2)
    KK     = Kmat + np.eye(n_obs) * signts

    try:
        L = np.linalg.cholesky(KK)
    except np.linalg.LinAlgError:
        L = np.linalg.cholesky(KK + np.eye(n_obs) * 1e-6)

    y_mat     = obs_values if obs_values.ndim == 2 else obs_values[:, None]
    Linv      = np.linalg.inv(L)
    alpha_vec = Linv.T @ (Linv @ y_mat)

    kstar = sigfts * np.exp(-0.5 * ell2ts * (float(target_doy) - obs_doys)**2)
    pred  = kstar @ alpha_vec
    pred  = np.where(pred < 0, 1e-5, pred)
    return pred.astype(np.float32)


# ══════════════════════════════════════════════════════════════════════════════
# SCRIPT 5 — addDoy
# ══════════════════════════════════════════════════════════════════════════════
def add_doy(date_str):
    """date_str: 'YYYY-MM-DD' → (doy:int, days_since_epoch:float)"""
    dt      = datetime.strptime(date_str, '%Y-%m-%d')
    doy     = dt.timetuple().tm_yday
    days_ep = float((dt - datetime(1970, 1, 1)).days)
    return doy, days_ep


# ══════════════════════════════════════════════════════════════════════════════
# SCRIPT 5 — getDoubleLogisticParams + doubleLogisticFitting
# ══════════════════════════════════════════════════════════════════════════════
def get_double_logistic_params(doys, values, custom_gap=0.30):
    """
    doys   : np.ndarray (n_times,)
    values : np.ndarray (n_times, n_pixels)
    Retorna dict con SOS,EOS,POS,LOS,customSOS,customEOS,vmin,vmax,n1,m1,n2,m2

    Doble logística:
      y(t) = vmin + vamp*[1/(1+exp(-m1*(t-n1))) - 1/(1+exp(-m2*(t-n2)))]
    """
    n_times, n_pix = values.shape
    doys  = doys.astype(float)
    vmin  = np.nanmin(values, axis=0)
    vmax  = np.nanmax(values, axis=0)
    vamp  = vmax - vmin
    pos   = doys[np.nanargmax(values, axis=0)]

    limit   = max(np.median(np.diff(doys)) * n_times * 0.25, 30.0)
    n1_arr  = np.full(n_pix, np.nan)
    m1_arr  = np.full(n_pix, np.nan)
    n2_arr  = np.full(n_pix, np.nan)
    m2_arr  = np.full(n_pix, np.nan)

    for p in range(n_pix):
        if vamp[p] == 0:
            continue
        # Fase ascendente → n1, m1
        mask = (doys >= pos[p] - limit) & (doys <= pos[p])
        if mask.sum() >= 3:
            y_rel = np.clip((values[mask, p] - vmin[p]) / vamp[p], 1e-6, 1-1e-6)
            sigx  = np.log((1 - y_rel) / y_rel)
            A     = np.column_stack([sigx, np.ones_like(sigx)])
            coef, *_ = np.linalg.lstsq(A, doys[mask], rcond=None)
            if coef[0] != 0:
                m1_arr[p] = -1.0 / coef[0]
                n1_arr[p] = coef[1]
        # Fase descendente → n2, m2
        mask = (doys > pos[p]) & (doys <= pos[p] + limit)
        if mask.sum() >= 3:
            y_rel = np.clip((values[mask, p] - vmin[p]) / vamp[p], 1e-6, 1-1e-6)
            sigx  = np.log((1 - y_rel) / y_rel)
            A     = np.column_stack([sigx, np.ones_like(sigx)])
            coef, *_ = np.linalg.lstsq(A, doys[mask], rcond=None)
            if coef[0] != 0:
                m2_arr[p] = -1.0 / coef[0]
                n2_arr[p] = coef[1]

    # SOS/EOS personalizados por umbral relativo
    customsos = np.full(n_pix, np.nan)
    customeos = np.full(n_pix, np.nan)
    for p in range(n_pix):
        thr = vmin[p] + custom_gap * vamp[p]
        m_a = doys <= pos[p]
        if m_a.sum() > 0:
            customsos[p] = doys[m_a][np.argmin(np.abs(values[m_a, p] - thr))]
        m_d = doys > pos[p]
        if m_d.sum() > 0:
            customeos[p] = doys[m_d][np.argmin(np.abs(values[m_d, p] - thr))]

    return {
        'vmin':      vmin.astype(np.float32),
        'vmax':      vmax.astype(np.float32),
        'n1':        n1_arr.astype(np.float32),
        'm1':        m1_arr.astype(np.float32),
        'n2':        n2_arr.astype(np.float32),
        'm2':        m2_arr.astype(np.float32),
        'sos':       n1_arr.astype(np.float32),
        'eos':       n2_arr.astype(np.float32),
        'pos':       pos.astype(np.float32),
        'los':       (n2_arr - n1_arr).astype(np.float32),
        'customsos': customsos.astype(np.float32),
        'customeos': customeos.astype(np.float32),
    }


def double_logistic_fitting(dl_params, doys_fit):
    """
    Genera la curva doble logística ajustada para los DOYs dados.
    Retorna np.ndarray (n_times, n_pixels)
    """
    vmin = dl_params['vmin'][None, :]
    vamp = (dl_params['vmax'] - dl_params['vmin'])[None, :]
    n1   = dl_params['n1'][None, :]
    m1   = dl_params['m1'][None, :]
    n2   = dl_params['n2'][None, :]
    m2   = dl_params['m2'][None, :]
    t    = doys_fit[:, None].astype(float)

    term1  = 1.0 / (1.0 + np.exp(-m1 * (t - n1)))
    term2  = 1.0 / (1.0 + np.exp(-m2 * (t - n2)))
    return (vmin + vamp * (term1 - term2)).astype(np.float32)
