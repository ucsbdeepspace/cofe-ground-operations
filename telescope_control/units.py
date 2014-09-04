import ephem
from time import gmtime, strftime, time

class Units:
    def __init__(self, config):
        """latitude and longitude need to be strings like 'd:m:s'"""
        self.c = config
        self.lon = self.c.get("location", "lon")
        self.lat = self.c.get("location", "LAT")
        
    def az_to_encoder(self, counts, ab=True):
        return self.__to_encoder("az", counts, ab)
        
    def el_to_encoder(self, counts, ab=True):
        return self.__to_encoder("el", counts, ab)

    def __to_encoder(self, flag, counts, ab):
        if flag == "az":
            offset = float(self.c.get("skypos", "az"))
        else: 
            offset = float(self.c.get("skypos", "el"))
        return int(float(self.c.get("encoders", flag))/360.0*(counts + (offset if ab else 0)))
    
    def encoder_to_az(self, counts, ab=True):
        return self.__from_encoder("az", counts, ab)

    def encoder_to_el(self, counts,ab=True):
        return self.__from_encoder("el", counts, ab)

    def __from_encoder(self, flag, counts, ab):
        offset = self.az_to_encoder(float(self.c.get("skypos", "az")), False) if flag == "az" else None
        offset = self.el_to_encoder(float(self.c.get("skypos", "el")), False) if offset is None else offset
        return self.__str_degrees(360.0/float(self.c.get("encoders", flag))*(counts - (offset if ab else 0)))

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
        self.c["skypos"]["az"] = current_Az - wanted_Az
        self.c["skypos"]["el"] = current_El - wanted_El

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
        obs.date = (d+h).format(t = gmtime(time()))
        
        return obs

if __name__=="__main__":
    from config import Config
    config = Config("config.txt")
    un = Units(config)
    print "360 deg in encoder:", un.az_to_encoder(360)
    
