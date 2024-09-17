import rasterio
import numpy as np
import pandas as pd
import os

# Path to your nightlight raster
raster_path = r"C:\Users\19023\Downloads\Swingler\Python LED Placing\Nightlight\downsampled_nightlight_30arcmin_nearestN.tif"

# Parameters for progress monitoring
progress_interval = 10000000  # Print progress every 10 million values
total_elements_processed = 0

# Define number of bins
num_bins = 100

print("Starting data read")

# First, we need to calculate the global max value to set the range for the histogram
global_max_value = -np.inf

# Open the raster file to find the global maximum value
with rasterio.open(raster_path) as src:
    # Get the dimensions of the raster
    height, width = src.shape
    total_elements = height * width
    print(f"Total elements to process: {total_elements}")

    # Loop through the raster row by row to find the global maximum
    for i in range(height):
        # Read the i-th row (1D array)
        row_data = src.read(1, window=((i, i + 1), (0, width))).flatten()

        # Filter out nodata values
        valid_row_data = row_data[row_data != src.nodata]

        # Update the global maximum value
        if len(valid_row_data) > 0:
            row_max = valid_row_data.max()
            if row_max > global_max_value:
                global_max_value = row_max

print(f"Global maximum value found: {global_max_value}")

# Now we can define the histogram range based on the global maximum value
hist_range = (0, global_max_value)

# Initialize the histogram accumulator
hist = np.zeros(num_bins)
bin_edges = None

# Re-open the raster file to compute the histogram
with rasterio.open(raster_path) as src:
    for i in range(height):
        # Read the i-th row (1D array)
        row_data = src.read(1, window=((i, i + 1), (0, width))).flatten()

        # Filter out nodata values
        valid_row_data = row_data[row_data != src.nodata]

        # Update the histogram with the valid data
        row_hist, bin_edges = np.histogram(valid_row_data, bins=num_bins, range=hist_range)
        hist += row_hist

        # Update progress
        total_elements_processed += len(row_data)

        if total_elements_processed % progress_interval == 0:
            print(f"Processed {total_elements_processed} out of {total_elements} elements "
                  f"({(total_elements_processed / total_elements) * 100:.2f}%)")

print("Finished reading data")

# Save the histogram data to a CSV file
output_csv_path = os.path.join(r"C:\Users\19023\Downloads", "nightlight_histogram.csv")

# Create a DataFrame with the bin edges and frequencies
hist_data = pd.DataFrame({
    'Bin Start': bin_edges[:-1],  # Start of each bin
    'Bin End': bin_edges[1:],     # End of each bin
    'Frequency': hist             # Frequency in each bin
})

# Save to CSV
hist_data.to_csv(output_csv_path, index=False)

print(f"Histogram data saved to {output_csv_path}")
