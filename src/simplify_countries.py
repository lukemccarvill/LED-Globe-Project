import geopandas as gpd
import os


def simplify_and_save_countries(shapefile_path, output_gpkg_path, simplify_tolerance=0.5):
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
    world = gpd.read_file(shapefile_path)

    # Read and display the CRS
    print(f"Original CRS: {world.crs}")
    print(f"Number of features: {len(world)}")

    # Ensure it's in EPSG:4326 (WGS84)
    if world.crs is None:
        print("No CRS found, setting to EPSG:4326...")
        world = world.set_crs('EPSG:4326')
    elif world.crs != 'EPSG:4326':
        print(f"Reprojecting from {world.crs} to EPSG:4326...")
        world = world.to_crs('EPSG:4326')
    else:
        print("CRS is already EPSG:4326")

    # Simplify geometries
    print(f"Simplifying geometries with tolerance={simplify_tolerance}...")
    world['geometry'] = world['geometry'].simplify(tolerance=simplify_tolerance)

    # Save as geopackage
    print(f"Saving to {output_gpkg_path}...")
    world.to_file(output_gpkg_path, driver="GPKG")

    # Get new file size
    new_size = os.path.getsize(output_gpkg_path)
    size_reduction = ((original_size - new_size) / original_size) * 100

    print("\n" + "="*50)
    print("File Size Comparison:")
    print(f"  Original: {original_size:,} bytes ({original_size / 1024 / 1024:.2f} MB)")
    print(f"  Simplified: {new_size:,} bytes ({new_size / 1024 / 1024:.2f} MB)")
    print(f"  Reduction: {size_reduction:.1f}%")
    print("="*50)
    print(f"\nSaved {len(world)} features to {output_gpkg_path}")

    return world


# Example usage:
if __name__ == "__main__":
    shapefile_path = '../data/ne_10m_admin_0_countries.shp'
    output_gpkg_path = '../data/countries_simplified.gpkg'

    # Simplify and save
    simplified_world = simplify_and_save_countries(
        shapefile_path,
        output_gpkg_path,
        simplify_tolerance=0.5
    )