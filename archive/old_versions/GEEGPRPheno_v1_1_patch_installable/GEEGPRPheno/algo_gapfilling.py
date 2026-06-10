# -*- coding: utf-8 -*-
"""
Algoritmo 2 QGIS: Relleno temporal de series GPR (Gapfilling).
Equivalente al Script 2 (GPRGapfilling) del repositorio GEEGPRPhenoDemos.
"""
import os, glob
import numpy as np
from datetime import datetime, timedelta
from qgis.core import (
    QgsProcessingAlgorithm, QgsProcessingParameterFile,
    QgsProcessingParameterString, QgsProcessingParameterEnum,
    QgsProcessingParameterNumber, QgsProcessingParameterBoolean,
    QgsProcessingParameterRasterDestination,
    QgsProcessingException,
)
from qgis.PyQt.QtCore import QCoreApplication


class GPRGapfillingAlgorithm(QgsProcessingAlgorithm):

    INPUT_FOLDER = 'INPUT_FOLDER'
    TARGET_DATE  = 'TARGET_DATE'
    TIME_WINDOW  = 'TIME_WINDOW'
    VEG_INDEX    = 'VEG_INDEX'
    CROP_TYPE    = 'CROP_TYPE'
    OUTPUT       = 'OUTPUT'
    ADD_TO_QGIS  = 'ADD_TO_QGIS'

    VEG_INDEX_OPTIONS = ['LAI','Cab','Cw','Cm','FVC','laiCab','laiCm','laiCw']
    CROP_OPTIONS      = ['media','maiz','trigo','cebada','girasol',
                         'colza','guisante','alfalfa','remolacha','patata']

    def tr(self, s): return QCoreApplication.translate('GPRGapfilling', s)
    def createInstance(self): return GPRGapfillingAlgorithm()
    def name(self): return 'gpr_gapfilling'
    def displayName(self): return self.tr('2. Relleno Temporal de Series GPR (Gapfilling)')
    def group(self): return self.tr('GEE GPR Phenology')
    def groupId(self): return 'geegprpheno'

    def shortHelpString(self):
        return self.tr(
            '<b>GPR Gapfilling Temporal</b> — Equivalente Script 2 (GPRGapfilling)<br><br>'
            'Usa GPR con kernel RBF temporal para rellenar lagunas en la serie temporal '
            'del índice biofísico causadas por nubes.<br><br>'
            '<b>Formato de archivos:</b> YYYY-MM-DD_*.tif (ej: 2020-04-11_LAI.tif)<br><br>'
            'Kernel RBF: K(t_i,t_j) = sigfts × exp(-0.5 × ell2ts × (t_i-t_j)²)<br>'
            'Hiperparámetros pre-calibrados por cultivo e índice biofísico.<br><br>'
            'Ref: M. Salinero-Delgado et al. — GEEGPRPhenoDemos'
        )

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterFile(
            self.INPUT_FOLDER,
            self.tr('Carpeta con rásters del índice (YYYY-MM-DD_*.tif)'),
            behavior=QgsProcessingParameterFile.Folder))
        self.addParameter(QgsProcessingParameterString(
            self.TARGET_DATE, self.tr('Fecha objetivo (YYYY-MM-DD)'),
            defaultValue='2020-04-11'))
        self.addParameter(QgsProcessingParameterNumber(
            self.TIME_WINDOW, self.tr('Ventana temporal (±días)'),
            type=QgsProcessingParameterNumber.Integer,
            defaultValue=30, minValue=1, maxValue=180))
        self.addParameter(QgsProcessingParameterEnum(
            self.VEG_INDEX, self.tr('Variable biofísica'),
            options=self.VEG_INDEX_OPTIONS, defaultValue=0))
        self.addParameter(QgsProcessingParameterEnum(
            self.CROP_TYPE, self.tr('Tipo de cultivo'),
            options=self.CROP_OPTIONS, defaultValue=0))
        self.addParameter(QgsProcessingParameterBoolean(
            self.ADD_TO_QGIS, self.tr('Cargar resultado como capa raster en QGIS'),
            defaultValue=True))
        self.addParameter(QgsProcessingParameterRasterDestination(
            self.OUTPUT, self.tr('Ráster de salida — serie gapfilled')))

    def processAlgorithm(self, parameters, context, feedback):
        import rasterio
        from .s2boa_models import MODELS
        from .gpr_algorithms import gpr_gapfilling_temporal

        folder      = self.parameterAsFile(parameters, self.INPUT_FOLDER, context)
        target_date = self.parameterAsString(parameters, self.TARGET_DATE, context).strip()
        time_window = self.parameterAsInt(parameters, self.TIME_WINDOW, context)
        veg_index   = self.VEG_INDEX_OPTIONS[self.parameterAsEnum(parameters, self.VEG_INDEX, context)]
        crop        = self.CROP_OPTIONS[self.parameterAsEnum(parameters, self.CROP_TYPE, context)]
        output_path = self.parameterAsOutputLayer(parameters, self.OUTPUT, context)
        add_to_qgis = self.parameterAsBool(parameters, self.ADD_TO_QGIS, context)

        model = MODELS[veg_index]
        feedback.pushInfo(f'Gapfilling: {veg_index} | {crop} | {target_date} ±{time_window}d')

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

        if not file_dates:
            raise QgsProcessingException('Ningún archivo con formato YYYY-MM-DD_*.tif encontrado.')

        target_dt = datetime.strptime(target_date, '%Y-%m-%d')
        obs_dates = {d: f for d, f in file_dates.items()
                     if abs((datetime.strptime(d, '%Y-%m-%d') - target_dt).days) <= time_window}

        feedback.pushInfo(f'Observaciones en ventana: {len(obs_dates)}')
        if len(obs_dates) < 2:
            raise QgsProcessingException(f'Se necesitan ≥2 observaciones. Encontradas: {len(obs_dates)}')

        first_f = list(obs_dates.values())[0]
        with rasterio.open(first_f) as src:
            meta   = src.meta.copy()
            n_rows, n_cols = src.height, src.width
            nodata = src.nodata if src.nodata is not None else -9999.0
            n_pix  = n_rows * n_cols

        epoch = datetime(1970, 1, 1)
        obs_doys_list, obs_vals_list = [], []
        for date_str, fpath in sorted(obs_dates.items()):
            dt = datetime.strptime(date_str, '%Y-%m-%d')
            obs_doys_list.append(float((dt - epoch).days))
            with rasterio.open(fpath) as src:
                obs_vals_list.append(src.read(1).astype(np.float32).flatten())
            if feedback.isCanceled(): return {}

        obs_doys   = np.array(obs_doys_list)
        obs_values = np.stack(obs_vals_list, axis=0)
        target_ep  = float((target_dt - epoch).days)
        pred_flat  = np.full(n_pix, nodata, dtype=np.float32)

        feedback.setProgress(40)
        block = max(10000, n_pix // 10)
        for start in range(0, n_pix, block):
            if feedback.isCanceled(): return {}
            end   = min(start + block, n_pix)
            chunk = obs_values[:, start:end]
            valid = np.all(chunk != nodata, axis=0) & np.all(np.isfinite(chunk), axis=0)
            if valid.any():
                out = np.full(end - start, nodata, dtype=np.float32)
                out[valid] = gpr_gapfilling_temporal(target_ep, obs_doys, chunk[:, valid], model, crop)
                pred_flat[start:end] = out
            feedback.setProgress(40 + int(50 * end / n_pix))

        out_meta = meta.copy()
        out_meta.update({'count': 1, 'dtype': 'float32', 'nodata': nodata, 'driver': 'GTiff'})
        with rasterio.open(output_path, 'w', **out_meta) as dst:
            dst.write(pred_flat.reshape(n_rows, n_cols), 1)
            dst.update_tags(1, VEGINDEX=veg_index, TARGET_DATE=target_date, CROP=crop)

        if add_to_qgis:
            from .qgis_utils import queue_raster_layer
            queue_raster_layer(context, output_path, f'Gapfilled_{veg_index}_{target_date}', feedback)

        feedback.setProgress(100)
        feedback.pushInfo(f'✅ Gapfilled guardado: {output_path}')
        return {self.OUTPUT: output_path}
