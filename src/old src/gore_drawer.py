import numpy as np
import matplotlib.pyplot as plt

def plot_multiple_gores(num_gores=12, fig=None, ax=None, draw_outlines=True, draw_equator=False, width=4, height=2):
    # Set exact canvas size 4000mm x 2000mm
    if fig is None or ax is None:
        fig, ax = plt.subplots(figsize=(width * 39.3701, height * 39.3701))  # 4000mm x 2000mm canvas in inches

    equator_width = width / num_gores  # Width of each gore at the equator
    gore_boundaries = []

    for i in range(num_gores):
        # Calculate center and y-range for each gore
        center_x = (i * equator_width) - (width / 2) + (equator_width / 2)
        y = np.linspace(-height / 2, height / 2, 500)  # Full height (2000mm)

        # Calculate x-values for left and right edges of the gore
        x_left = center_x - (equator_width / 2) * (1 - (np.abs(y) / (height / 2))**2)
        x_right = center_x + (equator_width / 2) * (1 - (np.abs(y) / (height / 2))**2)

        # Plot the gore outlines and fill them
        if draw_outlines:
            ax.plot(x_left, y, 'k-', lw=0.5)
            ax.plot(x_right, y, 'k-', lw=0.5)
            ax.fill_betweenx(y, x_left, x_right, color='lightgray', alpha=0.5)

        gore_boundaries.append((x_left, x_right, y))

    # Draw the equator line if specified
    if draw_equator:
        ax.plot([-width / 2, width / 2], [0, 0], 'k-', lw=0.5)  # Equator at y=0

    # Set axis limits exactly to the canvas size (4000mm x 2000mm)
    ax.set_xlim(-width / 2, width / 2)
    ax.set_ylim(-height / 2, height / 2)

    # Ensure strict aspect ratio with no additional scaling
    ax.set_aspect('equal')

    # Remove any padding, margins, or extra space
    plt.subplots_adjust(left=0, right=1, top=1, bottom=0)  # THIS LINE OF CODE SAVED THE SPACING/SHRINKING ISSUE
    ax.margins(0)  # Set margins to zero
    ax.axis('off')  # Turn off axes

    return fig, ax, gore_boundaries
