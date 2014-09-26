# circular.py
# execute and get properties of circular scan

import math
import threading
import time

class Scan:

    def __init__ (self, controller):
        self.controller = controller

    # scan: execute a scan
    #
    #   start_pt -> [az, el]: point to start from
    #   is_ccw: move counterclockwise (to the right)
    #   repeat: number of rotations
    def scan (self, start_pt, is_ccw = True, repeat = True):

        # find nearest starting point to current position
        cur_pos = self.controller.current_pos()
        d_az = (start_pt[0] - cur_pos[0]) % 360
        if d_az > 180:
            d_az -= 180 # convert to range (-180, 180]
        start_pt[0] = cur_pos[0] + d_az

        # move to starting point
        self.controller.stop = threading.Event()
        self.controller.slew(start_pt)
        self.controller.stall(start_pt)
        self.controller.stop = threading.Event()

        # compute speed and acceleration
        speed = float(self.controller.config.get("slew", "speed")) \
            / max(0.01, math.cos(math.radians(start_pt[1])))
        if not is_ccw:
            speed = -speed

        v_az = str(self.controller.converter.az_to_encoder(speed))
        self.controller.galil.sendOnly("AM")
        self.controller.galil.sendAndReceive("JG"
            + self.controller.galil.axis_az + "=" + str(v_az))

        accel = float(self.controller.config.get("slew", "accel")) \
            / max(0.01, math.cos(math.radians(start_pt[1])))
        a_az = str(self.controller.converter.az_to_encoder(accel))
        self.controller.galil.sendOnly("AC"
            + self.controller.galil.axis_az + "=" + str(a_az))
        self.controller.galil.sendOnly("DC"
            + self.controller.galil.axis_az + "=" + str(a_az))

        # start scan
        self.controller.galil.sendOnly("BG")

        # set up queue
        if str(repeat) == str(True):

            # wait told to stop
            while not self.stop.is_set():
                time.sleep(0.1)

        else: # repeat for <repeat> times
            self.scan_queue = repeat

            # wait until told to stop or queue is empty
            while not self.controller.stop.is_set() and self.scan_queue > 0:

                # wait approximately one cycle
                time.sleep(max(2, 360.0 / speed))
                self.controller.stall(start_pt)

                # decrease scan queue
                self.scan_queue -= 1

        # stop scan and update position
        self.controller.galil.sendOnly("ST")
        time.sleep(abs(speed / accel)) # wait for motor to stop
        self.controller.wait()

        az, el = self.controller.current_pos()
        self.controller.sync([az % 360.0, el])


    # points: retrieve a list of points for plotting on the sky chart
    #
    #   start_pt -> [az, el]: point to start from
    #
    # -> point_list -> list([az, el]): list of closely spaced points along
    #                                  the scan path
    def points (self, start_pt):
        point_list = []

        # no increment, stay on same level
        for i in range (0, 361):
            point_list.append([float(i), start_pt[1]])
        return point_list
