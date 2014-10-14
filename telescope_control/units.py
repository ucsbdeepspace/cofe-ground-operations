from datetime import datetime, timedelta
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
        enc = float(self.c.get("encoders", flag)) * counts/360.0

        # rounding
        if enc - int(enc) >= 0.5:
            enc = int(enc) + 1 # round up for positive numbers
        elif enc - int(enc) <= -0.5:
            enc = int(enc) - 1 # round down for negative numbers
        else: # no rounding
            enc = int(enc)

        return enc

    def encoder_to_az(self, counts, raw=False):
        return self.__from_encoder("az", counts, raw)

    def encoder_to_el(self, counts):
        return self.__from_encoder("el", counts)

    def __from_encoder(self, flag, counts, raw=False):
        dec_deg = 360.0/float(self.c.get("encoders", flag)) * counts
        if flag == "az" and not raw:
            dec_deg = dec_deg % 360
        return self.__str_degrees(dec_deg)

    def __str_degrees(self, val):
        val_abs = abs(val)
        d = int(val_abs)
        m = int((val_abs - d)*60)
        s = ((val_abs - d) - m/60.0)*3600.0
        return (val < 0 and "-" or "") + "{}:{:02d}:{:02.1f}".format(d, m, s)

    def azel_to_radec(self, az, el, dt=0):
        return self.get_obs(dt).radec_of(az, el)

    def radec_to_azel(self, ra, dec, dt=0):
        obj = ephem.FixedBody()
        obj._ra = ephem.hours(ra)
        obj._dec = ephem.degrees(dec)
        obj.compute(self.get_obs(dt))
        return obj.az, obj.alt

    def lst (self):
        o = ephem.Observer()
        o.lat = math.radians(float(self.c.get("location", "lat")))
        o.lon = math.radians(float(self.c.get("location", "lon")))
        return o.sidereal_time()

    def lct (self, dt=0.0):
        tm_now = datetime.now()
        tm_del = timedelta(seconds=dt)
        return (tm_now + tm_del).strftime("%H:%M:%S.%f")[:-4]

    def utc (self, dt=0.0):
        tm_now = datetime.utcnow()
        tm_del = timedelta(seconds=dt)
        return (tm_now + tm_del).strftime('%H:%M:%S.%f')[:-4]

    # get ephem.Observer object
    def get_obs (self, dt=0):
        obs = ephem.Observer()
        obs.lat = self.c.get("location", "lat")
        obs.lon = self.c.get("location", "lon")
        obs.date = str(datetime.utcnow())
        obs.pressure = 0

        return obs
