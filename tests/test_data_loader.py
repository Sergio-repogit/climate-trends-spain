"""
Tests para el cargador de datos y optimización de memoria.

Enfoque:
    - Verificación de reducción de huella de memoria.
    - Integridad de datos tras conversión de tipos.
    - Manejo de valores nulos (NaN) en optimización.
"""

import numpy as np
import pandas as pd
import pytest

from src.weather.data_loader import optimize_df


def test_optimize_df_memory_reduction():
    """Verifica que la optimización reduce el uso de memoria en RAM."""
    # Crear DataFrame con tipos pesados (int64, float64) y muchos datos
    n = 10000
    df = pd.DataFrame(
        {
            "id": np.random.randint(0, 100, n, dtype=np.int64),
            "temp": np.random.uniform(-10, 40, n).astype(np.float64),
            "rhum": np.random.uniform(0, 100, n).astype(np.float64),
            "category": ["A", "B", "C", "D"] * (n // 4),
        }
    )

    memory_before = df.memory_usage(deep=True).sum()
    df_optimized = optimize_df(df)
    memory_after = df_optimized.memory_usage(deep=True).sum()

    # La memoria debería haberse reducido significativamente
    assert memory_after < memory_before

    # Verificar que los tipos han cambiado a formatos más ligeros
    assert df_optimized["id"].dtype in [np.int8, np.int16, np.uint8, np.uint16]
    # Las temperaturas pasan a float32 o float16
    assert df_optimized["temp"].dtype in [np.float16, np.float32]


def test_optimize_df_integrity():
    """Verifica que los valores numéricos no se alteren significativamente."""
    df = pd.DataFrame({"temp": [15.5, 20.1, -5.2, 30.0], "rhum": [50, 60, 70, 80]})

    df_opt = optimize_df(df.copy())

    # Comprobar que los valores son aproximadamente iguales
    # (Usamos atol=0.1 porque float16 tiene menos precisión que float64)
    pd.testing.assert_frame_equal(df, df_opt, check_dtype=False, atol=0.1)


def test_optimize_df_with_nans():
    """Verifica que el optimizador maneja correctamente los NaNs."""
    df = pd.DataFrame({"temp": [15.5, np.nan, 20.0], "precip": [0.0, 1.0, np.nan]})

    # Este test fallaría si intentamos convertir a Int sin manejar NaNs
    df_opt = optimize_df(df)

    assert df_opt["temp"].isna().sum() == 1
    assert df_opt["precip"].isna().sum() == 1
    # Debería mantenerse como float (los Int de numpy no soportan NaN)
    assert np.issubdtype(df_opt["temp"].dtype, np.floating)


def test_optimize_df_categorical():
    """Verifica la optimización de columnas de texto repetitivas."""
    df = pd.DataFrame({"region": ["Galicia", "Madrid", "Andalucia", "Galicia"] * 100})

    df_opt = optimize_df(df)

    assert "region" in df_opt.columns
    assert len(df_opt["region"].unique()) == 3


# ============================================================================
# TESTS DE INTEGRACIÓN (CON MOCKING)
# ============================================================================

from unittest.mock import patch  # noqa: E402

from src.weather.config import Config  # noqa: E402


class MockConfig(Config):
    """Configuración aislada para no tocar carpetas reales."""

    def __init__(self, tmp_path):
        self.RAW_DIR = tmp_path / "raw"
        self.RAW_DIR.mkdir(parents=True, exist_ok=True)
        self.STATION_IDS = {"TEST_STATION": "00000"}
        # El cargador espera una lista/tupla para desempaquetar:
        # [lat, lon, alt, region, tipo_entorno, dist_costa]
        self.STATION_METADATA = {
            "TEST_STATION": [40.0, -3.0, 500, "TestRegion", "Costa", 5.0]
        }
        self.START_DATE = pd.to_datetime("2020-01-01")
        self.END_DATE = pd.to_datetime("2020-01-02")


@pytest.fixture
def mock_config(tmp_path):
    return MockConfig(tmp_path)


def test_download_all_stations_logic(mock_config):
    """Verifica que el proceso de descarga y ensamblado funciona (sin internet)."""

    # Simulamos la descarga de una estación
    mock_df = pd.DataFrame(
        {
            "timestamp": pd.date_range("2020-01-01", periods=10, freq="h"),
            "temp": np.random.uniform(15, 25, 10),
            "station_id": ["00000"] * 10,
        }
    )

    with patch("src.weather.data_loader.download_station_data") as mock_dl:
        mock_dl.return_value = mock_df

        from src.weather.data_loader import download_all_stations

        combined_df = download_all_stations(mock_config)

        # Verificaciones
        assert len(combined_df) == 10
        # Debe haber añadido las columnas de metadatos
        assert "region" in combined_df.columns
        assert "tipo_entorno" in combined_df.columns
        assert combined_df["region"].iloc[0] == "TestRegion"

        # Debe haberse guardado el archivo de metadatos JSON
        assert (mock_config.RAW_DIR / "stations_metadata.json").exists()
        assert (mock_config.RAW_DIR / "all_stations_raw.parquet").exists()
