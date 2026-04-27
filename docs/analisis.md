# Análisis de Tendencias Climáticas en España (2010-2025)

## 1. Análisis: Introducción y Objetivos
El presente estudio tiene como propósito cuantificar y diagnosticar la evolución de las temperaturas en España durante los últimos 15 años. Utilizando una red de 51 estaciones meteorológicas (una por provincia), se busca identificar no solo el calentamiento medio, sino la alteración en la frecuencia de eventos extremos (noches tropicales y olas de calor).

El dataset comprende más de **5.4 millones de registros horarios**, lo que permite un análisis de alta resolución temporal capaz de capturar fenómenos que las medias diarias suelen ocultar, como la persistencia del calor nocturno.

---

## 2. Carga y Limpieza de Datos: El Pipeline de Calidad

### Stack Técnico
- **Lenguaje:** Python 3.13.
- **Extracción:** API Meteostat (Librería Python `meteostat` v1.6+).
- **Almacenamiento:** Formato Apache Parquet con compresión Snappy y tipos de datos optimizados para eficiencia en RAM.
- **Procesamiento:** Pandas, NumPy y SciPy.

### Desafíos y Soluciones Matemáticas
La limpieza de datos crudos de estaciones meteorológicas presenta retos estructurales que se abordaron mediante un pipeline de **cuatro capas**:

1.  **Filtros Físicos:** Se eliminaron registros fuera de rangos termodinámicamente posibles en España (ej. **$>50^\circ C$ o $<35^\circ C$**).
2.  **Detección Estadística Estacionalizada (Z-Score + IQR):**
    Para diferenciar picos de calor reales de errores de sensor, se aplicó una doble técnica:
    - **IQR (Rango Intercuartílico):** Proporciona una detección robusta basada en la dispersión de los datos.
    - **Z-Score estacionalizado:** Compara cada hora (ej. cada "julio a las 15:00") solo contra su mismo grupo histórico del periodo 2010-2025.
3.  **Consistencia Temporal:**
    Se detectan **saltos bruscos** de temperatura (variaciones superiores a **$5^\circ C$ en una sola hora**) y valores constantes "bloqueados" (sensores que marcan lo mismo durante **24 horas seguidas**), marcándolos como fallos de instrumentación.
4.  **Gestión de Gaps (Interpolación):**
    ```python
    # Fragmento de lógica de interpolación avanzada (cleaning.py)
    if gap_length <= 6:
        # Spline cúbico para preservar el ciclo diario
        spline = UnivariateSpline(x_valid, y_valid, k=3, s=0)
        series_filled.loc[gap_group.index] = spline(x_gap)
    else:
        # Interpolación condicionada por patrón horario histórico
        filled_values = hourly_pattern.loc[gap_indices] + trend_anomaly.loc[gap_indices]
    ```

### Homogeneización (Test de Pettitt)
Como paso final, se implementó el **Test de Pettitt** para detectar cambios estructurales (saltos bruscos) que pudieran indicar un cambio de ubicación de la estación o del sensor, garantizando la integridad de la serie histórica frente a factores externos.

---

## 3. Metodología Estadística Avanzada

Para garantizar que las tendencias detectadas no son producto del azar, se han aplicado tres pilares de análisis robusto:

### A. Estimador de Pendiente de Sen (Sen's Slope)
A diferencia de la regresión lineal tradicional, el estimador de Sen es **no paramétrico**. Calcula la mediana de todas las pendientes posibles entre pares de puntos, lo que lo hace inmune a valores atípicos (outliers).

### B. Test de Mann-Kendall con TFPW
Las series climáticas tienen "memoria" (autocorrelación). Hemos aplicado el método **Trend-Free Pre-Whitening (TFPW)** para limpiar la serie de su dependencia interna antes de pasar el test. Si el **P-Value** es < 0.05, confirmamos que la tendencia es real y no ruido estadístico.

### C. Bootstrap e Intervalos de Confianza
Se han realizado **1.000 simulaciones de remuestreo (Bootstrap)** para cada estación. Esto nos permite asignar un intervalo de confianza al 95% a cada pendiente, aportando el rigor necesario para publicaciones científicas.

### D. Análisis de Indicadores de Impacto (Extremos)
El análisis no se limita a la temperatura media, máxima y mínima, sino que monitoriza la evolución de los umbrales críticos:
- **Noches Tropicales ($> 20^\circ C$):** Tendencia en el número de horas anuales con estrés térmico nocturno.
- **Calor y Frío Extremo:** Evolución de las horas por encima de **$35^\circ C$** y por debajo de **$0^\circ C$**.
- **Percentiles Dinámicos (P10 y P90):** Mientras que la media indica el cambio general, los percentiles detectan si los extremos se están volviendo más severos, independientemente de la media.

---

## 4. Análisis Exploratorio (EDA) e Interpretación

### A. Integridad del Dataset
![Heatmap de Completitud](file:///c:/Users/ergio/Desktop/programacion/big_data/repos/climate-trends-spain/data/results/figures/completeness_heatmap.png)
*Interpretación:* El gráfico muestra una alta densidad de datos (>95%) en la mayoría de las provincias tras la fase de interpolación. Las zonas con ligeros gaps corresponden a estaciones con fallos técnicos intermitentes que han sido tratados mediante medias mensuales para no sesgar la tendencia.

### B. Evolución de Extremos Térmicos
![Tendencia de Horas de Extremos](file:///c:/Users/ergio/Desktop/programacion/big_data/repos/climate-trends-spain/data/results/figures/extreme_hours_trends.png)
*Interpretación:* Se observa un crecimiento asimétrico. Las **Noches Tropicales** (mínimas $> 20^\circ C$) crecen a un ritmo superior que las máximas extremas. Esto sugiere que el calentamiento en España es un fenómeno predominantemente nocturno, reduciendo la capacidad de recuperación térmica de los ecosistemas y las ciudades.

### C. Aceleración por Subperiodos
![Comparativa de Aceleración](file:///c:/Users/ergio/Desktop/programacion/big_data/repos/climate-trends-spain/data/results/figures/acceleration_comparison.png)
*Interpretación:* Al comparar el periodo 2010-2017 frente al 2018-2025, se detecta un fenómeno de "valle-pico". Muchas estaciones muestran una aceleración en la pendiente de calentamiento en el segundo subperiodo, lo que indica que el cambio climático no solo es lineal, sino que presenta impulsos de aceleración reciente.

### D. Distribución Estacional (Invierno vs Verano)
![Tendencias Estacionales](file:///c:/Users/ergio/Desktop/programacion/big_data/repos/climate-trends-spain/data/results/figures/seasonal_trends.png)
*Interpretación:* El análisis revela una asimetría crítica: el **Verano** se calienta a un ritmo de **$+0.85^\circ C/década$**, mientras que el **Invierno** lo hace a **$+0.35^\circ C/década$**. Esto implica que los veranos se están "estirando" cronológicamente.

### E. Factor Altitud y Geografía
![Tendencia vs Altitud](file:///c:/Users/ergio/Desktop/programacion/big_data/repos/climate-trends-spain/data/results/figures/altitude_vs_trend.png)
*Interpretación:* Aunque el calentamiento es generalizado, las estaciones de media y alta montaña muestran una dispersión mayor, lo que sugiere una respuesta climática más compleja y variable según la orografía local.

![Costa vs Interior](file:///c:/Users/ergio/Desktop/programacion/big_data/repos/climate-trends-spain/data/results/figures/coastal_vs_inland.png)
*Interpretación:* Las estaciones de **Costa** presentan un calentamiento más homogéneo debido a la inercia térmica marina, mientras que el **Interior** peninsular registra los picos de calentamiento más extremos.

> [!TIP]
> **Análisis Interactivo:** Mientras que estas imágenes ofrecen una visión general, la **Aplicación Streamlit** integrada permite filtrar por estaciones individuales, regiones o tipos de entorno para obtener gráficas personalizadas de alta resolución en tiempo real.

---
## 5. Resultados y Métricas Clave
### A. Evolución Térmica Diferencial (T. Máx vs T. Mín)
El análisis revela que las temperaturas máximas están subiendo a un ritmo ligeramente superior, aunque las mínimas presentan una mayor consistencia geográfica.

| Variable | Tendencia Promedio | Significancia (P < 0.05) |
| :--- | :--- | :--- |
| **Temperatura Máxima** | **$+0.67 ^\circ C/década$** | 33% de estaciones |
| **Temperatura Mínima** | **$+0.55 ^\circ C/década$** | 29% de estaciones |
| **Temperatura Media** | **$+0.61 ^\circ C/década$** | 31% de estaciones |

### B. Indicadores de Extremos (Impacto Real)
Donde el cambio climático muestra su cara más agresiva es en los indicadores de umbral:

- **Noches Tropicales ($>20^\circ C$):** Es el indicador con mayor significancia estadística (**53% de las estaciones** muestran una tendencia clara). En promedio, España gana **25.8 horas de calor nocturno al año**.
- **Calor Extremo ($>35^\circ C$):** Incremento de **5.4 horas/año**, concentrado principalmente en el valle del Guadalquivir y el Ebro.
- **Frío Extremo ($<0^\circ C$):** Descenso de **1.8 horas de helada al año**. Aunque la significancia es menor (12%), es una tendencia constante en la Meseta Norte.

### C. Factor Estacional: La Asimetría del Calentamiento
El calentamiento en España no es uniforme a lo largo del año. Al analizar los datos por estaciones climáticas, observamos:

1.  **Verano (Récord):** Registra la pendiente más alta (**$+0.85 ^\circ C/década$**), impulsada por olas de calor más frecuentes y duraderas.
2.  **Primavera:** Segunda estación con mayor calentamiento, lo que provoca un adelantamiento del ciclo vegetativo.
3.  **Invierno y Otoño:** Muestran tendencias más moderadas (**$+0.35 ^\circ C/década$**), pero con una variabilidad mucho mayor (p-valores > 0.05 en la mayoría de casos).

### D. Top 5 Estaciones con Mayor Calentamiento (T. Media)
Aunque el calentamiento es general, estas cinco estaciones lideran el ranking nacional por su alta tasa de subida y significancia estadística:

| Estación  | Pendiente ($\circ C/década$) | P-Value (Confianza) |
| :---  :--- | :--- |
| **Albacete** | **1.17** | 0.0079 (Muy Alta) |
| **Valencia** | **1.02** | 0.01 (Alta) |
| **Almeria** | **0.96** | 0.0015 (Muy Alta) |
| **Barcelona** | **0.8** | 0.003 (Muy Alta) |
| **Málaga** | **0.76** | 0.01 (Alta) |

---

## 6. Conclusiones y Arquitectura Big Data

### Síntesis de Inteligencia Climática
1.  **Huella de Extremos:** Las **Noches Tropicales** han pasado de ser eventos ocasionales a una tendencia estadística robusta en más de la mitad del territorio nacional.
2.  **Asimetría Estacional:** España se enfrenta a un calentamiento "a dos velocidades". El **Verano** y el **Invierno**se calienta a más velocidad que la **Primavera** y el **Otoño**, lo que está alterando los ciclos biológicos y agrícolas.
3.  **Efecto Isla de Calor:** El análisis confirma que las capitales de provincia sufren un calentamiento nocturno superior a laszonas rurales, evidenciando la necesidad de políticas de urbanismo climático.

- **Eficiencia de Almacenamiento:** Mediante la optimización de tipos y el uso de almacenamiento columnar (**Parquet + Snappy**), el sistema procesa 5.4M de registros con un consumo de RAM inferior a **1 GB**.
- **Modularidad y Testing:** El código está diseñado como un paquete profesional, con una cobertura de tests del **80%** que garantiza la fiabilidad de cada cálculo estadístico.
- **Reproducibilidad:** Gracias al uso de `uv` y `pyproject.toml`, el entorno es 100% replicable en cualquier sistema con **Python 3.13**.

### Visión de Futuro
Este pipeline no es un análisis estático; es una infraestructura escalable. El sistema está preparado para integrar datos y modelos de **Machine Learning (LSTM)** para predecir tendencias futuras, convirtiéndose en una herramienta de decisión estratégica ante la crisis climática.

---

**Autor: Sergio Minguez Cruces**
