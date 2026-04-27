from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st


@st.cache_data
def load_comprehensive_trends():
    """Carga los resultados del análisis de tendencias. Usa dummy data si falla para que la UI funcione."""
    try:
        # Intentar cargar datos reales (asumiendo ejecución desde la raíz o dentro de streamlit_app)
        base_path = Path("data/results")
        if not base_path.exists():
            base_path = Path("../data/results")

        file_path = base_path / "comprehensive_trends.parquet"
        if file_path.exists():
            return pd.read_parquet(file_path)
        else:
            st.warning(
                "Datos reales no encontrados. Mostrando datos simulados para visualización UI."
            )
            return _generate_dummy_trends()
    except Exception as e:
        st.error(f"Error cargando datos: {e}")
        return pd.DataFrame()


def _generate_dummy_trends():
    np.random.seed(42)
    stations = [f"EST_{i:03d}" for i in range(1, 52)]
    return pd.DataFrame(
        {
            "station_id": stations,
            "region": ["Region_" + str(i % 17) for i in range(51)],
            "latitud": np.random.uniform(36.0, 43.0, 51),
            "longitud": np.random.uniform(-9.0, 3.0, 51),
            "altitud": np.random.uniform(0, 1500, 51),
            "tipo_entorno": np.random.choice(["Costa", "Interior"], 51),
            "distancia_costa": np.random.uniform(0, 200, 51),
            "tmax_slope": np.random.normal(0.4, 0.1, 51),
            "tmin_slope": np.random.normal(0.3, 0.1, 51),
            "tavg_slope": np.random.normal(0.35, 0.1, 51),
            "tropical_night_slope": np.random.normal(2, 1, 51),
            "p90_slope": np.random.normal(0.5, 0.2, 51),
        }
    )
