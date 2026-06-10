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
      kstar   = exp(PtTDX - 0.5 * XDXprecalc)
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
    # JavaScript original:
    # k_star = exp(PtTDX - 0.5 * XDX_pre_calc)
    # Do NOT multiply PtTDX by 0.5; only the precomputed train norm receives 0.5.
    kstar     = np.exp(PtTDX - 0.5 * xdx_vec[:, None])  # (n_train, n_pix)

    pred = (alpha @ kstar) * arg1 + meanmodel
    # Match GEE behavior: only negative predictions are lifted to a tiny positive value.
    # Upper clipping is intentionally avoided because Cab/laiCm/laiCw may exceed 10.
    pred = np.where(pred < 0, 1e-5, pred)
    return pred.astype(np.float32)

# ══════════════════════════════════════════════════════════════════════════════
# SCRIPT 2 — Relleno temporal GPR con kernel RBF sobre tiempo
# ══════════════════════════════════════════════════════════════════════════════
def gpr_gapfilling_temporal(target_doy, obs_doys, obs_values, model, crop='media'):
    """
    target_doy  : float — días desde epoch 1970-01-01 de la fecha objetivo
    obs_doys    : np.ndarray (n_obs,)
    obs_values  : np.ndarray (n_obs, n_pixels)
    model       : dict
    crop        : str — clave en gf_hyperparams

    Kernel RBF temporal, as in the GEE JavaScript:
      K(t_i,t_j) = sigfts * exp(-0.5 * ell2ts * (t_i-t_j)²)
      alpha      = (K + signts*I)^-1 y
      k_star     = sigfts * exp(-0.5 * ell2ts * (t*-t_obs)²)
      pred       = k_star.T @ alpha

    This function expects obs_values already filtered to valid observations for
    the pixels being predicted. It raises a ValueError if fewer than two valid
    temporal observations are provided.
    """
    hp = model['gf_hyperparams'].get(crop) or model['gf_hyperparams'].get('media')
    if hp is None:
        raise ValueError(f'No gapfilling hyperparameters found for crop={crop!r}')

    ell2ts = float(hp['ell2ts'])
    sigfts = float(hp['sigfts'])
    signts = float(hp['signts'])
    if ell2ts <= 0 or sigfts <= 0 or signts <= 0:
        raise ValueError(
            f'Invalid temporal GPR hyperparameters for crop={crop!r}: '
            f'ell2ts={ell2ts}, sigfts={sigfts}, signts={signts}'
        )

    obs_doys = np.asarray(obs_doys, dtype=np.float64)
    if obs_doys.size < 2:
        raise ValueError('At least two valid temporal observations are required for GPR gapfilling.')

    y_mat = np.asarray(obs_values, dtype=np.float64)
    if y_mat.ndim == 1:
        y_mat = y_mat[:, None]
    if y_mat.shape[0] != obs_doys.size:
        raise ValueError('obs_values first dimension must match obs_doys length.')

    t_diff = obs_doys[:, None] - obs_doys[None, :]
    Kmat   = sigfts * np.exp(-0.5 * ell2ts * t_diff**2)
    KK     = Kmat + np.eye(obs_doys.size, dtype=np.float64) * signts

    # Solving triangular systems is numerically safer and faster than explicit inverses.
    jitter = 0.0
    for _ in range(5):
        try:
            L = np.linalg.cholesky(KK + np.eye(obs_doys.size) * jitter)
            break
        except np.linalg.LinAlgError:
            jitter = 1e-8 if jitter == 0.0 else jitter * 10.0
    else:
        raise np.linalg.LinAlgError('Temporal GPR covariance matrix is not positive definite.')

    alpha_vec = np.linalg.solve(L.T, np.linalg.solve(L, y_mat))
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
    NumPy implementation of PhenologyFunctions.get_Double_Logistic_Params.

    doys   : np.ndarray (n_times,)
    values : np.ndarray (n_times, n_pixels), with np.nan for missing values
    Retorna dict con SOS, EOS, POS, LOS, customSOS, customEOS, vmin, vmax,
    n1, m1, n2, m2.

    Main equivalence points with the JavaScript:
      - vmin/vmax are computed within DOY 60–304 using interval means
        0–5% and 95–100% rather than raw min/max over the full year.
      - n1/m1 are fitted from the first sigmoid in the window between
        doymin1=(2*doyn1-doymax) and doymax.
      - n2/m2 use the first sigmoid correction before linear regression,
        exactly as the GEE routine does.
    """
    doys = np.asarray(doys, dtype=np.float64)
    y = np.asarray(values, dtype=np.float64)
    if y.ndim == 1:
        y = y[:, None]
    if y.shape[0] != doys.size:
        raise ValueError('values first dimension must match doys length.')

    n_times, n_pix = y.shape
    if n_times < 6:
        raise ValueError('At least 6 temporal images are recommended for LSP metrics.')

    custom_gap = float(custom_gap)
    y = np.where(np.isfinite(y), y, np.nan)

    def _interval_mean(vals, low_pct, high_pct):
        """Per-pixel approximation of ee.Reducer.intervalMean(low, high)."""
        out = np.full(vals.shape[1], np.nan, dtype=np.float64)
        for p in range(vals.shape[1]):
            v = vals[:, p]
            v = v[np.isfinite(v)]
            if v.size == 0:
                continue
            lo = np.nanpercentile(v, low_pct)
            hi = np.nanpercentile(v, high_pct)
            m = (v >= lo) & (v <= hi)
            if m.any():
                out[p] = np.nanmean(v[m])
        return out

    season = (doys >= 60) & (doys <= 304)
    if not season.any():
        season = np.ones_like(doys, dtype=bool)

    y_season = y[season]
    vmin = _interval_mean(y_season, 0, 5)
    vmax = _interval_mean(y_season, 95, 100)
    vamp = vmax - vmin
    vmid = (vmax + vmin) * 0.5

    # Fallbacks for sparse/flat pixels.
    vmin = np.where(np.isfinite(vmin), vmin, np.nanmin(y, axis=0))
    vmax = np.where(np.isfinite(vmax), vmax, np.nanmax(y, axis=0))
    vamp = vmax - vmin
    vmid = (vmax + vmin) * 0.5

    # doymax: DOY where the value is closest to vmax.
    gap2max = np.abs(y - vmax[None, :])
    gap2max[~np.isfinite(gap2max)] = np.inf
    doymax_idx = np.argmin(gap2max, axis=0)
    pos = doys[doymax_idx]

    doyn_limit = 60.0
    n1_arr = np.full(n_pix, np.nan, dtype=np.float64)
    m1_arr = np.full(n_pix, np.nan, dtype=np.float64)
    n2_arr = np.full(n_pix, np.nan, dtype=np.float64)
    m2_arr = np.full(n_pix, np.nan, dtype=np.float64)
    customsos = np.full(n_pix, np.nan, dtype=np.float64)
    customeos = np.full(n_pix, np.nan, dtype=np.float64)

    for p in range(n_pix):
        yp = y[:, p]
        if not np.isfinite(vmin[p]) or not np.isfinite(vmax[p]) or not np.isfinite(vamp[p]) or vamp[p] <= 0:
            continue

        gap2mid = np.abs(yp - vmid[p])
        gap2mid[~np.isfinite(gap2mid)] = np.inf

        m_pre = (doys < pos[p]) & (doys >= pos[p] - doyn_limit) & np.isfinite(yp)
        m_post = (doys > pos[p]) & (doys <= pos[p] + doyn_limit) & np.isfinite(yp)
        if not m_pre.any() or not m_post.any():
            continue

        doyn1 = doys[m_pre][np.argmin(gap2mid[m_pre])]
        doyn2 = doys[m_post][np.argmin(gap2mid[m_post])]

        # First fitting window, as in douLogFitCol1.
        doymin1 = 2.0 * doyn1 - pos[p]
        fit1 = (doys >= doymin1) & (doys <= pos[p]) & np.isfinite(yp)
        if fit1.sum() < 3:
            continue

        vmin1 = np.nanmin(yp[fit1])
        vsos = vmin1 + custom_gap * (vmax[p] - vmin1)
        customsos[p] = doys[fit1][np.argmin(np.abs(yp[fit1] - vsos))]

        denom1 = yp[fit1] - vmin[p]
        numer1 = vmax[p] - yp[fit1]
        ok1 = (denom1 > 0) & (numer1 > 0) & np.isfinite(denom1) & np.isfinite(numer1)
        if ok1.sum() < 3:
            continue
        sig_x1 = np.log(numer1[ok1] / denom1[ok1])
        sig_y1 = doys[fit1][ok1]
        A1 = np.column_stack([np.ones_like(sig_x1), sig_x1])
        coef1, *_ = np.linalg.lstsq(A1, sig_y1, rcond=None)
        n1 = coef1[0]
        slope1 = coef1[1]
        if slope1 == 0 or not np.isfinite(slope1):
            continue
        m1 = -1.0 / slope1
        n1_arr[p] = n1
        m1_arr[p] = m1

        # Second fitting window, as in douLogFitCol2.
        doymin2 = 2.0 * doyn2 - pos[p]
        fit2 = (doys <= doymin2) & (doys >= pos[p]) & np.isfinite(yp)
        if fit2.sum() < 3:
            continue

        vmin2 = np.nanmin(yp[fit2])
        # Original JS uses vamp, not vamp2, for veos.
        veos = vmin2 + custom_gap * vamp[p]
        customeos[p] = doys[fit2][np.argmin(np.abs(yp[fit2] - veos))]

        t2 = doys[fit2]
        y2 = yp[fit2]
        with np.errstate(over='ignore', invalid='ignore', divide='ignore'):
            temp_sig1 = 1.0 / (1.0 + np.exp(-m1 * (t2 - n1)))
            sig_x1_num = vamp[p] * (1.0 - temp_sig1) + y2 - vmin[p]
            sig_x2_den = vamp[p] * temp_sig1 - y2 + vmin[p]
            ok2 = (sig_x1_num > 0) & (sig_x2_den > 0) & np.isfinite(sig_x1_num) & np.isfinite(sig_x2_den)
            if ok2.sum() < 3:
                continue
            sig_x2 = np.log(sig_x1_num[ok2] / sig_x2_den[ok2])

        sig_y2 = t2[ok2]
        A2 = np.column_stack([np.ones_like(sig_x2), sig_x2])
        coef2, *_ = np.linalg.lstsq(A2, sig_y2, rcond=None)
        n2 = coef2[0]
        slope2 = coef2[1]
        if slope2 == 0 or not np.isfinite(slope2):
            continue
        m2 = -1.0 / slope2
        n2_arr[p] = n2
        m2_arr[p] = m2

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
