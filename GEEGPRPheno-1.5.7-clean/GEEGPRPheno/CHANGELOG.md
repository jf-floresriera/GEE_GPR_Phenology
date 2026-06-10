# Changelog

## 1.5.5 - Metadata normalization for QGIS repository upload

- Changed `hasProcessingProvider` from `yes` to `True`, following the boolean metadata format expected by QGIS.
- Removed the optional `deprecated` metadata line; the plugin is not deprecated by default.
- Kept the optimized lightweight icon and all security fixes from versions 1.5.3 and 1.5.4.
- No functional algorithmic code was removed.

## 1.5.4 - New QGIS upload with optimized icon

- Increased the plugin version because the QGIS Plugin Repository does not allow uploading a ZIP with a version number that already exists.
- Kept the validated HTTPS Google endpoint download introduced for the security scan.
- Kept the renamed optional GEE authentication JSON parameter to avoid false positive secret detection.
- Kept the optimized lightweight icon to reduce package size without removing functional Python modules.

## 1.5.3 - QGIS security scan fix

- Replaced generic `urllib.request.urlretrieve()` download calls with a validated HTTPS downloader restricted to Google/Earth Engine endpoints.
- Renamed the optional GEE JSON authentication-file parameter to avoid false-positive secret detection.
- Updated the plugin icon while preserving the processing algorithms and functional code.
- Kept MIT license and public-repository metadata for QGIS submission.

# GEEGPRPheno changelog

## Version 1.5.2 — QGIS Plugin Repository submission package

- Prepared a clean package for submission to the official QGIS Plugin Repository.
- Added `LICENSE` inside the plugin folder and aligned `metadata.txt` with `license=MIT`.
- Consolidated documentation to avoid multiple loose version-specific notes in the plugin root folder.
- Preserved all functional Python modules and model data, including `s2boa_models.py`.
- Preserved the original JavaScript color palettes and fixed visualization ranges for QGIS layers and PDF outputs.
- Kept dependency installation as manual instructions only; the public plugin package does not execute `pip` or shell commands from QGIS.

## Version 1.5.1

- Previous internal development version used as the base for the v1.5.2 publication package.
- Included improvements related to GEE/GPR phenology workflows and QGIS interface integration.

