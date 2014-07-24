# controller.py
# layer of abstraction for moving motors

import ephem
import math
import numpy as np

class Controller:
    
    def __init__ (self, galil, converter, config):
        self.galil = galil
        self.converter = converter
        self.config = config
    
    
    # queue_equ: queue and process a list of equatorial coordinates to slew to
    #
    #   crd_list -> list([ra, de]): list of coordinates to slew to (degrees)
    #   speed: rate (degrees/sec) to slew at
    #      note: use max speed if speed <= 0 or speed >= max speed
    #   on_done: argument-less function to call when complete
    #
    # -> error_code (0 = no error), error_msg (None, if error_code == 0)
    def queue_equ (self, crd_list, speed, on_done):
        
        i = 0
        
        # start queue with current motor position
        azi, alt = self.current_pos()
        prev_azi, prev_alt = np.degrees(azi), np.degrees(alt)
        
        # this function should be called once processing of previous item in
        #  list is complete
        def next_item ():
            
            if len(crd_list) > i:
                
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
                    if math.abs(dt - dt0) < 0.01:
                        break # accurate enough, stop loop
                    
                    # not accurate enough, continue looping
                    dt0 = dt
                    
                # compute horizontal coordinates of equatorial coordinates after
                #  time dt has passed (the point where we should slew to)
                azi, alt = self.converter.radec_to_azel(
                    crd_list[i][0], crd_list[i][1], dt)
                new_crd_h = [np.degrees(azi), np.degrees(alt)]
                
                # move onto the next item the next time this function is called
                i = i + 1
                prev_azi, prev_alt = azi, alt
                
                # move to computed horizontal coordinates, returning to the
                #  beginning of this current function when complete
                self.goto(new_crd_h, speed, next_item)
                
            # we've now completed processing the queue
            else:
                on_done() # signal completion of processing
            
        # move to first item (will recursively continue until all items complete)
        next_item()
        
        return 0
    
    
    # goto: slew to a particular coordinate from current position
    #
    #   coord_h -> [azimuth, altitude]: new position to slew to
    #   speed: rate (degrees/sec) to slew to new position
    #   on_done: argument-less function to call when complete
    #
    # -> error_code, error_msg
    def goto (self, coord_h, speed, on_done):
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
        azimuth = self.converter.encoder_to_az(pos_enc[0])
        altitude = self.converter.encoder_to_el(pos_enc[1])
        
        return azimuth, altitude
