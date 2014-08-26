import logging
import math
import sys
import time
import traceback
import wx

import config
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
    def __init__(self, galilInterface, converter, conf, *args, **kwargs):
        gui.TelescopeControlFrame.__init__(self, converter, *args, **kwargs)
        self.poll_update = wx.Timer(self)
        self.galil = galilInterface
        self.config = conf
        self.scan_thread = None
        self.scan_thread_stop = None
        self.step_size = 0
        
        # center of previously selected scan
        self.scan_center = [0, 0]
        self.scan_equ = False
        
        # set logging output
        self.logger = logging.getLogger()
        debug = logging.StreamHandler(sys.stdout)
        debug.setFormatter(logging.Formatter('%(message)s'))
        debug.setLevel(logging.DEBUG)
        self.logger.addHandler(debug)
        self.logger.setLevel(logging.DEBUG)
        
        # standard scan
        self.controller = controller.Controller(self.logger,
            self.galil, self.converter)
        # simple scans
        self.hg_scan = graticule.Scan(self.logger, self.galil, self.converter)
        self.zs_scan = zspiral.Scan(self.logger, self.galil, self.converter)
        
        # positions of solar system objects
        self.planets = planets.Planets(self.logger, self.converter)

        #wx.EVT_TIMER(self, self.poll_update.GetId(), self.update_display)
        self.bind_events()
        self.Bind(wx.EVT_TIMER, self.update_display, self.poll_update)
        print "Starting Display Update Poll"
        self.poll_update.Start(35)
        print ''

        print "Make sure to turn on the motors you will use!"
        print "Motors are automatically turned off when you exit."
        print ''

    def bind_events(self):
        # By putting the event bindings here, it means I can clear out the event handlers from the parent class (gui.py)
        # without breaking it
        self.Bind(wx.EVT_BUTTON, self.stop, self.button_stop_all)
        self.Bind(wx.EVT_BUTTON, self.stop, self.button_stop_az)
        self.Bind(wx.EVT_BUTTON, self.toggle_motor_state, self.buttton_az_motor)
        self.Bind(wx.EVT_BUTTON, self.stop, self.button_stop_el)
        self.Bind(wx.EVT_BUTTON, self.toggle_motor_state, self.button_el_motor)
        self.Bind(wx.EVT_TEXT_ENTER, self.set_step_size, self.step_size_input)
        
        self.Bind(wx.EVT_BUTTON, self.move_rel, self.button_up)
        self.Bind(wx.EVT_BUTTON, self.move_rel, self.button_left)
        self.Bind(wx.EVT_BUTTON, self.move_rel, self.button_right)
        self.Bind(wx.EVT_BUTTON, self.move_rel, self.button_down)
        self.Bind(wx.EVT_BUTTON, self.move_abs, self.button_start_move)
        
        self.Bind(wx.EVT_BUTTON, self.goto, self.buttonGotoPosition)
        self.Bind(wx.EVT_BUTTON, self.calibrate, self.buttonDoRaDecCalibrate)
        self.Bind(wx.EVT_BUTTON, self.track_radec, self.buttonTrackPosition)
        
        self.Bind(wx.EVT_BUTTON, self.sso_goto, self.sso_goto_input)
        self.Bind(wx.EVT_BUTTON, self.sso_sync, self.sso_sync_input)
        
        self.Bind(wx.EVT_BUTTON, self.scan, self.buttonScanStart)
        self.Bind(wx.EVT_BUTTON, self.set_preview, self.preview_scan)
        
        self.Bind(wx.EVT_BUTTON, self.horiz_scan, self.hg_begin_input)
        self.Bind(wx.EVT_BUTTON, self.hg_preview, self.hg_preview_input)
        self.Bind(wx.EVT_BUTTON, self.zenith_scan, self.zs_begin_input)
        self.Bind(wx.EVT_BUTTON, self.zs_preview, self.zs_preview_input)
        
        self.Bind(wx.EVT_COMBOBOX, self.change_cs, self.chart_crdsys)
        self.Bind(wx.EVT_SPINCTRL, self.change_fov, self.chart_fov)
        self.Bind(wx.EVT_COMBOBOX, self.change_cen, self.cur_center_input)
        

    def move_abs(self, event):
        azPos = float(self.absolute_move_ctrl_az.GetValue())
        elPos = float(self.absolute_move_ctrl_el.GetValue())
        azVal = self.converter.az_to_encoder(azPos)
        elVal = self.converter.el_to_encoder(elPos)

        self.galil.moveAbsolute(0, azVal)
        self.galil.moveAbsolute(1, elVal)

        self.galil.beginMotion()

    def goto(self, event):
        print "Event goto not implemented!"

    def calibrate(self, event):
        print "Event calibrate not implemented!"

    def track_radec(self, event):
        print "Event track_radec not implemented!"


    def stop(self, event):
        """This function is called whenever one of the stop
        buttons is pressed."""
        if self.controller.stop:
            self.controller.stop.set()
        if self.zspiral.stop:
            self.zspiral.stop.set()
        stops = [(self.button_stop_all, None),
                (self.button_stop_az, 0),
                (self.button_stop_el, 1)]
        for stop, axis in stops:
            if event.GetId() == stop.GetId():
                print "Stopping motor for axis {}".format("ALL" if axis is None else axis)
                self.galil.endMotion(axis)
                break
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
            print "Turning off motor for axis {}.".format(axis)
            self.galil.motorOff(axis)
        else:
            print "Turning on motor for axis {}.".format(axis)
            self.galil.motorOn(axis)
        print ''
        event.Skip()

    def set_step_size(self, event):
        """This is called after you type a number nad press enter
        on the step size box next to the arrow buttons."""
        value = self.step_size_input.GetValue()
        try:
            value = float(value)
        except:
            raise ValueError("You need to enter a step-size first!")
        if math.isnan(value):
            raise ValueError("NaN is not a valid step size. Nice try, though.")

        degrees = value
        self.step_size = [self.converter.az_to_encoder(degrees),
                        self.converter.el_to_encoder(degrees)]
        print "Setting joystick step size to {} degrees, {} encoder counts.".format(degrees, self.step_size[0])
        # print "\t{} encoder counts in the AZ direction".format(self.step_size[0])
        # print "\t{} encoder counts in the EL direction".format(self.step_size[1])
        # print ''
        

    def move_rel(self, event):
        self.set_step_size(None)  # Force the GUI to read the input, so the user doesn't have to hit enter.

        # This is caled when you click one of the arrow buttons

        b_s_a = [(self.button_up, 1, 1),
                (self.button_down, -1, 1),
                (self.button_right, 1, 0),
                (self.button_left, -1, 0)]

        for button, sign, axis in b_s_a:
            if event.GetId() == button.GetId():
                try:
                    print "Starting move of {} steps on axis {}.".format(sign*self.step_size[axis], axis)
                    self.galil.moveRelative(axis, sign*self.step_size[axis])
                except AttributeError:
                    print "Can't move! No step size entered!"
                    print "To enter a step size, type a number of degrees in"
                    print "the box near the arrows, and press enter."
                    traceback.print_exc()
                except Exception, error:
                    print error
                else:
                    self.galil.beginMotion(axis)
                break
        #print ''
        return

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
        self.scan_equ = \
            (self.coordsys_selector.GetSelection() == 1)
        self.sky_chart.given_equ = self.scan_equ
        
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
            
            self.scan_center = [crd_a, crd_b]
            self.sky_chart.center = self.scan_center[:]
            self.sky_chart.Refresh()
            
        return points

    # slew to a solar system object
    def sso_goto (self, event):
        
        # run slew to object in new thread
        self.scan_thread = threading.Thread(target=lambda:
            self.controller.goto(self.planets.hor_pos(
                self.planets.get_obj(self.sso_input.GetValue())),
                float(self.scan_speed_input.GetValue()),
                float(self.scan_accel_input.GetValue())))
        self.scan_thread.start()
        
        self.cur_center_input.SetSelection(0) # center on current position
        event.Skip()
    
    # set current position as position of solar system object
    def sso_sync (self, event):
        event.Skip()
    
    
    # scan button clicked
    def scan (self, event):
        points = self.show_scan()
        
        # run scan in new thread
        self.scan_thread = threading.Thread(target=lambda:
            self.controller.scan(points,
                self.coordsys_selector.GetSelection() == 0 and
                self.controller.process_hor or self.controller.process_equ,
                float(self.scan_speed_input.GetValue()),
                float(self.scan_accel_input.GetValue()),
                self.scan_repeat_input.GetValue() and 1 or
                    float(self.scan_cycles_input.GetValue())))
                    
        self.scan_thread.start()
        event.Skip()
    
    # show preview of scan
    def set_preview (self, event):
        self.show_scan()
        self.cur_center_input.SetSelection(1) # center on scan
        event.Skip()
    
    # execute a horizontal graticule scan
    def horiz_scan (self, event):
        self.hg_preview(event)
        
        self.scan_thread = threading.Thread(target=lambda:
            self.hg_scan.scan(
                float(self.left_azimuth_input.GetValue()),
                float(self.right_azimuth_input.GetValue()),
                float(self.low_altitude_input.GetValue()),
                float(self.high_altitude_input.GetValue()),
                int(self.hg_turns_input.GetValue()),
                float(self.scan_speed_input.GetValue()),
                float(self.scan_accel_input.GetValue()),
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
        self.scan_equ = False
        
        # determine the point in the center of the scan
        left_az = float(self.left_azimuth_input.GetValue()) % 360
        right_az = float(self.right_azimuth_input.GetValue()) % 360
        if left_az > right_az:
            left_az -= 360
        cen_az = 0.5 * (left_az + right_az)
        cen_el = 0.5 * (float(self.low_altitude_input.GetValue()) +
                        float(self.high_altitude_input.GetValue()))
        
        self.scan_center = [cen_az, cen_el]
        self.sky_chart.center = self.scan_center[:]
        
        self.cur_center_input.SetSelection(1) # center on scan
        self.sky_chart.Refresh()
        
    # execute a zenith spiral scan
    def zenith_scan (self, event):
        self.zs_preview(event)
        
        self.scan_thread = threading.Thread(target=lambda:
            self.zs_scan.scan(
                [float(self.zst_azimuth_input.GetValue()),
                 float(self.zst_altitude_input.GetValue())],
                float(self.zs_inc_input.GetValue()),
                float(self.scan_speed_input.GetValue()),
                float(self.scan_accel_input.GetValue()),
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
        
        self.scan_equ = False
        self.sky_chart.given_equ = False
        self.scan_center = \
            [float(self.zst_azimuth_input.GetValue()),
             0.5 * (float(self.zst_altitude_input.GetValue()) + 90)]
        self.sky_chart.center = self.scan_center[:]
        
        self.cur_center_input.SetSelection(1) # center on scan
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
        
        # center on current position
        if self.cur_center_input.GetSelection() == 0:
            self.sky_chart.center = self.controller.current_pos()
            self.sky_chart.given_equ = False
        
        # center of current scan
        elif self.cur_center_input.GetSelection() == 1:
            self.sky_chart.center = self.scan_center[:]
            self.sky_chart.given_equ = self.scan_equ
        
        self.sky_chart.Refresh()
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

        # print "motOn", self.galil.motOn
        # print "inMot", self.galil.inMot

        event.Skip()
        return

def main():		# Shut up pylinter
    print "Reading configuration file..."
    conf = config.Config("config.txt") #make the config object...
    galilInterface = globalConf.gInt
    
    print "Setting up converter..."
    converter = units.Units(conf) #...and the converter...
    
    print "Launching app..."
    app = wx.App()
    
    print "Building UI..."
    mainFrame = MainWindow(galilInterface, converter, conf, None, -1, "")
    app.SetTopWindow(mainFrame)
    mainFrame.Show()
    
    print "Entering main loop..."
    app.MainLoop()

    # close galil interface on exit
    galilInterface.close()

if __name__ == "__main__":
    main()
