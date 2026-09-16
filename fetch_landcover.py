import requests
import json

# Kukatpally-Hafeezpet bounding box (south, west, north, east)
bbox = "17.42,78.32,17.52,78.44"

query = f"""
[out:json][timeout:120];
(
  way["landuse"]({bbox});
  way["natural"]({bbox});
  way["leisure"]({bbox});
);
out geom;
"""

# Using a mirror server, often less congested than the main one
url = "https://overpass-api.de/api/interpreter"

headers = {
    "User-Agent": "HydraFlow-SIH26085-Project/1.0 (student project)",
    "Accept": "application/json"
}

response = requests.post(url, data={"data": query}, headers=headers, timeout=150)

print("Status code:", response.status_code)

if response.status_code != 200:
    print("Response text (first 500 chars):", response.text[:500])
else:
    data = response.json()
    print("Number of features found:", len(data["elements"]))

    with open("landcover_raw.json", "w") as f:
        json.dump(data, f)

    print("Saved to landcover_raw.json")