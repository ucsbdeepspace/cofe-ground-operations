# zspiral.py
# execute and get properties of zenith spiral scans

import math
import threading

class Scan:
    
    def __init__ (self, logger, galil):
        self.logger = logger
        self.galil = galil
    
    # scan: execute a scan
    #
    #   start_pt -> [az, el]: point to start and go up from
    #   increment: increment in altitude (degrees) per loop
    #      when positive => move in ccw spiral towards zenith
    #      when negative => move in cw spiral towards zenith
    #   speed: maximum angular speed in degrees/sec to move at
    #   accel: acceleration (degrees/sec^2) to change velocity
    #   repeat: number of complete in and out cycles to run
    #
    # -> (returns once scan is complete)
    def scan (self, start_pt, increment, speed, accel, repeat):
        self.stop = threading.Event()
        
        # compute horizon speed of each axis (only used if |speed| > 1e-5)
        v_az = speed * 360 / math.sqrt(360**2 + increment**2)
        v_el = speed * increment / math.sqrt(360**2 + increment**2)
        
        # switch only azimuth direction if negative increment, not altitude
        if increment < -1e-5:
            v_az = -v_az
            v_el = -v_el
        
        # set up queue
        if str(repeat) == str(True):
            self.scan_queue = 1
        else: # repeat for <repeat> times
            self.scan_queue = repeat
        
        # TODO: slew to starting point and pause
        
        # zero increment -- slew in circle
        if -1e-5 <= increment <= 1e-5:
            while self.scan_queue > 0 and not self.stop.is_set():
                # TODO: move azimuth motor at speed v_az/cos(alt) 360 degrees
                #       without pausing unless self.scan_queue == 1 and
                #       str(repeat) != str(True)
                
                if str(repeat) != str(True):
                    self.scan_queue -= 1
                
        # non-zero increment -- slew in ccw spiral to zenith then back
        else: # math.fabs(increment) > 1e-5
            while self.scan_queue > 0 and not self.stop.is_set():
                # TODO: move azimuth motor at speed min(10*speed, v_az/cos(alt)
                #       until altitude = 90; move altitude motor at speed
                #       v_el until altitude = 90.
                
                if str(repeat) != str(True) and self.scan_queue <= 0.5:
                    break
                
                # TODO: repeat scan, moving both motors in opposite direction
                #       until altitude = start_pt[1]
                
                if str(repeat) != str(True):
                    self.scan_queue -= 1
        
        return 0
        

    # points: retrieve a list of points for plotting on the sky chart
    #
    #   start_pt -> [az, el]: point to start and go up from
    #   increment: increment in altitude (degrees) per loop
    #      when positive => move in ccw spiral towards zenith
    #      when negative => move in cw spiral towards zenith
    #
    # -> point_list -> list([az, el]): list of closely spaced points along
    #                                  the scan path
    def points (self, start_pt, increment):
        point_list = []
        
        # no increment, stay on same level
        if math.fabs(increment) <= 1e-5:
            for i in range (0, 361):
                point_list.append([float(i), start_pt[0]])
            return point_list
        
        # positive increment: approach zenith in ccw spiral
        if increment > 1e-5:
            rotations = (90.0 - start_pt[1]) / increment
            for i in range(0, int(360 * rotations)):
                point_list.append([(start_pt[0] + i) % 360.0,
                                    start_pt[1] + i / 360.0 * increment])
            return point_list
        
        # negative increment: approach zenith in cw spiral
        if increment < -1e-5:
            rotations = -(90.0 - start_pt[1]) / increment
            for i in range(0, int(360 * rotations)):
                point_list.append([(start_pt[0] - i) % 360.0,
                                    start_pt[1] - i / 360.0 * increment])
            return point_list
