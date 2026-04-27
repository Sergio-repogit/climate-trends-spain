# Análisis de Tendencias Climáticas en España (2010-2025)

Este proyecto realiza un análisis avanzado de series temporales meteorológicas para detectar y cuantificar el cambio climático en España. Utilizando datos horarios de **50 estaciones meteorológicas**, el estudio aplica métodos estadísticos no paramétricos para identificar tendencias significativas, aceleraciones térmicas y cambios en eventos extremos.

---

## Descripción del Proyecto
Este proyecto implementa un pipeline completo de Big Data para el estudio del clima. El objetivo es detectar y cuantificar cambios en la temperatura durante el período **2010-2025** mediante técnicas estadísticas avanzadas y una metodología científica robusta basada en datos de alta resolución.

## Objetivos
* **Análisis de tendencias:** Detectar variaciones térmicas con corrección de autocorrelación.
* **Extremos térmicos:** Cuantificar cambios en eventos críticos (noches tropicales, calor/frío extremo).
* **Influencia geográfica:** Estudiar el efecto de la altitud y la proximidad al mar.
* **Variabilidad temporal:** Analizar diferencias estacionales y la aceleración del calentamiento.
* **Calidad de datos:** Garantizar resultados fiables mediante un control de calidad (QC) riguroso en 3 capas.

## Analisis Implementados
El proyecto incorpora metodologías avanzadas como:

1. **Control de Autocorrelación (Pre-Whitening)**
   * **Problema:** Las series climáticas presentan dependencia temporal que infla los falsos positivos en el test de Mann-Kendall.
   * **Solución:** Aplicación de *Trend-Free Pre-Whitening* (TFPW) antes del análisis.

2. **Downcasting y Optimización de Memoria**
   * **Contexto Big Data:** Gestión de ~5.4M de registros.
   * **Solución:** Optimización de tipos para procesamiento íntegro en RAM y persistencia en **Apache Parquet**.

3. **Separación Tmax / Tmin / Tmean**
   * **Justificación:** El calentamiento no es homogéneo; las temperaturas mínimas suelen aumentar a mayor ritmo que las máximas.

4. **Intervalos de Confianza (Bootstrap)**
   * **Solución:** Estimación de incertidumbre en la pendiente de Sen mediante remuestreo.

5. **Análisis de Extremos Térmicos**
   * **Métricas:** Noches tropicales ($T > 20^\circ\text{C}$), Calor extremo ($T > 35^\circ\text{C}$) y Frío extremo ($T < 0^\circ\text{C}$).

6. **Relación Altitud vs. Tendencia**
   * **Análisis:** Regresión lineal para validar si el calentamiento es más severo en cotas altas.

7. **Mapa de Calor de Completitud**
   * **Transparencia:** Visualización matriz estaciones × años para validar la robustez del dataset.

8. **Clasificación Costa/Interior**
   * **Análisis:** Uso de test de Mann-Whitney para comparar la regulación térmica marina.

9. **Análisis de Aceleración**
   * **Método:** Comparación de tendencias por subperíodos dentro del rango 2010-2025.

10. **Análisis de Percentiles (p10, p50, p90)**
    * **Justificación:** El cambio climático afecta más severamente a las colas de la distribución que a la media.

11. **Interpolación Condicionada**
    * **Solución:** Uso de Splines cúbicos y patrones históricos para el tratamiento de *missing values* sin romper el ciclo diario.

## Estaciones Meteorológicas
El proyecto analiza **50 estaciones** estratégicas obtenidas vía **Meteostat** (fuentes AEMET, NOAA, DWD), cubriendo:
* **Costa Cantábrica y Atlántica**
* **Meseta Norte y Sur**
* **Levante y Valle del Ebro**
* **Andalucía y Sistemas Montañosos**
* **Archipiélagos (Baleares)**

## Volumen de Datos
* **Registros totales:** 5.4 millones de registros horarios.
* **Formato:** Apache Parquet (compresión optimizada).
* **Variables:** 47 métricas estadísticas calculadas por estación.
* **Período:** 2010-2025.

## Autores
**Sergio Mínguez Cruces**
*Tutor: Álvaro Diez*

## Licencia
MIT License - Ver archivo LICENSE para más detalles.