import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

# Setup paths
parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.append(str(parent_dir))

from utils.styling import load_css  # noqa: E402

st.set_page_config(page_title="Eficiencia Big Data", layout="wide")
load_css()


def app():
    st.title("Calidad de Datos y Eficiencia Big Data")

    tab1, tab2 = st.tabs(["Eficiencia Big Data (Storage)", "Control de Calidad (QC)"])

    with tab1:
        st.header("Optimización de Almacenamiento y RAM")

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Ahorro de Disco", "91.1%", "756 MB → 67 MB")
        with col2:
            st.metric("Reducción de RAM", "2.15x", "1.1 GB → 500 MB")
        with col3:
            st.metric("Formato Core", "Parquet", "Optimizado dftypes")

        st.markdown("### Comparativa de Formatos")
        df_storage = pd.DataFrame(
            {
                "Formato": [
                    "CSV (Crudo)",
                    "Parquet (Estándar)",
                    "Parquet (Optimizado)",
                ],
                "Tamaño en Disco (MB)": [756, 150, 67],
            }
        )

        col_fig, col_text = st.columns([2, 1])
        with col_fig:
            fig = px.pie(
                df_storage,
                values="Tamaño en Disco (MB)",
                names="Formato",
                title="Consumo de Disco por Formato",
                color_discrete_sequence=px.colors.sequential.RdBu,
            )
            fig.update_traces(textposition="inside", textinfo="percent+label")
            st.plotly_chart(fig, use_container_width=True)

        with col_text:
            st.markdown("### El Reto del Big Data")
            st.info(
                "El paso de un formato plano (CSV) a uno columnar y tipado (Parquet) permite procesar los millones de registros en memoria estándar sin saturar la RAM."
            )

    with tab2:
        st.header("Pipeline de Control de Calidad")
        st.markdown("""
        **Flujo de 3 Capas Estrictas:**
        1. **Filtros Físicos:** Limpieza de imposibles termodinámicos.
        2. **Detección Estadística:** Z-Score + IQR Estacionalizado para anomalías.
        3. **Consistencia Temporal:** Eliminación de bloques constantes y variaciones irreales.

        **Homogeneización:**
        - Test de Pettitt para detección de 'changepoints' estructurales.
        - Interpolación condicionada mediante Splines.
        """)

        st.success("La calidad media de los datos tras el pipeline es del 92%.")


if __name__ == "__main__":
    app()
