import rasterio
import matplotlib.pyplot as plt

# Sample rainfall value for demo (realistic July monsoon burst, mm/hour)
rainfall_mm_per_hr = 45

with rasterio.open("output_hh.tif") as dem:
    elevation = dem.read(1)
    print("DEM shape (rows, cols):", elevation.shape)
    print("Elevation range (m):", elevation.min(), "to", elevation.max())
    print("Sample rainfall input (mm/hr):", rainfall_mm_per_hr)

plt.imshow(elevation, cmap="terrain")
plt.colorbar(label="Elevation (m)")
plt.title(f"Kukatpally-Hafeezpet DEM | Rainfall input: {rainfall_mm_per_hr} mm/hr")
plt.savefig("dem_preview.png")
plt.show()