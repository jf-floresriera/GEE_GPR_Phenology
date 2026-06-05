# GEEGPRPheno v1.5.1

## Main changes

- Default interface language changed to English.
- Language selector keeps English, Spanish and Portuguese available.
- New language settings key (`GEEGPRPheno/language_v151`) so fresh installs open in English by default.
- Extended translation coverage for user-visible plugin fragments.
- PDF report text now follows the selected interface language.
- PDF labels for time series, maps, LSP atlas, histograms and report notes are localized.
- Layer group names and QGIS layer-loading messages are localized.
- Processing enum labels for data source, mask mode and crop type are localized while preserving internal model keys.

## Preserved from v1.5.0

- GEE authentication and project switching.
- Controlled dependency installer.
- AOI polygon drawing tool.
- GEE and local Sentinel-2 BOA sources.
- SCL/QA60 robust cloud-water masking.
- Spectral GPR prediction.
- Temporal GPR gapfilling.
- LSP computation.
- QGIS layer grouping and automatic symbology.
- PDF and CSV report generation.
