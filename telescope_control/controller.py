# controller.py
# layer of abstraction for moving motors

import ephem
import math
import numpy as np
import time
import threading

class Controller:
    
    def __init__ (self, logger, galil, converter, config):
        self.logger = logger
        self.galil = galil
        self.converter = converter
        self.config = config
        
        self.scan_queue = 0 # number of scans left to do
    
    
    # scan: generic scan function
    #   (note: should be executed in a maximum of one thread at any time)
    #
    #   crd_list -> list([crd_a, crd_b])
    #     crd_a = coordinate that goes from 0 to 360 degrees
    #     crd_b = coordinate that goes from -90 to 90 degrees
    #   process_func: function to process list of points
    #     (see "queue_hor" and "queue_equ" below)
    #   speed: rate (degrees/sec) to slew at
    #      note: use max speed if speed <= 0 or speed >= max speed
    #   repeat: number of times to repeat (use "True" for indefinite repetition)
    #   
    # -> error_code (0 = no error), error_msg (None, if error_code == 0)
    #      (returns once scan is complete)
    def scan (self, crd_list, process_func, speed, repeat = 1):
        
        # unset any previously set stop events
        self.stop = threading.Event()
        
        # repeat indefinitely
        if repeat == True:
            self.scan_queue = 1
        else: # repeat for <repeat> times
            self.scan_queue = repeat
        
        # queue and process scan
        while self.scan_queue > 0 and not self.stop.is_set():
            
            # process forward scan and wait until scan is complete
            process_func(crd_list, speed)
            
            # reverse direction and repeat, waiting until scan is complete
            crd_list.reverse()
            process_func(crd_list, speed)
            
            # reset direction and prepare for next time
            crd_list.reverse()
            if repeat != True:
                self.scan_queue = self.scan_queue - 1
        
        return 0
        
    # process_hor: process a list of horizontal coordinates to slew to
    #
    #   crd_list -> list([azi, alt]): list of coordinates to slew to (degrees)
    #   speed: rate (degrees/sec) to slew at
    #
    # -> error_code, error_msg
    #      (returns once scan is complete)
    def process_hor (self, crd_list, speed):
        
        i = 0
        
        # loop through all segments
        while len(crd_list) > i and not self.stop.is_set():
            self.goto(crd_list[i - 1], speed)
            i = i + 1
        
        return 0
    
    
    # process_equ: process a list of equatorial coordinates to slew to
    #
    #   crd_list -> list([ra, de]): list of coordinates to slew to (degrees)
    #   speed: rate (degrees/sec) to slew at
    #
    # -> error_code (0 = no error), error_msg (None, if error_code == 0)
    #      (returns once scan is complete)
    def process_equ (self, crd_list, speed):
        
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
                    crd_list[i][0], crd_list[i][1], dt0)
                d_azi = azi - prev_azi
                d_alt = alt - prev_alt
                cosAlt = math.cos(ephem.degree * 0.5 * (alt + prev_alt))
                
                # approximate angular distance to move (in degrees)
                delta = math.sqrt(d_azi ** 2 + (d_alt * cosAlt) ** 2)
                
                # estimate of time needed to get to next point
                dt = delta / speed
                if math.fabs(dt - dt0) < 0.01:
                    break # accurate enough, stop loop
                
                # not accurate enough, continue looping
                dt0 = dt
                
            # compute horizontal coordinates of equatorial coordinates after
            #  time dt has passed (the point where we should slew to)
            azi, alt = self.converter.radec_to_azel(
                crd_list[i][0], crd_list[i][1], dt)
            new_crd_h = [np.degrees(azi), np.degrees(alt)]
            
            # move to new position and reset for the next iteration
            self.goto(new_crd_h, speed)
            prev_azi, prev_alt = azi, alt
            i = i + 1
        
        return 0
    
    
    # goto: slew to a particular coordinate from current position
    #
    #   coord_h -> [azimuth, altitude]: new position to slew to
    #   speed: rate (degrees/sec) to slew to new position
    #
    # -> error_code, error_msg
    def goto (self, coord_h, speed):
        self.logger.info("slew to " + str(coord_h[0]) + ", " + str(coord_h[1]))
        # TODO: stall until slew is finished
        return 0
    
    
    # move_axis: move single axis to some position at some speed
    #
    #   axis: integer indicating axis
    #      0 = azimuth axis
    #      1 = altitude axis
    #   new_pos: coordinate (degrees) to move axis to
    #   speed: rate (degrees/sec) to slew to new position
    #
    # -> error_code, error_msg
    def move_axis (self, axis, new_pos, speed):
        return 0
    
    
    # current_pos: retrieve current motor positions
    # -> azimuth, altitude
    def current_pos (self):
        pos_enc = list(self.galil.pos)
        azimuth = ephem.degrees(self.converter.encoder_to_az(pos_enc[0]))
        altitude = ephem.degrees(self.converter.encoder_to_el(pos_enc[1]))
        
        return azimuth, altitude
