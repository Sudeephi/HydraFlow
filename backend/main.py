from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import json
import rasterio
import numpy as np
import xgboost as xgb
import pandas as pd

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load real OSM road data (252 roads, Kukatpally-Hafeezpet)
with open("roads_data.json", "r", encoding="utf-8") as f:
    ROADS_GEOJSON = json.load(f)

# Load DEM (elevation raster)
dem_dataset = rasterio.open("output_hh.tif")
dem_band = dem_dataset.read(1)
dem_min = float(np.nanmin(dem_band))
dem_max = float(np.nanmax(dem_band))

# Load trained XGBoost flood risk model
xgb_model = xgb.XGBRegressor()
xgb_model.load_model("flood_risk_model.json")

# Load per-road Curve Number (CN) from land cover analysis
with open("road_cn_lookup.json", "r", encoding="utf-8") as f:
    CN_LOOKUP_LIST = json.load(f)
ROAD_CN_LOOKUP = {entry["road_id"]: entry["cn"] for entry in CN_LOOKUP_LIST}

# Load real hourly rainfall time-series (Teammate 3's data)
with open("rainfall_series.json", "r", encoding="utf-8") as f:
    RAINFALL_SERIES = json.load(f)
RAINFALL_TIMESERIES = {entry["hour"]: entry["rainfall_mm"] for entry in RAINFALL_SERIES}


def get_cn_for_road(road_id: str) -> float:
    return ROAD_CN_LOOKUP.get(road_id, DEFAULT_CN)


def get_rainfall_for_hour(hour: int) -> float:
    return RAINFALL_TIMESERIES.get(hour, RAINFALL_TIMESERIES[max(RAINFALL_TIMESERIES.keys())])


def get_elevation_at(lon: float, lat: float) -> float:
    """Sample the DEM raster at a given lon/lat. Returns None if outside bounds."""
    try:
        row, col = dem_dataset.index(lon, lat)
        if 0 <= row < dem_band.shape[0] and 0 <= col < dem_band.shape[1]:
            val = dem_band[row, col]
            if np.isnan(val):
                return None
            return float(val)
    except Exception:
        pass
    return None


def get_road_elevation_and_confidence(road: dict):
    """Average elevation + confidence based on fraction of valid DEM samples."""
    coords = road["geometry"]["coordinates"]
    elevations = []
    for lon, lat in coords:
        elev = get_elevation_at(lon, lat)
        if elev is not None:
            elevations.append(elev)

    total_points = len(coords)
    valid_points = len(elevations)
    valid_ratio = valid_points / total_points if total_points > 0 else 0

    if not elevations:
        avg_elevation = (dem_min + dem_max) / 2
    else:
        avg_elevation = sum(elevations) / len(elevations)

    confidence = round(60 + 35 * valid_ratio)  # 60-95% range, real data-driven
    return avg_elevation, confidence


# Default Curve Number for our mixed-urban pilot area.
# CN ranges: paved/urban ~90-95, residential ~80-85, vegetation ~60-70, water ~98.
# We'll use one flat value until land cover data gives us per-road values.
DEFAULT_CN = 85


def compute_scs_runoff(rainfall_mm: float, cn: float = DEFAULT_CN) -> float:
    s = (25400 / cn) - 254
    if rainfall_mm <= 0.2 * s:
        return 0.0
    q = ((rainfall_mm - 0.2 * s) ** 2) / (rainfall_mm + 0.8 * s)
    return q

def normalize_runoff_to_risk(runoff_mm: float, rainfall_mm: float) -> float:
    """
    Converts runoff depth into a 0-1 risk score.
    Runoff can't exceed rainfall, so we normalize against it as the ceiling.
    """
    if rainfall_mm <= 0:
        return 0.0
    return min(runoff_mm / rainfall_mm, 1.0)


def get_terrain_factor(elevation: float) -> float:
    """
    Lower elevation (relative to area range) = higher flood risk contribution.
    Returns a value 0.0 (highest ground, lowest risk boost) to 0.3 (lowest ground, highest risk boost).
    """
    if dem_max == dem_min:
        return 0.15
    normalized_low = 1 - ((elevation - dem_min) / (dem_max - dem_min))  # 1 = lowest point
    return normalized_low * 0.3


def get_risk_at_hour(base_risk: float, elevation: float, hour: int) -> float:
    terrain_boost = get_terrain_factor(elevation)  # 0 to 0.3
    combined = base_risk + terrain_boost
    return min(max(combined, 0), 1)


@app.get("/")
def read_root():
    return {"message": "HydraFlow backend is running", "dem_loaded": True, "elevation_range_m": [dem_min, dem_max]}


@app.get("/roads")
def get_roads():
    return get_nowcast(hour=0)


@app.get("/nowcast")
def get_nowcast(hour: int = 0):
    hour = max(0, min(hour, 3))
    features = []
    for road in ROADS_GEOJSON["features"]:
        if not road.get("geometry") or road["geometry"]["type"] != "LineString":
            continue
        road_id = str(road.get("id", road["properties"].get("id", "")))
        elevation, confidence = get_road_elevation_and_confidence(road)
        rainfall_mm = get_rainfall_for_hour(hour)
        cn = get_cn_for_road(road_id)

        # Use the trained XGBoost model instead of the raw formula
        model_input = pd.DataFrame([[elevation, cn, rainfall_mm]], columns=["elevation", "cn", "rainfall_mm"])
        risk = float(xgb_model.predict(model_input)[0])
        risk = min(max(risk, 0), 1)  # safety clamp
        features.append({
            "type": "Feature",
            "properties": {
                "road_id": road_id,
                "name": road["properties"].get("name", "Unnamed Road"),
                "risk": round(risk, 3),
                "elevation_m": round(elevation, 1),
                "confidence": confidence,
            },
            "geometry": road["geometry"],
        })
    return {"type": "FeatureCollection", "features": features, "hour": hour}