# -*- coding: utf-8 -*-
"""Sistema ligero de internacionalización para el plugin.

No reemplaza Qt Linguist; permite seleccionar idioma desde el plugin y traduce
las cadenas principales de la interfaz y de Processing. Las cadenas no incluidas
vuelven automáticamente al texto original.
"""

try:
    from qgis.PyQt.QtCore import QSettings
except Exception:
    QSettings = None

LANG_OPTIONS = {
    'en': 'English',
    'es': 'Español',
    'pt': 'Português',
}

_SETTINGS_KEY = 'GEEGPRPheno/language_v151'
_DEFAULT_LANGUAGE = 'en'


def get_language():
    if QSettings is None:
        return _DEFAULT_LANGUAGE
    try:
        lang = QSettings().value(_SETTINGS_KEY, _DEFAULT_LANGUAGE, type=str)
        return lang if lang in LANG_OPTIONS else _DEFAULT_LANGUAGE
    except Exception:
        return _DEFAULT_LANGUAGE


def set_language(lang):
    lang = lang if lang in LANG_OPTIONS else _DEFAULT_LANGUAGE
    if QSettings is not None:
        try:
            QSettings().setValue(_SETTINGS_KEY, lang)
        except Exception:
            pass
    return lang


_TRANSLATIONS = {
    'en': {
        'Abrir GEE GPR Phenology Tools': 'Open GEE GPR Phenology Tools',
        'Abrir panel GEE GPR Phenology': 'Open GEE GPR Phenology panel',
        'Autenticar Google Earth Engine': 'Authenticate Google Earth Engine',
        'Cambiar proyecto GEE / reautenticar': 'Change GEE project / re-authenticate',
        'Verificar conexion GEE': 'Check GEE connection',
        'Dibujar poligono AOI en el mapa': 'Draw AOI polygon on the map',
        'Diagnosticar dependencias Python': 'Diagnose Python dependencies',
        'Instalar/actualizar dependencias Python': 'Install/update Python dependencies',
        'Ayuda y documentacion': 'Help and documentation',
        'Idioma / Language / Idioma': 'Language / Idioma / Idioma',
        'Verificar GEE': 'Check GEE',
        'Fenologia': 'Phenology',
        '1. Prediccion Espectral GPR': '1. Spectral GPR prediction',
        '2. Relleno Temporal GPR (Gapfilling)': '2. Temporal GPR gapfilling',
        '3. Metricas LSP (Fenologia)': '3. LSP metrics (phenology)',
        '4. Pipeline GEE Automatico': '4. Automatic GEE pipeline',
        'Dibujar AOI en el mapa': 'Draw AOI on the map',
        'Abrir y ejecutar': 'Open and run',
        'Version': 'Version',
        'Idioma': 'Language',
        'El idioma se aplicará completamente al reabrir el panel o reiniciar QGIS.': 'The language will be fully applied after reopening the panel or restarting QGIS.',

        '1. Predicción Espectral GPR (pixel a pixel)': '1. Spectral GPR prediction (pixel by pixel)',
        '2. Relleno Temporal de Series GPR (Gapfilling)': '2. Temporal GPR series gapfilling',
        '3. Generación de Métricas LSP (Fenología)': '3. LSP metrics generation (phenology)',
        '4. Pipeline GEE Automatico (Descarga + GPR + LSP)': '4. Automatic GEE pipeline (download + GPR + LSP)',
        'GEE GPR Phenology': 'GEE GPR Phenology',
        'Ráster Sentinel-2 BOA (mínimo 10 bandas)': 'Sentinel-2 BOA raster (minimum 10 bands)',
        'Variable biofísica a estimar': 'Biophysical variable to estimate',
        'Variable biofísica': 'Biophysical variable',
        'Variable biofisica': 'Biophysical variable',
        'Factor de escala de las bandas': 'Band scale factor',
        'Aplicar máscara de nubes/agua': 'Apply cloud/water mask',
        'Ráster máscara nubes (1=válido, 0=nube)': 'Cloud mask raster (1=valid, 0=cloud)',
        'Cargar resultado como capa raster en QGIS': 'Load result as raster layer in QGIS',
        'Cargar salidas generadas como capas raster en QGIS': 'Load generated outputs as raster layers in QGIS',
        'Ráster de salida — índice biofísico GPR': 'Output raster — GPR biophysical index',
        'Carpeta con rásters del índice (YYYY-MM-DD_*.tif)': 'Folder with index rasters (YYYY-MM-DD_*.tif)',
        'Fecha objetivo (YYYY-MM-DD)': 'Target date (YYYY-MM-DD)',
        'Ventana temporal (±días)': 'Temporal window (±days)',
        'Tipo de cultivo': 'Crop type',
        'Ráster de salida — serie gapfilled': 'Output raster — gapfilled series',
        'Carpeta con rásters gapfilled temporales (YYYY-MM-DD_*.tif)': 'Folder with temporal gapfilled rasters (YYYY-MM-DD_*.tif)',
        'Umbral relativo para SOS/EOS personalizado (0.0–1.0)': 'Relative threshold for custom SOS/EOS (0.0–1.0)',
        'Ráster de salida — métricas LSP (12 bandas)': 'Output raster — LSP metrics (12 bands)',
        'Fuente de datos Sentinel-2 BOA': 'Sentinel-2 BOA data source',
        'Area de interes (capa vectorial)': 'Area of interest (vector layer)',
        'Fecha inicio del cultivo (YYYY-MM-DD)': 'Crop start date (YYYY-MM-DD)',
        'Fecha fin del cultivo (YYYY-MM-DD)': 'Crop end date (YYYY-MM-DD)',
        'Porcentaje maximo de nubosidad (0-100)': 'Maximum cloud percentage (0-100)',
        'Mascara de nubes/agua para descarga GEE': 'Cloud/water mask for GEE download',
        'Ventana de gapfilling temporal (+-dias)': 'Temporal gapfilling window (+-days)',
        'Calcular metricas LSP al final': 'Compute LSP metrics at the end',
        'Umbral relativo SOS/EOS (0.0-1.0)': 'Relative SOS/EOS threshold (0.0-1.0)',
        'ID del proyecto GEE (opcional)': 'GEE project ID (optional)',
        'Clave Service Account JSON (opcional)': 'Service Account JSON key (optional)',
        'Carpeta local con GeoTIFF S2 BOA de 10 bandas (opcional)': 'Local folder with 10-band S2 BOA GeoTIFFs (optional)',
        'Generar reportes graficos PDF (series temporales, mapas y metricas LSP)': 'Generate PDF graphic reports (time series, maps and LSP metrics)',
        'Carpeta de salida': 'Output folder',
    },
    'pt': {
        'Abrir GEE GPR Phenology Tools': 'Abrir ferramentas GEE GPR Phenology',
        'Abrir panel GEE GPR Phenology': 'Abrir painel GEE GPR Phenology',
        'Autenticar Google Earth Engine': 'Autenticar Google Earth Engine',
        'Cambiar proyecto GEE / reautenticar': 'Alterar projeto GEE / reautenticar',
        'Verificar conexion GEE': 'Verificar conexão GEE',
        'Dibujar poligono AOI en el mapa': 'Desenhar polígono AOI no mapa',
        'Diagnosticar dependencias Python': 'Diagnosticar dependências Python',
        'Instalar/actualizar dependencias Python': 'Instalar/atualizar dependências Python',
        'Ayuda y documentacion': 'Ajuda e documentação',
        'Idioma / Language / Idioma': 'Idioma / Language / Idioma',
        'Verificar GEE': 'Verificar GEE',
        'Fenologia': 'Fenologia',
        '1. Prediccion Espectral GPR': '1. Predição espectral GPR',
        '2. Relleno Temporal GPR (Gapfilling)': '2. Preenchimento temporal GPR (gapfilling)',
        '3. Metricas LSP (Fenologia)': '3. Métricas LSP (fenologia)',
        '4. Pipeline GEE Automatico': '4. Pipeline GEE automático',
        'Dibujar AOI en el mapa': 'Desenhar AOI no mapa',
        'Abrir y ejecutar': 'Abrir e executar',
        'Version': 'Versão',
        'Idioma': 'Idioma',
        'El idioma se aplicará completamente al reabrir el panel o reiniciar QGIS.': 'O idioma será aplicado completamente ao reabrir o painel ou reiniciar o QGIS.',

        '1. Predicción Espectral GPR (pixel a pixel)': '1. Predição espectral GPR (pixel a pixel)',
        '2. Relleno Temporal de Series GPR (Gapfilling)': '2. Preenchimento temporal de séries GPR (gapfilling)',
        '3. Generación de Métricas LSP (Fenología)': '3. Geração de métricas LSP (fenologia)',
        '4. Pipeline GEE Automatico (Descarga + GPR + LSP)': '4. Pipeline GEE automático (download + GPR + LSP)',
        'GEE GPR Phenology': 'GEE GPR Phenology',
        'Ráster Sentinel-2 BOA (mínimo 10 bandas)': 'Raster Sentinel-2 BOA (mínimo 10 bandas)',
        'Variable biofísica a estimar': 'Variável biofísica a estimar',
        'Variable biofísica': 'Variável biofísica',
        'Variable biofisica': 'Variável biofísica',
        'Factor de escala de las bandas': 'Fator de escala das bandas',
        'Aplicar máscara de nubes/agua': 'Aplicar máscara de nuvens/água',
        'Ráster máscara nubes (1=válido, 0=nube)': 'Raster máscara de nuvens (1=válido, 0=nuvem)',
        'Cargar resultado como capa raster en QGIS': 'Carregar resultado como camada raster no QGIS',
        'Cargar salidas generadas como capas raster en QGIS': 'Carregar saídas geradas como camadas raster no QGIS',
        'Ráster de salida — índice biofísico GPR': 'Raster de saída — índice biofísico GPR',
        'Carpeta con rásters del índice (YYYY-MM-DD_*.tif)': 'Pasta com rasters do índice (YYYY-MM-DD_*.tif)',
        'Fecha objetivo (YYYY-MM-DD)': 'Data alvo (YYYY-MM-DD)',
        'Ventana temporal (±días)': 'Janela temporal (±dias)',
        'Tipo de cultivo': 'Tipo de cultura',
        'Ráster de salida — serie gapfilled': 'Raster de saída — série preenchida',
        'Carpeta con rásters gapfilled temporales (YYYY-MM-DD_*.tif)': 'Pasta com rasters temporais preenchidos (YYYY-MM-DD_*.tif)',
        'Umbral relativo para SOS/EOS personalizado (0.0–1.0)': 'Limiar relativo para SOS/EOS personalizado (0.0–1.0)',
        'Ráster de salida — métricas LSP (12 bandas)': 'Raster de saída — métricas LSP (12 bandas)',
        'Fuente de datos Sentinel-2 BOA': 'Fonte de dados Sentinel-2 BOA',
        'Area de interes (capa vectorial)': 'Área de interesse (camada vetorial)',
        'Fecha inicio del cultivo (YYYY-MM-DD)': 'Data inicial da cultura (YYYY-MM-DD)',
        'Fecha fin del cultivo (YYYY-MM-DD)': 'Data final da cultura (YYYY-MM-DD)',
        'Porcentaje maximo de nubosidad (0-100)': 'Percentual máximo de nebulosidade (0-100)',
        'Mascara de nubes/agua para descarga GEE': 'Máscara de nuvens/água para download GEE',
        'Ventana de gapfilling temporal (+-dias)': 'Janela de gapfilling temporal (+-dias)',
        'Calcular metricas LSP al final': 'Calcular métricas LSP no final',
        'Umbral relativo SOS/EOS (0.0-1.0)': 'Limiar relativo SOS/EOS (0.0-1.0)',
        'ID del proyecto GEE (opcional)': 'ID do projeto GEE (opcional)',
        'Clave Service Account JSON (opcional)': 'Chave JSON da Service Account (opcional)',
        'Carpeta local con GeoTIFF S2 BOA de 10 bandas (opcional)': 'Pasta local com GeoTIFF S2 BOA de 10 bandas (opcional)',
        'Generar reportes graficos PDF (series temporales, mapas y metricas LSP)': 'Gerar relatórios gráficos PDF (séries temporais, mapas e métricas LSP)',
        'Carpeta de salida': 'Pasta de saída',
    }
}



# Traducciones adicionales incorporadas en v1.5.1. Se agregan por update para
# no alterar la estructura anterior del diccionario.
_EXTRA_TRANSLATIONS = {
    'en': {
        # General/default
        'Español': 'Spanish', 'Português': 'Portuguese',
        'Descripcion': 'Description', 'Desarrollador': 'Developer',
        'Algoritmos incluidos': 'Included algorithms', 'Dependencias': 'Dependencies',
        'Abrir LinkedIn': 'Open LinkedIn', 'Enviar correo': 'Send email',
        'Espectral': 'Spectral', 'GEE Auto': 'GEE Auto',
        'Estado GEE - clic para autenticar': 'GEE status - click to authenticate',
        'GEE conectado correctamente': 'GEE connected correctly',
        'Sin conexion GEE - clic para autenticar': 'No GEE connection - click to authenticate',
        'Sin GEE': 'No GEE', 'GEE activo': 'GEE active',
        'Google Earth Engine conectado correctamente.\nEl Pipeline Automatico esta listo.': 'Google Earth Engine is connected correctly.\nThe automatic pipeline is ready.',
        'Sin conexion GEE': 'No GEE connection',
        'No hay conexion activa con Google Earth Engine.\n\nDeseas autenticarte ahora?': 'There is no active Google Earth Engine connection.\n\nDo you want to authenticate now?',
        'Dibujar AOI': 'Draw AOI',
        'Dibuja el polígono sobre el mapa:\n\n• Clic izquierdo: agregar vértices.\n• Clic derecho: cerrar y crear la capa AOI.\n\nLa capa se llamará AOI_GEEGPRPheno_dibujado y quedará activa para usarla en el pipeline.': 'Draw the polygon on the map:\n\n• Left click: add vertices.\n• Right click: close and create the AOI layer.\n\nThe layer will be named AOI_GEEGPRPheno_dibujado and will be active for use in the pipeline.',
        'Dibuja al menos 3 vértices y cierra con clic derecho.': 'Draw at least 3 vertices and close with right click.',
        'AOI dibujada creada y activada. Selecciónala como AOI_LAYER en el pipeline.': 'Drawn AOI created and activated. Select it as AOI_LAYER in the pipeline.',
        'No se pudo activar la herramienta AOI:\n{ex}': 'Could not activate the AOI tool:\n{ex}',
        'No se pudo crear la capa AOI:\n{ex}': 'Could not create the AOI layer:\n{ex}',
        'ID de proyecto Google Cloud / GEE': 'Google Cloud / GEE project ID',
        'Proyecto GEE guardado': 'Saved GEE project',
        'Autenticacion Google Earth Engine': 'Google Earth Engine authentication',
        'Autenticacion exitosa': 'Authentication successful',
        'Error de autenticacion': 'Authentication error',
        'Instalar dependencias Python': 'Install Python dependencies',
        'Dependencias instaladas': 'Dependencies installed',
        'Instalación incompleta': 'Incomplete installation',
        'GEEGPRPheno — dependencias Python': 'GEEGPRPheno — Python dependencies',
        # Processing options
        'Carpeta local S2 BOA': 'Local S2 BOA folder',
        'Estricto cultivo (SCL 4-5, QA60 si existe)': 'Strict crop mask (SCL 4-5, QA60 if available)',
        'Original JavaScript (SCL + QA60 si existe)': 'Original JavaScript (SCL + QA60 if available)',
        'Extendido SCL 4-7, QA60 si existe': 'Extended SCL 4-7, QA60 if available',
        'Sin mascara': 'No mask',
        'media': 'average', 'maiz': 'maize', 'trigo': 'wheat', 'cebada': 'barley',
        'girasol': 'sunflower', 'colza': 'rapeseed', 'guisante': 'pea',
        'alfalfa': 'alfalfa', 'remolacha': 'sugar beet', 'patata': 'potato',
        # Feedback/messages
        'Formato de fecha incorrecto (YYYY-MM-DD)': 'Incorrect date format (YYYY-MM-DD)',
        'La fecha fin debe ser posterior a la fecha inicio.': 'End date must be later than start date.',
        'Leyendo area de interes...': 'Reading area of interest...',
        'Conectando a Google Earth Engine...': 'Connecting to Google Earth Engine...',
        'Usando fuente local externa: GeoTIFF Sentinel-2 BOA ya descargados.': 'Using external local source: previously downloaded Sentinel-2 BOA GeoTIFFs.',
        'No se encontraron imagenes S2 con los filtros:': 'No S2 images were found with the selected filters:',
        'Periodo': 'Period', 'Nubosidad max': 'Max cloud cover',
        'Prueba aumentar el % de nubosidad o ampliar el periodo.': 'Try increasing the cloud percentage or extending the date range.',
        'fechas unicas disponibles.': 'unique dates available.',
        'Aplicando prediccion espectral GPR': 'Applying spectral GPR prediction',
        'Aplicando gapfilling temporal GPR': 'Applying temporal GPR gapfilling',
        'Calculando metricas LSP...': 'Computing LSP metrics...',
        'Pipeline GEE completado.': 'GEE pipeline completed.',
        'fecha duplicada ignorada': 'duplicate date ignored',
        'limpieza': 'cleanup', 'raster antiguos eliminados en': 'old rasters removed in',
        'raster armonizado a grilla comun': 'raster harmonized to common grid',
        'no se pudo armonizar': 'could not harmonize',
        'grilla comun aplicada a': 'common grid applied to',
        'Seleccionaste fuente local, pero no indicaste una carpeta valida con GeoTIFF Sentinel-2 BOA.': 'You selected a local source but did not provide a valid folder with Sentinel-2 BOA GeoTIFFs.',
        'No se encontraron GeoTIFF en la carpeta local': 'No GeoTIFFs were found in the local folder',
        'omitido sin fecha en nombre': 'skipped because no date was found in the filename',
        'omitido (<10 bandas)': 'skipped (<10 bands)',
        'omitido no legible': 'skipped because it could not be read',
        'fecha duplicada omitida': 'duplicate date skipped',
        'local ok': 'local ok',
        'aviso: QA60 no disponible; se aplica máscara basada en SCL.': 'notice: QA60 is not available; an SCL-based mask will be applied.',
        'aviso: SCL no disponible; se usa QA60 si existe, o sin máscara si no existe.': 'notice: SCL is not available; QA60 will be used if available, otherwise no mask is applied.',
        'imagenes encontradas.': 'images found.',
        'Limitando a 50 imagenes de': 'Limiting to 50 images out of',
        'disponibles.': 'available.',
        'duplicada': 'duplicate', 'se conserva una sola imagen por fecha': 'only one image per date is kept',
        'faltan bandas': 'missing bands', 'omitida': 'skipped',
        'Menos de 2 observaciones, omitiendo gapfilling.': 'Fewer than 2 observations; skipping gapfilling.',
        'pocas obs en ventana, omitiendo.': 'too few observations in the window; skipping.',
        'No hay archivos gapfilled para LSP.': 'No gapfilled files found for LSP.',
        'Se necesitan >=6 imagenes para LSP. Disponibles': 'At least 6 images are required for LSP. Available',
        'No hay pixeles con al menos 6 observaciones validas para LSP.': 'No pixels with at least 6 valid observations for LSP.',
        'No se pudieron generar PDF: matplotlib no disponible': 'PDF reports could not be generated: matplotlib is not available',
        'No se pudo guardar CSV resumen': 'Could not save summary CSV',
        # QGIS groups/layer loading
        'GEEGPRPheno - Raw Sentinel-2': 'GEEGPRPheno - Raw Sentinel-2',
        'GEEGPRPheno - GPR pred': 'GEEGPRPheno - GPR prediction',
        'GEEGPRPheno - Gapfilled': 'GEEGPRPheno - Gapfilled',
        'GEEGPRPheno - LSP': 'GEEGPRPheno - LSP',
        'No se pudo aplicar simbologia a': 'Could not apply symbology to',
        'No se pudo agrupar': 'Could not group',
        'No se pudo cargar en QGIS; no existe': 'Could not load into QGIS; file does not exist',
        'No se pudo programar la carga de': 'Could not schedule loading of',
        'capa programada para cargar en QGIS': 'layer scheduled to load into QGIS',
        # PDF/report strings
        'Reporte GEE GPR Phenology': 'GEE GPR Phenology report',
        'Contenido del reporte:': 'Report contents:',
        'Series temporales de estadisticos espaciales (prediccion y gapfilling).': 'Time series of spatial statistics (prediction and gapfilling).',
        'Mapas de la ultima fecha disponible para prediccion GPR y gapfilling.': 'Maps of the latest available date for GPR prediction and gapfilling.',
        'Resumen de metricas LSP y atlas de bandas en PDF adicional.': 'Summary of LSP metrics and band atlas in an additional PDF.',
        'N. predicciones': 'No. predictions', 'N. gapfilled': 'No. gapfilled',
        'Carpeta reportes': 'Reports folder', 'CSV resumen': 'Summary CSV',
        'Nota: Los estadisticos se calculan con pixeles validos, excluyendo nodata.': 'Note: statistics are computed using valid pixels, excluding nodata.',
        'Prediccion GPR — media': 'GPR prediction — mean',
        'Prediccion GPR — IQR': 'GPR prediction — IQR',
        'Gapfilled GPR — media': 'Gapfilled GPR — mean',
        'Gapfilled GPR — IQR': 'Gapfilled GPR — IQR',
        'Serie temporal de': 'Time series of', 'Fecha': 'Date',
        'Ultima prediccion GPR': 'Latest GPR prediction',
        'Ultimo gapfilling GPR': 'Latest GPR gapfilling',
        'Columna': 'Column', 'Fila': 'Row',
        'Atlas de metricas LSP': 'LSP metrics atlas',
        'Banda': 'Band',
        'Cada pagina siguiente muestra el mapa espacial y un histograma resumido.': 'Each following page shows the spatial map and a summary histogram.',
        'Histograma': 'Histogram', 'Frecuencia': 'Frequency', 'Sin datos validos': 'No valid data',
    },
    'pt': {
        'English': 'Inglês', 'Español': 'Espanhol',
        'Descripcion': 'Descrição', 'Desarrollador': 'Desenvolvedor',
        'Algoritmos incluidos': 'Algoritmos incluídos', 'Dependencias': 'Dependências',
        'Abrir LinkedIn': 'Abrir LinkedIn', 'Enviar correo': 'Enviar e-mail',
        'Espectral': 'Espectral', 'GEE Auto': 'GEE Auto',
        'Estado GEE - clic para autenticar': 'Estado GEE - clique para autenticar',
        'GEE conectado correctamente': 'GEE conectado corretamente',
        'Sin conexion GEE - clic para autenticar': 'Sem conexão GEE - clique para autenticar',
        'Sin GEE': 'Sem GEE', 'GEE activo': 'GEE ativo',
        'Google Earth Engine conectado correctamente.\nEl Pipeline Automatico esta listo.': 'Google Earth Engine conectado corretamente.\nO pipeline automático está pronto.',
        'Sin conexion GEE': 'Sem conexão GEE',
        'No hay conexion activa con Google Earth Engine.\n\nDeseas autenticarte ahora?': 'Não há conexão ativa com o Google Earth Engine.\n\nDeseja autenticar agora?',
        'Dibujar AOI': 'Desenhar AOI',
        'Dibuja el polígono sobre el mapa:\n\n• Clic izquierdo: agregar vértices.\n• Clic derecho: cerrar y crear la capa AOI.\n\nLa capa se llamará AOI_GEEGPRPheno_dibujado y quedará activa para usarla en el pipeline.': 'Desenhe o polígono no mapa:\n\n• Clique esquerdo: adicionar vértices.\n• Clique direito: fechar e criar a camada AOI.\n\nA camada será chamada AOI_GEEGPRPheno_dibujado e ficará ativa para uso no pipeline.',
        'Dibuja al menos 3 vértices y cierra con clic derecho.': 'Desenhe pelo menos 3 vértices e feche com clique direito.',
        'AOI dibujada creada y activada. Selecciónala como AOI_LAYER en el pipeline.': 'AOI desenhada criada e ativada. Selecione-a como AOI_LAYER no pipeline.',
        'ID de proyecto Google Cloud / GEE': 'ID do projeto Google Cloud / GEE',
        'Proyecto GEE guardado': 'Projeto GEE salvo',
        'Autenticacion Google Earth Engine': 'Autenticação Google Earth Engine',
        'Autenticacion exitosa': 'Autenticação bem-sucedida',
        'Error de autenticacion': 'Erro de autenticação',
        'Instalar dependencias Python': 'Instalar dependências Python',
        'Dependencias instaladas': 'Dependências instaladas',
        'Instalación incompleta': 'Instalação incompleta',
        'GEEGPRPheno — dependencias Python': 'GEEGPRPheno — dependências Python',
        'Carpeta local S2 BOA': 'Pasta local S2 BOA',
        'Estricto cultivo (SCL 4-5, QA60 si existe)': 'Máscara estrita para cultivo (SCL 4-5, QA60 se existir)',
        'Original JavaScript (SCL + QA60 si existe)': 'JavaScript original (SCL + QA60 se existir)',
        'Extendido SCL 4-7, QA60 si existe': 'Estendido SCL 4-7, QA60 se existir',
        'Sin mascara': 'Sem máscara',
        'media': 'média', 'maiz': 'milho', 'trigo': 'trigo', 'cebada': 'cevada',
        'girasol': 'girassol', 'colza': 'colza', 'guisante': 'ervilha',
        'alfalfa': 'alfafa', 'remolacha': 'beterraba', 'patata': 'batata',
        'Formato de fecha incorrecto (YYYY-MM-DD)': 'Formato de data incorreto (YYYY-MM-DD)',
        'La fecha fin debe ser posterior a la fecha inicio.': 'A data final deve ser posterior à data inicial.',
        'Leyendo area de interes...': 'Lendo área de interesse...',
        'Conectando a Google Earth Engine...': 'Conectando ao Google Earth Engine...',
        'Usando fuente local externa: GeoTIFF Sentinel-2 BOA ya descargados.': 'Usando fonte local externa: GeoTIFF Sentinel-2 BOA já baixados.',
        'No se encontraron imagenes S2 con los filtros:': 'Nenhuma imagem S2 foi encontrada com os filtros selecionados:',
        'Periodo': 'Período', 'Nubosidad max': 'Nebulosidade máx.',
        'Prueba aumentar el % de nubosidad o ampliar el periodo.': 'Tente aumentar a porcentagem de nebulosidade ou ampliar o período.',
        'fechas unicas disponibles.': 'datas únicas disponíveis.',
        'Aplicando prediccion espectral GPR': 'Aplicando predição espectral GPR',
        'Aplicando gapfilling temporal GPR': 'Aplicando gapfilling temporal GPR',
        'Calculando metricas LSP...': 'Calculando métricas LSP...',
        'Pipeline GEE completado.': 'Pipeline GEE concluído.',
        'fecha duplicada ignorada': 'data duplicada ignorada',
        'limpieza': 'limpeza', 'raster antiguos eliminados en': 'rasters antigos removidos em',
        'raster armonizado a grilla comun': 'raster harmonizado para grade comum',
        'no se pudo armonizar': 'não foi possível harmonizar',
        'grilla comun aplicada a': 'grade comum aplicada a',
        'Seleccionaste fuente local, pero no indicaste una carpeta valida con GeoTIFF Sentinel-2 BOA.': 'Você selecionou fonte local, mas não indicou uma pasta válida com GeoTIFF Sentinel-2 BOA.',
        'No se encontraron GeoTIFF en la carpeta local': 'Nenhum GeoTIFF foi encontrado na pasta local',
        'omitido sin fecha en nombre': 'ignorado sem data no nome',
        'omitido (<10 bandas)': 'ignorado (<10 bandas)',
        'omitido no legible': 'ignorado porque não pôde ser lido',
        'fecha duplicada omitida': 'data duplicada ignorada',
        'local ok': 'local ok',
        'aviso: QA60 no disponible; se aplica máscara basada en SCL.': 'aviso: QA60 indisponível; será aplicada máscara baseada em SCL.',
        'aviso: SCL no disponible; se usa QA60 si existe, o sin máscara si no existe.': 'aviso: SCL indisponível; será usado QA60 se existir, caso contrário sem máscara.',
        'imagenes encontradas.': 'imagens encontradas.',
        'Limitando a 50 imagenes de': 'Limitando a 50 imagens de',
        'disponibles.': 'disponíveis.',
        'duplicada': 'duplicada', 'se conserva una sola imagen por fecha': 'mantém-se apenas uma imagem por data',
        'faltan bandas': 'bandas ausentes', 'omitida': 'ignorada',
        'Menos de 2 observaciones, omitiendo gapfilling.': 'Menos de 2 observações; ignorando gapfilling.',
        'pocas obs en ventana, omitiendo.': 'poucas observações na janela; ignorando.',
        'No hay archivos gapfilled para LSP.': 'Não há arquivos gapfilled para LSP.',
        'Se necesitan >=6 imagenes para LSP. Disponibles': 'São necessárias >=6 imagens para LSP. Disponíveis',
        'No hay pixeles con al menos 6 observaciones validas para LSP.': 'Não há pixels com pelo menos 6 observações válidas para LSP.',
        'No se pudieron generar PDF: matplotlib no disponible': 'Não foi possível gerar PDF: matplotlib indisponível',
        'No se pudo guardar CSV resumen': 'Não foi possível salvar o CSV de resumo',
        'GEEGPRPheno - Raw Sentinel-2': 'GEEGPRPheno - Sentinel-2 bruto',
        'GEEGPRPheno - GPR pred': 'GEEGPRPheno - Predição GPR',
        'GEEGPRPheno - Gapfilled': 'GEEGPRPheno - Gapfilled',
        'GEEGPRPheno - LSP': 'GEEGPRPheno - LSP',
        'No se pudo aplicar simbologia a': 'Não foi possível aplicar simbologia a',
        'No se pudo agrupar': 'Não foi possível agrupar',
        'No se pudo cargar en QGIS; no existe': 'Não foi possível carregar no QGIS; não existe',
        'No se pudo programar la carga de': 'Não foi possível programar o carregamento de',
        'capa programada para cargar en QGIS': 'camada programada para carregar no QGIS',
        'Reporte GEE GPR Phenology': 'Relatório GEE GPR Phenology',
        'Contenido del reporte:': 'Conteúdo do relatório:',
        'Series temporales de estadisticos espaciales (prediccion y gapfilling).': 'Séries temporais de estatísticas espaciais (predição e gapfilling).',
        'Mapas de la ultima fecha disponible para prediccion GPR y gapfilling.': 'Mapas da última data disponível para predição GPR e gapfilling.',
        'Resumen de metricas LSP y atlas de bandas en PDF adicional.': 'Resumo de métricas LSP e atlas de bandas em PDF adicional.',
        'N. predicciones': 'N. predições', 'N. gapfilled': 'N. gapfilled',
        'Carpeta reportes': 'Pasta de relatórios', 'CSV resumen': 'CSV resumo',
        'Nota: Los estadisticos se calculan con pixeles validos, excluyendo nodata.': 'Nota: as estatísticas são calculadas com pixels válidos, excluindo nodata.',
        'Prediccion GPR — media': 'Predição GPR — média',
        'Prediccion GPR — IQR': 'Predição GPR — IQR',
        'Gapfilled GPR — media': 'Gapfilled GPR — média',
        'Gapfilled GPR — IQR': 'Gapfilled GPR — IQR',
        'Serie temporal de': 'Série temporal de', 'Fecha': 'Data',
        'Ultima prediccion GPR': 'Última predição GPR',
        'Ultimo gapfilling GPR': 'Último gapfilling GPR',
        'Columna': 'Coluna', 'Fila': 'Linha',
        'Atlas de metricas LSP': 'Atlas de métricas LSP',
        'Banda': 'Banda',
        'Cada pagina siguiente muestra el mapa espacial y un histograma resumido.': 'Cada página seguinte mostra o mapa espacial e um histograma resumido.',
        'Histograma': 'Histograma', 'Frecuencia': 'Frequência', 'Sin datos validos': 'Sem dados válidos',
    },
    'es': {}
}


_EXTRA_TRANSLATIONS['en'].update({

        'Aplica modelo GPR pre-entrenado sobre las\n10 bandas Sentinel-2 BOA para estimar\npixel a pixel variables biofisicas:\nLAI, Cab, Cw, Cm, FVC, laiCab, laiCm, laiCw': 'Applies a pre-trained GPR model to the\n10 Sentinel-2 BOA bands to estimate\nbiophysical variables pixel by pixel:\nLAI, Cab, Cw, Cm, FVC, laiCab, laiCm, laiCw',
        'Usa GPR con kernel RBF temporal para\nrellenar lagunas en la serie temporal\ncausadas por cobertura nubosa.\nHiperparametros calibrados por cultivo.': 'Uses GPR with a temporal RBF kernel to\nfill gaps in the time series\ncaused by cloud cover.\nCrop-calibrated hyperparameters.',
        'Ajusta doble logistica por pixel sobre\nla serie temporal gapfilled y extrae:\nSOS, EOS, POS, LOS, vmin, vmax\ny parametros n1, m1, n2, m2.': 'Fits a double logistic curve per pixel over\nthe gapfilled time series and extracts:\nSOS, EOS, POS, LOS, vmin, vmax\nand parameters n1, m1, n2, m2.',
        'Pipeline completo automatico:\n1  Descarga S2 L2A desde Google Earth Engine\n2  Filtra por area, fechas y nubosidad\n3  Prediccion espectral GPR\n4  Gapfilling temporal GPR\n5  Metricas LSP fenologicas (opcional)': 'Full automatic pipeline:\n1  Downloads S2 L2A from Google Earth Engine\n2  Filters by area, dates and cloud cover\n3  Spectral GPR prediction\n4  Temporal GPR gapfilling\n5  LSP phenology metrics (optional)',
        'Plugin de QGIS para la estimacion de variables biofisicas y fenologia de cultivos a partir de imagenes Sentinel-2 BOA, usando modelos de Regresion por Procesos Gaussianos (GPR) pre-entrenados. Incluye pipeline automatico con descarga directa desde Google Earth Engine (GEE).\n\nBasado en la metodologia de:\nM. Salinero-Delgado et al. — GEEGPRPhenoDemos': 'QGIS plugin for estimating biophysical variables and crop phenology from Sentinel-2 BOA imagery using pre-trained Gaussian Process Regression (GPR) models. It includes an automatic pipeline with direct download from Google Earth Engine (GEE).\n\nBased on the methodology of:\nM. Salinero-Delgado et al. — GEEGPRPhenoDemos',
        'Estima LAI, Cab, Cw, Cm, FVC pixel a pixel': 'Estimates LAI, Cab, Cw, Cm, FVC pixel by pixel',
        '2. Relleno Temporal GPR': '2. Temporal GPR gapfilling',
        'Rellena series temporales con cobertura nubosa': 'Fills time series affected by cloud cover',
        'SOS, EOS, POS, LOS via doble logistica': 'SOS, EOS, POS, LOS via double logistic',
        'Descarga S2 + GPR + LSP en un solo paso': 'Downloads S2 + GPR + LSP in one step',

})
_EXTRA_TRANSLATIONS['pt'].update({

        'Aplica modelo GPR pre-entrenado sobre las\n10 bandas Sentinel-2 BOA para estimar\npixel a pixel variables biofisicas:\nLAI, Cab, Cw, Cm, FVC, laiCab, laiCm, laiCw': 'Aplica um modelo GPR pré-treinado às\n10 bandas Sentinel-2 BOA para estimar\nvariáveis biofísicas pixel a pixel:\nLAI, Cab, Cw, Cm, FVC, laiCab, laiCm, laiCw',
        'Usa GPR con kernel RBF temporal para\nrellenar lagunas en la serie temporal\ncausadas por cobertura nubosa.\nHiperparametros calibrados por cultivo.': 'Usa GPR com kernel RBF temporal para\npreencher lacunas na série temporal\ncausadas por cobertura de nuvens.\nHiperparâmetros calibrados por cultura.',
        'Ajusta doble logistica por pixel sobre\nla serie temporal gapfilled y extrae:\nSOS, EOS, POS, LOS, vmin, vmax\ny parametros n1, m1, n2, m2.': 'Ajusta dupla logística por pixel sobre\na série temporal gapfilled e extrai:\nSOS, EOS, POS, LOS, vmin, vmax\ne parâmetros n1, m1, n2, m2.',
        'Pipeline completo automatico:\n1  Descarga S2 L2A desde Google Earth Engine\n2  Filtra por area, fechas y nubosidad\n3  Prediccion espectral GPR\n4  Gapfilling temporal GPR\n5  Metricas LSP fenologicas (opcional)': 'Pipeline automático completo:\n1  Baixa S2 L2A do Google Earth Engine\n2  Filtra por área, datas e nebulosidade\n3  Predição espectral GPR\n4  Gapfilling temporal GPR\n5  Métricas fenológicas LSP (opcional)',
        'Plugin de QGIS para la estimacion de variables biofisicas y fenologia de cultivos a partir de imagenes Sentinel-2 BOA, usando modelos de Regresion por Procesos Gaussianos (GPR) pre-entrenados. Incluye pipeline automatico con descarga directa desde Google Earth Engine (GEE).\n\nBasado en la metodologia de:\nM. Salinero-Delgado et al. — GEEGPRPhenoDemos': 'Plugin QGIS para estimar variáveis biofísicas e fenologia de culturas a partir de imagens Sentinel-2 BOA, usando modelos pré-treinados de Regressão por Processos Gaussianos (GPR). Inclui pipeline automático com download direto do Google Earth Engine (GEE).\n\nBaseado na metodologia de:\nM. Salinero-Delgado et al. — GEEGPRPhenoDemos',
        'Estima LAI, Cab, Cw, Cm, FVC pixel a pixel': 'Estima LAI, Cab, Cw, Cm, FVC pixel a pixel',
        '2. Relleno Temporal GPR': '2. Gapfilling temporal GPR',
        'Rellena series temporales con cobertura nubosa': 'Preenche séries temporais com cobertura de nuvens',
        'SOS, EOS, POS, LOS via doble logistica': 'SOS, EOS, POS, LOS via dupla logística',
        'Descarga S2 + GPR + LSP en un solo paso': 'Baixa S2 + GPR + LSP em uma única etapa',

})
for _lang, _mapping in _EXTRA_TRANSLATIONS.items():
    _TRANSLATIONS.setdefault(_lang, {}).update(_mapping)

_PHRASE_TRANSLATIONS = {
    'en': [
        ('Prediccion', 'Prediction'), ('Predicción', 'Prediction'), ('Relleno Temporal', 'Temporal gapfilling'),
        ('Metricas', 'Metrics'), ('Métricas', 'Metrics'), ('Fenologia', 'Phenology'), ('Fenología', 'Phenology'),
        ('automatico', 'automatic'), ('Automatico', 'Automatic'), ('Descarga', 'Download'),
        ('imagenes', 'images'), ('imágenes', 'images'), ('variables biofisicas', 'biophysical variables'),
        ('variables biofísicas', 'biophysical variables'), ('pixel a pixel', 'pixel by pixel'),
        ('area', 'area'), ('Área', 'Area'), ('capa vectorial', 'vector layer'), ('mascara', 'mask'),
        ('nubes', 'clouds'), ('agua', 'water'), ('salida', 'output'), ('ráster', 'raster'), ('Ráster', 'Raster'),
        ('Carpeta', 'Folder'), ('Fecha', 'Date'), ('Tipo de cultivo', 'Crop type'),
        ('Cargar resultado como capa raster en QGIS', 'Load result as raster layer in QGIS'),
    ],
    'pt': [
        ('Prediccion', 'Predição'), ('Predicción', 'Predição'), ('Relleno Temporal', 'Preenchimento temporal'),
        ('Metricas', 'Métricas'), ('Fenologia', 'Fenologia'), ('Descarga', 'Download'),
        ('imagenes', 'imagens'), ('imágenes', 'imagens'), ('pixel a pixel', 'pixel a pixel'),
        ('capa vectorial', 'camada vetorial'), ('mascara', 'máscara'), ('nubes', 'nuvens'),
        ('agua', 'água'), ('salida', 'saída'), ('Carpeta', 'Pasta'), ('Fecha', 'Data'),
    ],
}


def tr(text):
    """Translate a user-visible string according to the selected language.

    Default language is English from v1.5.1. Spanish source strings are kept as
    canonical keys to preserve backward compatibility with the previous code.
    """
    lang = get_language()
    if lang == 'es':
        return text
    translated = _TRANSLATIONS.get(lang, {}).get(text)
    if translated is not None:
        return translated
    # Fallback phrase replacement for long Processing help texts and legacy UI
    out = text
    for src, dst in _PHRASE_TRANSLATIONS.get(lang, []):
        out = out.replace(src, dst)
    return out
