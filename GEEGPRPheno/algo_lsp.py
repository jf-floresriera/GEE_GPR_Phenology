# -*- coding: utf-8 -*-
"""
Algoritmo 3 QGIS: Generación de métricas LSP (Fenología).
Equivalente a los Scripts 4+5 (LSPGeneration + PhenologyFunctions).
Salida: ráster 12 bandas → SOS, EOS, POS, LOS, customSOS, customEOS,
        vmin, vmax, n1, m1, n2, m2
"""
import os, glob
import numpy as np
from datetime import datetime
from qgis.core import (
    QgsProcessingAlgorithm, QgsProcessingParameterFile,
    QgsProcessingParameterNumber, QgsProcessingParameterRasterDestination,
    QgsProcessingParameterBoolean, QgsProcessingException,
)
from qgis.PyQt.QtCore import QCoreApplication


class LSPGenerationAlgorithm(QgsProcessingAlgorithm):

    INPUT_FOLDER  = 'INPUT_FOLDER'
    CUSTOM_GAP    = 'CUSTOM_GAP'
    OUTPUT        = 'OUTPUT'

    def tr(self, s): return QCoreApplication.translate('LSPGeneration', s)
    def createInstance(self): return LSPGenerationAlgorithm()
    def name(self): return 'lsp_generation'
    def displayName(self): return self.tr('3. Generación de Métricas LSP (Fenología)')
    def group(self): return self.tr('GEE GPR Phenology')
    def groupId(self): return 'geegprpheno'

    def shortHelpString(self):
        return self.tr(
            '<b>Generación de Métricas LSP</b> — Equivalente Scripts 4+5<br><br>'
            'Ajusta la doble logística por píxel sobre la serie temporal gapfilled y extrae:<br>'
            'SOS, EOS, POS, LOS, customSOS, customEOS, vmin, vmax, n1, m1, n2, m2<br><br>'
            'Doble logística:<br>'
            'y(t) = vmin + vamp×[1/(1+exp(-m1(t-n1))) − 1/(1+exp(-m2(t-n2)))]<br><br>'
            '<b>Mínimo 6 imágenes</b> para ajustar la función.<br>'
            'Formato: YYYY-MM-DD_*.tif<br><br>'
            'Ref: M. Salinero-Delgado et al. — GEEGPRPhenoDemos'
        )

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterFile(
            self.INPUT_FOLDER,
            self.tr('Carpeta con rásters gapfilled temporales (YYYY-MM-DD_*.tif)'),
            behavior=QgsProcessingParameterFile.Folder))
        self.addParameter(QgsProcessingParameterNumber(
            self.CUSTOM_GAP,
            self.tr('Umbral relativo para SOS/EOS personalizado (0.0–1.0)'),
            type=QgsProcessingParameterNumber.Double,
            defaultValue=0.30, minValue=0.0, maxValue=1.0))
        self.addParameter(QgsProcessingParameterRasterDestination(
            self.OUTPUT, self.tr('Ráster de salida — métricas LSP (12 bandas)')))

    def processAlgorithm(self, parameters, context, feedback):
        import rasterio
        from .gpr_algorithms import get_double_logistic_params, add_doy

        folder      = self.parameterAsFile(parameters, self.INPUT_FOLDER, context)
        custom_gap  = self.parameterAsDouble(parameters, self.CUSTOM_GAP, context)
        output_path = self.parameterAsOutputLayer(parameters, self.OUTPUT, context)

        tif_files = sorted(glob.glob(os.path.join(folder, '*.tif')))
        if not tif_files:
            raise QgsProcessingException(f'No hay .tif en: {folder}')

        file_dates = {}
        for f in tif_files:
            bn = os.path.basename(f)
            try:
                datetime.strptime(bn[:10], '%Y-%m-%d')
                file_dates[bn[:10]] = f
            except ValueError:
                pass

        if len(file_dates) < 6:
            raise QgsProcessingException(
                f'Se necesitan ≥6 imágenes para ajustar la doble logística. Hay: {len(file_dates)}')

        feedback.pushInfo(f'Imágenes en serie temporal: {len(file_dates)}')

        first_f = list(file_dates.values())[0]
        with rasterio.open(first_f) as src:
            meta   = src.meta.copy()
            n_rows, n_cols = src.height, src.width
            nodata = src.nodata if src.nodata is not None else -9999.0
            n_pix  = n_rows * n_cols

        doys_list, arrays_list = [], []
        for date_str, fpath in sorted(file_dates.items()):
            doy, _ = add_doy(date_str)
            doys_list.append(float(doy))
            with rasterio.open(fpath) as src:
                arrays_list.append(src.read(1).astype(np.float32).flatten())
            if feedback.isCanceled(): return {}

        doys_arr   = np.array(doys_list)
        values_arr = np.stack(arrays_list, axis=0)

        feedback.setProgress(30)
        feedback.pushInfo('Ajustando doble logística...')

        valid = np.all(values_arr != nodata, axis=0) & np.all(np.isfinite(values_arr), axis=0)
        feedback.pushInfo(f'Píxeles válidos: {valid.sum()} / {n_pix}')

        if not valid.any():
            raise QgsProcessingException('No hay píxeles válidos en la serie temporal.')

        lsp = get_double_logistic_params(doys_arr, values_arr[:, valid], custom_gap=custom_gap)
        feedback.setProgress(80)

        band_names = ['sos','eos','pos','los','customsos','customeos',
                      'vmin','vmax','n1','m1','n2','m2']
        bands_out = []
        for bname in band_names:
            full = np.full(n_pix, nodata, dtype=np.float32)
            full[valid] = lsp[bname]
            bands_out.append(full.reshape(n_rows, n_cols))

        out_meta = meta.copy()
        out_meta.update({'count': len(band_names), 'dtype': 'float32',
                         'nodata': nodata, 'driver': 'GTiff'})
        with rasterio.open(output_path, 'w', **out_meta) as dst:
            for i, (arr, bname) in enumerate(zip(bands_out, band_names)):
                dst.write(arr, i + 1)
                dst.update_tags(i + 1, NAME=bname.upper(),
                                UNITS='DOY' if bname not in ('los','vmin','vmax') else 'days/index')
            dst.update_tags(BAND_NAMES=','.join(b.upper() for b in band_names),
                            CUSTOM_GAP=str(custom_gap))

        feedback.setProgress(100)
        feedback.pushInfo(f'✅ LSP guardado: {output_path}')
        feedback.pushInfo(f'Bandas: {", ".join(b.upper() for b in band_names)}')
        return {self.OUTPUT: output_path}
