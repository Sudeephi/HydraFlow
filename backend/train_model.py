import json
import random
import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score

random.seed(42)
np.random.seed(42)

# --- Step 1: Generate synthetic training examples ---
# Each example: elevation, cn, rainfall_mm -> risk (0-1)
# We simulate a plausible relationship with some noise, mimicking real-world variability.

N_SAMPLES = 5000

elevations = np.random.uniform(530, 640, N_SAMPLES)  # matches our DEM range
cns = np.random.choice([65, 70, 82, 85, 92, 98], N_SAMPLES)  # matches our real CN values
rainfalls = np.random.uniform(5, 80, N_SAMPLES)  # mm/hr range

def scs_runoff(rainfall_mm, cn):
    s = (25400 / cn) - 254
    if rainfall_mm <= 0.2 * s:
        return 0.0
    return ((rainfall_mm - 0.2 * s) ** 2) / (rainfall_mm + 0.8 * s)

def synthetic_risk(elevation, cn, rainfall_mm, elev_min=530, elev_max=640):
    runoff = scs_runoff(rainfall_mm, cn)
    base = min(runoff / max(rainfall_mm, 1), 1.0)
    terrain_boost = (1 - (elevation - elev_min) / (elev_max - elev_min)) * 0.3
    noise = np.random.normal(0, 0.05)  # realistic measurement noise
    risk = min(max(base + terrain_boost + noise, 0), 1)
    return risk

risks = [synthetic_risk(e, c, r) for e, c, r in zip(elevations, cns, rainfalls)]

df = pd.DataFrame({
    "elevation": elevations,
    "cn": cns,
    "rainfall_mm": rainfalls,
    "risk": risks,
})

print("Sample of training data:")
print(df.head())
print(f"\nTotal samples: {len(df)}")

# --- Step 2: Train XGBoost model ---
X = df[["elevation", "cn", "rainfall_mm"]]
y = df["risk"]

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

model = xgb.XGBRegressor(
    n_estimators=100,
    max_depth=4,
    learning_rate=0.1,
    random_state=42,
)
model.fit(X_train, y_train)

# --- Step 3: Evaluate ---
preds = model.predict(X_test)
mae = mean_absolute_error(y_test, preds)
r2 = r2_score(y_test, preds)

print(f"\nModel Evaluation:")
print(f"MAE: {mae:.4f}")
print(f"R² Score: {r2:.4f}")

# --- Step 4: Save the trained model ---
model.save_model("flood_risk_model.json")
print("\nModel saved to flood_risk_model.json")