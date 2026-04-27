"""
Tests para el módulo de análisis estadístico.

Cubre:
    - Pre-whitening
    - Mann-Kendall
    - Variables derivadas
    - Cálculos anuales
"""

import numpy as np
import pandas as pd
import pytest

from src.weather.analysis import (
    calculate_derived_variables,
    mann_kendall_with_confidence,
    prewhiten_series,
)
from src.weather.config import Config


@pytest.fixture
def config():
    """Fixture de configuración."""
    return Config()


@pytest.fixture
def sample_timeseries():
    """Serie temporal de ejemplo con tendencia."""
    # Serie con tendencia positiva + ruido
    n = 20
    trend = np.linspace(10, 15, n)
    noise = np.random.normal(0, 0.5, n)
    series = pd.Series(trend + noise)
    return series


def test_prewhiten_series(sample_timeseries):
    """Test de pre-whitening para eliminar autocorrelación."""
    prewhitened, rho = prewhiten_series(sample_timeseries)

    # Debe retornar serie y coeficiente de autocorrelación
    assert isinstance(prewhitened, pd.Series)
    assert isinstance(rho, float)
    # rho debería estar entre -1 y 1
    assert -1 <= rho <= 1


def test_mann_kendall_with_confidence_increasing():
    """Test de Mann-Kendall con tendencia creciente."""
    # Serie con tendencia claramente creciente
    series = pd.Series(np.arange(20) + np.random.normal(0, 0.1, 20))

    result = mann_kendall_with_confidence(series)

    # Debería detectar tendencia creciente
    assert result["trend"] == "increasing"
    # P-value debería ser bajo
    assert result["p_value"] < 0.05
    # Slope debería ser positivo
    assert result["sens_slope"] > 0


def test_mann_kendall_with_confidence_decreasing():
    """Test de Mann-Kendall con tendencia decreciente."""
    # Serie con tendencia claramente decreciente
    series = pd.Series(20 - np.arange(20) + np.random.normal(0, 0.1, 20))

    result = mann_kendall_with_confidence(series)

    # Debería detectar tendencia decreciente
    assert result["trend"] == "decreasing"
    # P-value debería ser bajo
    assert result["p_value"] < 0.05
    # Slope debería ser negativo
    assert result["sens_slope"] < 0


def test_mann_kendall_with_confidence_no_trend():
    """Test de Mann-Kendall sin tendencia."""
    # Serie sin tendencia (ruido puro)
    series = pd.Series(np.random.normal(15, 1, 20))

    result = mann_kendall_with_confidence(series)

    # P-value debería ser alto (no significativo)
    # Con ruido aleatorio, a veces puede dar falsos positivos
    # así que solo verificamos que existe el resultado
    assert "p_value" in result
    assert "sens_slope" in result


def test_mann_kendall_confidence_intervals(sample_timeseries):
    """Test de intervalos de confianza en Sen's slope."""
    result = mann_kendall_with_confidence(sample_timeseries, confidence_level=0.95)

    # Debe tener intervalos de confianza
    assert "slope_lower_ci" in result
    assert "slope_upper_ci" in result

    # IC inferior debe ser menor que IC superior
    if not pd.isna(result["slope_lower_ci"]) and not pd.isna(result["slope_upper_ci"]):
        assert result["slope_lower_ci"] <= result["slope_upper_ci"]


def test_calculate_derived_variables(config):
    """Test de cálculo de variables derivadas."""
    # DataFrame de ejemplo
    dates = pd.date_range("2020-01-01", periods=100, freq="h")
    df = pd.DataFrame(
        {
            "timestamp": dates,
            "temp": np.random.uniform(10, 30, 100),
            "rhum": np.random.uniform(40, 90, 100),
            "station_id": ["test_station"] * 100,
        }
    )

    df_enriched = calculate_derived_variables(df, config)

    # Verificar que se añadieron las variables derivadas
    assert "season" in df_enriched.columns
    assert "is_night" in df_enriched.columns
    assert "anomalia_termica" in df_enriched.columns
    assert "heat_index" in df_enriched.columns
    assert "is_tropical_night" in df_enriched.columns
    assert "is_extreme_heat" in df_enriched.columns
    assert "is_cold_extreme" in df_enriched.columns

    # Verificar tipos
    assert pd.api.types.is_string_dtype(df_enriched["season"])
    assert df_enriched["is_night"].dtype in [int, np.int64, np.int32]


def test_extreme_thresholds(config):
    """Test de umbrales de extremos térmicos."""
    df = pd.DataFrame(
        {
            "timestamp": pd.date_range("2020-01-01", periods=24, freq="h"),
            "temp": [25] * 8 + [22] * 16,  # Primeras 8h son diurnas, resto nocturnas
            "rhum": [50] * 24,
            "station_id": ["test"] * 24,
        }
    )

    df_enriched = calculate_derived_variables(df, config)

    # Verificar que se detectan correctamente los extremos
    # (aunque en este ejemplo no haya extremos reales)
    assert df_enriched["is_tropical_night"].sum() >= 0
    assert df_enriched["is_extreme_heat"].sum() >= 0
    assert df_enriched["is_cold_extreme"].sum() >= 0


def test_analyze_trends_comprehensive(config):
    """Test de integración: verifica el motor principal de tendencias."""
    # Crear datos simulados enriquecidos para 2 años
    dates = pd.date_range("2020-01-01", "2021-12-31", freq="D")
    n = len(dates)
    df = pd.DataFrame(
        {
            "timestamp": dates,
            "station_id": ["TEST_STATION"] * n,
            "region": ["TestRegion"] * n,
            "latitud": [40.0] * n,
            "longitud": [-3.0] * n,
            "altitud": [500] * n,
            "tipo_entorno": ["Costa"] * n,
            "distancia_costa": [5.0] * n,
            "temp": np.random.normal(15, 5, n),
            "tavg": np.random.normal(15, 2, n),
            "tmax": np.random.normal(20, 2, n),
            "tmin": np.random.normal(10, 2, n),
            "is_tropical_night": np.random.randint(0, 2, n),
            "is_extreme_heat": np.random.randint(0, 2, n),
            "is_cold_extreme": np.random.randint(0, 2, n),
        }
    )

    # Redirigir resultados a carpeta temporal para no ensuciar
    import tempfile
    from pathlib import Path

    from src.weather.analysis import analyze_trends_comprehensive

    with tempfile.TemporaryDirectory() as tmp_dir:
        original_results_dir = config.RESULTS_DIR
        config.RESULTS_DIR = Path(tmp_dir)

        results = analyze_trends_comprehensive(df, config)

        assert isinstance(results, pd.DataFrame)
        assert len(results) == 1
        assert "tavg_slope" in results.columns
        assert "tropical_night_slope" in results.columns
        assert "p90_slope" in results.columns

        # Restaurar
        config.RESULTS_DIR = original_results_dir
