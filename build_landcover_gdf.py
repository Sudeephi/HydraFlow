import json
from shapely.geometry import Polygon
import geopandas as gpd
from cn_lookup import get_cn

with open("landcover_raw.json", "r") as f:
    data = json.load(f)

records = []

for el in data["elements"]:
    geom = el.get("geometry")
    tags = el.get("tags", {})

    if not geom or len(geom) < 3:
        continue  # skip features without enough points to form a shape

    # Overpass gives points as {"lat": .., "lon": ..} - convert to (lon, lat) for shapely
    coords = [(pt["lon"], pt["lat"]) for pt in geom]

    try:
        polygon = Polygon(coords)
        if not polygon.is_valid or polygon.is_empty:
            continue
    except Exception:
        continue

    cn = get_cn(tags)

    records.append({
        "geometry": polygon,
        "cn": cn,
        "tags": str(tags)
    })

gdf = gpd.GeoDataFrame(records, crs="EPSG:4326")

print("Total valid land cover polygons:", len(gdf))
print(gdf[["cn"]].value_counts())

gdf.to_file("landcover_with_cn.geojson", driver="GeoJSON")
print("Saved to landcover_with_cn.geojson")