import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.append(str(parent_dir))

from utils.data_loader import load_comprehensive_trends  # noqa: E402
from utils.styling import load_css  # noqa: E402

st.set_page_config(page_title="Análisis Espacial", layout="wide")
load_css()


def app():
    st.title("Análisis Espacial: Altitud y Costa")
    st.markdown("Estudio de la variación de tendencias según factores geográficos.")

    df = load_comprehensive_trends()

    if df.empty:
        st.stop()

    # Selector único en el sidebar para esta página
    st.sidebar.title("Configuración")
    temp_var = st.sidebar.selectbox(
        "Variable Térmica",
        options=["tavg_slope", "tmax_slope", "tmin_slope"],
        index=0,
        format_func=lambda x: {
            "tavg_slope": "Temperatura Media",
            "tmax_slope": "Temperatura Máxima",
            "tmin_slope": "Temperatura Mínima",
        }.get(x),
    )
    st.sidebar.markdown("---")

    # Mapeo de nombres para legibilidad en los gráficos
    var_names = {
        "tavg_slope": "Temp. Media",
        "tmax_slope": "Temp. Máxima",
        "tmin_slope": "Temp. Mínima",
    }
    pretty_name = var_names.get(temp_var, temp_var)

    # Usamos el dataframe completo (sin filtrar por estaciones)
    df_filtered = df.copy()

    tab1, tab2 = st.tabs(["Efecto Altitud", "Costa vs Interior"])

    with tab1:
        st.subheader(f"Elevation-Dependent Warming ({pretty_name})")
        st.markdown(
            "Correlación entre la altitud de la estación y la pendiente de calentamiento."
        )
        if "altitud" in df_filtered.columns:
            # Crear rangos de altitud cada 300m (basado en el dataset original para consistencia)
            bins = range(0, 3300, 300)
            labels = [f"{i}-{i + 300}m" for i in bins[:-1]]
            df_filtered["Rango Altitud"] = pd.cut(
                df_filtered["altitud"], bins=bins, labels=labels
            )

            fig1 = px.box(
                df_filtered,
                x="Rango Altitud",
                y=temp_var,
                points="all",
                hover_name="station_id",
                color="Rango Altitud",
                labels={
                    "Rango Altitud": "Rango de Altitud",
                    temp_var: f"Pendiente {pretty_name} (°C/década)",
                },
                title=f"Tendencia de {pretty_name} por Tramos de Altitud",
            )
            fig1.update_xaxes(categoryorder="array", categoryarray=labels)
            st.plotly_chart(fig1, use_container_width=True)
        else:
            st.warning("No se encontraron datos de altitud en el dataset.")

    with tab2:
        st.subheader(f"Comparativa Costa vs Interior ({pretty_name})")
        st.markdown("Diferencias en la aceleración térmica según la proximidad al mar.")
        if "tipo_entorno" in df_filtered.columns:
            fig2 = px.box(
                df_filtered,
                x="tipo_entorno",
                y=temp_var,
                color="tipo_entorno",
                points="all",
                hover_name="station_id",
                labels={
                    "tipo_entorno": "Ubicación",
                    temp_var: f"Pendiente {pretty_name} (°C/década)",
                },
                title=f"Impacto de la Costa en la Tendencia de {pretty_name}",
            )
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.warning(
                "No se encontraron datos de tipo de entorno (Costa/Interior) en el dataset."
            )


if __name__ == "__main__":
    app()
