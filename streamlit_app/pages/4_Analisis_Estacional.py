import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import pymannkendall as mk
import streamlit as st

parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.append(str(parent_dir))

from utils.data_loader import load_comprehensive_trends  # noqa: E402
from utils.styling import load_css  # noqa: E402

st.set_page_config(page_title="Análisis Estacional", layout="wide")
load_css()


@st.cache_data
def calculate_seasonal_analysis():
    """Calcula tendencias por estación del año para todas las estaciones"""
    try:
        df = pd.read_parquet(
            "data/processed/all_stations_enriched.parquet",
            columns=["station_id", "timestamp", "temp", "tmax", "tmin", "season"],
        )
    except Exception:
        return pd.DataFrame()

    df["year"] = pd.to_datetime(df["timestamp"]).dt.year

    seasonal_agg = (
        df.groupby(["station_id", "year", "season"])
        .agg({"temp": "mean", "tmax": "mean", "tmin": "mean"})
        .reset_index()
    )

    results = []
    stations = seasonal_agg["station_id"].unique()
    seasons = ["Invierno", "Primavera", "Verano", "Otoño"]
    vars_to_analyze = {"temp": "Media", "tmax": "Máxima", "tmin": "Mínima"}

    progress_text = "Calculando distribuciones estacionales..."
    my_bar = st.progress(0, text=progress_text)

    total = len(stations)
    for i, station in enumerate(stations):
        station_data = seasonal_agg[seasonal_agg["station_id"] == station]
        for season in seasons:
            season_data = station_data[station_data["season"] == season].sort_values(
                "year"
            )
            if len(season_data) >= 5:
                for var_code, var_name in vars_to_analyze.items():
                    res = mk.original_test(season_data[var_code])
                    results.append(
                        {
                            "station_id": station,
                            "season": season,
                            "variable": var_name,
                            "slope": res.slope * 10,
                            "p_value": res.p,
                        }
                    )
        my_bar.progress((i + 1) / total)

    my_bar.empty()
    return pd.DataFrame(results)


def app():
    st.title("Análisis Estacional Comparativo")
    st.markdown("""
    Esta página permite comparar cómo afecta el calentamiento a cada estación del año y situar 
    una ciudad específica frente a la distribución nacional.
    """)

    # Cargar metadatos y tendencias
    df_meta = load_comprehensive_trends()[
        ["station_id", "region", "latitud", "longitud"]
    ]
    df_seasonal = calculate_seasonal_analysis()

    if df_seasonal.empty:
        st.error("Error al cargar datos estacionales.")
        st.stop()

    # --- FILTROS ESTÁNDAR (Como en el resto de la app) ---
    from components.filters import render_sidebar_filters

    df_filtered_meta, temp_var_code = render_sidebar_filters(df_meta)

    # Mapear la variable seleccionada en el filtro estándar a nuestro análisis
    var_mapping = {
        "tavg_slope": "Media",
        "tmax_slope": "Máxima",
        "tmin_slope": "Mínima",
    }
    selected_var = var_mapping.get(temp_var_code, "Media")

    # Estaciones seleccionadas para resaltar
    selected_stations = df_filtered_meta["station_id"].unique().tolist()

    # Preparar datos para el Boxplot (Todas las estaciones para la variable elegida)
    df_box = df_seasonal[df_seasonal["variable"] == selected_var].copy()
    df_box = df_box.merge(df_meta[["station_id", "region"]], on="station_id")

    # Ordenar estaciones
    season_order = ["Invierno", "Primavera", "Verano", "Otoño"]
    df_box["season"] = pd.Categorical(
        df_box["season"], categories=season_order, ordered=True
    )
    df_box = df_box.sort_values("season")

    # --- VISUALIZACIÓN 1: BOXPLOT NACIONAL ---
    st.subheader(f"Distribución Nacional de Tendencias: Temperatura {selected_var}")
    if selected_stations:
        st.markdown(
            f"Mostrando distribución nacional. Resaltando **{len(selected_stations)}** estaciones seleccionadas."
        )
    else:
        st.markdown(
            "Mostrando distribución nacional. (Usa los filtros del lateral para resaltar estaciones específicas)."
        )

    # Crear el Boxplot base
    fig_box = px.box(
        df_box,
        x="season",
        y="slope",
        color="season",
        points="all",
        hover_name="station_id",
        color_discrete_map={
            "Invierno": "#66c2a5",
            "Primavera": "#fc8d62",
            "Verano": "#8da0cb",
            "Otoño": "#e78ac3",
        },
        labels={"season": "Estación del Año", "slope": "Pendiente (°C/década)"},
        category_orders={"season": season_order},
    )

    # Resaltar las estaciones elegidas
    if selected_stations:
        df_selected = df_box[df_box["station_id"].isin(selected_stations)]
        fig_box.add_trace(
            go.Scatter(
                x=df_selected["season"],
                y=df_selected["slope"],
                mode="markers",
                name="Seleccionadas",
                hovertext=df_selected["station_id"],
                marker=dict(
                    color="red",
                    size=10,
                    symbol="diamond",
                    line=dict(width=1, color="white"),
                ),
                showlegend=True,
            )
        )

    fig_box.update_layout(showlegend=False, height=600)
    st.plotly_chart(fig_box, use_container_width=True)

    st.markdown("---")

    # --- VISUALIZACIÓN 2: MAPA ESPACIAL ---
    # Para el mapa, mostramos el promedio anual de esa variable para dar contexto geográfico
    st.subheader(f"Mapa General de Tendencias: Temperatura {selected_var}")

    # Agrupamos por estación meteorológica para ver la media de las 4 estaciones
    df_map = df_box.groupby(["station_id"]).agg({"slope": "mean"}).reset_index()
    df_map = df_map.merge(
        df_meta[["station_id", "latitud", "longitud"]], on="station_id"
    )

    fig_map = px.scatter_mapbox(
        df_map,
        lat="latitud",
        lon="longitud",
        color="slope",
        size=df_map["slope"].abs(),
        hover_name="station_id",  # Cambiado a station_id
        color_continuous_scale=px.colors.diverging.RdBu_r,
        range_color=[-1, 1],
        zoom=4.5,
        mapbox_style="carto-positron",
        center={"lat": 40.0, "lon": -3.5},
        labels={"slope": "°C/década"},
    )
    st.plotly_chart(fig_map, use_container_width=True)


if __name__ == "__main__":
    app()
