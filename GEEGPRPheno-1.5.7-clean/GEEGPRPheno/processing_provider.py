# -*- coding: utf-8 -*-
from qgis.core import QgsProcessingProvider
from .algo_spectral_prediction import GPRSpectralPredictionAlgorithm
from .algo_gapfilling import GPRGapfillingAlgorithm
from .algo_lsp import LSPGenerationAlgorithm
from .algo_gee_pipeline import GEEAutoPipelineAlgorithm   # ← NUEVA LÍNEA


class GEEGPRPhenoProvider(QgsProcessingProvider):

    def loadAlgorithms(self):
        self.addAlgorithm(GPRSpectralPredictionAlgorithm())
        self.addAlgorithm(GPRGapfillingAlgorithm())
        self.addAlgorithm(LSPGenerationAlgorithm())
        self.addAlgorithm(GEEAutoPipelineAlgorithm())       # ← NUEVA LÍNEA

    def id(self):
        return 'geegprpheno'

    def name(self):
        return 'GEE GPR Phenology'

    def longName(self):
        return 'GEE GPR Phenology — Variables biofísicas y fenología Sentinel-2'

    def icon(self):
        from qgis.PyQt.QtGui import QIcon
        import os
        icon_path = os.path.join(os.path.dirname(__file__), 'icon.png')
        return QIcon(icon_path)
