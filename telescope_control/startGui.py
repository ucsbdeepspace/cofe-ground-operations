try:
    import configparser
except:
    import ConfigParser as configparser

import ephem
import math
import string
import sys
import time
import traceback
import wx

import controller
import gui
import globalConf
import planets
import scans
import threading
import units

import circular
import graticule

class MainWindow(gui.TelescopeControlFrame):
    def __init__(self, galilInterface, *args, **kwargs):

        # load configuration
        print("Loading configuration...")
        self.config = configparser.ConfigParser()
        self.config.read("config.ini")
        self.galil = galilInterface

        # axes
        self.galil.axis_az = self.config.get("axes", "az")
        self.galil.axis_el = self.config.get("axes", "el")

        print("Setting up units converter...")
        self.converter = units.Units(self.config) # ...and the converter...

        gui.TelescopeControlFrame.__init__(self, self.converter, self.config,
            *args, **kwargs)
        self.change_scan_crd(None)

        self.scan_thread = None
        self.step_size = 0

        print("Setting up scanning...")
        # standard scan
        self.controller = controller.Controller(self.logger,
            self.galil, self.converter, self.config)
        # simple scans
        self.hg_scan = graticule.Scan(self.controller)
        self.cc_scan = circular.Scan(self.controller)

        self.poll_update = wx.Timer(self)
        print("Setting up event handlers...")
        self.bind_events()
        self.Bind(wx.EVT_TIMER, self.update_display, self.poll_update)
        print("Starting display update poll...")
        self.poll_update.Start(30)
        print('')

        print("Make sure to turn on the motors you will use!")
        print("Motors are automatically turned off when you exit.")
        print('')

    def bind_events(self):
        # By putting the event bindings here, it means I can clear out the event handlers from the parent class (gui.py)
        # without breaking it
        self.Bind(wx.EVT_CLOSE, self.stop)

        self.Bind(wx.EVT_BUTTON, self.stop, self.button_stop_all)
        self.Bind(wx.EVT_BUTTON, self.toggle_motor_state, self.buttton_az_motor)
        self.Bind(wx.EVT_BUTTON, self.toggle_motor_state, self.button_el_motor)
        self.Bind(wx.EVT_TEXT, self.set_step_size, self.step_size_input)

        self.Bind(wx.EVT_BUTTON, self.reset_galil, self.reset_input)
        self.Bind(wx.EVT_BUTTON, self.rezero_galil, self.rezero_input)

        self.Bind(wx.EVT_BUTTON, self.move_rel, self.button_up)
        self.Bind(wx.EVT_BUTTON, self.move_rel, self.button_left)
        self.Bind(wx.EVT_BUTTON, self.move_rel, self.button_right)
        self.Bind(wx.EVT_BUTTON, self.move_rel, self.button_down)

        self.Bind(wx.EVT_BUTTON, self.goto_hor, self.goto_hor_input)
        self.Bind(wx.EVT_BUTTON, self.sync_hor, self.sync_hor_input)
        self.Bind(wx.EVT_BUTTON, self.goto_equ, self.goto_equ_input)
        self.Bind(wx.EVT_BUTTON, self.sync_equ, self.sync_equ_input)

        self.Bind(wx.EVT_BUTTON, self.sso_goto, self.sso_goto_input)
        self.Bind(wx.EVT_BUTTON, self.sso_sync, self.sso_sync_input)
        self.Bind(wx.EVT_BUTTON, self.sso_scan, self.sso_scan_input)
        self.Bind(wx.EVT_BUTTON, self.ngcic_goto, self.ngcic_goto_input)
        self.Bind(wx.EVT_BUTTON, self.ngcic_sync, self.ngcic_sync_input)
        self.Bind(wx.EVT_BUTTON, self.ngcic_scan, self.ngcic_scan_input)

        self.Bind(wx.EVT_BUTTON, self.scan, self.buttonScanStart)
        self.Bind(wx.EVT_BUTTON, self.set_preview, self.preview_scan)

        self.Bind(wx.EVT_BUTTON, self.horiz_scan, self.hg_begin_input)
        self.Bind(wx.EVT_BUTTON, self.hg_preview, self.hg_preview_input)
        self.Bind(wx.EVT_BUTTON, self.circular_scan, self.cc_begin_input)
        self.Bind(wx.EVT_BUTTON, self.cc_preview, self.cc_preview_input)

        self.Bind(wx.EVT_COMBOBOX, self.change_cs, self.chart_crdsys)
        self.Bind(wx.EVT_SPINCTRL, self.change_fov, self.chart_fov)
        self.Bind(wx.EVT_COMBOBOX, self.change_cen, self.cur_center_input)
        self.Bind(wx.EVT_COMBOBOX, self.change_scan_crd, self.scan_coordsys)

        self.Bind(wx.EVT_TEXT, self.change_speed, self.scan_speed_input)
        self.Bind(wx.EVT_TEXT, self.change_accel, self.scan_accel_input)
        self.Bind(wx.EVT_TEXT, self.change_lon, self.obs_lon_input)
        self.Bind(wx.EVT_TEXT, self.change_lat, self.obs_lat_input)
        self.Bind(wx.EVT_CHECKBOX, self.change_gps_usage, self.gps_time_input)

        self.Bind(wx.EVT_TEXT, self.change_lim, self.az_min_input)
        self.Bind(wx.EVT_TEXT, self.change_lim, self.az_max_input)
        self.Bind(wx.EVT_TEXT, self.change_lim, self.el_min_input)
        self.Bind(wx.EVT_TEXT, self.change_lim, self.el_max_input)
        self.Bind(wx.EVT_CHECKBOX, self.change_lim, self.az_limit_input)
        self.Bind(wx.EVT_CHECKBOX, self.change_lim, self.el_limit_input)


    def goto_hor (self, event):

        # read end position
        azPos = float(self.goto_az_input.GetValue())
        elPos = float(self.goto_el_input.GetValue())
        azVal = self.converter.az_to_encoder(azPos)
        elVal = self.converter.el_to_encoder(elPos)

        # move to new position at appropriate speed and acceleration
        self.controller.slew([azPos, elPos])

        event.Skip()

    def sync_hor (self, event):
        self.controller.sync([float(self.sync_az_input.GetValue()),
                              float(self.sync_el_input.GetValue())])
        event.Skip()

    def goto_equ(self, event):
        # track given equatorial position
        equ_pos = [float(self.goto_ra_input.GetValue()),
                   float(self.goto_de_input.GetValue())]
        self.scan_thread = threading.Thread(target=lambda:
            self.controller.track(equ_pos))
        self.scan_thread.start() # run in new thread

        event.Skip()

    def sync_equ (self, event):
        # convert to horizontal
        az, el = self.converter.radec_to_azel(
            math.radians(float(self.sync_ra_input.GetValue())),
            math.radians(float(self.sync_de_input.GetValue())))
        hor_pos = [math.degrees(az), math.degrees(el)]

        self.controller.sync(hor_pos)
        event.Skip()

    def stop (self, event):
        """This function is called whenever one of the stop
        buttons is pressed."""
        if hasattr(self.controller, "stop"):
            self.controller.stop.set()

        if hasattr(self.hg_scan, "stop"):
            self.hg_scan.stop.set()
        if hasattr(self.hg_scan.controller, "stop"):
            self.hg_scan.controller.stop.set()

        if hasattr(self.cc_scan.controller, "stop"):
            self.cc_scan.controller.stop.set()

        self.galil.sendOnly("ST")
        self.copy_config()

        time.sleep(0.51) # provide enough time for tracking to exit
        event.Skip()

    def toggle_motor_state(self, event):
        """This function is called whenever you toggle the
        motor on/motor off buttons. I think it would be nifty
        to add something to change the size/color/font of the
        button text here. It would help alot."""
        axis = self.galil.axis_az
        if event.GetId() == self.button_el_motor.GetId():
            axis = self.galil.axis_el
        if self.galil.checkMotorPower(string.uppercase.index(axis)):
            print("Turning off motor for axis {}.".format(axis))
            self.galil.sendOnly("MO " + axis)
        else:
            print("Turning on motor for axis {}.".format(axis))
            self.galil.sendOnly("SH " + axis)
        print('')
        event.Skip()

    def set_step_size(self, event):
        """This is called after you type a number nad press enter
        on the step size box next to the arrow buttons."""
        try:
            self.step_deg = float(self.step_size_input.GetValue())
            if math.isnan(self.step_deg):
                raise Exception()
        except:
            raise ValueError("Invalid step size.")

        self.step_size = \
            {self.galil.axis_az : self.converter.az_to_encoder(self.step_deg),
             self.galil.axis_el : self.converter.el_to_encoder(self.step_deg)}

    # reload programs into the Galil
    def reset_galil (self, event):
        self.galil.resetGalil()
        event.Skip()

    # go to physical zero position
    def rezero_galil (self, event):
        self.galil.executeFunction("HOMEA")
        event.Skip()

    # arrow button clicked
    def move_rel(self, event):
        self.set_step_size(None)  # read step size

        # stop any previous motion
        self.galil.sendOnly("ST")

        # get current position
        cur_pos = self.controller.current_pos()

        # list((button, sign of slew, axis))
        buttons = {self.button_up.GetId()    : [ 1, self.galil.axis_el],
                   self.button_down.GetId()  : [-1, self.galil.axis_el],
                   self.button_right.GetId() : [ 1, self.galil.axis_az],
                   self.button_left.GetId()  : [-1, self.galil.axis_az]}

        sign = buttons[event.GetId()][0]
        axis = buttons[event.GetId()][1]
        try:
            self.logger.info("moving {} degrees on axis {}.".format(
                sign * self.step_deg, axis))

            # set speed of axes
            speed = float(self.config.get("slew", "speed"))
            speed_az = self.converter.az_to_encoder( # adjust for altitude
                speed / max(0.01, math.cos(math.radians(cur_pos[1]))))
            speed_el = self.converter.el_to_encoder(speed)
            self.galil.sendOnly("SP" + self.galil.axis_az + "=" + str(speed_az))
            self.galil.sendOnly("SP" + self.galil.axis_el + "=" + str(speed_el))

            # set acceleration of axes
            accel = float(self.config.get("slew", "accel"))
            accel_az = self.converter.az_to_encoder( # adjust for altitude
                accel / (math.cos(math.radians(cur_pos[1])) + 0.01))
            accel_el = self.converter.el_to_encoder(accel)
            self.galil.sendOnly("AC" + self.galil.axis_az + "=" + str(accel_az))
            self.galil.sendOnly("AC" + self.galil.axis_el + "=" + str(accel_el))
            self.galil.sendOnly("DC" + self.galil.axis_az + "=" + str(accel_az))
            self.galil.sendOnly("DC" + self.galil.axis_el + "=" + str(accel_el))

            # do move
            self.galil.sendOnly("PR" + axis + "=" +
                str(sign * self.step_size[axis]))
            self.galil.sendOnly("BG " + axis)
        except AttributeError:
            print("Can't move! No step size entered!")
            print("To enter a step size, type a number of degrees in")
            print("the box near the arrows, and press enter.")
            traceback.print_exc()

    # slew to a solar system object
    def sso_goto (self, event):
        self.stop(event)

        # run slew to object in new thread
        self.scan_thread = threading.Thread(target=lambda:
            self.controller.track(self.planets.equ_pos(
                self.planets.get_obj(self.sso_input.GetValue()))))
        self.scan_thread.start()

        self.cur_center_input.SetSelection(0) # center on current position
        event.Skip()

    # set current position as position of solar system object
    def sso_sync (self, event):
        self.stop(event)

        # get coordinates
        hor_pos = self.planets.hor_pos(
            self.planets.get_obj(self.sso_input.GetValue()))
        self.controller.sync(hor_pos)
        event.Skip()

    # set scan position to position of solar system object
    def sso_scan (self, event):

        # get coordinates
        equ_pos = self.planets.equ_pos(
            self.planets.get_obj(self.sso_input.GetValue()))

        # set as center of equatorial scan
        self.center_crda_input.SetValue("{0:.4f}".format(equ_pos[0]))
        self.center_crdb_input.SetValue("{0:.4f}".format(equ_pos[1]))
        self.scan_coordsys.SetSelection(1) # set to equatorial

        # switch to scan tab
        self.controlNotebook.SetSelection(3)
        event.Skip()

    # get horizontal corodinates of an NGC or IC object
    def get_ngcic_pos (self, name):
        equ_pos = False
        for obj in self.sky_chart.ngcic:
            if obj[0] == name:
                equ_pos = obj[1] # -> position

        # not found
        if not equ_pos:
            self.logger.error("object does not exist: " + name)
            return

        return equ_pos

    # slew to an NGC/IC object
    def ngcic_goto (self, event):
        self.stop(event)

        # get coordinates
        equ_pos = self.get_ngcic_pos(self.ngcic_catalog.GetValue()
            + " " + str(self.ngcic_input.GetValue()))
        if not equ_pos:
            return # object not found

        # run slew to object in new thread
        self.scan_thread = threading.Thread(target=lambda:
            self.controller.track(equ_pos))
        self.scan_thread.start()

        self.cur_center_input.SetSelection(0) # center on current position
        event.Skip()

    # set current position as position of NGC/IC object
    def ngcic_sync (self, event):
        self.stop(event)

        # get coordinates
        equ_pos = self.get_ngcic_pos(self.ngcic_catalog.GetValue()
            + " " + str(self.ngcic_input.GetValue()))
        if not equ_pos:
            return # object not found

        # convert to horizontal
        az, el = self.converter.radec_to_azel(
            math.radians(equ_pos[0]), math.radians(equ_pos[1]))
        hor_pos = [math.degrees(az), math.degrees(el)]

        # sync to object position
        self.controller.sync(hor_pos)
        event.Skip()

    # set scan position to position of NGC/IC object
    def ngcic_scan (self, event):

        # get coordinates
        equ_pos = self.get_ngcic_pos(self.ngcic_catalog.GetValue()
            + " " + str(self.ngcic_input.GetValue()))
        if not equ_pos:
            return # object not found

        # set as center of equatorial scan
        self.center_crda_input.SetValue("{0:.4f}".format(equ_pos[0]))
        self.center_crdb_input.SetValue("{0:.4f}".format(equ_pos[1]))
        self.scan_coordsys.SetSelection(1) # set to equatorial

        # switch to scan tab
        self.controlNotebook.SetSelection(3)
        event.Skip()

    # show selected scan on sky chart
    def show_scan (self, scan_func):

        self.sky_chart.path, center = scan_func() # show path on chart
        self.sky_chart.given_equ = False

        # center sky chart in the middle of the scan region
        self.sky_chart.scan_center = center
        self.sky_chart.Refresh()

    # fetch scan function
    def get_scan (self):

        # user inputs
        center = [float(self.center_crda_input.GetValue()) % 360,
                  float(self.center_crdb_input.GetValue())]
        size = float(self.size_edge_input.GetValue())
        num_turns = int(self.num_turns_input.GetValue())
        scan_id = self.scan_type_input.GetSelection()

        # function to generate list of points
        if self.scan_coordsys.GetSelection() == 0: # horizontal
            def scan_func ():
                return scans.scan_list[scan_id](center, size, num_turns), \
                       center

        else: # equatorial
            def scan_func ():

                # convert center to horizontal coordinates
                az, el = self.converter.radec_to_azel(
                    math.radians(center[0]),
                    math.radians(center[1])
                )
                center_hor = [math.degrees(az), math.degrees(el)]

                # compute list
                return scans.scan_list[scan_id](center_hor, size, num_turns), \
                       center_hor

        return scan_func

    # show preview of scan
    def set_preview (self, event):
        self.scan_func = self.get_scan()
        self.show_scan(self.scan_func)
        self.cur_center_input.SetSelection(1) # center on scan
        self.change_cen(event)

    # scan button clicked
    def scan (self, event):

        self.set_preview(event)
        self.stop(event)

        # run scan in new thread
        self.scan_thread = threading.Thread(target=lambda:
            self.controller.scan(lambda: self.scan_func()[0],
                self.scan_repeat_input.GetValue() or
                    float(self.scan_cycles_input.GetValue())))

        self.scan_thread.start()
        event.Skip()

    # execute a horizontal graticule scan
    def horiz_scan (self, event):
        self.hg_preview(event)
        self.stop(event)

        self.scan_thread = threading.Thread(target=lambda:
            self.hg_scan.scan(
                float(self.left_azimuth_input.GetValue()),
                float(self.right_azimuth_input.GetValue()),
                float(self.low_altitude_input.GetValue()),
                float(self.high_altitude_input.GetValue()),
                int(self.hg_turns_input.GetValue()),
                float(self.hg_cycles_input.GetValue()) == 0.0 or
                    float(self.hg_cycles_input.GetValue())))
        self.scan_thread.start()
        event.Skip()

    # show preview of horizontal graticule scan
    def hg_preview (self, event):

        # determine the point in the center of the scan
        left_az = float(self.left_azimuth_input.GetValue()) % 360
        right_az = float(self.right_azimuth_input.GetValue()) % 360
        if left_az > right_az:
            left_az -= 360
        cen_az = 0.5 * (left_az + right_az)
        cen_el = 0.5 * (float(self.low_altitude_input.GetValue()) +
                        float(self.high_altitude_input.GetValue()))

        self.sky_chart.scan_center = [cen_az, cen_el]

        def scan_func ():
            return self.hg_scan.points(
                float(self.left_azimuth_input.GetValue()),
                float(self.right_azimuth_input.GetValue()),
                float(self.low_altitude_input.GetValue()),
                float(self.high_altitude_input.GetValue()),
                int(self.hg_turns_input.GetValue())), \
                self.sky_chart.scan_center

        self.scan_func = scan_func
        self.sky_chart.path = scan_func()

        self.sky_chart.given_equ = False

        self.cur_center_input.SetSelection(1) # center on scan
        self.change_cen(event)
        self.sky_chart.Refresh()

    # execute a zenith spiral scan
    def circular_scan (self, event):
        self.cc_preview(event)
        self.stop(event)

        self.scan_thread = threading.Thread(target=lambda:
            self.cc_scan.scan(
                [float(self.cc_azimuth_input.GetValue()),
                 float(self.cc_altitude_input.GetValue())],
                 float(self.cc_ccw_input.GetValue()),
                 float(self.cc_cycles_input.GetValue()) == 0.0 or
                    float(self.cc_cycles_input.GetValue())))
        self.scan_thread.start()
        event.Skip()

    # show preview of zenith spiral scan
    def cc_preview (self, event):

        # center circular scan at the starting point
        self.sky_chart.scan_center = \
            [float(self.cc_azimuth_input.GetValue()),
             float(self.cc_altitude_input.GetValue())]

        def scan_func ():
            return self.cc_scan.points(
                [float(self.cc_azimuth_input.GetValue()),
                 float(self.cc_altitude_input.GetValue())]), \
                self.sky_chart.scan_center

        self.scan_func = scan_func
        self.sky_chart.path, self.sky_chart.scan_center = scan_func()
        self.sky_chart.given_equ = False

        self.cur_center_input.SetSelection(1) # center on scan
        self.change_cen(event)
        self.sky_chart.Refresh()

    # change the coordinate system of the chart
    def change_cs (self, event):
        self.sky_chart.show_equ = bool(self.chart_crdsys.GetSelection())
        self.sky_chart.Refresh()

    # spin control for chart field of view changed
    def change_fov (self, event):
        self.sky_chart.h_fov = float(self.chart_fov.GetValue())
        self.sky_chart.Refresh()
        event.Skip()

    # change the center of the sky chart
    def change_cen (self, event):

        # center on current position if needed
        self.sky_chart.cen_curscan = bool(self.cur_center_input.GetSelection())
        self.sky_chart.Refresh()

        event.Skip()

    # change the scan coordinate system
    def change_scan_crd (self, event):

        # set coordinate labels to equatorial
        if self.scan_coordsys.GetSelection() == 1:
            self.center_crda_label.SetLabel("Right Asc: ")
            self.center_crdb_label.SetLabel("Declination: ")

        else: # set to horizontal
            self.center_crda_label.SetLabel("Azimuth: ")
            self.center_crdb_label.SetLabel("Altitude: ")

    # copy config & controller objects to all scans
    def copy_config (self):
        self.converter.c = self.config
        self.controller.config = self.config

        self.sky_chart.converter = self.converter
        self.controller.converter = self.converter

        self.hg_scan.controller = self.controller
        self.cc_scan.controller = self.controller

    # write configuration file and update all copies of the configuration
    def write_config (self):
        self.copy_config()

        with open("config.ini", "w") as configfile:
            self.config.write(configfile)

    # change slew speed
    def change_speed (self, event):
        try:
            speed = float(self.scan_speed_input.GetValue())
        except ValueError:
            speed = 10.0
        self.config.set("slew", "speed", str(speed))
        self.write_config()
        event.Skip()

    # change the acceleration
    def change_accel (self, event):
        try:
            accel = float(self.scan_accel_input.GetValue())
        except ValueError:
            accel = 10.0
        self.config.set("slew", "accel", str(accel))
        self.write_config()
        event.Skip()

    # change observer longitude
    def change_lon (self, event):
        try:
            lon = float(self.obs_lon_input.GetValue())
        except ValueError:
            lon = 0.0
        self.config.set("location", "lon", str(lon))
        self.write_config()
        event.Skip()

    # change observer latitude
    def change_lat (self, event):
        try:
            lat = float(self.obs_lat_input.GetValue())
        except ValueError:
            lat = 0.0
        self.config.set("location", "lat", str(lat))
        self.write_config()
        event.Skip()

    # change usage of GPS time
    def change_gps_usage (self, event):
        self.config.set("time", "use_gps", str(self.gps_time_input.GetValue()))
        self.write_config()
        event.Skip()

    # any of the limit settings changed
    def change_lim (self, event):
        try:
            az_lim = bool(self.az_limit_input.GetValue())
            az_min = float(self.az_min_input.GetValue())
            az_max = float(self.az_max_input.GetValue())
            el_lim = bool(self.el_limit_input.GetValue())
            el_min = float(self.el_min_input.GetValue())
            el_max = float(self.el_max_input.GetValue())
        except:
            return # TODO: show that limits are not valid

        self.config.set("limits", "az_check", str(az_lim))
        self.config.set("limits", "az_min", str(az_min))
        self.config.set("limits", "az_max", str(az_max))
        self.config.set("limits", "el_check", str(el_lim))
        self.config.set("limits", "el_min", str(el_min))
        self.config.set("limits", "el_max", str(el_max))
        self.write_config()

    def update_display (self, event):

        # update sky chart
        self.sky_chart.curpos_h = self.controller.current_pos()
        if hasattr(self, "scan_func"):
            self.sky_chart.path, self.sky_chart.scan_center = self.scan_func()
        self.sky_chart.Refresh()

        if not self.galil:  # Short circuit in test-mode
            return

        # constrain to range
        self.controller.constrain()

        raw_data = list(self.galil.pos)
        data = [raw_data[string.uppercase.index(self.galil.axis_az)],
                raw_data[string.uppercase.index(self.galil.axis_el)]]

        az = math.degrees(ephem.degrees(self.converter.encoder_to_az(data[0])))
        el = math.degrees(ephem.degrees(self.converter.encoder_to_el(data[1])))

        ra, dec = self.converter.azel_to_radec(az, el)

        if self.config.get("time", "use_gps") == "True":
            dt = (self.galil.gpsDelTime) * 0.001 \
                - int(self.config.get("time", "leap_sec"))

        else: # no GPS device, use system time
            dt = 0.0

        data = [(self.az_status, "", ephem.degrees(str(az % 360.0))),
                (self.el_status, "", ephem.degrees(str(el))),

                (self.az_raw_status, "", data[0]),
                (self.el_raw_status, "", data[1]),

                (self.ra_status, "", ra),
                (self.dec_status, "", dec),
                (self.local_status, "", self.converter.lct(dt)),
                (self.utc_status, "", self.converter.utc(dt)),
                (self.gps_status, "",
                 self.config.get("time", "use_gps") == "True" and \
                    (self.galil.haveLock and "Locked" or "Not Locked")
                    or "Off")]

        for widget, prefix, datum in data:
            widget.SetLabel(prefix + str(datum))

        if self.galil.udpPackets:
            self.packet_num.SetLabel("Received Galil\nData-Records: %d" % self.galil.udpPackets)

        # azimuth motor
        if self.galil.motOn[string.uppercase.index(self.galil.axis_az)]:
            self.azMotorPowerStateLabel.SetLabel("Motor On")
        else:
            self.azMotorPowerStateLabel.SetLabel("Motor Off")

        # altitude motor
        if self.galil.motOn[string.uppercase.index(self.galil.axis_el)]:
            self.elMotorPowerStateLabel.SetLabel("Motor On")
        else:
            self.elMotorPowerStateLabel.SetLabel("Motor Off")

        event.Skip()
        return

def main():		# Shut up pylinter

    galilInterface = globalConf.gInt

    print("Launching app...")
    app = wx.App()

    mainFrame = MainWindow(galilInterface, None, -1, "")
    app.SetTopWindow(mainFrame)
    mainFrame.Show()

    print("Entering main loop...")
    app.MainLoop()

    # close galil interface on exit
    galilInterface.close()

if __name__ == "__main__":
    main()
