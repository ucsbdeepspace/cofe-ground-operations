# controller.py
# layer of abstraction for moving motors

import circle
import ephem
import math
import time
import threading

class Controller:
    
    def __init__ (self, logger, galil, converter, config):
        self.logger = logger
        self.galil = galil
        self.converter = converter
        
        self.scan_queue = 0 # number of scans left to do
    
    
    # current_pos: retrieve current motor positions
    # -> azimuth, altitude
    def current_pos (self):
        pos_enc = list(self.galil.pos)
        azimuth = ephem.degrees(self.converter.encoder_to_az(pos_enc[0]))
        altitude = ephem.degrees(self.converter.encoder_to_el(pos_enc[1]))
        
        return azimuth, altitude
    
    
    # scan: generic scan function
    #   (note: should be executed in a maximum of one thread at any time)
    #
    #   crd_list -> list([crd_a, crd_b])
    #     crd_a = coordinate that goes from 0 to 360 degrees
    #     crd_b = coordinate that goes from -90 to 90 degrees
    #   process_func: function to process list of points
    #     (optionally, use "process_hor" and "process_equ" below)
    #   repeat: number of times to repeat (use "True" for indefinite repetition)
    #   
    # -> (returns once scan is complete)
    def scan (self, crd_list, process_func, repeat = 1):
        
        # unset any previously set stop events
        self.stop = threading.Event()
        
        # repeat indefinitely
        if str(repeat) == str(True):
            self.scan_queue = 1
        else: # repeat for <repeat> times
            self.scan_queue = repeat
        
        # queue and process scan
        while self.scan_queue > 0 and not self.stop.is_set():
            
            # process forward scan and wait until scan is complete
            process_func(crd_list)
            
            # reverse direction and repeat, waiting until scan is complete
            crd_list.reverse()
            process_func(crd_list)
            
            # reset direction and prepare for next time
            crd_list.reverse()
            if str(repeat) != str(True):
                self.scan_queue = self.scan_queue - 1
        
        return 0
        
    # process_hor: process a list of horizontal coordinates to slew to
    #
    #   crd_list -> list([azi, alt]): list of coordinates to slew to (degrees)
    #
    # -> (returns once scan is complete)
    def process_hor (self, crd_list):
        
        i = 0
        
        # loop through all segments
        while len(crd_list) > i and not self.stop.is_set():
            self.goto(crd_list[i - 1])
            i = i + 1
        
        return 0
    
    
    # process_equ: process a list of equatorial coordinates to slew to
    #
    #   crd_list -> list([ra, de]): list of coordinates to slew to (degrees)
    #
    # -> (returns once scan is complete)
    def process_equ (self, crd_list):
        
        i = 0
        
        # start with current motor position
        prev_azi, prev_alt = self.current_pos()
        
        # loop through all segments
        while len(crd_list) > i and not self.stop.is_set():
            
            ##
            # iteratively compute the altitude and azimuth of a set of
            # equatorial coordinates at the time which we will reach that
            # point with the telescope -- ie. the current altitude and
            # azimuth of a particular set of a particular set of equatorial
            # coordinates will no longer be current by the time we get
            # there -- we need to find the new coordinates before moving
            ##
            dt0 = 0
            
            # continue looping until we've converged close enough to the
            #  actual amount of time it takes to reach our target point
            while True:
                
                # compute estimate of distance to the next point
                azi, alt = self.converter.radec_to_azel(
                    math.radians(crd_list[i][0]), math.radians(crd_list[i][1]),
                    dt0)
                d_azi = math.degrees(azi) - prev_azi
                d_alt = math.degrees(alt) - prev_alt
                cosAlt = math.cos(ephem.degree * 0.5 * (alt + prev_alt))
                
                # approximate angular distance to move (in degrees)
                delta = math.sqrt(d_azi ** 2 + (d_alt * cosAlt) ** 2)
                
                # estimate of time needed to get to next point
                dt = delta / float(self.config.get("slew", "speed"))
                if math.fabs(dt - dt0) < 0.01:
                    break # accurate enough, stop loop
                
                # not accurate enough, continue looping
                dt0 = dt
                
            # compute horizontal coordinates of equatorial coordinates after
            #  time dt has passed (the point where we should slew to)
            azi, alt = self.converter.radec_to_azel(
                math.radians(crd_list[i][0]), math.radians(crd_list[i][1]), dt)
            new_crd_h = [math.degrees(azi), math.degrees(alt)]
            
            # move to new position and reset for the next iteration
            self.goto(new_crd_h)
            prev_azi, prev_alt = azi, alt
            i = i + 1
        
        return 0
    
    
    # goto: slew to a particular coordinate from current position
    #
    #   hor_pos -> [azimuth, altitude]: new position to slew to
    #
    # -> (returns once slew has reached destination point)
    def goto (self, hor_pos):
        self.logger.info("slew to " + str(hor_pos[0]) + ", " + str(hor_pos[1]))
        
        # angular distance and bearing to new point
        cur_a, cur_b = self.current_pos()
        ang_dist = circle.distance([cur_a, cur_b], hor_pos)
        bearing = circle.bearing([cur_a, cur_b], hor_pos)
        
        # generate list of intermediate points to slew to
        num_int = int(ang_dist) # one intermediate point per degree
        point_list = []
        
        for i in range(1, num_int + 1):
            a, b = circle.waypoint([cur_a, cur_b], bearing,
                i * ang_dist / num_int)
            point_list.append([a, b])
        
        # TODO: slew to all points in point_list; stall until slew is finished
        return 0
    
    
    # track: follow an equatorial position indefinitely
    #
    #   equ_pos -> [ra, de]: position to track
    #
    # -> (returns once tracking ends)
    def track (self, equ_pos):
        # TODO: slew to equatorial coordinate and continue to track
        None

    
    # sync: set current position of motors
    #   hor_pos -> [az, el]: position to set motor position to
    def sync (self, hor_pos):
        # TODO: set position of motors to given position
        None
