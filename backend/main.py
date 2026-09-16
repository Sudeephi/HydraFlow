from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import json

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


def get_base_risk(road_id: str) -> float:
    """Deterministic fake risk from road_id — matches frontend's formula exactly."""
    hash_val = 0
    for ch in road_id:
        hash_val = (hash_val * 31 + ord(ch)) % 100
    return hash_val / 100


def get_risk_at_hour(base_risk: float, hour: int) -> float:
    """Matches frontend's getRiskAtHour exactly, so numbers stay consistent."""
    growth_factor = 1 + (hour * 0.15) * base_risk
    return min(base_risk * growth_factor, 1)


@app.get("/")
def read_root():
    return {"message": "HydraFlow backend is running"}


@app.get("/roads")
def get_roads():
    """Current risk snapshot (hour 0)."""
    features = []
    for road in ROADS_GEOJSON["features"]:
        if not road.get("geometry") or road["geometry"]["type"] != "LineString":
            continue
        road_id = str(road.get("id", road["properties"].get("id", "")))
        risk = get_risk_at_hour(get_base_risk(road_id), 0)
        features.append({
            "type": "Feature",
            "properties": {
                "road_id": road_id,
                "name": road["properties"].get("name", "Unnamed Road"),
                "risk": round(risk, 3),
            },
            "geometry": road["geometry"],
        })
    return {"type": "FeatureCollection", "features": features}


@app.get("/nowcast")
def get_nowcast(hour: int = 0):
    hour = max(0, min(hour, 3))
    features = []
    for road in ROADS_GEOJSON["features"]:
        if not road.get("geometry") or road["geometry"]["type"] != "LineString":
            continue
        road_id = str(road.get("id", road["properties"].get("id", "")))
        risk = get_risk_at_hour(get_base_risk(road_id), hour)
        features.append({
            "type": "Feature",
            "properties": {
                "road_id": road_id,
                "name": road["properties"].get("name", "Unnamed Road"),
                "risk": round(risk, 3),
            },
            "geometry": road["geometry"],
        })
    return {"type": "FeatureCollection", "features": features, "hour": hour}