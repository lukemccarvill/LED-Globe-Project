# this was just try try out raster resampling algorithms like max and q3, it is slower and needs reproject() instead of dataset.read()
# you can ignore this script unless you want to try out these other algos
# I liked the look of cubic (as opposed to nearest neighbour) compared to the native resolution, but there is always give and take with resampling. 
# Different algo options: https://rasterio.readthedocs.io/en/stable/api/rasterio.enums.html#rasterio.enums.Resampling

import rasterio
import numpy as np
from rasterio.enums import Resampling
from rasterio.warp import reproject, calculate_default_transform

# Path to the large GeoTIFF
input_path = r"C:\Users\19023\Downloads\VNL_npp_2023_global_vcmslcfg_v2_c202402081600.average_masked.dat.tif\VNL_npp_2023_global_vcmslcfg_v2_c202402081600.average_masked.dat.tif"
output_path = r"C:\Users\19023\Downloads\Swingler\Python LED Placing\Nightlight\downsampled_nightlight_30arcmin_q3.tif"

# Desired resolution in degrees (0.5 degrees = 30 arc-minutes)
target_resolution = 0.5

with rasterio.open(input_path) as dataset:
    # Calculate new dimensions and transformation for the resampling
    transform, new_width, new_height = calculate_default_transform(
        dataset.crs, dataset.crs, dataset.width, dataset.height, *dataset.bounds, resolution=target_resolution
    )

    # Prepare metadata for the new raster
    new_meta = dataset.meta.copy()
    new_meta.update({
        'driver': 'GTiff',
        'height': new_height,
        'width': new_width,
        'transform': transform
    })

    # Create an array to hold the resampled data
    data = np.empty((dataset.count, new_height, new_width), dtype=dataset.dtypes[0])

    # Loop through each band and apply resampling using 'max'
    for i in range(1, dataset.count + 1):
        reproject(
            source=rasterio.band(dataset, i),
            destination=data[i - 1],
            src_transform=dataset.transform,
            src_crs=dataset.crs,
            dst_transform=transform,
            dst_crs=dataset.crs,
            resampling=Resampling.q3  # Apply the 'max' resampling algorithm
        )

    # Saturate values between 0 and 150
    data = np.clip(data, 0, 150)

    # Replace NaN values with 0
    data = np.nan_to_num(data, nan=0.0)

    # Write the downsampled and processed raster to a new file
    with rasterio.open(output_path, 'w', **new_meta) as dst:
        dst.write(data)

print(f"Downsampled raster saved at {output_path}")
