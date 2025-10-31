"""

This script provides functionality for distributing and positioning LEDs on a geographic map
based on country-level energy consumption data. It consists of two main components:

1. determine_num_leds: Calculates the number of LEDs to allocate to each country based on
   their proportional energy consumption for a given year. Countries with higher energy
   consumption receive more LEDs proportionally.

2. allocate_leds: Places the allocated LEDs at specific geographic coordinates within each
   country's boundaries. LEDs are positioned according to raster density data, with options
   to overflow into surrounding ocean areas when a country's land area has insufficient
   cells. Supports manual position editing via GeoJSON export/import.


Function Specifications:

determine_num_leds(led_data, energy_timeseries, year, tot_leds)
    Inputs:
        - led_data: DataFrame with columns ['Entity', 'Year', 'primary_energy_consumption__twh']
        - energy_timeseries: GeoDataFrame with country names and geographic data
        - year: int, target year for energy consumption data
        - tot_leds: int, total number of LEDs to distribute across all countries

    Outputs:
        - DataFrame with columns: ['Entity', energy_year, 'energy_prop', 'num_leds', 'Round']
          where 'Round' contains the final integer LED count per country

allocate_leds(led_data, energy_timeseries, year, allocate_leds=True, place_ocean=True,
              use_edited_geojson=False, manual_manipulation=False,
              geojson_output_path="led_positions_for_manual_edit.geojson",
              prev_edited_geojson_path="prev_edited_led_positions.geojson")
    Inputs:
        - led_data: DataFrame from determine_num_leds() with LED counts per country
        - energy_timeseries: GeoDataFrame with columns ['country', 'point_index', year, 'geometry']
        - year: int, year column name to use for raster density values
        - allocate_leds: bool, whether to perform LED allocation (default: True)
        - place_ocean: bool, allow LED placement in ocean when land cells exhausted (default: True)
        - use_edited_geojson: bool, load previously edited positions instead of recalculating (default: False)
        - manual_manipulation: bool, export GeoJSON for manual editing (default: False)
        - geojson_output_path: str, path to save GeoJSON for manual editing
        - prev_edited_geojson_path: str, path to load previously edited GeoJSON

    Outputs:
        - GeoDataFrame with columns: ['geometry', 'Country', 'Raster_Density']
          containing Point geometries for each LED position

"""

import numpy as np
import pandas as pd
import geopandas as gpd
import os

def determine_num_leds(led_data, not_countries, year, tot_leds):
    led_data = led_data.pivot(index="Entity", columns="Year", values="primary_energy_consumption__twh").reset_index()
    led_data = led_data[~led_data["Entity"].isin(not_countries)]

    missing = max(led_data.isna().sum())
    idx = (np.abs(led_data.columns.values[1:-1] - year)).argmin() + 1
    energy_year = led_data.columns.values[idx]
    if energy_year > 1975:
        while missing > 10:
            missing = led_data.isna().sum().loc[energy_year]
            if missing > 10:
                energy_year -= 1

    led_data = led_data[['Entity', energy_year]]
    total_energy = led_data[energy_year].sum()
    led_data['energy_prop'] = led_data[energy_year] / total_energy
    led_data['num_leds'] = led_data['energy_prop'] * tot_leds

    def rounding(led_data):
        return np.round(led_data["num_leds"]).astype(int) if led_data["num_leds"] > 1 else np.floor(
            led_data["num_leds"]).astype(int)

    led_data["Round"] = led_data.apply(rounding, axis=1)

    return led_data


def allocate_leds(led_data, energy_timeseries, year, alias, allocate_leds=True, place_ocean=True, use_edited_geojson=False,
                  manual_manipulation=False, geojson_output_path="led_positions_for_manual_edit.geojson",
                  prev_edited_geojson_path="prev_edited_led_positions.geojson"):
    if not allocate_leds:
        print("LED allocation skipped as draw_leds is set to False.")
        return gpd.GeoDataFrame()  # Return an empty GeoDataFrame

    # If using a previously edited GeoJSON, load that file and skip LED allocation
    if use_edited_geojson and os.path.exists(prev_edited_geojson_path):
        print(f"Using the previously edited GeoJSON file from the data folder: {prev_edited_geojson_path}")
        return gpd.read_file(prev_edited_geojson_path)

    all_leds_gdf = gpd.GeoDataFrame()  # Stores all valid LED positions

    for index, row in led_data.iterrows():

        country_name = row['Entity']
        if country_name in alias.keys():
            country_name = alias[country_name]
        num_leds = int(row['Round'])
        leds_placed = 0

        if type(country_name) == str: values_array = energy_timeseries[energy_timeseries['country']== country_name]
        else: values_array = energy_timeseries[energy_timeseries['country'].isin(country_name)]
        values_array = values_array[["point_index", f"{year}", "geometry"]].sort_values(f"{year}", ascending=False)

        available_cells = len(values_array)
        missing_leds = num_leds - available_cells

        if available_cells == 0:
            print(f"Could not find {country_name} in raster data, skipping...")

        else:

            for leds in range(0, num_leds - leds_placed):  # Place LEDs on the land-space

                if leds_placed < available_cells:

                    all_leds_gdf = pd.concat(
                        [all_leds_gdf, gpd.GeoDataFrame({'geometry': [values_array["geometry"].iloc[leds]],
                                                         'Country': [country_name],
                                                         'Raster_Density': [values_array[f"{year}"].iloc[leds]]
                                                         }, geometry='geometry')], ignore_index=True)
                    leds_placed += 1

                else:

                    if place_ocean == True:

                        if leds_placed >= num_leds:
                            break

                        print(
                            f"Warning: {country_name} requested {num_leds} LEDs, but only {available_cells} cells are available. Attempting to place {missing_leds} LEDs in surrounding area.")
                        values_sorted = energy_timeseries.iloc[
                            energy_timeseries.geometry.x.argsort().values].reset_index(drop=True)
                        surround = 1

                        while leds_placed < num_leds:

                            surround_indices = ([x - (720 * surround) for x in values_array.point_index] +
                                                [x + (720 * surround) for x in values_array.point_index] +
                                                [x - surround for x in values_array.point_index] +
                                                [x + surround for x in values_array.point_index])
                            surround_indices = np.unique(list(filter(lambda x: x >= 0, surround_indices)))
                            values_filtered = energy_timeseries[
                                energy_timeseries["point_index"].isin(surround_indices)].query("country.isnull()")

                            for leds in range(len(values_filtered)):  # Place remaining LEDs on the land-space
                                all_leds_gdf = pd.concat([all_leds_gdf, gpd.GeoDataFrame(
                                    {'geometry': [values_filtered["geometry"].iloc[leds]],
                                     'Country': [country_name],
                                     'Raster_Density': [values_filtered[f"{year}"].iloc[leds]]
                                     }, geometry='geometry')], ignore_index=True)
                                leds_placed += 1
                                if leds_placed >= num_leds:
                                    break

                            surround += 1

                    else:
                        print(
                            f"Warning: {country_name} requested {num_leds} LEDs, but only {leds_placed} were placed due to not having enough space.")
                        break

    # If manual manipulation is enabled, output the GeoJSON to the transients folder
    if manual_manipulation:
        all_leds_gdf.to_file(geojson_output_path, driver='GeoJSON')
        print(f"LED positions saved to {geojson_output_path} for manual manipulation.")
        return all_leds_gdf  # Return the GeoDataFrame for further processing if needed

    return all_leds_gdf