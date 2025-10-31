# Master script for a repo created by Luke McCarvill in Aug/Sept 2024. Significant ChatGPT usage throughout! This was my first Python project.
# Support from Dr. Andrew Swingler and Riley Fitzpatrick.
#
# This script creates a crisp 4000x2000mm gores-based SVG map with ability to enable the gores, countries, and LED placements.
#   it can allow you to manually move LED marker placements in QGIS (or similar GIS software) by moving the GeoJSON dot vectors using the manual mode TRUE
#   it gives you helpful information about which countries need LEDs (due to failed auto placement)
#   it draws an equator, if you want
#   it creates a pick-and-place Excel file with sheets for each gore-half to be manufactured. The global csv is likely not useful and just a transient step.
#   ensure you've closed any files (QGIS, Excel, etc) before getting python to work on them, or else it will likely throw a permissions error
# Note: many of the scripts are not appropriately generalizable using vars; num_gores, width, and height should really be editable in main but those values are hardcoded elsewhere

import matplotlib
matplotlib.use("TkAgg")   # Luke needs this for it to run. matplotlib needs a backend; this will fix an issue if the user's env doesn't already have a gui backend
import matplotlib.pyplot as plt
from dataclasses import dataclass
from LEDs import *
from gores import *
from config import *

# ~~~ to interface with gui
@dataclass
class Options:
    draw_gores: bool = True  # set to False if you don't want gore outlines
    draw_equator: bool = True # set to True if you want a black line along the equator to divide gore halves
    draw_countries: bool = True  # set to False if you don't want country mappings
    draw_leds: bool = True  # set to False if you don't want LED markings
    place_ocean: bool = True  # set to True to put missing LEDs in ocean
    use_edited_geojson: bool = False  # Set to True to use a previously edited GeoJSON file from the data folder
    manual_manipulation: bool = False  # set to True to enable manual manipulation mode. NORMALLY FALSE.
    create_coords_for_manufact: bool = False  # Toggle this to create gore half coordinates for pick-and-place
    use_simplified_countries: bool = True  # Set to True to use pre-simplified geopackage (faster loading)
    require_backend = False # Set to True if your env doesn't already have a gui backend

    raster_choice: str = "population"   # one of: "population", "nightlights", "ghs_volume", "ghs_surface"
    raster_year: int = 2025 # all options except nightlights have options 1975-2025 except nightlights which is fixed to 2024

    # Color mode selection
    COLOR_MODE = 'leds'  # Options: 'continent', 'leds'

# ~~~

def run(opts: Options):
    """Like original, but using opts.<field? rather than bare variables"""
    # Get the root directory of the project (assumes script is run from within the project structure)
    project_root = os.path.dirname(os.path.dirname(__file__))

    # Define relative paths based on the project structure
    data_dir = os.path.join(project_root, 'data')
    raster_dir = os.path.join(data_dir, "rasters")
    transient_dir = os.path.join(project_root, 'transients') # these are temp/middle-of-the-process files
    output_dir = os.path.join(project_root, 'outputs')

    # Ensure the output directory exists
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # paths for data, transients, and output files
    shapefile_path = os.path.join(data_dir, 'ne_10m_admin_0_countries.shp') # may need other files rather than just shp?

    # raster_path = os.path.join(data_dir, 'gpw_v4_population_density_rev11_2020_30_min.tif')
    # raster_dir = os.path.join(project_root, 'nightlight_vs_population') # I DONT THINK WE NEED THE NIGHTLIGHT VS POP FOLDER AT ALL ANYMORE ~~~

    def _find_raster(patterns):
        if os.path.isdir(raster_dir):
            for f in os.listdir(raster_dir):
                fl = f.lower()
                # return the first matching tif that contains any of the patterns
                if fl.endswith('.tif') and any(p in fl for p in patterns):
                    return os.path.join(raster_dir, f)
        return None

    if opts.raster_choice == "population":
        raster_path = _find_raster(['pop', 'dens'])
    elif opts.raster_choice == "nightlights":
        raster_path = _find_raster(['night', 'light', 'viirs', 'ntl'])
    else:
        raster_path = None
    # These geopackages are expected to live in data/rasters and contain per-year columns used by the allocator.
    timeseries_map = {
        "population": "GHS_POP_timeseries_points.gpkg",
        "ghs_volume": "GHS_BUILT_V_timeseries_points.gpkg",
        "ghs_surface": "GHS_BUILT_S_timeseries_points.gpkg",
        "nightlights": "nightlight_timeseries_points.gpkg",
    }

    chosen = getattr(opts, "raster_choice", "population")
    chosen_file = timeseries_map.get(chosen, "GHS_POP_timeseries_points.gpkg")
    energy_raster_path = os.path.join(raster_dir, chosen_file)
    country_energy_path = os.path.join(data_dir, 'Country Energy Data.xlsx')
    # Store previously edited geoJSON file in 'data' directory as well, if you want it to be used in the code.

    # Use the year selected in the GUI (or default)
    year = getattr(opts, "raster_year", 2025)

    # Print user-facing confirmation of chosen raster and year
    print(f"Selected raster family: {chosen} -> {chosen_file}")
    print(f"Selected raster year: {year}")

    # Validate the chosen geopackage exists and offer helpful feedback/fallback
    if not os.path.exists(energy_raster_path):
        print(f"Warning: expected geopackage '{chosen_file}' not found at:\n  {energy_raster_path}")
        if os.path.isdir(raster_dir):
            found = [f for f in os.listdir(raster_dir) if f.lower().endswith('.gpkg')]
        else:
            found = []

        if found:
            print("Found these .gpkg files in data/rasters:")
            for f in found:
                print(f"  - {f}")
            # Prefer any timeseries file, otherwise pick first gpkg as fallback
            fallback = next((f for f in found if 'timeseries' in f.lower()), found[0])
            energy_raster_path = os.path.join(raster_dir, fallback)
            print(f"Falling back to: {fallback}\nUsing: {energy_raster_path}")
        else:
            raise FileNotFoundError(
                f"No .gpkg files found in {raster_dir}. Please add '{chosen_file}' or a valid geopackage before running.")

    energy_timeseries = gpd.read_file(energy_raster_path)
    geojson_output_path = os.path.join(transient_dir, 'led_positions_for_manual_edit.geojson')
    output_svg_filename = os.path.join(output_dir, 'full_map_4m_by_2m.svg')

    # Parameters for the final output
    tot_leds = 3500 # number of leds to add
    final_width = 4 # meters
    final_height = 2 # meters
    led_width = 0.002 # meters (2mm)
    led_height = 0.0035 # meters (3.5mm)
    num_gores = 12  # number of gores to draw

    # Establish gui backend if user specifies
    if opts.require_backend:
        matplotlib.use('TkAgg')

    # Load the country shapefile and LED data - old method
    #world = gpd.read_file(shapefile_path)
    #led_data = pd.read_excel(country_energy_path)
    # chosen_column = [str(col) for col in led_data.columns if "Chosen" in str(col)][0] # Find the column that contains the string "Chosen"
    led_data = pd.read_csv("../data/API/global_energy_consumption.csv") # new way of allocating leds

    
    #### USING THE NEW WAY OF DETERMINING THE NUMBER OF LEDS - DO WE EVEN NEED THIS SECTION ANYMORE? CAN WE EDIT SOME OF THIS
    # Do we want to keep the old way of manually editing data now that we can dynamically update from API + dynamically allocate LEDs, even when out of cells to place them
    # Check if the edited GeoJSON file exists and use it if the flag is set
    if opts.use_edited_geojson:
        geojson_files = [f for f in os.listdir(data_dir) if f.endswith('.geojson')]
        if len(geojson_files) == 1:
            print(f"Using the GeoJSON file: {geojson_files[0]}")
            all_leds_gdf = gpd.read_file(os.path.join(data_dir, geojson_files[0]))
        elif len(geojson_files) == 0:
            print("No GeoJSON files found in the data folder.")
        else:
            print(f"Multiple GeoJSON files found: {geojson_files}. Please ensure only one file is present.")

    elif opts.manual_manipulation and opts.draw_leds and os.path.exists(geojson_output_path):
        print("Manual manipulation mode enabled. Loading the manual edit GeoJSON file from the transients folder.")
        all_leds_gdf = gpd.read_file(geojson_output_path)
    else:
        # Filter the LED data to include only the top entities and drop NaN values
        #led_data = led_data[led_data[chosen_column] > 0].dropna(subset=[chosen_column])
        # Allocate LEDs based on population
        led_data = determine_num_leds(led_data, not_countries, year, tot_leds)
        all_leds_gdf = allocate_leds(led_data, energy_timeseries, year, alias, allocate_leds=opts.draw_leds, place_ocean=opts.place_ocean, manual_manipulation=opts.manual_manipulation, geojson_output_path=geojson_output_path)

    #raster_path = os.path.join(data_dir, 'gpw_v4_population_density_rev11_2020_30_min.tif')
    energy_raster_path = os.path.join(raster_dir, "GHS_BUILT_S_timeseries_points.gpkg")
    #country_energy_path = os.path.join(data_dir, 'Country Energy Data.xlsx')
    # Store previously edited geoJSON file in 'data' directory as well, if you want it to be used in the code.
    
    energy_timeseries = gpd.read_file(energy_raster_path)
    geojson_output_path = os.path.join(transient_dir, 'led_positions_for_manual_edit.geojson')
    output_svg_filename = os.path.join(output_dir, 'full_map_4m_by_2m.svg')

    # Parameters for the final output -- put these in GUI eventually?
    year = 2025
    tot_leds = 3500 # number of leds to add
    final_width = 4 # meters
    final_height = 2 # meters
    led_width = 0.002 # meters (2mm)
    led_height = 0.0035 # meters (3.5mm)
    num_gores = 12  # number of gores to draw

    # Establish gui backend if user specifies
    if opts.require_backend:
        matplotlib.use('TkAgg')

    # Load the country shapefile and LED data - old method
    #world = gpd.read_file(shapefile_path)
    #led_data = pd.read_excel(country_energy_path)
    # chosen_column = [str(col) for col in led_data.columns if "Chosen" in str(col)][0] # Find the column that contains the string "Chosen"
    led_data = pd.read_csv("../data/API/global_energy_consumption.csv") # new way of allocating leds

    
    #### USING THE NEW WAY OF DETERMINING THE NUMBER OF LEDS - DO WE EVEN NEED THIS SECTION ANYMORE? CAN WE EDIT SOME OF THIS
    # Do we want to keep the old way of manually editing data now that we can dynamically update from API + dynamically allocate LEDs, even when out of cells to place them
    # Check if the edited GeoJSON file exists and use it if the flag is set
    if opts.use_edited_geojson:
        geojson_files = [f for f in os.listdir(data_dir) if f.endswith('.geojson')]
        if len(geojson_files) == 1:
            print(f"Using the GeoJSON file: {geojson_files[0]}")
            all_leds_gdf = gpd.read_file(os.path.join(data_dir, geojson_files[0]))
        elif len(geojson_files) == 0:
            print("No GeoJSON files found in the data folder.")
        else:
            print(f"Multiple GeoJSON files found: {geojson_files}. Please ensure only one file is present.")

    elif opts.manual_manipulation and opts.draw_leds and os.path.exists(geojson_output_path):
        print("Manual manipulation mode enabled. Loading the manual edit GeoJSON file from the transients folder.")
        all_leds_gdf = gpd.read_file(geojson_output_path)
    else:
        # Filter the LED data to include only the top entities and drop NaN values
        #led_data = led_data[led_data[chosen_column] > 0].dropna(subset=[chosen_column])
        # Allocate LEDs based on population
        led_data = determine_num_leds(led_data, not_countries, year, tot_leds)
        all_leds_gdf = allocate_leds(led_data, energy_timeseries, year, alias, allocate_leds=opts.draw_leds, place_ocean=opts.place_ocean, manual_manipulation=opts.manual_manipulation, geojson_output_path=geojson_output_path)

        # If in manual manipulation mode, the script will exit after creating the GeoJSON
        if opts.manual_manipulation and opts.draw_leds:
            print("Manual manipulation mode is enabled. Please edit the GeoJSON file and rerun the script.")
            print("Please ensure you close QGIS before rerunning the script or else you will get an error that the GeoJSON file is being used by another software.")
            exit()  # Exit the script here to allow for manual edits


    # Set up the final figure dimensions (4000mm x 2000mm)
    fig, ax = plt.subplots(figsize=(final_width * 39.3701, final_height * 39.3701))  # Exact 4m x 2m canvas in inches

    # Draw the gores with the correct dimensions
    fig, ax, gore_boundaries = plot_multiple_gores(num_gores=num_gores, fig=fig, ax=ax, draw_outlines=opts.draw_gores, draw_equator=opts.draw_equator, width=final_width, height=final_height)

    # Draw the countries if specified
    if opts.draw_countries:
        draw_countries_on_gores(shapefile_path, fig, ax, gore_boundaries, draw_countries=True, use_simplified=opts.use_simplified_countries)

    # Plot the LEDs if specified
    if opts.draw_leds:
        plot_leds_on_gores(all_leds_gdf, ax, gore_boundaries, led_width=led_width, led_height=led_height, scale_factor=1, plot_leds=True)

    # create the coordinates, centred at bottom-left of each gore half, if specified
    if opts.create_coords_for_manufact:
        create_gorehalf_coords(transient_dir)

    # Save both PNG and simplified SVG
    output_base = output_svg_filename.replace('.svg', '')

    # Rasterized SVG (much smaller)
    for collection in ax.collections:
        collection.set_rasterized(True)
    fig.savefig(output_svg_filename, format="svg", dpi=300, pad_inches=0, transparent=True)
    print(f"Rasterized SVG saved as {output_svg_filename}")

    plt.show()
    plt.close(fig)

if __name__ == "__main__":
    # click run on main.py to run with defaults (no gui)
    run(Options())


#def save_plot_as_svg(fig, filename="world_on_gores.svg"):
    # Save the figure to an SVG file
    #print("Saving SVG file...")
    #fig.savefig(filename, format='svg')
