# zspiral.py
# execute and get properties of zenith spiral scans

import math
import threading
import time

class Scan:
    
    def __init__ (self, logger, galil, converter, config):
        self.logger = logger
        self.galil = galil
        self.converter = converter
        self.config = config
    
    # scan: execute a scan
    #
    #   start_pt -> [az, el]: point to start and go up from
    #   increment: increment in altitude (degrees) per loop
    #      when positive => move in ccw spiral towards zenith
    #      when negative => move in cw spiral towards zenith
    #   repeat: number of complete in and out cycles to run
    def scan (self, start_pt, increment, repeat):
        self.stop = threading.Event()
        
        # compute horizon speed of each axis (only used if |speed| > 1e-5)
        speed = float(self.config.get("slew", "speed"))
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
        
        # set speed and acceleration
        speed = self.converter.az_to_encoder(float(self.config.get("slew", "speed")))
        self.galil.sendOnly("SP" + self.galil.axis_az + "=" + str(speed))
        self.galil.sendOnly("SP" + self.galil.axis_el + "=" + str(speed))
        
        accel_az = str(self.converter.az_to_encoder(float(self.config.get("slew", "accel"))))
        accel_el = str(self.converter.el_to_encoder(float(self.config.get("slew", "accel"))))
        self.galil.sendOnly("AC" + self.galil.axis_az + "=" + accel_az)
        self.galil.sendOnly("AC" + self.galil.axis_el + "=" + accel_el)
        self.galil.sendOnly("DC" + self.galil.axis_az + "=" + accel_az)
        self.galil.sendOnly("DC" + self.galil.axis_el + "=" + accel_el)
        
        # slew to starting point
        self.galil.sendOnly("PA" + self.galil.axis_az + "=" +
            str(self.converter.az_to_encoder(start_pt[0])))
        self.galil.sendOnly("PA" + self.galil.axis_el + "=" +
            str(self.converter.el_to_encoder(start_pt[1])))
        self.galil.sendOnly("BG")
        self.galil.sendOnly("AM") # stall until motion is complete
        
        # zero increment -- slew in circle
        if -1e-5 <= increment <= 1e-5:
            # move at speed v_az/cos(alt)
            circ_speed = int(speed / (math.cos(math.radians(start_pt[1])) + 0.01))
            self.galil.sendOnly("SP" + self.galil.axis_az + "=" + str(circ_speed))
            
            # check if cw or ccw
            if increment >= 0.0:
                angle = 360.0 # ccw viewing towards zenith
            else:
                angle = -360.0 # cw viewing towards zenith
            
            while self.scan_queue > 0 and not self.stop.is_set():
                # move azimuth motor 360 degrees
                self.galil.sendOnly("PR" + self.galil.axis_az + "=" +
                    str(self.converter.az_to_encoder(angle)))
                self.galil.sendOnly("BG " + self.galil.axis_az)
                    
                # reset position
                self.galil.sendOnly("AM")
                self.galil.sendOnly("DP" + self.galil.axis_az + "=" +
                    str(self.converter.az_to_encoder(start_pt[0])))
                
                if str(repeat) != str(True):
                    self.scan_queue -= 1
                
                # stall until motion is approximately complete
                time.sleep(self.converter.az_to_encoder(360.0) / circ_speed)
                
        # non-zero increment -- slew in ccw spiral to zenith then back
        else: # math.fabs(increment) > 1e-5
            while self.scan_queue > 0 and not self.stop.is_set():
                # TODO: move azimuth motor at speed min(10*speed, v_az/cos(alt)
                #       until altitude = 90; move altitude motor at speed
                #       v_el until altitude = 90.
                
                if self.scan_queue <= 0.5 or self.stop.is_set():
                    self.scan_queue = 0
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
                point_list.append([float(i), start_pt[1]])
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
