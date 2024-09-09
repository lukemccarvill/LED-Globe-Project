import matplotlib.pyplot as plt
import numpy as np
import geopandas as gpd
import random
from gore_drawer import plot_multiple_gores

random.seed(42)  # to get consistent green countries

def map_country_to_gore(gore_boundaries, lon, lat):
    gore_x, gore_y = [], []
    for lon_point, lat_point in zip(lon, lat):
        gore_index = int((lon_point + 180) / 30)
        if gore_index >= len(gore_boundaries):
            continue
        
        x_left, x_right, y = gore_boundaries[gore_index]
        relative_lon = ((lon_point + 180) % 30) / 30
        relative_lat = (lat_point + 90) / 180

        num_points = len(x_left)
        y_pos = y[int(relative_lat * (num_points - 1))]
        x_pos = x_left[int(relative_lat * (num_points - 1))] + relative_lon * (x_right[int(relative_lat * (num_points - 1))] - x_left[int(relative_lat * (num_points - 1))])

        gore_x.append(x_pos)
        gore_y.append(y_pos)

    return gore_x, gore_y

def draw_countries_on_gores(world_shapefile, fig, ax, gore_boundaries, draw_countries=True, simplify_tolerance=0.1):
    if not draw_countries:
        return  # If country drawing is disabled, exit early

    # Load the shapefile
    print("Loading shapefile...")
    world = gpd.read_file(world_shapefile)

    # Simplify geometries
    print("Simplifying geometries...")
    world['geometry'] = world['geometry'].apply(lambda geom: geom.simplify(tolerance=simplify_tolerance))

    # Iterate over all countries and plot them
    for _, country in world.iterrows():
        country_name = country['ADMIN']
        print(f"Starting {country_name}...")
        
        # Generate a random shade of green
        random_green = (random.uniform(0, 0.5), random.uniform(0.5, 1), random.uniform(0, 0.5))
        
        if country.geometry.geom_type == 'Polygon':
            polygons = [country.geometry]
        elif country.geometry.geom_type == 'MultiPolygon':
            polygons = list(country.geometry.geoms)
        else:
            continue

        for polygon in polygons:
            x, y = polygon.exterior.xy
            gore_x, gore_y = map_country_to_gore(gore_boundaries, np.array(x), np.array(y))
            if gore_x and gore_y:
                ax.fill(gore_x, gore_y, color=random_green, linewidth=0)
        
        print(f"Finished {country_name}.")

    print("Countries have been mapped onto the gores.")

def save_plot_as_svg(fig, filename="world_on_gores.svg"):
    # Save the figure to an SVG file
    print("Saving SVG file...")
    fig.savefig(filename, format='svg')
