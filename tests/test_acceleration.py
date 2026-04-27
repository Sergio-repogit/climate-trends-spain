"""
Tests para el análisis de aceleración climática (subperíodos).

Verifica que el sistema sea capaz de segmentar los datos correctamente
y calcular tendencias diferenciadas por lustros.
"""

import numpy as np
import pandas as pd
import pytest

from src.weather.analysis import analyze_trends_acceleration
from src.weather.config import Config


@pytest.fixture
def config():
    """Fixture de configuración."""
    return Config()


@pytest.fixture
def acceleration_sample_df():
    """
    Genera un DataFrame con 15 años de datos (2010-2025).
    Estación 'STATION_ACC': Calentamiento que se duplica cada 5 años.
    Estación 'STATION_FLAT': Sin tendencia.
    """
    dates = pd.date_range("2010-01-01", "2025-12-31", freq="D")
    n = len(dates)

    # Segmentos de 5 años aprox (365 * 5 = 1825 días)
    # Estación con aceleración:
    # 2010-2015: +0.1°C total
    # 2015-2020: +1.0°C total
    # 2020-2025: +3.0°C total
    s1 = np.linspace(15, 15.1, 1825 + 1)  # + bisiesto
    s2 = np.linspace(15.1, 16.1, 1826 + 1)
    s3 = np.linspace(16.1, 19.1, n - (len(s1) + len(s2)))

    temp_acc = np.concatenate([s1, s2, s3])
    # Añadir ruido mínimo para no romper el test estadístico
    temp_acc += np.random.normal(0, 0.05, n)

    df_acc = pd.DataFrame(
        {
            "timestamp": dates,
            "station_id": "STATION_ACC",
            "tmax": temp_acc + 2,
            "tmin": temp_acc - 2,
            "tavg": temp_acc,
        }
    )

    # Estación plana
    temp_flat = np.full(n, 15.0) + np.random.normal(0, 0.05, n)
    df_flat = pd.DataFrame(
        {
            "timestamp": dates,
            "station_id": "STATION_FLAT",
            "tmax": temp_flat + 2,
            "tmin": temp_flat - 2,
            "tavg": temp_flat,
        }
    )

    return pd.concat([df_acc, df_flat]).reset_index(drop=True)


def test_acceleration_output_structure(acceleration_sample_df, config):
    """Verifica que el DataFrame de salida tenga las columnas y filas esperadas."""
    results = analyze_trends_acceleration(acceleration_sample_df, config)

    # Comprobar columnas
    expected_cols = ["station_id", "periodo", "tmax_slope", "tmin_slope", "tavg_slope"]
    for col in expected_cols:
        assert col in results.columns

    # 2 estaciones * 3 subperiodos = 6 filas
    assert len(results) == 6

    # Comprobar que los periodos coinciden con la config
    periods = results["periodo"].unique()
    assert len(periods) == 3
    assert "2010-2015" in periods
    assert "2020-2025" in periods


def test_acceleration_trend_detection(acceleration_sample_df, config):
    """Verifica que detecte que la pendiente es mayor en el último periodo para STATION_ACC."""
    results = analyze_trends_acceleration(acceleration_sample_df, config)

    acc_results = results[results["station_id"] == "STATION_ACC"].sort_values("periodo")
    slopes = acc_results["tavg_slope"].values

    # La pendiente de 2020-2025 debe ser claramente superior a la de 2010-2015
    assert slopes[2] > slopes[0]
    # En el último periodo la pendiente debería ser positiva y significativa
    assert slopes[2] > 0.5


def test_acceleration_flat_station(acceleration_sample_df, config):
    """Verifica que una estación sin tendencia mantenga pendientes cercanas a cero."""
    results = analyze_trends_acceleration(acceleration_sample_df, config)

    flat_results = results[results["station_id"] == "STATION_FLAT"]

    # Todas las pendientes deberían ser muy pequeñas (ruido blanco)
    for slope in flat_results["tavg_slope"]:
        assert abs(slope) < 0.2
