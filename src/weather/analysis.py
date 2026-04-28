"""
Módulo de análisis estadístico de tendencias climáticas.

Funciones principales:
    - calculate_derived_variables: Variables meteorológicas derivadas
    - prewhiten_series: Corrección de autocorrelación (TFPW)
    - mann_kendall_with_confidence: Test MK con IC bootstrap
    - analyze_trends_comprehensive: Análisis completo por estación
"""

import numpy as np
import pandas as pd
import pymannkendall as mk
from statsmodels.tsa.stattools import acf
from tqdm import tqdm

from .config import Config

# ============================================================================
# VARIABLES DERIVADAS
# ============================================================================


def calculate_derived_variables(df: pd.DataFrame, config: Config) -> pd.DataFrame:
    """
    Calcula variables meteorológicas derivadas.

    Variables generadas:
        - season: Estación del año
        - is_night: Clasificación día/noche
        - anomalia_termica: Desviación de la media histórica
        - heat_index: Índice de calor
        - is_tropical_night: Noche tropical (T>20°C nocturno)
        - is_extreme_heat: Calor extremo (T>35°C)
        - is_cold_extreme: Frío extremo (T<0°C)

    Args:
        df: DataFrame con datos limpios
        config: Configuración

    Returns:
        DataFrame enriquecido con variables derivadas
    """
    print("\n" + "=" * 70)
    print("CALCULANDO VARIABLES DERIVADAS")
    print("=" * 70)

    df_derived = df.copy()
    df_derived["timestamp"] = pd.to_datetime(df_derived["timestamp"])

    # Estación del año
    def get_season(month):
        if month in [12, 1, 2]:
            return "Invierno"
        elif month in [3, 4, 5]:
            return "Primavera"
        elif month in [6, 7, 8]:
            return "Verano"
        else:
            return "Otoño"

    df_derived["season"] = df_derived["timestamp"].dt.month.map(get_season)

    # Clasificación día/noche (20:00-08:00 = noche)
    hour = df_derived["timestamp"].dt.hour
    df_derived["is_night"] = ((hour >= 20) | (hour < 8)).astype(int)

    # Anomalía térmica (respecto a media histórica mes-hora)
    if "temp" in df_derived.columns:
        df_derived["month"] = df_derived["timestamp"].dt.month
        df_derived["hour"] = df_derived["timestamp"].dt.hour

        historical_means = df_derived.groupby(["station_id", "month", "hour"])[
            "temp"
        ].transform("mean")
        df_derived["anomalia_termica"] = df_derived["temp"] - historical_means

        df_derived.drop(["month", "hour"], axis=1, inplace=True)

    # Heat Index (sensación térmica con humedad)
    if "temp" in df_derived.columns and "rhum" in df_derived.columns:
        T = df_derived["temp"]
        RH = df_derived["rhum"]

        # Convertir a Fahrenheit
        T_F = T * 9 / 5 + 32

        # Fórmula de Rothfusz
        HI_F = (
            -42.379
            + 2.04901523 * T_F
            + 10.14333127 * RH
            - 0.22475541 * T_F * RH
            - 0.00683783 * T_F * T_F
            - 0.05481717 * RH * RH
            + 0.00122874 * T_F * T_F * RH
            + 0.00085282 * T_F * RH * RH
            - 0.00000199 * T_F * T_F * RH * RH
        )

        # Convertir a Celsius
        heat_index_C = (HI_F - 32) * 5 / 9

        # Solo usar heat index si T > 27°C
        df_derived["heat_index"] = np.where(T > 27, heat_index_C, T)

    # EXTREMOS TÉRMICOS
    print("  Calculando extremos térmicos...")

    if "temp" in df_derived.columns:
        # Noches tropicales (T>20°C durante la noche)
        df_derived["is_tropical_night"] = (
            (df_derived["is_night"] == 1)
            & (df_derived["temp"] > config.TROPICAL_NIGHT_THRESHOLD)
        ).astype(int)

        # Calor extremo (T>35°C)
        df_derived["is_extreme_heat"] = (
            df_derived["temp"] > config.EXTREME_HEAT_THRESHOLD
        ).astype(int)

        # Frío extremo (T<0°C)
        df_derived["is_cold_extreme"] = (
            df_derived["temp"] < config.COLD_EXTREME_THRESHOLD
        ).astype(int)

    print(" Variables derivadas calculadas")
    print("    - season, is_night, anomalia_termica, heat_index")
    print("    - Extremos: noches tropicales, calor extremo, frío extremo")

    return df_derived


# ============================================================================
# PRE-WHITENING (CORRECCIÓN DE AUTOCORRELACIÓN)
# ============================================================================


def prewhiten_series(series: pd.Series) -> tuple[pd.Series, float]:
    """
    Aplica Trend-Free Pre-Whitening (TFPW) para corregir autocorrelación.

    Metodología:
        1. Estimar y remover tendencia lineal
        2. Calcular autocorrelación lag-1 (p)
        3. Aplicar AR(1): x'_t = x_t - p·x_{t-1}
        4. Restaurar tendencia

    Args:
        series: Serie temporal (típicamente medias anuales)

    Returns:
        Tupla (serie_prewhitened, autocorrelación_lag1)

    """
    clean_series = series.dropna()

    if len(clean_series) < 10:
        return clean_series, 0.0

    # Paso 1: Estimar tendencia lineal
    x = np.arange(len(clean_series))
    y = clean_series.values

    # Regresión lineal
    slope, intercept = np.polyfit(x, y, 1)
    trend = slope * x + intercept

    # Remover tendencia
    detrended = y - trend

    # Paso 2: Calcular autocorrelación lag-1
    acf_values = acf(detrended, nlags=1, fft=False)
    rho = acf_values[1]  # lag-1

    # Paso 3: Pre-whitening AR(1)
    if abs(rho) > 0.1:  # Solo si autocorrelación significativa
        # x'_t = x_t - ρ·x_{t-1}
        prewhitened = detrended[1:] - rho * detrended[:-1]

        # Restaurar tendencia
        prewhitened_with_trend = prewhitened + trend[1:]

        return pd.Series(prewhitened_with_trend, index=clean_series.index[1:]), rho
    else:
        return clean_series, rho


# ============================================================================
# MANN-KENDALL CON INTERVALOS DE CONFIANZA
# ============================================================================


def mann_kendall_with_confidence(
    series: pd.Series, confidence_level: float = 0.95
) -> dict:
    """
    Test de Mann-Kendall con pre-whitening e intervalos de confianza.

    Mejoras respecto a MK estándar:
        1. Pre-whitening para corregir autocorrelación
        2. Intervalos de confianza bootstrap para Sen's slope
        3. Reporte de autocorrelación detectada

    Args:
        series: Serie temporal
        confidence_level: Nivel de confianza (default 0.95)

    Returns:
        Diccionario con resultados:
            - trend: 'increasing', 'decreasing', 'no trend'
            - p_value: Significancia estadística
            - sens_slope: Pendiente Sen (valor/año)
            - sens_slope_per_decade: Pendiente Sen (valor/década)
            - slope_lower_ci, slope_upper_ci: Intervalos de confianza
            - autocorrelation_lag1: Autocorrelación detectada
            - n_years: Longitud de la serie
    """
    # Pre-whitening
    prewhitened_series, rho = prewhiten_series(series)

    clean_series = prewhitened_series.dropna()

    if len(clean_series) < 3:
        return {
            "trend": "insufficient data",
            "p_value": np.nan,
            "z_score": np.nan,
            "tau": np.nan,
            "sens_slope": np.nan,
            "sens_slope_per_decade": np.nan,
            "slope_lower_ci": np.nan,
            "slope_upper_ci": np.nan,
            "autocorrelation_lag1": np.nan,
            "n_years": len(clean_series),
        }

    try:
        # Test de Mann-Kendall
        result = mk.original_test(clean_series)

        # Sen's slope
        slope = result.slope
        slope_per_decade = slope * 10 if slope is not None else np.nan

        # Obtener tau
        tau_value = getattr(result, "tau", np.nan)  # Default a NaN si no existe

        # Intervalo de confianza bootstrap
        n = len(clean_series)
        all_slopes = []

        # Calcular TODAS las pendientes entre pares de puntos
        for i in range(n):
            for j in range(i + 1, n):
                if clean_series.index[j] != clean_series.index[i]:
                    s = (clean_series.iloc[j] - clean_series.iloc[i]) / (j - i)
                    all_slopes.append(s)

        if len(all_slopes) > 0:
            all_slopes = np.array(all_slopes)
            alpha = 1 - confidence_level

            # Percentiles para IC
            lower_ci = np.percentile(all_slopes, alpha / 2 * 100) * 10
            upper_ci = np.percentile(all_slopes, (1 - alpha / 2) * 100) * 10
        else:
            lower_ci = np.nan
            upper_ci = np.nan

        return {
            "trend": result.trend,
            "p_value": result.p,
            "z_score": result.z,
            "tau": tau_value,
            "sens_slope": slope,
            "sens_slope_per_decade": slope_per_decade,
            "slope_lower_ci": lower_ci,
            "slope_upper_ci": upper_ci,
            "autocorrelation_lag1": rho,
            "n_years": len(clean_series),
        }
    except Exception as e:
        print(f"Error en Mann-Kendall: {e}")
        return {
            "trend": "error",
            "p_value": np.nan,
            "z_score": np.nan,
            "tau": np.nan,
            "sens_slope": np.nan,
            "sens_slope_per_decade": np.nan,
            "slope_lower_ci": np.nan,
            "slope_upper_ci": np.nan,
            "autocorrelation_lag1": np.nan,
            "n_years": len(clean_series),
        }


# ============================================================================
# CÁLCULOS ANUALES
# ============================================================================


def calculate_annual_stats(
    df: pd.DataFrame, station_id: str, temp_var: str
) -> pd.Series:
    """
    Calcula estadísticas anuales para análisis de tendencias.

    Args:
        df: DataFrame completo
        station_id: ID de la estación
        temp_var: 'temp', 'tmax', 'tmin', 'tavg'

    Returns:
        Serie temporal con medias anuales
    """
    station_df = df[df["station_id"] == station_id].copy()
    station_df["timestamp"] = pd.to_datetime(station_df["timestamp"])
    station_df.set_index("timestamp", inplace=True)

    annual_means = station_df[temp_var].resample("YE").mean()

    return annual_means


def calculate_extreme_hours_annual(
    df: pd.DataFrame, station_id: str, extreme_type: str
) -> pd.Series:
    """
    Calcula horas anuales de extremos térmicos.

    Args:
        df: DataFrame completo
        station_id: ID de la estación
        extreme_type: 'tropical_night', 'extreme_heat', 'cold_extreme'

    Returns:
        Serie con conteo anual de horas
    """
    station_df = df[df["station_id"] == station_id].copy()
    station_df["timestamp"] = pd.to_datetime(station_df["timestamp"])
    station_df["year"] = station_df["timestamp"].dt.year

    col_map = {
        "tropical_night": "is_tropical_night",
        "extreme_heat": "is_extreme_heat",
        "cold_extreme": "is_cold_extreme",
    }

    col = col_map[extreme_type]

    # Contar horas por año
    annual_counts = station_df.groupby("year")[col].sum()

    return annual_counts


def calculate_percentiles_annual(df: pd.DataFrame, station_id: str) -> pd.DataFrame:
    """
    Calcula percentiles anuales de temperatura.

    Justificación: El cambio climático afecta más a extremos que a medias.
    p90 detecta cambios en la cola superior de la distribución.

    Args:
        df: DataFrame completo
        station_id: ID de la estación

    Returns:
        DataFrame con percentiles anuales (p10, p25, p50, p75, p90)
    """
    station_df = df[df["station_id"] == station_id].copy()
    station_df["timestamp"] = pd.to_datetime(station_df["timestamp"])
    station_df["year"] = station_df["timestamp"].dt.year

    percentiles = station_df.groupby("year")["temp"].agg(
        [
            ("p10", lambda x: x.quantile(0.10)),
            ("p25", lambda x: x.quantile(0.25)),
            ("p50", lambda x: x.quantile(0.50)),
            ("p75", lambda x: x.quantile(0.75)),
            ("p90", lambda x: x.quantile(0.90)),
        ]
    )

    return percentiles


# ============================================================================
# ANÁLISIS COMPLETO
# ============================================================================


def analyze_trends_comprehensive(df: pd.DataFrame, config: Config) -> pd.DataFrame:
    """
    Análisis completo de tendencias con todas las mejoras científicas.

    Incluye:
        1. Tmax/Tmin/Tmean separados
        2. Corrección de autocorrelación (pre-whitening)
        3. Intervalos de confianza bootstrap
        4. Extremos térmicos (noches tropicales, calor/frío extremo)
        5. Percentiles (p90)

    Args:
        df: DataFrame con datos enriquecidos
        config: Configuración

    Returns:
        DataFrame con resultados de tendencias (47 columnas)
    """
    print("\n" + "=" * 70)
    print("ANÁLISIS DE TENDENCIAS COMPLETO")
    print("=" * 70)

    results_list = []

    for station_id in tqdm(df["station_id"].unique(), desc="Analizando estaciones"):
        station_data = df[df["station_id"] == station_id].iloc[0]

        result_row = {
            "station_id": station_id,
            "region": station_data["region"],
            "latitud": station_data["latitud"],
            "longitud": station_data["longitud"],
            "altitud": station_data["altitud"],
            "tipo_entorno": station_data["tipo_entorno"],
            "distancia_costa": station_data["distancia_costa"],
        }

        # Análisis para Tmax, Tmin, Tavg separados
        for temp_var in ["tmax", "tmin", "tavg"]:
            if temp_var in df.columns:
                annual = calculate_annual_stats(df, station_id, temp_var)
                mk_result = mann_kendall_with_confidence(
                    annual, config.CONFIDENCE_LEVEL
                )

                prefix = temp_var
                result_row[f"{prefix}_slope"] = mk_result["sens_slope_per_decade"]
                result_row[f"{prefix}_p_value"] = mk_result["p_value"]
                result_row[f"{prefix}_lower_ci"] = mk_result["slope_lower_ci"]
                result_row[f"{prefix}_upper_ci"] = mk_result["slope_upper_ci"]
                result_row[f"{prefix}_autocorr"] = mk_result["autocorrelation_lag1"]

        # Extremos térmicos
        for extreme_type in ["tropical_night", "extreme_heat", "cold_extreme"]:
            extreme_annual = calculate_extreme_hours_annual(
                df, station_id, extreme_type
            )
            mk_extreme = mann_kendall_with_confidence(
                extreme_annual, config.CONFIDENCE_LEVEL
            )

            result_row[f"{extreme_type}_slope"] = mk_extreme["sens_slope_per_decade"]
            result_row[f"{extreme_type}_p_value"] = mk_extreme["p_value"]

        # Percentiles (p90 para extremos de calor)
        percentiles_df = calculate_percentiles_annual(df, station_id)
        if len(percentiles_df) > 0:
            p90_mk = mann_kendall_with_confidence(
                percentiles_df["p90"], config.CONFIDENCE_LEVEL
            )
            result_row["p90_slope"] = p90_mk["sens_slope_per_decade"]
            result_row["p90_p_value"] = p90_mk["p_value"]

        results_list.append(result_row)

    results_df = pd.DataFrame(results_list)

    # Asegurar que el directorio existe antes de guardar
    config.RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    # Guardar resultados
    results_path = config.RESULTS_DIR / "comprehensive_trends.parquet"
    results_df.to_parquet(results_path, index=False)

    results_json = config.RESULTS_DIR / "comprehensive_trends.json"
    results_df.to_json(results_json, orient="records", indent=2)

    print(f"\n Análisis completado para {len(results_df)} estaciones")
    print(f"Resultados guardados en: {results_path}")

    return results_df


# ============================================================================
# ANÁLISIS DE ACELERACIÓN
# ============================================================================


def analyze_trends_acceleration(df: pd.DataFrame, config: Config) -> pd.DataFrame:
    """
    Analiza la aceleración del cambio climático comparando tendencias en subperiodos.

    Calcula el Mann-Kendall para cada subperiodo definido en config.SUBPERIODS.

    Args:
        df: DataFrame enriquecido
        config: Configuración

    Returns:
        DataFrame con tendencias por subperiodo y estación
    """
    print("\n" + "=" * 70)
    print("ANALIZANDO ACELERACIÓN POR SUBPERIODOS")
    print("=" * 70)

    results_acc = []
    stations = df["station_id"].unique()

    for start, end, label in tqdm(config.SUBPERIODS, desc="Procesando subperiodos"):
        # Filtrar datos del subperiodo
        mask = (df["timestamp"] >= start) & (df["timestamp"] <= end)
        sub_df = df[mask].copy()

        if sub_df.empty:
            continue

        for station_id in stations:
            station_sub = sub_df[sub_df["station_id"] == station_id]
            if station_sub.empty:
                continue

            res_row = {"station_id": station_id, "periodo": label}

            # Analizar Tmax, Tmin y Tavg
            for temp_var in ["tmax", "tmin", "tavg"]:
                if temp_var in station_sub.columns:
                    annual = calculate_annual_stats(station_sub, station_id, temp_var)
                    if len(annual) >= 3:
                        mk = mann_kendall_with_confidence(
                            annual, config.CONFIDENCE_LEVEL
                        )
                        res_row[f"{temp_var}_slope"] = mk["sens_slope_per_decade"]
                        res_row[f"{temp_var}_p_value"] = mk["p_value"]
                    else:
                        res_row[f"{temp_var}_slope"] = np.nan
                        res_row[f"{temp_var}_p_value"] = np.nan

            results_acc.append(res_row)

    results_df = pd.DataFrame(results_acc)

    # Asegurar que el directorio existe antes de guardar
    config.RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    # Guardar resultados
    acc_path = config.RESULTS_DIR / "acceleration_trends.parquet"
    results_df.to_parquet(acc_path, index=False)

    acc_json = config.RESULTS_DIR / "acceleration_trends.json"
    results_df.to_json(acc_json, orient="records", indent=2)

    print(f"\n Análisis de aceleración guardado en: {acc_path}")

    return results_df
