try:
    import configparser
except:
    import ConfigParser as configparser

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

import graticule
import zspiral

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
        
        self.poll_update = wx.Timer(self)
        self.scan_thread = None
        self.step_size = 0
        
        print("Setting up scanning...")
        # standard scan
        self.controller = controller.Controller(self.logger,
            self.galil, self.converter, self.config)
        # simple scans
        self.hg_scan = graticule.Scan(self.logger,
            self.galil, self.converter, self.config)
        self.zs_scan = zspiral.Scan(self.logger,
            self.galil, self.converter, self.config)

        #wx.EVT_TIMER(self, self.poll_update.GetId(), self.update_display)
        print("Setting up event handlers...")
        self.bind_events()
        self.Bind(wx.EVT_TIMER, self.update_display, self.poll_update)
        print("Starting display update poll...")
        self.poll_update.Start(100)
        print('')

        print("Make sure to turn on the motors you will use!")
        print("Motors are automatically turned off when you exit.")
        print('')

    def bind_events(self):
        # By putting the event bindings here, it means I can clear out the event handlers from the parent class (gui.py)
        # without breaking it
        self.Bind(wx.EVT_CLOSE, self.stop)
        
        self.Bind(wx.EVT_BUTTON, self.stop, self.button_stop_all)
        self.Bind(wx.EVT_BUTTON, self.stop, self.button_stop_az)
        self.Bind(wx.EVT_BUTTON, self.toggle_motor_state, self.buttton_az_motor)
        self.Bind(wx.EVT_BUTTON, self.stop, self.button_stop_el)
        self.Bind(wx.EVT_BUTTON, self.toggle_motor_state, self.button_el_motor)
        self.Bind(wx.EVT_TEXT, self.set_step_size, self.step_size_input)
        
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
        self.Bind(wx.EVT_BUTTON, self.ngcic_goto, self.ngcic_goto_input)
        self.Bind(wx.EVT_BUTTON, self.ngcic_sync, self.ngcic_sync_input)
        
        self.Bind(wx.EVT_BUTTON, self.scan, self.buttonScanStart)
        self.Bind(wx.EVT_BUTTON, self.set_preview, self.preview_scan)
        
        self.Bind(wx.EVT_BUTTON, self.horiz_scan, self.hg_begin_input)
        self.Bind(wx.EVT_BUTTON, self.hg_preview, self.hg_preview_input)
        self.Bind(wx.EVT_BUTTON, self.zenith_scan, self.zs_begin_input)
        self.Bind(wx.EVT_BUTTON, self.zs_preview, self.zs_preview_input)
        
        self.Bind(wx.EVT_COMBOBOX, self.change_cs, self.chart_crdsys)
        self.Bind(wx.EVT_SPINCTRL, self.change_fov, self.chart_fov)
        self.Bind(wx.EVT_COMBOBOX, self.change_cen, self.cur_center_input)
        
        self.Bind(wx.EVT_TEXT, self.change_speed, self.scan_speed_input)
        self.Bind(wx.EVT_TEXT, self.change_accel, self.scan_accel_input)
        self.Bind(wx.EVT_TEXT, self.change_lon, self.obs_lon_input)
        self.Bind(wx.EVT_TEXT, self.change_lat, self.obs_lat_input)
        

    def goto_hor (self, event):
        azPos = float(self.goto_az_input.GetValue())
        elPos = float(self.goto_el_input.GetValue())
        azVal = self.converter.az_to_encoder(azPos)
        elVal = self.converter.el_to_encoder(elPos)

        self.galil.sendOnly("PA" + self.galil.axis_az + "=" + str(azVal))
        self.galil.sendOnly("PA" + self.galil.axis_el + "=" + str(elVal))
        self.galil.sendOnly("BG")
        
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

    def stop(self, event):
        """This function is called whenever one of the stop
        buttons is pressed."""
        if hasattr(self.controller, "stop"):
            self.controller.stop.set()
        if hasattr(self.hg_scan, "stop"):
            self.hg_scan.stop.set()
        if hasattr(self.zs_scan, "stop"):
            self.zs_scan.stop.set()
        stops = [(self.button_stop_all, None),
                (self.button_stop_az, 0),
                (self.button_stop_el, 1)]
        for stop, axis in stops:
            if event.GetId() == stop.GetId():
                print("Stopping motor for axis {}".format("ALL" if axis is None else axis))
                self.galil.endMotion(axis)
                break
        time.sleep(1.01) # provide enough time for any scan loops to exit
        event.Skip()

    def toggle_motor_state(self, event):
        """This function is called whenever you toggle the
        motor on/motor off buttons. I think it would be nifty
        to add something to change the size/color/font of the 
        button text here. It would help alot."""
        axis = 0
        if event.GetId() == self.button_el_motor.GetId():
            axis = 1
        if self.galil.checkMotorPower(axis):
            print("Turning off motor for axis {}.".format(axis))
            self.galil.motorOff(axis)
        else:
            print("Turning on motor for axis {}.".format(axis))
            self.galil.motorOn(axis)
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
        

    def move_rel(self, event):
        self.set_step_size(None)  # read step size

        # This is caled when you click one of the arrow buttons

        b_s_a = [(self.button_up, 1, self.galil.axis_el),
                (self.button_down, -1, self.galil.axis_el),
                (self.button_right, 1, self.galil.axis_az),
                (self.button_left, -1, self.galil.axis_az)]

        for button, sign, axis in b_s_a:
            if event.GetId() == button.GetId():
                try:
                    self.logger.info("moving {} degrees on axis {}.".format(
                        sign * self.step_deg, axis))
                    self.galil.sendOnly("PR" + axis + "=" +
                        str(sign * self.step_size[axis]))
                except AttributeError:
                    print("Can't move! No step size entered!")
                    print("To enter a step size, type a number of degrees in")
                    print("the box near the arrows, and press enter.")
                    traceback.print_exc()
                else:
                    self.galil.sendOnly("BG " + axis)
                break
        return
    
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

    # show selected scan on sky chart
    def show_scan (self):
        
        # load some settings
        pt1 = [float(self.corner1_crda_box.GetValue()) % 360,
               float(self.corner1_crdb_box.GetValue())]
        pt2 = [float(self.corner2_crda_box.GetValue()) % 360,
               float(self.corner2_crdb_box.GetValue())]
        pt3 = [float(self.corner3_crda_box.GetValue()) % 360,
               float(self.corner3_crdb_box.GetValue())]
        pt4 = [float(self.corner4_crda_box.GetValue()) % 360,
               float(self.corner4_crdb_box.GetValue())]
        
        num_turns = int(self.num_turns_input.GetValue())
        scan_id = self.comboBoxScanOptions.GetSelection()
        
        # compute a list of points to scan to and update sky chart
        points = scans.scan_list[scan_id](pt1, pt2, pt3, pt4, num_turns)
        self.sky_chart.path = points[:] # show path on chart
        self.sky_chart.given_equ = (self.coordsys_selector.GetSelection() == 1)
        
        # center sky chart in the middle of the scan region
        if len(points) > 0:
            
            # trig functions in degrees
            def cos (x):
                return math.cos(math.radians(x))
            def sin (x):
                return math.sin(math.radians(x))
            def atan2 (y, x):
                return math.degrees(math.atan2(y, x))
            
            # convert the corner points to rectangular vectors and sum
            x = cos(pt1[0])*cos(pt1[1]) + cos(pt2[0])*cos(pt2[1]) + \
                cos(pt3[0])*cos(pt3[1]) + cos(pt4[0])*cos(pt4[1])
            y = sin(pt1[0])*cos(pt1[1]) + sin(pt2[0])*cos(pt2[1]) + \
                sin(pt3[0])*cos(pt3[1]) + sin(pt4[0])*cos(pt4[1])
            z = sin(pt1[1]) + sin(pt2[1]) + sin(pt3[1]) + sin(pt4[1])
            
            # convert the resulting vector into spherical coordinates
            crd_a = atan2(y, x)
            crd_b = atan2(z, math.sqrt(x*x + y*y))
            
            self.sky_chart.scan_center = [crd_a, crd_b]
            self.sky_chart.Refresh()
            
        return points
    
    # show preview of scan
    def set_preview (self, event):
        points = self.show_scan()
        self.cur_center_input.SetSelection(1) # center on scan
        self.change_cen(event)
        
        return points
    
    # scan button clicked
    def scan (self, event):
        points = self.set_preview(event)
        self.stop(event)
        
        # run scan in new thread
        self.scan_thread = threading.Thread(target=lambda:
            self.controller.scan(points,
                self.coordsys_selector.GetSelection() == 0 and
                    self.controller.process_hor or self.controller.process_equ,
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
        self.sky_chart.path = self.hg_scan.points(
            float(self.left_azimuth_input.GetValue()),
            float(self.right_azimuth_input.GetValue()),
            float(self.low_altitude_input.GetValue()),
            float(self.high_altitude_input.GetValue()),
            int(self.hg_turns_input.GetValue()))
        
        self.sky_chart.given_equ = False
        
        # determine the point in the center of the scan
        left_az = float(self.left_azimuth_input.GetValue()) % 360
        right_az = float(self.right_azimuth_input.GetValue()) % 360
        if left_az > right_az:
            left_az -= 360
        cen_az = 0.5 * (left_az + right_az)
        cen_el = 0.5 * (float(self.low_altitude_input.GetValue()) +
                        float(self.high_altitude_input.GetValue()))
        
        self.sky_chart.scan_center = [cen_az, cen_el]
        
        self.cur_center_input.SetSelection(1) # center on scan
        self.change_cen(event)
        self.sky_chart.Refresh()
        
    # execute a zenith spiral scan
    def zenith_scan (self, event):
        self.zs_preview(event)
        self.stop(event)
        
        self.scan_thread = threading.Thread(target=lambda:
            self.zs_scan.scan(
                [float(self.zst_azimuth_input.GetValue()),
                 float(self.zst_altitude_input.GetValue())],
                float(self.zs_inc_input.GetValue()),
                float(self.zs_cycles_input.GetValue()) == 0.0 or
                    float(self.zs_cycles_input.GetValue())))
        self.scan_thread.start()
        event.Skip()
    
    # show preview of zenith spiral scan
    def zs_preview (self, event):
        self.sky_chart.path = self.zs_scan.points(
            [float(self.zst_azimuth_input.GetValue()),
             float(self.zst_altitude_input.GetValue())],
            float(self.zs_inc_input.GetValue()))
        
        self.sky_chart.given_equ = False
        self.sky_chart.scan_center = \
            [float(self.zst_azimuth_input.GetValue()),
             0.5 * (float(self.zst_altitude_input.GetValue()) + 90)]
        
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
    
    # write configuration file and update all copies of the configuration
    def write_config (self):
        self.converter.c = self.config
        self.sky_chart.converter = self.converter
        
        self.controller.config = self.config
        self.controller.converter = self.converter
        self.hg_scan.config = self.config
        self.hg_scan.converter = self.converter
        self.zs_scan.config = self.config
        self.zs_scan.converter = self.converter
        
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
    
    def update_display (self, event):
        
        # update sky chart
        self.sky_chart.curpos_h = self.controller.current_pos()
        self.sky_chart.Refresh()
        
        if not self.galil:  # Short circuit in test-mode
            return

        data = list(self.galil.pos)
        
        az = self.converter.encoder_to_az(data[0])
        el = self.converter.encoder_to_el(data[1])

        ra, dec = self.converter.azel_to_radec(az, el)

        data = [(self.az_status,     "",     az                   ),
                (self.el_status,     "",     el                   ),

                (self.az_raw_status, "", data[0]              ),
                (self.el_raw_status, "", data[1]              ),
                
                (self.ra_status,     "",     ra                   ),
                (self.dec_status,    "",    dec                  ),
                (self.local_status,  "",  self.converter.lct() ),
                (self.lst_status,    "",    self.converter.lst() ),
                (self.utc_status,    "",    self.converter.utc() )]


        for widget, prefix, datum in data:
            widget.SetLabel(prefix + str(datum))


        if self.galil.udpPackets:
            self.packet_num.SetLabel("Received Galil\nData-Records: %d" % self.galil.udpPackets)

        motStateLabels = [self.azMotorPowerStateLabel, self.elMotorPowerStateLabel]
        for x in range(2):
            if self.galil.motOn[x]:
                motStateLabels[x].SetLabel("Motor On")
            else:
                motStateLabels[x].SetLabel("Motor Off")

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
