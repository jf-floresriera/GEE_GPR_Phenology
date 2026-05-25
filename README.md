# 🛰 GEE GPR Phenology — QGIS Plugin

<div align="center">

![QGIS](https://img.shields.io/badge/QGIS-3.x-green?logo=qgis&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.8%2B-blue?logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-yellow)
![Status](https://img.shields.io/badge/Status-Active-brightgreen)

**Plugin de QGIS para estimación de variables biofísicas y fenología de cultivos**  
**a partir de imágenes Sentinel-2 usando Regresión por Procesos Gaussianos (GPR)**

[📦 Instalación](#-instalación) · [🚀 Uso rápido](#-uso-rápido) · [📐 Algoritmos](#-algoritmos) · [🌍 Pipeline GEE](#-pipeline-gee-automático) · [📬 Contacto](#-contacto)

</div>

---

## 📋 Descripción

**GEE GPR Phenology** es un plugin de QGIS que implementa en Python/NumPy la metodología GPR del repositorio [GEEGPRPhenoDemos](https://github.com/msalinero/GEEGPRPhenoDemos) (Salinero-Delgado et al.), adaptándola para trabajar directamente en el entorno de escritorio QGIS con imágenes locales **y** con descarga automatizada desde **Google Earth Engine (GEE)**.

### ¿Qué hace este plugin?

Dado un stack de imágenes Sentinel-2 BOA (10 bandas: B2, B3, B4, B5, B6, B7, B8, B8A, B11, B12), el plugin:

1. **Estima variables biofísicas** pixel a pixel mediante modelos GPR pre-entrenados
2. **Rellena lagunas temporales** en la serie causadas por cobertura nubosa (Gapfilling GPR)
3. **Extrae métricas fenológicas** (SOS, EOS, POS, LOS, etc.) ajustando una doble logística
4. **Automatiza todo el flujo** descargando imágenes directamente desde Google Earth Engine

### Variables biofísicas soportadas

| Variable | Descripción | Unidades |
|----------|-------------|---------|
| **LAI** | Leaf Area Index | m²/m² |
| **Cab** | Contenido de clorofila foliar | µg/cm² |
| **Cw** | Contenido de agua foliar | cm |
| **Cm** | Materia seca foliar | g/cm² |
| **FVC** | Fracción de Cobertura Vegetal | — |
| **laiCab** | LAI × Cab | g/m² |
| **laiCm** | LAI × Cm | g/m² |
| **laiCw** | LAI × Cw | g/m² |

---

## 🗂 Estructura del repositorio

```
GEEGPRPheno/
├── __init__.py                  # Entrada del plugin QGIS
├── plugin.py                    # Interfaz principal (QDialog con pestañas)
├── processing_provider.py       # Proveedor de algoritmos QGIS Processing
│
├── algo_spectral_prediction.py  # Algoritmo 1: Predicción Espectral GPR
├── algo_gapfilling.py           # Algoritmo 2: Gapfilling Temporal GPR
├── algo_lsp.py                  # Algoritmo 3: Métricas LSP (Fenología)
├── algo_gee_pipeline.py         # Algoritmo 4: Pipeline GEE Automático
│
├── gpr_algorithms.py            # Núcleo matemático GPR (NumPy puro)
├── s2boa_models.py              # Modelos GPR pre-entrenados (hiperparámetros)
├── installer.py                 # Instalador automático de dependencias
│
├── icon.png                     # Icono del plugin
├── icon.svg                     # Icono vectorial
├── metadata.txt                 # Metadatos QGIS Plugin Manager
└── requirements.txt             # Dependencias Python
```

---

## 📦 Instalación

### Opción 1 — Desde QGIS Plugin Manager (recomendado)

> *Próximamente disponible en el repositorio oficial de plugins QGIS*

### Opción 2 — Instalación manual

1. Descarga o clona este repositorio:
   ```bash
   git clone https://github.com/jf-floresriera/GEE_GPR_Phenology.git
   ```

2. Copia la carpeta `GEEGPRPheno` al directorio de plugins de QGIS:

   | Sistema | Ruta |
   |---------|------|
   | **Windows** | `C:\Users\<usuario>\AppData\Roaming\QGIS\QGIS3\profiles\default\python\plugins\` |
   | **Linux** | `~/.local/share/QGIS/QGIS3/profiles/default/python/plugins/` |
   | **macOS** | `~/Library/Application Support/QGIS/QGIS3/profiles/default/python/plugins/` |

3. En QGIS: **Complementos → Administrar e instalar complementos → Instalados** → activa `GEE GPR Phenology`

4. El instalador automático instalará las dependencias Python al activar el plugin por primera vez.

### Dependencias Python

```
numpy >= 1.21.0
scipy >= 1.7.0
rasterio >= 1.3.0
earthengine-api >= 0.1.370   # Solo requerido para el Algoritmo 4 (Pipeline GEE)
```

---

## 🚀 Uso rápido

Al activar el plugin aparece un **panel flotante** con 5 pestañas:

```
🌿 Espectral  |  🔁 Gapfilling  |  📈 LSP  |  🛰 GEE Auto  |  ℹ Info
```

Puedes usar los algoritmos de dos formas:
- **Desde el panel**: clic en "Abrir y ejecutar" en cada pestaña
- **Desde Processing Toolbox**: `GEE GPR Phenology` → selecciona el algoritmo

---

## 📐 Algoritmos

### 🌿 Algoritmo 1 — Predicción Espectral GPR

**Archivo:** `algo_spectral_prediction.py`  
**Equivalente:** Script 3 `GPRPredictedMean` de GEEGPRPhenoDemos

Aplica un modelo GPR pre-entrenado sobre las 10 bandas Sentinel-2 BOA para estimar variables biofísicas pixel a pixel.

**Matemática del kernel RBF espectral:**

```
k(x, x') = σ² · exp(-0.5 · Σ (xᵢ - x'ᵢ)² / ℓᵢ²)

predicción = k* · α + μ
```

Donde `α` son los coeficientes pre-calculados sobre el conjunto de entrenamiento y `μ` es el valor medio del modelo.

**Entradas:**

| Parámetro | Descripción |
|-----------|-------------|
| Ráster S2 BOA | Imagen con mínimo 10 bandas |
| Variable biofísica | LAI, Cab, Cw, Cm, FVC, laiCab, laiCm, laiCw |
| Bandas B2–B12 | Número de banda para cada longitud de onda |
| Factor de escala | 10000 para S2 L2A estándar |
| Máscara de nubes | Ráster binario opcional (1=válido, 0=nube) |

**Salida:** Ráster GeoTIFF float32 con la variable estimada

---

### 🔁 Algoritmo 2 — Gapfilling Temporal GPR

**Archivo:** `algo_gapfilling.py`  
**Equivalente:** Script 2 `GPRGapfilling` de GEEGPRPhenoDemos

Rellena lagunas temporales en la serie del índice biofísico causadas por cobertura nubosa, usando GPR con kernel RBF temporal.

**Kernel RBF temporal:**

```
K(tᵢ, tⱼ) = σ²_f · exp(-0.5 / ℓ²_ts · (tᵢ - tⱼ)²)

predicción(t*) = k*ᵀ · (K + σ²_n I)⁻¹ · y
```

Los hiperparámetros `(ℓ²_ts, σ²_f, σ²_n)` están **pre-calibrados por tipo de cultivo** para 10 especies (maíz, trigo, cebada, girasol, colza, guisante, alfalfa, remolacha, patata, media).

**Entradas:**

| Parámetro | Descripción |
|-----------|-------------|
| Carpeta de rásters | Archivos con formato `YYYY-MM-DD.tif` |
| Fecha objetivo | Fecha a interpolar/rellenar |
| Ventana temporal | ±días alrededor de la fecha objetivo |
| Variable biofísica | Para seleccionar el modelo correcto |
| Tipo de cultivo | Para los hiperparámetros GPR |

**Salida:** Ráster GeoTIFF float32 gapfilled para la fecha objetivo

---

### 📈 Algoritmo 3 — Métricas LSP (Fenología)

**Archivo:** `algo_lsp.py`  
**Equivalente:** Scripts 4 y 5 `LSPGeneration` + `PhenologyFunctions`

Ajusta una **doble logística** pixel a pixel sobre la serie temporal gapfilled para extraer métricas de fenología de temporada de cultivo.

**Función doble logística:**

```
y(t) = vmin + vamp · [1/(1+exp(-m₁(t-n₁))) - 1/(1+exp(-m₂(t-n₂)))]
```

**Métricas extraídas (12 bandas de salida):**

| Banda | Métrica | Descripción |
|-------|---------|-------------|
| 1 | **SOS** | Start of Season — inicio de temporada (DOY) |
| 2 | **EOS** | End of Season — fin de temporada (DOY) |
| 3 | **POS** | Peak of Season — máximo de la curva (DOY) |
| 4 | **LOS** | Length of Season — duración en días |
| 5 | **customSOS** | SOS con umbral relativo personalizado |
| 6 | **customEOS** | EOS con umbral relativo personalizado |
| 7 | **vmin** | Valor mínimo de la curva |
| 8 | **vmax** | Valor máximo de la curva |
| 9 | **n₁** | Parámetro de inflexión fase ascendente |
| 10 | **m₁** | Pendiente de la fase ascendente |
| 11 | **n₂** | Parámetro de inflexión fase descendente |
| 12 | **m₂** | Pendiente de la fase descendente |

**Requisito mínimo:** 6 imágenes en la serie temporal para ajustar la función.

---

## 🌍 Pipeline GEE Automático

**Archivo:** `algo_gee_pipeline.py`  
**Algoritmo 4** — Integra todos los pasos anteriores con descarga directa de Sentinel-2 desde Google Earth Engine.

### Flujo completo

```
AOI (capa QGIS) + Fechas cultivo + % Nubosidad
           ↓
[GEE] Filtrar S2 L2A COPERNICUS/S2_SR_HARMONIZED
           ↓ (máscara SCL)
[GEE] Descargar bandas B2–B12 (escala 10m, EPSG:4326)
           ↓
[GPR] Predicción espectral pixel a pixel
           ↓
[GPR] Gapfilling temporal ±ventana días
           ↓ (opcional)
[LSP] Doble logística → SOS, EOS, POS, LOS...
           ↓
Carpetas de salida GeoTIFF
```

### Parámetros

| Parámetro | Descripción |
|-----------|-------------|
| **Área de interés** | Capa vectorial del proyecto QGIS (dibujada o cargada) |
| **Fecha inicio cultivo** | `YYYY-MM-DD` — inicio de la temporada |
| **Fecha fin cultivo** | `YYYY-MM-DD` — fin de la temporada |
| **Nubosidad máxima** | Filtro CLOUDY_PIXEL_PERCENTAGE (0–100%) |
| **Variable biofísica** | LAI, Cab, Cw, Cm, FVC, laiCab, laiCm, laiCw |
| **Tipo de cultivo** | Para hiperparámetros GPR del gapfilling |
| **Ventana gapfilling** | ±días alrededor de cada fecha (default: 30) |
| **Umbral SOS/EOS** | Umbral relativo personalizado (0.0–1.0) |
| **Calcular LSP** | Activar/desactivar métricas fenológicas |
| **ID proyecto GEE** | Proyecto GEE (opcional, ej: `ee-miusuario`) |
| **Clave Service Account** | JSON para autenticación automatizada (opcional) |

### Carpetas de salida generadas

```
carpeta_salida/
├── 01_S2_raw/          → Imágenes S2 descargadas (YYYY-MM-DD_S2.tif)
├── 02_LAI_pred/        → Predicción GPR por fecha
├── 03_LAI_gapfilled/   → Serie gapfilled
└── 04_LAI_LSP/         → LSP_LAI.tif (12 bandas)
```

### Autenticación GEE

#### Opción 1 — Desde el menú del plugin (recomendado)
```
Complementos → GEE GPR Phenology → Autenticar Google Earth Engine
```

#### Opción 2 — Desde terminal
```bash
# Instalar API
pip install earthengine-api

# Autenticar (abre el navegador)
earthengine authenticate
```

#### Opción 3 — Desde Consola Python de QGIS
```python
import ee
ee.Authenticate(auth_mode='notebook')
ee.Initialize()
```

---

## 📁 Modelos GPR pre-entrenados

Los modelos están almacenados en `s2boa_models.py` como diccionarios NumPy. Cada modelo contiene:

| Componente | Descripción |
|------------|-------------|
| `Xtrain` | Conjunto de entrenamiento normalizado |
| `alpha_coefficients` | Coeficientes GPR pre-calculados |
| `mx`, `sx` | Media y desviación para normalización de bandas |
| `meanmodel` | Media del modelo (offset) |
| `hypell` | Longitudes de escala por banda |
| `hypsig` | Amplitud del kernel |
| `XDXprecalc` | Producto pre-calculado para eficiencia |
| `gf_hyperparams` | Hiperparámetros de gapfilling por cultivo |

Los modelos fueron entrenados sobre el dataset **ALEBD** (Salinero-Delgado et al.) con muestras del sensor Sentinel-2 en condiciones BOA (Bottom-Of-Atmosphere).

---

## 🔧 Desarrollo y contribuciones

### Estructura de clases principales

```python
GEEGPRPhenoPlugin          # plugin.py — clase principal QGIS
└── GEEPanelDialog         # Ventana flotante con pestañas

GEEGPRPhenoProvider        # processing_provider.py — proveedor Processing
├── GPRSpectralPredictionAlgorithm   # Algoritmo 1
├── GPRGapfillingAlgorithm           # Algoritmo 2
├── LSPGenerationAlgorithm           # Algoritmo 3
└── GEEAutoPipelineAlgorithm         # Algoritmo 4
```

### Agregar un nuevo algoritmo

1. Crea `algo_nuevo.py` heredando de `QgsProcessingAlgorithm`
2. Impleméntalo en `processing_provider.py`:
   ```python
   from .algo_nuevo import NuevoAlgoritmo
   self.addAlgorithm(NuevoAlgoritmo())
   ```
3. Agrega una pestaña en `plugin.py` → método `_build_ui()`

### Tests

```bash
# Verificar sintaxis de todos los archivos
python3 -m py_compile *.py

# Verificar imports (requiere QGIS en el PATH)
python3 -c "from gpr_algorithms import gpr_spectral_prediction; print('OK')"
```

---

## 📚 Referencias

Este plugin implementa la metodología de:

> **M. Salinero-Delgado et al.** — *Monitoring Biophysical Variables from Sentinel-2 Time Series using Gaussian Process Regression*  
> Repositorio original: [GEEGPRPhenoDemos](https://github.com/msalinero/GEEGPRPhenoDemos)

Para la teoría de GPR aplicada a teledetección:

- Rasmussen & Williams (2006) — *Gaussian Processes for Machine Learning*
- Camps-Valls et al. — *Kernel Methods for Remote Sensing Data Analysis*

---

## 📬 Contacto

<table>
<tr>
<td><b>Desarrollador</b></td>
<td>Jesús Enrique Flores Riera</td>
</tr>
<tr>
<td><b>Institución</b></td>
<td>Laboratorio 227 — Universidad Nacional de Colombia</td>
</tr>
<tr>
<td><b>Correo</b></td>
<td><a href="mailto:jfloresr@unal.edu.co">jfloresr@unal.edu.co</a></td>
</tr>
<tr>
<td><b>LinkedIn</b></td>
<td><a href="https://www.linkedin.com/in/flores-riera/">linkedin.com/in/flores-riera</a></td>
</tr>
<tr>
<td><b>Repositorio</b></td>
<td><a href="https://github.com/jf-floresriera/GEE_GPR_Phenology">github.com/jf-floresriera/GEE_GPR_Phenology</a></td>
</tr>
</table>

---

## 📄 Licencia

Este proyecto está bajo la licencia **MIT**. Ver el archivo [LICENSE](LICENSE) para más detalles.

---

<div align="center">

Desarrollado con ❤ en el **Laboratorio 227 — Universidad Nacional de Colombia**  
**Jesús Enrique Flores Riera** · 2025–2026

</div>
