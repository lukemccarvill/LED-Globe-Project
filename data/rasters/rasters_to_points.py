import os
import glob
import re
from pathlib import Path
import numpy as np
import rasterio
import geopandas as gpd
from shapely.geometry import Point
import pandas as pd


def extract_year_from_filename(filename):
    """Extract year from GHS filename"""
    match = re.search(r'E(\d{4})', filename)
    if match:
        return int(match.group(1))
    return None


def get_raster_files_by_variable():
    """Group raster files by variable type"""
    tif_files = glob.glob("*_30arcmin.tif")

    variables = {
        'GHS_BUILT_V': [],
        'GHS_BUILT_S': [],
        'GHS_POP': []
    }

    for tif_file in tif_files:
        year = extract_year_from_filename(tif_file)
        if year is None:
            continue

        for var_name in variables.keys():
            if tif_file.startswith(var_name):
                variables[var_name].append((year, tif_file))
                break

    # Sort by year
    for var_name in variables.keys():
        variables[var_name].sort(key=lambda x: x[0])

    return variables


def create_reference_grid(raster_path):
    """Create a reference grid of all possible point locations"""
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

    # Filter to only points that have non-zero data in at least one year
    year_cols = [str(year) for year, _ in year_files]

    # Check for non-zero in any year
    print(f"  Filtering to cells with data...")
    mask = np.zeros(len(gdf), dtype=bool)
    for col in year_cols:
        mask |= (gdf[col] != 0)

    gdf_filtered = gdf[mask].copy()
    print(f"  Points with data: {len(gdf_filtered):,} ({len(gdf_filtered) / len(gdf) * 100:.1f}%)")

    # Spatial join with countries
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

    # Save to GeoPackage
    output_file = f"{var_name}_timeseries_points.gpkg"
    print(f"  Writing to {output_file}...")
    gdf_filtered.to_file(output_file, driver='GPKG', layer='points')

    # Get file size
    output_size_mb = os.path.getsize(output_file) / (1024 * 1024)
    print(f"  → Created: {output_file} ({output_size_mb:.2f} MB)")
    print(f"     Points: {len(gdf_filtered):,}")
    print(f"     Columns: {list(gdf_filtered.columns)}")


def main():
    # Load countries
    print("Loading countries from ../countries_simplified.gpkg...")
    try:
        countries = gpd.read_file('../countries_simplified.gpkg')
        print(f"  Loaded {len(countries)} countries\n")
    except Exception as e:
        print(f"  Error loading countries: {e}")
        print("  Continuing without country data...\n")
        countries = None

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
    print("Processing complete!")
    print("=" * 60)
    print("\nOutput files:")
    for var_name in variables.keys():
        output_file = f"{var_name}_timeseries_points.gpkg"
        if os.path.exists(output_file):
            size_mb = os.path.getsize(output_file) / (1024 * 1024)
            print(f"  {output_file} ({size_mb:.2f} MB)")


if __name__ == "__main__":
    main()