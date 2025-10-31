import requests
import json
import pandas as pd
import os
import geopandas as gpd
from shapely.geometry import shape

"""

   Files to import:                       Source:                       Saves to file:

1. global energy consumption              ourworldindata.org            global_energy_consumption
2. per capita energy consumption          ourworldindata.org            per_capita_energy_consumption
3. world administrative boundaries        opendatasoft.com (WFP, UN)    countries                  
4. 

"""

# Create the directory structure if it doesn't exist
# Use '../data/API' to go up from src to parent, then into data/API
os.makedirs('../data/API', exist_ok=True)
print("Directory '../data/API' created or already exists")

## --------------------------------------------- GLOBAL ENERGY CONSUMPTION ---------------------------------------------
# region

# Fetch the data
df = pd.read_csv(
    "https://ourworldindata.org/grapher/primary-energy-cons.csv?v=1&csvType=full&useColumnShortNames=true",
    storage_options={'User-Agent': 'Our World In Data data fetch/1.0'}
)

print("Data columns:", df.columns.tolist())
print(f"Data shape: {df.shape}")

# Save the DataFrame to CSV
df.to_csv('../data/API/global_energy_consumption.csv', index=False)
print("Data saved to: ../data/API/global_energy_consumption.csv")

# Fetch the metadata
metadata = requests.get(
    "https://ourworldindata.org/grapher/primary-energy-cons.metadata.json?v=1&csvType=full&useColumnShortNames=true"
).json()

# Save the metadata to JSON
with open('../data/API/global_energy_consumption_metadata.json', 'w') as f:
    json.dump(metadata, f, indent=2)
print("Metadata saved to: ../data/API/global_energy_consumption_metadata.json\n")

# endregion

## ------------------------------------------- PER CAPITA ENERGY CONSUMPTION -------------------------------------------
# region

# Fetch the data
df = pd.read_csv(
    "https://ourworldindata.org/grapher/per-capita-energy-use.csv?v=1&csvType=full&useColumnShortNames=true",
    storage_options={'User-Agent': 'Our World In Data data fetch/1.0'}
)

print("Data columns:", df.columns.tolist())
print(f"Data shape: {df.shape}")

# Save the DataFrame to CSV
df.to_csv('../data/API/per_capita_energy_consumption.csv', index=False)
print("Data saved to: ../data/API/per_capita_energy_consumption.csv")

# Fetch the metadata
metadata = requests.get(
    "https://ourworldindata.org/grapher/per-capita-energy-use.metadata.json?v=1&csvType=full&useColumnShortNames=true"
).json()

# Save the metadata to JSON
with open('../data/API/per_capita_energy_consumption_metadata.json', 'w') as f:
    json.dump(metadata, f, indent=2)
print("Metadata saved to: ../data/API/per_capita_energy_consumption_metadata.json")

# endregion

## ------------------------------------------ WORLD ADMINISTRATIVE BOUNDARIES ------------------------------------------
# region

response = requests.get(
    "https://public.opendatasoft.com/api/explore/v2.1/catalog/datasets/world-administrative-boundaries-countries/records"
)

data = response.json()
records = data['results']

# Extract geometry and properties from the API response
features = []
for record in records:
    # The geometry is in record['geo_shape'] for Opendatasoft APIs
    if 'geo_shape' in record:
        features.append({
            'geometry': shape(record['geo_shape']),
            **record  # Include all other fields
        })

# Convert to GeoDataFrame
gdf = gpd.GeoDataFrame(features, crs='EPSG:4326')

# Save as GeoPackage
gdf.to_file('../data/API/countries.gpkg', driver='GPKG')
print("\nCountries data saved to: ../data/API/countries.gpkg")

# endregion