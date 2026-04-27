"""
Configuración centralizada del proyecto de análisis climático.

Este módulo contiene todas las constantes, parámetros y configuraciones
utilizadas en el análisis de tendencias climáticas en España.
"""

from datetime import datetime
from pathlib import Path


class Config:
    """Configuración centralizada del proyecto."""

    # ========================================================================
    # PERÍODO DE ANÁLISIS
    # ========================================================================
    START_DATE = datetime(2010, 1, 1)
    END_DATE = datetime(2025, 12, 31)

    # Subperíodos para análisis de aceleración
    SUBPERIODS: list[tuple[datetime, datetime, str]] = [
        (datetime(2010, 1, 1), datetime(2015, 12, 31), "2010-2015"),
        (datetime(2015, 1, 1), datetime(2020, 12, 31), "2015-2020"),
        (datetime(2020, 1, 1), datetime(2025, 12, 31), "2020-2025"),
    ]

    # ========================================================================
    # CONTROL DE CALIDAD
    # ========================================================================

    # Completitud de datos
    MIN_COMPLETENESS = 0.70  # 70% mínimo de datos completos

    # Interpolación de gaps
    MAX_GAP_HOURS_SHORT = 6  # Spline para gaps ≤6 horas
    MAX_GAP_HOURS_LONG = 72  # Condicionada para gaps 6-72 horas
    LONG_GAP_THRESHOLD = 0.075  # 7.5% - umbral para aplicar interpolación condicionada

    # Capa 1: Rangos físicos (hard limits)
    TEMP_MIN_PHYSICAL = -35.0  # °C
    TEMP_MAX_PHYSICAL = 50.0  # °C
    HUMIDITY_MIN = 0.0  # %
    HUMIDITY_MAX = 100.0  # %
    PRESSURE_MIN = 900.0  # hPa
    PRESSURE_MAX = 1050.0  # hPa

    # Capa 2: Detección estadística estacionalizada
    IQR_MULTIPLIER = 3.0  # Outliers extremos
    Z_SCORE_THRESHOLD = 4.0  # Umbral conservador

    # Capa 3: Consistencia temporal
    MAX_TEMP_CHANGE_PER_HOUR = 5.0  # °C
    CONSTANT_VALUE_HOURS = 24  # Horas

    # Homogeneización (Pettitt Test)
    PETTITT_SIGNIFICANCE = 0.05  # Nivel de significancia para detectar cambios

    # ========================================================================
    # ANÁLISIS DE EXTREMOS TÉRMICOS
    # ========================================================================
    TROPICAL_NIGHT_THRESHOLD = 20.0  # °C - Noches tropicales
    EXTREME_HEAT_THRESHOLD = 35.0  # °C - Calor extremo
    COLD_EXTREME_THRESHOLD = 0.0  # °C - Frío extremo

    # ========================================================================
    # PARÁMETROS ESTADÍSTICOS
    # ========================================================================
    SIGNIFICANCE_LEVEL = 0.05  # α para Mann-Kendall
    CONFIDENCE_LEVEL = 0.95  # IC para Sen's slope

    # ========================================================================
    # DIRECTORIOS
    # ========================================================================
    BASE_DIR = Path(__file__).parent.parent.parent  # Raíz del proyecto
    DATA_DIR = BASE_DIR / "data"
    RAW_DIR = DATA_DIR / "raw"
    PROCESSED_DIR = DATA_DIR / "processed"
    RESULTS_DIR = DATA_DIR / "results"
    MAPS_DIR = RESULTS_DIR / "maps"
    FIGURES_DIR = RESULTS_DIR / "figures"

    # ========================================================================
    # ESTACIONES METEOROLÓGICAS
    # ========================================================================

    # IDs de estaciones Meteostat (códigos WMO/ICAO)
    STATION_IDS = {
        "A_Coruna": "08002",
        "Santander": "08021",
        "Bilbao": "08025",
        "San_Sebastian": "08029",
        "Leon": "08055",
        "Burgos": "08075",
        "Valladolid": "08140",
        "Zaragoza": "08160",
        "Barcelona": "08181",
        "Girona": "08184",
        "Madrid": "08221",
        "Ciudad_Real": "LERL0",
        "Madrid_Torrejon": "08227",
        "Valencia": "08284",
        "Alicante": "08360",
        "Murcia": "08429",
        "Malaga": "08482",
        "Sevilla": "08391",
        "Granada": "08419",
        "Almeria": "08487",
        "Palma_Mallorca": "08306",
        "Ibiza": "08373",
        "Cordoba": "08410",
        "Jaen": "08417",
        "Caceres": "08261",
        "Badajoz": "08330",
        "Santiago_de_Compostela": "08042",
        "Pontevedra": "08044",
        "Vigo": "08045",
        "Ourense": "08048",
        "Gijon": "08014",
        "Oviedo": "08015",
        "Albacete": "08280",
        "Avila": "08210",
        "Cadiz": "08449",
        "Castellon": "08286",
        "Cuenca": "08231",
        "Huesca": "LEHC0",
        "Huelva": "08383",
        "Lleida": "LEDA0",
        "Logrono": "08084",
        "Lugo": "08008",
        "Palencia": "08141",
        "Pamplona": "08085",
        "Salamanca": "08202",
        "Segovia": "08213",
        "Soria": "08148",
        "Tarragona": "08175",
        "Teruel": "08235",
        "Toledo": "08272",
        "Vitoria": "08080",
    }

    # Metadata de estaciones
    # Formato: {station_name: (lat, lon, alt, region, tipo_entorno, dist_costa_km)}
    STATION_METADATA = {
        "A_Coruna": (43.3623, -8.4115, 67, "Galicia", "Costa", 2),
        "Santander": (43.4623, -3.8099, 65, "Cantabria", "Costa", 1),
        "Bilbao": (43.3014, -2.9106, 42, "País Vasco", "Costa", 8),
        "San_Sebastian": (43.3183, -1.9812, 5, "País Vasco", "Costa", 0),
        "Leon": (42.5987, -5.5671, 838, "Castilla y León", "Interior", 180),
        "Burgos": (42.3439, -3.6969, 856, "Castilla y León", "Interior", 200),
        "Valladolid": (41.6521, -4.7246, 694, "Castilla y León", "Interior", 250),
        "Zaragoza": (41.6488, -0.8891, 247, "Aragón", "Interior", 280),
        "Barcelona": (41.3874, 2.1686, 95, "Cataluña", "Costa", 5),
        "Girona": (41.9794, 2.8214, 70, "Cataluña", "Interior", 25),
        "Madrid": (40.4168, -3.7038, 667, "Madrid", "Interior", 300),
        "Ciudad_Real": (38.9833, -3.9167, 628, "Castilla-La Mancha", "Interior", 320),
        "Madrid_Torrejon": (40.4967, -3.4458, 607, "Madrid", "Interior", 280),
        "Valencia": (39.4699, -0.3763, 16, "Comunidad Valenciana", "Costa", 1),
        "Alicante": (38.3452, -0.4815, 7, "Comunidad Valenciana", "Costa", 0),
        "Murcia": (37.9922, -1.1307, 64, "Murcia", "Interior", 40),
        "Malaga": (36.7213, -4.4214, 7, "Andalucía", "Costa", 1),
        "Sevilla": (37.3891, -5.9845, 34, "Andalucía", "Interior", 70),
        "Granada": (37.1773, -3.5986, 687, "Andalucía", "Interior", 60),
        "Almeria": (36.8381, -2.4597, 21, "Andalucía", "Costa", 2),
        "Palma_Mallorca": (39.5696, 2.6502, 8, "Islas Baleares", "Costa", 0),
        "Ibiza": (38.9067, 1.4206, 6, "Islas Baleares", "Costa", 0),
        "Cordoba": (37.8882, -4.7794, 123, "Andalucía", "Interior", 140),
        "Jaen": (37.7796, -3.7849, 574, "Andalucía", "Interior", 160),
        "Caceres": (39.4753, -6.3724, 459, "Extremadura", "Interior", 200),
        "Badajoz": (38.8794, -6.9707, 185, "Extremadura", "Interior", 180),
        "Santiago_de_Compostela": (42.8785, -8.5481, 260, "Galicia", "Interior", 30),
        "Pontevedra": (42.4336, -8.6475, 20, "Galicia", "Costa", 2),
        "Vigo": (42.2304, -8.7256, 30, "Galicia", "Costa", 0),
        "Ourense": (42.3403, -7.8666, 132, "Galicia", "Interior", 70),
        "Gijon": (43.5432, -5.6614, 10, "Asturias", "Costa", 0),
        "Oviedo": (43.3603, -5.8448, 232, "Asturias", "Interior", 25),
        "Albacete": (38.9942, -1.8585, 686, "Castilla-La Mancha", "Interior", 140),
        "Avila": (40.6567, -4.7002, 1131, "Castilla y León", "Interior", 300),
        "Cadiz": (36.5271, -6.2886, 11, "Andalucía", "Costa", 0),
        "Castellon": (39.9864, -0.0513, 30, "Comunidad Valenciana", "Costa", 4),
        "Cuenca": (40.0704, -2.1374, 946, "Castilla-La Mancha", "Interior", 180),
        "Huesca": (42.1362, -0.4087, 488, "Aragón", "Interior", 180),
        "Huelva": (37.2614, -6.9447, 54, "Andalucía", "Costa", 15),
        "Lleida": (41.6176, 0.6200, 167, "Cataluña", "Interior", 80),
        "Logrono": (42.4627, -2.4450, 384, "La Rioja", "Interior", 100),
        "Lugo": (43.0121, -7.5558, 465, "Galicia", "Interior", 70),
        "Palencia": (42.0095, -4.5241, 749, "Castilla y León", "Interior", 150),
        "Pamplona": (42.8125, -1.6458, 446, "Navarra", "Interior", 60),
        "Salamanca": (40.9701, -5.6635, 802, "Castilla y León", "Interior", 320),
        "Segovia": (40.9429, -4.1088, 1002, "Castilla y León", "Interior", 300),
        "Soria": (41.7636, -2.4649, 1063, "Castilla y León", "Interior", 150),
        "Tarragona": (41.1189, 1.2445, 68, "Cataluña", "Costa", 0),
        "Teruel": (40.3457, -1.1065, 915, "Aragón", "Interior", 120),
        "Toledo": (39.8628, -4.0273, 529, "Castilla-La Mancha", "Interior", 320),
        "Vitoria": (42.8467, -2.6717, 525, "País Vasco", "Interior", 50),
    }

    @classmethod
    def create_directories(cls) -> None:
        """Crea la estructura de directorios del proyecto."""
        for dir_path in [
            cls.RAW_DIR,
            cls.PROCESSED_DIR,
            cls.RESULTS_DIR,
            cls.MAPS_DIR,
            cls.FIGURES_DIR,
        ]:
            dir_path.mkdir(parents=True, exist_ok=True)
