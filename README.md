# Análisis de Datos Meteorológicos

> Proyecto final — Big Data · Grado en Matemáticas · UNIE Universidad

[![Tests](https://img.shields.io/badge/tests-28%20passed-brightgreen)](#)
[![Coverage](https://img.shields.io/badge/coverage-80%25-brightgreen)](#)
![Python](https://img.shields.io/badge/python-3.13-blue)
![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)
[![CI](https://github.com/Sergio-repogit/climate-trends-spain/actions/workflows/ci.yml/badge.svg)](https://github.com/Sergio-repogit/climate-trends-spain/actions/workflows/ci.yml)
[![Docs](https://github.com/Sergio-repogit/climate-trends-spain/actions/workflows/docs.yml/badge.svg)](https://sergio-repogit.github.io/climate-trends-spain/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://climate-trends-spain.streamlit.app)

---

## Description

Este proyecto realiza un análisis avanzado de series temporales meteorológicas para detectar y cuantificar el cambio climático en España durante el período **2010-2025**. Utilizando datos horarios de **50 estaciones meteorológicas**, el estudio aplica métodos estadísticos no paramétricos para identificar tendencias significativas, aceleraciones térmicas y cambios en eventos extremos.


## Documentation

Full documentation at **[sergio-repogit.github.io/climate-trends-spain/](https://sergio-repogit.github.io/climate-trends-spain/)**

## Installation

  ```bash
    git clone https://github.com/Sergio-repogit/climate-trends-spain.git
    cd climate-trends-spain
    pip install uv
    uv sync --group dev
  ```

## Ejecución del Pipeline

Para ejecutar el pipeline completo (Descarga -> Limpieza -> Análisis -> Visualización):

  ```bash
  python -m src.weather.main
  ```

## Comandos de Desarrollo

  ```bash
  python -m pytest                          # ejecutar tests
  python -m pytest --cov=src/weather -v     # tests con cobertura
  python -m ruff check .                    # linter
  python -m ruff format .                   # formateador
  ```

## Project Structure

  ```
proyecto-meteorologia/
├── src/weather/           # Código modular
│   ├── config.py          # Configuración + 26 estaciones
│   ├── data_loader.py     # Descarga + optimización tipos
│   ├── cleaning.py        # QC 3 capas + homogeneización
│   ├── analysis.py        # Mann-Kendall + pre-whitening
│   ├── viz.py             # Folium + matplotlib
│   └── main.py            # Orquestador pipeline
├── tests/                 # Tests unitarios (>70% cobertura)
│   ├── test_cleaning.py
│   ├── test_stats.py
|   ├── test_acceleration.py
|   ├── test_data_loader.py
|   ├── test_viz.py
├── docs/                  # Documentación MkDocs
│   ├── index.md
│   ├── analiisis.md
│   └── index.md
├── data/                  # Datos (excluidos de git)
│   ├── raw/
|       └── {station}.parquet
│   ├── processed/
|       ├── all_stations_clean.parquet
|       └── all_stations_enriched.parquet
│   └── results/
│       ├── maps/          # trend_map.html (Folium)
│       ├── figures/       # 6 visualizaciones PNG
|       ├── acceleration_trends.parquet
|       └── comprehensive_trends.parquet
├── streamlit_app/                  # Página streamlit
│   ├── pages/
│       ├── 1_Dashboard_General    
|       ├── 2_Tendencias_y_Aceleracion
│       ├── 3_Extremos_y_Percentiles    
|       ├── 4_Analisis_Estacional
│       ├── 5_Analisis_Espacial    
|       ├── 6_Calidad_y_Eficiencia_Big_Data
│       ├── 7_Metodologia_y_Matematicas   
|       └── 8_Descarga_Datos
├── pyproject.toml         # Dependencias 
├── mkdocs.yml             # Config documentación
├── LICENSE                # MIT License
└── README.md              # Este archivo
```
## Visualizaciones Generadas
 
1. **trend_map.html**: Mapa interactivo Folium con tendencias
2. **altitude_vs_trend.png**: Elevation-Dependent Warming (R² + p-value)
3. **completeness_heatmap.png**: Matriz estaciones×años (calidad datos)
4. **coastal_vs_inland.png**: Costa vs Interior (Mann-Whitney U)
5. **extreme_hours_trends.png**: Noches tropicales + calor/frío extremo
6. **seasonal_trends.png**: Tendencias por estación del año

## Methodology

El análisis se centra en la detección de tendencias no paramétricas:
* **Quality Control (QC):** Limpieza en 3 capas para detección de outliers, interpolación y homogeneización de series.
* **Mann-Kendall Test:** Para evaluar si hay una tendencia monótona ascendente o descendente.
* **Sen's Slope Estimator:** Para calcular la magnitud de dicha tendencia.
* **Pre-whitening:** Aplicado a las series para eliminar la autocorrelación serial antes del test de Mann-Kendall.

## Quality Control (QC) Process

Dada la naturaleza de los datos horarios, se aplica un pipeline de limpieza propio:
1.  **Physical Limits Check:** Validación de rangos climáticos extremos (temperaturas fuera de $[-30, 50]$ °C, valores nunca alcanzados en España).
2.  **Detección estadística estacionalizada (Z-score + IQR):** Para evitar falsos positivos (ej. identificar 40°C como outlier en invierno pero no en verano), se aplican métodos estadísticos sobre ventanas mensuales.
3.  **Consistencia temporal:** Detecta inconsistencias temporales (saltos bruscos y valores constantes).

## Data Source & Acquisition

El proyecto utiliza la librería [Meteostat](https://github.com/meteostat/meteostat-python), que agrega datos de fuentes oficiales (AEMET, NOAA, DWD).
* **Periodo:** 2010 – 2025 (proyección según disponibilidad).
* **Resolución:** Horaria (Hourly).
* **Estaciones:** 50 puntos geográficos seleccionados por su consistencia histórica.
* **Optimización:** Los datos se persisten en formato **Apache Parquet**, reduciendo el espacio en disco frente a CSV y optimizando los tipos de datos de forma aumtomática dentro del flujo del pipeline.
* **Vectorización:** Debido a la optimización la base se trabaja en RAM por lo que tecnicas como polars/dask no son tan optimas por lo que se trabajará con `NumPy` y `Pandas` para evitar bucles `for` en el cálculo de tendencias sobre los millones de registros horarios y así reducir más su consumo.

## Dashboard Interactivo

Se ha desarrollado una aplicación web multipágina con **Streamlit** para la exploración exhaustiva de los resultados. La interfaz permite democratizar el acceso a los datos complejos de Big Data:

* **Análisis Multidimensional:** Desde dashboards generales hasta análisis específicos de extremos, estacionalidad y geografía (altitud/costa e interior).
* **Métricas de Eficiencia:** Página dedicada a visualizar el impacto de la optimización de tipos y el rendimiento del procesamiento en RAM.
* **Transparencia Matemática:** Sección explicativa con la formulación de los tests estadísticos aplicados.

**Para ejecutar el dashboard localmente:**

```bash
# Si usas el entorno virtual directamente
./.venv/Scripts/streamlit run streamlit_app/Home.py

# O con uv 
uv run streamlit run streamlit_app/Home.py
```

## Uso de herramientas de IA

Durante el desarrollo de este proyecto se han utilizado herramientas de inteligencia artificial como apoyo puntual, principalmente para consultas específicas de implementación, resolución de errores y mejora de la eficiencia del código.

En concreto, se han empleado modelos de lenguaje Claude Sonnet 4.5 y Gemini 3.1 como asistentes para:
- Aclarar dudas sobre librerías y funciones concretas.
- Sugerir posibles enfoques de implementación.
- Ayudar en la depuración de errores puntuales.

El diseño del proyecto, la selección de metodologías, el desarrollo principal del código y la interpretación de los resultados han sido realizados de forma autónoma. Las herramientas de IA se han utilizado únicamente como soporte, de manera similar a la consulta de documentación técnica o foros especializados.

Se garantiza la comprensión completa de todo el código presentado, así como de las decisiones metodológicas adoptadas.

## Author

**Sergio Mínguez Cruces** · [github.com/Sergio-repogit](https://github.com/Sergio-repogit)

## Professor

**Álvaro Diez** · [github.com/alvarodiez20](https://github.com/alvarodiez20)





*Big Data · 4º Grado en Matemáticas · UNIE Universidad · 2025–2026*