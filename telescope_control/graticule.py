# graticule.py
# execute and get properties of horizontal graticule scans

import math
import threading

class Scan:
    
    def __init__ (self, controller):
        self.controller = controller
    
    # scan: execute a scan
    #
    #   left_az, right_az, low_el, high_el: slew boundaries
    #      (note: starts at left_az, low_el and proceeds to right_az, high_el)
    #   num_turns: number of back and forth turns to do -- 1 turn = 2 switchbacks
    #   repeat: number of complete in and out cycles to run
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
        speed = self.controller.converter.az_to_encoder(float(
            self.controller.config.get("slew", "speed")
        ))
        self.controller.galil.sendOnly("SP" +
            self.controller.galil.axis_az + "=" + str(speed))
        self.controller.galil.sendOnly("SP" +
            self.controller.galil.axis_el + "=" + str(speed))
        
        accel_az = str(self.controller.converter.az_to_encoder(
            float(self.controller.config.get("slew", "accel"))
        ))
        accel_el = str(self.controller.converter.el_to_encoder(
            float(self.controller.config.get("slew", "accel"))
        ))
        self.controller.galil.sendOnly("AC" +
            self.controller.galil.axis_az + "=" + accel_az)
        self.controller.galil.sendOnly("AC" +
            self.controller.galil.axis_el + "=" + accel_el)
        self.controller.galil.sendOnly("DC" +
            self.controller.galil.axis_az + "=" + accel_az)
        self.controller.galil.sendOnly("DC" +
            self.controller.galil.axis_el + "=" + accel_el)
        
        # slew to left_az, low_el
        self.controller.galil.sendOnly("PA" +
            self.controller.galil.axis_az + "=" +
            str(self.controller.converter.az_to_encoder(left_az)))
        self.controller.galil.sendOnly("PA" +
            self.controller.galil.axis_el + "=" +
            str(self.controller.converter.el_to_encoder(low_el)))
        self.controller.galil.sendOnly("BG")
        self.controller.galil.sendOnly("AM") # stall until motion is complete
        
        # queue and process scan
        while self.scan_queue > 0 and not self.stop.is_set():
            
            # upward part of motion
            for i in range(0, num_turns):
                
                alt1 = (1 - float(i)/num_turns)*low_el \
                          + float(i)/num_turns*high_el
                # increase altitude to alt1 if needed
                self.controller.galil.sendOnly("PA" +
                    self.controller.galil.axis_el + "=" +
                    str(self.controller.converter.el_to_encoder(alt1)))
                self.controller.galil.sendOnly("BG")
                self.controller.galil.sendOnly("AM") # stall until motion is complete
                
                # increase azimuth until right_az
                self.controller.galil.sendOnly("SP" +
                    self.controller.galil.axis_az + "=" +
                    str(speed / max(0.01, math.cos(math.radians(alt1)))))
                self.controller.galil.sendOnly("PA" +
                    self.controller.galil.axis_az + "=" +
                    str(self.controller.converter.el_to_encoder(right_az)))
                self.controller.galil.sendOnly("BG")
                self.controller.galil.sendOnly("AM") # stall until motion is complete
                
                alt2 = (1.0 - (i+0.5)/num_turns)*low_el \
                            + (i+0.5)/num_turns*high_el
                # increase altitude to alt2
                self.controller.galil.sendOnly("PA" +
                    self.controller.galil.axis_el + "=" +
                    str(self.controller.converter.el_to_encoder(alt2)))
                self.controller.galil.sendOnly("BG")
                self.controller.galil.sendOnly("AM") # stall until motion is complete
                
                # decrease azimuth until we're back at left_az
                self.controller.galil.sendOnly("SP" +
                    self.controller.galil.axis_az + "=" +
                    str(speed / max(0.01, math.cos(math.radians(alt2)))))
                self.controller.galil.sendOnly("PA" +
                    self.controller.galil.axis_az + "=" +
                    str(self.controller.converter.el_to_encoder(left_az)))
                self.controller.galil.sendOnly("BG")
                self.controller.galil.sendOnly("AM") # stall until motion is complete
            
            # increase altitude to high_el
            self.controller.galil.sendOnly("PA" +
                self.controller.galil.axis_el + "=" +
                str(self.controller.converter.el_to_encoder(high_el)))
            self.controller.galil.sendOnly("BG")
            self.controller.galil.sendOnly("AM") # stall until motion is complete
            
            # increase azimuth to right_az
            self.controller.galil.sendOnly("SP" +
                self.controller.galil.axis_az + "=" +
                str(speed / max(0.01, math.cos(math.radians(high_el)))))
            self.controller.galil.sendOnly("PA" +
                self.controller.galil.axis_az + "=" +
                str(self.controller.converter.el_to_encoder(right_az)))
            self.controller.galil.sendOnly("BG")
            self.controller.galil.sendOnly("AM") # stall until motion is complete
            
            # check if we should do downward part
            if self.scan_queue <= 0.5 or self.stop.is_set():
                self.scan_queue = 0
                break
            
            # downward part of motion
            for i in range(0, num_turns):
                
                alt1 = (1 - float(i)/num_turns)*high_el \
                          + float(i)/num_turns * low_el
                # decrease altitude to alt1 if needed
                self.controller.galil.sendOnly("PA" +
                    self.controller.galil.axis_el + "=" +
                    str(self.controller.converter.el_to_encoder(alt1)))
                self.controller.galil.sendOnly("BG")
                self.controller.galil.sendOnly("AM") # stall until motion is complete
                
                # decrease azimuth until left_az
                self.controller.galil.sendOnly("SP" +
                    self.controller.galil.axis_az + "=" +
                    str(speed / max(0.01, math.cos(math.radians(alt1)))))
                self.controller.galil.sendOnly("PA" +
                    self.controller.galil.axis_az + "=" +
                    str(self.controller.converter.el_to_encoder(left_az)))
                self.controller.galil.sendOnly("BG")
                self.controller.galil.sendOnly("AM") # stall until motion is complete
                
                alt2 = (1.0 - (i+0.5)/num_turns)*high_el \
                            + (i+0.5)/num_turns * low_el
                # decrease altitude to alt2
                self.controller.galil.sendOnly("PA" +
                    self.controller.galil.axis_el + "=" +
                    str(self.controller.converter.el_to_encoder(alt2)))
                self.controller.galil.sendOnly("BG")
                self.controller.galil.sendOnly("AM") # stall until motion is complete
                
                # increase azimuth until we're back at right_az
                self.controller.galil.sendOnly("SP" +
                    self.controller.galil.axis_az + "=" +
                    str(speed / max(0.01, math.cos(math.radians(alt2)))))
                self.controller.galil.sendOnly("PA" +
                    self.controller.galil.axis_az + "=" +
                    str(self.controller.converter.el_to_encoder(right_az)))
                self.controller.galil.sendOnly("BG")
                self.controller.galil.sendOnly("AM") # stall until motion is complete
            
            # decrease altitude to low_el
            self.controller.galil.sendOnly("PA" +
                self.controller.galil.axis_el + "=" +
                str(self.controller.converter.el_to_encoder(low_el)))
            self.controller.galil.sendOnly("BG")
            self.controller.galil.sendOnly("AM") # stall until motion is complete
            
            # decrease azimuth to left_az
            self.controller.galil.sendOnly("SP" +
                self.controller.galil.axis_az + "=" +
                str(speed / max(0.01, math.cos(math.radians(low_el)))))
            self.controller.galil.sendOnly("PA" +
                self.controller.galil.axis_az + "=" +
                str(self.controller.converter.el_to_encoder(left_az)))
            self.controller.galil.sendOnly("BG")
            self.controller.galil.sendOnly("AM") # stall until motion is complete
            
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
            for j in range(1, int(right_az - left_az) / 10):
                crd_list.append([left_az + j, alt1])
            crd_list.append([right_az, alt1])
            
            # move towards pt3 half a step and go the other direction
            alt2 = (1.0 - (i+0.5)/num_turns)*low_el \
                        + (i+0.5)/num_turns*high_el
            crd_list.append([right_az, alt2])
            for j in range(1, int(right_az - left_az) / 10):
                crd_list.append([right_az - j, alt2])
            crd_list.append([left_az, alt2])
        
        # execute the final stretch of the scan
        crd_list.append([left_az, high_el])
        for j in range(1, int(right_az - left_az) / 10):
            crd_list.append([left_az + j, high_el])
        crd_list.append([right_az, high_el])
        
        return crd_list
