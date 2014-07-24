# scans.py
# produce a list of coordinates for various scans

# note: crd_a = az, ra, lon, etc.
#       crd_b = el, de, lat, etc.

# serpentine: go from left to right, go up half a step, and go back left and repeat
#
#   crd1a, crd1b: starting point
#   crd2a, crd2b: end point
#   num_turns: number of back and forth turns to do -- 1 turn = 2 switchbacks
#
# -> list([crd_a, crd_b]): list of coordinates in proper order for the scan
def serpentine (crd1a, crd1b, crd2a, crd2b, num_turns):
    
    crd_list = [] # final list of coordinates
    
    b_list = [] # list of b-coordinates
    b_step = float(crd2b - crd1b) / num_turns # spacing between two steps
    
    # fill in list of b coordinates
    for i in range(0, num_turns + 1):
        b_list.append(crd1b + i * b_step)
    
    # fill in actual list of coordinates
    for b in b_list:
        # left to right
        crd_list.append([crd1a, b])
        crd_list.append([crd2a, b])
        # go back from the right to the left
        crd_list.append([crd2a, b + 0.5 * b_step])
        crd_list.append([crd1a, b + 0.5 * b_step])
    
    return crd_list


# zigzag: go from left to right, then back to the left on the next step up
#
#   crd1a, crd1b: starting point
#   crd2a, crd2b: end point
#   num_turns: number of zigzags to do -- 1 turn = 2 switchbacks
#
# -> list([crd_a, crd_b]): list of coordinates in proper order for the scan
def zigzag (crd1a, crd1b, crd2a, crd2b, num_turns):
    
    crd_list = [] # final list of coordinates
    
    b_list = [] # list of b-coordinates
    b_step = float(crd2b - crd1b) / num_turns # spacing between two zigzags
    
    # fill in list of b coordinates
    for i in range(0, num_turns + 1):
        b_list.append(crd1b + i * b_step)
    
    # fill in actual list of coordinates
    for b in b_list:
        # zigzag back and forth between left and right side
        crd_list.append([crd1a, b])
        crd_list.append([crd2a, b])
    
    return crd_list
