#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Validation script for GEEGPRPheno mathematical core.
Run from the repository root:

    python tools/validate_math_equivalence.py

This script does not require QGIS. It validates:
1) Spectral GPR prediction against an independent transcription of the GEE JS formula.
2) Temporal GPR gapfilling against a direct kernel solve.
3) Basic LSP/double-logistic smoke test on a synthetic seasonal curve.
"""
from pathlib import Path
import sys
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "GEEGPRPheno"
sys.path.insert(0, str(PLUGIN))

from s2boa_models import MODELS  # noqa: E402
from gpr_algorithms import (      # noqa: E402
    gpr_spectral_prediction,
    gpr_gapfilling_temporal,
    get_double_logistic_params,
)


def independent_js_spectral_formula(X, model):
    """Independent NumPy transcription of GPRPredictedMean.js."""
    Xnorm = (X - model["mx"]) / model["sx"]
    Xnorm_ell = Xnorm * model["hypell"]
    PtTPt = -0.5 * np.sum(Xnorm_ell * Xnorm, axis=1)
    arg1 = np.exp(PtTPt) * float(model["hypsig"])
    PtTDX = model["Xtrain"] @ Xnorm_ell.T
    kstar = np.exp(PtTDX - 0.5 * model["XDXprecalc"][:, None])
    pred = (model["alpha_coefficients"] @ kstar) * arg1 + float(model["meanmodel"])
    return np.where(pred < 0, 1e-5, pred).astype(np.float32)


def validate_spectral():
    rng = np.random.default_rng(42)
    print("\n[Spectral GPR equivalence]")
    for name, model in MODELS.items():
        X = rng.uniform(0.02, 0.75, size=(100, 10)).astype(np.float64)
        expected = independent_js_spectral_formula(X, model)
        actual = gpr_spectral_prediction(X, model)
        maxabs = float(np.max(np.abs(expected - actual)))
        print(f"  {name:6s} max_abs_error={maxabs:.3e}")
        if not np.allclose(expected, actual, rtol=1e-6, atol=1e-5):
            raise AssertionError(f"Spectral model mismatch for {name}")


def validate_gapfilling():
    print("\n[Temporal GPR gapfilling]")
    model = MODELS["LAI"]
    hp = model["gf_hyperparams"]["media"]
    assert hp["ell2ts"] > 0 and hp["sigfts"] > 0 and hp["signts"] > 0

    obs_doys = np.array([19000.0, 19010.0, 19025.0, 19039.0])
    y = np.array([[1.0, 2.0], [1.4, 2.5], [2.2, 3.0], [2.0, 2.7]])
    target = 19020.0

    tdiff = obs_doys[:, None] - obs_doys[None, :]
    K = hp["sigfts"] * np.exp(-0.5 * hp["ell2ts"] * tdiff**2)
    K = K + np.eye(obs_doys.size) * hp["signts"]
    alpha = np.linalg.solve(K, y)
    kstar = hp["sigfts"] * np.exp(-0.5 * hp["ell2ts"] * (target - obs_doys) ** 2)
    expected = np.where(kstar @ alpha < 0, 1e-5, kstar @ alpha).astype(np.float32)
    actual = gpr_gapfilling_temporal(target, obs_doys, y, model, "media").ravel()

    print(f"  expected={expected} actual={actual}")
    if not np.allclose(expected, actual, rtol=1e-6, atol=1e-6):
        raise AssertionError("Gapfilling kernel mismatch")


def validate_lsp_smoke():
    print("\n[LSP smoke test]")
    doys = np.array([40, 70, 100, 130, 160, 190, 220, 250, 280, 310, 340], dtype=float)

    def dl(t):
        return 0.5 + 4.0 * (
            1.0 / (1.0 + np.exp(-0.08 * (t - 110.0)))
            - 1.0 / (1.0 + np.exp(-0.08 * (t - 250.0)))
        )

    values = np.stack([dl(doys), 1.2 * dl(doys)], axis=1)
    params = get_double_logistic_params(doys, values, custom_gap=0.3)
    print(f"  n1={params['n1']} n2={params['n2']} pos={params['pos']}")
    if not np.isfinite(params["pos"]).all():
        raise AssertionError("LSP POS contains non-finite values")


def main():
    validate_spectral()
    validate_gapfilling()
    validate_lsp_smoke()
    print("\nVALIDATION_OK")


if __name__ == "__main__":
    main()
