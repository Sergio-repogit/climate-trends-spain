"""
Tests para el módulo de visualización.

Verifica que las funciones de graficado generen los archivos físicos
esperados (PNG y HTML) en las rutas configuradas.
"""

import numpy as np
import pandas as pd
import pytest

from src.weather.config import Config
from src.weather.viz import generate_all_visualizations


class MockConfig(Config):
    """Subclase de Config para redirigir salidas a carpetas de test."""
    def __init__(self, tmp_path):
        self.BASE_DIR = tmp_path
        self.DATA_DIR = self.BASE_DIR / "data"
        self.RAW_DIR = self.DATA_DIR / "raw"
        self.PROCESSED_DIR = self.DATA_DIR / "processed"
        self.RESULTS_DIR = self.DATA_DIR / "results"
        self.MAPS_DIR = self.RESULTS_DIR / "maps"
        self.FIGURES_DIR = self.RESULTS_DIR / "figures"
        self.create_directories()

    def create_directories(self) -> None:
        for dir_path in [self.RAW_DIR, self.PROCESSED_DIR, self.RESULTS_DIR, self.MAPS_DIR, self.FIGURES_DIR]:
            dir_path.mkdir(parents=True, exist_ok=True)


@pytest.fixture
def mock_config(tmp_path):
    """Fixture que proporciona una configuración aislada para tests."""
    return MockConfig(tmp_path)


@pytest.fixture
def dummy_data():
    """Genera datos realistas para que las funciones de viz no fallen."""
    # Necesitamos al menos un par de estaciones para que los gráficos de comparación funcionen
    stations = ["TEST1", "TEST2"]
    dates = pd.date_range("2020-01-01", periods=48, freq="h")

    dfs = []
    for s in stations:
        dfs.append(pd.DataFrame({
            "timestamp": dates,
            "station_id": [s] * len(dates),
            "temp": np.random.normal(15, 5, len(dates)),
            "tmax": np.random.normal(20, 5, len(dates)),
            "tmin": np.random.normal(10, 5, len(dates)),
            "tavg": np.random.normal(15, 5, len(dates)),
            "season": ["Invierno"] * len(dates),
            "is_night": [0] * len(dates),
            "month": [d.month for d in dates],
            "hour": [d.hour for d in dates]
        }))

    df = pd.concat(dfs)

    # Resultados de tendencias
    results_list = []
    for s in stations:
        results_list.append({
            "station_id": s,
            "latitud": 40.0,
            "longitud": -3.0,
            "tavg_slope": 0.5,
            "tmax_slope": 0.6,
            "tmin_slope": 0.4,
            "tavg_p_value": 0.01,
            "tmax_p_value": 0.01,
            "tmin_p_value": 0.01,
            "altitud": 500,
            "tipo_entorno": "Costa" if s == "TEST1" else "Interior",
            "region": "TestRegion",
            "distancia_costa": 5.0
        })
    results_df = pd.DataFrame(results_list)

    # Resultados de aceleración
    acc_list = []
    for s in stations:
        for p in ["2010-2015", "2015-2020", "2020-2025"]:
            acc_list.append({
                "station_id": s,
                "periodo": p,
                "tmax_slope": 0.1,
                "tmin_slope": 0.1,
                "tavg_slope": 0.1
            })
    acc_df = pd.DataFrame(acc_list)

    return df, results_df, acc_df


def test_generate_all_visualizations_creates_files(dummy_data, mock_config):
    """Test de integración: verifica que se creen todos los archivos de salida."""
    df, results_df, acc_df = dummy_data

    # Ejecutar generador
    generate_all_visualizations(df, results_df, acc_df, mock_config)

    # Verificar existencia de archivos clave
    assert (mock_config.MAPS_DIR / "trend_map.html").exists()
    assert (mock_config.FIGURES_DIR / "altitude_vs_trend.png").exists()
    assert (mock_config.FIGURES_DIR / "acceleration_comparison.png").exists()
    assert (mock_config.FIGURES_DIR / "completeness_heatmap.png").exists()
    assert (mock_config.FIGURES_DIR / "coastal_vs_inland.png").exists()

