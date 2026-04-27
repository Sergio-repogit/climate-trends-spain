import streamlit as st


def render_sidebar_filters(df):
    """Renderiza filtros en el sidebar y devuelve el dataframe filtrado"""
    st.sidebar.title(" Filtros Climáticos")
    st.sidebar.markdown("---")

    all_stations = df["station_id"].unique().tolist() if not df.empty else []

    stations_selected = st.sidebar.multiselect(
        "Estaciones",
        options=all_stations,
        default=[],
        help="Selecciona las estaciones a analizar (deja vacío para ver todas)",
    )

    env_type = st.sidebar.radio(
        "Tipo de Entorno", options=["Todas", "Costa", "Interior"], index=0
    )

    temp_var = st.sidebar.selectbox(
        "Variable Térmica",
        options=["tavg_slope", "tmax_slope", "tmin_slope"],
        index=0,
        format_func=lambda x: x.split("_")[0].upper(),
    )

    st.sidebar.markdown("---")
    with st.sidebar.expander(" Información"):
        st.write("**Datos:** Meteostat (51 Provincias)")
        st.write("**Periodo:** 2010-2025")

    df_filtered = df.copy()
    if stations_selected:
        df_filtered = df_filtered[df_filtered["station_id"].isin(stations_selected)]
    if env_type != "Todas":
        df_filtered = df_filtered[df_filtered["tipo_entorno"] == env_type]

    return df_filtered, temp_var
