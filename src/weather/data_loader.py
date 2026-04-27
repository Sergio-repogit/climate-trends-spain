"""
Módulo de descarga y carga de datos meteorológicos.

Funciones principales:
    - download_station_data: Descarga datos horarios de una estación por ID
    - download_all_stations: Descarga datos de todas las estaciones configuradas
    - optimize_df: Optimiza tipos de datos para reducir uso de memoria
"""

from datetime import datetime

import numpy as np
import pandas as pd
from meteostat import Point, config, hourly, stations
from tqdm import tqdm

from .config import Config

config.block_large_requests = False


def optimize_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    Optimiza los tipos de datos de un DataFrame para reducir uso de memoria.

    Estrategia:
        - Enteros: uint8/16/32 o int8/16/32 según rango
        - Floats: float32 si precisión ≤3 decimales, sino float64
        - Categóricos: category si <50% valores únicos
        - Fechas: datetime64

    Args:
        df: DataFrame a optimizar

    Returns:
        DataFrame con tipos optimizados

    Examples:
        >>> df_opt = optimize_df(df_raw)
        >>> print(f"Reducción memoria: {df_raw.memory_usage().sum() / df_opt.memory_usage().sum():.2f}x")
    """
    df_opt = df.copy()

    for col in df_opt.columns:
        col_type = df_opt[col].dtype

        # Numéricos (int/float)
        if pd.api.types.is_numeric_dtype(col_type):
            if df_opt[col].isnull().all():
                continue

            col_min = df_opt[col].min()
            col_max = df_opt[col].max()
            has_nans = df_opt[col].isnull().any()

            # Enteros (solo si no tienen NaNs para usar tipos numpy estándar)
            if pd.api.types.is_integer_dtype(col_type) and not has_nans:
                # Unsigned int (solo positivos)
                if col_min >= 0:
                    if col_max <= 255:
                        df_opt[col] = df_opt[col].astype("uint8")
                    elif col_max <= 65535:
                        df_opt[col] = df_opt[col].astype("uint16")
                    else:
                        df_opt[col] = df_opt[col].astype("uint32")
                # Signed int (con negativos)
                else:
                    if col_min >= -128 and col_max <= 127:
                        df_opt[col] = df_opt[col].astype("int8")
                    elif col_min >= -32768 and col_max <= 32767:
                        df_opt[col] = df_opt[col].astype("int16")
                    else:
                        df_opt[col] = df_opt[col].astype("int32")

            # Floats o Enteros con NaNs
            else:
                # Si es float64 o integer con NaNs, intentar bajar a float32
                # Verificar si precisión ≤3 decimales para seguridad
                non_nan_vals = df_opt[col].dropna()
                if len(non_nan_vals) > 0:
                    max_diff = np.abs(non_nan_vals - np.round(non_nan_vals, 3)).max()
                    if max_diff <= 0.001:
                        df_opt[col] = df_opt[col].astype("float32")
                    else:
                        df_opt[col] = df_opt[col].astype("float64")

        # No numéricos (object, datetime, category)
        else:
            # Fechas (detectar por nombre de columna)
            if "date" in col.lower() or "timestamp" in col.lower():
                df_opt[col] = pd.to_datetime(df_opt[col])
            # Categóricos vs object
            else:
                num_unique = df_opt[col].nunique()
                if len(df_opt) > 0 and (num_unique / len(df_opt)) < 0.5:
                    df_opt[col] = df_opt[col].astype("category")
                else:
                    df_opt[col] = df_opt[col].astype("object")

    return df_opt


def download_station_data(
    station_name: str,
    station_id: str,
    lat: float,
    lon: float,
    alt: int,
    start: datetime,
    end: datetime,
) -> pd.DataFrame | None:
    """
    Descarga datos meteorológicos horarios de una estación desde Meteostat.

    METODOLOGÍA (meteostat v2.1.4):
        1. Buscar estaciones cercanas con stations.nearby(Point)
        2. Filtrar por ID específico para validar que existe
        3. Obtener lat/lon/elevation REALES de la estación encontrada
        4. Descargar datos usando station_id directamente (hourly() con string)
        5. Procesar y agregar datos diarios

    Nota: En v2.x, hourly(Point) usa interpolación geoespacial y puede devolver
    vacío si no hay proveedores geo-location. Pasar el station_id como string
    descarga directamente de la estación WMO/ICAO.

    Args:
        station_name: Nombre identificador (ej: "Madrid")
        station_id: ID de estación WMO/ICAO (ej: "08221")
        lat: Latitud aproximada (para búsqueda inicial)
        lon: Longitud aproximada (para búsqueda inicial)
        alt: Altitud aproximada (para búsqueda inicial)
        start: Fecha de inicio
        end: Fecha de fin

    Returns:
        DataFrame con datos horarios + agregaciones diarias, o None si falla
    """
    try:
        # PASO 1: Validar que la estación existe en Meteostat
        search_point = Point(lat, lon, alt)
        nearby_stations = stations.nearby(search_point)

        if nearby_stations.empty:
            print(
                f"  {station_name} ({station_id}): No se encontraron estaciones cercanas"
            )
            return None

        # PASO 2: Filtrar por ID específico
        # nearby() devuelve DF con 'id' como índice → reset para filtrar
        nearby_stations = nearby_stations.reset_index()
        station_match = nearby_stations[nearby_stations["id"] == station_id]

        if station_match.empty:
            print(f"  {station_name} ({station_id}): ID no encontrado en Meteostat")
            print(
                f"      Estaciones cercanas disponibles: {nearby_stations['id'].tolist()[:5]}"
            )
            return None

        # PASO 3: Obtener coordenadas REALES de la estación encontrada
        station_real = station_match.iloc[0]
        lat_real = station_real["latitude"]
        lon_real = station_real["longitude"]
        alt_real = station_real["elevation"]

        print(
            f"  {station_name} ({station_id}): Coords reales: ({lat_real:.4f}, {lon_real:.4f}, {alt_real}m)"
        )

        # PASO 4: Descargar datos usando station_id directamente
        data = hourly(station_id, start, end)
        df = data.fetch()

        if df is None or df.empty:
            print(f"{station_name} ({station_id}): Sin datos horarios en el período")
            return None

        # PASO 5: Procesar datos
        df = df.reset_index()
        df.rename(columns={"time": "timestamp"}, inplace=True)
        df["station_id"] = station_name

        # Calcular Tmax/Tmin/Tmean diarios desde datos horarios
        df["date"] = pd.to_datetime(df["timestamp"]).dt.date

        # Agregaciones diarias
        daily_agg = (
            df.groupby(["station_id", "date"])
            .agg({"temp": ["max", "min", "mean"]})
            .reset_index()
        )
        daily_agg.columns = ["station_id", "date", "tmax", "tmin", "tavg"]

        # Merge con datos horarios
        df = df.merge(daily_agg, on=["station_id", "date"], how="left")
        df.drop("date", axis=1, inplace=True)

        # Actualizar coordenadas a valores reales
        df["latitud_real"] = lat_real
        df["longitud_real"] = lon_real
        df["altitud_real"] = alt_real

        return df

    except Exception as e:
        print(f"Error descargando {station_name} ({station_id}): {e}")
        return None


def download_all_stations(config: Config) -> pd.DataFrame:
    """
    Descarga datos horarios de todas las estaciones configuradas.

    Proceso:
        1. Itera sobre Config.STATION_IDS y Config.STATION_METADATA
        2. Descarga cada estación con download_station_data()
        3. Añade metadatos (región, tipo_entorno, etc.)
        4. Guarda individual en RAW_DIR
        5. Combina todas en un DataFrame único
        6. Guarda metadata JSON
        7. Guarda dataset consolidado
        8. Optimiza tipos de datos

    Args:
        config: Objeto de configuración

    Returns:
        DataFrame consolidado con todas las estaciones

    Raises:
        ValueError: Si no se descarga ninguna estación
    """
    print("=" * 70)
    print("DESCARGANDO DATOS HORARIOS (2010-2025)")
    print("=" * 70)

    all_data = []
    metadata_list = []

    # Iterar sobre estaciones configuradas
    for station_name, station_id in tqdm(
        config.STATION_IDS.items(), desc="Descargando estaciones"
    ):
        # Obtener metadata
        if station_name not in config.STATION_METADATA:
            print(f"  [!] {station_name}: Sin metadata configurada")
            continue

        lat, lon, alt, region, tipo_entorno, dist_costa = config.STATION_METADATA[
            station_name
        ]

        # Descargar datos
        df = download_station_data(
            station_name=station_name,
            station_id=station_id,
            lat=lat,
            lon=lon,
            alt=alt,
            start=config.START_DATE,
            end=config.END_DATE,
        )

        if df is not None and not df.empty:
            # Añadir metadatos como columnas
            df["region"] = region
            df["latitud"] = lat
            df["longitud"] = lon
            df["altitud"] = alt
            df["tipo_entorno"] = tipo_entorno
            df["distancia_costa"] = dist_costa

            all_data.append(df)

            # Guardar individual (sin optimizar aún)
            parquet_path = config.RAW_DIR / f"{station_name}.parquet"
            df.to_parquet(parquet_path, index=False)

            metadata_list.append(
                {
                    "station_name": station_name,
                    "station_id": station_id,
                    "lat": lat,
                    "lon": lon,
                    "alt": alt,
                    "region": region,
                    "tipo_entorno": tipo_entorno,
                    "dist_costa": dist_costa,
                    "records": len(df),
                }
            )

            print(f"  [OK] {station_name}: {len(df):,} registros")
        else:
            print(f"  [X] {station_name}: Sin datos")

    if not all_data:
        raise ValueError("No se descargaron datos de ninguna estación")

    # Combinar todos los DataFrames
    combined_df = pd.concat(all_data, ignore_index=True)
    combined_df.sort_values(["station_id", "timestamp"], inplace=True)

    # --- MÉTRICAS DE ALMACENAMIENTO (BIG DATA) ---
    # 1. Tamaño original estimado en CSV (guardado temporal para medición real)
    temp_csv = config.RAW_DIR / "temp_comparison.csv"
    combined_df.to_csv(temp_csv, index=False)
    csv_size = temp_csv.stat().st_size / (1024**2)
    temp_csv.unlink()

    # 2. Optimizar tipos de datos (Reducción de memoria en RAM)
    print("\n" + "-" * 40)
    print("MÉTRICAS DE OPTIMIZACIÓN (BIG DATA)")
    print("-" * 40)

    memory_before = combined_df.memory_usage(deep=True).sum() / 1024**2
    combined_df = optimize_df(combined_df)
    memory_after = combined_df.memory_usage(deep=True).sum() / 1024**2
    mem_reduction = memory_before / memory_after

    # 3. Guardar dataset consolidado (Optimizado) y medir tamaño en disco
    combined_path = config.RAW_DIR / "all_stations_raw.parquet"
    combined_df.to_parquet(combined_path, index=False)
    parquet_size = combined_path.stat().st_size / (1024**2)

    storage_saving = (1 - (parquet_size / csv_size)) * 100

    print(
        f"  [RAM]  Memoria reducida: {memory_before:.1f} MB -> {memory_after:.1f} MB ({mem_reduction:.2f}x)"
    )
    print(f"  [DISK] Tamaño CSV est.: {csv_size:.1f} MB")
    print(f"  [DISK] Tamaño Parquet:  {parquet_size:.1f} MB")
    print(f"  [OK]   Ahorro en disco:  {storage_saving:.1f}%")
    print("-" * 40)

    # Guardar metadata
    metadata_df = pd.DataFrame(metadata_list)
    metadata_path = config.RAW_DIR / "stations_metadata.json"
    metadata_df.to_json(metadata_path, orient="records", indent=2)

    print(f"\n[OK] Dataset combinado: {len(combined_df):,} registros")
    print(f"[OK] Estaciones: {len(metadata_list)}/{len(config.STATION_IDS)}")
    print(f"[OK] Período: {config.START_DATE.date()} -> {config.END_DATE.date()}")

    return combined_df
