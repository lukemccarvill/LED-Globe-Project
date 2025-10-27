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


def map_polygon_to_gore(gore_boundaries, gore_index, polygon):
    """Map a polygon from lon/lat to gore coordinate space"""
    x, y = polygon.exterior.xy
    gore_x, gore_y = [], []

    x_left, x_right, y_gore = gore_boundaries[gore_index]
    gore_width = 30  # degrees

    for lon_point, lat_point in zip(x, y):
        relative_lon = ((lon_point + 180) % gore_width) / gore_width
        relative_lat = (lat_point + 90) / 180

        num_points = len(x_left)
        y_index = int(relative_lat * (num_points - 1))
        y_index = max(0, min(y_index, num_points - 1))

        y_pos = y_gore[y_index]
        x_pos = x_left[y_index] + relative_lon * (x_right[y_index] - x_left[y_index])

        gore_x.append(x_pos)
        gore_y.append(y_pos)

    return gore_x, gore_y


def draw_countries_on_gores(world_shapefile, fig, ax, gore_boundaries, draw_countries=True, use_simplified=True):
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

    # Note: No need to simplify again if using the simplified file

    # Create gore polygons as GeoDataFrame
    print("Creating gore polygons as GeoDataFrame...")
    gores_gdf = create_gore_polygons_gdf(gore_boundaries, num_gores=len(gore_boundaries))

    # Optional: Save to geopackage for debugging
    # gores_gdf.to_file("gores.gpkg", driver="GPKG")
    # world.to_file("countries.gpkg", driver="GPKG")

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