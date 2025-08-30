class Feature:
    """Defines a basic configuration of features."""
    def __init__(self, api_name: str, db_col: str, invert_score: bool = False, apply_log: bool = False):
        self.api_name = api_name # Name used in the API (for frontend request)
        self.db_col = db_col
        self.invert_score = invert_score
        self.apply_log = apply_log


# --- Feature config defined base on PCA scripts ---
FEATURES_CONFIG = [
    Feature(api_name="price", db_col="price", apply_log=True),
    Feature(api_name="airQualityScore", db_col="aqi", invert_score=True),
    Feature(api_name="walkScore", db_col="nwi_score"),
    Feature(api_name="nearestBusStopDistance", db_col="nearest_bus_stop_miles", invert_score=True, apply_log=True),
    Feature(api_name="busStopsNumber", db_col="nearby_bus_stops", apply_log=True),
    Feature(api_name="nearestParkDistance", db_col="nearest_park_miles", invert_score=True, apply_log=True),
    Feature(api_name="openStreetNumber", db_col="nearby_parks"),
]

# --- helper variables ---
API_FEATURE_NAMES = [f.api_name for f in FEATURES_CONFIG]
DB_COLUMN_NAMES = [f.db_col for f in FEATURES_CONFIG]