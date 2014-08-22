# scans.py
# produce a list of coordinates for various scans

# note: crd_a = az, ra, lon, etc.
#       crd_b = el, de, lat, etc.

# serpentine: go from left to right, go up half a step, and go back left and repeat
#
#   pt1, pt2, pt3, pt4 -> [crd_a, crd_b]: corners forming the scan boundary
#   num_turns: number of back and forth turns to do -- 1 turn = 2 switchbacks
#
# -> list([crd_a, crd_b]): list of coordinates in proper order for the scan
def serpentine (pt1, pt2, pt3, pt4, num_turns):
    
    crd_list = [] # final list of coordinates
    
    for i in range(0, num_turns):
        
        # start on pt1 side and move toward pt2 side
        crd_list.append(
            [(1 - float(i)/num_turns)*pt1[0] + float(i)/num_turns*pt4[0],
             (1 - float(i)/num_turns)*pt1[1] + float(i)/num_turns*pt4[1]]
        )
        crd_list.append(
            [(1 - float(i)/num_turns)*pt2[0] + float(i)/num_turns*pt3[0],
             (1 - float(i)/num_turns)*pt2[1] + float(i)/num_turns*pt3[1]]
        )
        
        # move towards pt3 half a step and go the other direction
        crd_list.append(
            [(1 - (i + 0.5)/num_turns)*pt2[0] + (i + 0.5)/num_turns*pt3[0],
             (1 - (i + 0.5)/num_turns)*pt2[1] + (i + 0.5)/num_turns*pt3[1]]
        )
        crd_list.append(
            [(1 - (i + 0.5)/num_turns)*pt1[0] + (i + 0.5)/num_turns*pt4[0],
             (1 - (i + 0.5)/num_turns)*pt1[1] + (i + 0.5)/num_turns*pt4[1]]
        )
    
    # execute the final stretch of the scan
    crd_list.append([pt4[0], pt4[1]])
    crd_list.append([pt3[0], pt3[1]])
    
    return crd_list


# zigzag: go from left to right, then back to the left on the next step up
#
#   pt1, pt2, pt3, pt4 -> [crd_a, crd_b]: corners forming the scan boundary
#   num_turns: number of zigzags to do -- 1 turn = 2 switchbacks
#
# -> list([crd_a, crd_b]): list of coordinates in proper order for the scan
def zigzag (pt1, pt2, pt3, pt4, num_turns):
    
    crd_list = [] # final list of coordinates
    
    for i in range(0, num_turns + 1):
        
        # start on pt1 side and move toward pt2 side
        crd_list.append(
            [(1 - float(i)/num_turns)*pt1[0] + float(i)/num_turns*pt4[0],
             (1 - float(i)/num_turns)*pt1[1] + float(i)/num_turns*pt4[1]]
        )
        crd_list.append(
            [(1 - float(i)/num_turns)*pt2[0] + float(i)/num_turns*pt3[0],
             (1 - float(i)/num_turns)*pt2[1] + float(i)/num_turns*pt3[1]]
        )
    
    return crd_list

# list: scans implemented
# => list(functions)
scan_list = [serpentine, zigzag]
