# graticule.py
# execute and get properties of horizontal graticule scans

import math
import threading

class Scan:
    
    def __init__ (self, logger, galil, converter, config):
        self.logger = logger
        self.galil = galil
        self.converter = converter
        self.config = config
    
    # scan: execute a scan
    #
    #   left_az, right_az, low_el, high_el: slew boundaries
    #      (note: starts at left_az, low_el and proceeds to right_az, high_el)
    #   num_turns: number of back and forth turns to do -- 1 turn = 2 switchbacks
    #   repeat: number of complete in and out cycles to run
    #
    # -> (returns once scan is complete)
    def scan (self, left_az, right_az, low_el, high_el, num_turns, repeat):
        self.stop = threading.Event()
        
        # ensure that right_az-360 < left_az < right_az
        left_az = left_az % 360
        right_az = right_az % 360
        
        if left_az > right_az:
            left_az -= 360
        
        # set up queue
        if str(repeat) == str(True):
            self.scan_queue = 1
        else: # repeat for <repeat> times
            self.scan_queue = repeat
        
        # set speed and acceleration
        self.sendOnly("SPA=" + self.config.get("slew", "speed"))
        self.sendOnly("ACA=" + self.config.get("slew", "accel"))
        
        # TODO: slew to left_az, low_el and pause
        
        # queue and process scan
        while self.scan_queue > 0 and not self.stop.is_set():
            
            # upward part of motion
            for i in range(0, num_turns):
                
                alt1 = (1 - float(i)/num_turns)*low_el \
                          + float(i)/num_turns*high_el
                # TODO: increase altitude to alt1 if needed
                # TODO: increase azimuth until right_az
                
                alt2 = (1.0 - (i+0.5)/num_turns)*low_el \
                            + (i+0.5)/num_turns*high_el
                # TODO: increase altitude to alt2
                # TODO: decrease azimuth until we're back at left_az
            
            # TODO: increase altitude to high_el
            # TODO; increase azimuth to right_el
            
            # check if we should do downward part
            if self.scan_queue <= 0.5 or self.stop.is_set():
                self.scan_queue = 0
                break
            
            # downward part of motion
            for i in range(0, num_turns):
                
                alt1 = (1 - float(i)/num_turns)*high_el \
                          + float(i)/num_turns * low_el
                # TODO: decrease altitude to alt1 if needed
                # TODO: decrease azimuth until left_az
                
                alt2 = (1.0 - (i+0.5)/num_turns)*high_el \
                            + (i+0.5)/num_turns * low_el
                # TODO: decrease altitude to alt2
                # TODO: increase azimuth until we're back at right_az
            
            # TODO: decrease altitude to low_el
            # TODO: decrease azimuth to left_az
            
            if str(repeat) != str(True):
                self.scan_queue -= 1
        
        return 0
        

    # points: retrieve a list of points for plotting on the sky chart
    #
    #   left_az, right_az, low_el, high_el: slew boundaries
    #      (note: starts at left_az, low_el and proceeds to right_az, high_el)
    #   num_turns: number of back and forth turns to do -- 1 turn = 2 switchbacks
    #
    # -> point_list -> list([az, el]): list of closely spaced points along
    #                                  the scan path
    def points (self, left_az, right_az, low_el, high_el, num_turns):
        crd_list = []
        
        # ensure that right_az-360 < left_az < right_az
        left_az = left_az % 360
        right_az = right_az % 360
        
        if left_az > right_az:
            left_az -= 360
        
        for i in range(0, num_turns):
            
            # start on left_az side and move toward right_az side
            alt1 = (1 - float(i)/num_turns)*low_el \
                      + float(i)/num_turns*high_el
            crd_list.append([left_az, alt1])
            for j in range(1, int(right_az - left_az)):
                crd_list.append([left_az + j, alt1])
            crd_list.append([right_az, alt1])
            
            # move towards pt3 half a step and go the other direction
            alt2 = (1.0 - (i+0.5)/num_turns)*low_el \
                        + (i+0.5)/num_turns*high_el
            crd_list.append([right_az, alt2])
            for j in range(1, int(right_az - left_az)):
                crd_list.append([right_az - j, alt2])
            crd_list.append([left_az, alt2])
        
        # execute the final stretch of the scan
        crd_list.append([left_az, high_el])
        for j in range(1, int(right_az - left_az)):
            crd_list.append([left_az + j, high_el])
        crd_list.append([right_az, high_el])
        
        return crd_list
