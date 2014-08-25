import ephem
from time import gmtime, strftime, time

class Units:
    def __init__(self, config):
        """latitude and longitude need to be strings like 'd:m:s'"""
        self.c = config
        self.lon = self.c["LON"]
        self.lat = self.c["LAT"]
        
    def az_to_encoder(self, counts, ab=True):
        return self.__to_encoder("AzEncPerRev", counts, ab)
        
    def el_to_encoder(self, counts, ab=True):
        return self.__to_encoder("ElEncPerRev", counts, ab)

    def __to_encoder(self, flag, counts, ab):
        if "Az" in flag :
            offset = self.c["AzOffset"] 
        else: 
            offset = self.c["ElOffset"]
        return int(self.c[flag]/360.0*(counts + (offset if ab else 0)))
    
    def encoder_to_az(self, counts, ab=True):
        return self.__from_encoder("AzEncPerRev", counts, ab)

    def encoder_to_el(self, counts,ab=True):
        return self.__from_encoder("ElEncPerRev", counts, ab)

    def __from_encoder(self, flag, counts, ab):
        offset = self.az_to_encoder(self.c["AzOffset"], False) if "Az" in flag else None
        offset = self.el_to_encoder(self.c["ElOffset"], False) if offset is None else offset
        return self.__str_degrees(360.0/self.c[flag]*(counts - (offset if ab else 0)))

    def __str_degrees(self, val):
        d = int(val)
        m = int((val - d)/60.)
        s = ((val - d)/60. - m)/60.
        return "{}:{}:{:2.2f}".format(d, m, abs(s))

    def azel_to_radec(self, az, el):
        """az and el must be human readable string like 'h:m:s' or  floats
        in radians"""
        o = ephem.Observer()
        o.lat = self.lat
        o.lon = self.lon
        o.pressure = 0
        return  o.radec_of(az, el)

    def radec_to_azel(self, ra, dec, dt=0):
        telescope = ephem.Observer()
        telescope.lat = self.lat
        telescope.lon = self.lon
        d = "{t.tm_year}/{t.tm_mon}/{t.tm_mday} "
        h = "{t.tm_hour}:{t.tm_min}:{t.tm_sec}"
        telescope.date = (d+h).format(t = gmtime(time() + dt))

        star = ephem.FixedBody()
        star._ra = ephem.hours(ra)
        star._dec = ephem.degrees(dec)
        star.compute(telescope)
        return star.az, star.alt
        
    def set_offset(self, wanted_Az, wanted_El, current_Az, current_El):
        self.c["AzOffset"] = current_Az - wanted_Az
        self.c["ElOffset"] = current_El - wanted_El

    def lst(self):
        o = ephem.Observer()
        o.lat = self.lat
        o.lon = self.lon
        return o.sidereal_time()

    def lct(self):
        return strftime("%H:%M:%S")

    def utc(self):
        return "{t.tm_hour}:{t.tm_min}:{t.tm_sec}".format(t=gmtime())
    
    # get ephem.Observer object
    def get_obs (self):
        obs = ephem.Observer()
        obs.lat = self.lat
        obs.lon = self.lon
        d = "{t.tm_year}/{t.tm_mon}/{t.tm_mday} "
        h = "{t.tm_hour}:{t.tm_min}:{t.tm_sec}"
        obs.date = (d+h).format(t = gmtime(time() + dt))
        
        return obs

if __name__=="__main__":
    from config import Config
    config = Config("config.txt")
    un = Units(config)
    print "360 deg in encoder:", un.az_to_encoder(360)
    
