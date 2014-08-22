# circle.py
# great circle math functions

import math

# distance: angular distance (degrees) between two points on a sphere
#
#   pt1 -> [crd_a, crd_b]: azimuth and elevation angles of first point
#   pt2 -> [crd_a, crd_b]: azimuth and elevation angles of second point
#
# -> theta: angular distance between pt1 and pt2
def distance (pt1, pt2):
    
    # <pt1, pt2> = ||pt1|| ||pt2|| cos(theta)
    # cos(theta) = <pt1, pt2> / (||pt1|| ||pt2||)
    #            = <pt1, pt2>             <-- letting pt1, pt2 be unit vectors
    #            = sin(pt1[1])*sin(pt2[1])+cos(pt1[1])*cos(pt2[1])*cos(pt2[0]-pt1[0])
    return math.degrees(math.acos(
        math.sin(math.radians(pt1[1])) * math.sin(math.radians(pt2[1])) +
        math.cos(math.radians(pt1[1])) * math.cos(math.radians(pt2[1]))
            * math.cos(math.radians(pt2[0] - pt1[0]))))


# bearing: direction to go from one point to another
#
#   pt1 -> [crd_a, crd_b]: point to start and get the bearing at
#   pt2 -> [crd_a, crd_b]: destination point
#
# -> angle: degrees east of north
def bearing (pt1, pt2):
    
    # convert inputs to radians
    pt1_a = math.radians(pt1[0])
    pt1_b = math.radians(pt1[1])
    pt2_a = math.radians(pt2[0])
    pt2_b = math.radians(pt2[1])
    
    return math.degrees(math.atan2(
        math.cos(pt2_b) * math.sin(pt2_a - pt1_a),
        math.cos(pt1_b) * math.sin(pt2_b) -
            math.sin(pt1_b) * math.cos(pt2_b) * math.cos(pt2_a - pt1_a)))


# waypoint: compute the position of a point on a great circle
#
#   pt1 -> [crd_a, crd_b]: point to start at
#   bearing_1: bearing of great circle at pt1
#   delta: angular distance to travel along great circle (degrees)
#
# -> pt2: the point delta along the great circle from pt1
def waypoint (pt1, bearing_1, delta):
    
    # convert inputs to radians
    pt1_b = math.radians(pt1[1])
    dist = math.radians(delta)
    b_rad = math.radians(bearing_1)

    return \
        (pt1[0] + math.degrees(math.atan2(
            math.sin(dist) * math.sin(b_rad),
            math.cos(pt1_b) * math.cos(dist) -
            math.sin(pt1_b) * math.sin(dist) * math.cos(b_rad)))) % 360, \
        \
        math.degrees(math.asin(
            math.sin(pt1_b) * math.cos(dist) +
            math.cos(pt1_b) * math.sin(dist) * math.cos(b_rad)))
