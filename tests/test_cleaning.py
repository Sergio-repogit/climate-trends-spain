"""
Tests para el módulo de limpieza de datos.

Cubre:
    - Filtros físicos
    - Detección de outliers estacionalizada
    - Consistencia temporal
    - Interpolación spline
    - Test de Pettitt
"""

import numpy as np
import pandas as pd
import pytest

from src.weather.cleaning import (
    apply_physical_limits,
    detect_outliers_seasonalized_iqr,
    detect_outliers_seasonalized_zscore,
    detect_temporal_inconsistencies,
    interpolate_gaps_spline,
    pettitt_test,
)
from src.weather.config import Config


@pytest.fixture
def config():
    """Fixture de configuración para tests."""
    return Config()


@pytest.fixture
def sample_df():
    """DataFrame de ejemplo para tests."""
    dates = pd.date_range("2020-01-01", periods=100, freq="h")
    df = pd.DataFrame(
        {
            "timestamp": dates,
            "temp": np.random.normal(15, 5, 100),
            "rhum": np.random.uniform(30, 90, 100),
            "pres": np.random.uniform(980, 1020, 100),
            "month": [d.month for d in dates],
            "hour": [d.hour for d in dates],
        }
    )
    return df


def test_apply_physical_limits(sample_df, config):
    """Test de filtros físicos."""
    # Añadir valores fuera de rango
    sample_df.loc[0, "temp"] = -50.0  # Muy frío
    sample_df.loc[1, "temp"] = 60.0  # Muy caliente
    sample_df.loc[2, "rhum"] = 150.0  # Humedad imposible

    df_clean = apply_physical_limits(sample_df, config)

    # Verificar que valores fuera de rango son NaN
    assert pd.isna(df_clean.loc[0, "temp"])
    assert pd.isna(df_clean.loc[1, "temp"])
    assert pd.isna(df_clean.loc[2, "rhum"])


def test_detect_outliers_seasonalized_zscore():
    """Test de detección de outliers por Z-score."""
    # Datos con un outlier claro
    df = pd.DataFrame(
        {
            "temp": [10, 11, 12, 11, 10, 100],  # 100 es outlier
        }
    )

    outliers = detect_outliers_seasonalized_zscore(df, "temp", threshold=1.5)

    # El último valor debería ser outlier
    assert outliers.iloc[-1]
    assert outliers.iloc[0:5].sum() == 0


def test_detect_outliers_seasonalized_iqr():
    """Test de detección de outliers por IQR."""
    df = pd.DataFrame(
        {
            "temp": [10, 11, 12, 11, 10, 100],  # 100 es outlier
        }
    )

    outliers = detect_outliers_seasonalized_iqr(df, "temp", multiplier=3.0)

    # El último valor debería ser outlier
    assert outliers.iloc[-1]


def test_detect_temporal_inconsistencies(config):
    """Test de detección de inconsistencias temporales."""
    # Crear serie con salto brusco
    df = pd.DataFrame(
        {
            "temp": [10, 11, 12, 30, 31, 32],  # Salto de 12 a 30
        }
    )

    sudden_jumps, constant_blocks = detect_temporal_inconsistencies(df, "temp", config)

    # Debería detectar el salto
    assert sudden_jumps.iloc[3]


def test_interpolate_gaps_spline():
    """Test de interpolación con spline."""
    # Crear serie con gap corto
    series = pd.Series([10, 11, np.nan, np.nan, 14, 15])

    filled = interpolate_gaps_spline(series, max_gap=3)

    # Verificar que el gap fue rellenado
    assert not filled.isna().any()
    # Los valores interpolados deberían estar entre 11 y 14
    assert 11 < filled.iloc[2] < 14
    assert 11 < filled.iloc[3] < 14


def test_pettitt_test():
    """Test del test de Pettitt para detectar cambio de punto."""
    # Serie con cambio de punto claro
    series = pd.Series([10] * 10 + [20] * 10)

    change_idx, p_value = pettitt_test(series)

    # Debería detectar cambio alrededor del índice 10
    assert 8 <= change_idx <= 12
    # P-value debería ser bajo (cambio significativo)
    assert p_value < 0.05


def test_pettitt_test_no_change():
    """Test de Pettitt con serie sin cambio."""
    # Serie sin cambio
    series = pd.Series(np.random.normal(15, 1, 20))

    change_idx, p_value = pettitt_test(series)

    # P-value debería ser alto (no hay cambio significativo)
    assert p_value > 0.05


def test_clean_station_data_full_pipeline(sample_df, config):
    """Test de integración: verifica el flujo completo de limpieza."""
    # Añadir diversos problemas
    sample_df.loc[0, "temp"] = 80.0  # Outlier físico
    sample_df.loc[10:15, "temp"] = 20.0  # Bloque constante
    sample_df.loc[20, "temp"] = np.nan  # Gap para interpolar

    from src.weather.cleaning import quality_control_station

    # Ejecutar limpieza completa
    df_cleaned = quality_control_station(sample_df, config)

    assert isinstance(df_cleaned, pd.DataFrame)
    # El valor de 80.0 debería haber sido eliminado
    assert pd.isna(df_cleaned.loc[0, "temp"]) or df_cleaned.loc[0, "temp"] < 50.0
    # Debería haber columnas de QC
    assert "is_outlier" in df_cleaned.columns
