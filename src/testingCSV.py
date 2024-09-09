# this script takes the CSV file that the led_plotter script made and tests it out on the gores using blue rectangles instead of red
# this is just to see if the plot_leds_on_gores() function is working properly; it is not used in main.py

import csv
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from gore_drawer import plot_multiple_gores

# Paths to relevant files
csv_input_path = "led_coordinates_global.csv"
output_filename = "gore_with_csv_leds.svg"

# Parameters for the output
final_width = 4  # meters
final_height = 2  # meters
num_gores = 12  # number of gores to draw
led_width = 0.002  # meters (2mm)
led_height = 0.0035  # meters (3.5mm)

# Set up the figure
fig, ax = plt.subplots(figsize=(final_width * 39.3701, final_height * 39.3701))  # Convert meters to inches

# Draw the gores
fig, ax, gore_boundaries = plot_multiple_gores(num_gores=num_gores, fig=fig, ax=ax, draw_outlines=True, width=final_width, height=final_height)

# Read the CSV file and plot the LED markers in blue
with open(csv_input_path, mode='r') as csv_file:
    reader = csv.DictReader(csv_file)
    for row in reader:
        x = float(row['X (mm)']) / 1000  # Convert back from mm to meters
        y = float(row['Y (mm)']) / 1000  # Convert back from mm to meters

        # Plot the LED as a blue rectangle
        rect = Rectangle((x - led_width / 2, y - led_height / 2), led_width, led_height, color='blue', edgecolor='none')
        ax.add_patch(rect)

print(f"Plotted LED markers from {csv_input_path} in blue.")

# Save the final output with tight bounding box and no padding
fig.savefig(output_filename, format="svg", bbox_inches='tight', pad_inches=0, transparent=True)

# Show the plot
plt.show()
plt.close(fig)

print(f"Full map saved as {output_filename}")
