# planets.py
# positions of solar system objects

import ephem
import math

objects = ["Sun", "Moon", "Mercury", "Venus", "Mars",
           "Jupiter", "Saturn", "Uranus", "Neptune"]

class Planets:
    
    def __init__ (self, logger, converter):
        self.logger = logger
        self.converter = converter
    
    # get object given solar system object name
    def get_obj (self, obj_str):
        try:
            return {
                "Sun"     : ephem.Sun(),
                "Moon"    : ephem.Moon(),
                "Mercury" : ephem.Mercury(),
                "Venus"   : ephem.Venus(),
                "Mars"    : ephem.Mars(),
                "Jupiter" : ephem.Jupiter(),
                "Saturn"  : ephem.Saturn(),
                "Uranus"  : ephem.Uranus(),
                "Neptune" : ephem.Neptune()
            }[obj_str]
        except:
            self.logger.error("Invalid object: " + obj_str)
    
    # equ_pos: compute the equatorial position of a given solar system object
    #
    #   obj: PyEphem object created from get_obj()
    #
    # -> ra, de: equatorial position of the object
    def equ_pos (self, obj):
        obj.compute(self.converter.get_obs())
        return math.degrees(obj.ra), math.degrees(obj.dec)
    
    # hor_pos: compute the horizontal position of a given solar system object
    #
    #   obj: PyEphem object created from get_obj()
    #
    # -> az, el: horizontal position of an object
    def hor_pos (self, obj):
        obj.compute(self.converter.get_obs())
        az, el = self.converter.radec_to_azel(obj.ra, obj.dec)
        return math.degrees(az), math.degrees(el)
