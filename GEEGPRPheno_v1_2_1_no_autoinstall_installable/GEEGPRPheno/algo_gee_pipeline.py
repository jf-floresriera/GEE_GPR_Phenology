# -*- coding: utf-8 -*-
"""
algo_gee_pipeline.py
====================
Algoritmo 4 QGIS: Pipeline GEE Automatico con descarga Sentinel-2.
"""
import os
import re
import json
import shutil
import numpy as np
from datetime import datetime
from qgis.core import (
    QgsProcessingAlgorithm,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterString,
    QgsProcessingParameterNumber,
    QgsProcessingParameterEnum,
    QgsProcessingParameterFile,
    QgsProcessingParameterBoolean,
    QgsProcessingParameterFolderDestination,
    QgsProcessingException,
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransform,
    QgsProject,
)
from qgis.PyQt.QtCore import QCoreApplication


class GEEAutoPipelineAlgorithm(QgsProcessingAlgorithm):

    DATA_SOURCE        = 'DATA_SOURCE'
    AOI_LAYER          = 'AOI_LAYER'
    START_DATE         = 'START_DATE'
    END_DATE           = 'END_DATE'
    CLOUD_PCT          = 'CLOUD_PCT'
    MASK_MODE          = 'MASK_MODE'
    VEG_INDEX          = 'VEG_INDEX'
    CROP_TYPE          = 'CROP_TYPE'
    CUSTOM_GAP         = 'CUSTOM_GAP'
    GAPFILL_WINDOW     = 'GAPFILL_WINDOW'
    OUTPUT_FOLDER      = 'OUTPUT_FOLDER'
    RUN_LSP            = 'RUN_LSP'
    ADD_OUTPUTS_TO_QGIS = 'ADD_OUTPUTS_TO_QGIS'
    LOCAL_S2_FOLDER    = 'LOCAL_S2_FOLDER'
    GEE_PROJECT        = 'GEE_PROJECT'
    SERVICE_ACCOUNT_KEY = 'SERVICE_ACCOUNT_KEY'

    DATA_SOURCE_OPTIONS = ['Google Earth Engine', 'Carpeta local S2 BOA']
    MASK_MODE_OPTIONS = ['Estricto cultivo (SCL 4-5 + QA60)', 'Original JavaScript (QA60 + SCL)', 'Extendido SCL 4-7 + QA60', 'Sin mascara']
    VEG_INDEX_OPTIONS = ['LAI', 'Cab', 'Cw', 'Cm', 'FVC', 'laiCab', 'laiCm', 'laiCw']
    CROP_OPTIONS = [
        'media', 'maiz', 'trigo', 'cebada', 'girasol',
        'colza', 'guisante', 'alfalfa', 'remolacha', 'patata'
    ]

    def tr(self, s):
        return QCoreApplication.translate('GEEAutoPipeline', s)

    def createInstance(self):
        return GEEAutoPipelineAlgorithm()

    def name(self):
        return 'gee_auto_pipeline'

    def displayName(self):
        return self.tr('4. Pipeline GEE Automatico (Descarga + GPR + LSP)')

    def group(self):
        return self.tr('GEE GPR Phenology')

    def groupId(self):
        return 'geegprpheno'

    def shortHelpString(self):
        return self.tr(
            'Pipeline GEE Automatico.\n\n'
            'Pasos:\n'
            '1. Conecta a Google Earth Engine\n'
            '2. Filtra imagenes S2 L2A por area, fechas y nubosidad\n'
            '3. Prediccion espectral GPR\n'
            '4. Gapfilling temporal GPR\n'
            '5. Metricas LSP fenologicas (opcional)\n\n'
            'Requiere autenticacion GEE previa:\n'
            'Menu Plugins > GEE GPR Phenology > Autenticar GEE'
        )

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterEnum(
            self.DATA_SOURCE,
            self.tr('Fuente de datos Sentinel-2 BOA'),
            options=self.DATA_SOURCE_OPTIONS,
            defaultValue=0
        ))
        self.addParameter(QgsProcessingParameterFeatureSource(
            self.AOI_LAYER,
            self.tr('Area de interes (capa vectorial)')
        ))
        self.addParameter(QgsProcessingParameterString(
            self.START_DATE,
            self.tr('Fecha inicio del cultivo (YYYY-MM-DD)'),
            defaultValue='2023-03-01'
        ))
        self.addParameter(QgsProcessingParameterString(
            self.END_DATE,
            self.tr('Fecha fin del cultivo (YYYY-MM-DD)'),
            defaultValue='2023-09-30'
        ))
        self.addParameter(QgsProcessingParameterNumber(
            self.CLOUD_PCT,
            self.tr('Porcentaje maximo de nubosidad (0-100)'),
            type=QgsProcessingParameterNumber.Integer,
            defaultValue=20, minValue=0, maxValue=100
        ))
        self.addParameter(QgsProcessingParameterEnum(
            self.MASK_MODE,
            self.tr('Mascara de nubes/agua para descarga GEE'),
            options=self.MASK_MODE_OPTIONS,
            defaultValue=0
        ))
        self.addParameter(QgsProcessingParameterEnum(
            self.VEG_INDEX,
            self.tr('Variable biofisica'),
            options=self.VEG_INDEX_OPTIONS,
            defaultValue=0
        ))
        self.addParameter(QgsProcessingParameterEnum(
            self.CROP_TYPE,
            self.tr('Tipo de cultivo'),
            options=self.CROP_OPTIONS,
            defaultValue=0
        ))
        self.addParameter(QgsProcessingParameterNumber(
            self.GAPFILL_WINDOW,
            self.tr('Ventana de gapfilling temporal (+-dias)'),
            type=QgsProcessingParameterNumber.Integer,
            defaultValue=30, minValue=5, maxValue=90
        ))
        self.addParameter(QgsProcessingParameterBoolean(
            self.RUN_LSP,
            self.tr('Calcular metricas LSP al final'),
            defaultValue=True
        ))
        self.addParameter(QgsProcessingParameterNumber(
            self.CUSTOM_GAP,
            self.tr('Umbral relativo SOS/EOS (0.0-1.0)'),
            type=QgsProcessingParameterNumber.Double,
            defaultValue=0.30, minValue=0.0, maxValue=1.0
        ))
        self.addParameter(QgsProcessingParameterString(
            self.GEE_PROJECT,
            self.tr('ID del proyecto GEE (opcional)'),
            defaultValue='', optional=True
        ))
        self.addParameter(QgsProcessingParameterFile(
            self.SERVICE_ACCOUNT_KEY,
            self.tr('Clave Service Account JSON (opcional)'),
            behavior=QgsProcessingParameterFile.File,
            extension='json', optional=True
        ))
        self.addParameter(QgsProcessingParameterFile(
            self.LOCAL_S2_FOLDER,
            self.tr('Carpeta local con GeoTIFF S2 BOA de 10 bandas (opcional)'),
            behavior=QgsProcessingParameterFile.Folder,
            optional=True
        ))
        self.addParameter(QgsProcessingParameterBoolean(
            self.ADD_OUTPUTS_TO_QGIS,
            self.tr('Cargar resultado final como capa raster en QGIS'),
            defaultValue=True
        ))
        self.addParameter(QgsProcessingParameterFolderDestination(
            self.OUTPUT_FOLDER,
            self.tr('Carpeta de salida')
        ))

    def processAlgorithm(self, parameters, context, feedback):
        import rasterio
        from .s2boa_models import MODELS
        from .gpr_algorithms import (
            gpr_spectral_prediction,
            gpr_gapfilling_temporal,
            get_double_logistic_params,
            add_doy
        )

        data_source_i = self.parameterAsEnum(parameters, self.DATA_SOURCE, context)
        source      = self.parameterAsSource(parameters, self.AOI_LAYER, context)
        start_date  = self.parameterAsString(parameters, self.START_DATE, context).strip()
        end_date    = self.parameterAsString(parameters, self.END_DATE, context).strip()
        cloud_pct   = self.parameterAsInt(parameters, self.CLOUD_PCT, context)
        mask_mode_i = self.parameterAsEnum(parameters, self.MASK_MODE, context)
        veg_index   = self.VEG_INDEX_OPTIONS[self.parameterAsEnum(parameters, self.VEG_INDEX, context)]
        crop        = self.CROP_OPTIONS[self.parameterAsEnum(parameters, self.CROP_TYPE, context)]
        gf_window   = self.parameterAsInt(parameters, self.GAPFILL_WINDOW, context)
        run_lsp     = self.parameterAsBool(parameters, self.RUN_LSP, context)
        custom_gap  = self.parameterAsDouble(parameters, self.CUSTOM_GAP, context)
        gee_project = self.parameterAsString(parameters, self.GEE_PROJECT, context).strip()
        local_s2_folder = self.parameterAsFile(parameters, self.LOCAL_S2_FOLDER, context)
        add_outputs = self.parameterAsBool(parameters, self.ADD_OUTPUTS_TO_QGIS, context)
        out_folder  = self.parameterAsString(parameters, self.OUTPUT_FOLDER, context)

        try:
            dt_start = datetime.strptime(start_date, '%Y-%m-%d')
            dt_end   = datetime.strptime(end_date, '%Y-%m-%d')
        except ValueError as e:
            raise QgsProcessingException(f'Formato de fecha incorrecto (YYYY-MM-DD): {e}')

        if dt_end <= dt_start:
            raise QgsProcessingException('La fecha fin debe ser posterior a la fecha inicio.')

        feedback.pushInfo('Leyendo area de interes...')
        aoi_geom = self._get_aoi_wgs84(source, context)
        aoi_bbox = aoi_geom.boundingBox()
        feedback.pushInfo(
            f'AOI bbox (WGS84): [{aoi_bbox.xMinimum():.4f}, {aoi_bbox.yMinimum():.4f}, '
            f'{aoi_bbox.xMaximum():.4f}, {aoi_bbox.yMaximum():.4f}]'
        )

        raw_folder = os.path.join(out_folder, '01_S2_raw')
        os.makedirs(raw_folder, exist_ok=True)

        if data_source_i == 0:
            feedback.pushInfo('Conectando a Google Earth Engine...')
            ee = self._init_gee(gee_project, feedback, parameters, context)

            feedback.pushInfo(
                f'Buscando imagenes S2 L2A/BOA en GEE: {start_date} -> {end_date} | Nubosidad <= {cloud_pct}%'
            )
            downloaded_dates = self._download_s2_images(
                ee, aoi_bbox, start_date, end_date, cloud_pct, raw_folder, feedback, mask_mode_i
            )
        else:
            feedback.pushInfo('Usando fuente local externa: GeoTIFF Sentinel-2 BOA ya descargados.')
            downloaded_dates = self._collect_local_s2_images(
                local_s2_folder, raw_folder, start_date, end_date, feedback
            )

        if not downloaded_dates:
            raise QgsProcessingException(
                f'No se encontraron imagenes S2 con los filtros:\n'
                f'  Periodo: {start_date} -> {end_date}\n'
                f'  Nubosidad max: {cloud_pct}%\n'
                'Prueba aumentar el % de nubosidad o ampliar el periodo.'
            )

        feedback.pushInfo(f'{len(downloaded_dates)} imagenes descargadas.')
        feedback.setProgress(35)

        feedback.pushInfo(f'Aplicando prediccion espectral GPR ({veg_index})...')
        pred_folder = os.path.join(out_folder, f'02_{veg_index}_pred')
        os.makedirs(pred_folder, exist_ok=True)

        model = MODELS[veg_index]
        pred_dates = self._run_spectral_prediction(
            downloaded_dates, raw_folder, pred_folder,
            model, veg_index, gpr_spectral_prediction, feedback
        )
        feedback.setProgress(60)

        feedback.pushInfo(f'Aplicando gapfilling temporal GPR (ventana +-{gf_window}d)...')
        gf_folder = os.path.join(out_folder, f'03_{veg_index}_gapfilled')
        os.makedirs(gf_folder, exist_ok=True)

        self._run_gapfilling(
            pred_dates, pred_folder, gf_folder,
            model, veg_index, crop, gf_window,
            gpr_gapfilling_temporal, feedback
        )
        feedback.setProgress(80)

        lsp_output = None
        if run_lsp:
            feedback.pushInfo('Calculando metricas LSP...')
            lsp_folder = os.path.join(out_folder, f'04_{veg_index}_LSP')
            os.makedirs(lsp_folder, exist_ok=True)
            lsp_output = self._run_lsp(
                gf_folder, veg_index, custom_gap, lsp_folder,
                get_double_logistic_params, add_doy, feedback
            )

        feedback.setProgress(100)
        feedback.pushInfo('=' * 50)
        feedback.pushInfo('Pipeline GEE completado.')
        feedback.pushInfo(f'  Raw S2:      {raw_folder}')
        feedback.pushInfo(f'  Pred GPR:    {pred_folder}')
        feedback.pushInfo(f'  Gapfilled:   {gf_folder}')
        if lsp_output:
            feedback.pushInfo(f'  LSP:         {lsp_output}')
        if add_outputs:
            self._queue_final_outputs_to_qgis(context, lsp_output, gf_folder, pred_dates, veg_index, feedback)
        feedback.pushInfo('=' * 50)

        return {self.OUTPUT_FOLDER: out_folder}

    # =========================================================================
    # METODOS AUXILIARES
    # =========================================================================

    def _load_saved_gee_project(self):
        """Lee el Project ID guardado por el panel del plugin, si existe."""
        cfg = os.path.join(os.path.expanduser('~'), '.config', 'earthengine', 'qgis_plugin_config.json')
        try:
            if os.path.exists(cfg):
                with open(cfg, 'r', encoding='utf-8') as f:
                    return json.load(f).get('project', '') or ''
        except Exception:
            return ''
        return ''

    def _extract_date_from_name(self, filename):
        """Extrae fechas YYYY-MM-DD o YYYYMMDD de nombres de GeoTIFF/SAFE."""
        base = os.path.basename(filename)
        m = re.search(r'(20\d{2}-\d{2}-\d{2})', base)
        if m:
            return m.group(1)
        m = re.search(r'(20\d{6})', base)
        if m:
            raw = m.group(1)
            return f'{raw[0:4]}-{raw[4:6]}-{raw[6:8]}'
        return None

    def _collect_local_s2_images(self, local_folder, raw_folder, start_date, end_date, feedback):
        """Usa una carpeta externa como fuente no-GEE.

        Requisito: cada GeoTIFF debe tener al menos 10 bandas BOA en este orden:
        B2, B3, B4, B5, B6, B7, B8, B8A, B11, B12. Puede venir de Copernicus
        Browser, Sentinel Hub, SNAP/Sen2Cor, Semi-Automatic Classification Plugin,
        o cualquier flujo externo. El nombre debe contener YYYY-MM-DD o YYYYMMDD.
        """
        import rasterio

        if not local_folder or not os.path.isdir(local_folder):
            raise QgsProcessingException(
                'Seleccionaste fuente local, pero no indicaste una carpeta valida con GeoTIFF Sentinel-2 BOA.'
            )

        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        candidates = []
        for root, _, files in os.walk(local_folder):
            for name in files:
                if name.lower().endswith(('.tif', '.tiff')):
                    candidates.append(os.path.join(root, name))

        if not candidates:
            raise QgsProcessingException(f'No se encontraron GeoTIFF en la carpeta local: {local_folder}')

        selected = []
        seen = set()
        for fpath in sorted(candidates):
            date_str = self._extract_date_from_name(fpath)
            if not date_str:
                feedback.pushInfo(f'  omitido sin fecha en nombre: {os.path.basename(fpath)}')
                continue
            dt = datetime.strptime(date_str, '%Y-%m-%d')
            if not (start_dt <= dt <= end_dt):
                continue
            try:
                with rasterio.open(fpath) as src:
                    if src.count < 10:
                        feedback.pushInfo(f'  omitido (<10 bandas): {os.path.basename(fpath)}')
                        continue
            except Exception as ex:
                feedback.pushInfo(f'  omitido no legible: {os.path.basename(fpath)} | {ex}')
                continue
            if date_str in seen:
                feedback.pushInfo(f'  fecha duplicada omitida: {date_str} ({os.path.basename(fpath)})')
                continue
            out_path = os.path.join(raw_folder, f'{date_str}_S2.tif')
            if os.path.abspath(fpath) != os.path.abspath(out_path):
                shutil.copy2(fpath, out_path)
            selected.append(date_str)
            seen.add(date_str)
            feedback.pushInfo(f'  local ok {date_str}: {os.path.basename(fpath)}')

        return selected

    def _build_s2_mask(self, ee, img, mask_mode_i):
        """Construye máscara Sentinel-2 con SCL + QA60.

        0 Estricto cultivo: vegetación y suelo desnudo/no vegetado (SCL 4,5), QA60 sin nube/cirrus.
        1 Original JS: QA60 + exclusión de agua, sombras, nubes, cirrus y nieve/hielo.
        2 Extendido: SCL 4,5,6,7 + QA60; reproduce el comportamiento anterior pero con QA60.
        3 Sin máscara: solo descarga bandas.
        """
        scl = img.select('SCL')
        qa = img.select('QA60')
        cloud_bit = 1 << 10
        cirrus_bit = 1 << 11
        qa_clear = qa.bitwiseAnd(cloud_bit).eq(0).And(qa.bitwiseAnd(cirrus_bit).eq(0))

        if mask_mode_i == 3:
            return ee.Image(1)
        if mask_mode_i == 0:
            return qa_clear.And(scl.eq(4).Or(scl.eq(5)))
        if mask_mode_i == 1:
            return (qa_clear
                    .And(scl.neq(3))
                    .And(scl.neq(6))
                    .And(scl.neq(7))
                    .And(scl.neq(8))
                    .And(scl.neq(9))
                    .And(scl.neq(10))
                    .And(scl.neq(11)))
        return qa_clear.And(scl.eq(4).Or(scl.eq(5)).Or(scl.eq(6)).Or(scl.eq(7)))

    def _queue_final_outputs_to_qgis(self, context, lsp_output, gf_folder, pred_dates, veg_index, feedback):
        """Carga una capa de comprobación visual al proyecto QGIS al finalizar."""
        from .qgis_utils import queue_raster_layer

        if lsp_output:
            queue_raster_layer(context, lsp_output, f'LSP_{veg_index}', feedback)
            return

        if pred_dates:
            last_date = sorted(pred_dates)[-1]
            gf_path = os.path.join(gf_folder, f'{last_date}_{veg_index}.tif')
            queue_raster_layer(context, gf_path, f'GPR_gapfilled_{veg_index}_{last_date}', feedback)

    def _get_aoi_wgs84(self, source, context):
        crs_wgs84 = QgsCoordinateReferenceSystem('EPSG:4326')
        transform = QgsCoordinateTransform(
            source.sourceCrs(), crs_wgs84, QgsProject.instance()
        )
        geoms = []
        for feat in source.getFeatures():
            geom = feat.geometry()
            geom.transform(transform)
            geoms.append(geom)
        if not geoms:
            raise QgsProcessingException('La capa AOI no contiene geometrias validas.')
        if len(geoms) == 1:
            return geoms[0]
        union = geoms[0]
        for g in geoms[1:]:
            union = union.combine(g)
        return union

    def _init_gee(self, project_id, feedback, parameters=None, context=None):
        project_id = (project_id or self._load_saved_gee_project()).strip()
        try:
            import ee
        except ImportError:
            raise QgsProcessingException(
                'earthengine-api no instalado.\n'
                'Ejecuta en Consola Python de QGIS:\n'
                '  import subprocess, sys\n'
                '  subprocess.run([sys.executable, "-m", "pip", "install", "earthengine-api"])'
            )

        # Estrategia 1: Service Account JSON
        sa_key_path = ''
        if parameters is not None and context is not None:
            try:
                sa_key_path = self.parameterAsFile(
                    parameters, self.SERVICE_ACCOUNT_KEY, context
                ) or ''
            except Exception:
                pass

        if sa_key_path and os.path.isfile(sa_key_path):
            try:
                with open(sa_key_path) as f:
                    key_data = json.load(f)
                sa_email = key_data.get('client_email', '')
                credentials = ee.ServiceAccountCredentials(sa_email, sa_key_path)
                if project_id:
                    ee.Initialize(credentials, project=project_id)
                else:
                    ee.Initialize(credentials)
                feedback.pushInfo(f'GEE conectado via Service Account: {sa_email} | Proyecto: {project_id or "default"}')
                return ee
            except Exception as ex:
                feedback.pushInfo(f'Service Account fallo: {ex}')

        # Estrategia 2: credenciales guardadas
        try:
            if project_id:
                ee.Initialize(project=project_id)
            else:
                ee.Initialize()
            feedback.pushInfo(f'Google Earth Engine conectado (credenciales guardadas). Proyecto: {project_id or "default"}')
            return ee
        except Exception:
            pass

        # Estrategia 3: sin autenticacion
        raise QgsProcessingException(
            'No hay credenciales GEE disponibles.\n\n'
            'Autenticate primero:\n'
            '  Menu Plugins > GEE GPR Phenology > Autenticar Google Earth Engine\n\n'
            'O desde Consola Python de QGIS:\n'
            '  import ee\n'
            '  ee.Authenticate(auth_mode="notebook")\n'
            '  ee.Initialize()'
        )

    def _download_s2_images(self, ee, aoi_bbox, start_date, end_date,
                             cloud_pct, out_folder, feedback, mask_mode_i=0):
        import urllib.request

        bbox = [
            aoi_bbox.xMinimum(), aoi_bbox.yMinimum(),
            aoi_bbox.xMaximum(), aoi_bbox.yMaximum()
        ]
        ee_region = ee.Geometry.BBox(*bbox)
        S2_BANDS  = ['B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'B8', 'B8A', 'B11', 'B12', 'SCL']

        collection = (
            ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
            .filterBounds(ee_region)
            .filterDate(start_date, end_date)
            .filter(ee.Filter.lte('CLOUDY_PIXEL_PERCENTAGE', cloud_pct))
            .select(S2_BANDS)
        )

        count = collection.size().getInfo()
        feedback.pushInfo(f'  -> {count} imagenes encontradas.')

        if count == 0:
            return []

        if count > 50:
            feedback.pushInfo(f'  Limitando a 50 imagenes de {count} disponibles.')
            collection = collection.limit(50)

        image_list = collection.toList(collection.size())
        n_images   = min(count, 50)
        downloaded = []

        for i in range(n_images):
            if feedback.isCanceled():
                return downloaded

            img      = ee.Image(image_list.get(i))
            date_str = img.date().format('YYYY-MM-dd').getInfo()
            out_path = os.path.join(out_folder, f'{date_str}_S2.tif')

            if os.path.exists(out_path):
                feedback.pushInfo(f'  [cache] {date_str}')
                downloaded.append(date_str)
                feedback.setProgress(5 + int(25 * (i + 1) / n_images))
                continue

            try:
                valid_mask = self._build_s2_mask(ee, img, mask_mode_i)
                img_masked = img.select(S2_BANDS[:-1]).updateMask(valid_mask)

                url = img_masked.getDownloadURL({
                    'region': ee_region,
                    'scale':  10,
                    'crs':    'EPSG:4326',
                    'format': 'GEO_TIFF',
                    'bands':  S2_BANDS[:-1],
                })
                urllib.request.urlretrieve(url, out_path)
                downloaded.append(date_str)
                feedback.pushInfo(f'  ok {date_str}')

            except Exception as ex:
                feedback.pushInfo(f'  error {date_str}: {ex}')

            feedback.setProgress(5 + int(25 * (i + 1) / n_images))

        return downloaded

    def _run_spectral_prediction(self, dates, in_folder, out_folder,
                                  model, veg_index, gpr_predict_fn, feedback):
        import rasterio
        pred_dates = []

        for i, date_str in enumerate(dates):
            if feedback.isCanceled():
                return pred_dates

            in_path  = os.path.join(in_folder, f'{date_str}_S2.tif')
            out_path = os.path.join(out_folder, f'{date_str}_{veg_index}.tif')

            if not os.path.exists(in_path):
                continue

            try:
                with rasterio.open(in_path) as src:
                    meta   = src.meta.copy()
                    n_rows = src.height
                    n_cols = src.width
                    nodata = src.nodata if src.nodata is not None else -9999.0
                    bands  = np.stack(
                        [src.read(b + 1).astype(np.float32)
                         for b in range(min(10, src.count))],
                        axis=-1
                    )

                bands_scaled = bands / 10000.0
                n_pix        = n_rows * n_cols
                bands_flat   = bands_scaled.reshape(n_pix, 10)
                valid_mask   = (
                    np.all(bands_flat > 0, axis=1) &
                    np.all(np.isfinite(bands_flat), axis=1)
                )
                valid_idx  = np.where(valid_mask)[0]
                pred_flat  = np.full(n_pix, nodata, dtype=np.float32)

                if len(valid_idx) > 0:
                    block = max(10000, len(valid_idx) // 10)
                    for start in range(0, len(valid_idx), block):
                        end   = min(start + block, len(valid_idx))
                        chunk = valid_idx[start:end]
                        pred_flat[chunk] = gpr_predict_fn(bands_flat[chunk], model)

                out_meta = meta.copy()
                out_meta.update({'count': 1, 'dtype': 'float32',
                                 'nodata': nodata, 'driver': 'GTiff'})

                with rasterio.open(out_path, 'w', **out_meta) as dst:
                    dst.write(pred_flat.reshape(n_rows, n_cols), 1)
                    dst.update_tags(1, VEGINDEX=veg_index, DATE=date_str)

                pred_dates.append(date_str)
                feedback.pushInfo(f'  GPR pred ok: {date_str}')

            except Exception as ex:
                feedback.pushInfo(f'  GPR pred error {date_str}: {ex}')

            feedback.setProgress(35 + int(20 * (i + 1) / max(len(dates), 1)))

        return pred_dates

    def _run_gapfilling(self, dates, in_folder, out_folder,
                         model, veg_index, crop, gf_window,
                         gpr_gapfill_fn, feedback):
        import rasterio

        epoch      = datetime(1970, 1, 1)
        obs_by_date = {}

        for date_str in dates:
            fpath = os.path.join(in_folder, f'{date_str}_{veg_index}.tif')
            if os.path.exists(fpath):
                obs_by_date[date_str] = fpath

        if len(obs_by_date) < 2:
            feedback.pushInfo('Menos de 2 observaciones, omitiendo gapfilling.')
            return

        first_f = list(obs_by_date.values())[0]
        with rasterio.open(first_f) as src:
            meta   = src.meta.copy()
            n_rows = src.height
            n_cols = src.width
            nodata = src.nodata if src.nodata is not None else -9999.0

        for i, target_date in enumerate(dates):
            if feedback.isCanceled():
                return

            out_path  = os.path.join(out_folder, f'{target_date}_{veg_index}.tif')
            target_dt = datetime.strptime(target_date, '%Y-%m-%d')

            obs_in_window = {
                d: f for d, f in obs_by_date.items()
                if abs((datetime.strptime(d, '%Y-%m-%d') - target_dt).days) <= gf_window
            }

            if len(obs_in_window) < 2:
                feedback.pushInfo(f'  {target_date}: pocas obs en ventana, omitiendo.')
                continue

            obs_doys_list = []
            obs_vals_list = []
            for date_str, fpath in sorted(obs_in_window.items()):
                dt = datetime.strptime(date_str, '%Y-%m-%d')
                obs_doys_list.append(float((dt - epoch).days))
                with rasterio.open(fpath) as src:
                    obs_vals_list.append(src.read(1).astype(np.float32).flatten())

            obs_doys   = np.array(obs_doys_list)
            obs_values = np.stack(obs_vals_list, axis=0)
            target_ep  = float((target_dt - epoch).days)
            n_pix      = n_rows * n_cols
            pred_flat  = np.full(n_pix, nodata, dtype=np.float32)

            block = max(10000, n_pix // 10)
            for start in range(0, n_pix, block):
                end   = min(start + block, n_pix)
                chunk = obs_values[:, start:end]
                finite_valid = (chunk != nodata) & np.isfinite(chunk)
                can_predict = finite_valid.sum(axis=0) >= 2
                if can_predict.any():
                    out_c = np.full(end - start, nodata, dtype=np.float32)
                    pattern_matrix = finite_valid[:, can_predict].T
                    unique_patterns, inverse = np.unique(pattern_matrix, axis=0, return_inverse=True)
                    can_predict_idx = np.where(can_predict)[0]

                    for pat_i, pattern in enumerate(unique_patterns):
                        selected_local = can_predict_idx[inverse == pat_i]
                        if pattern.sum() < 2:
                            continue
                        pred_vals = gpr_gapfill_fn(
                            target_ep,
                            obs_doys[pattern],
                            chunk[pattern][:, selected_local],
                            model,
                            crop,
                        )
                        out_c[selected_local] = pred_vals.ravel()
                    pred_flat[start:end] = out_c

            out_meta = meta.copy()
            out_meta.update({'count': 1, 'dtype': 'float32',
                             'nodata': nodata, 'driver': 'GTiff'})

            with rasterio.open(out_path, 'w', **out_meta) as dst:
                dst.write(pred_flat.reshape(n_rows, n_cols), 1)
                dst.update_tags(1, VEGINDEX=veg_index, DATE=target_date, CROP=crop)

            feedback.pushInfo(f'  Gapfilled ok: {target_date}')
            feedback.setProgress(60 + int(18 * (i + 1) / max(len(dates), 1)))

    def _run_lsp(self, gf_folder, veg_index, custom_gap, lsp_folder,
                  lsp_fn, add_doy_fn, feedback):
        import glob
        import rasterio

        tif_files = sorted(glob.glob(os.path.join(gf_folder, f'*_{veg_index}.tif')))

        if not tif_files:
            feedback.pushInfo('No hay archivos gapfilled para LSP.')
            return None

        if len(tif_files) < 6:
            feedback.pushInfo(
                f'Se necesitan >=6 imagenes para LSP. Disponibles: {len(tif_files)}'
            )
            return None

        with rasterio.open(tif_files[0]) as src:
            meta   = src.meta.copy()
            n_rows = src.height
            n_cols = src.width
            nodata = src.nodata if src.nodata is not None else -9999.0

        doys_list   = []
        arrays_list = []

        for fpath in tif_files:
            date_str = os.path.basename(fpath)[:10]
            try:
                doy, _ = add_doy_fn(date_str)
                doys_list.append(float(doy))
                with rasterio.open(fpath) as src:
                    arrays_list.append(src.read(1).astype(np.float32).flatten())
            except Exception:
                continue

        if len(doys_list) < 6:
            return None

        doys_arr   = np.array(doys_list)
        values_arr = np.stack(arrays_list, axis=0)
        values_arr = np.where(values_arr == nodata, np.nan, values_arr)
        n_pix      = n_rows * n_cols

        valid = np.sum(np.isfinite(values_arr), axis=0) >= 6
        if not valid.any():
            feedback.pushInfo('No hay pixeles con al menos 6 observaciones validas para LSP.')
            return None

        lsp = lsp_fn(doys_arr, values_arr[:, valid], custom_gap=custom_gap)

        band_names = ['sos', 'eos', 'pos', 'los', 'customsos', 'customeos',
                      'vmin', 'vmax', 'n1', 'm1', 'n2', 'm2']
        bands_out  = []

        for bname in band_names:
            full = np.full(n_pix, nodata, dtype=np.float32)
            full[valid] = lsp[bname]
            bands_out.append(full.reshape(n_rows, n_cols))

        lsp_path = os.path.join(lsp_folder, f'LSP_{veg_index}.tif')
        out_meta  = meta.copy()
        out_meta.update({'count': len(band_names), 'dtype': 'float32',
                         'nodata': nodata, 'driver': 'GTiff'})

        with rasterio.open(lsp_path, 'w', **out_meta) as dst:
            for idx, (arr, bname) in enumerate(zip(bands_out, band_names)):
                dst.write(arr, idx + 1)
                dst.update_tags(idx + 1, NAME=bname.upper())
            dst.update_tags(
                BAND_NAMES=','.join(b.upper() for b in band_names),
                CUSTOM_GAP=str(custom_gap),
                VEG_INDEX=veg_index
            )

        return lsp_path
