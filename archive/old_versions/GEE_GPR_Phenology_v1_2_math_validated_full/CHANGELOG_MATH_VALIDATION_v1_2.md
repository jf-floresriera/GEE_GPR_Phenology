# Changelog v1.2.0 — Mathematical validation patch

## Fixed

- Corrected the spectral GPR kernel term from `exp(0.5 * (PtTDX - XDXprecalc))` to `exp(PtTDX - 0.5 * XDXprecalc)`, matching the original GEE JavaScript.
- Removed the fixed upper clipping at 10 from spectral GPR predictions. The JavaScript only clips negative values to `1e-5`.
- Restored temporal GPR gapfilling hyperparameters from `S2BOAModels.js`; previous Python dictionaries contained zeros.
- Improved temporal gapfilling so pixels with incomplete but sufficient valid observations are processed instead of being discarded.
- Reworked LSP parameter extraction to better match the original `PhenologyFunctions.js` workflow.
- Avoided spectral reflectance clipping before GPR prediction; Sentinel-2 bands are divided by the scale factor without artificial upper truncation.

## Added

- `VALIDACION_MATEMATICA_MODELOS.md`: technical validation report.
- `tools/validate_math_equivalence.py`: standalone NumPy validation script, runnable without QGIS.

## Validated

- Spectral GPR models LAI, Cab, Cm, Cw, FVC, laiCab, laiCm and laiCw match an independent NumPy transcription of the JavaScript formula with zero numerical difference in the validation test.
- Temporal GPR gapfilling matches a direct RBF kernel solve on a controlled test case.
- LSP returns finite and coherent parameters on a synthetic double-logistic seasonal curve.
