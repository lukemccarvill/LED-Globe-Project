import os
import csv
from matplotlib.patches import Rectangle
from raster_mapper import map_raster_to_gore

def plot_leds_on_gores(all_leds_gdf, ax, gore_boundaries, led_width=0.002, led_height=0.0035, scale_factor=1, plot_leds=True):
    # Define the path to the 'transients' folder in the repository
    project_root = os.path.dirname(os.path.dirname(__file__))  # Assuming script is run from 'src'
    transients_dir = os.path.join(project_root, 'transients')

    # Create the 'transients' folder if it doesn't exist
    if not os.path.exists(transients_dir):
        os.makedirs(transients_dir)

    # Path to save the CSV file
    csv_output_path = os.path.join(transients_dir, "led_coordinates_global.csv")

    if not plot_leds:
        return  # If LED plotting is disabled, exit early

    # Extract LED coordinates
    led_lon = all_leds_gdf.geometry.x
    led_lat = all_leds_gdf.geometry.y

    # Open the CSV file to write the pick-and-place data
    with open(csv_output_path, mode='w', newline='') as file:
        writer = csv.writer(file)

        # Create the header row without the blank column
        writer.writerow(["X (mm)", "Y (mm)", "Gore Section"])  

        # Map the LED data to the gores
        gore_x, gore_y = map_raster_to_gore(gore_boundaries, led_lon, led_lat)

        # Scale the dimensions of the rectangles
        rect_width = led_width * scale_factor  # Adjusted width in plot units
        rect_height = led_height * scale_factor  # Adjusted height in plot units

        # Plot the LED data as rectangles on the gores
        for lon, lat, x, y in zip(led_lon, led_lat, gore_x, gore_y):
            rect = Rectangle((x - rect_width / 2, y - rect_height / 2), rect_width, rect_height, facecolor='red', edgecolor='none')
            ax.add_patch(rect)

            # Determine the gore section and hemisphere
            gore_index = int((lon + 180) / 30) + 1  # Gore section number (1-12)
            hemisphere = "N" if lat >= 0 else "S"  # North or South
            section_label = f"{gore_index}{hemisphere}"

            # Write to CSV: X, Y, Gore Section
            writer.writerow([x * 1000, y * 1000, section_label])

    print(f"CSV saved at {csv_output_path}")
    print("LED rectangles plotted on the gores.")
