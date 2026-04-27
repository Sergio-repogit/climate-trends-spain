import sys
from pathlib import Path

import plotly.express as px
import streamlit as st

# Setup paths
parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.append(str(parent_dir))

from components.filters import render_sidebar_filters  # noqa: E402
from utils.data_loader import load_comprehensive_trends  # noqa: E402
from utils.styling import load_css  # noqa: E402

st.set_page_config(page_title="Dashboard General", layout="wide")
load_css()


def app():
    st.title("Dashboard General de Tendencias")
    df = load_comprehensive_trends()

    if df.empty:
        st.stop()

    df_filtered, temp_var = render_sidebar_filters(df)

    st.subheader("Distribución de Pendientes por Estación")
    st.markdown(
        "¿Cuántas estaciones se calientan a qué ritmo? Este histograma muestra la frecuencia de las distintas tendencias."
    )
    if not df_filtered.empty:
        col1, col2 = st.columns(2)
        with col1:
            fig_hist = px.histogram(
                df,
                x=temp_var,
                nbins=20,
                title=f"Frecuencia de las Tendencias de Calentamiento ({temp_var})",
                color_discrete_sequence=["#667eea"],
            )
            st.plotly_chart(fig_hist, use_container_width=True)
        with col2:
            df_sorted = df_filtered.sort_values(by=temp_var, ascending=False).head(15)
            fig_bar = px.bar(
                df_sorted,
                x=temp_var,
                y="station_id",
                orientation="h",
                title="Top Estaciones Seleccionadas (Max 15)",
                color=temp_var,
                color_continuous_scale="Reds",
            )
            fig_bar.update_layout(yaxis={"categoryorder": "total ascending"})
            st.plotly_chart(fig_bar, use_container_width=True)
            st.caption(
                f"*Nota: Si seleccionas más de 15 estaciones, el gráfico mostrará únicamente las 15 con mayor {temp_var}.*"
            )

        st.subheader("Datos Detallados")
        st.dataframe(df_filtered, use_container_width=True)

        with st.expander("Diccionario de Variables"):
            st.markdown("""
            | Variable | Descripción |
            | :--- | :--- |
            | **region** | Nombre de la ciudad o provincia de la estación. |
            | **tavg_slope** | Pendiente de la temperatura media (°C/década). |
            | **tmax_slope / tmin_slope** | Tendencia de temperaturas máximas y mínimas (°C/década). |
            | **p_value** | Significancia estadística. Valores < 0.05 indican tendencias robustas. |
            | **[var]_lower_ci / [var]_upper_ci** | Límites inferior/superior del Intervalo de Confianza (95%) mediante Bootstrap. |
            | **[var]_autocorr** | Coeficiente de autocorrelación serial (Lag-1). Mide la persistencia del dato. |
            | **extreme_heat_slope** | Tendencia en la frecuencia/intensidad de extremos cálidos. |
            | **cold_extreme_slope** | Tendencia en la frecuencia/intensidad de extremos fríos. |
            | **tropical_night_slope** | Incremento de noches con Tª mín > 20°C por década. |
            | **p90_slope** | Tendencia de los extremos de calor (Percentil 90). |
            """)


if __name__ == "__main__":
    app()
