from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st


@st.cache_data
def load_unified_dataset():
    """Carga el dataset unificado desde el archivo parquet o genera dummy data."""
    try:
        # Resolver ruta relativa compatible con Git y Streamlit Cloud
        possible_paths = [
            Path("data/results/unified_streamlit_data.parquet"),
            Path("../data/results/unified_streamlit_data.parquet"),
            Path("streamlit_app/data/unified_streamlit_data.parquet"),
        ]

        file_path = None
        for path in possible_paths:
            if path.exists():
                file_path = path
                break

        if file_path is not None:
            return pd.read_parquet(file_path)
        else:
            st.warning(
                "Base de datos unificada no encontrada. Cargando datos de simulación para demostración."
            )
            return _generate_dummy_unified()
    except Exception as e:
        st.error(f"Error cargando base de datos unificada: {e}")
        return _generate_dummy_unified()


@st.cache_data
def load_comprehensive_trends():
    df = load_unified_dataset()
    if df.empty:
        return df
    return df[df["dataset_type"] == "comprehensive_trends"].dropna(axis=1, how="all")


@st.cache_data
def load_acceleration_trends():
    df = load_unified_dataset()
    if df.empty:
        return df
    return df[df["dataset_type"] == "acceleration_trends"].dropna(axis=1, how="all")


@st.cache_data
def load_annual_timeseries(station_id):
    df = load_unified_dataset()
    if df.empty:
        return df
    res = df[
        (df["dataset_type"] == "annual_timeseries") & (df["station_id"] == station_id)
    ].dropna(axis=1, how="all")
    if not res.empty:
        res["timestamp"] = pd.to_datetime(res["timestamp"])
    return res


@st.cache_data
def load_yearly_extremes():
    df = load_unified_dataset()
    if df.empty:
        return df
    return df[df["dataset_type"] == "yearly_extremes"].dropna(axis=1, how="all")


@st.cache_data
def load_seasonal_analysis():
    df = load_unified_dataset()
    if df.empty:
        return df
    return df[df["dataset_type"] == "seasonal_trends"].dropna(axis=1, how="all")


def _generate_dummy_unified():
    # Genera un dataset unificado simulado completo y consistente
    np.random.seed(42)
    stations = [f"EST_{i:03d}" for i in range(1, 52)]

    # 1. Comprehensive trends
    df_comp = pd.DataFrame(
        {
            "station_id": stations,
            "region": ["Region_" + str(i % 17) for i in range(51)],
            "latitud": np.random.uniform(36.0, 43.0, 51),
            "longitud": np.random.uniform(-9.0, 3.0, 51),
            "altitud": np.random.uniform(0, 1500, 51),
            "tipo_entorno": np.random.choice(["Costa", "Interior"], 51),
            "distancia_costa": np.random.uniform(0, 200, 51),
            "tmax_slope": np.random.normal(0.4, 0.1, 51),
            "tmax_p_value": [0.01] * 51,
            "tmax_lower_ci": np.random.normal(0.3, 0.1, 51),
            "tmax_upper_ci": np.random.normal(0.5, 0.1, 51),
            "tmax_autocorr": [0.1] * 51,
            "tmin_slope": np.random.normal(0.3, 0.1, 51),
            "tmin_p_value": [0.01] * 51,
            "tmin_lower_ci": np.random.normal(0.2, 0.1, 51),
            "tmin_upper_ci": np.random.normal(0.4, 0.1, 51),
            "tmin_autocorr": [0.1] * 51,
            "tavg_slope": np.random.normal(0.35, 0.1, 51),
            "tavg_p_value": [0.01] * 51,
            "tavg_lower_ci": np.random.normal(0.25, 0.1, 51),
            "tavg_upper_ci": np.random.normal(0.45, 0.1, 51),
            "tavg_autocorr": [0.1] * 51,
            "tropical_night_slope": np.random.normal(2, 1, 51),
            "tropical_night_p_value": [0.01] * 51,
            "extreme_heat_slope": np.random.normal(1.5, 0.5, 51),
            "extreme_heat_p_value": [0.01] * 51,
            "cold_extreme_slope": np.random.normal(-1.0, 0.5, 51),
            "cold_extreme_p_value": [0.01] * 51,
            "p90_slope": np.random.normal(0.5, 0.2, 51),
            "p90_p_value": [0.01] * 51,
            "dataset_type": "comprehensive_trends",
        }
    )

    # 2. Acceleration trends
    acc_rows = []
    for s in stations:
        for p, factor in [("2010-2015", 0.7), ("2015-2020", 1.1), ("2020-2025", 1.4)]:
            acc_rows.append(
                {
                    "station_id": s,
                    "periodo": p,
                    "tavg_slope": 0.35 * factor,
                    "tmax_slope": 0.4 * factor,
                    "tmin_slope": 0.3 * factor,
                    "tavg_p_value": 0.01,
                    "tmax_p_value": 0.01,
                    "tmin_p_value": 0.01,
                    "dataset_type": "acceleration_trends",
                }
            )
    df_acc = pd.DataFrame(acc_rows)

    # 3. Annual timeseries
    ts_rows = []
    for s in stations:
        base_temp = np.random.uniform(10, 20)
        for year in range(2010, 2026):
            ts_rows.append(
                {
                    "station_id": s,
                    "year": year,
                    "temp": base_temp
                    + (year - 2010) * 0.035
                    + np.random.normal(0, 0.5),
                    "timestamp": pd.to_datetime(f"{year}-12-31"),
                    "dataset_type": "annual_timeseries",
                }
            )
    df_ts = pd.DataFrame(ts_rows)

    # 4. Yearly extremes
    ext_rows = []
    for s in stations:
        for year in range(2010, 2026):
            ext_rows.append(
                {
                    "station_id": s,
                    "year": year,
                    "is_tropical_night": int(
                        np.random.poisson(10 + (year - 2010) * 0.5)
                    ),
                    "is_extreme_heat": int(np.random.poisson(5 + (year - 2010) * 0.2)),
                    "is_cold_extreme": int(np.random.poisson(8 - (year - 2010) * 0.3)),
                    "dataset_type": "yearly_extremes",
                }
            )
    df_ext = pd.DataFrame(ext_rows)

    # 5. Seasonal trends
    season_rows = []
    for s in stations:
        for season in ["Invierno", "Primavera", "Verano", "Otoño"]:
            for var_name, slope in [("Media", 0.35), ("Máxima", 0.4), ("Mínima", 0.3)]:
                season_rows.append(
                    {
                        "station_id": s,
                        "season": season,
                        "variable": var_name,
                        "slope": slope + np.random.normal(0, 0.1),
                        "p_value": 0.01,
                        "dataset_type": "seasonal_trends",
                    }
                )
    df_season = pd.DataFrame(season_rows)

    return pd.concat([df_comp, df_acc, df_ts, df_ext, df_season], ignore_index=True)
