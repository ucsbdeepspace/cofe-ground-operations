# circle.py
# great circle math functions

import math

# distance: angular distance (degrees) between two points on a sphere
#
#   pt1_a, pt1_b: azimuth and elevation angles of first point
#   pt2_a, pt2_b: azimuth and elevation angles of second point
#
# -> theta: angular distance between pt1 and pt2
def distance (pt1_a, pt1_b, pt2_a, pt2_b):
    
    # <pt1, pt2> = ||pt1|| ||pt2|| cos(theta)
    # cos(theta) = <pt1, pt2> / (||pt1|| ||pt2||)
    #            = <pt1, pt2>             <-- letting pt1, pt2 be unit vectors
    #            = sin(pt1_b)*sin(pt2_b)+cos(pt1_b)*cos(pt2_b)*cos(pt2_a-pt1_a)
    return math.degrees(math.acos(
        math.sin(math.radians(pt1_b)) * math.sin(math.radians(pt2_b)) +
        math.cos(math.radians(pt1_b)) * math.cos(math.radians(pt2_b))
            * math.cos(math.radians(pt2_a - pt1_a))))


# bearing: direction to go from one point to another
#
#   pt1_a, pt1_b: point to start and get the bearing at
#   pt2_a, pt2_b: destination point
#
# -> angle: degrees east of north
def bearing (pt1_a, pt1_b, pt2_a, pt2_b):
    return math.degrees(math.atan2(math.sin(math.radians(pt2_a - pt1_a)),
        math.cos(math.radians(pt1_b)) * math.sin(math.radians(pt2_b)) -
        math.sin(math.radians(pt1_b)) * math.cos(math.radians(pt2_a - pt1_a))))


# waypoint: compute the position of a point on a great circle
#
#   pt1_a, pt1_b: point to start at
#   bearing_1: bearing of great circle at (pt1_a, pt1_b)
#   delta: angular distance to travel along great circle (degrees)
#
# -> pt2_a, pt2_b: the point delta along the great circle from (pt1_a, pt1_b)
def waypoint (pt1_a, pt1_b, bearing_0, delta):
    
    # bearing at the ascending node (radians)
    bearing_an = math.asin(
        math.sin(math.radians(bearing_1)) * math.cos(math.radians(pt1_b)))
    
    # angular distance of (pt1_a, pt1_b) from the ascending node (radians)
    dist_an = math.atan2(math.tan(math.radians(pt1_b)),
                         math.cos(math.radians(bearing_1)))
    
    # longitude of the ascending node (degrees)
    lon_an = pt1_a - math.degrees(math.atan2(
        math.sin(bearing_an) * math.sin(dist_an),
        math.cos(dist_an)))
    
    # compute point from Napier's rules
    return \
        lon_an + math.degrees(math.atan2(
            math.sin(bearing_an) * math.sin(math.radians(delta)),
            math.cos(math.radians(delta)))), \
        \
        math.degrees(math.asin(math.cos(bearing_an) *
            math.sin(math.radians(delta))))
