from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import random

app = FastAPI()

# Allow the frontend (localhost:5173) to call this API — browsers block
# cross-origin requests by default without this.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Base road data — same shape as frontend/src/data/roads.json
# risk: 0.0-1.0 (this is the CURRENT / hour-0 risk)
BASE_ROADS = [
    {"road_id": "R1", "name": "Kukatpally Main Road", "risk": 0.82,
     "coordinates": [[78.4011, 17.4933], [78.4035, 17.4948], [78.4058, 17.4962]]},
    {"road_id": "R2", "name": "Hafeezpet Road", "risk": 0.35,
     "coordinates": [[78.3612, 17.4785], [78.3634, 17.4801], [78.3660, 17.4818]]},
    {"road_id": "R3", "name": "Bachupally Road", "risk": 0.61,
     "coordinates": [[78.3892, 17.5102], [78.3915, 17.5120], [78.3940, 17.5135]]},
    {"road_id": "R4", "name": "Miyapur Road", "risk": 0.15,
     "coordinates": [[78.3548, 17.4967], [78.3572, 17.4985], [78.3598, 17.5001]]},
    {"road_id": "R5", "name": "KPHB Colony Road", "risk": 0.93,
     "coordinates": [[78.3987, 17.4855], [78.4008, 17.4870], [78.4030, 17.4888]]},
]


def build_feature(road: dict, risk: float) -> dict:
    """Wraps one road into a GeoJSON Feature, matching roads.json's exact shape."""
    return {
        "type": "Feature",
        "properties": {
            "road_id": road["road_id"],
            "name": road["name"],
            "risk": round(risk, 2),
        },
        "geometry": {
            "type": "LineString",
            "coordinates": road["coordinates"],
        },
    }


@app.get("/")
def read_root():
    return {"message": "HydraFlow backend is running"}


@app.get("/roads")
def get_roads():
    """Current risk snapshot (hour 0) — same shape as the old mock roads.json."""
    features = [build_feature(r, r["risk"]) for r in BASE_ROADS]
    return {"type": "FeatureCollection", "features": features}


@app.get("/nowcast")
def get_nowcast(hour: int = 0):
    """
    Returns risk projected 'hour' hours ahead (0-3), matching the frontend's
    timeline slider (Now, +1h, +2h, +3h).
    For now: risk drifts randomly up/down each hour as a placeholder for the
    real XGBoost model, which the ML teammate will plug in later.
    """
    hour = max(0, min(hour, 3))  # clamp to 0-3, matches slider range
    random.seed(hour)  # same hour always gives same result (consistent demo)

    features = []
    for road in BASE_ROADS:
        drift = random.uniform(-0.15, 0.20) * hour
        projected_risk = max(0.0, min(1.0, road["risk"] + drift))
        features.append(build_feature(road, projected_risk))

    return {"type": "FeatureCollection", "features": features, "hour": hour}