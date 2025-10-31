"""
Gore-based map projection and rendering utilities.

This module handles the creation of sinusoidal gore projections for displaying global geographic data on a 4000x2000mm
physical map. Includes functions for rendering countries, placing LEDs, and generating manufacturing coordinates.

"""

import pandas as pd
import geopandas as gpd
import random
from shapely.geometry import Polygon
from tqdm import tqdm
import os
import numpy as np
import matplotlib.pyplot as plt
import csv
from matplotlib.patches import Rectangle

from config import countries_by_continent, continent_colors

random.seed(42)  # to get consistent green countries


# Create and render multiple gore projections for the globe map
def plot_multiple_gores(num_gores=12, fig=None, ax=None, draw_outlines=True, draw_equator=False, width=4, height=2):
    # Set exact canvas size 4000mm x 2000mm
    if fig is None or ax is None:
        fig, ax = plt.subplots(figsize=(width * 39.3701, height * 39.3701))  # 4000mm x 2000mm canvas in inches

    equator_width = width / num_gores  # Width of each gore at the equator
    gore_boundaries = []

    for i in range(num_gores):
        # Calculate center and y-range for each gore
        center_x = (i * equator_width) - (width / 2) + (equator_width / 2)
        y = np.linspace(-height / 2, height / 2, 500)  # Full height (2000mm)

        # Calculate x-values for left and right edges of the gore
        x_left = center_x - (equator_width / 2) * (1 - (np.abs(y) / (height / 2))**2)
        x_right = center_x + (equator_width / 2) * (1 - (np.abs(y) / (height / 2))**2)

        # Plot the gore outlines and fill them
        if draw_outlines:
            ax.plot(x_left, y, 'k-', lw=0.5)
            ax.plot(x_right, y, 'k-', lw=0.5)
            ax.fill_betweenx(y, x_left, x_right, color='lightgray', alpha=0.5)

        gore_boundaries.append((x_left, x_right, y))

    # Draw the equator line if specified
    if draw_equator:
        ax.plot([-width / 2, width / 2], [0, 0], 'k-', lw=0.5)  # Equator at y=0

    # Set axis limits exactly to the canvas size (4000mm x 2000mm)
    ax.set_xlim(-width / 2, width / 2)
    ax.set_ylim(-height / 2, height / 2)

    # Ensure strict aspect ratio with no additional scaling
    ax.set_aspect('equal')

    # Remove any padding, margins, or extra space
    plt.subplots_adjust(left=0, right=1, top=1, bottom=0)  # THIS LINE OF CODE SAVED THE SPACING/SHRINKING ISSUE
    ax.margins(0)  # Set margins to zero
    ax.axis('off')  # Turn off axes

    return fig, ax, gore_boundaries


# Create GeoDataFrame of gore polygon boundaries in lon/lat space (EPSG:4326)
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


# Transform a polygon from lon/lat coordinates to gore projection space
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


# Interpolate x and y positions along gore boundaries for a given latitude
def interpolate_between_points(y, x_left, x_right, relative_lat):
    num_points = len(y)
    index_below = int(relative_lat * (num_points - 1))
    index_above = min(index_below + 1, num_points - 1)
    fraction = (relative_lat * (num_points - 1)) - index_below

    # Interpolating y position
    y_pos = y[index_below] + fraction * (y[index_above] - y[index_below])

    # Interpolating x positions
    x_left_pos = x_left[index_below] + fraction * (x_left[index_above] - x_left[index_below])
    x_right_pos = x_right[index_below] + fraction * (x_right[index_above] - x_right[index_below])

    return y_pos, x_left_pos, x_right_pos


# Render country polygons mapped onto gore projections
def draw_countries_on_gores(world_shapefile, fig, ax, gore_boundaries, draw_countries=True,
                            use_simplified=True, debug_plots=False, all_leds_gdf=None, color_by_leds=False):
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

    # If coloring by LEDs, calculate LED count per country
    led_counts = None
    norm = None
    if color_by_leds and all_leds_gdf is not None:
        import matplotlib.colors as mcolors

        # Count LEDs per country by spatial join
        world_with_leds = gpd.sjoin(world, all_leds_gdf, how='left', predicate='contains')
        led_counts = world_with_leds.groupby(world_with_leds.index).size()

        # Create normalization for intensity
        max_leds = led_counts.max() if len(led_counts) > 0 else 1
        min_leds = led_counts.min() if len(led_counts) > 0 else 0
        norm = mcolors.Normalize(vmin=min_leds, vmax=max_leds)

        print(f"LED count range: {min_leds} to {max_leds}")

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
        continent = getattr(country, 'CONTINENT', None)

        # Get base color from continent
        if continent and continent in continent_colors:
            base_color = continent_colors[continent]
        else:
            base_color = '#FF0000'  # Bright red for unmapped countries
            print(f"Warning: No continent mapping for {country_name} (continent: {continent})")

        # Use base continent color
        country_color = base_color

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
                        ax.fill(gore_x, gore_y, color=country_color, linewidth=0, edgecolor='black')

                    except Exception as e:
                        # Skip problematic polygons
                        continue

            except Exception as e:
                # Skip gores that cause errors
                continue

    print("Countries have been mapped onto the gores.")


# Map arrays of lon/lat coordinates (e.g., LED positions) to gore space
def map_raster_to_gore(gore_boundaries, lon, lat):
    gore_x, gore_y = [], []
    for lon_point, lat_point in zip(lon, lat):
        gore_index = int((lon_point + 180) / 30)
        if gore_index >= len(gore_boundaries):
            continue

        x_left, x_right, y = gore_boundaries[gore_index]
        relative_lon = ((lon_point + 180) % 30) / 30
        relative_lat = (lat_point + 90) / 180

        y_pos, x_left_pos, x_right_pos = interpolate_between_points(y, x_left, x_right, relative_lat)
        x_pos = x_left_pos + relative_lon * (x_right_pos - x_left_pos)

        gore_x.append(x_pos)
        gore_y.append(y_pos)

    return gore_x, gore_y


# Render LED positions as rectangles on gore map and export coordinates to CSV
def plot_leds_on_gores(all_leds_gdf, ax, gore_boundaries, led_width=0.002, led_height=0.0035, scale_factor=1, plot_leds=True):
    # Define the path to the 'transients' folder in the repository
    project_root = os.path.dirname(os.path.dirname(__file__))  # Assuming script is run from 'src'
    transients_dir = os.path.join(project_root, 'transients')

    # Create the 'transients' folder if it doesn't exist
    if not os.path.exists(transients_dir):
        os.makedirs(transients_dir)

    # Path to save the CSV file
    csv_output_path = os.path.join(transients_dir, "led_coordinates_global.csv")

    if not plot_leds:
        return  # If LED plotting is disabled, exit early

    # Extract LED coordinates
    led_lon = all_leds_gdf.geometry.x
    led_lat = all_leds_gdf.geometry.y

    # Open the CSV file to write the pick-and-place data
    with open(csv_output_path, mode='w', newline='') as file:
        writer = csv.writer(file)

        # Create the header row without the blank column
        writer.writerow(["X (mm)", "Y (mm)", "Gore Section"])

        # Map the LED data to the gores
        gore_x, gore_y = map_raster_to_gore(gore_boundaries, led_lon, led_lat)

        # Scale the dimensions of the rectangles
        rect_width = led_width * scale_factor  # Adjusted width in plot units
        rect_height = led_height * scale_factor  # Adjusted height in plot units

        # Plot the LED data as rectangles on the gores
        for lon, lat, x, y in zip(led_lon, led_lat, gore_x, gore_y):
            rect = Rectangle((x - rect_width / 2, y - rect_height / 2), rect_width, rect_height, facecolor='#FFBF00', edgecolor='none')
            ax.add_patch(rect)

            # Determine the gore section and hemisphere
            gore_index = int((lon + 180) / 30) + 1  # Gore section number (1-12)
            hemisphere = "N" if lat >= 0 else "S"  # North or South
            section_label = f"{gore_index}{hemisphere}"

            # Write to CSV: X, Y, Gore Section
            writer.writerow([x * 1000, y * 1000, section_label])

    print(f"CSV saved at {csv_output_path}")
    print("LED rectangles plotted on the gores.")


# Convert global gore coordinates to individual gore-half manufacturing coordinates
def translate_coords(x, y, gore_section):
    # Define width and height of each gore half
    gore_width = 4000 / 12  # mm # THIS SHOULD BE CHANGED TO TAKE THE ACTUAL VARIABLE FROM MAIN IN THE FUTURE
    gore_height = 1000  # mm

    # Get the gore number and hemisphere from the section
    gore_num = int(gore_section[:-1])  # Get gore number (1-12)
    hemisphere = gore_section[-1]  # Get hemisphere (N/S)

    # Translate x-coordinates: Shift each gore section to its own 0 to 333.33 range
    x_translated = x - ((gore_num - 1) * 333.33 - 2000)

    # Translate y-coordinates: Shift northern and southern hemisphere
    if hemisphere == "N":
        y_translated = y  # Northern hemisphere coordinates stay in the range 0-1000
    else:
        y_translated = y + 1000  # Southern hemisphere is below, so shift by +1000

    return x_translated, y_translated


# Generate Excel pick-and-place file with translated coordinates for each gore half
def create_gorehalf_coords(transient_dir=None):
    """
    Create gore half coordinates for manufacturing.

    Parameters:
    -----------
    transient_dir : str, optional
        Path to the transients directory. If not provided, uses relative path.
    """

    # Construct the CSV input path
    if transient_dir is None:
        # Fallback to relative path
        csv_input_path = '../transients/led_coordinates_global.csv'
    else:
        csv_input_path = os.path.join(transient_dir, 'led_coordinates_global.csv')

    # Get the root directory of the project (assumes script is run from 'src')
    project_root = os.path.dirname(os.path.dirname(__file__))
    output_dir = os.path.join(project_root, 'outputs')

    # Ensure the 'outputs' directory exists
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Define the path for the xlsx output
    xlsx_output_path = os.path.join(output_dir, "gorehalf_coordinates_with_sheets.xlsx")

    # Read the CSV file generated from the previous script
    print(f"Reading CSV from: {csv_input_path}")
    df = pd.read_csv(csv_input_path)

    # Translate the coordinates and store them in new columns
    df[['Mid X (mm)', 'Mid Y (mm)']] = df.apply(
        lambda row: translate_coords(row['X (mm)'], row['Y (mm)'], row['Gore Section']), axis=1, result_type='expand')

    # Reorder the data to follow the gore half order: 1N, 1S, 2N, 2S, ..., 12N, 12S
    df['Sort_Key'] = df['Gore Section'].map(lambda x: (int(x[:-1]), x[-1]))
    df = df.sort_values('Sort_Key')

    # Drop the Sort_Key column since it's no longer needed
    df.drop(columns=['Sort_Key'], inplace=True)

    # Create summary of totals per gore section
    gore_sections = [f"{i}{h}" for i in range(1, 13) for h in ['N', 'S']]
    summary_data = [(section, len(df[df['Gore Section'] == section])) for section in gore_sections]
    summary_df = pd.DataFrame(summary_data, columns=['Gore Section', 'Total LEDs'])

    # Create a new Excel writer object
    with pd.ExcelWriter(xlsx_output_path, engine='openpyxl') as writer:
        # Write the summary starting in row 1
        summary_df.to_excel(writer, sheet_name='Master', startrow=0, startcol=5, index=False)

        # Write the full data starting immediately after the summary, at row 1
        df[['Mid X (mm)', 'Mid Y (mm)', 'Gore Section']].to_excel(writer, sheet_name='Master', startrow=0, index=False)

        # Loop through each gore section, create individual sheets for each
        for gore_section in gore_sections:
            section_df = df[df['Gore Section'] == gore_section]
            if not section_df.empty:
                section_df[['Mid X (mm)', 'Mid Y (mm)']].to_excel(writer, sheet_name=gore_section, index=False)

    print(f"Translated coordinates and sheets saved to {xlsx_output_path}.")


# Create diagnostic visualization showing countries, gore boxes, and their overlay
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


# Visualize how a specific country gets clipped and mapped across gore sections.
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