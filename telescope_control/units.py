import ephem
import math
from time import gmtime, strftime, time

class Units:
    def __init__(self, config):
        """latitude and longitude need to be strings like 'd:m:s'"""
        self.c = config
        
    def az_to_encoder(self, counts):
        return self.__to_encoder("az", counts)
        
    def el_to_encoder(self, counts):
        return self.__to_encoder("el", counts)

    def __to_encoder(self, flag, counts):
        return int(float(self.c.get("encoders", flag))/360.0 * counts)
    
    def encoder_to_az(self, counts):
        return self.__from_encoder("az", counts)

    def encoder_to_el(self, counts):
        return self.__from_encoder("el", counts)

    def __from_encoder(self, flag, counts):
        return self.__str_degrees(360.0/float(self.c.get("encoders", flag)) * counts)

    def __str_degrees(self, val):
        d = int(val)
        m = int((val - d)*60.0)
        s = ((val - d)*60.0 - m)*60.0
        return "{}:{}:{:2.1f}".format(d, m, abs(s))

    def azel_to_radec(self, az, el, dt=0):
        o = self.get_obs(dt)
        
        return  o.radec_of(az, el)

    def radec_to_azel(self, ra, dec, dt=0):
        telescope = self.get_obs(dt)

        star = ephem.FixedBody()
        star._ra = ephem.hours(ra)
        star._dec = ephem.degrees(dec)
        star.compute(telescope)
        return star.az, star.alt
        
    def set_offset(self, wanted_Az, wanted_El, current_Az, current_El):
        self.c["skypos"]["az"] = current_Az - wanted_Az
        self.c["skypos"]["el"] = current_El - wanted_El

    def lst(self):
        o = ephem.Observer()
        o.lat = math.radians(float(self.c.get("location", "lat")))
        o.lon = math.radians(float(self.c.get("location", "lon")))
        return o.sidereal_time()

    def lct(self):
        return strftime("%H:%M:%S")

    def utc(self):
        return "{t.tm_hour}:{t.tm_min}:{t.tm_sec}".format(t=gmtime())
    
    # get ephem.Observer object
    def get_obs (self, dt=0):
        obs = ephem.Observer()
        obs.lat = math.radians(float(self.c.get("location", "lat")))
        obs.lon = math.radians(float(self.c.get("location", "lon")))
        d = "{t.tm_year}/{t.tm_mon}/{t.tm_mday} "
        h = "{t.tm_hour}:{t.tm_min}:{t.tm_sec}"
        obs.date = (d+h).format(t = gmtime(time() + dt))
        obs.pressure = 0
        
        return obs
    
