def interpolate_between_points(y, x_left, x_right, relative_lat):
    num_points = len(y)
    index_below = int(relative_lat * (num_points - 1))
    index_above = min(index_below + 1, num_points - 1)
    fraction = (relative_lat * (num_points - 1)) - index_below
    
    # Interpolating y position
    y_pos = y[index_below] + fraction * (y[index_above] - y[index_below])
    
    # Interpolating x positions
    x_left_pos = x_left[index_below] + fraction * (x_left[index_above] - x_left[index_below])
    x_right_pos = x_right[index_below] + fraction * (x_right[index_above] - x_right[index_below])
    
    return y_pos, x_left_pos, x_right_pos