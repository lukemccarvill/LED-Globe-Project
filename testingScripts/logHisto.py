# log histo

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

# Path to the histogram CSV file
csv_path = os.path.join(r"C:\Users\19023\Downloads", "nightlight_histogram.csv")

# Read the histogram data from CSV
hist_data = pd.read_csv(csv_path)

# Extract bin start and frequency data
bin_starts = hist_data['Bin Start']
frequencies = hist_data['Frequency']

# Ensure that frequencies are positive (logarithms of zero or negative values are undefined for the log plot)
log_frequencies = frequencies[frequencies > 0]

# Create a figure with two subplots: one for linear and one for log scale
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

# Linear scale histogram (left)
ax1.bar(bin_starts[:len(frequencies)], frequencies, width=(bin_starts[1] - bin_starts[0]), color='blue', edgecolor='black', alpha=0.7)
ax1.set_title('Nightlight Data Value Distribution (Linear Scale)')
ax1.set_xlabel('Pixel Value')
ax1.set_ylabel('Frequency')
ax1.grid(True)

# Logarithmic scale histogram (right)
ax2.bar(bin_starts[:len(log_frequencies)], log_frequencies, width=(bin_starts[1] - bin_starts[0]), color='blue', edgecolor='black', alpha=0.7)
ax2.set_yscale('log')  # Set the y-axis to logarithmic scale
ax2.set_title('Nightlight Data Value Distribution (Logarithmic Scale)')
ax2.set_xlabel('Pixel Value')
ax2.set_ylabel('Frequency (Log Scale)')
ax2.grid(True, which="both", ls="--")  # Grid lines for both major and minor ticks

# Adjust layout to prevent overlap
plt.tight_layout()

# Show the plots
plt.show()

print("Linear and logarithmic histograms plotted successfully.")
