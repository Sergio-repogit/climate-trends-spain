from .analysis import (
    analyze_trends_acceleration,
    analyze_trends_comprehensive,
    calculate_derived_variables,
)
from .cleaning import process_all_stations_qc
from .config import Config
from .data_loader import download_all_stations
from .viz import generate_all_visualizations


def run_pipeline():
    """
    Ejecuta el pipeline completo de análisis climático.

    Fases:
        1. Configuración y creación de directorios
        2. Descarga de datos horarios desde Meteostat
        3. Control de calidad (3 capas + homogeneización)
        4. Cálculo de variables derivadas
        5. Análisis de tendencias (Mann-Kendall con mejoras)
        6. Análisis de aceleración (subperiodos)
        7. Generación de visualizaciones
        8. Resumen final
    """
    print("\n")
    print("+" + "=" * 68 + "+")
    print("|" + " " * 68 + "|")
    print("|" + "  ANÁLISIS DE TENDENCIAS CLIMÁTICAS EN ESPAÑA  ".center(68) + "|")
    print("|" + " " * 68 + "|")
    print("+" + "=" * 68 + "+")
    print("\n")

    # Configuración
    config = Config()
    config.create_directories()

    # ========================================================================
    # FASE 1: DESCARGA DE DATOS
    # ========================================================================
    print("\n" + "FASE 1: DESCARGA DE DATOS HORARIOS")
    print("-" * 70)

    raw_df = download_all_stations(config)

    # ========================================================================
    # FASE 2: CONTROL DE CALIDAD
    # ========================================================================
    print("\n" + "FASE 2: CONTROL DE CALIDAD (3 CAPAS)")
    print("-" * 70)

    clean_df = process_all_stations_qc(raw_df, config)

    # Guardar datos limpios
    clean_path = config.PROCESSED_DIR / "all_stations_clean.parquet"
    clean_df.to_parquet(clean_path, index=False)
    print(f"\n Datos limpios guardados en: {clean_path}")

    # ========================================================================
    # FASE 3: VARIABLES DERIVADAS
    # ========================================================================
    print("\n" + "FASE 3: VARIABLES DERIVADAS")
    print("-" * 70)

    enriched_df = calculate_derived_variables(clean_df, config)

    # Guardar datos enriquecidos
    enriched_path = config.PROCESSED_DIR / "all_stations_enriched.parquet"
    enriched_df.to_parquet(enriched_path, index=False)
    print(f"\n Datos enriquecidos guardados en: {enriched_path}")

    # ========================================================================
    # FASE 4: ANÁLISIS DE TENDENCIAS
    # ========================================================================
    print("\n" + "FASE 4: ANÁLISIS DE TENDENCIAS")
    print("-" * 70)

    results_df = analyze_trends_comprehensive(enriched_df, config)

    # ========================================================================
    # FASE 5: ANÁLISIS DE ACELERACIÓN
    # ========================================================================
    print("\n" + "FASE 5: ANÁLISIS DE ACELERACIÓN (SUBPERIODOS)")
    print("-" * 70)

    acc_df = analyze_trends_acceleration(enriched_df, config)

    # ========================================================================
    # FASE 6: VISUALIZACIONES
    # ========================================================================
    print("\n" + "FASE 6: VISUALIZACIONES")
    print("-" * 70)

    generate_all_visualizations(enriched_df, results_df, acc_df, config)

    # ========================================================================
    # FASE 7: RESUMEN FINAL
    # ========================================================================
    print("\n" + "=" * 70)
    print("ANÁLISIS COMPLETADO")
    print("=" * 70)

    print("\nResultados guardados en:")
    print(f"  - Datos procesados: {config.PROCESSED_DIR}")
    print(f"  - Resultados: {config.RESULTS_DIR}")
    print(f"  - Mapas: {config.MAPS_DIR}")
    print(f"  - Figuras: {config.FIGURES_DIR}")

    print("\nArchivos clave:")
    print("  - comprehensive_trends.parquet (47 columnas)")
    print("  - quality_control_stats.json")
    print("  - trend_map.html (mapa interactivo)")
    print("  - altitude_vs_trend.png")
    print("  - completeness_heatmap.png")
    print("  - coastal_vs_inland.png")
    print("  - extreme_hours_trends.png")
    print("  - seasonal_trends.png")

    print("\n" + "=" * 70)
    print("Análisis finalizado con éxito")
    print("=" * 70)
    print()


if __name__ == "__main__":
    run_pipeline()
