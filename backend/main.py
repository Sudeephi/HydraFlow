from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import json
import rasterio
import numpy as np

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


def get_road_elevation(road: dict) -> float:
    """Average elevation across a road's coordinate points."""
    coords = road["geometry"]["coordinates"]
    elevations = []
    for lon, lat in coords:
        elev = get_elevation_at(lon, lat)
        if elev is not None:
            elevations.append(elev)
    if not elevations:
        return (dem_min + dem_max) / 2  # fallback: mid-range
    return sum(elevations) / len(elevations)


def get_base_risk(road_id: str) -> float:
    """Deterministic fake risk from road_id (placeholder for real rainfall/runoff model)."""
    hash_val = 0
    for ch in road_id:
        hash_val = (hash_val * 31 + ord(ch)) % 100
    return hash_val / 100


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
    terrain_boost = get_terrain_factor(elevation)
    combined = base_risk + terrain_boost
    growth = combined + (hour * 0.12) + (hour * 0.1 * combined)
    return min(max(growth, 0), 1)


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
        elevation = get_road_elevation(road)
        risk = get_risk_at_hour(get_base_risk(road_id), elevation, hour)
        features.append({
            "type": "Feature",
            "properties": {
                "road_id": road_id,
                "name": road["properties"].get("name", "Unnamed Road"),
                "risk": round(risk, 3),
                "elevation_m": round(elevation, 1),
            },
            "geometry": road["geometry"],
        })
    return {"type": "FeatureCollection", "features": features, "hour": hour}