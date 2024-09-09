import os
import numpy as np
import pandas as pd
import rasterio
from shapely.geometry import Point
import geopandas as gpd
from rasterio.mask import mask

def allocate_leds(led_data, world, raster_path, allocate_leds=True, use_edited_geojson=False, manual_manipulation=False, geojson_output_path="led_positions_for_manual_edit.geojson", prev_edited_geojson_path="prev_edited_led_positions.geojson"):
    if not allocate_leds:
        print("LED allocation skipped as draw_leds is set to False.")
        return gpd.GeoDataFrame()  # Return an empty GeoDataFrame

    # If using a previously edited GeoJSON, load that file and skip LED allocation
    if use_edited_geojson and os.path.exists(prev_edited_geojson_path):
        print(f"Using the previously edited GeoJSON file from the data folder: {prev_edited_geojson_path}")
        return gpd.read_file(prev_edited_geojson_path)

    all_leds_gdf = gpd.GeoDataFrame()  # Stores all valid LED positions

    with rasterio.open(raster_path) as src:
        nodata_value = src.nodata  # Get the No Data value from the raster

        for index, row in led_data.iterrows():
            country_name = row['Entity']
            num_leds = int(row['Round'])
            leds_placed = 0

            try:
                # Get the country's geometry from the world GeoDataFrame
                country_geom = world[world['ADMIN'] == country_name].geometry.iloc[0]
                out_image, out_transform = mask(src, [country_geom], crop=True)
                population_array = out_image[0]

                flat_population = population_array.flatten()
                sorted_indices = flat_population.argsort()[::-1]  # Sort by population density (highest first)

                available_cells = len(sorted_indices)
                if num_leds > available_cells:
                    print(f"Warning: {country_name} requested {num_leds} LEDs, but only {available_cells} cells are available. Attempting to place {available_cells} LEDs.")

                rows, cols = divmod(sorted_indices[:num_leds], population_array.shape[1])

                for r, c in zip(rows, cols):
                    pop_value = population_array[r, c]

                    # Stop placing LEDs when encountering problematic values
                    if pop_value <= 0 or pop_value == nodata_value:
                        print(f"Encountered problematic value for {country_name}. Stopping LED placement. {leds_placed} LEDs placed out of {num_leds} requested.")
                        break

                    # Calculate the geographical coordinates of the LED position
                    x, y = out_transform * (c + 0.5, r + 0.5)
                    all_leds_gdf = pd.concat([all_leds_gdf, gpd.GeoDataFrame({
                        'geometry': [Point(x, y)],
                        'Country': [country_name],
                        'Pop_Density': [pop_value]
                    }, geometry='geometry')], ignore_index=True)

                    leds_placed += 1

                if leds_placed < num_leds:
                    print(f"Warning: {country_name} requested {num_leds} LEDs, but only {leds_placed} were placed due to problematic values.")

            except IndexError:
                print(f"Could not find geometry for {country_name}, skipping...")

    # Set the CRS of the GeoDataFrame
    all_leds_gdf.set_crs(src.crs, inplace=True)

    # If manual manipulation is enabled, output the GeoJSON to the transients folder
    if manual_manipulation:
        all_leds_gdf.to_file(geojson_output_path, driver='GeoJSON')
        print(f"LED positions saved to {geojson_output_path} for manual manipulation.")
        return all_leds_gdf  # Return the GeoDataFrame for further processing if needed

    return all_leds_gdf
