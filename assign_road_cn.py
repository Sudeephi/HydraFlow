import json
import geopandas as gpd
from shapely.geometry import shape

# Load land cover polygons with CN values (from Step 6)
landcover_gdf = gpd.read_file("landcover_with_cn.geojson")

# Re-project to a metric CRS (UTM zone 44N, correct for Hyderabad)
# so that distance calculations are in real meters, not degrees
landcover_gdf = landcover_gdf.to_crs(epsg=32644)

# Load roads
with open("backend/roads_data.json", "r") as f:
    roads_data = json.load(f)

results = []

for feature in roads_data["features"]:
    props = feature["properties"]
    road_id = props.get("@id", "unknown")
    road_name = props.get("name", "unnamed road")

    line = shape(feature["geometry"])  # LineString, in lat/lon (EPSG:4326)
    midpoint = line.interpolate(0.5, normalized=True)  # point halfway along the road

    # Re-project this single point to the same metric CRS as landcover_gdf
    midpoint_proj = gpd.GeoSeries([midpoint], crs="EPSG:4326").to_crs(epsg=32644).iloc[0]

    # Find the nearest land cover polygon to this midpoint (in real meters now)
    distances = landcover_gdf.geometry.distance(midpoint_proj)
    nearest_idx = distances.idxmin()
    nearest_cn = landcover_gdf.loc[nearest_idx, "cn"]

    results.append({
        "road_id": road_id,
        "road_name": road_name,
        "cn": int(nearest_cn)
    })

with open("road_cn_lookup.json", "w") as f:
    json.dump(results, f, indent=2)

print("Roads processed:", len(results))
print("\nSample results:")
for r in results[:10]:
    print(r)