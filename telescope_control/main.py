from gui import MyFrame
from galil import Galil
from config import Config
from units import Units
import time, wx

#This is just to aid in some nonsensical
#programming I have in here. I Lol'd!
def map_(array, func_list):
    """WARNING! This breaks if your func_list is over 1000
    functions long! :p"""
    if len(func_list) == 0:
        return array
    f = func_list[0]
    return map_([f(x) for x in array], func_list[1:])

class MainWindow(MyFrame):
    def __init__(self, galil, converter, config, *args, **kwargs):
        MyFrame.__init__(self, *args, **kwargs)
        self.poll_update = wx.Timer(self)
        self.galil = galil
        self.converter = converter
        self.config = config
        self.scan_thread = None
        self.scan_thread_stop = None

        #wx.EVT_TIMER(self, self.poll_update.GetId(), self.update_display)
        self.Bind(wx.EVT_TIMER, self.update_display, self.poll_update)
        print "Starting Display Update Poll"
        self.poll_update.Start(35)
        print ''

        print "Make sure to turn on the motors you will use!"
        print "Motors are automatically turned off when you exit."
        print ''

    def stop(self, event):
        """This function is called whenever one of the stop
        buttons is pressed."""
        if self.scan_thread_stop:
            self.scan_thread_stop.set()
        stops = [(self.button_stop_all, None),
                 (self.button_stop_az, 0),
                 (self.button_stop_el, 1)]
        for stop, axis in stops:
            if event.GetId() == stop.GetId():
                print "Stopping motor for axis {}".format("ALL" if axis is None else chr(65+axis))
                self.galil.end_motion(axis)
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
        if self.galil.is_motor_on(axis):
            print "Turning off motor for axis {}.".format(chr(65+axis))
            self.galil.motor_off(axis)
        else:
            print "Turning on motor for axis {}.".format(chr(65+axis))
            self.galil.motor_on(axis)
        print ''
        event.Skip()

    def set_step_size(self, event):
        """This is called after you type a number nad press enter
        on the step size box next to the arrow buttons."""
        degrees = float(self.step_size_input.GetValue())
        print "Setting joystick step size to {} degrees.".format(degrees)
        self.step_size = [self.converter.az_to_encoder(degrees),
                          self.converter.el_to_encoder(degrees)]
        print "\t{} encoder counts in the AZ direction".format(self.step_size[0])
        print "\t{} encoder counts in the EL direction".format(self.step_size[1])
        print ''
        event.Skip()

    def move_rel(self, event):
        """This is caled when you click one of the arrow buttons"""
        b_s_a = [(self.button_up, 1, 1),
                 (self.button_down, -1, 1),
                 (self.button_right, 1, 0),
                 (self.button_left, -1, 0)]
        for button, sign, axis in b_c_a:
            if event.GetId()==button.GetId():
                try:
                    print "Starting move of {} steps on axis {}.".format(sign*self.step_size[axis], chr(65+axis))
                    print self.galil.move_steps(axis, sign*self.step_size[axis])
                except AttributeError:
                    print "Can't move! No step size entered!"
                    print "To enter a step size, type a number of degrees in"
                    print "the box near the arrows, and press enter."
                except Exception, e:
                    print e
                else:
                    print self.galil.begin_motion(axis)
                break
        print ''
        event.Skip()
        return

    #The next two functions really feel like they can be 
    #abstracted into one, more powerful function. I couldn't
    #decide on a way to do it that would be good. :p

    def __single_axis_scan_func_continuous(self, flag):
        #A private helper function written to control
        #continuous scans. I think this was a bit buggy...
        funcs = [lambda x: 'scan_'+x+'_input',
                 lambda x: getattr(self, x).GetValue(),
                 eval]
        inputs = map_(['min_'+flag, 'max_'+flag, 'period'], funcs)

        encoders = getattr(self.converter, '{}_to_encoder'.format(flag))(inputs[1]-inputs[0])
        period = inputs[2]
        axis = 0 if flag == 'az' else 1

        while not self.scan_thread_stop.is_set():
            check = self.galil.in_motion(axis)
            if not check:
                print 'THE GALIL CONTROLLER IS TELlING ME IT IS NOT MOVING!!!'
                print 'Starting {} Scan'.format(flag.upper())
                print self.galil.scan(axis, 
                                      encoders,
                                      period,
                                      1)
            time.sleep(.125)
        return

    def __single_axis_scan_func(self, flag, step=False):
        #A private helper function to control single axis scans.
        funcs = [lambda x: 'scan_'+x+'_input',
                 lambda x: getattr(self, x).GetValue(),
                 int]
        inputs = map_(['min_'+flag,'max_'+flag, 'period', 'cycles'], funcs)

        encoders = getattr(self.converter, '{}_to_encoder'.format(flag))(inputs[1]-inputs[0])
        period, cycles = inputs[2:5]
        axis = 0 if flag == 'az' else 1

        if step:
            encoders = encoders / self.config["SCAN_STEPS"]
            period = self.config["SCAN_STEP_PERIOD"]
            cycles = .5
        
        print self.galil.scan(axis,
                              abs(encoders),
                              period,
                              cycles)
        print ''

    def azimuth_scan_func_continuous(self):
        return self.__single_axis_scan_func_continuous('az')

    def elevation_scan_func_continuous(self):
        return self.__single_axis_scan_func_continuous('el')

    def azimuth_scan_func(self, step=False):
        self.__single_axis_scan_func('az', step)

    def elevation_scan_func(self, step=False):
        self.__single_axis_scan_func('el', step)

    def square_scan_func(self, step_el=True):
        #This really needs to be redone and thought through more.
        #I just quickly hacked this nonsense together.
        scans = [self.azimuth_scan_func, self.elevation_scan_func]
        steps = self.config["SCAN_STEPS"]
        axis = not step_el

        while not self.scan_func_stop.is_set():
            if not self.galil.in_motion(axis):
                if axis != step_el:
                    scans[axis]()
                else:
                    scans[axis](step=True)
                    steps -= 1
            if steps == 0:
                break
            axis = not axis
            time.sleep(.125)

    def scan(self, event):
        #This is the function that gets called when
        #you press the scan button.
        from threading import Thread, Event
        def not_implemented(name):
            print name, "Scan Not Implemented!"

        scan_type = self.scan_options.GetValue()
        if self.scan_continuous_input.GetValue():
            junk = '_continuous'
        else:
            junk = ''
        func = getattr(self, 
                       ('{}_scan_func'+junk).format(scan_type.lower()),
                       lambda : not_implemented(scan_type))
        self.scan_thread_stop = Event()
        self.scan_thread = Thread(target=func)
        self.scan_thread.start()
        event.Skip()

    def update_display(self, event):
        #print "updating"
        statuses = [(self.az_status, "Az: "),
                    (self.el_status, "El: "),
                    (self.ra_status, "Ra: "),
                    (self.dec_status,"Dec: "),
                    (self.local_status, "Local: "),
                    (self.lst_status, "Lst: "),
                    (self.utc_status, "Utc: ")]
        while True: #Sometimes the galil responds with 
            try:    #an empty string. When it does...
                data = list(self.galil.get_position())
            except: #...try again.
                continue
            else: #Otherwise, get outta here.
                break
        #data is ordered this way to match the order
        #of the statuses pairs.
        data = [self.converter.encoder_to_az(data[0]),
                self.converter.encoder_to_el(data[1])]
        data += list(self.converter.azel_to_radec(*data))
        data += [self.converter.lct(),
                 self.converter.lst(), 
                 self.converter.utc()]
        data = map(str, data)
        for (widget, prefix), datum in zip(statuses, data):
            widget.SetLabel(prefix + datum)
        event.Skip()
        return

if __name__ == "__main__":
    config = Config("config.txt") #make the config object...
    galil = Galil(config["IP"], config["PORT"]) #...and the galil...
    converter = Units(config) #...and the converter...
    app = wx.PySimpleApp(0)
    wx.InitAllImageHandlers()
    #...and pass them to your MainWindow class!!!
    frame_1 = MainWindow(galil, converter, config, None, -1, "")
    app.SetTopWindow(frame_1)
    frame_1.Show()
    app.MainLoop()
