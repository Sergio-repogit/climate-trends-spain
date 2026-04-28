"""
Módulo de control de calidad y limpieza de datos meteorológicos.

Implementa un pipeline de 3 capas para garantizar calidad de datos:
    1. Filtros físicos (hard limits)
    2. Detección estadística estacionalizada (IQR + Z-score)
    3. Consistencia temporal (saltos bruscos, valores constantes)

Además incluye:
    - Interpolación spline para gaps cortos
    - Interpolación condicionada para gaps largos
    - Test de Pettitt para homogeneización (detectar cambios de emplazamiento)
"""

import numpy as np
import pandas as pd
from scipy.interpolate import UnivariateSpline
from tqdm import tqdm

from .config import Config

# ============================================================================
# CAPA 1: FILTROS FÍSICOS
# ============================================================================


def apply_physical_limits(df: pd.DataFrame, config: Config) -> pd.DataFrame:
    """
    Aplica filtros de rango físico (hard limits).

    Elimina valores físicamente imposibles en el contexto geográfico de España.

    Args:
        df: DataFrame con datos crudos
        config: Configuración con límites físicos

    Returns:
        DataFrame con valores fuera de rangos marcados como NaN
    """
    df_clean = df.copy()

    # Temperatura
    if "temp" in df_clean.columns:
        mask = (df_clean["temp"] < config.TEMP_MIN_PHYSICAL) | (
            df_clean["temp"] > config.TEMP_MAX_PHYSICAL
        )
        df_clean.loc[mask, "temp"] = np.nan

    # Humedad relativa
    if "rhum" in df_clean.columns:
        mask = (df_clean["rhum"] < config.HUMIDITY_MIN) | (
            df_clean["rhum"] > config.HUMIDITY_MAX
        )
        df_clean.loc[mask, "rhum"] = np.nan

    # Presión atmosférica
    if "pres" in df_clean.columns:
        mask = (df_clean["pres"] < config.PRESSURE_MIN) | (
            df_clean["pres"] > config.PRESSURE_MAX
        )
        df_clean.loc[mask, "pres"] = np.nan

    return df_clean


# ============================================================================
# CAPA 2: DETECCIÓN ESTADÍSTICA ESTACIONALIZADA
# ============================================================================


def detect_outliers_seasonalized_zscore(
    group_df: pd.DataFrame, col: str, threshold: float
) -> pd.Series:
    """
    Detecta outliers usando Z-score estacionalizado por mes y hora.

    No compara una hora contra todo el año, sino cada "julio 15:00" solo
    contra otros "julios 15:00".

    Args:
        group_df: DataFrame agrupado por mes y hora
        col: Columna a analizar
        threshold: Umbral de z-score (4.0)

    Returns:
        Serie booleana indicando outliers
    """
    if col not in group_df.columns or group_df[col].isna().all():
        return pd.Series(False, index=group_df.index)

    mean = group_df[col].mean()
    std = group_df[col].std()

    if std == 0 or pd.isna(std):
        return pd.Series(False, index=group_df.index)

    z_scores = np.abs((group_df[col] - mean) / std)
    return z_scores > threshold


def detect_outliers_seasonalized_iqr(
    group_df: pd.DataFrame, col: str, multiplier: float
) -> pd.Series:
    """
    Detecta outliers usando IQR estacionalizado por mes y hora.

    Más robusto que z-score frente a distribuciones no normales.

    Args:
        group_df: DataFrame agrupado por mes y hora
        col: Columna a analizar
        multiplier: Multiplicador del IQR (3.0 para outliers extremos)

    Returns:
        Serie booleana indicando outliers
    """
    if col not in group_df.columns or group_df[col].isna().all():
        return pd.Series(False, index=group_df.index)

    Q1 = group_df[col].quantile(0.25)
    Q3 = group_df[col].quantile(0.75)
    IQR = Q3 - Q1

    if IQR == 0 or pd.isna(IQR):
        return pd.Series(False, index=group_df.index)

    lower_bound = Q1 - multiplier * IQR
    upper_bound = Q3 + multiplier * IQR

    return (group_df[col] < lower_bound) | (group_df[col] > upper_bound)


# ============================================================================
# CAPA 3: CONSISTENCIA TEMPORAL
# ============================================================================


def detect_temporal_inconsistencies(
    df: pd.DataFrame, col: str, config: Config
) -> tuple[pd.Series, pd.Series]:
    """
    Detecta inconsistencias temporales (saltos bruscos y valores constantes).

    Args:
        df: DataFrame con datos de UNA estación (ordenado por timestamp)
        col: Columna a analizar
        config: Configuración

    Returns:
        Tupla (serie_saltos_bruscos, serie_valores_constantes)
    """
    if col not in df.columns:
        return pd.Series(False, index=df.index), pd.Series(False, index=df.index)

    # Saltos bruscos (cambio > MAX_TEMP_CHANGE_PER_HOUR entre horas consecutivas)
    diff = df[col].diff().abs()
    sudden_jumps = diff > config.MAX_TEMP_CHANGE_PER_HOUR

    # Valores constantes (mismo valor durante CONSTANT_VALUE_HOURS horas)
    constant_blocks = pd.Series(False, index=df.index)

    if not df[col].isna().all():
        value_changes = (df[col] != df[col].shift()).cumsum()

        for _, group in df.groupby(value_changes):
            if len(group) >= config.CONSTANT_VALUE_HOURS:
                value = group[col].iloc[0]
                if not pd.isna(value):
                    constant_blocks.loc[group.index] = True

    return sudden_jumps, constant_blocks


# ============================================================================
# INTERPOLACIÓN SPLINE (GAPS CORTOS)
# ============================================================================


def interpolate_gaps_spline(series: pd.Series, max_gap: int) -> pd.Series:
    """
    Interpolación con spline cúbico para gaps cortos (≤6 horas).

    Justificación: La temperatura tiene estructura no lineal (ciclo diario).
    Spline preserva mejor la continuidad temporal que interpolación lineal.

    Args:
        series: Serie temporal con gaps
        max_gap: Máximo gap a interpolar (horas)

    Returns:
        Serie con gaps cortos interpolados
    """
    series_filled = series.copy()
    gaps = series_filled.isna()
    gap_groups = (gaps != gaps.shift()).cumsum()

    for gap_id, gap_group in series_filled[gaps].groupby(gap_groups[gaps]):
        gap_length = len(gap_group)

        if gap_length <= max_gap:
            start_idx = gap_group.index[0]
            end_idx = gap_group.index[-1]

            idx_pos_start = series_filled.index.get_loc(start_idx)
            idx_pos_end = series_filled.index.get_loc(end_idx)

            # Ventana de contexto: 24 horas antes y después
            window_before = max(0, idx_pos_start - 24)
            window_after = min(len(series_filled), idx_pos_end + 24)

            window_data = series_filled.iloc[window_before:window_after]
            valid_data = window_data.dropna()

            if len(valid_data) >= 4:  # Mínimo para spline cúbico
                try:
                    # Timestamp a segundos
                    x_valid = valid_data.index.astype(np.int64) // 10**9
                    y_valid = valid_data.values

                    # Spline cúbico
                    spline = UnivariateSpline(x_valid, y_valid, k=3, s=0)

                    # Interpolar gap
                    x_gap = gap_group.index.astype(np.int64) // 10**9
                    y_gap = spline(x_gap)

                    series_filled.loc[gap_group.index] = y_gap
                except Exception:
                    # Fallback a interpolación lineal si spline falla
                    series_filled.loc[start_idx:end_idx] = series_filled.interpolate(
                        method="linear", limit=max_gap
                    ).loc[start_idx:end_idx]

    return series_filled


# ============================================================================
# INTERPOLACIÓN CONDICIONADA (GAPS LARGOS)
# ============================================================================


def interpolate_gaps_conditioned(
    df: pd.DataFrame, col: str, max_gap: int, config: Config
) -> pd.Series:
    """
    Interpolación condicionada por hora para gaps largos (>6h, ≤72h).

    Método:
        1. Estimar tendencia mensual-anual
        2. Estimar patrón horario histórico
        3. Combinar: valor_fill = patrón_horario + anomalía_tendencia

    Args:
        df: DataFrame con datos de UNA estación
        col: Columna a interpolar
        max_gap: Máximo gap a interpolar (horas)
        config: Configuración

    Returns:
        Serie con gaps largos interpolados
    """
    series = df[col].copy()
    df_temp = df.copy()

    # Añadir columnas temporales
    df_temp["year"] = pd.to_datetime(df_temp["timestamp"]).dt.year
    df_temp["month"] = pd.to_datetime(df_temp["timestamp"]).dt.month
    df_temp["hour"] = pd.to_datetime(df_temp["timestamp"]).dt.hour

    # Tendencia: media por año y mes
    monthly_year_mean = df_temp.groupby(["year", "month"])[col].transform("mean")

    # Patrón horario: media histórica por mes y hora
    hourly_pattern = df_temp.groupby(["month", "hour"])[col].transform("mean")

    # Anomalía de tendencia
    monthly_mean = df_temp.groupby("month")[col].transform("mean")
    trend_anomaly = monthly_year_mean - monthly_mean

    # Rellenar gaps largos
    gaps = series.isna()
    gap_groups = (gaps != gaps.shift()).cumsum()

    for gap_id, gap_group in series[gaps].groupby(gap_groups[gaps]):
        gap_length = len(gap_group)

        if config.MAX_GAP_HOURS_SHORT < gap_length <= max_gap:
            gap_indices = gap_group.index
            filled_values = (
                hourly_pattern.loc[gap_indices] + trend_anomaly.loc[gap_indices]
            )
            series.loc[gap_indices] = filled_values

    return series


# ============================================================================
# HOMOGENEIZACIÓN: TEST DE PETTITT
# ============================================================================


def pettitt_test(series: pd.Series) -> tuple[int, float]:
    """
    Test de Pettitt para detectar cambio de punto en una serie temporal.

    Usado para detectar cambios de emplazamiento o instrumentación en estaciones
    meteorológicas (homogeneización básica).

    Args:
        series: Serie temporal (típicamente medias anuales)

    Returns:
        Tupla (índice_cambio, p_value)
            - índice_cambio: Posición del cambio detectado (o -1 si no hay)
            - p_value: Significancia estadística
    """
    n = len(series)
    if n < 3:
        return -1, 1.0

    # Calcular estadístico U
    U = np.zeros(n)
    for t in range(1, n):
        # Comparar datos antes y después de t
        before = series.iloc[:t].values
        after = series.iloc[t:].values

        # U_t = suma de signos de diferencias
        U_t = 0
        for x in before:
            for y in after:
                U_t += np.sign(y - x)
        U[t] = abs(U_t)

    # Estadístico K (máximo de U)
    K = np.max(U)
    change_point = np.argmax(U)

    # P-value aproximado
    p_value = 2 * np.exp(-6 * K**2 / (n**3 + n**2))

    return change_point, p_value


def homogenize_station(df: pd.DataFrame, config: Config) -> pd.DataFrame:
    """
    Aplica test de Pettitt para detectar cambios de emplazamiento.

    Si se detecta un cambio significativo en la serie de medias anuales,
    se marca en los metadatos para consideración posterior.

    Args:
        df: DataFrame de UNA estación
        config: Configuración

    Returns:
        DataFrame con columna 'has_changepoint' añadida
    """
    df_clean = df.copy()

    # Calcular medias anuales
    df_clean["year"] = pd.to_datetime(df_clean["timestamp"]).dt.year
    annual_means = df_clean.groupby("year")["temp"].mean()

    # Aplicar test de Pettitt
    change_idx, p_value = pettitt_test(annual_means)

    # Marcar si hay cambio significativo
    has_changepoint = p_value < config.PETTITT_SIGNIFICANCE

    df_clean["has_changepoint"] = has_changepoint
    df_clean["changepoint_year"] = (
        annual_means.index[change_idx] if has_changepoint else np.nan
    )
    df_clean["changepoint_pvalue"] = p_value

    df_clean.drop("year", axis=1, inplace=True)

    return df_clean


# ============================================================================
# PIPELINE DE QC COMPLETO
# ============================================================================


def quality_control_station(df: pd.DataFrame, config: Config) -> pd.DataFrame:
    """
    Aplica control de calidad completo (3 capas) a datos de UNA estación.

    Pipeline:
        1. Filtros físicos
        2. Detección estadística estacionalizada (Z-score + IQR)
        3. Consistencia temporal
        4. Interpolación spline (gaps cortos)
        5. Interpolación condicionada (gaps largos si >7.5%)
        6. Homogeneización (Test de Pettitt)

    Args:
        df: DataFrame con datos de una estación
        config: Configuración

    Returns:
        DataFrame limpio con variables de QC añadidas
    """
    df_clean = df.copy()
    df_clean["timestamp"] = pd.to_datetime(df_clean["timestamp"])

    # Columnas temporales
    df_clean["month"] = df_clean["timestamp"].dt.month
    df_clean["hour"] = df_clean["timestamp"].dt.hour

    # Inicializar columnas QC
    df_clean["is_outlier"] = False
    df_clean["was_missing"] = df_clean["temp"].isna()
    df_clean["z_score"] = np.nan

    # CAPA 1: Filtros físicos
    df_clean = apply_physical_limits(df_clean, config)

    # CAPA 2: Detección estacionalizada
    if "temp" in df_clean.columns:
        grouped = df_clean.groupby(["month", "hour"], group_keys=False)

        outliers_zscore = grouped.apply(
            lambda x: detect_outliers_seasonalized_zscore(
                x, "temp", config.Z_SCORE_THRESHOLD
            )
        )

        outliers_iqr = grouped.apply(
            lambda x: detect_outliers_seasonalized_iqr(x, "temp", config.IQR_MULTIPLIER)
        )

        # Combinar: outlier si AMBOS lo detectan
        statistical_outliers = outliers_zscore & outliers_iqr

        # Calcular z-scores
        z_scores = pd.Series(np.nan, index=df_clean.index)
        for (month, hour), group in df_clean.groupby(["month", "hour"]):
            mean = group["temp"].mean()
            std = group["temp"].std()
            if std > 0 and not pd.isna(std):
                z_scores.loc[group.index] = np.abs((group["temp"] - mean) / std)
        df_clean["z_score"] = z_scores

        # CAPA 3: Consistencia temporal
        sudden_jumps, constant_blocks = detect_temporal_inconsistencies(
            df_clean, "temp", config
        )

        df_clean["is_outlier"] = statistical_outliers | sudden_jumps | constant_blocks
        df_clean.loc[df_clean["is_outlier"], "temp"] = np.nan

    # INTERPOLACIÓN
    if "temp" in df_clean.columns:
        # Contar gaps largos
        gaps = df_clean["temp"].isna()
        gap_groups = (gaps != gaps.shift()).cumsum()

        long_gaps_count = 0
        total_gap_hours = 0

        for gap_id, gap_group in df_clean[gaps].groupby(gap_groups[gaps]):
            gap_length = len(gap_group)
            total_gap_hours += gap_length
            if gap_length > config.MAX_GAP_HOURS_SHORT:
                long_gaps_count += 1

        long_gap_ratio = total_gap_hours / len(df_clean)

        # Primero: spline para gaps cortos
        df_clean["temp"] = interpolate_gaps_spline(
            df_clean["temp"], config.MAX_GAP_HOURS_SHORT
        )

        # Si >7.5% gaps largos: interpolación condicionada
        if long_gap_ratio > config.LONG_GAP_THRESHOLD:
            df_clean["temp"] = interpolate_gaps_conditioned(
                df_clean, "temp", config.MAX_GAP_HOURS_LONG, config
            )

    # HOMOGENEIZACIÓN
    df_clean = homogenize_station(df_clean, config)

    # Limpiar columnas auxiliares
    df_clean.drop(["month", "hour"], axis=1, inplace=True)

    return df_clean


def process_all_stations_qc(df: pd.DataFrame, config: Config) -> pd.DataFrame:
    """
    Aplica control de calidad a todas las estaciones.

    Args:
        df: DataFrame completo con todas las estaciones
        config: Configuración

    Returns:
        DataFrame limpio con estadísticas de QC guardadas
    """
    print("\n" + "=" * 70)
    print("CONTROL DE CALIDAD AVANZADO (3 CAPAS + HOMOGENEIZACIÓN)")
    print("=" * 70)

    cleaned_stations = []
    qc_stats = []

    for station_id in tqdm(df["station_id"].unique(), desc="QC"):
        station_df = df[df["station_id"] == station_id].copy()

        total_records = len(station_df)
        missing_before = station_df["temp"].isna().sum()

        clean_station = quality_control_station(station_df, config)

        missing_after = clean_station["temp"].isna().sum()
        outliers_detected = clean_station["is_outlier"].sum()
        interpolated = (
            clean_station["was_missing"] & clean_station["temp"].notna()
        ).sum()

        # Homogeneización
        has_changepoint = clean_station["has_changepoint"].iloc[0]
        changepoint_year = clean_station["changepoint_year"].iloc[0]

        cleaned_stations.append(clean_station)

        qc_stats.append(
            {
                "station_id": station_id,
                "total_records": total_records,
                "missing_before": int(missing_before),
                "outliers_detected": int(outliers_detected),
                "missing_after": int(missing_after),
                "interpolated": int(interpolated),
                "completeness_before": float(
                    (total_records - missing_before) / total_records
                ),
                "completeness_after": float(
                    (total_records - missing_after) / total_records
                ),
                "has_changepoint": bool(has_changepoint),
                "changepoint_year": (
                    int(changepoint_year) if not pd.isna(changepoint_year) else None
                ),
            }
        )

    df_clean = pd.concat(cleaned_stations, ignore_index=True)

    # Guardar estadísticas
    qc_df = pd.DataFrame(qc_stats)
    qc_path = config.RESULTS_DIR / "quality_control_stats.json"
    qc_df.to_json(qc_path, orient="records", indent=2)

    print(f"\n Total registros: {len(df_clean):,}")
    print(f" Outliers detectados: {df_clean['is_outlier'].sum():,}")
    print(
        f" Valores interpolados: {(df_clean['was_missing'] & df_clean['temp'].notna()).sum():,}"
    )
    print(f" Completitud promedio: {qc_df['completeness_after'].mean():.1%}")
    print(f" Estaciones con cambio de emplazamiento: {qc_df['has_changepoint'].sum()}")

    return df_clean
