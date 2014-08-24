# zspiral.py
# execute and get properties of zenith spiral scans

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
    #   cycles: number of complete in and out cycles to run
    #   speed: maximum angular speed in degrees/sec to move at
    #   accel: acceleration (degrees/sec^2) to change velocity
    #
    # -> (returns once scan is complete)
    def scan (start_pt, increment, cycles, speed, accel):
        pass

    # points: retrieve a list of points for plotting on the sky chart
    #
    #   start_pt -> [az, el]: point to start and go up from
    #   increment: increment in altitude (degrees) per loop
    #      when positive => move in ccw spiral towards zenith
    #      when negative => move in cw spiral towards zenith
    #
    # -> point_list -> list([az, el]): list of closely spaced points along
    #                                  the scan path
    def points (start_pt, increment):
        pass
