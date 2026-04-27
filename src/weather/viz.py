"""
Módulo de visualizaciones para análisis climático.

Funciones principales:
    - create_trend_map: Mapa interactivo Folium
    - create_altitude_vs_trend_plot: Elevation-Dependent Warming
    - create_completeness_heatmap: Matriz de calidad de datos
    - create_coastal_vs_inland_comparison: Costa vs Interior
    - create_extreme_hours_trends: Tendencias de extremos térmicos
    - create_seasonal_trends: Tendencias por estación del año
"""

import folium
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from scipy.stats import mannwhitneyu, pearsonr

from .config import Config

# ============================================================================
# MAPA INTERACTIVO FOLIUM
# ============================================================================


def create_trend_map(results_df: pd.DataFrame, config: Config) -> None:
    """
    Crea mapa interactivo Folium con tendencias por estación.

    Características:
        - Marcadores color-coded según magnitud de tendencia
        - Popups con información detallada
        - Clusters para mejor visualización
        - Escala de referencia

    Args:
        results_df: DataFrame con resultados de tendencias
        config: Configuración

    Outputs:
        Guarda mapa HTML en MAPS_DIR/trend_map.html
    """
    print("\n  Creando mapa interactivo de tendencias...")

    # Centro de España
    center_lat = 40.4168
    center_lon = -3.7038

    # Crear mapa base
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=6,
        tiles="OpenStreetMap",
    )

    # Función para determinar color según tendencia
    def get_color(slope):
        if pd.isna(slope):
            return "gray"
        elif slope > 0.5:
            return "red"  # Calentamiento fuerte
        elif slope > 0.2:
            return "orange"  # Calentamiento moderado
        elif slope > -0.2:
            return "yellow"  # Neutro
        elif slope > -0.5:
            return "lightblue"  # Enfriamiento moderado
        else:
            return "blue"  # Enfriamiento fuerte

    # Añadir marcadores
    for _, row in results_df.iterrows():
        # Usar tavg_slope como principal
        slope = row.get("tavg_slope", np.nan)
        p_value = row.get("tavg_p_value", np.nan)

        # Popup con información
        popup_html = f"""
        <div style="font-family: Arial; font-size: 12px; width: 300px;">
            <h4 style="margin: 0 0 10px 0;">{row["station_id"].replace("_", " ")}</h4>
            <table style="width: 100%; border-collapse: collapse;">
                <tr style="background-color: #f0f0f0;">
                    <td style="padding: 5px;"><b>Región:</b></td>
                    <td style="padding: 5px;">{row["region"]}</td>
                </tr>
                <tr>
                    <td style="padding: 5px;"><b>Altitud:</b></td>
                    <td style="padding: 5px;">{row["altitud"]} m</td>
                </tr>
                <tr style="background-color: #f0f0f0;">
                    <td style="padding: 5px;"><b>Tipo:</b></td>
                    <td style="padding: 5px;">{row["tipo_entorno"]}</td>
                </tr>
                <tr>
                    <td style="padding: 5px;"><b>Dist. Costa:</b></td>
                    <td style="padding: 5px;">{row["distancia_costa"]} km</td>
                </tr>
                <tr style="background-color: #ffe0e0;">
                    <td style="padding: 5px;"><b>Tmax:</b></td>
                    <td style="padding: 5px;">{row.get("tmax_slope", np.nan):.3f} °C/década</td>
                </tr>
                <tr style="background-color: #e0e0ff;">
                    <td style="padding: 5px;"><b>Tmin:</b></td>
                    <td style="padding: 5px;">{row.get("tmin_slope", np.nan):.3f} °C/década</td>
                </tr>
                <tr style="background-color: #e0ffe0;">
                    <td style="padding: 5px;"><b>Tavg:</b></td>
                    <td style="padding: 5px;">{slope:.3f} °C/década</td>
                </tr>
                <tr>
                    <td style="padding: 5px;"><b>P-value:</b></td>
                    <td style="padding: 5px;">{p_value:.4f}</td>
                </tr>
            </table>
        </div>
        """

        folium.CircleMarker(
            location=[row["latitud"], row["longitud"]],
            radius=8,
            popup=folium.Popup(popup_html, max_width=350),
            color="black",
            fillColor=get_color(slope),
            fillOpacity=0.7,
            weight=1,
        ).add_to(m)

    # Añadir leyenda
    legend_html = """
    <div style="position: fixed;
                top: 10px; right: 10px; width: 180px; height: 180px;
                background-color: white; border:2px solid grey; z-index:9999;
                font-size:12px; padding: 10px;">
        <h4 style="margin: 0 0 10px 0;">Tendencia (°C/década)</h4>
        <p><span style="color: red;">●</span> > 0.5 (Calentamiento fuerte)</p>
        <p><span style="color: orange;">●</span> 0.2 - 0.5 (Moderado)</p>
        <p><span style="color: yellow;">●</span> -0.2 - 0.2 (Neutro)</p>
        <p><span style="color: lightblue;">●</span> -0.5 - -0.2 (Enfriamiento moderado)</p>
        <p><span style="color: blue;">●</span> < -0.5 (Enfriamiento fuerte)</p>
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))

    # Guardar
    output_path = config.MAPS_DIR / "trend_map.html"
    m.save(str(output_path))

    print(f"   Guardado: {output_path}")


# ============================================================================
# GRÁFICO ALTITUD VS TENDENCIA
# ============================================================================


def create_altitude_vs_trend_plot(results_df: pd.DataFrame, config: Config) -> None:
    """
    Gráfico de dispersión: Altitud vs Tendencia.

    Detecta fenómeno de Elevation-Dependent Warming: ¿Se calientan más
    las montañas que las zonas de baja altitud?

    Args:
        results_df: DataFrame con resultados
        config: Configuración

    Outputs:
        altitude_vs_trend.png (3 paneles con R² y p-value)
    """
    print("\n  Creando gráfico Altitud vs Tendencia...")

    fig, axes = plt.subplots(1, 3, figsize=(18, 5))

    for idx, (temp_var, ax) in enumerate(zip(["tmax", "tmin", "tavg"], axes)):
        col = f"{temp_var}_slope"
        if col in results_df.columns:
            # Regression plot con IC
            sns.regplot(
                data=results_df,
                x="altitud",
                y=col,
                ax=ax,
                scatter_kws={"s": 100, "alpha": 0.6},
                line_kws={"color": "red", "linewidth": 2},
            )

            # Calcular R²
            valid_data = results_df[["altitud", col]].dropna()
            if len(valid_data) > 2:
                r, p_val = pearsonr(valid_data["altitud"], valid_data[col])
                r2 = r**2

                ax.text(
                    0.05,
                    0.95,
                    f"R² = {r2:.3f}\np = {p_val:.4f}",
                    transform=ax.transAxes,
                    verticalalignment="top",
                    bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.5),
                )

            ax.set_xlabel("Altitud (m)", fontsize=12)
            ax.set_ylabel(f"Tendencia {temp_var.upper()} (°C/década)", fontsize=12)
            ax.set_title(
                f"{temp_var.upper()}: Elevation-Dependent Warming",
                fontsize=13,
                fontweight="bold",
            )
            ax.grid(alpha=0.3)
            ax.axhline(y=0, color="black", linestyle="--", linewidth=0.8)

    plt.tight_layout()

    path = config.FIGURES_DIR / "altitude_vs_trend.png"
    plt.savefig(path, dpi=300, bbox_inches="tight")
    plt.close()

    print(f"     Guardado: {path}")


# ============================================================================
# MAPA DE CALOR COMPLETENESS
# ============================================================================


def create_completeness_heatmap(df: pd.DataFrame, config: Config) -> None:
    """
    Mapa de calor de completeness de datos (estaciones × años).

    Justificación: Transparencia en la calidad de datos. Muestra visualmente
    dónde están los gaps.

    Args:
        df: DataFrame con datos procesados
        config: Configuración

    Outputs:
        completeness_heatmap.png
    """
    print("\n  Creando mapa de calor de completeness...")

    # Calcular completeness por estación y año
    df_temp = df.copy()
    df_temp["timestamp"] = pd.to_datetime(df_temp["timestamp"])
    df_temp["year"] = df_temp["timestamp"].dt.year

    # Matriz: filas = estaciones, columnas = años
    completeness_matrix = []
    stations = sorted(df_temp["station_id"].unique())
    years = sorted(df_temp["year"].unique())

    for station in stations:
        station_data = df_temp[df_temp["station_id"] == station]
        completeness_row = []

        for year in years:
            year_data = station_data[station_data["year"] == year]
            if len(year_data) > 0:
                completeness = year_data["temp"].notna().mean()
            else:
                completeness = 0.0
            completeness_row.append(completeness)

        completeness_matrix.append(completeness_row)

    # Crear heatmap
    fig, ax = plt.subplots(figsize=(16, 10))

    sns.heatmap(
        completeness_matrix,
        xticklabels=years,
        yticklabels=stations,
        cmap="RdYlGn",
        vmin=0,
        vmax=1,
        cbar_kws={"label": "Completitud de Datos"},
        ax=ax,
        linewidths=0.5,
        linecolor="gray",
    )

    ax.set_xlabel("Año", fontsize=12)
    ax.set_ylabel("Estación", fontsize=12)
    ax.set_title(
        "Mapa de Calor: Completitud de Datos por Estación y Año",
        fontsize=14,
        fontweight="bold",
    )

    plt.tight_layout()

    path = config.FIGURES_DIR / "completeness_heatmap.png"
    plt.savefig(path, dpi=300, bbox_inches="tight")
    plt.close()

    print(f"     Guardado: {path}")


# ============================================================================
# COMPARACIÓN COSTA VS INTERIOR
# ============================================================================


def create_coastal_vs_inland_comparison(
    results_df: pd.DataFrame, config: Config
) -> None:
    """
    Comparación de tendencias: Costa vs Interior.

    Pregunta: ¿El mar actúa como regulador térmico frenando el calentamiento?

    Args:
        results_df: DataFrame con resultados
        config: Configuración

    Outputs:
        coastal_vs_inland.png (3 paneles con Mann-Whitney U test)
    """
    print("\n  Creando comparación Costa vs Interior...")

    fig, axes = plt.subplots(1, 3, figsize=(18, 5))

    for idx, (temp_var, ax) in enumerate(zip(["tmax", "tmin", "tavg"], axes)):
        col = f"{temp_var}_slope"
        if col in results_df.columns:
            # Box plot por tipo de entorno
            sns.boxplot(
                data=results_df,
                x="tipo_entorno",
                y=col,
                palette={"Costa": "lightblue", "Interior": "coral"},
                ax=ax,
            )

            # Añadir puntos individuales
            sns.stripplot(
                data=results_df,
                x="tipo_entorno",
                y=col,
                color="black",
                alpha=0.5,
                size=6,
                ax=ax,
            )

            ax.axhline(y=0, color="black", linestyle="--", linewidth=0.8)
            ax.set_xlabel("Tipo de Entorno", fontsize=12)
            ax.set_ylabel(f"Tendencia {temp_var.upper()} (°C/década)", fontsize=12)
            ax.set_title(
                f"{temp_var.upper()}: Costa vs Interior",
                fontsize=13,
                fontweight="bold",
            )
            ax.grid(axis="y", alpha=0.3)

            # Test estadístico
            costa_data = results_df[results_df["tipo_entorno"] == "Costa"][col].dropna()
            interior_data = results_df[results_df["tipo_entorno"] == "Interior"][
                col
            ].dropna()

            if len(costa_data) > 0 and len(interior_data) > 0:
                stat, p_val = mannwhitneyu(
                    costa_data, interior_data, alternative="two-sided"
                )

                ax.text(
                    0.5,
                    0.95,
                    f"Mann-Whitney U p = {p_val:.4f}",
                    transform=ax.transAxes,
                    horizontalalignment="center",
                    verticalalignment="top",
                    bbox=dict(boxstyle="round", facecolor="yellow", alpha=0.5),
                )

    plt.tight_layout()

    path = config.FIGURES_DIR / "coastal_vs_inland.png"
    plt.savefig(path, dpi=300, bbox_inches="tight")
    plt.close()

    print(f"     Guardado: {path}")


# ============================================================================
# TENDENCIAS DE EXTREMOS TÉRMICOS
# ============================================================================


def create_extreme_hours_trends(
    df: pd.DataFrame, results_df: pd.DataFrame, config: Config
) -> None:
    """
    Tendencias de horas de estrés térmico.

    Impacto: "Las horas de calor extremo aumentaron un 20%" es más
    significativo que "la media subió 0.3°C".

    Args:
        df: DataFrame completo
        results_df: DataFrame con resultados
        config: Configuración

    Outputs:
        extreme_hours_trends.png (3 paneles)
    """
    print("\n  Creando gráficos de extremos térmicos...")

    fig, axes = plt.subplots(1, 3, figsize=(18, 5))

    extremes = [
        ("tropical_night", "Noches Tropicales (T>20°C nocturno)", "orangered"),
        ("extreme_heat", "Horas de Calor Extremo (T>35°C)", "crimson"),
        ("cold_extreme", "Horas de Frío Extremo (T<0°C)", "steelblue"),
    ]

    for (extreme_type, title, color), ax in zip(extremes, axes):
        col = f"{extreme_type}_slope"

        if col in results_df.columns:
            # Ordenar por magnitud de cambio
            sorted_df = results_df.sort_values(col, ascending=False)

            # Bar plot horizontal
            ax.barh(sorted_df["station_id"], sorted_df[col], color=color, alpha=0.7)

            ax.axvline(x=0, color="black", linestyle="-", linewidth=1)
            ax.set_xlabel("Cambio (horas/año por década)", fontsize=11)
            ax.set_title(title, fontsize=12, fontweight="bold")
            ax.grid(axis="x", alpha=0.3)

            # Marcar significancia estadística
            p_col = f"{extreme_type}_p_value"
            if p_col in sorted_df.columns:
                significant = sorted_df[sorted_df[p_col] < config.SIGNIFICANCE_LEVEL]
                if len(significant) > 0:
                    # Encontrar posiciones y_positions
                    y_positions = []
                    for idx in significant.index:
                        y_pos = list(sorted_df.index).index(idx)
                        y_positions.append(y_pos)

                    ax.scatter(
                        [sorted_df.loc[idx, col] for idx in significant.index],
                        y_positions,
                        marker="*",
                        s=200,
                        color="gold",
                        edgecolors="black",
                        label="Significativo (p<0.05)",
                        zorder=10,
                    )
                    ax.legend()

    plt.tight_layout()

    path = config.FIGURES_DIR / "extreme_hours_trends.png"
    plt.savefig(path, dpi=300, bbox_inches="tight")
    plt.close()

    print(f"     Guardado: {path}")


# ============================================================================
# TENDENCIAS POR ESTACIÓN DEL AÑO
# ============================================================================


def create_seasonal_trends(df: pd.DataFrame, config: Config) -> None:
    """
    Análisis de tendencias por estación del año (Invierno, Primavera, etc.).

    Pregunta: ¿Se calienta más el verano o el invierno?

    Args:
        df: DataFrame con datos enriquecidos
        config: Configuración

    Outputs:
        seasonal_trends.png
    """
    print("\n  Creando gráficos de tendencias estacionales...")

    from .analysis import mann_kendall_with_confidence

    # Calcular tendencias por estación del año
    seasonal_results = []

    for station_id in df["station_id"].unique():
        station_data = df[df["station_id"] == station_id]

        for season in ["Invierno", "Primavera", "Verano", "Otoño"]:
            season_data = station_data[station_data["season"] == season].copy()

            if len(season_data) > 0:
                # Medias anuales por estación
                season_data["timestamp"] = pd.to_datetime(season_data["timestamp"])
                season_data["year"] = season_data["timestamp"].dt.year

                annual_means = season_data.groupby("year")["temp"].mean()

                if len(annual_means) >= 3:
                    mk_result = mann_kendall_with_confidence(
                        annual_means, config.CONFIDENCE_LEVEL
                    )

                    seasonal_results.append(
                        {
                            "station_id": station_id,
                            "season": season,
                            "slope": mk_result["sens_slope_per_decade"],
                            "p_value": mk_result["p_value"],
                        }
                    )

    seasonal_df = pd.DataFrame(seasonal_results)

    if len(seasonal_df) > 0:
        # Box plot por estación
        fig, ax = plt.subplots(figsize=(12, 6))

        sns.boxplot(
            data=seasonal_df,
            x="season",
            y="slope",
            order=["Invierno", "Primavera", "Verano", "Otoño"],
            palette="Set2",
            ax=ax,
        )

        sns.stripplot(
            data=seasonal_df,
            x="season",
            y="slope",
            order=["Invierno", "Primavera", "Verano", "Otoño"],
            color="black",
            alpha=0.3,
            ax=ax,
        )

        ax.axhline(y=0, color="black", linestyle="--", linewidth=0.8)
        ax.set_xlabel("Estación del Año", fontsize=12)
        ax.set_ylabel("Tendencia (°C/década)", fontsize=12)
        ax.set_title(
            "Tendencias de Temperatura por Estación del Año",
            fontsize=14,
            fontweight="bold",
        )
        ax.grid(axis="y", alpha=0.3)

        plt.tight_layout()

        path = config.FIGURES_DIR / "seasonal_trends.png"
        plt.savefig(path, dpi=300, bbox_inches="tight")
        plt.close()

        print(f"     Guardado: {path}")


# ============================================================================
# GRÁFICO DE ACELERACIÓN
# ============================================================================


def create_acceleration_plot(acc_df: pd.DataFrame, config: Config) -> None:
    """
    Crea un gráfico de barras agrupadas mostrando la aceleración por subperiodos.

    Muestra Tmax, Tmin y Tavg en paneles separados para comparar la evolución
    de la pendiente entre los subperiodos definidos.

    Args:
        acc_df: DataFrame con resultados de aceleración
        config: Configuración
    """
    print("\n  Creando gráfico de aceleración por subperiodos...")

    if acc_df.empty:
        print("  [!] No hay datos de aceleración para graficar")
        return

    # Preparar datos para seaborn (formato largo/tidy)
    plot_df = acc_df.melt(
        id_vars=["station_id", "periodo"],
        value_vars=["tmax_slope", "tmin_slope", "tavg_slope"],
        var_name="temp_type",
        value_name="slope",
    )

    # Limpiar nombres de temperatura para el título
    plot_df["temp_type"] = plot_df["temp_type"].str.replace("_slope", "").str.upper()

    # Configurar estilo visual
    sns.set_theme(style="whitegrid")

    # Crear gráfico de facetas (un panel por cada tipo de temperatura)
    g = sns.catplot(
        data=plot_df,
        kind="bar",
        x="station_id",
        y="slope",
        hue="periodo",
        col="temp_type",
        col_wrap=1,
        palette="magma",
        alpha=0.8,
        height=5,
        aspect=3,
    )

    g.set_axis_labels("Estación", "Pendiente (°C/década)")
    g.set_titles("Evolución de la Tendencia: {col_name}")

    # Ajustes finales en cada panel
    for ax in g.axes.flat:
        # Línea de referencia en cero
        ax.axhline(0, color="black", linestyle="-", linewidth=0.8)
        # Rotar nombres de estaciones para legibilidad
        plt.setp(ax.get_xticklabels(), rotation=45, ha="right")

    path = config.FIGURES_DIR / "acceleration_comparison.png"
    g.savefig(path, dpi=300, bbox_inches="tight")
    plt.close()

    print(f"     Guardado: {path}")


# ============================================================================
# GENERADOR DE TODAS LAS VISUALIZACIONES
# ============================================================================


def generate_all_visualizations(
    df: pd.DataFrame, results_df: pd.DataFrame, acc_df: pd.DataFrame, config: Config
) -> None:
    """
    Genera todas las visualizaciones del proyecto.

    Args:
        df: DataFrame con datos enriquecidos
        results_df: DataFrame con resultados de tendencias
        acc_df: DataFrame con resultados de aceleración
        config: Configuración
    """
    print("\n" + "=" * 70)
    print("GENERANDO VISUALIZACIONES")
    print("=" * 70)

    create_trend_map(results_df, config)
    create_altitude_vs_trend_plot(results_df, config)
    create_completeness_heatmap(df, config)
    create_coastal_vs_inland_comparison(results_df, config)
    create_extreme_hours_trends(df, results_df, config)
    create_seasonal_trends(df, config)
    create_acceleration_plot(acc_df, config)

    print("\n Todas las visualizaciones generadas")
