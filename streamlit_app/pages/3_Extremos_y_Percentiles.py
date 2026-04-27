import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.append(str(parent_dir))

from components.filters import render_sidebar_filters  # noqa: E402
from utils.data_loader import load_comprehensive_trends  # noqa: E402
from utils.styling import load_css  # noqa: E402

st.set_page_config(page_title="Extremos Térmicos", layout="wide")
load_css()


@st.cache_data
def get_yearly_extremes():
    import pyarrow.dataset as ds

    dataset = ds.dataset(
        "data/processed/all_stations_enriched.parquet", format="parquet"
    )
    table = dataset.to_table(
        columns=[
            "station_id",
            "timestamp",
            "is_tropical_night",
            "is_extreme_heat",
            "is_cold_extreme",
        ]
    )
    df = table.to_pandas()

    # Convertir timestamp a fecha (sin hora) para agrupar por días naturales
    df["date"] = pd.to_datetime(df["timestamp"]).dt.date
    df["year"] = pd.to_datetime(df["timestamp"]).dt.year

    # IMPORTANTE: Colapsamos las horas en días.
    # Si en un día de 24h hubo al menos una hora marcada como extremo, el día cuenta como 1.
    daily_flags = (
        df.groupby(["station_id", "date", "year"])[
            ["is_tropical_night", "is_extreme_heat", "is_cold_extreme"]
        ]
        .any()
        .astype(int)
        .reset_index()
    )

    # Ahora sumamos los días por año
    yearly_counts = (
        daily_flags.groupby(["station_id", "year"])[
            ["is_tropical_night", "is_extreme_heat", "is_cold_extreme"]
        ]
        .sum()
        .reset_index()
    )
    return yearly_counts


def app():
    st.title("Análisis de Extremos Térmicos")
    st.markdown(
        "Evolución anual de las noches tropicales y tendencias en los días de calor o frío extremo."
    )

    df_trends = load_comprehensive_trends()
    if df_trends.empty:
        st.stop()

    df_filtered, temp_var = render_sidebar_filters(df_trends)
    selected_stations = sorted(df_filtered["station_id"].unique().tolist())
    n_stations = len(selected_stations)

    # Generar paleta dinámica de alto contraste (Alphabet + Light24)
    if n_stations <= 26:
        color_seq = px.colors.qualitative.Alphabet
    else:
        # Combinamos dos paletas grandes para cubrir las 51 estaciones sin repeticiones
        color_seq = px.colors.qualitative.Alphabet + px.colors.qualitative.Light24

    # Carga y procesado agrupado de eventos extremos
    yearly_extremes = get_yearly_extremes()
    yearly_filtered = yearly_extremes[
        yearly_extremes["station_id"].isin(selected_stations)
    ]

    st.subheader("Evolución Anual de Noches Tropicales")
    st.markdown(
        "Número total de noches al año donde la temperatura mínima no bajó de los 20°C."
    )
    if not yearly_filtered.empty:
        fig1 = px.bar(
            yearly_filtered,
            x="year",
            y="is_tropical_night",
            color="station_id",
            title="Noches Tropicales por Año (Barras Apiladas)",
            labels={
                "year": "Año",
                "is_tropical_night": "Nº Noches Tropicales",
                "station_id": "Estación",
            },
            barmode="stack",
            color_discrete_sequence=color_seq,
        )
        fig1.update_layout(xaxis=dict(tickmode="linear", dtick=1))
        st.plotly_chart(fig1, use_container_width=True)
    else:
        st.info("No hay datos de noches tropicales para las estaciones seleccionadas.")

    st.markdown("---")
    st.subheader("Evolución de Extremos por Calor")
    st.markdown(
        "Número de días al año considerados como de calor extremo (Temperatura máxima > 35°C)."
    )
    if not yearly_filtered.empty:
        fig2 = px.bar(
            yearly_filtered,
            x="year",
            y="is_extreme_heat",
            color="station_id",
            title="Días de Calor Extremo por Año",
            labels={
                "year": "Año",
                "is_extreme_heat": "Nº Días Calor Extremo",
                "station_id": "Estación",
            },
            barmode="stack",
            color_discrete_sequence=color_seq,
        )
        fig2.update_layout(xaxis=dict(tickmode="linear", dtick=1))
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown("---")
    st.subheader("Evolución de Extremos por Frío")
    st.markdown(
        "Número de días al año considerados como de frío extremo o heladas (Temperatura mínima < 0°C)."
    )
    if not yearly_filtered.empty:
        fig3 = px.bar(
            yearly_filtered,
            x="year",
            y="is_cold_extreme",
            color="station_id",
            title="Días de Frío Extremo por Año",
            labels={
                "year": "Año",
                "is_cold_extreme": "Nº Días Frío Extremo",
                "station_id": "Estación",
            },
            barmode="stack",
            color_discrete_sequence=color_seq,
        )
        fig3.update_layout(xaxis=dict(tickmode="linear", dtick=1))
        st.plotly_chart(fig3, use_container_width=True)

    st.markdown("---")
    st.subheader("Ranking: Incremento de Noches Tropicales")
    top_tropical = df_filtered.sort_values(
        by="tropical_night_slope", ascending=False
    ).head(15)
    fig_bar = px.bar(
        top_tropical,
        x="tropical_night_slope",
        y="station_id",
        orientation="h",
        title="Estaciones con mayor crecimiento (Horas extra / década)",
        labels={
            "tropical_night_slope": "Horas extra / década",
            "station_id": "Estación",
        },
        color="tropical_night_slope",
        color_continuous_scale="YlOrRd",
    )
    fig_bar.update_layout(yaxis={"categoryorder": "total ascending"})
    st.plotly_chart(fig_bar, use_container_width=True)


if __name__ == "__main__":
    app()
