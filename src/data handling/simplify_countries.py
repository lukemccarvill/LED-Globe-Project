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