# -*- coding: utf-8 -*-
"""
Utilidades PyQGIS para cargar salidas raster al proyecto al finalizar un
algoritmo de Processing, con agrupacion y simbologia automatica segura.
"""
import os
from .i18n import tr as _tr
from .gee_palettes import get_vis_params, get_palette

_POSTPROCESSORS = []  # evita que QGIS destruya el postprocesador antes de tiempo


def _safe_feedback(feedback, message, warning=False):
    try:
        if feedback:
            if warning and hasattr(feedback, 'pushWarning'):
                feedback.pushWarning(message)
            else:
                feedback.pushInfo(message)
    except Exception:
        pass


try:
    from qgis.core import QgsProcessingLayerPostProcessorInterface
except Exception:
    class QgsProcessingLayerPostProcessorInterface(object):
        pass


class RasterLoadPostProcessor(QgsProcessingLayerPostProcessorInterface):
    """Postprocesador compatible con QGIS para agrupar y simbolizar capas raster."""

    def __init__(self, group_name='', style_kind='singleband', variable=''):
        self.group_name = group_name or ''
        self.style_kind = style_kind or 'singleband'
        self.variable = variable or ''

    def postProcessLayer(self, layer, context, feedback):  # firma esperada por QGIS
        try:
            self._apply_style(layer)
        except Exception as ex:
            _safe_feedback(feedback, f'{_tr("No se pudo aplicar simbologia a")} {layer.name()}: {ex}', True)
        try:
            self._move_to_group(layer)
        except Exception as ex:
            _safe_feedback(feedback, f'{_tr("No se pudo agrupar")} {layer.name()}: {ex}', True)
        try:
            layer.triggerRepaint()
        except Exception:
            pass

    def _move_to_group(self, layer):
        if not self.group_name:
            return
        from qgis.core import QgsProject
        project = QgsProject.instance()
        root = project.layerTreeRoot()
        group = root.findGroup(self.group_name)
        if group is None:
            group = root.addGroup(self.group_name)
        node = root.findLayer(layer.id())
        if node is not None and node.parent() != group:
            clone = node.clone()
            group.addChildNode(clone)
            node.parent().removeChildNode(node)

    def _apply_style(self, layer):
        if self.style_kind == 'raw_rgb':
            self._style_raw_rgb(layer)
        elif self.style_kind == 'lsp':
            self._style_lsp(layer)
        else:
            self._style_singleband(layer)

    def _style_raw_rgb(self, layer):
        from qgis.core import QgsMultiBandColorRenderer, QgsContrastEnhancement
        provider = layer.dataProvider()
        if layer.bandCount() < 3:
            self._style_singleband(layer)
            return
        # S2 exportado como B2, B3, B4, B5...; RGB natural = B4/B3/B2 = 3/2/1
        renderer = QgsMultiBandColorRenderer(provider, 3, 2, 1)
        try:
            for band, ce in [(3, renderer.redContrastEnhancement()),
                             (2, renderer.greenContrastEnhancement()),
                             (1, renderer.blueContrastEnhancement())]:
                stats = provider.bandStatistics(band)
                ce.setMinimumValue(float(stats.minimumValue))
                vmax = float(stats.maximumValue)
                # Para Sentinel-2 BOA escalado 0-10000, limitar ayuda a visualizar sin quemar la imagen.
                ce.setMaximumValue(min(vmax, 3000.0) if vmax > 3000 else vmax)
                ce.setContrastEnhancementAlgorithm(QgsContrastEnhancement.StretchToMinimumMaximum, True)
        except Exception:
            pass
        layer.setRenderer(renderer)

    def _style_singleband(self, layer):
        from qgis.PyQt.QtGui import QColor
        from qgis.core import QgsColorRampShader, QgsRasterShader, QgsSingleBandPseudoColorRenderer
        provider = layer.dataProvider()
        if not self.variable:
            self.variable = layer.name()

        # Use the original JavaScript visualization parameters whenever the
        # variable is recognized. This preserves the same color palettes and
        # fixed min/max ranges used in the GEE scripts. If the variable is not
        # recognized, fall back to the raster's data range.
        vis = get_vis_params(self.variable, fallback=True)
        colors = vis.get('palette') or self._palette_for_variable(self.variable)
        vmin = vis.get('min')
        vmax = vis.get('max')
        if vmin is None or vmax is None or not (float(vmax) > float(vmin)):
            vmin, vmax = self._robust_range(provider, 1)
        else:
            vmin, vmax = float(vmin), float(vmax)

        shader = QgsRasterShader()
        ramp = QgsColorRampShader()
        ramp.setColorRampType(QgsColorRampShader.Interpolated)
        items = []
        n = max(len(colors) - 1, 1)
        for i, hex_color in enumerate(colors):
            val = vmin + (vmax - vmin) * (i / n)
            items.append(QgsColorRampShader.ColorRampItem(val, QColor(hex_color), f'{val:.3g}'))
        ramp.setColorRampItemList(items)
        shader.setRasterShaderFunction(ramp)
        renderer = QgsSingleBandPseudoColorRenderer(provider, 1, shader)
        layer.setRenderer(renderer)

    def _style_lsp(self, layer):
        # El raster LSP es multibanda. QGIS visualiza una banda a la vez; dejamos la banda 1 (SOS)
        # con la paleta LSP original del JavaScript (LSPGeneration.js).
        self.variable = 'LSP_DOY'
        self._style_singleband(layer)

    def _robust_range(self, provider, band):
        try:
            stats = provider.bandStatistics(band)
            vmin = float(stats.minimumValue)
            vmax = float(stats.maximumValue)
            if not (vmax > vmin):
                return 0.0, 1.0
            return vmin, vmax
        except Exception:
            return 0.0, 1.0

    def _palette_for_variable(self, variable):
        # Centralized in gee_palettes.py, generated from the original JS scripts.
        return get_palette(variable)


def queue_raster_layer(context, raster_path, layer_name, feedback=None, group_name='', style_kind='singleband', variable=''):
    """Programa un GeoTIFF para cargarse en QGIS al terminar Processing.

    Además aplica un postprocesador para:
    - agrupar la capa en el panel de capas;
    - aplicar simbologia automatica segun tipo de salida;
    - evitar llamadas directas a QgsProject.addMapLayer desde el hilo del algoritmo.
    """
    if not raster_path:
        return False
    if not os.path.exists(raster_path):
        _safe_feedback(feedback, f'{_tr("No se pudo cargar en QGIS; no existe")}: {raster_path}', True)
        return False

    try:
        from qgis.core import QgsProcessingContext, QgsProject
        details = QgsProcessingContext.LayerDetails(
            layer_name,
            QgsProject.instance(),
            layer_name
        )
        pp = RasterLoadPostProcessor(group_name=group_name, style_kind=style_kind, variable=variable)
        _POSTPROCESSORS.append(pp)
        try:
            details.setPostProcessor(pp)
        except Exception:
            # Algunas versiones cambian ligeramente la API; si no permite postprocesador,
            # al menos se carga la capa sin romper el pipeline.
            pass
        try:
            if group_name and hasattr(details, 'groupName'):
                details.groupName = group_name
        except Exception:
            pass
        context.addLayerToLoadOnCompletion(raster_path, details)
        _safe_feedback(feedback, f'  -> {_tr("capa programada para cargar en QGIS")}: {group_name}/{layer_name}' if group_name else f'  -> {_tr("capa programada para cargar en QGIS")}: {layer_name}')
        return True
    except Exception as ex:
        _safe_feedback(feedback, f'{_tr("No se pudo programar la carga de")} {layer_name}: {ex}', True)
        return False
