import matplotlib.pyplot as plt
import numpy as np
import geopandas as gpd
import random
from shapely.geometry import Polygon, MultiPolygon, Point
from gore_drawer import plot_multiple_gores
from tqdm import tqdm
import os

random.seed(42)  # to get consistent green countries


def create_gore_polygons_gdf(gore_boundaries, num_gores=12):
    """Create a GeoDataFrame of gore polygons in lon/lat space (EPSG:4326)"""
    gore_width = 360 / num_gores
    geometries = []
    gore_ids = []

    for i in range(num_gores):
        lon_min = -180 + (i * gore_width)
        lon_max = lon_min + gore_width

        # Create a box for this gore
        coords = [
            (lon_min, -90),
            (lon_max, -90),
            (lon_max, 90),
            (lon_min, 90),
            (lon_min, -90)
        ]
        gore_poly = Polygon(coords)
        geometries.append(gore_poly)
        gore_ids.append(i)

    gdf = gpd.GeoDataFrame({'gore_id': gore_ids, 'geometry': geometries}, crs='EPSG:4326')
    return gdf

# debug
def plot_debug_geopackages(world, gores_gdf, output_path='../outputs/debug_geopackages.png'):
    """Plot the countries and gore boxes for debugging"""
    fig, axes = plt.subplots(1, 3, figsize=(24, 8))

    # Plot 1: Countries only
    world.plot(ax=axes[0], color='lightblue', edgecolor='black', linewidth=0.5)
    axes[0].set_title(f'Countries ({len(world)} features)', fontsize=14)
    axes[0].set_xlabel('Longitude')
    axes[0].set_ylabel('Latitude')
    axes[0].grid(True, alpha=0.3)

    # Plot 2: Gore boxes only
    gores_gdf.plot(ax=axes[1], color='lightgreen', edgecolor='red', linewidth=2, alpha=0.3)
    axes[1].set_title(f'Gore Boxes ({len(gores_gdf)} gores)', fontsize=14)
    axes[1].set_xlabel('Longitude')
    axes[1].set_ylabel('Latitude')
    axes[1].grid(True, alpha=0.3)

    # Add gore labels
    for idx, gore in gores_gdf.iterrows():
        centroid = gore.geometry.centroid
        axes[1].text(centroid.x, centroid.y, str(idx),
                     ha='center', va='center', fontsize=10, fontweight='bold')

    # Plot 3: Countries + Gore boxes overlay
    world.plot(ax=axes[2], color='lightblue', edgecolor='black', linewidth=0.5)
    gores_gdf.plot(ax=axes[2], facecolor='none', edgecolor='red', linewidth=2)
    axes[2].set_title('Countries with Gore Box Overlay', fontsize=14)
    axes[2].set_xlabel('Longitude')
    axes[2].set_ylabel('Latitude')
    axes[2].grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"Debug plot saved to {output_path}")
    plt.show()


# debug
def plot_clipped_example(world, gores_gdf, country_name='United States of America',
                         output_path='../outputs/debug_clipped_example.png'):
    """Plot an example of how a specific country gets clipped by gores"""
    # Find the country
    country = world[world['ADMIN'] == country_name].iloc[0]
    country_geom = country.geometry

    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    axes = axes.flatten()

    # Plot original country
    gpd.GeoSeries([country_geom]).plot(ax=axes[0], color='blue', alpha=0.5)
    axes[0].set_title(f'Original: {country_name}', fontsize=12)
    axes[0].grid(True, alpha=0.3)

    # Get relevant gores
    lon_min, lat_min, lon_max, lat_max = country_geom.bounds
    gore_width = 360 / len(gores_gdf)
    start_gore = max(0, int((lon_min + 180) / gore_width))
    end_gore = min(len(gores_gdf) - 1, int((lon_max + 180) / gore_width))

    # Plot each clipped piece
    plot_idx = 1
    for gore_idx in range(start_gore, min(end_gore + 1, start_gore + 5)):  # Limit to 5 gores
        gore_geom = gores_gdf.loc[gore_idx, 'geometry']
        clipped = country_geom.intersection(gore_geom)

        if not clipped.is_empty:
            # Plot gore box
            gpd.GeoSeries([gore_geom]).plot(ax=axes[plot_idx], facecolor='none',
                                            edgecolor='red', linewidth=2)
            # Plot original country outline
            gpd.GeoSeries([country_geom]).plot(ax=axes[plot_idx], facecolor='none',
                                               edgecolor='blue', linewidth=1, alpha=0.5)
            # Plot clipped result
            gpd.GeoSeries([clipped]).plot(ax=axes[plot_idx], color='green', alpha=0.7)
            axes[plot_idx].set_title(f'Gore {gore_idx}: Clipped', fontsize=12)
            axes[plot_idx].grid(True, alpha=0.3)
            plot_idx += 1

            if plot_idx >= len(axes):
                break

    # Hide unused subplots
    for idx in range(plot_idx, len(axes)):
        axes[idx].axis('off')

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"Clipped example plot saved to {output_path}")
    plt.show()


def map_polygon_to_gore(gore_boundaries, gore_index, polygon):
    """Map a polygon from lon/lat to gore coordinate space with proper interpolation based on y_gore values"""
    x, y = polygon.exterior.xy
    gore_x, gore_y = [], []

    x_left, x_right, y_gore = gore_boundaries[gore_index]
    gore_width = 360 / len(gore_boundaries)  # Should be 30 for 12 gores

    # Calculate the longitude range for THIS specific gore
    gore_lon_min = -180 + (gore_index * gore_width)
    gore_lon_max = gore_lon_min + gore_width

    # Convert lists to numpy arrays for easier interpolation
    y_gore_array = np.array(y_gore)
    x_left_array = np.array(x_left)
    x_right_array = np.array(x_right)

    for lon_point, lat_point in zip(x, y):
        # Calculate position within THIS gore (0 to 1)
        relative_lon = (lon_point - gore_lon_min) / gore_width
        relative_lat = (lat_point + 90) / 180

        # Clamp values to [0, 1] to handle floating point errors
        relative_lon = max(0, min(1, relative_lon))
        relative_lat = max(0, min(1, relative_lat))

        # Map relative_lat to the actual y coordinate in gore space
        # y_gore ranges from its min to max value (typically bottom to top of gore)
        target_y = y_gore_array[0] + relative_lat * (y_gore_array[-1] - y_gore_array[0])

        # Find the two points in y_gore that bracket target_y
        # Use searchsorted to find where target_y would fit in the sorted y_gore array
        if y_gore_array[-1] > y_gore_array[0]:
            # y_gore is increasing (normal case)
            idx_upper = np.searchsorted(y_gore_array, target_y)
        else:
            # y_gore is decreasing (shouldn't happen but handle it)
            idx_upper = np.searchsorted(y_gore_array[::-1], target_y)
            idx_upper = len(y_gore_array) - idx_upper

        # Clamp indices
        idx_upper = max(1, min(len(y_gore_array) - 1, idx_upper))
        idx_lower = idx_upper - 1

        # Calculate interpolation weight based on actual y values
        y_lower = y_gore_array[idx_lower]
        y_upper = y_gore_array[idx_upper]

        if abs(y_upper - y_lower) < 1e-10:
            # Points are essentially the same, use lower point
            t = 0.0
        else:
            t = (target_y - y_lower) / (y_upper - y_lower)
            t = max(0, min(1, t))  # Clamp to [0, 1]

        # Interpolate to get the actual y position
        y_pos = y_lower * (1 - t) + y_upper * t

        # Interpolate left and right boundaries at this y position
        x_left_interp = x_left_array[idx_lower] * (1 - t) + x_left_array[idx_upper] * t
        x_right_interp = x_right_array[idx_lower] * (1 - t) + x_right_array[idx_upper] * t

        # Calculate final x position
        x_pos = x_left_interp + relative_lon * (x_right_interp - x_left_interp)

        gore_x.append(x_pos)
        gore_y.append(y_pos)

    return gore_x, gore_y


def draw_countries_on_gores(world_shapefile, fig, ax, gore_boundaries, draw_countries=True,
                            use_simplified=True, debug_plots=False):
    if not draw_countries:
        return  # If country drawing is disabled, exit early

    # Determine which file to load
    if use_simplified:
        # Try to use simplified geopackage first
        simplified_path = world_shapefile.replace('.shp', '_simplified.gpkg')
        if os.path.exists(simplified_path):
            print(f"Loading simplified geopackage from {simplified_path}...")
            world = gpd.read_file(simplified_path)
        else:
            print(f"Simplified file not found: {simplified_path}")
            print(f"Loading original shapefile from {world_shapefile}...")
            world = gpd.read_file(world_shapefile)
    else:
        # Load the original shapefile
        print(f"Loading shapefile from {world_shapefile}...")
        world = gpd.read_file(world_shapefile)

    # Ensure it's in EPSG:4326
    if world.crs is None:
        world = world.set_crs('EPSG:4326')
    elif world.crs != 'EPSG:4326':
        print(f"Reprojecting from {world.crs} to EPSG:4326...")
        world = world.to_crs('EPSG:4326')

    # Create gore polygons as GeoDataFrame
    print("Creating gore polygons as GeoDataFrame...")
    gores_gdf = create_gore_polygons_gdf(gore_boundaries, num_gores=len(gore_boundaries))

    # Create debug plots if requested
    if debug_plots:
        print("Creating debug plots...")
        plot_debug_geopackages(world, gores_gdf)
        plot_clipped_example(world, gores_gdf, country_name='United States of America')
        plot_clipped_example(world, gores_gdf, country_name='Russia')
        print("Debug plots created. Check the outputs folder.")
        return  # Exit after creating debug plots

    # Iterate over all countries and plot them
    for country in tqdm(world.itertuples(), total=len(world), desc="Drawing countries", unit="country"):
        country_name = country.ADMIN

        # Generate a random shade of green
        random_green = (random.uniform(0, 0.5), random.uniform(0.5, 1), random.uniform(0, 0.5))

        # Get country geometry
        country_geom = country.geometry

        if country_geom is None or country_geom.is_empty:
            continue

        # Find which gores this country intersects
        country_bounds = country_geom.bounds
        lon_min, lat_min, lon_max, lat_max = country_bounds

        # Quick check: which gores could this country intersect?
        gore_width = 360 / len(gore_boundaries)
        start_gore = max(0, int((lon_min + 180) / gore_width))
        end_gore = min(len(gore_boundaries) - 1, int((lon_max + 180) / gore_width))

        # Handle antimeridian crossing
        if lon_max - lon_min > 180:
            # Process all gores for countries that span most of the world
            potential_gores = range(len(gore_boundaries))
        else:
            potential_gores = range(start_gore, end_gore + 1)

        # Process each relevant gore
        for gore_idx in potential_gores:
            try:
                gore_geom = gores_gdf.loc[gore_idx, 'geometry']

                # Clip country to this gore using overlay
                clipped = country_geom.intersection(gore_geom)

                if clipped.is_empty:
                    continue

                # Handle different geometry types
                if clipped.geom_type == 'Polygon':
                    polygons = [clipped]
                elif clipped.geom_type == 'MultiPolygon':
                    polygons = list(clipped.geoms)
                elif clipped.geom_type == 'GeometryCollection':
                    polygons = [g for g in clipped.geoms if g.geom_type in ['Polygon', 'MultiPolygon']]
                    # Flatten MultiPolygons
                    flat_polygons = []
                    for poly in polygons:
                        if poly.geom_type == 'Polygon':
                            flat_polygons.append(poly)
                        elif poly.geom_type == 'MultiPolygon':
                            flat_polygons.extend(list(poly.geoms))
                    polygons = flat_polygons
                else:
                    continue

                # Map each clipped polygon to gore coordinates and plot
                for polygon in polygons:
                    if polygon.geom_type != 'Polygon' or polygon.is_empty:
                        continue

                    try:
                        gore_x, gore_y = map_polygon_to_gore(gore_boundaries, gore_idx, polygon)

                        if len(gore_x) < 3:
                            continue

                        # Plot the polygon
                        ax.fill(gore_x, gore_y, color=random_green, linewidth=0, edgecolor='none')

                    except Exception as e:
                        # Skip problematic polygons
                        continue

            except Exception as e:
                # Skip gores that cause errors
                continue

    print("Countries have been mapped onto the gores.")


def save_plot_as_svg(fig, filename="world_on_gores.svg"):
    # Save the figure to an SVG file
    print("Saving SVG file...")
    fig.savefig(filename, format='svg')
