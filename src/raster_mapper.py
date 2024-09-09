from interpolator import interpolate_between_points

def map_raster_to_gore(gore_boundaries, lon, lat):
    gore_x, gore_y = [], []
    for lon_point, lat_point in zip(lon, lat):
        gore_index = int((lon_point + 180) / 30)
        if gore_index >= len(gore_boundaries):
            continue
        
        x_left, x_right, y = gore_boundaries[gore_index]
        relative_lon = ((lon_point + 180) % 30) / 30
        relative_lat = (lat_point + 90) / 180

        y_pos, x_left_pos, x_right_pos = interpolate_between_points(y, x_left, x_right, relative_lat)
        x_pos = x_left_pos + relative_lon * (x_right_pos - x_left_pos)

        gore_x.append(x_pos)
        gore_y.append(y_pos)

    return gore_x, gore_y