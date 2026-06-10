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
from .i18n import tr as _tr


class GEEAutoPipelineAlgorithm(QgsProcessingAlgorithm):

    DATA_SOURCE = 'DATA_SOURCE'
    AOI_LAYER = 'AOI_LAYER'
    START_DATE = 'START_DATE'
    END_DATE = 'END_DATE'
    CLOUD_PCT = 'CLOUD_PCT'
    MASK_MODE = 'MASK_MODE'
    VEG_INDEX = 'VEG_INDEX'
    CROP_TYPE = 'CROP_TYPE'
    CUSTOM_GAP = 'CUSTOM_GAP'
    GAPFILL_WINDOW = 'GAPFILL_WINDOW'
    OUTPUT_FOLDER = 'OUTPUT_FOLDER'
    RUN_LSP = 'RUN_LSP'
    ADD_OUTPUTS_TO_QGIS = 'ADD_OUTPUTS_TO_QGIS'
    GENERATE_PDF_REPORTS = 'GENERATE_PDF_REPORTS'
    LOCAL_S2_FOLDER = 'LOCAL_S2_FOLDER'
    GEE_PROJECT = 'GEE_PROJECT'
    GEE_AUTH_JSON = 'GEE_AUTH_JSON'

    DATA_SOURCE_OPTIONS = ['Google Earth Engine', 'Carpeta local S2 BOA']
    MASK_MODE_OPTIONS = ['Estricto cultivo (SCL 4-5, QA60 si existe)', 'Original JavaScript (SCL + QA60 si existe)', 'Extendido SCL 4-7, QA60 si existe', 'Sin mascara']
    VEG_INDEX_OPTIONS = ['LAI', 'Cab', 'Cw', 'Cm', 'FVC', 'laiCab', 'laiCm', 'laiCw']
    CROP_OPTIONS = [
        'media', 'maiz', 'trigo', 'cebada', 'girasol',
        'colza', 'guisante', 'alfalfa', 'remolacha', 'patata'
    ]

    def tr(self, s):
        return _tr(QCoreApplication.translate(self.__class__.__name__, s))

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
            options=[self.tr(o) for o in self.DATA_SOURCE_OPTIONS],
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
            options=[self.tr(o) for o in self.MASK_MODE_OPTIONS],
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
            options=[self.tr(o) for o in self.CROP_OPTIONS],
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
            self.GEE_AUTH_JSON,
            self.tr('Archivo JSON de autenticacion GEE (opcional)'),
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
            self.tr('Cargar salidas generadas como capas raster en QGIS'),
            defaultValue=True
        ))
        self.addParameter(QgsProcessingParameterBoolean(
            self.GENERATE_PDF_REPORTS,
            self.tr('Generar reportes graficos PDF (series temporales, mapas y metricas LSP)'),
            defaultValue=True
        ))
        self.addParameter(QgsProcessingParameterFolderDestination(
            self.OUTPUT_FOLDER,
            self.tr('Carpeta de salida')
        ))

    def processAlgorithm(self, parameters, context, feedback):
        from .s2boa_models import MODELS
        from .gpr_algorithms import (
            gpr_spectral_prediction,
            gpr_gapfilling_temporal,
            get_double_logistic_params,
            add_doy
        )

        data_source_i = self.parameterAsEnum(parameters, self.DATA_SOURCE, context)
        source = self.parameterAsSource(parameters, self.AOI_LAYER, context)
        start_date = self.parameterAsString(parameters, self.START_DATE, context).strip()
        end_date = self.parameterAsString(parameters, self.END_DATE, context).strip()
        cloud_pct = self.parameterAsInt(parameters, self.CLOUD_PCT, context)
        mask_mode_i = self.parameterAsEnum(parameters, self.MASK_MODE, context)
        veg_index = self.VEG_INDEX_OPTIONS[self.parameterAsEnum(parameters, self.VEG_INDEX, context)]
        crop = self.CROP_OPTIONS[self.parameterAsEnum(parameters, self.CROP_TYPE, context)]
        gf_window = self.parameterAsInt(parameters, self.GAPFILL_WINDOW, context)
        run_lsp = self.parameterAsBool(parameters, self.RUN_LSP, context)
        custom_gap = self.parameterAsDouble(parameters, self.CUSTOM_GAP, context)
        gee_project = self.parameterAsString(parameters, self.GEE_PROJECT, context).strip()
        local_s2_folder = self.parameterAsFile(parameters, self.LOCAL_S2_FOLDER, context)
        add_outputs = self.parameterAsBool(parameters, self.ADD_OUTPUTS_TO_QGIS, context)
        generate_pdfs = self.parameterAsBool(parameters, self.GENERATE_PDF_REPORTS, context)
        out_folder = self.parameterAsString(parameters, self.OUTPUT_FOLDER, context)

        try:
            dt_start = datetime.strptime(start_date, '%Y-%m-%d')
            dt_end = datetime.strptime(end_date, '%Y-%m-%d')
        except ValueError as e:
            raise QgsProcessingException(f'{self.tr("Formato de fecha incorrecto (YYYY-MM-DD)")}: {e}')

        if dt_end <= dt_start:
            raise QgsProcessingException(self.tr('La fecha fin debe ser posterior a la fecha inicio.'))

        feedback.pushInfo(self.tr('Leyendo area de interes...'))
        aoi_geom = self._get_aoi_wgs84(source, context)
        aoi_bbox = aoi_geom.boundingBox()
        feedback.pushInfo(
            f'AOI bbox (WGS84): [{aoi_bbox.xMinimum():.4f}, {aoi_bbox.yMinimum():.4f}, '
            f'{aoi_bbox.xMaximum():.4f}, {aoi_bbox.yMaximum():.4f}]'
        )

        raw_folder = os.path.join(out_folder, '01_S2_raw')
        os.makedirs(raw_folder, exist_ok=True)

        if data_source_i == 0:
            feedback.pushInfo(self.tr('Conectando a Google Earth Engine...'))
            ee = self._init_gee(gee_project, feedback, parameters, context)

            feedback.pushInfo(
                f'Buscando imagenes S2 L2A/BOA en GEE: {start_date} -> {end_date} | Nubosidad <= {cloud_pct}%'
            )
            downloaded_dates = self._download_s2_images(
                ee, aoi_bbox, start_date, end_date, cloud_pct, raw_folder, feedback, mask_mode_i
            )
        else:
            feedback.pushInfo(self.tr('Usando fuente local externa: GeoTIFF Sentinel-2 BOA ya descargados.'))
            downloaded_dates = self._collect_local_s2_images(
                local_s2_folder, raw_folder, start_date, end_date, feedback
            )

        downloaded_dates = self._unique_dates(downloaded_dates, feedback)

        if not downloaded_dates:
            raise QgsProcessingException(
                f'{self.tr("No se encontraron imagenes S2 con los filtros:")}\n'
                f'  {self.tr("Periodo")}: {start_date} -> {end_date}\n'
                f'  {self.tr("Nubosidad max")}: {cloud_pct}%\n'
                + self.tr('Prueba aumentar el % de nubosidad o ampliar el periodo.')  # noqa: W503
            )

        feedback.pushInfo(f'{len(downloaded_dates)} {self.tr("fechas unicas disponibles.")}')
        self._harmonize_raw_stack(raw_folder, downloaded_dates, feedback)
        feedback.setProgress(35)

        feedback.pushInfo(f'{self.tr("Aplicando prediccion espectral GPR")} ({veg_index})...')
        pred_folder = os.path.join(out_folder, f'02_{veg_index}_pred')
        os.makedirs(pred_folder, exist_ok=True)
        self._clean_generated_tifs(pred_folder, feedback)

        model = MODELS[veg_index]
        pred_dates = self._run_spectral_prediction(
            downloaded_dates, raw_folder, pred_folder,
            model, veg_index, gpr_spectral_prediction, feedback
        )
        feedback.setProgress(60)

        feedback.pushInfo(f'{self.tr("Aplicando gapfilling temporal GPR")} ({self.tr("Ventana temporal (±días)")} +-{gf_window}d)...')
        gf_folder = os.path.join(out_folder, f'03_{veg_index}_gapfilled')
        os.makedirs(gf_folder, exist_ok=True)
        self._clean_generated_tifs(gf_folder, feedback)

        self._run_gapfilling(
            pred_dates, pred_folder, gf_folder,
            model, veg_index, crop, gf_window,
            gpr_gapfilling_temporal, feedback
        )
        feedback.setProgress(80)

        lsp_output = None
        if run_lsp:
            feedback.pushInfo(self.tr('Calculando metricas LSP...'))
            lsp_folder = os.path.join(out_folder, f'04_{veg_index}_LSP')
            os.makedirs(lsp_folder, exist_ok=True)
            self._clean_generated_tifs(lsp_folder, feedback)
            lsp_output = self._run_lsp(
                gf_folder, veg_index, custom_gap, lsp_folder,
                get_double_logistic_params, add_doy, feedback
            )

        feedback.setProgress(100)
        feedback.pushInfo('=' * 50)
        feedback.pushInfo(self.tr('Pipeline GEE completado.'))
        feedback.pushInfo(f'  Raw S2:      {raw_folder}')
        feedback.pushInfo(f'  Pred GPR:    {pred_folder}')
        feedback.pushInfo(f'  Gapfilled:   {gf_folder}')
        if lsp_output:
            feedback.pushInfo(f'  LSP:         {lsp_output}')
        if add_outputs:
            self._queue_outputs_to_qgis(context, raw_folder, pred_folder, gf_folder, lsp_output, veg_index, pred_dates, feedback)
        if generate_pdfs:
            pdf_outputs = self._generate_pdf_reports(raw_folder, pred_folder, gf_folder, lsp_output, veg_index, out_folder, feedback)
            if pdf_outputs:
                for pdf in pdf_outputs:
                    feedback.pushInfo(f'  PDF:         {pdf}')
        feedback.pushInfo('=' * 50)

        return {self.OUTPUT_FOLDER: out_folder}

    # =========================================================================
    # METODOS AUXILIARES
    # =========================================================================

    def _unique_dates(self, dates, feedback=None):
        """Elimina fechas duplicadas conservando el orden original."""
        out = []
        seen = set()
        for d in dates:
            if d in seen:
                if feedback:
                    feedback.pushInfo(f'  {self.tr("fecha duplicada ignorada")}: {d}')
                continue
            seen.add(d)
            out.append(d)
        return out

    def _clean_generated_tifs(self, folder, feedback=None):
        """Evita que resultados viejos queden mezclados con una corrida nueva."""
        if not os.path.isdir(folder):
            return
        removed = 0
        for name in os.listdir(folder):
            if name.lower().endswith(('.tif', '.tiff', '.aux.xml')):
                try:
                    os.remove(os.path.join(folder, name))
                    removed += 1
                except Exception:
                    pass
        if removed and feedback:
            feedback.pushInfo(f'  {self.tr("limpieza")}: {removed} {self.tr("raster antiguos eliminados en")} {folder}')

    def _harmonize_raw_stack(self, raw_folder, dates, feedback=None):
        """Asegura que todos los GeoTIFF S2 tengan la misma grilla raster.

        Algunas descargas de GEE pueden quedar con una diferencia de 1 pixel o
        con una transformacion ligeramente distinta. Si no se corrige, LSP falla
        al intentar apilar arrays con ``np.stack``. Esta rutina toma el primer
        raster valido como grilla de referencia y reproyecta/remuestrea el resto
        a esa grilla antes de ejecutar GPR, gapfilling y LSP.
        """
        import rasterio
        from rasterio.warp import reproject, Resampling

        paths = [os.path.join(raw_folder, f'{d}_S2.tif') for d in dates]
        paths = [p for p in paths if os.path.exists(p)]
        if len(paths) < 2:
            return

        ref_path = paths[0]
        with rasterio.open(ref_path) as ref:
            ref_crs = ref.crs
            ref_transform = ref.transform
            ref_height = ref.height
            ref_width = ref.width
            ref_count = ref.count

        harmonized = 0
        for path in paths[1:]:
            try:
                with rasterio.open(path) as src:
                    same_grid = (
                        src.width == ref_width and  # noqa: W504
                        src.height == ref_height and  # noqa: W504
                        src.count == ref_count and  # noqa: W504
                        src.crs == ref_crs and  # noqa: W504
                        tuple(src.transform) == tuple(ref_transform)
                    )
                    if same_grid:
                        continue

                    meta = src.meta.copy()
                    meta.update({
                        'height': ref_height,
                        'width': ref_width,
                        'transform': ref_transform,
                        'crs': ref_crs,
                        'count': min(src.count, ref_count),
                        'driver': 'GTiff'
                    })
                    nodata = src.nodata
                    tmp = path + '.harmonized.tif'
                    with rasterio.open(tmp, 'w', **meta) as dst:
                        for b in range(1, min(src.count, ref_count) + 1):
                            dst_arr = np.full((ref_height, ref_width), nodata if nodata is not None else 0, dtype=src.dtypes[b - 1])
                            reproject(
                                source=rasterio.band(src, b),
                                destination=dst_arr,
                                src_transform=src.transform,
                                src_crs=src.crs,
                                dst_transform=ref_transform,
                                dst_crs=ref_crs,
                                src_nodata=nodata,
                                dst_nodata=nodata,
                                resampling=Resampling.bilinear,
                            )
                            dst.write(dst_arr, b)
                        try:
                            dst.update_tags(**src.tags())
                        except Exception:
                            pass
                os.replace(tmp, path)
                harmonized += 1
                if feedback:
                    feedback.pushInfo(f'  {self.tr("raster armonizado a grilla comun")}: {os.path.basename(path)}')
            except Exception as ex:
                if feedback:
                    feedback.pushWarning(f'  {self.tr("no se pudo armonizar")} {os.path.basename(path)}: {ex}')
        if harmonized and feedback:
            feedback.pushInfo(f'  {self.tr("grilla comun aplicada a")} {harmonized} raster Sentinel-2.')

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
                self.tr('Seleccionaste fuente local, pero no indicaste una carpeta valida con GeoTIFF Sentinel-2 BOA.')
            )

        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        candidates = []
        for root, _, files in os.walk(local_folder):
            for name in files:
                if name.lower().endswith(('.tif', '.tiff')):
                    candidates.append(os.path.join(root, name))

        if not candidates:
            raise QgsProcessingException(f'{self.tr("No se encontraron GeoTIFF en la carpeta local")}: {local_folder}')

        selected = []
        seen = set()
        for fpath in sorted(candidates):
            date_str = self._extract_date_from_name(fpath)
            if not date_str:
                feedback.pushInfo(f'  {self.tr("omitido sin fecha en nombre")}: {os.path.basename(fpath)}')
                continue
            dt = datetime.strptime(date_str, '%Y-%m-%d')
            if not (start_dt <= dt <= end_dt):
                continue
            try:
                with rasterio.open(fpath) as src:
                    if src.count < 10:
                        feedback.pushInfo(f'  {self.tr("omitido (<10 bandas)")}: {os.path.basename(fpath)}')
                        continue
            except Exception as ex:
                feedback.pushInfo(f'  {self.tr("omitido no legible")}: {os.path.basename(fpath)} | {ex}')
                continue
            if date_str in seen:
                feedback.pushInfo(f'  {self.tr("fecha duplicada omitida")}: {date_str} ({os.path.basename(fpath)})')
                continue
            out_path = os.path.join(raw_folder, f'{date_str}_S2.tif')
            if os.path.abspath(fpath) != os.path.abspath(out_path):
                shutil.copy2(fpath, out_path)
            selected.append(date_str)
            seen.add(date_str)
            feedback.pushInfo(f'  {self.tr("local ok")} {date_str}: {os.path.basename(fpath)}')

        return selected

    def _build_s2_mask(self, ee, img, mask_mode_i, band_names=None, feedback=None):
        """Construye máscara Sentinel-2 robusta con SCL y QA60 cuando existe.

        La versión anterior fallaba porque se intentaba seleccionar QA60 después
        de haber reducido la imagen a [B2..B12, SCL]. Además, algunos flujos de
        Sentinel-2 pueden no traer QA60. Esta función usa QA60 solo si está
        disponible; de lo contrario aplica una máscara SCL robusta.
        """
        if mask_mode_i == 3:
            return ee.Image.constant(1)

        if band_names is None:
            try:
                band_names = img.bandNames().getInfo()
            except Exception:
                band_names = []

        has_scl = 'SCL' in band_names
        has_qa60 = 'QA60' in band_names

        if has_qa60:
            qa = img.select('QA60')
            cloud_bit = 1 << 10
            cirrus_bit = 1 << 11
            qa_clear = qa.bitwiseAnd(cloud_bit).eq(0).And(qa.bitwiseAnd(cirrus_bit).eq(0))
        else:
            qa_clear = ee.Image.constant(1)
            if feedback is not None:
                feedback.pushInfo('  ' + self.tr('aviso: QA60 no disponible; se aplica máscara basada en SCL.'))

        if not has_scl:
            if feedback is not None:
                feedback.pushInfo('  ' + self.tr('aviso: SCL no disponible; se usa QA60 si existe, o sin máscara si no existe.'))
            return qa_clear

        scl = img.select('SCL')
        if mask_mode_i == 0:
            # Cultivo/suelo: vegetación y suelo desnudo/no vegetado.
            return qa_clear.And(scl.eq(4).Or(scl.eq(5)))
        if mask_mode_i == 1:
            # Cercano al JS original: excluir sombras, agua, no clasificado,
            # nubes, cirrus y nieve/hielo; QA60 refuerza cuando existe.
            return (qa_clear
                    .And(scl.neq(3))
                    .And(scl.neq(6))
                    .And(scl.neq(7))
                    .And(scl.neq(8))
                    .And(scl.neq(9))
                    .And(scl.neq(10))
                    .And(scl.neq(11)))
        # Extendido: conserva vegetación/suelo/agua/no clasificado como la lógica anterior,
        # pero con QA60 si existe.
        return qa_clear.And(scl.eq(4).Or(scl.eq(5)).Or(scl.eq(6)).Or(scl.eq(7)))

    def _queue_outputs_to_qgis(self, context, raw_folder, pred_folder, gf_folder, lsp_output, veg_index, pred_dates, feedback):
        """Programa las salidas principales para visualizacion directa en QGIS.

        Se cargan: Sentinel-2 crudo, predicciones GPR, gapfilled y el raster LSP
        cuando exista. Para no saturar el proyecto, se cargan como maximo las
        12 fechas mas recientes por grupo.
        """
        from .qgis_utils import queue_raster_layer

        def _queue_folder(folder, suffix, prefix, group_name, style_kind, variable):
            files = []
            if os.path.isdir(folder):
                for name in sorted(os.listdir(folder)):
                    if name.lower().endswith('.tif') and (suffix is None or name.endswith(suffix)):
                        files.append(os.path.join(folder, name))
            if len(files) > 12:
                feedback.pushInfo(f'  {prefix}: se encontraron {len(files)} capas; se cargan las 12 mas recientes.')
                files = files[-12:]
            for fpath in files:
                base = os.path.splitext(os.path.basename(fpath))[0]
                queue_raster_layer(
                    context, fpath, f'{prefix}_{base}', feedback,
                    group_name=group_name, style_kind=style_kind, variable=variable
                )

        _queue_folder(
            raw_folder, '_S2.tif', 'S2_raw',
            self.tr('GEEGPRPheno - Raw Sentinel-2'), 'raw_rgb', 'S2_RGB'
        )
        _queue_folder(
            pred_folder, f'_{veg_index}.tif', f'GPR_pred_{veg_index}',
            self.tr('GEEGPRPheno - GPR pred'), 'singleband', veg_index
        )
        _queue_folder(
            gf_folder, f'_{veg_index}.tif', f'GPR_gapfilled_{veg_index}',
            self.tr('GEEGPRPheno - Gapfilled'), 'singleband', veg_index
        )

        if lsp_output:
            queue_raster_layer(
                context, lsp_output, f'LSP_{veg_index}', feedback,
                group_name=self.tr('GEEGPRPheno - LSP'), style_kind='lsp', variable='LSP_DOY'
            )

    def _generate_pdf_reports(self, raw_folder, pred_folder, gf_folder, lsp_output, veg_index, out_folder, feedback):
        """Genera reportes PDF con series temporales y resumen espacial de resultados."""
        import glob
        import rasterio
        import numpy as np
        from .gee_palettes import get_vis_params

        try:
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt
            from matplotlib.backends.backend_pdf import PdfPages
        except Exception as ex:
            feedback.pushWarning(f'{self.tr("No se pudieron generar PDF: matplotlib no disponible")} ({ex})')
            return []

        reports_dir = os.path.join(out_folder, '05_reportes_pdf')
        os.makedirs(reports_dir, exist_ok=True)

        def _sorted_tifs(folder, suffix):
            files = []
            if os.path.isdir(folder):
                files = sorted(glob.glob(os.path.join(folder, f'*{suffix}')))
            return files

        def _date_from_path(path):
            return os.path.basename(path)[:10]

        def _read_band1(path):
            with rasterio.open(path) as src:
                arr = src.read(1).astype(np.float32)
                nodata = src.nodata
            if nodata is not None:
                arr = np.where(arr == nodata, np.nan, arr)
            arr[~np.isfinite(arr)] = np.nan
            return arr

        def _mpl_style(variable):
            """Return cmap/vmin/vmax using the original JavaScript visParams."""
            from matplotlib.colors import LinearSegmentedColormap
            vp = get_vis_params(variable, fallback=True)
            palette = vp.get('palette') or ['#2c7bb6', '#abd9e9', '#ffffbf', '#fdae61', '#d7191c']
            cmap = LinearSegmentedColormap.from_list(f'{vp.get("name", variable)}_js', palette, N=max(len(palette), 256))
            vmin = vp.get('min')
            vmax = vp.get('max')
            return cmap, vmin, vmax

        def _imshow_js(ax, arr, variable):
            cmap, vmin, vmax = _mpl_style(variable)
            kwargs = {'cmap': cmap}
            if vmin is not None and vmax is not None and float(vmax) > float(vmin):
                kwargs.update({'vmin': float(vmin), 'vmax': float(vmax)})
            return ax.imshow(arr, **kwargs)

        def _compute_stats(files):
            stats = []
            for path in files:
                arr = _read_band1(path)
                valid = np.isfinite(arr)
                if not valid.any():
                    continue
                vals = arr[valid]
                stats.append({
                    'date': _date_from_path(path),
                    'path': path,
                    'count': int(vals.size),
                    'mean': float(np.nanmean(vals)),
                    'median': float(np.nanmedian(vals)),
                    'std': float(np.nanstd(vals)),
                    'min': float(np.nanmin(vals)),
                    'max': float(np.nanmax(vals)),
                    'p25': float(np.nanpercentile(vals, 25)),
                    'p75': float(np.nanpercentile(vals, 75)),
                })
            return stats

        pred_files = _sorted_tifs(pred_folder, f'_{veg_index}.tif')
        gf_files = _sorted_tifs(gf_folder, f'_{veg_index}.tif')
        pred_stats = _compute_stats(pred_files)
        gf_stats = _compute_stats(gf_files)

        # Exportar CSV de resumen
        csv_path = os.path.join(reports_dir, f'resumen_series_{veg_index}.csv')
        try:
            import csv
            with open(csv_path, 'w', newline='', encoding='utf-8') as f:
                w = csv.writer(f)
                w.writerow(['stage', 'date', 'count', 'mean', 'median', 'std', 'min', 'max', 'p25', 'p75'])
                for stage, items in [('pred', pred_stats), ('gapfilled', gf_stats)]:
                    for s in items:
                        w.writerow([stage, s['date'], s['count'], s['mean'], s['median'], s['std'], s['min'], s['max'], s['p25'], s['p75']])
        except Exception as ex:
            feedback.pushWarning(f'{self.tr("No se pudo guardar CSV resumen")}: {ex}')

        pdf_paths = []
        summary_pdf = os.path.join(reports_dir, f'reporte_resumen_{veg_index}.pdf')
        with PdfPages(summary_pdf) as pdf:
            fig = plt.figure(figsize=(11.69, 8.27))
            fig.text(0.06, 0.92, f'{self.tr("Reporte GEE GPR Phenology")} — {veg_index}', fontsize=18, weight='bold')
            fig.text(0.06, 0.87, self.tr('Contenido del reporte:'), fontsize=12, weight='bold')
            fig.text(0.08, 0.83, '• ' + self.tr('Series temporales de estadisticos espaciales (prediccion y gapfilling).'), fontsize=11)
            fig.text(0.08, 0.79, '• ' + self.tr('Mapas de la ultima fecha disponible para prediccion GPR y gapfilling.'), fontsize=11)
            if lsp_output:
                fig.text(0.08, 0.75, '• ' + self.tr('Resumen de metricas LSP y atlas de bandas en PDF adicional.'), fontsize=11)
            fig.text(0.06, 0.68, f'{self.tr("N. predicciones")}: {len(pred_stats)}', fontsize=11)
            fig.text(0.06, 0.64, f'{self.tr("N. gapfilled")}: {len(gf_stats)}', fontsize=11)
            fig.text(0.06, 0.60, f'{self.tr("Carpeta reportes")}: {reports_dir}', fontsize=10)
            fig.text(0.06, 0.56, f'{self.tr("CSV resumen")}: {csv_path}', fontsize=10)
            fig.text(0.06, 0.10, self.tr('Nota: Los estadisticos se calculan con pixeles validos, excluyendo nodata.'), fontsize=9)
            fig.tight_layout()
            pdf.savefig(fig)
            plt.close(fig)

            # Serie temporal
            if pred_stats or gf_stats:
                fig, ax = plt.subplots(figsize=(11.69, 8.27))
                if pred_stats:
                    x = list(range(len(pred_stats)))
                    labels = [s['date'] for s in pred_stats]
                    mean = np.array([s['mean'] for s in pred_stats])
                    p25 = np.array([s['p25'] for s in pred_stats])
                    p75 = np.array([s['p75'] for s in pred_stats])
                    ax.plot(x, mean, marker='o', label=self.tr('Prediccion GPR — media'))
                    ax.fill_between(x, p25, p75, alpha=0.2, label=self.tr('Prediccion GPR — IQR'))
                if gf_stats:
                    x2 = list(range(len(gf_stats)))
                    labels2 = [s['date'] for s in gf_stats]
                    mean2 = np.array([s['mean'] for s in gf_stats])
                    p25_2 = np.array([s['p25'] for s in gf_stats])
                    p75_2 = np.array([s['p75'] for s in gf_stats])
                    ax.plot(x2, mean2, marker='s', label=self.tr('Gapfilled GPR — media'))
                    ax.fill_between(x2, p25_2, p75_2, alpha=0.2, label=self.tr('Gapfilled GPR — IQR'))
                    labels = labels2 if not pred_stats else labels
                ax.set_title(f'{self.tr("Serie temporal de")} {veg_index}')
                ax.set_xlabel(self.tr('Fecha'))
                ax.set_ylabel(veg_index)
                ax.set_xticks(list(range(len(labels))))
                ax.set_xticklabels(labels, rotation=45, ha='right')
                ax.grid(True, alpha=0.3)
                ax.legend()
                fig.tight_layout()
                pdf.savefig(fig)
                plt.close(fig)

            # Páginas de mapas de última fecha
            map_candidates = []
            if pred_files:
                map_candidates.append((self.tr('Ultima prediccion GPR'), pred_files[-1]))
            if gf_files:
                map_candidates.append((self.tr('Ultimo gapfilling GPR'), gf_files[-1]))
            for title, path in map_candidates:
                arr = _read_band1(path)
                if np.isfinite(arr).any():
                    fig, ax = plt.subplots(figsize=(11.69, 8.27))
                    im = _imshow_js(ax, arr, veg_index)
                    ax.set_title(f'{title} — {_date_from_path(path)}')
                    ax.set_xlabel(self.tr('Columna'))
                    ax.set_ylabel(self.tr('Fila'))
                    plt.colorbar(im, ax=ax, shrink=0.8, label=veg_index)
                    fig.tight_layout()
                    pdf.savefig(fig)
                    plt.close(fig)

        pdf_paths.append(summary_pdf)

        if lsp_output and os.path.exists(lsp_output):
            lsp_pdf = os.path.join(reports_dir, f'atlas_LSP_{veg_index}.pdf')
            band_labels = ['SOS', 'EOS', 'POS', 'LOS', 'CustomSOS', 'CustomEOS', 'Vmin', 'Vmax', 'n1', 'm1', 'n2', 'm2']
            with rasterio.open(lsp_output) as src, PdfPages(lsp_pdf) as pdf:
                n_bands = src.count
                # Resumen tabular en primera pagina
                fig = plt.figure(figsize=(11.69, 8.27))
                fig.text(0.06, 0.92, f'{self.tr("Atlas de metricas LSP")} — {veg_index}', fontsize=18, weight='bold')
                ypos = 0.84
                for i in range(min(n_bands, len(band_labels))):
                    fig.text(0.08, ypos, f'• {self.tr("Banda")} {i + 1}: {band_labels[i]}', fontsize=11)
                    ypos -= 0.045
                fig.text(0.06, 0.10, self.tr('Cada pagina siguiente muestra el mapa espacial y un histograma resumido.'), fontsize=10)
                pdf.savefig(fig)
                plt.close(fig)

                for i in range(1, n_bands + 1):
                    arr = src.read(i).astype(np.float32)
                    nodata = src.nodata
                    if nodata is not None:
                        arr = np.where(arr == nodata, np.nan, arr)
                    arr[~np.isfinite(arr)] = np.nan
                    label = band_labels[i - 1] if i - 1 < len(band_labels) else f'Band_{i}'
                    fig = plt.figure(figsize=(11.69, 8.27))
                    ax1 = fig.add_subplot(1, 2, 1)
                    im = _imshow_js(ax1, arr, 'LSP_DOY')
                    ax1.set_title(label)
                    plt.colorbar(im, ax=ax1, shrink=0.8)
                    ax2 = fig.add_subplot(1, 2, 2)
                    vals = arr[np.isfinite(arr)]
                    if vals.size:
                        ax2.hist(vals.ravel(), bins=30)
                        ax2.set_title(f'{self.tr("Histograma")} {label}')
                        ax2.set_xlabel(label)
                        ax2.set_ylabel(self.tr('Frecuencia'))
                    else:
                        ax2.text(0.5, 0.5, self.tr('Sin datos validos'), ha='center', va='center')
                        ax2.set_axis_off()
                    fig.tight_layout()
                    pdf.savefig(fig)
                    plt.close(fig)
            pdf_paths.append(lsp_pdf)

        return pdf_paths

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
                'Instálalo manualmente con el Python asociado a QGIS, por ejemplo:\n'
                '  python -m pip install --upgrade earthengine-api'
            )

        # Estrategia 1: archivo JSON de autenticacion GEE
        auth_json_path = ''
        if parameters is not None and context is not None:
            try:
                auth_json_path = self.parameterAsFile(
                    parameters, self.GEE_AUTH_JSON, context
                ) or ''
            except Exception:
                pass

        if auth_json_path and os.path.isfile(auth_json_path):
            try:
                with open(auth_json_path, encoding='utf-8') as f:
                    auth_data = json.load(f)
                account_email = auth_data.get('client_email', '')
                credentials = ee.ServiceAccountCredentials(account_email, auth_json_path)
                if project_id:
                    ee.Initialize(credentials, project=project_id)
                else:
                    ee.Initialize(credentials)
                feedback.pushInfo(f'GEE conectado via Service Account: {account_email} | Proyecto: {project_id or "default"}')
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

    def _is_allowed_download_host(self, host_name):
        """Return True only for Google HTTPS endpoints used by Earth Engine."""
        host_name = (host_name or '').lower()
        allowed_hosts = (
            'googleapis.com',
            'googleusercontent.com',
            'storage.googleapis.com',
        )
        return any(
            host_name == allowed or host_name.endswith('.' + allowed)
            for allowed in allowed_hosts
        )

    def _download_https_file(self, url, out_path):
        """Download a GEE GeoTIFF from a validated HTTPS Google endpoint.

        The QGIS plugin repository blocks generic urllib downloads because
        schemes such as file:// could be abused if user-controlled URLs were
        accepted. Here the URL comes from Earth Engine getDownloadURL(), but it
        is still validated explicitly before downloading.
        """
        from urllib.parse import urlparse
        import requests

        parsed = urlparse(url)
        if parsed.scheme.lower() != 'https':
            raise QgsProcessingException(
                'La descarga desde GEE solo permite URL HTTPS.'
            )
        if not self._is_allowed_download_host(parsed.hostname):
            raise QgsProcessingException(
                'La URL generada por GEE no pertenece a un dominio permitido de Google.'
            )

        tmp_path = f'{out_path}.part'
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

        try:
            with requests.get(url, stream=True, timeout=(30, 600)) as response:
                final_url = urlparse(response.url)
                if final_url.scheme.lower() != 'https':
                    raise QgsProcessingException(
                        'La descarga redirigio a una URL no segura.'
                    )
                if not self._is_allowed_download_host(final_url.hostname):
                    raise QgsProcessingException(
                        'La descarga redirigio a un dominio no permitido.'
                    )

                response.raise_for_status()
                with open(tmp_path, 'wb') as dst:
                    for chunk in response.iter_content(chunk_size=1024 * 1024):
                        if chunk:
                            dst.write(chunk)

            os.replace(tmp_path, out_path)
        finally:
            if os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except OSError:
                    pass

    def _download_s2_images(self, ee, aoi_bbox, start_date, end_date,
                            cloud_pct, out_folder, feedback, mask_mode_i=0):
        bbox = [
            aoi_bbox.xMinimum(), aoi_bbox.yMinimum(),
            aoi_bbox.xMaximum(), aoi_bbox.yMaximum()
        ]
        ee_region = ee.Geometry.BBox(*bbox)
        EXPORT_BANDS = ['B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'B8', 'B8A', 'B11', 'B12']

        # No se aplica .select() aquí para no eliminar QA60 antes de construir
        # la máscara. El error reportado venía de intentar usar QA60 después
        # de haberlo excluido de la imagen.
        collection = (
            ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
            .filterBounds(ee_region)
            .filterDate(start_date, end_date)
            .filter(ee.Filter.lte('CLOUDY_PIXEL_PERCENTAGE', cloud_pct))
        )

        count = collection.size().getInfo()
        feedback.pushInfo(f'  -> {count} {self.tr("imagenes encontradas.")}')

        if count == 0:
            return []

        if count > 50:
            feedback.pushInfo(f'  {self.tr("Limitando a 50 imagenes de")} {count} {self.tr("disponibles.")}')
            collection = collection.limit(50)

        image_list = collection.toList(collection.size())
        n_images = min(count, 50)
        downloaded = []
        seen_dates = set()

        for i in range(n_images):
            if feedback.isCanceled():
                return downloaded

            img = ee.Image(image_list.get(i))
            date_str = img.date().format('YYYY-MM-dd').getInfo()

            if date_str in seen_dates:
                feedback.pushInfo(f'  {self.tr("duplicada")} {date_str}: {self.tr("se conserva una sola imagen por fecha")}')
                feedback.setProgress(5 + int(25 * (i + 1) / n_images))
                continue

            out_path = os.path.join(out_folder, f'{date_str}_S2.tif')

            if os.path.exists(out_path):
                feedback.pushInfo(f'  [cache] {date_str}')
                downloaded.append(date_str)
                seen_dates.add(date_str)
                feedback.setProgress(5 + int(25 * (i + 1) / n_images))
                continue

            try:
                band_names = img.bandNames().getInfo()
                missing = [b for b in EXPORT_BANDS if b not in band_names]
                if missing:
                    feedback.pushInfo(f'  omitida {date_str}: faltan bandas {missing}')
                    continue
                valid_mask = self._build_s2_mask(ee, img, mask_mode_i, band_names, feedback)
                img_masked = img.select(EXPORT_BANDS).updateMask(valid_mask)

                url = img_masked.getDownloadURL({
                    'region': ee_region,
                    'scale': 10,
                    'crs': 'EPSG:4326',
                    'format': 'GEO_TIFF',
                    'bands': EXPORT_BANDS,
                })
                self._download_https_file(url, out_path)
                downloaded.append(date_str)
                seen_dates.add(date_str)
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

            in_path = os.path.join(in_folder, f'{date_str}_S2.tif')
            out_path = os.path.join(out_folder, f'{date_str}_{veg_index}.tif')

            if not os.path.exists(in_path):
                continue

            try:
                with rasterio.open(in_path) as src:
                    meta = src.meta.copy()
                    n_rows = src.height
                    n_cols = src.width
                    nodata = src.nodata if src.nodata is not None else -9999.0
                    bands = np.stack(
                        [src.read(b + 1).astype(np.float32)
                         for b in range(min(10, src.count))],
                        axis=-1
                    )

                bands_scaled = bands / 10000.0
                n_pix = n_rows * n_cols
                bands_flat = bands_scaled.reshape(n_pix, 10)
                valid_mask = (
                    np.all(bands_flat > 0, axis=1) &  # noqa: W504
                    np.all(np.isfinite(bands_flat), axis=1)
                )
                valid_idx = np.where(valid_mask)[0]
                pred_flat = np.full(n_pix, nodata, dtype=np.float32)

                if len(valid_idx) > 0:
                    block = max(10000, len(valid_idx) // 10)
                    for start in range(0, len(valid_idx), block):
                        end = min(start + block, len(valid_idx))
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

        epoch = datetime(1970, 1, 1)
        obs_by_date = {}

        for date_str in dates:
            fpath = os.path.join(in_folder, f'{date_str}_{veg_index}.tif')
            if os.path.exists(fpath):
                obs_by_date[date_str] = fpath

        if len(obs_by_date) < 2:
            feedback.pushInfo(self.tr('Menos de 2 observaciones, omitiendo gapfilling.'))
            return

        first_f = list(obs_by_date.values())[0]
        with rasterio.open(first_f) as src:
            meta = src.meta.copy()
            n_rows = src.height
            n_cols = src.width
            nodata = src.nodata if src.nodata is not None else -9999.0

        for i, target_date in enumerate(dates):
            if feedback.isCanceled():
                return

            out_path = os.path.join(out_folder, f'{target_date}_{veg_index}.tif')
            target_dt = datetime.strptime(target_date, '%Y-%m-%d')

            obs_in_window = {
                d: f for d, f in obs_by_date.items()
                if abs((datetime.strptime(d, '%Y-%m-%d') - target_dt).days) <= gf_window
            }

            if len(obs_in_window) < 2:
                feedback.pushInfo(f'  {target_date}: {self.tr("pocas obs en ventana, omitiendo.")}')
                continue

            obs_doys_list = []
            obs_vals_list = []
            for date_str, fpath in sorted(obs_in_window.items()):
                dt = datetime.strptime(date_str, '%Y-%m-%d')
                obs_doys_list.append(float((dt - epoch).days))
                with rasterio.open(fpath) as src:
                    obs_vals_list.append(src.read(1).astype(np.float32).flatten())

            obs_doys = np.array(obs_doys_list)
            obs_values = np.stack(obs_vals_list, axis=0)
            target_ep = float((target_dt - epoch).days)
            n_pix = n_rows * n_cols
            pred_flat = np.full(n_pix, nodata, dtype=np.float32)

            block = max(10000, n_pix // 10)
            for start in range(0, n_pix, block):
                end = min(start + block, n_pix)
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
        from rasterio.warp import reproject, Resampling

        tif_files = sorted(glob.glob(os.path.join(gf_folder, f'*_{veg_index}.tif')))

        if not tif_files:
            feedback.pushInfo(self.tr('No hay archivos gapfilled para LSP.'))
            return None

        if len(tif_files) < 6:
            feedback.pushInfo(
                f'{self.tr("Se necesitan >=6 imagenes para LSP. Disponibles")}: {len(tif_files)}'
            )
            return None

        with rasterio.open(tif_files[0]) as ref:
            meta = ref.meta.copy()
            n_rows = ref.height
            n_cols = ref.width
            nodata = ref.nodata if ref.nodata is not None else -9999.0
            ref_transform = ref.transform
            ref_crs = ref.crs

        def _read_aligned_band1(fpath):
            with rasterio.open(fpath) as src:
                src_nodata = src.nodata if src.nodata is not None else nodata
                if (src.height == n_rows and src.width == n_cols and  # noqa: W504
                        src.crs == ref_crs and tuple(src.transform) == tuple(ref_transform)):
                    arr = src.read(1).astype(np.float32)
                else:
                    feedback.pushInfo(f'  LSP: armonizando grilla de {os.path.basename(fpath)}')
                    arr = np.full((n_rows, n_cols), nodata, dtype=np.float32)
                    reproject(
                        source=rasterio.band(src, 1),
                        destination=arr,
                        src_transform=src.transform,
                        src_crs=src.crs,
                        dst_transform=ref_transform,
                        dst_crs=ref_crs,
                        src_nodata=src_nodata,
                        dst_nodata=nodata,
                        resampling=Resampling.bilinear,
                    )
            return arr.flatten()

        doys_list = []
        arrays_list = []

        for fpath in tif_files:
            date_str = os.path.basename(fpath)[:10]
            try:
                doy, _ = add_doy_fn(date_str)
                arr_flat = _read_aligned_band1(fpath)
                if arr_flat.size != n_rows * n_cols:
                    feedback.pushInfo(f'  LSP: omitido por tamaño incompatible {os.path.basename(fpath)}')
                    continue
                doys_list.append(float(doy))
                arrays_list.append(arr_flat)
            except Exception as ex:
                feedback.pushInfo(f'  LSP: omitido {os.path.basename(fpath)} | {ex}')
                continue

        if len(doys_list) < 6:
            feedback.pushInfo(f'LSP omitido: solo {len(doys_list)} imagenes validas tras armonizar grillas.')
            return None

        doys_arr = np.array(doys_list)
        values_arr = np.stack(arrays_list, axis=0)
        values_arr = np.where(values_arr == nodata, np.nan, values_arr)
        n_pix = n_rows * n_cols

        valid = np.sum(np.isfinite(values_arr), axis=0) >= 6
        if not valid.any():
            feedback.pushInfo(self.tr('No hay pixeles con al menos 6 observaciones validas para LSP.'))
            return None

        lsp = lsp_fn(doys_arr, values_arr[:, valid], custom_gap=custom_gap)

        band_names = ['sos', 'eos', 'pos', 'los', 'customsos', 'customeos',
                      'vmin', 'vmax', 'n1', 'm1', 'n2', 'm2']
        bands_out = []

        for bname in band_names:
            full = np.full(n_pix, nodata, dtype=np.float32)
            full[valid] = lsp[bname]
            bands_out.append(full.reshape(n_rows, n_cols))

        lsp_path = os.path.join(lsp_folder, f'LSP_{veg_index}.tif')
        out_meta = meta.copy()
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
