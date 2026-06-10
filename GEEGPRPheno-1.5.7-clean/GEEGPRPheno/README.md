# GEE GPR Phenology

**GEE GPR Phenology** is a QGIS plugin for Sentinel-2 BOA/L2A imagery, Gaussian Process Regression (GPR) biophysical variable prediction, temporal gap filling and land surface phenology (LSP) metrics.

## Main tools

- Sentinel-2 BOA/L2A processing workflow.
- GPR spectral prediction using pre-trained models.
- Temporal gap filling.
- Double logistic fitting for phenological curve reconstruction.
- LSP metrics such as SOS, EOS, POS and LOS.
- Automatic QGIS layer loading with palettes and fixed visualization ranges consistent with the original JavaScript workflow.

## Version

Current public submission version: **1.5.5**.

## QGIS compatibility

- Minimum QGIS version: 3.16
- Maximum QGIS version: 3.99
- Category: Raster
- Processing provider: yes

## Required files in the plugin package

The official ZIP must contain a single root folder named `GEEGPRPheno/`. Inside that folder, the key files are:

- `metadata.txt`
- `__init__.py`
- `LICENSE`
- `plugin.py`
- `processing_provider.py`
- algorithm modules (`algo_*.py`)
- support modules (`gpr_algorithms.py`, `gee_palettes.py`, `qgis_utils.py`, `i18n.py`, `installer.py`)
- model data module (`s2boa_models.py`)
- `requirements.txt`
- `icon.png`

## Dependencies

The plugin requires Python packages that may need to be installed in the Python environment used by QGIS:

```text
numpy>=1.21.0
scipy>=1.7.0
rasterio>=1.3.0
```

For Google Earth Engine workflows, the Earth Engine Python API is also required:

```text
earthengine-api
```

For public repository safety, this plugin does **not** install dependencies automatically from QGIS. Install missing packages manually using the Python environment associated with your QGIS installation.

## Windows / OSGeo4W dependency installation

Close QGIS, open **OSGeo4W Shell**, and run commands equivalent to:

```bat
python -m pip install --upgrade pip
python -m pip install --upgrade numpy scipy rasterio earthengine-api
```

Then reopen QGIS and activate the plugin.

## License

This plugin is distributed under the MIT License. See `LICENSE`.

## Repository

https://github.com/jf-floresriera/GEE_GPR_Phenology

## Issue tracker

https://github.com/jf-floresriera/GEE_GPR_Phenology/issues


## Version 1.5.5 QGIS submission note

This version keeps the functionality of v1.5.2 and the security corrections introduced for the QGIS Plugin Repository. It validates Earth Engine HTTPS download URLs, avoids parameter names that can be misinterpreted as embedded credentials, and uses an optimized lightweight plugin icon. No credentials, tokens or private files are distributed with the plugin.
