# controller.py
# layer of abstraction for moving motors

import circle
import ephem
import math
import string
import time
import threading

class Controller:

    def __init__ (self, logger, galil, converter, config):
        self.logger = logger
        self.galil = galil
        self.converter = converter
        self.config = config

        self.scan_queue = 0 # number of scans left to do


    # current_pos: retrieve current motor positions
    # -> azimuth, altitude
    def current_pos (self):
        pos_enc = list(self.galil.pos)

        azimuth = ephem.degrees(self.converter.encoder_to_az(
            pos_enc[string.uppercase.index(self.galil.axis_az)]))
        altitude = ephem.degrees(self.converter.encoder_to_el(
            pos_enc[string.uppercase.index(self.galil.axis_el)]))

        return math.degrees(azimuth), math.degrees(altitude)


    # scan: generic scan function
    #
    #   crd_func -> function -> list([az, el]): returns list of coordinates
    #   process_func: function to process list of points
    #     (optionally, use "process_hor" and "process_equ" below)
    #   repeat: number of times to repeat (use "True" for indefinite repetition)
    def scan (self, crd_func, repeat = 1):

        # unset any previously set stop events
        self.stop = threading.Event()

        # repeat indefinitely
        if str(repeat) == str(True):
            self.scan_queue = 1
        else: # repeat for <repeat> times
            self.scan_queue = repeat

        # function to return list of reversed coordinates
        def crd_reverse ():
            crd_list = crd_func()
            crd_list.reverse()
            return crd_list

        # queue and process scan
        while self.scan_queue > 0 and not self.stop.is_set():

            # process forward scan and wait until scan is complete
            self.process_hor(crd_func)

            # quit if we only need to process one direction
            if self.scan_queue <= 0.5 or self.stop.is_set():
                break

            # reverse direction and repeat
            self.process_hor(crd_reverse)

            # check whether to continue
            if str(repeat) != str(True):
                self.scan_queue -= 1

        self.logger.info("scan complete")


    # process_hor: process a list of horizontal coordinates to slew to
    #   crd_func -> function -> list([az, el]): returns list of coordinates
    def process_hor (self, crd_func):

        # initialize loop
        i = 0
        prev_pt = self.current_pos()
        crd_list = crd_func()

        # loop through all segments
        while len(crd_list) > i and not self.stop.is_set():
            self.galil.sendOnly("AM")
            time.sleep(self.slew(crd_list[i], begin=prev_pt))
            self.stall(crd_list[i])

            prev_pt = crd_list[i]
            crd_list = crd_func()
            i = i + 1


    # slew: basic, linear motion on both axes from one point to another
    #
    #   hor_pos -> [az, el]: position to slew to
    #   begin -> [az, el]: where to start slewing from
    #
    # -> time needed for slew (seconds)
    def slew (self, hor_pos, begin=None, simulate=False):

        begin = begin or self.current_pos()

        # find speed of each axis
        alt_av = math.radians(0.5 * (hor_pos[1] + begin[1]))
        d_az = hor_pos[0] - begin[0]
        d_el = hor_pos[1] - begin[1]
        delta = math.sqrt((d_az * math.cos(alt_av))**2 + d_el**2) or 0.01

        speed = float(self.config.get("slew", "speed"))
        speed_az = self.converter.az_to_encoder(abs(d_az) / delta * speed
            / max(0.01, math.cos(alt_av)))
        speed_el = self.converter.el_to_encoder(abs(d_el) / delta * speed)

        # find acceleration of each axis
        accel = float(self.config.get("slew", "accel"))
        accel_az = self.converter.az_to_encoder(abs(d_az) / delta * accel
            / max(0.01, math.cos(alt_av)))
        accel_el = self.converter.el_to_encoder(abs(d_el) / delta * accel)

        ##
        # compute time needed to perform slew
        ##

        # time needed to accelerate in each axis
        tm_az_ac = accel_az and float(speed_az) / accel_az or 0.0
        tm_el_ac = accel_el and float(speed_el) / accel_el or 0.0

        # distance travelled while accelerating and decelerating in each axis
        d_az_ac = accel_az * tm_az_ac**2
        d_el_ac = accel_el * tm_el_ac**2

        # distance travelled at top speed
        d_az_constv = abs(self.converter.az_to_encoder(d_az)) - abs(d_az_ac)
        d_el_constv = abs(self.converter.el_to_encoder(d_el)) - abs(d_el_ac)

        # time spent at top speed
        tm_az_constv = speed_az and float(d_az_constv) / speed_az or 0.0
        tm_el_constv = speed_el and float(d_el_constv) / speed_el or 0.0

        # total time spent
        tm_az = tm_az_ac + tm_az_constv
        tm_el = tm_el_ac + tm_el_constv
        tm_tot = max(tm_az, tm_el)

        ##
        # send instructions to motor
        ##

        if not simulate:

            # set speed and acceleration of axes
            if speed_az:
                self.galil.sendOnly("SP" + self.galil.axis_az + "=" + str(speed_az))
                self.galil.sendOnly("AC" + self.galil.axis_az + "=" + str(accel_az))
                self.galil.sendOnly("DC" + self.galil.axis_az + "=" + str(accel_az))
            if speed_el:
                self.galil.sendOnly("SP" + self.galil.axis_el + "=" + str(speed_el))
                self.galil.sendOnly("AC" + self.galil.axis_el + "=" + str(accel_el))
                self.galil.sendOnly("DC" + self.galil.axis_el + "=" + str(accel_el))

            # move to position
            if speed_az:
                self.galil.sendOnly("PA" + self.galil.axis_az + "=" +
                    str(self.converter.az_to_encoder(begin[0] + d_az)))
            if speed_el:
                self.galil.sendOnly("PA" + self.galil.axis_el + "=" +
                    str(self.converter.el_to_encoder(begin[1] + d_el)))
            self.logger.info(self.galil.sendAndReceive("BG"))

        return tm_tot


    # track: follow an equatorial position indefinitely
    #
    #   equ_pos -> [ra, de]: position to track
    #
    # -> (returns once tracking ends)
    def track (self, equ_pos):

        # unset any previously set stop events
        self.stop = threading.Event()

        # move to initial position quickly
        azi, alt = self.converter.radec_to_azel(
            math.radians(equ_pos[0]), math.radians(equ_pos[1]))
        hor_pos = [math.degrees(azi), math.degrees(alt)]

        self.slew(hor_pos)
        self.galil.sendOnly("AM") # stall until motion is complete

        # enable tracking mode
        self.galil.sendOnly("PT 1,1,1,1")

        # slew to equatorial coordinate and loop until self.stop is set
        while not self.stop.is_set():

            # compute new position
            old_pos = hor_pos
            azi, alt = self.converter.radec_to_azel(
                math.radians(equ_pos[0]), math.radians(equ_pos[1]))
            hor_pos = [math.degrees(azi), math.degrees(alt)]

            # compute motor velocities
            speed = circle.distance(old_pos, hor_pos) / 0.5 # per 0.5 seconds
            bearing = circle.bearing(old_pos, hor_pos)
            speed_az = math.fabs(speed * math.cos(math.radians(bearing))) \
                / (math.cos(math.radians(hor_pos[1])) + 0.01)
            speed_el = math.fabs(speed * math.sin(math.radians(bearing)))

            # adjust motor speed
            self.galil.sendOnly("SP" + self.galil.axis_az + "=" +
                str(10 * max(1, self.converter.az_to_encoder(speed_az))))
            self.galil.sendOnly("SP" + self.galil.axis_el + "=" +
                str(10 * max(1, self.converter.el_to_encoder(speed_el))))

            # move to new position
            self.galil.sendOnly("PA" + self.galil.axis_az + "=" +
                str(self.converter.az_to_encoder(hor_pos[0])))
            self.galil.sendOnly("PA" + self.galil.axis_el + "=" +
                str(self.converter.el_to_encoder(hor_pos[1])))

            time.sleep(0.5) # wait 0.5 seconds to update again

        # exit tracking mode
        self.galil.sendOnly("ST")


    # sync: set current position of motors
    #   hor_pos -> [az, el]: position to set motor position to
    def sync (self, hor_pos):

        # define current position as the given position
        self.galil.sendOnly("DP" + self.galil.axis_az + "=" +
            str(self.converter.az_to_encoder(hor_pos[0])))
        self.galil.sendOnly("DP" + self.galil.axis_el + "=" +
            str(self.converter.el_to_encoder(hor_pos[1])))


    # stall: pause execution until we are within some distance of a target
    #   dest_pos -> [az, el]: target position
    #   pre_time: return when we've reached a distance < speed/pre_time
    def stall (self, dest_pos, pre_time=0.1):

        while not (hasattr(self, "stop") and self.stop.is_set()):

            # current position
            cur_pos = self.current_pos()
            alt_av = math.radians(0.5 * (cur_pos[1] + dest_pos[1]))
            d_az = (dest_pos[0] - cur_pos[0]) % 360
            if abs(d_az - 360) < abs(d_az):
                d_az = abs(d_az - 360)
            else:
                d_az = abs(d_az)
            d_el = abs(dest_pos[1] - cur_pos[1])
            delta = math.sqrt((d_az * math.cos(alt_av))**2 + d_el**2) or 0.01

            # compute speed, assuming we're slewing directly toward the target
            speed = float(self.config.get("slew", "speed"))
            speed_az = d_az / delta * speed / max(0.01, math.cos(alt_av))
            speed_el = d_el / delta * speed

            # leave loop if close enough on both axes
            if (d_az == 0.0 or d_az / speed_az < pre_time) and \
               (d_el == 0.0 or d_el / speed_el < pre_time):
                return

            # wait 10 milliseconds before testing again
            time.sleep(0.01)
