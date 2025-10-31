import pandas as pd
import geopandas as gpd
import rasterio
import numpy as np

def load_data(country_energy_path, shapefile_path, raster_path):
    # Load LED distribution data from CSV
    led_data = pd.read_excel(country_energy_path)
    
    # Load world countries shapefile
    world = gpd.read_file(shapefile_path)
    
    # Load the population density raster
    with rasterio.open(raster_path) as src:
        raster_data = src.read(1)
        raster_transform = src.transform
        raster_crs = src.crs
        raster_nodata = src.nodata
        if raster_nodata is not None:
            raster_data[raster_data == raster_nodata] = np.nan

    # Generate a meshgrid of the coordinates
    height, width = raster_data.shape
    cols, rows = np.meshgrid(np.arange(width), np.arange(height))
    lon, lat = rasterio.transform.xy(raster_transform, rows, cols)
    lon_flat = np.array(lon).flatten()
    lat_flat = np.array(lat).flatten()
    raster_flat = raster_data.flatten()

    # Remove NaN values
    valid_mask = ~np.isnan(raster_flat)
    raster_flat = raster_flat[valid_mask]
    lon_flat = lon_flat[valid_mask]
    lat_flat = lat_flat[valid_mask]

    # Convert negative values to zero
    raster_flat[raster_flat < 0] = 0

    return led_data, world, raster_flat, lon_flat, lat_flat, raster_transform, raster_crs
