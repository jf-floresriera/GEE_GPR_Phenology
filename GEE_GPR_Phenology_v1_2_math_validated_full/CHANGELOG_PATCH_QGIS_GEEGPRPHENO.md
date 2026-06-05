# Patch técnico — GEE GPR Phenology QGIS Plugin

## Objetivo

Este parche atiende cuatro problemas reportados durante la migración del flujo original de Google Earth Engine/JavaScript hacia un complemento de QGIS:

1. Reducir la dependencia exclusiva de Google Earth Engine.
2. Revisar y robustecer la máscara de nubosidad/agua en Sentinel-2 BOA/L2A.
3. Corregir el manejo del Project ID y la reautenticación de Earth Engine dentro de QGIS.
4. Cargar automáticamente una capa raster de comprobación en el proyecto QGIS al terminar los procesos.

## Cambios implementados

### 1. Nueva fuente de datos local externa

Archivo modificado: `GEEGPRPheno/algo_gee_pipeline.py`

Se agregó el parámetro:

- `Fuente de datos Sentinel-2 BOA`
  - `Google Earth Engine`
  - `Carpeta local S2 BOA`

La opción de carpeta local permite ejecutar el pipeline sin conectarse a GEE. El usuario puede usar imágenes BOA/L2A descargadas desde Copernicus Browser, Sentinel Hub, SNAP/Sen2Cor, Semi-Automatic Classification Plugin u otro flujo externo.

Requisito de los GeoTIFF locales:

- Archivo `.tif` o `.tiff`.
- Nombre con fecha `YYYY-MM-DD` o `YYYYMMDD`.
- Mínimo 10 bandas en el orden:
  `B2, B3, B4, B5, B6, B7, B8, B8A, B11, B12`.

El algoritmo copia los archivos válidos a `01_S2_raw` usando el nombre estándar `YYYY-MM-DD_S2.tif`.

### 2. Máscara de nubes/agua configurable

Archivo modificado: `GEEGPRPheno/algo_gee_pipeline.py`

Se agregó el parámetro:

- `Mascara de nubes/agua para descarga GEE`
  - `Estricto cultivo (SCL 4-5 + QA60)`
  - `Original JavaScript (QA60 + SCL)`
  - `Extendido SCL 4-7 + QA60`
  - `Sin mascara`

El modo recomendado para cultivos es `Estricto cultivo`, porque conserva principalmente vegetación y suelo/no vegetado, y evita incluir agua o píxeles no clasificados.

### 3. Corrección de autenticación y cambio de proyecto GEE

Archivo modificado: `GEEGPRPheno/plugin.py`

Se agregó un nuevo menú:

- `Cambiar proyecto GEE / reautenticar`

También se cambió la lógica de autenticación para:

- Mostrar el Project ID guardado.
- Permitir cambiar de proyecto antes de inicializar Earth Engine.
- Guardar el nuevo Project ID en la configuración del plugin.
- Forzar renovación de credenciales mediante `ee.Authenticate(force=True)` cuando la versión de `earthengine-api` lo soporta.
- Reiniciar la sesión local de `ee` cuando la API permite `ee.Reset()`.

### 4. Carga de resultados raster en el proyecto QGIS

Archivos modificados:

- `GEEGPRPheno/qgis_utils.py` nuevo.
- `GEEGPRPheno/algo_gee_pipeline.py`.
- `GEEGPRPheno/algo_spectral_prediction.py`.
- `GEEGPRPheno/algo_gapfilling.py`.
- `GEEGPRPheno/algo_lsp.py`.

Se agregó un parámetro booleano para preguntar si se desea cargar el resultado en QGIS:

- `Cargar resultado final como capa raster en QGIS` en el pipeline.
- `Cargar resultado como capa raster en QGIS` en los algoritmos individuales.

El cargue se hace mediante `context.addLayerToLoadOnCompletion(...)`, no con `QgsProject.instance().addMapLayer(...)` directamente, para evitar cierres o bloqueos por ejecución en hilos de Processing.

### 5. Mejora para que el panel no quede cerrado u oculto al ejecutar algoritmos

Archivo modificado: `GEEGPRPheno/plugin.py`

Después de cerrar el diálogo de Processing, el panel se vuelve a mostrar y recuperar foco si estaba visible antes de ejecutar el algoritmo.

## Validación realizada

- Los archivos `.py` compilan correctamente con `python -m py_compile`.
- No se realizó prueba funcional dentro de QGIS porque el entorno de esta revisión no tiene una sesión QGIS activa ni credenciales GEE/CDSE configuradas.

## Puntos pendientes recomendados

1. Probar en QGIS 3.x con un AOI pequeño y 2–3 fechas para verificar carga de capas.
2. Probar cambio de proyecto GEE desde el nuevo menú.
3. Validar visualmente la diferencia entre las máscaras `Estricto cultivo`, `Original JavaScript` y `Extendido`.
4. Para una versión posterior, integrar descarga directa por Copernicus Data Space/Sentinel Hub Process API con usuario, Client ID y Client Secret, si se desea automatizar completamente la alternativa no-GEE.
