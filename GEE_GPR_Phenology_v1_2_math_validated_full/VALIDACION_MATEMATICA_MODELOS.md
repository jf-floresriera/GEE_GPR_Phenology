# Validación matemática del núcleo GPR/LSP del plugin GEEGPRPheno

Versión revisada: **1.2.0-math-validated**  
Fecha de revisión: 2026-06-05

## 1. Objetivo de la revisión

Se revisó la equivalencia entre el flujo original en Google Earth Engine/JavaScript y la implementación Python/QGIS del plugin, con énfasis en:

1. Predicción espectral GPR pixel a pixel para LAI, Cab, Cw, Cm, FVC, laiCab, laiCm y laiCw.
2. Gapfilling temporal mediante GPR con kernel RBF.
3. Métricas fenológicas LSP mediante doble logística.
4. Manejo de escala Sentinel-2 BOA/L2A.
5. Robustez frente a nodata, nubes y series temporales incompletas.

## 2. Hallazgos críticos encontrados

### 2.1. Error en la función espectral GPR `k_star`

En el JavaScript original, la expresión es:

```javascript
k_star = exp(PtTDX - 0.5 * XDX_pre_calc)
```

En el plugin Python estaba implementada como:

```python
kstar = exp(0.5 * (PtTDX - XDXprecalc))
```

Esto aplica un factor `0.5` adicional a `PtTDX`, cambiando la forma del kernel y, por tanto, la predicción final. Se corrigió a:

```python
kstar = np.exp(PtTDX - 0.5 * xdx_vec[:, None])
```

### 2.2. Recorte superior incorrecto a 10

El código Python recortaba cualquier predicción mayor a 10:

```python
pred = np.where(pred > 10.0, 10.0, pred)
```

Ese recorte no existe en el JavaScript original y afecta gravemente variables como **Cab**, **laiCm** y **laiCw**, cuyos rangos pueden superar 10 por sus unidades. Se eliminó este recorte. Se mantiene únicamente la regla original del JavaScript:

```python
pred = np.where(pred < 0, 1e-5, pred)
```

### 2.3. Hiperparámetros temporales del gapfilling estaban en cero

En `s2boa_models.py`, los hiperparámetros `ell2ts`, `sigfts` y `signts` estaban en cero para todos los cultivos. Esto hacía que el kernel temporal fuese matemáticamente degenerado.

Se copiaron desde el archivo original `S2BOAModels.js` todos los hiperparámetros por:

- variable biofísica: LAI, Cab, Cm, Cw, FVC, laiCab, laiCm, laiCw;
- cultivo: maíz, trigo, cebada, girasol, colza, guisante, alfalfa, remolacha, patata y media.

### 2.4. Manejo de nodata en gapfilling demasiado restrictivo

El plugin exigía que un píxel fuera válido en **todas** las fechas de la ventana temporal. Esto era poco robusto porque en datos Sentinel-2 es normal que algunas fechas tengan nubes/nodata.

Se cambió la lógica para usar los píxeles con al menos dos observaciones válidas y agruparlos por patrón temporal de disponibilidad. Así, el GPR temporal usa únicamente las fechas válidas de cada píxel o grupo de píxeles.

### 2.5. Implementación LSP no suficientemente equivalente al JavaScript

La función inicial de LSP usaba mínimos/máximos simples y una doble logística simplificada. El JavaScript original usa:

- `intervalMean(95,100)` para `vmax`;
- `intervalMean(0,5)` para `vmin`;
- ventana DOY 60–304;
- búsqueda de `doymax`, `doyn1` y `doyn2`;
- regresión lineal de la primera sigmoide;
- corrección de la segunda sigmoide usando la primera.

Se reescribió `get_double_logistic_params()` para seguir más fielmente esa estructura.

## 3. Validaciones realizadas

Se agregó el script:

```bash
python tools/validate_math_equivalence.py
```

Este script no requiere QGIS y valida el núcleo matemático directamente con NumPy.

### 3.1. Predicción espectral GPR

Se comparó la función `gpr_spectral_prediction()` contra una transcripción independiente de la fórmula JavaScript. Resultado:

| Modelo | Error absoluto máximo |
|---|---:|
| LAI | 0.000e+00 |
| Cab | 0.000e+00 |
| Cm | 0.000e+00 |
| Cw | 0.000e+00 |
| FVC | 0.000e+00 |
| laiCab | 0.000e+00 |
| laiCm | 0.000e+00 |
| laiCw | 0.000e+00 |

### 3.2. Gapfilling temporal GPR

Se comparó `gpr_gapfilling_temporal()` contra una solución directa del sistema:

```python
alpha = solve(K + signts * I, y)
pred = k_star @ alpha
```

Resultado de prueba:

```text
expected=[1.6961195 2.5719554]
actual  =[1.6961195 2.5719554]
```

### 3.3. LSP / doble logística

Se aplicó una prueba sintética tipo curva fenológica. La función devuelve parámetros finitos y coherentes:

```text
n1=[110.87875 110.87875]
n2=[247.79846 247.79846]
pos=[190. 190.]
```

## 4. Archivos modificados

- `GEEGPRPheno/gpr_algorithms.py`
  - Corrección de `kstar` espectral.
  - Eliminación del recorte superior fijo a 10.
  - Reescritura robusta de `gpr_gapfilling_temporal()`.
  - Reescritura más fiel de `get_double_logistic_params()`.

- `GEEGPRPheno/s2boa_models.py`
  - Inclusión de hiperparámetros temporales originales del `.js`.
  - Actualización del test interno.

- `GEEGPRPheno/algo_gapfilling.py`
  - Manejo robusto de observaciones temporales incompletas.

- `GEEGPRPheno/algo_gee_pipeline.py`
  - Gapfilling robusto por patrones temporales de disponibilidad.
  - LSP con mínimo de 6 observaciones válidas por píxel.

- `GEEGPRPheno/algo_lsp.py`
  - LSP ahora acepta píxeles con al menos 6 observaciones válidas, no necesariamente todas las fechas.

- `tools/validate_math_equivalence.py`
  - Script de validación reproducible del núcleo matemático.

## 5. Estado actual de confianza

Después de esta corrección, la parte espectral GPR queda matemáticamente equivalente al JavaScript original en pruebas NumPy.

El gapfilling temporal queda corregido con los hiperparámetros originales y validado contra una solución directa del kernel RBF.

La parte LSP fue mejorada para seguir mucho más de cerca el JavaScript, pero se recomienda una validación final con datos reales: exportar desde GEE una pequeña AOI y comparar pixel a pixel contra el resultado del plugin para el mismo rango de fechas, misma máscara, misma colección y mismo índice.

## 6. Recomendación para validación final con datos reales

Para cerrar la validación científica del plugin se recomienda preparar un caso mínimo con:

1. Una AOI pequeña, por ejemplo una parcela o polígono de pocas hectáreas.
2. Un periodo corto con 6–12 imágenes Sentinel-2 L2A/BOA.
3. La misma máscara en GEE y QGIS.
4. Exportación de:
   - predicción espectral GPR;
   - imagen gapfilled;
   - métricas LSP.
5. Comparación raster pixel a pixel mediante RMSE, MAE, sesgo medio, correlación y mapa de diferencias.

Con esta prueba se puede documentar formalmente la equivalencia entre el plugin y el flujo original en `.js`.
