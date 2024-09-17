# Sept 2024: Trying to change pop density raster to nightlight raster
#
# updated raster path
# updated geojson output path
# updated output svg filename

# need to change all the details with population, country (if relevant)
# need to add option to use downsampler script somehow -- could just be a standalone script that people run so that I don't need to deal with the 11 GB raster at all.


import os
import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
from led_allocator import allocate_leds
from country_mapper import draw_countries_on_gores
from gore_drawer import plot_multiple_gores
from led_plotter import plot_leds_on_gores
from per_gorehalf_coords import create_gorehalf_coords

# Get the root directory of the project (assumes script is run from within the project structure)
project_root = os.path.dirname(os.path.dirname(__file__))

# Define relative paths based on the project structure
data_dir = os.path.join(project_root, 'data')
transient_dir = os.path.join(project_root, 'transients') # these are temp/middle-of-the-process files
output_dir = os.path.join(project_root, 'outputs')

# Ensure the output directory exists
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# paths for data, transients, and output files
shapefile_path = os.path.join(data_dir, 'ne_10m_admin_0_countries.shp') # may need other files rather than just shp?
# raster_path = os.path.join(data_dir, 'gpw_v4_population_density_rev11_2020_30_min.tif')
raster_path = os.path.join(transient_dir, 'downsampled_nightlight_30arcmin_nearestN.tif')
country_energy_path = os.path.join(data_dir, 'Country Energy Data.xlsx')
# Store previously edited geoJSON file in 'data' directory as well, if you want it to be used in the code.

# geojson_output_path = os.path.join(transient_dir, 'led_positions_for_manual_edit.geojson')
geojson_output_path = os.path.join(transient_dir, 'led_positions_for_manual_edit_nightlight.geojson')
# output_svg_filename = os.path.join(output_dir, 'full_map_4m_by_2m.svg')
output_svg_filename = os.path.join(output_dir, 'full_map_4m_by_2m_nightlight.svg')

# Parameters for the final output
final_width = 4 # meters
final_height = 2 # meters
led_width = 0.002 # meters (2mm)
led_height = 0.0035 # meters (3.5mm)
num_gores = 12  # number of gores to draw
draw_gores = True  # set to False if you don't want gore outlines
draw_equator = True # set to True if you want a black line along the equator to divide gore halves
draw_countries = True  # set to False if you don't want country mappings
draw_leds = True  # set to False if you don't want LED markings
use_edited_geojson = False  # Set to True to use a previously edited GeoJSON file from the data folder
manual_manipulation = False  # set to True to enable manual manipulation mode
create_coords_for_manufact = False  # Toggle this to create gore half coordinates for pick-and-place

# Load the country shapefile and LED data
world = gpd.read_file(shapefile_path)
led_data = pd.read_excel(country_energy_path)

# Find the column that contains the string "Chosen"
chosen_column = [str(col) for col in led_data.columns if "Chosen" in str(col)][0]

# Check if the edited GeoJSON file exists and use it if the flag is set
if use_edited_geojson:
    geojson_files = [f for f in os.listdir(data_dir) if f.endswith('.geojson')]
    if len(geojson_files) == 1:
        print(f"Using the GeoJSON file: {geojson_files[0]}")
        all_leds_gdf = gpd.read_file(os.path.join(data_dir, geojson_files[0]))
    elif len(geojson_files) == 0:
        print("No GeoJSON files found in the data folder.")
    else:
        print(f"Multiple GeoJSON files found: {geojson_files}. Please ensure only one file is present.")

elif manual_manipulation and draw_leds and os.path.exists(geojson_output_path):
    print("Manual manipulation mode enabled. Loading the manual edit GeoJSON file from the transients folder.")
    all_leds_gdf = gpd.read_file(geojson_output_path)
else:
    # Filter the LED data to include only the top entities and drop NaN values
    led_data = led_data[led_data[chosen_column] > 0].dropna(subset=[chosen_column])

    # Allocate LEDs based on population
    all_leds_gdf = allocate_leds(led_data, world, raster_path, allocate_leds=draw_leds, manual_manipulation=manual_manipulation, geojson_output_path=geojson_output_path)

    # If in manual manipulation mode, the script will exit after creating the GeoJSON
    if manual_manipulation and draw_leds:
        print("Manual manipulation mode is enabled. Please edit the GeoJSON file and rerun the script.")
        print("Please ensure you close QGIS before rerunning the script or else you will get an error that the GeoJSON file is being used by another software.")
        exit()  # Exit the script here to allow for manual edits


# Set up the final figure dimensions (4000mm x 2000mm)
fig, ax = plt.subplots(figsize=(final_width * 39.3701, final_height * 39.3701))  # Exact 4m x 2m canvas in inches

# Draw the gores with the correct dimensions
fig, ax, gore_boundaries = plot_multiple_gores(num_gores=num_gores, fig=fig, ax=ax, draw_outlines=draw_gores, draw_equator=draw_equator, width=final_width, height=final_height)

# Draw the countries if specified
if draw_countries:
    draw_countries_on_gores(shapefile_path, fig, ax, gore_boundaries, draw_countries=True, simplify_tolerance=0.1)

# Plot the LEDs if specified
if draw_leds:
    plot_leds_on_gores(all_leds_gdf, ax, gore_boundaries, led_width=led_width, led_height=led_height, scale_factor=1, plot_leds=True)

# create the coordinates, centred at bottom-left of each gore half, if specified
if create_coords_for_manufact:
    create_gorehalf_coords()

# Save the final output with tight bounding box and exact dimensions
fig.savefig(output_svg_filename, format="svg", dpi=150, pad_inches=0, transparent=True)

print(f"File saved as {output_svg_filename}")

plt.show()
plt.close(fig)
