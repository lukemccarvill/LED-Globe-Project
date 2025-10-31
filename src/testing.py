# this script takes the CSV file that the led_plotter script made and tests it out on the gores using blue rectangles instead of red
# this is just to see if the plot_leds_on_gores() function is working properly; it is not used in main.py
# run this script as a standalone script, ensure it has access to gore_drawer and the path to the gorehalf_coordinates_with_sheets.xlsx file
# this is just to see if the create_gorehalf_coords() function is working properly; it is not used in main.py

import csv
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from gores import *

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

# Function to reverse the translation from per-gorehalf coordinates to globe coordinates
def reverse_translation(x, y, gore_half):
    # Each gore half should have a 333.33mm width and 1000mm height
    gore_width = 333.33
    gore_height = 1000

    # Determine which gore and hemisphere the coordinates belong to
    gore_number = int(gore_half[:-1])  # Gore number (1 to 12)
    hemisphere = gore_half[-1]  # 'N' for north, 'S' for south

    # Translate x back into globe coordinates
    x_globe = x + (gore_number - 1) * gore_width - 2000  # Translation to match globe coordinates

    # Translate y depending on the hemisphere
    if hemisphere == 'N':
        y_globe = y  # North hemisphere above the equator
    else:
        y_globe = y - 1000  # South hemisphere below the equator

    return x_globe / 1000, y_globe / 1000  # Convert back to meters


def plot_translated_leds(xlsx_file):
    # Load the coordinates from the xlsx file
    df = pd.read_excel(xlsx_file)

    # Setup the plot with gores using the existing gore_drawer function
    fig, ax = plt.subplots(figsize=(4 * 39.3701, 2 * 39.3701))  # 4000mm x 2000mm canvas in inches
    fig, ax, gore_boundaries = plot_multiple_gores(num_gores=12, fig=fig, ax=ax, draw_outlines=True, width=4, height=2)

    # Iterate over each row in the dataframe
    for index, row in df.iterrows():
        # Adjust column names to match your Excel file
        x, y, gore_half = row['Mid X (mm)'], row['Mid Y (mm)'], row['Gore Section']

        # Reverse translate the coordinates back to global coordinates
        x_globe, y_globe = reverse_translation(x, y, gore_half)

        # Plot the LEDs as green rectangles
        rect = Rectangle((x_globe - 0.002 / 2, y_globe - 0.0035 / 2), 0.002, 0.0035, color='green', edgecolor='none')
        ax.add_patch(rect)

    # Adjust the figure and save it
    plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
    ax.margins(0)
    ax.set_aspect('equal')
    ax.axis('off')  # Turn off axes

    # Save the final output
    plt.savefig("translated_leds_on_gores.svg", format="svg", bbox_inches='tight', pad_inches=0, transparent=True)
    plt.show()


if __name__ == "__main__":
    # Replace with the path to the xlsx file
    xlsx_file = r"C:\Users\19023\Downloads\Swingler\Python LED Placing\gorehalf_coordinates_with_sheets.xlsx"
    plot_translated_leds(xlsx_file)

