import os
import numpy as np
import pandas as pd
import geopandas as gpd

def determine_num_leds(led_data, energy_timeseries, year, tot_leds):
    countries = set(energy_timeseries["country"])
    # pivot so each year is a column; keep only countries present in the raster timeseries
    led_data = led_data.pivot(index="Entity", columns="Year", values="primary_energy_consumption__twh").reset_index()
    led_data = led_data[led_data["Entity"].isin(countries)]

    # Collect available year columns (as ints) from the pivoted DataFrame and map to actual column labels
    available_years = []
    col_map = {}
    for c in led_data.columns:
        if c == 'Entity':
            continue
        try:
            y = int(c)
            available_years.append(y)
            col_map[y] = c
        except Exception:
            # skip non-year columns
            continue
    if not available_years:
        raise ValueError("No year columns found in energy data after pivot.")

    available_years = sorted(available_years)
    # pick the closest available year to the requested year
    energy_year = min(available_years, key=lambda y: abs(y - year))

    # Use the actual column label (string or int) from the pivot table
    col_label = col_map.get(energy_year, energy_year)
    led_data = led_data[['Entity', col_label]]
    led_data[energy_year] = led_data[energy_year].replace(np.nan, 0)
    total_energy = led_data[energy_year].sum()
    led_data['energy_prop'] = led_data[energy_year] / total_energy
    led_data['num_leds'] = led_data['energy_prop'] * tot_leds

    def rounding(row):
        val = row["num_leds"]
        if pd.isna(val):
            return 0
        return int(np.round(val)) if val > 1 else int(np.floor(val))

    led_data["Round"] = led_data.apply(rounding, axis=1)
    
    return led_data

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
        num_leds = row['Round']
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

                            surround_indices = ([x - (720*surround) for x in values_array.point_index] + 
                                                [x + (720*surround) for x in values_array.point_index] +
                                                [x - surround for x in values_array.point_index] + 
                                                [x + surround for x in values_array.point_index]) 
                            surround_indices = np.unique(list(filter(lambda x: x >= 0, surround_indices)))
                            values_filtered = energy_timeseries[energy_timeseries["point_index"].isin(surround_indices)].query("country.isnull()")

                            for leds in range(len(values_filtered)): # Place remaining LEDs on the land-space
                                all_leds_gdf = pd.concat([all_leds_gdf, gpd.GeoDataFrame({'geometry': [values_filtered["geometry"].iloc[leds]],
                                                                                        'Country': [country_name],
                                                                                        'Raster_Density': [values_filtered[f"{year}"].iloc[leds]]
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
