import rasterio
import numpy as np
from rasterio.enums import Resampling

# Path to the large GeoTIFF
input_path = r"C:\Users\19023\Downloads\VNL_npp_2023_global_vcmslcfg_v2_c202402081600.average_masked.dat.tif\VNL_npp_2023_global_vcmslcfg_v2_c202402081600.average_masked.dat.tif"
output_path = r"C:\Users\19023\Downloads\Swingler\Python LED Placing\Nightlight\downsampled_nightlight_30arcmin_nearestN.tif"

# Desired resolution in degrees (0.5 degrees = 30 arc-minutes)
target_resolution = 0.5

with rasterio.open(input_path) as dataset:
    # Calculate new dimensions based on the target resolution
    new_width = int((dataset.bounds.right - dataset.bounds.left) / target_resolution)
    new_height = int((dataset.bounds.top - dataset.bounds.bottom) / target_resolution)
    
    # Set the new affine transform for the output raster
    new_transform = dataset.transform * dataset.transform.scale(
        (dataset.width / new_width),
        (dataset.height / new_height)
    )
    
    # Resample the data using nearest neighbor
    data = dataset.read(
        out_shape=(
            dataset.count,  # number of bands
            new_height,
            new_width
        ),
        resampling=Resampling.nearest # can also use .bilinear, which appears blurrier but smoother. same reso, just different resampling algo
    )
    
    # Saturate values between 0 and 150
    data = np.clip(data, 0, 150)

    # Replace NaN values with 0
    data = np.nan_to_num(data, nan=0.0)
    
    # Update metadata for the new resolution
    new_meta = dataset.meta.copy()
    new_meta.update({
        'height': new_height,
        'width': new_width,
        'transform': new_transform
    })

    # Write the downsampled and processed raster to a new file
    with rasterio.open(output_path, 'w', **new_meta) as dst:
        dst.write(data)

print(f"Downsampled raster saved at {output_path}")
