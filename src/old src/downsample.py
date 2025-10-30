""""

This script downsamples raster data from a resolution of 30 arcsecs to 30 arcminutes.

Data is accessed from the Global Human Settlement layers:
1. GHS-BUILT-S
2. GHS-BUILT-V
3. GHS-POP

resolution: 30 arcsec, coordinate system: WGS84
epochs:

Further background on the Global Human Settlement layers can be found here:
Pesaresi, M. et al. (2024) "Advances on the Global Human Settlement Layer by joint assessment of Earth Observation and
    population survey data", International Journal of Digital Earth, 17(1). DOI: 10.1080/17538947.2024.2390454

"""

import os
import glob
import re
from pathlib import Path
import numpy as np
import rasterio
from rasterio.windows import Window
from rasterio.transform import Affine


def downsample_tif_fast(input_path, output_path, factor=60):
    """
    Fast downsample using block processing
    30 arcminutes / 30 arcseconds = 60x factor
    """
    print(f"Processing: {input_path}")

    with rasterio.open(input_path) as src:
        # Read metadata
        profile = src.profile.copy()

        # Calculate new dimensions
        new_height = src.height // factor
        new_width = src.width // factor

        # Update transform for new resolution
        # Each pixel is now 60x larger
        old_transform = src.transform
        new_transform = Affine(
            old_transform.a * factor,  # x pixel size
            old_transform.b,
            old_transform.c,  # x origin
            old_transform.d,
            old_transform.e * factor,  # y pixel size (usually negative)
            old_transform.f  # y origin
        )

        # Update profile
        profile.update({
            'height': new_height,
            'width': new_width,
            'transform': new_transform
        })

        # Process each band
        with rasterio.open(output_path, 'w', **profile) as dst:
            for band_idx in range(1, src.count + 1):
                print(f"  Processing band {band_idx}/{src.count}...", end='\r')

                # Read entire band (for global data, might want to process in chunks)
                data = src.read(band_idx)

                # Reshape and sum
                # Trim to exact multiple of factor if needed
                trim_height = (data.shape[0] // factor) * factor
                trim_width = (data.shape[1] // factor) * factor
                data = data[:trim_height, :trim_width]

                # Reshape to group pixels into blocks and sum
                # Shape: (new_height, factor, new_width, factor)
                reshaped = data.reshape(
                    new_height, factor,
                    new_width, factor
                )

                # Sum along the factor dimensions
                downsampled = reshaped.sum(axis=(1, 3))

                # Write output
                dst.write(downsampled, band_idx)

        print(f"  Processing band {src.count}/{src.count}... Done!")

    # Get output file size in MB
    output_size_mb = os.path.getsize(output_path) / (1024 * 1024)
    print(f"  → Created: {output_path} ({output_size_mb:.2f} MB)")


def main():
    # Find all .tif files in current directory
    tif_files = glob.glob("**/*.tif")

    # Filter for GHS files
    ghs_files = [f for f in tif_files if f.startswith(('GHS_BUILT_S', 'GHS_BUILT_V', 'GHS_POP'))]

    if not ghs_files:
        print("No GHS .tif files found in current directory")
        return

    print(f"Found {len(ghs_files)} GHS .tif files to process\n")

    for input_file in ghs_files:
        # Create output filename - keep only up to E{year}
        base_name = Path(input_file).stem
        # Extract everything up to and including E followed by 4 digits (year)
        match = re.match(r'(GHS_[A-Z_]+_E\d{4})', base_name)
        if match:
            prefix = match.group(1)
        else:
            # Fallback to full name if pattern doesn't match
            prefix = base_name
        output_file = f"{prefix}_30arcmin.tif"

        try:
            downsample_tif_fast(input_file, output_file, factor=60)
        except Exception as e:
            print(f"  ✗ Error processing {input_file}: {e}")
            import traceback
            traceback.print_exc()
            continue

    print(f"\nProcessing complete!")


if __name__ == "__main__":
    main()