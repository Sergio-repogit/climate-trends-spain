import sys
from pathlib import Path

import streamlit as st

parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.append(str(parent_dir))

from utils.data_loader import load_comprehensive_trends  # noqa: E402
from utils.styling import load_css  # noqa: E402

st.set_page_config(page_title="Descarga de Datos", layout="wide")
load_css()


def app():
    st.title("Centro de Descargas")

    df = load_comprehensive_trends()
    if df.empty:
        st.stop()

    st.subheader("Resultados del Análisis de Tendencias (Completos)")
    st.dataframe(df.head(100), use_container_width=True)

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

    csv = df.to_csv(index=False).encode("utf-8")

    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            label="Descargar CSV",
            data=csv,
            file_name="tendencias_clima_espana.csv",
            mime="text/csv",
        )
    with col2:
        st.markdown(
            "**Nota:** Para rendimiento Big Data en producción, se sugiere conectar directamente al archivo Parquet generado por el pipeline."
        )

    st.markdown("---")
    st.subheader("Código para reproducir resultados (Python)")
    st.code(
        """
import pandas as pd
df = pd.read_parquet('data/results/comprehensive_trends.parquet')
top_calentamiento = df.sort_values(by='tavg_slope', ascending=False).head(5)
print(top_calentamiento[['region', 'tavg_slope']])
    """,
        language="python",
    )


if __name__ == "__main__":
    app()
