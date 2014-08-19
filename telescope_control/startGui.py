
import gui
import globalConf
import config
import units
import controller
import scans

import logging
import math
import sys
import time
import wx

import traceback

# WHRYYYYYYYYYYYYYYYYYY (Connor)
#This is just to aid in some nonsensical
#programming I have in here. I Lol'd!
def map_(array, func_list):
    """WARNING! This breaks if your func_list is over 1000
    functions long! :p"""
    if len(func_list) == 0:
        return array
    fList = func_list[0]
    ret = map_([fList(x) for x in array], func_list[1:])
    print ret
    return ret


class MainWindow(gui.TelescopeControlFrame):
    def __init__(self, galilInterface, converter, conf, *args, **kwargs):
        gui.TelescopeControlFrame.__init__(self, *args, **kwargs)
        self.poll_update = wx.Timer(self)
        self.galil = galilInterface
        self.converter = converter
        self.config = conf
        self.scan_thread = None
        self.scan_thread_stop = None
        self.step_size = 0
        
        # set logging output
        self.logger = logging.getLogger()
        debug = logging.StreamHandler(sys.stdout)
        debug.setFormatter(logging.Formatter('%(message)s'))
        debug.setLevel(logging.DEBUG)
        self.logger.addHandler(debug)
        self.logger.setLevel(logging.DEBUG)
        
        self.controller = controller.Controller(self.logger,
            self.galil, self.converter, self.config)

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
        self.Bind(wx.EVT_BUTTON, self.scan, self.buttonScanStart)

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
    
    def scan(self, event):
        
        #This is the function that gets called when
        #you press the scan button.
        from threading import Thread, Event
        
        # load some settings
        speed = 4 # angular speed in deg/s
        crd1a = self.textCtrlScanMinAz.GetValue()
        crd1b = self.textCtrlScanMinEl.GetValue()
        crd2a = self.textCtrlScanMaxAz.GetValue()
        crd2b = self.textCtrlScanMaxEl.GetValue()
        num_turns = 10
        
        scan_id = self.comboBoxScanOptions.GetSelection()
        
        self.scan_thread = Thread(target=lambda:
            self.controller.scan(scans.scan_list[scan_id](crd1a, crd1b, crd2a, crd2b, num_turns),
                self.coordsys_selector.GetSelection() == 0 and
                self.controller.process_hor or self.controller.process_equ,
                float(self.scan_speed_input.GetValue()),
                self.scan_continuous_input.GetValue() and 1 or float(self.scan_cycles_input.GetValue())))
                    
        self.scan_thread.start()
        event.Skip()

    def update_display(self, event):
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
    conf = config.Config("config.txt") #make the config object...
    galilInterface = globalConf.gInt
    converter = units.Units(conf) #...and the converter...
    app = wx.App()
    #...and pass them to your MainWindow class!!!
    mainFrame = MainWindow(galilInterface, converter, conf, None, -1, "")
    app.SetTopWindow(mainFrame)
    mainFrame.Show()
    app.MainLoop()

    # close galil interface on exit
    galilInterface.close()

if __name__ == "__main__":
    main()
