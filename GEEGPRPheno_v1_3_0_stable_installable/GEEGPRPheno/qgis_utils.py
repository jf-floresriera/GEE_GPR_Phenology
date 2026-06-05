# -*- coding: utf-8 -*-
"""
Utilidades PyQGIS para cargar salidas raster al proyecto al finalizar un
algoritmo de Processing sin tocar directamente la interfaz desde el hilo de
procesamiento.
"""
import os


def queue_raster_layer(context, raster_path, layer_name, feedback=None):
    """Programa un GeoTIFF para cargarse en el proyecto QGIS al terminar.

    Usar context.addLayerToLoadOnCompletion evita cierres/crashes que pueden
    ocurrir si se llama QgsProject.instance().addMapLayer() desde un algoritmo
    que se ejecuta en un hilo de Processing.
    """
    if not raster_path:
        return False
    if not os.path.exists(raster_path):
        if feedback:
            feedback.pushWarning(f'No se pudo cargar en QGIS; no existe: {raster_path}')
        return False

    try:
        from qgis.core import QgsProcessingContext, QgsProject
        details = QgsProcessingContext.LayerDetails(
            layer_name,
            QgsProject.instance(),
            layer_name
        )
        context.addLayerToLoadOnCompletion(raster_path, details)
        if feedback:
            feedback.pushInfo(f'  -> capa programada para cargar en QGIS: {layer_name}')
        return True
    except Exception as ex:
        if feedback:
            feedback.pushWarning(f'No se pudo programar la carga de {layer_name}: {ex}')
        return False
