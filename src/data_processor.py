"""
This script processes raster data from the Global Human Settlement layers.

Configuration options:
- downsample: If True, downsample raster data from 30 arcsecs to 30 arcminutes
- rasters_to_points: If True, convert downsampled rasters to point GeoPackages with time series

Data is accessed from the Global Human Settlement layers:
1. GHS-BUILT-S
2. GHS-BUILT-V
3. GHS-POP

resolution: 30 arcsec, coordinate system: WGS84

Further background on the Global Human Settlement layers can be found here:
Pesaresi, M. et al. (2024) "Advances on the Global Human Settlement Layer by joint assessment of Earth Observation and
    population survey data", International Journal of Digital Earth, 17(1). DOI: 10.1080/17538947.2024.2390454
"""

import os
import re
from pathlib import Path
import numpy as np
import rasterio
from rasterio.transform import Affine

# =============================================================================
# CONFIGURATION
# =============================================================================

CONFIG = {
    'downsample': True,  # Downsample from 30 arcsec to 30 arcmin
    'rasters_to_points': True,  # Convert rasters to point GeoPackages
    'downsample_factor': 60,  # 30 arcminutes / 30 arcseconds = 60x
    'input_rasters_dir': '../data/rasters',  # Directory containing input GHS .tif files
    'output_dir': '../data/rasters',  # Directory for output files
    'countries_file': '../data/countries_simplified.gpkg',  # Path to countries file for spatial join
}


# =============================================================================
# DOWNSAMPLING FUNCTIONS
# =============================================================================

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

                # Read entire band
                data = src.read(band_idx)

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


def run_downsample():
    """Run the downsampling process"""
    print("\n" + "=" * 60)
    print("STEP 1: DOWNSAMPLING RASTERS")
    print("=" * 60 + "\n")

    # Create output directory if it doesn't exist
    output_dir = Path(CONFIG['output_dir'])
    output_dir.mkdir(parents=True, exist_ok=True)

    # Find all .tif files in input directory
    input_dir = Path(CONFIG['input_rasters_dir'])
    if not input_dir.exists():
        print(f"Error: Input directory not found: {input_dir}")
        return []

    tif_files = list(input_dir.glob("**/*.tif"))

    # Filter for GHS files
    ghs_files = [f for f in tif_files if any(
        f.name.startswith(prefix) for prefix in ['GHS_BUILT_S', 'GHS_BUILT_V', 'GHS_POP']
    )]

    if not ghs_files:
        print(f"No GHS .tif files found in {input_dir}")
        return []

    print(f"Found {len(ghs_files)} GHS .tif files to process\n")

    output_files = []
    for input_file in ghs_files:
        # Create output filename - keep only up to E{year}
        base_name = input_file.stem
        # Extract everything up to and including E followed by 4 digits (year)
        match = re.match(r'(GHS_[A-Z_]+_E\d{4})', base_name)
        if match:
            prefix = match.group(1)
        else:
            # Fallback to full name if pattern doesn't match
            prefix = base_name
        output_file = output_dir / f"{prefix}_30arcmin.tif"

        try:
            downsample_tif_fast(str(input_file), str(output_file), factor=CONFIG['downsample_factor'])
            output_files.append(str(output_file))
        except Exception as e:
            print(f"  ✗ Error processing {input_file}: {e}")
            import traceback
            traceback.print_exc()
            continue

    print(f"\nDownsampling complete! Created {len(output_files)} files.")
    return output_files


# =============================================================================
# RASTER TO POINTS FUNCTIONS
# =============================================================================

def extract_year_from_filename(filename):
    """Extract year from GHS filename"""
    match = re.search(r'E(\d{4})', filename)
    if match:
        return int(match.group(1))
    return None


def get_raster_files_by_variable():
    """Group raster files by variable type"""
    output_dir = Path(CONFIG['output_dir'])
    tif_files = list(output_dir.glob("**/*_30arcmin.tif"))

    variables = {
        'GHS_BUILT_V': [],
        'GHS_BUILT_S': [],
        'GHS_POP': []
    }

    for tif_file in tif_files:
        year = extract_year_from_filename(tif_file.name)
        if year is None:
            continue

        for var_name in variables.keys():
            if tif_file.name.startswith(var_name):
                variables[var_name].append((year, str(tif_file)))
                break

    # Sort by year
    for var_name in variables.keys():
        variables[var_name].sort(key=lambda x: x[0])

    return variables


def create_reference_grid(raster_path):
    """Create a reference grid of all possible point locations"""
    import geopandas as gpd
    from shapely.geometry import Point

    with rasterio.open(raster_path) as src:
        # Create grid of all cell centers
        rows, cols = np.indices((src.height, src.width))

        # Convert to geographic coordinates
        xs, ys = rasterio.transform.xy(src.transform, rows.flatten(), cols.flatten(), offset='center')

        # Create point index (row * width + col)
        point_indices = (rows.flatten() * src.width + cols.flatten()).astype(int)

        # Create GeoDataFrame with all possible points
        gdf = gpd.GeoDataFrame({
            'point_index': point_indices,
            'geometry': [Point(x, y) for x, y in zip(xs, ys)]
        }, crs=src.crs)

        return gdf


def add_year_data(base_gdf, raster_path, year_col):
    """Add data from a raster as a new column"""
    print(f"    Adding data for {year_col}...")

    with rasterio.open(raster_path) as src:
        data = src.read(1).flatten()

        # Add as new column
        base_gdf[year_col] = data

        # Track non-zero count
        non_zero = (data != 0).sum()
        if src.nodata is not None:
            non_zero = ((data != 0) & (data != src.nodata)).sum()

        print(f"      Non-zero cells: {non_zero:,}")

    return base_gdf


def process_variable(var_name, year_files, countries):
    """Process all years for one variable into a single point file"""
    import geopandas as gpd

    print(f"\nProcessing {var_name}:")
    print(f"  Found {len(year_files)} years: {[y for y, _ in year_files]}")

    if not year_files:
        print(f"  No files found for {var_name}, skipping...")
        return

    # Use first file to create reference grid
    first_year, first_file = year_files[0]
    print(f"  Creating reference grid from {first_file}...")
    gdf = create_reference_grid(first_file)

    print(f"  Total grid points: {len(gdf):,}")

    # Add data for each year
    for year, raster_file in year_files:
        year_col = str(year)
        gdf = add_year_data(gdf, raster_file, year_col)

    # Keep ALL points (including ocean - no filtering for non-zero data)
    year_cols = [str(year) for year, _ in year_files]
    gdf_filtered = gdf.copy()
    print(f"  Keeping all points: {len(gdf_filtered):,}")

    # Spatial join with countries
    if countries is not None:
        print(f"  Performing spatial join with countries...")
        if countries.crs != gdf_filtered.crs:
            countries_proj = countries.to_crs(gdf_filtered.crs)
        else:
            countries_proj = countries

        gdf_filtered = gdf_filtered.sjoin(countries_proj, how='left', predicate='within')

        # Find country name column
        country_col = None
        for col in ['name', 'NAME', 'ADMIN', 'Country', 'country', 'NAME_EN']:
            if col in gdf_filtered.columns:
                country_col = col
                break

        # Reorder columns: point_index, country, then years in order
        if country_col:
            cols_order = ['point_index', country_col] + year_cols + ['geometry']
            gdf_filtered = gdf_filtered[cols_order].rename(columns={country_col: 'country'})
        else:
            cols_order = ['point_index'] + year_cols + ['geometry']
            gdf_filtered = gdf_filtered[cols_order]

        # Remove index_right from spatial join if present
        if 'index_right' in gdf_filtered.columns:
            gdf_filtered = gdf_filtered.drop(columns=['index_right'])
    else:
        # No countries file - just use point_index, years, and geometry
        cols_order = ['point_index'] + year_cols + ['geometry']
        gdf_filtered = gdf_filtered[cols_order]

    # Save to GeoPackage in output directory
    output_dir = Path(CONFIG['output_dir'])
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / f"{var_name}_timeseries_points.gpkg"

    print(f"  Writing to {output_file}...")
    gdf_filtered.to_file(str(output_file), driver='GPKG', layer='points')

    # Get file size
    output_size_mb = os.path.getsize(output_file) / (1024 * 1024)
    print(f"  → Created: {output_file} ({output_size_mb:.2f} MB)")
    print(f"     Points: {len(gdf_filtered):,}")
    print(f"     Columns: {list(gdf_filtered.columns)}")


def run_rasters_to_points():
    """Run the raster to points conversion process"""
    import geopandas as gpd

    print("\n" + "=" * 60)
    print("STEP 2: CONVERTING RASTERS TO POINTS")
    print("=" * 60 + "\n")

    # Load countries
    countries = None
    if CONFIG['countries_file']:
        print(f"Loading countries from {CONFIG['countries_file']}...")
        try:
            countries = gpd.read_file(CONFIG['countries_file'])
            print(f"  Loaded {len(countries)} countries\n")
        except Exception as e:
            print(f"  Error loading countries: {e}")
            print("  Continuing without country data...\n")

    # Get files grouped by variable
    variables = get_raster_files_by_variable()

    # Process each variable
    for var_name, year_files in variables.items():
        if year_files:
            try:
                process_variable(var_name, year_files, countries)
            except Exception as e:
                print(f"  ✗ Error processing {var_name}: {e}")
                import traceback
                traceback.print_exc()

    print("\n" + "=" * 60)
    print("Raster to points conversion complete!")
    print("=" * 60)
    print("\nOutput files:")
    output_dir = Path(CONFIG['output_dir'])
    for var_name in variables.keys():
        output_file = output_dir / f"{var_name}_timeseries_points.gpkg"
        if output_file.exists():
            size_mb = os.path.getsize(output_file) / (1024 * 1024)
            print(f"  {output_file} ({size_mb:.2f} MB)")


# =============================================================================
# MAIN
# =============================================================================

def main():
    """Main execution function based on configuration"""
    print("\n" + "=" * 60)
    print("GHS DATA PROCESSING PIPELINE")
    print("=" * 60)
    print("\nConfiguration:")
    print(f"  Downsample: {CONFIG['downsample']}")
    print(f"  Rasters to Points: {CONFIG['rasters_to_points']}")
    print(f"  Input directory: {CONFIG['input_rasters_dir']}")
    print(f"  Output directory: {CONFIG['output_dir']}")
    if CONFIG['rasters_to_points']:
        print(f"  Countries file: {CONFIG['countries_file']}")

    # Step 1: Downsample if enabled
    if CONFIG['downsample']:
        run_downsample()
    else:
        print("\nSkipping downsampling (disabled in config)")

    # Step 2: Convert to points if enabled
    if CONFIG['rasters_to_points']:
        # Check if geopandas is available
        try:
            import geopandas as gpd
            from shapely.geometry import Point
            run_rasters_to_points()
        except ImportError:
            print("\n" + "=" * 60)
            print("ERROR: geopandas not installed")
            print("=" * 60)
            print("To enable raster to points conversion, install geopandas:")
            print("  pip install geopandas")
    else:
        print("\nSkipping raster to points conversion (disabled in config)")

    print("\n" + "=" * 60)
    print("PROCESSING COMPLETE!")
    print("=" * 60)


if __name__ == "__main__":
    main()

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


import requests
import json
import pandas as pd
import os
import geopandas as gpd
from shapely.geometry import shape

"""

   Files to import:                       Source:                       Saves to file:

1. global energy consumption              ourworldindata.org            global_energy_consumption
2. per capita energy consumption          ourworldindata.org            per_capita_energy_consumption
3. world administrative boundaries        opendatasoft.com (WFP, UN)    countries                  
4. 

"""

# Create the directory structure if it doesn't exist
# Use '../data/API' to go up from src to parent, then into data/API
os.makedirs('../data/API', exist_ok=True)
print("Directory '../data/API' created or already exists")

## --------------------------------------------- GLOBAL ENERGY CONSUMPTION ---------------------------------------------
# region

# Fetch the data
df = pd.read_csv(
    "https://ourworldindata.org/grapher/primary-energy-cons.csv?v=1&csvType=full&useColumnShortNames=true",
    storage_options={'User-Agent': 'Our World In Data data fetch/1.0'}
)

print("Data columns:", df.columns.tolist())
print(f"Data shape: {df.shape}")

# Save the DataFrame to CSV
df.to_csv('../data/API/global_energy_consumption.csv', index=False)
print("Data saved to: ../data/API/global_energy_consumption.csv")

# Fetch the metadata
metadata = requests.get(
    "https://ourworldindata.org/grapher/primary-energy-cons.metadata.json?v=1&csvType=full&useColumnShortNames=true"
).json()

# Save the metadata to JSON
with open('../data/API/global_energy_consumption_metadata.json', 'w') as f:
    json.dump(metadata, f, indent=2)
print("Metadata saved to: ../data/API/global_energy_consumption_metadata.json\n")

# endregion

## ------------------------------------------- PER CAPITA ENERGY CONSUMPTION -------------------------------------------
# region

# Fetch the data
df = pd.read_csv(
    "https://ourworldindata.org/grapher/per-capita-energy-use.csv?v=1&csvType=full&useColumnShortNames=true",
    storage_options={'User-Agent': 'Our World In Data data fetch/1.0'}
)

print("Data columns:", df.columns.tolist())
print(f"Data shape: {df.shape}")

# Save the DataFrame to CSV
df.to_csv('../data/API/per_capita_energy_consumption.csv', index=False)
print("Data saved to: ../data/API/per_capita_energy_consumption.csv")

# Fetch the metadata
metadata = requests.get(
    "https://ourworldindata.org/grapher/per-capita-energy-use.metadata.json?v=1&csvType=full&useColumnShortNames=true"
).json()

# Save the metadata to JSON
with open('../data/API/per_capita_energy_consumption_metadata.json', 'w') as f:
    json.dump(metadata, f, indent=2)
print("Metadata saved to: ../data/API/per_capita_energy_consumption_metadata.json")

# endregion

## ------------------------------------------ WORLD ADMINISTRATIVE BOUNDARIES ------------------------------------------
# region

response = requests.get(
    "https://public.opendatasoft.com/api/explore/v2.1/catalog/datasets/world-administrative-boundaries-countries/records"
)

data = response.json()
records = data['results']

# Extract geometry and properties from the API response
features = []
for record in records:
    # The geometry is in record['geo_shape'] for Opendatasoft APIs
    if 'geo_shape' in record:
        features.append({
            'geometry': shape(record['geo_shape']),
            **record  # Include all other fields
        })

# Convert to GeoDataFrame
gdf = gpd.GeoDataFrame(features, crs='EPSG:4326')

# Save as GeoPackage
gdf.to_file('../data/API/countries.gpkg', driver='GPKG')
print("\nCountries data saved to: ../data/API/countries.gpkg")

# endregion

import geopandas as gpd
import matplotlib.pyplot as plt
import os


def simplify_and_save_countries(shapefile_path, output_gpkg_path, simplify_tolerance=0.5, plot_comparison=True):
    """
    Import a country shapefile, simplify geometries, and save as geopackage.

    Parameters:
    -----------
    shapefile_path : str
        Path to the input shapefile (e.g., 'data/ne_10m_admin_0_countries.shp')
    output_gpkg_path : str
        Path for the output geopackage (e.g., 'data/countries_simplified.gpkg')
    simplify_tolerance : float
        Tolerance for geometry simplification in the units of the CRS (default: 0.5 degrees)
    plot_comparison : bool
        Whether to plot before/after comparison (default: True)

    Returns:
    --------
    geopandas.GeoDataFrame
        The simplified GeoDataFrame
    """

    # Get original file size
    original_size = os.path.getsize(shapefile_path)
    print(f"Original shapefile size: {original_size:,} bytes ({original_size / 1024 / 1024:.2f} MB)")

    # Load the shapefile
    print(f"Loading shapefile from {shapefile_path}...")
    world_original = gpd.read_file(shapefile_path)

    # Read and display the CRS
    print(f"Original CRS: {world_original.crs}")
    print(f"Number of features: {len(world_original)}")

    # Ensure it's in EPSG:4326 (WGS84)
    if world_original.crs is None:
        print("No CRS found, setting to EPSG:4326...")
        world_original = world_original.set_crs('EPSG:4326')
    elif world_original.crs != 'EPSG:4326':
        print(f"Reprojecting from {world_original.crs} to EPSG:4326...")
        world_original = world_original.to_crs('EPSG:4326')
    else:
        print("CRS is already EPSG:4326")

    # Simplify geometries
    print(f"Simplifying geometries with tolerance={simplify_tolerance}...")
    world_simplified = world_original.copy()
    world_simplified['geometry'] = world_simplified['geometry'].simplify(tolerance=simplify_tolerance)

    # Save as geopackage
    print(f"Saving to {output_gpkg_path}...")
    world_simplified.to_file(output_gpkg_path, driver="GPKG")

    # Get new file size
    new_size = os.path.getsize(output_gpkg_path)
    size_reduction = ((original_size - new_size) / original_size) * 100

    print("\n" + "=" * 50)
    print("File Size Comparison:")
    print(f"  Original: {original_size:,} bytes ({original_size / 1024 / 1024:.2f} MB)")
    print(f"  Simplified: {new_size:,} bytes ({new_size / 1024 / 1024:.2f} MB)")
    print(f"  Reduction: {size_reduction:.1f}%")
    print("=" * 50)
    print(f"\nSaved {len(world_simplified)} features to {output_gpkg_path}")

    # Plot comparison if requested
    if plot_comparison:
        print("\nCreating comparison plot...")
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(20, 10))

        # Plot original
        world_original.plot(ax=ax1, color='lightblue', edgecolor='black', linewidth=0.5)
        ax1.set_title(f'Original ({original_size / 1024 / 1024:.2f} MB)', fontsize=16)
        ax1.set_xlabel('Longitude')
        ax1.set_ylabel('Latitude')
        ax1.grid(True, alpha=0.3)

        # Plot simplified
        world_simplified.plot(ax=ax2, color='lightgreen', edgecolor='black', linewidth=0.5)
        ax2.set_title(f'Simplified (tolerance={simplify_tolerance}, {new_size / 1024 / 1024:.2f} MB)', fontsize=16)
        ax2.set_xlabel('Longitude')
        ax2.set_ylabel('Latitude')
        ax2.grid(True, alpha=0.3)

        plt.tight_layout()

        # Save the comparison plot
        comparison_plot_path = output_gpkg_path.replace('.gpkg', '_comparison.png')
        plt.savefig(comparison_plot_path, dpi=150, bbox_inches='tight')
        print(f"Comparison plot saved to {comparison_plot_path}")

        plt.show()

    return world_simplified


# Example usage:
if __name__ == "__main__":
    shapefile_path = '../data/ne_10m_admin_0_countries.shp'
    output_gpkg_path = '../data/countries_simplified.gpkg'

    # Simplify and save
    simplified_world = simplify_and_save_countries(
        shapefile_path,
        output_gpkg_path,
        simplify_tolerance=.01,
        plot_comparison=True
    )