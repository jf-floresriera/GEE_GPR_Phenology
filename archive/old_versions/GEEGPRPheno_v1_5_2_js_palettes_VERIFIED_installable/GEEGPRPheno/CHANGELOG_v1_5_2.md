# GEEGPRPheno v1.5.2

## Visual consistency with original JavaScript scripts

- Added `gee_palettes.py`, generated from the original `visualization.js` and `LSPGeneration.js`.
- QGIS automatic raster symbology now uses the same palettes and fixed min/max ranges as the original GEE scripts:
  - LAI: `LAI_palette`, 0–7
  - Cab/FVC/laiCab: `greens_palette` with original ranges
  - Cw/laiCw: `blues_palette` with original ranges
  - Cm/laiCm: `oranges_palette` with original ranges
  - NDVI: `viridis_palette`, 0–1
  - LSP metrics: `lsp_palette`, 0–365 DOY
- PDF map pages now use the same palettes and min/max visualization ranges, preserving visual equivalence with the JS workflow.

No changes were made to the GPR math, gapfilling, LSP computation, GEE authentication, AOI drawing, multilingual UI, or dependency workflow.
