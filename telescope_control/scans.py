# scans.py
# produce a list of coordinates for various scans

# note: crd_a = az, ra, lon, etc.
#       crd_b = el, de, lat, etc.

import math

# rectangular: slew over a roughly square region of sky one axis at a time
#
#   center -> [az, el]: object at center of scan
#   size: side length of scan box (degrees)
#   num_turns: number of back and forth turns to do -- 1 turn = 2 switchbacks
#
# -> list([az, el]): list of coordinates in proper order for the scan
def rectangular (center, size, num_turns):
    
    # altitude bounds
    low_el = center[1] - 0.5 * size
    if low_el > 89.9:
        low_el = 89.9
    
    high_el = center[1] + 0.5 * size
    if high_el > 90.0:
        high_el = 90.0
    
    # azimuth bounds
    left_az_low = center[0] - 0.5 * size \
        / max(0.01, math.cos(math.radians(low_el)))
    right_az_low = center[0] + 0.5 * size \
        / max(0.01, math.cos(math.radians(low_el)))
    
    left_az_high = center[0] - 0.5 * size \
        / max(0.01, math.cos(math.radians(high_el)))
    right_az_high = center[0] + 0.5 * size \
        / max(0.01, math.cos(math.radians(high_el)))
    
    # generate list of points
    crd_list = []
    for i in range(0, num_turns):
        
        # upper level
        alt_up = float(i)/num_turns * low_el + (1-float(i)/num_turns) * high_el
        
        # start on left
        crd_list.append(
            [float(i)/num_turns*left_az_low + (1-float(i)/num_turns)*left_az_high,
             alt_up]
        )
        
        # move to the right
        crd_list.append(
            [float(i)/num_turns*right_az_low + (1-float(i)/num_turns)*right_az_high,
             alt_up]
        )
        
        # lower level
        alt_low = (i+0.5)/num_turns * low_el + (1-(i+0.5)/num_turns) * high_el
        
        # move down vertically to lower level
        crd_list.append(
            [float(i)/num_turns*right_az_low + (1-float(i)/num_turns)*right_az_high,
             alt_low]
        )
        
        # move left to next azimuth
        crd_list.append(
            [(i+1.0)/num_turns*left_az_low + (1-(i+1.0)/num_turns)*left_az_high,
             alt_low]
        )
    
    # final stretch
    
    # start on left
    crd_list.append([left_az_low, low_el])
    
    # move to the right
    crd_list.append([right_az_low, low_el])
    
    return crd_list

# linear: slew in azimuth across an object
#
#   center -> [az, el]: object at center of scan
#   size: total length of scan line (degrees)
#   num_turns: (ignored)
#
# -> list([az, el]): list of coordinates in proper order for the scan
def linear (center, size, num_turns = None):
    
    # find true length accounting for altitude
    true_length = size / max(0.01, math.cos(math.radians(center[1])))
    
    # start on left and move to the right
    return [
        [center[0] - 0.5 * true_length, center[1]],
        [center[0] + 0.5 * true_length, center[1]]
    ]

# list: scans implemented
# => list(functions)
scan_list = [rectangular, linear]
