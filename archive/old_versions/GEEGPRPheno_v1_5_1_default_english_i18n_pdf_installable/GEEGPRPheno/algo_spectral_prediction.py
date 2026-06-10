# -*- coding: utf-8 -*-
"""
Algoritmo 1 QGIS: Predicción Espectral GPR pixel a pixel.
Equivalente al Script 3 (GPRPredictedMean) del repositorio GEEGPRPhenoDemos.
"""
import numpy as np
from qgis.core import (
    QgsProcessingAlgorithm, QgsProcessingParameterRasterLayer,
    QgsProcessingParameterBand, QgsProcessingParameterEnum,
    QgsProcessingParameterRasterDestination, QgsProcessingParameterBoolean,
    QgsProcessingParameterNumber, QgsProcessingException,
)
from qgis.PyQt.QtCore import QCoreApplication
from .i18n import tr as _tr


class GPRSpectralPredictionAlgorithm(QgsProcessingAlgorithm):

    INPUT_RASTER    = 'INPUT_RASTER'
    VEG_INDEX       = 'VEG_INDEX'
    BAND_B2         = 'BAND_B2'
    BAND_B3         = 'BAND_B3'
    BAND_B4         = 'BAND_B4'
    BAND_B5         = 'BAND_B5'
    BAND_B6         = 'BAND_B6'
    BAND_B7         = 'BAND_B7'
    BAND_B8         = 'BAND_B8'
    BAND_B8A        = 'BAND_B8A'
    BAND_B11        = 'BAND_B11'
    BAND_B12        = 'BAND_B12'
    SCALE_FACTOR    = 'SCALE_FACTOR'
    APPLY_CLOUD_MASK= 'APPLY_CLOUD_MASK'
    CLOUD_MASK      = 'CLOUD_MASK'
    OUTPUT          = 'OUTPUT'
    ADD_TO_QGIS     = 'ADD_TO_QGIS'

    VEG_INDEX_OPTIONS = ['LAI','Cab','Cw','Cm','FVC','laiCab','laiCm','laiCw']

    def tr(self, s):
        return _tr(QCoreApplication.translate(self.__class__.__name__, s))
    def createInstance(self): return GPRSpectralPredictionAlgorithm()
    def name(self): return 'gpr_spectral_prediction'
    def displayName(self): return self.tr('1. Predicción Espectral GPR (pixel a pixel)')
    def group(self): return self.tr('GEE GPR Phenology')
    def groupId(self): return 'geegprpheno'

    def shortHelpString(self):
        return self.tr(
            '<b>Predicción Espectral GPR</b> — Equivalente Script 3 (GPRPredictedMean)<br><br>'
            'Aplica un modelo GPR pre-entrenado sobre las 10 bandas Sentinel-2 BOA '
            '(B2,B3,B4,B5,B6,B7,B8,B8A,B11,B12) para estimar píxel a píxel:<br>'
            'LAI, Cab, Cw, Cm, FVC, laiCab, laiCm, laiCw<br><br>'
            '<b>Factor de escala:</b> 10000 para S2 L2A estándar (DN); 1 si ya es [0,1].<br><br>'
            'Ref: M. Salinero-Delgado et al. — GEEGPRPhenoDemos'
        )

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterRasterLayer(
            self.INPUT_RASTER, self.tr('Ráster Sentinel-2 BOA (mínimo 10 bandas)')))
        self.addParameter(QgsProcessingParameterEnum(
            self.VEG_INDEX, self.tr('Variable biofísica a estimar'),
            options=self.VEG_INDEX_OPTIONS, defaultValue=0))

        band_defs = [
            (self.BAND_B2,  1,  'Banda B2  — Azul ~490nm'),
            (self.BAND_B3,  2,  'Banda B3  — Verde ~560nm'),
            (self.BAND_B4,  3,  'Banda B4  — Rojo ~665nm'),
            (self.BAND_B5,  4,  'Banda B5  — Red-Edge 1 ~705nm'),
            (self.BAND_B6,  5,  'Banda B6  — Red-Edge 2 ~740nm'),
            (self.BAND_B7,  6,  'Banda B7  — Red-Edge 3 ~783nm'),
            (self.BAND_B8,  7,  'Banda B8  — NIR ~842nm'),
            (self.BAND_B8A, 8,  'Banda B8A — NIR estrecho ~865nm'),
            (self.BAND_B11, 9,  'Banda B11 — SWIR1 ~1610nm'),
            (self.BAND_B12, 10, 'Banda B12 — SWIR2 ~2190nm'),
        ]
        for param, default, label in band_defs:
            self.addParameter(QgsProcessingParameterBand(
                param, self.tr(label),
                parentLayerParameterName=self.INPUT_RASTER,
                defaultValue=default, optional=False))

        self.addParameter(QgsProcessingParameterNumber(
            self.SCALE_FACTOR, self.tr('Factor de escala de las bandas'),
            type=QgsProcessingParameterNumber.Double,
            defaultValue=10000.0, minValue=1.0))
        self.addParameter(QgsProcessingParameterBoolean(
            self.APPLY_CLOUD_MASK, self.tr('Aplicar máscara de nubes/agua'),
            defaultValue=False))
        self.addParameter(QgsProcessingParameterRasterLayer(
            self.CLOUD_MASK, self.tr('Ráster máscara nubes (1=válido, 0=nube)'),
            optional=True))
        self.addParameter(QgsProcessingParameterBoolean(
            self.ADD_TO_QGIS, self.tr('Cargar resultado como capa raster en QGIS'),
            defaultValue=True))
        self.addParameter(QgsProcessingParameterRasterDestination(
            self.OUTPUT, self.tr('Ráster de salida — índice biofísico GPR')))

    def processAlgorithm(self, parameters, context, feedback):
        import rasterio
        from .s2boa_models import MODELS
        from .gpr_algorithms import gpr_spectral_prediction

        raster_layer = self.parameterAsRasterLayer(parameters, self.INPUT_RASTER, context)
        veg_idx_i    = self.parameterAsEnum(parameters, self.VEG_INDEX, context)
        veg_index    = self.VEG_INDEX_OPTIONS[veg_idx_i]
        scale_factor = self.parameterAsDouble(parameters, self.SCALE_FACTOR, context)
        apply_mask   = self.parameterAsBool(parameters, self.APPLY_CLOUD_MASK, context)
        output_path  = self.parameterAsOutputLayer(parameters, self.OUTPUT, context)
        add_to_qgis  = self.parameterAsBool(parameters, self.ADD_TO_QGIS, context)

        band_params = [self.BAND_B2, self.BAND_B3, self.BAND_B4, self.BAND_B5,
                       self.BAND_B6, self.BAND_B7, self.BAND_B8, self.BAND_B8A,
                       self.BAND_B11, self.BAND_B12]
        band_indices = [self.parameterAsInt(parameters, b, context) - 1
                        for b in band_params]

        model = MODELS[veg_index]
        feedback.pushInfo(f'Modelo: {veg_index} | Escala: {scale_factor}')

        with rasterio.open(raster_layer.source()) as src:
            meta   = src.meta.copy()
            n_rows, n_cols = src.height, src.width
            nodata = src.nodata if src.nodata is not None else -9999.0
            bands_data = np.stack(
                [src.read(bi + 1).astype(np.float32) for bi in band_indices],
                axis=-1)  # (rows, cols, 10)
            valid_pixel = np.any(bands_data > 0, axis=-1)   # True donde hay dato real S2
            cloud_mask  = valid_pixel.copy()                 # base: excluir nodata
            if apply_mask:
                mask_layer = self.parameterAsRasterLayer(parameters, self.CLOUD_MASK, context)
                if mask_layer:
                    with rasterio.open(mask_layer.source()) as msrc:
                        cloud_mask = msrc.read(1).astype(bool)

        # Match the original GEE workflow: Sentinel-2 L2A DN values are only divided
        # by the scale factor. No upper clipping is applied here because it changes
        # the spectrum before the GPR model; clouds/water should be handled by masks.
        bands_scaled = bands_data / scale_factor
        cloud_mask &= np.all(np.isfinite(bands_scaled), axis=-1)
        n_pix        = n_rows * n_cols
        bands_flat   = bands_scaled.reshape(n_pix, 10)
        mask_flat    = cloud_mask.flatten()
        valid_idx    = np.where(mask_flat)[0]
        pred_flat    = np.full(n_pix, nodata, dtype=np.float32)

        if len(valid_idx) == 0:
            raise QgsProcessingException('No hay píxeles válidos.')

        block = max(10000, len(valid_idx) // 10)
        for start in range(0, len(valid_idx), block):
            if feedback.isCanceled(): return {}
            end   = min(start + block, len(valid_idx))
            chunk = valid_idx[start:end]
            pred_flat[chunk] = gpr_spectral_prediction(bands_flat[chunk], model)
            feedback.setProgress(20 + int(70 * end / len(valid_idx)))

        pred_2d  = pred_flat.reshape(n_rows, n_cols)
        out_meta = meta.copy()
        out_meta.update({'count': 1, 'dtype': 'float32', 'nodata': nodata, 'driver': 'GTiff'})

        with rasterio.open(output_path, 'w', **out_meta) as dst:
            dst.write(pred_2d, 1)
            dst.update_tags(1, VEGINDEX=veg_index, UNITS=model['units'], MODEL=model['model'])

        if add_to_qgis:
            from .qgis_utils import queue_raster_layer
            queue_raster_layer(context, output_path, f'GPR_{veg_index}', feedback, group_name=self.tr('GEEGPRPheno - GPR pred'), style_kind='singleband', variable=veg_index)

        feedback.setProgress(100)
        feedback.pushInfo(f'✅ Guardado: {output_path}')
        return {self.OUTPUT: output_path}
