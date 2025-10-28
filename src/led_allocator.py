import os
#import numpy as np
import pandas as pd
#import rasterio
#from shapely.geometry import Point
import geopandas as gpd
#from rasterio.mask import mask

def allocate_leds(led_data, energy_timeseries, year, allocate_leds=True, place_ocean=True, use_edited_geojson=False, manual_manipulation=False, geojson_output_path="led_positions_for_manual_edit.geojson", prev_edited_geojson_path="prev_edited_led_positions.geojson"):
    if not allocate_leds:
        print("LED allocation skipped as draw_leds is set to False.")
        return gpd.GeoDataFrame()  # Return an empty GeoDataFrame

    # If using a previously edited GeoJSON, load that file and skip LED allocation
    if use_edited_geojson and os.path.exists(prev_edited_geojson_path):
        print(f"Using the previously edited GeoJSON file from the data folder: {prev_edited_geojson_path}")
        return gpd.read_file(prev_edited_geojson_path)

    all_leds_gdf = gpd.GeoDataFrame()  # Stores all valid LED positions

    for index,row in led_data.iterrows():

        country_name = row['Entity']
        num_leds = int(row['Round'])
        leds_placed = 0

        values_array = energy_timeseries[energy_timeseries['country'] == country_name]
        values_array = values_array[["point_index", f"{year}", "geometry"]].sort_values(f"{year}", ascending=False)

        available_cells = len(values_array)
        missing_leds = num_leds - available_cells
        
        if available_cells == 0:
            print(f"Could not find {country_name} in raster data, skipping...")

        else:

            for leds in range(0,num_leds-leds_placed): # Place LEDs on the land-space

                if leds_placed < available_cells: 
                    
                    all_leds_gdf = pd.concat([all_leds_gdf, gpd.GeoDataFrame({'geometry': [values_array["geometry"].iloc[leds]],
                                                                            'Country': [country_name],
                                                                            'Raster_Density': [values_array[f"{year}"].iloc[leds]]
                                                                            }, geometry='geometry')], ignore_index=True)
                    leds_placed += 1

                else:

                    if place_ocean == True:

                        if leds_placed >= num_leds:
                            break

                        print(f"Warning: {country_name} requested {num_leds} LEDs, but only {available_cells} cells are available. Attempting to place {missing_leds} LEDs in surrounding area.")
                        values_sorted = energy_timeseries.iloc[energy_timeseries.geometry.x.argsort().values].reset_index(drop=True)
                        surround = 1
                        
                        while leds_placed < num_leds:

                            values_sorted_filtered = values_sorted[values_sorted['country'] == country_name]
                            surround_indices = [x-surround for x in values_sorted_filtered.index] + [x+surround for x in values_sorted_filtered.index] 
                            surround_indices = values_sorted.loc[surround_indices].query("country.isnull()").index
                            values_sorted.loc[surround_indices, "country"] = country_name

                            for leds in surround_indices: # Place remaining LEDs on the land-space
                                all_leds_gdf = pd.concat([all_leds_gdf, gpd.GeoDataFrame({'geometry': [values_sorted["geometry"].iloc[leds]],
                                                                                        'Country': [country_name],
                                                                                        'Raster_Density': [values_sorted[f"{year}"].iloc[leds]]
                                                                                        }, geometry='geometry')], ignore_index=True)
                                leds_placed += 1
                                if leds_placed >= num_leds:
                                    break

                            surround += 1
                    
                    else: 
                        print(f"Warning: {country_name} requested {num_leds} LEDs, but only {leds_placed} were placed due to not having enough space.")
                        break

    # If manual manipulation is enabled, output the GeoJSON to the transients folder
    if manual_manipulation:
        all_leds_gdf.to_file(geojson_output_path, driver='GeoJSON')
        print(f"LED positions saved to {geojson_output_path} for manual manipulation.")
        return all_leds_gdf  # Return the GeoDataFrame for further processing if needed

    return all_leds_gdf
