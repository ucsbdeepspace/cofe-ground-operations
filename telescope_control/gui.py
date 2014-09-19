import logging
import wx

from chart import *
import planets
import scans

class TelescopeControlFrame(wx.Frame):
    def __init__(self, converter, config, *args, **kwds):
        kwds["style"] = wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)
        
        self.config = config
        
        # set logging output
        print("Setting up logging...")
        self.logger = logging.getLogger()
        debug = logging.StreamHandler(sys.stdout)
        debug.setFormatter(logging.Formatter('%(message)s'))
        debug.setLevel(logging.DEBUG)
        self.logger.addHandler(debug)
        self.logger.setLevel(logging.DEBUG)
        
        # unit converter (needed for sky chart)
        self.converter = converter
        
        # positions of solar system objects (for sky chart)
        self.planets = planets.Planets(self.logger, self.converter)

        # Common flags for adding things to sizers
        # Huzzah for {sizer}.AddF(item, SizerFlags)
        self.sizerFlags = wx.SizerFlags().Expand().Border(wx.ALL, 5).Align(
            wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER)

        print("Building UI...")
        self.__create_layout()
        self.__set_properties()

        
    def __set_properties(self):
        self.SetTitle("Telescope Control")
        self.scan_coordsys.SetSelection(1)
        self.scan_type_input.SetSelection(0)
        
    def __create_readoutPanel(self):

        self.statusReadoutPanel                   = wx.Panel(self)
        
        self.statusReadoutPanel.SetDoubleBuffered(True)   # Fix text flickering by forcing the container to be double-buffered.

        self.label_az_status     = wx.StaticText(self.statusReadoutPanel, wx.ID_ANY, "Az:")
        self.label_el_status     = wx.StaticText(self.statusReadoutPanel, wx.ID_ANY, "El:")
        self.label_az_raw_status = wx.StaticText(self.statusReadoutPanel, wx.ID_ANY, "Az Raw:")
        self.label_el_raw_status = wx.StaticText(self.statusReadoutPanel, wx.ID_ANY, "El Raw:")
        self.label_ra_status     = wx.StaticText(self.statusReadoutPanel, wx.ID_ANY, "Ra:")
        self.label_dec_status    = wx.StaticText(self.statusReadoutPanel, wx.ID_ANY, "Dec:")
        self.label_utc_status    = wx.StaticText(self.statusReadoutPanel, wx.ID_ANY, "Utc:")
        self.label_lst_status    = wx.StaticText(self.statusReadoutPanel, wx.ID_ANY, "Lst:")
        self.label_local_status  = wx.StaticText(self.statusReadoutPanel, wx.ID_ANY, "Local:")

        self.az_status     = wx.StaticText(self.statusReadoutPanel, wx.ID_ANY, "0.00 Degrees")
        self.el_status     = wx.StaticText(self.statusReadoutPanel, wx.ID_ANY, "0.00 Degrees")
        self.az_raw_status = wx.StaticText(self.statusReadoutPanel, wx.ID_ANY, "0 Counts")
        self.el_raw_status = wx.StaticText(self.statusReadoutPanel, wx.ID_ANY, "0 Counts")
        self.ra_status     = wx.StaticText(self.statusReadoutPanel, wx.ID_ANY, "0.00 Degrees")
        self.dec_status    = wx.StaticText(self.statusReadoutPanel, wx.ID_ANY, "0.00 Degrees")
        self.utc_status    = wx.StaticText(self.statusReadoutPanel, wx.ID_ANY, "0.00")
        self.lst_status    = wx.StaticText(self.statusReadoutPanel, wx.ID_ANY, "0.00")
        self.local_status  = wx.StaticText(self.statusReadoutPanel, wx.ID_ANY, "0.00")

        self.packet_num  = wx.StaticText(self.statusReadoutPanel, wx.ID_ANY, "RX Pkts: 0 (no data received)")

        textItems = [self.label_az_status,     self.az_status,
                    self.label_el_status,      self.el_status,
                    self.label_az_raw_status,  self.az_raw_status,
                    self.label_el_raw_status,  self.el_raw_status,
                    self.label_ra_status,      self.ra_status,
                    self.label_dec_status,     self.dec_status,
                    self.label_utc_status,     self.utc_status,
                    self.label_lst_status,     self.lst_status,
                    self.label_local_status,   self.local_status]


        for item in textItems:
            if isinstance(item, wx.StaticText):
                item.SetFont(wx.Font(12, wx.DEFAULT, wx.NORMAL, wx.NORMAL, 0, "MS Shell Dlg 2"))

        
        itemSizer = wx.FlexGridSizer(rows=9, cols=2)
        itemSizer.AddMany(textItems)
        itemSizer.AddGrowableCol(0, proportion=1)		# Setting both colums to be growable forces them to expand into the 
        itemSizer.AddGrowableCol(1, proportion=1)		# available space

        self.statusSizerStaticbox = wx.StaticBox(self.statusReadoutPanel, wx.ID_ANY, "Status")
        sizer = wx.StaticBoxSizer(self.statusSizerStaticbox, wx.VERTICAL)
        sizer.AddF(itemSizer, self.sizerFlags)
        sizer.AddF([1,1], self.sizerFlags)
        sizer.AddF([1,1], self.sizerFlags)
        sizer.AddF(self.packet_num, self.sizerFlags)

        self.statusReadoutPanel.SetSizer(sizer)

        return self.statusReadoutPanel

    def __create_motor_power_ctrl_StaticBox(self, parent):

        gridSizer = wx.FlexGridSizer(rows=2, cols=2)

        self.buttton_az_motor       = wx.Button(parent, wx.ID_ANY, "AZ Motor Power")
        self.button_el_motor        = wx.Button(parent, wx.ID_ANY, "EL Motor Power")

        self.azMotorPowerStateLabel = wx.StaticText(parent, wx.ID_ANY, label="Powered Off")
        self.elMotorPowerStateLabel = wx.StaticText(parent, wx.ID_ANY, label="Powered Off")

        gridSizer.AddF(self.buttton_az_motor, self.sizerFlags)
        gridSizer.AddF(self.azMotorPowerStateLabel, self.sizerFlags)
        gridSizer.AddF(self.button_el_motor, self.sizerFlags)
        gridSizer.AddF(self.elMotorPowerStateLabel, self.sizerFlags)

        controlButtonsStaticBox     = wx.StaticBox(parent, wx.ID_ANY, "Motor Power")
        controlButtonsStaticBox.SetDoubleBuffered(True)   # Fix text flickering by forcing the container to be double-buffered.
        sizer = wx.StaticBoxSizer(controlButtonsStaticBox, wx.VERTICAL)
        sizer.Add(gridSizer, flag=wx.EXPAND)

        return sizer

    def __create_motion_control_StaticBox(self, parent):


        verticalSizer = wx.BoxSizer(wx.VERTICAL)
        horizontalSizer = wx.BoxSizer(wx.HORIZONTAL)

        self.button_stop_all = wx.Button(parent, wx.ID_ANY, "Stop All")
        self.button_stop_az  = wx.Button(parent, wx.ID_ANY, "Stop AZ")
        self.button_stop_el  = wx.Button(parent, wx.ID_ANY, "Stop EL")


        verticalSizer.AddF(self.button_stop_all, self.sizerFlags)
        
        horizontalSizer.AddF(self.button_stop_az, self.sizerFlags)
        horizontalSizer.AddF(self.button_stop_el, self.sizerFlags)
        verticalSizer.Add(horizontalSizer, flag=wx.EXPAND)

        controlButtonsStaticBox = wx.StaticBox(parent, wx.ID_ANY, "Motion Control")
        sizer = wx.StaticBoxSizer(controlButtonsStaticBox, wx.VERTICAL)
        sizer.Add(verticalSizer)

        return sizer
    
    def __create_chart_options(self, parent):
        chart_options_box = wx.StaticBox(parent, wx.ID_ANY, "Chart Options")
        options_box_sizer = wx.StaticBoxSizer(chart_options_box, wx.VERTICAL)
        list_sizer = wx.BoxSizer(wx.VERTICAL)
        
        list_sizer.AddF(wx.StaticText(parent, wx.ID_ANY, "Center on:"), self.sizerFlags)
        
        self.cur_center_input = wx.ComboBox(parent, wx.ID_ANY,
            choices=["Current Position", "Current Scan"],
            style=wx.CB_DROPDOWN | wx.CB_READONLY)
        list_sizer.AddF(self.cur_center_input, self.sizerFlags)
        self.cur_center_input.SetSelection(0)
        options_box_sizer.Add(list_sizer)
        
        return options_box_sizer

    def __create_controls_sizer(self):

        controlButtonPanel = wx.Panel(self)
        sizer = wx.BoxSizer(wx.VERTICAL)

        sizer.Add(self.__create_motor_power_ctrl_StaticBox(controlButtonPanel), flag=wx.EXPAND)
        sizer.Add(self.__create_motion_control_StaticBox(controlButtonPanel), flag=wx.EXPAND)
        sizer.Add(self.__create_chart_options(controlButtonPanel), flag=wx.EXPAND)


        controlButtonPanel.SetSizer(sizer)
        return controlButtonPanel


    def __create_equ_goto (self, parentNotebook):
        staticBoxGotoRaDec = wx.StaticBox(parentNotebook, wx.ID_ANY, "Track Position")
        staticTextRaLabel = wx.StaticText(parentNotebook, wx.ID_ANY, "Ra: ")
        staticTextDecLabel = wx.StaticText(parentNotebook, wx.ID_ANY, "Dec:")

        self.goto_ra_input = wx.TextCtrl(parentNotebook, wx.ID_ANY, "0")
        self.goto_de_input = wx.TextCtrl(parentNotebook, wx.ID_ANY, "0")
        self.goto_equ_input = wx.Button(parentNotebook, wx.ID_ANY, "Start Tracking")

        gridSizer = wx.FlexGridSizer(3, 2)
        gridSizer.AddF(staticTextRaLabel, self.sizerFlags)
        gridSizer.AddF(self.goto_ra_input, self.sizerFlags)

        gridSizer.AddF(staticTextDecLabel, self.sizerFlags)
        gridSizer.AddF(self.goto_de_input, self.sizerFlags)
        
        gridSizer.Add([1,1])
        gridSizer.Add(self.goto_equ_input, flag=wx.EXPAND)

        baseSizer = wx.StaticBoxSizer(staticBoxGotoRaDec, wx.VERTICAL)
        baseSizer.Add(gridSizer, 1, wx.EXPAND)

        return baseSizer

    def __create_equ_sync (self, parent):
        staticBoxRaDecCal = wx.StaticBox(parent, wx.ID_ANY, "Sync to Position")
        staticTextDecLabel = wx.StaticText(parent, wx.ID_ANY, "Dec:")
        staticTextRaLabel = wx.StaticText(parent, wx.ID_ANY, "Ra: ")

        self.sync_ra_input = wx.TextCtrl(parent, wx.ID_ANY, "0")
        self.sync_de_input = wx.TextCtrl(parent, wx.ID_ANY, "0")

        gridSizer = wx.FlexGridSizer(3, 2)

        gridSizer.AddF(staticTextRaLabel, self.sizerFlags)
        gridSizer.AddF(self.sync_ra_input, self.sizerFlags)

        gridSizer.AddF(staticTextDecLabel, self.sizerFlags)
        gridSizer.AddF(self.sync_de_input, self.sizerFlags)
        
        gridSizer.Add([1,1])
        self.sync_equ_input = wx.Button(parent, wx.ID_ANY, "Calibrate")
        gridSizer.Add(self.sync_equ_input, flag=wx.EXPAND)
        
        baseSizer = wx.StaticBoxSizer(staticBoxRaDecCal, wx.VERTICAL)
        baseSizer.Add(gridSizer, 1, wx.EXPAND)
        return baseSizer

    def __create_joystick_panel(self, parent):
        staticBoxRelativeMoveCtrl = wx.StaticBox(parent, wx.ID_ANY, "Relative Move")

        self.button_up            = wx.Button(parent, wx.ID_ANY, "^")
        self.button_left          = wx.Button(parent, wx.ID_ANY, "<")
        self.button_right         = wx.Button(parent, wx.ID_ANY, ">")
        self.button_down          = wx.Button(parent, wx.ID_ANY, "v")

        self.step_size_input      = wx.TextCtrl(parent, wx.ID_ANY, "10", style=wx.TE_PROCESS_ENTER)
        self.staticTextStepSize   = wx.StaticText(parent, wx.ID_ANY, "Degrees")
        
        stepSizeSizer = wx.BoxSizer(wx.HORIZONTAL)
        stepSizeSizer.AddF(self.step_size_input, self.sizerFlags)
        stepSizeSizer.AddF(self.staticTextStepSize, self.sizerFlags)

        joystickSizer = wx.GridSizer(3, 3)
        joystickSizer.Add([1,1])
        joystickSizer.Add(self.button_up, flag=wx.EXPAND)
        joystickSizer.Add([1,1])

        joystickSizer.Add(self.button_left, flag=wx.EXPAND)
        joystickSizer.Add([1,1])
        joystickSizer.Add(self.button_right, flag=wx.EXPAND)
        
        joystickSizer.Add([1,1])
        joystickSizer.Add(self.button_down, flag=wx.EXPAND)
        joystickSizer.Add([1,1])

        joystickPaneSizer = wx.StaticBoxSizer(staticBoxRelativeMoveCtrl, wx.VERTICAL)
        joystickPaneSizer.Add(stepSizeSizer, 0, wx.EXPAND)
        joystickPaneSizer.Add(joystickSizer, 1, wx.EXPAND)

        return joystickPaneSizer

    def __create_az_el_calibrate_panel(self, parent):
        calibrateStaticBox      = wx.StaticBox(parent, wx.ID_ANY, "Sync to Position")
        self.sync_az_input = wx.TextCtrl(parent, wx.ID_ANY, "0")
        self.sync_el_input = wx.TextCtrl(parent, wx.ID_ANY, "0")

        self.sync_hor_input = wx.Button(parent, wx.ID_ANY, "Calibrate")
        
        gridSizer = wx.FlexGridSizer(3,2)
        gridSizer.AddF(wx.StaticText(parent, wx.ID_ANY, "Azimuth:"), self.sizerFlags)
        gridSizer.AddF(self.sync_az_input, self.sizerFlags)
        gridSizer.AddF(wx.StaticText(parent, wx.ID_ANY, "Altitude:"), self.sizerFlags)
        gridSizer.AddF(self.sync_el_input, self.sizerFlags)
        gridSizer.Add([1,1])
        gridSizer.AddF(self.sync_hor_input, self.sizerFlags)

        baseSizer = wx.StaticBoxSizer(calibrateStaticBox, wx.VERTICAL)
        baseSizer.Add(gridSizer, 1, wx.EXPAND)

        return baseSizer

    def __create_absolute_move_pane(self, parent):

        absoluteMoveStaticBox = wx.StaticBox(parent, wx.ID_ANY, "Move to Position")
        self.goto_az_input = wx.TextCtrl(parent, wx.ID_ANY, "0")
        self.goto_el_input = wx.TextCtrl(parent, wx.ID_ANY, "0")
        self.goto_hor_input = wx.Button(parent, wx.ID_ANY, "Start Move")

        gridSizer = wx.FlexGridSizer(3,2)
        gridSizer.AddF(wx.StaticText(parent, wx.ID_ANY, "Azimuth: "), self.sizerFlags)
        gridSizer.AddF(self.goto_az_input, self.sizerFlags)
        gridSizer.AddF(wx.StaticText(parent, wx.ID_ANY, "Altitude: "), self.sizerFlags)
        gridSizer.AddF(self.goto_el_input, self.sizerFlags)
        gridSizer.Add([1,1])
        gridSizer.AddF(self.goto_hor_input, self.sizerFlags)


        baseSizer = wx.StaticBoxSizer(absoluteMoveStaticBox, wx.VERTICAL)
        baseSizer.Add(gridSizer, 1, wx.EXPAND)

        return baseSizer

    def __create_joystick_pane(self):
        notebookJoystickPane = wx.Panel(self.controlNotebook)
        
        h_sizer = wx.BoxSizer(wx.HORIZONTAL)
        h_sizer.Add(self.__create_joystick_panel(notebookJoystickPane), 1, wx.EXPAND)
        
        v_sizer = wx.BoxSizer(wx.VERTICAL)
        v_sizer.Add(self.__create_absolute_move_pane(notebookJoystickPane), 1, wx.EXPAND)
        v_sizer.Add(self.__create_az_el_calibrate_panel(notebookJoystickPane), 1, wx.EXPAND)
        h_sizer.Add(v_sizer, 1, wx.EXPAND)
        
        notebookJoystickPane.SetSizer(h_sizer)
        return notebookJoystickPane

    # list of targets to slew and sync to
    def __create_targets_pane (self):
        targets_panel = wx.Panel(self.controlNotebook)
        overall_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        equ_sizer = wx.BoxSizer(wx.VERTICAL)
        equ_sizer.Add(self.__create_equ_goto(targets_panel), 1, wx.EXPAND)
        equ_sizer.Add(self.__create_equ_sync(targets_panel), 1, wx.EXPAND)
        overall_sizer.Add(equ_sizer, 1, wx.EXPAND)
        
        targets_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # box for solar system objects
        sso_box = wx.StaticBox(targets_panel, wx.ID_ANY, "Solar System Objects")
        sso_box_sizer = wx.StaticBoxSizer(sso_box, wx.VERTICAL)
        
        sso_sizer = wx.BoxSizer(wx.HORIZONTAL)
        sso_sizer.AddF(wx.StaticText(targets_panel, wx.ID_ANY, "Object: "),
            self.sizerFlags)
        self.sso_input = wx.ComboBox(targets_panel, wx.ID_ANY,
            choices=planets.objects, style=wx.CB_DROPDOWN | wx.CB_READONLY)
        self.sso_input.SetSelection(0)
        sso_sizer.AddF(self.sso_input, self.sizerFlags)
        sso_box_sizer.Add(sso_sizer)
        
        sso_buttons_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.sso_goto_input = wx.Button(targets_panel, wx.ID_ANY, "Goto")
        sso_buttons_sizer.Add(self.sso_goto_input)
        self.sso_sync_input = wx.Button(targets_panel, wx.ID_ANY, "Sync")
        sso_buttons_sizer.Add(self.sso_sync_input)
        self.sso_scan_input = wx.Button(targets_panel, wx.ID_ANY, "Scan")
        sso_buttons_sizer.Add(self.sso_scan_input)
        sso_box_sizer.Add(sso_buttons_sizer)
        
        targets_sizer.Add(sso_box_sizer, 1, wx.EXPAND)
        
        # box for other objects
        ngcic_box = wx.StaticBox(targets_panel, wx.ID_ANY, "NGC/IC Objects")
        ngcic_box_sizer = wx.StaticBoxSizer(ngcic_box, wx.VERTICAL)
        
        ngcic_sizer = wx.FlexGridSizer(2, 2)
        ngcic_sizer.AddF(wx.StaticText(targets_panel, wx.ID_ANY, "Catalog: "),
            self.sizerFlags)
        self.ngcic_catalog = wx.ComboBox(targets_panel, wx.ID_ANY,
            choices=["NGC", "IC"], style=wx.CB_DROPDOWN | wx.CB_READONLY)
        self.ngcic_catalog.SetSelection(0)
        ngcic_sizer.AddF(self.ngcic_catalog, self.sizerFlags)
        
        ngcic_sizer.AddF(wx.StaticText(targets_panel, wx.ID_ANY, "Number: "),
            self.sizerFlags)
        self.ngcic_input = wx.SpinCtrl(targets_panel, wx.ID_ANY,
            value="1", min=1, max=7840)
        ngcic_sizer.AddF(self.ngcic_input, self.sizerFlags)
        ngcic_box_sizer.Add(ngcic_sizer)
        
        ngcic_buttons_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.ngcic_goto_input = wx.Button(targets_panel, wx.ID_ANY, "Goto")
        ngcic_buttons_sizer.Add(self.ngcic_goto_input)
        self.ngcic_sync_input = wx.Button(targets_panel, wx.ID_ANY, "Sync")
        ngcic_buttons_sizer.Add(self.ngcic_sync_input)
        self.ngcic_scan_input = wx.Button(targets_panel, wx.ID_ANY, "Scan")
        ngcic_buttons_sizer.Add(self.ngcic_scan_input)
        ngcic_box_sizer.Add(ngcic_buttons_sizer)
        
        targets_sizer.Add(ngcic_box_sizer, 1, wx.EXPAND)
        overall_sizer.Add(targets_sizer, 1, wx.EXPAND)
        
        targets_panel.SetSizer(overall_sizer)
        return targets_panel
    
    # simple scans: use the least motor movements between points
    def __create_simple_scans (self):
        simple_panel = wx.Panel(self.controlNotebook)
        simple_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        # box for zenith spiral scan
        zenith_box = wx.StaticBox(simple_panel, wx.ID_ANY, "Zenith Spiral Scan")
        zenith_box_sizer = wx.StaticBoxSizer(zenith_box, wx.VERTICAL)
        
        zs_sizer = wx.FlexGridSizer(4, 2)
        zs_sizer.AddF(wx.StaticText(simple_panel, wx.ID_ANY, "Starting Azimuth: "),
            self.sizerFlags)
        self.zst_azimuth_input = wx.TextCtrl(simple_panel, wx.ID_ANY, "0")
        zs_sizer.AddF(self.zst_azimuth_input, self.sizerFlags)
        
        zs_sizer.AddF(wx.StaticText(simple_panel, wx.ID_ANY, "Starting Altitude: "),
            self.sizerFlags)
        self.zst_altitude_input = wx.TextCtrl(simple_panel, wx.ID_ANY, "10")
        zs_sizer.AddF(self.zst_altitude_input, self.sizerFlags)
        
        zs_sizer.AddF(wx.StaticText(simple_panel, wx.ID_ANY, "Altitude Increment: "),
            self.sizerFlags)
        self.zs_inc_input = wx.TextCtrl(simple_panel, wx.ID_ANY, "10")
        zs_sizer.AddF(self.zs_inc_input, self.sizerFlags)
        
        zs_sizer.AddF(wx.StaticText(simple_panel, wx.ID_ANY, "Cycles (0 = infinite): "),
            self.sizerFlags)
        self.zs_cycles_input = wx.TextCtrl(simple_panel, wx.ID_ANY, "1")
        zs_sizer.AddF(self.zs_cycles_input, self.sizerFlags)
        
        zenith_box_sizer.Add(zs_sizer)
        
        zs_buttons_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        self.zs_preview_input = wx.Button(simple_panel, wx.ID_ANY, "Preview")
        zs_buttons_sizer.Add(self.zs_preview_input)
        self.zs_begin_input = wx.Button(simple_panel, wx.ID_ANY, "Begin Scan")
        zs_buttons_sizer.Add(self.zs_begin_input)
        
        zenith_box_sizer.Add(zs_buttons_sizer)
        
        simple_sizer.Add(zenith_box_sizer, 1, wx.EXPAND)
        
        # box for horizontal graticule scans
        horiz_box = wx.StaticBox(simple_panel, wx.ID_ANY, "Horizontal Graticule Scan")
        horiz_box_sizer = wx.StaticBoxSizer(horiz_box, wx.VERTICAL)
        
        hg_sizer = wx.FlexGridSizer(4, 2)
        hg_sizer.AddF(wx.StaticText(simple_panel, wx.ID_ANY, "Left Azimuth: "),
            self.sizerFlags)
        self.left_azimuth_input = wx.TextCtrl(simple_panel, wx.ID_ANY, "0")
        hg_sizer.AddF(self.left_azimuth_input, self.sizerFlags)
        
        hg_sizer.AddF(wx.StaticText(simple_panel, wx.ID_ANY, "Right Azimuth: "),
            self.sizerFlags)
        self.right_azimuth_input = wx.TextCtrl(simple_panel, wx.ID_ANY, "190")
        hg_sizer.AddF(self.right_azimuth_input, self.sizerFlags)
        
        hg_sizer.AddF(wx.StaticText(simple_panel, wx.ID_ANY, "Low Altitude: "),
            self.sizerFlags)
        self.low_altitude_input = wx.TextCtrl(simple_panel, wx.ID_ANY, "10")
        hg_sizer.AddF(self.low_altitude_input, self.sizerFlags)
        
        hg_sizer.AddF(wx.StaticText(simple_panel, wx.ID_ANY, "High Altitude: "),
            self.sizerFlags)
        self.high_altitude_input = wx.TextCtrl(simple_panel, wx.ID_ANY, "80")
        hg_sizer.AddF(self.high_altitude_input, self.sizerFlags)
        
        hg_sizer.AddF(wx.StaticText(simple_panel, wx.ID_ANY, "# of S-Turns: "),
            self.sizerFlags)
        self.hg_turns_input = wx.TextCtrl(simple_panel, wx.ID_ANY, "5")
        hg_sizer.AddF(self.hg_turns_input, self.sizerFlags)
        
        hg_sizer.AddF(wx.StaticText(simple_panel, wx.ID_ANY, "Cycles (0 = infinite): "),
            self.sizerFlags)
        self.hg_cycles_input = wx.TextCtrl(simple_panel, wx.ID_ANY, "1")
        hg_sizer.AddF(self.hg_cycles_input, self.sizerFlags)
        
        horiz_box_sizer.Add(hg_sizer)
        
        hg_buttons_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        self.hg_preview_input = wx.Button(simple_panel, wx.ID_ANY, "Preview")
        hg_buttons_sizer.Add(self.hg_preview_input)
        self.hg_begin_input = wx.Button(simple_panel, wx.ID_ANY, "Begin Scan")
        hg_buttons_sizer.Add(self.hg_begin_input)
        
        horiz_box_sizer.Add(hg_buttons_sizer)
        simple_sizer.Add(horiz_box_sizer, 1, wx.EXPAND)
        
        simple_panel.SetSizer(simple_sizer)
        return simple_panel

    # short scans: take the shortest angular distance between points
    def __create_scanning_pane(self):
        scan_panel = wx.Panel(self.controlNotebook)
        
        self.center_crda_label = wx.StaticText(scan_panel, wx.ID_ANY, "Crd A: ")
        self.center_crda_input = wx.TextCtrl(scan_panel, wx.ID_ANY, "10")
        self.center_crdb_label = wx.StaticText(scan_panel, wx.ID_ANY, "Crd B: ")
        self.center_crdb_input = wx.TextCtrl(scan_panel, wx.ID_ANY, "40")
        
        size_edge_label = wx.StaticText(scan_panel, wx.ID_ANY, "Size (degrees): ")
        size_edge_label.SetToolTipString("Size: length (in degrees) of each "
            + "side of the scan box.")
        self.size_edge_input = wx.TextCtrl(scan_panel, wx.ID_ANY, "10")
        num_turns_label = wx.StaticText(scan_panel, wx.ID_ANY, "# of S-Turns: ")
        num_turns_label.SetToolTipString("S-Turn: two 180 degree "
            + "U-turns, resembling the letter S.")
        self.num_turns_input = wx.TextCtrl(scan_panel, wx.ID_ANY, "5")
        scan_cycles_label = wx.StaticText(scan_panel, wx.ID_ANY, "Cycles to Run: ")
        scan_cycles_label.SetToolTipString("Cycle: move from one end of the "
            + "scan to the other and back.")
        self.scan_cycles_input = wx.TextCtrl(scan_panel, wx.ID_ANY, "1")
        self.scan_repeat_input = wx.CheckBox(scan_panel, wx.ID_ANY, "Repeat indefinitely")
        self.buttonScanStart = wx.Button(scan_panel, wx.ID_ANY, "Begin Scan")
        self.preview_scan = wx.Button(scan_panel, wx.ID_ANY, "Preview")

        coord_sys = ["Horizontal (A=Az, B=El)", "Equatorial (A=RA, B=De)"]
        self.scan_coordsys = wx.ComboBox(scan_panel, wx.ID_ANY,
            choices=coord_sys, style=wx.CB_DROPDOWN | wx.CB_READONLY)
        
        scanOptionsList = [func.__name__.capitalize() for func in scans.scan_list]
        self.scan_type_input = wx.ComboBox(scan_panel, wx.ID_ANY,
            choices=scanOptionsList, style=wx.CB_DROPDOWN | wx.CB_READONLY)
        
        scan_param_box = wx.StaticBox(scan_panel, wx.ID_ANY, "Parameters")
        param_box_sizer = wx.StaticBoxSizer(scan_param_box)
        scan_param_sizer = wx.FlexGridSizer(3, 2)
        scan_param_sizer.AddF(size_edge_label, self.sizerFlags)
        scan_param_sizer.AddF(self.size_edge_input, self.sizerFlags)
        scan_param_sizer.AddF(num_turns_label, self.sizerFlags)
        scan_param_sizer.AddF(self.num_turns_input, self.sizerFlags)
        scan_param_sizer.AddF(scan_cycles_label, self.sizerFlags)
        scan_param_sizer.AddF(self.scan_cycles_input, self.sizerFlags)
        scan_param_sizer.AddF(self.scan_repeat_input, self.sizerFlags)
        param_box_sizer.AddF(scan_param_sizer, self.sizerFlags)
        
        scan_left_sizer = wx.BoxSizer(wx.VERTICAL)
        scan_left_sizer.Add(param_box_sizer, 1, wx.EXPAND)
        
        # --
        
        scan_center_box = wx.StaticBox(scan_panel, wx.ID_ANY, "Center")
        center_box_sizer = wx.StaticBoxSizer(scan_center_box)
        scan_center_sizer = wx.FlexGridSizer(2, 2)
        scan_center_sizer.AddF(self.center_crda_label, self.sizerFlags)
        scan_center_sizer.AddF(self.center_crda_input, self.sizerFlags)
        scan_center_sizer.AddF(self.center_crdb_label, self.sizerFlags)
        scan_center_sizer.AddF(self.center_crdb_input, self.sizerFlags)
        center_box_sizer.AddF(scan_center_sizer, self.sizerFlags)
        
        scan_select_sizer = wx.BoxSizer(wx.VERTICAL)
        scan_select_sizer.Add(self.scan_coordsys, 1, wx.EXPAND)
        scan_select_sizer.Add(self.scan_type_input, 1, wx.EXPAND)
        
        scan_button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        scan_button_sizer.Add(self.preview_scan, 1, wx.EXPAND)
        scan_button_sizer.Add(self.buttonScanStart, 1, wx.EXPAND)
        scan_select_sizer.Add(scan_button_sizer, 1, wx.EXPAND)
        
        scan_type_box = wx.StaticBox(scan_panel, wx.ID_ANY, "Type")
        type_box_sizer = wx.StaticBoxSizer(scan_type_box, wx.VERTICAL)
        type_box_sizer.Add(scan_select_sizer, 1, wx.EXPAND)
        
        scan_right_sizer = wx.BoxSizer(wx.VERTICAL)
        scan_right_sizer.Add(center_box_sizer, 1, wx.EXPAND)
        scan_right_sizer.Add(type_box_sizer, 1, wx.EXPAND)

        scan_sizer = wx.BoxSizer(wx.HORIZONTAL)
        scan_sizer.Add(scan_left_sizer, 1, wx.EXPAND)
        scan_sizer.Add(scan_right_sizer, 1, wx.EXPAND)
        
        scan_panel.SetSizer(scan_sizer)

        return scan_panel

    def __create_options_pane(self):
        notebookOptionsPane = wx.Panel(self.controlNotebook)
        options_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        ##
        # slew box
        ##
        
        slew_box = wx.StaticBox(notebookOptionsPane, wx.ID_ANY, "Slew Options")
        slew_box_sizer = wx.StaticBoxSizer(slew_box, wx.VERTICAL)
        
        scan_speed_label = wx.StaticText(notebookOptionsPane, wx.ID_ANY, "Speed (deg/s): ")
        self.scan_speed_input = wx.TextCtrl(notebookOptionsPane, wx.ID_ANY,
            self.config.get("slew", "speed"))
        
        scan_accel_label = wx.StaticText(notebookOptionsPane, wx.ID_ANY, "Accel (deg/s^2):")
        self.scan_accel_input = wx.TextCtrl(notebookOptionsPane, wx.ID_ANY,
            self.config.get("slew", "accel"))

        slew_grid = wx.FlexGridSizer(4,2)
        slew_grid.AddF(scan_speed_label, self.sizerFlags)
        slew_grid.AddF(self.scan_speed_input, self.sizerFlags)

        slew_grid.AddF(scan_accel_label, self.sizerFlags)
        slew_grid.AddF(self.scan_accel_input, self.sizerFlags)

        slew_box_sizer.Add(slew_grid)
        options_sizer.Add(slew_box_sizer, 1, wx.EXPAND)
        
        ##
        # observer box
        ##
        
        obs_box = wx.StaticBox(notebookOptionsPane, wx.ID_ANY, "Observer Options")
        obs_box_sizer = wx.StaticBoxSizer(obs_box, wx.VERTICAL)
        
        obs_lon_label = wx.StaticText(notebookOptionsPane, wx.ID_ANY, "Longitude (deg): ")
        self.obs_lon_input = wx.TextCtrl(notebookOptionsPane, wx.ID_ANY,
            self.config.get("location", "lon"))
        
        obs_lat_label = wx.StaticText(notebookOptionsPane, wx.ID_ANY, "Latitude (deg):")
        self.obs_lat_input = wx.TextCtrl(notebookOptionsPane, wx.ID_ANY,
            self.config.get("location", "lat"))

        obs_grid = wx.FlexGridSizer(4,2)
        obs_grid.AddF(obs_lon_label, self.sizerFlags)
        obs_grid.AddF(self.obs_lon_input, self.sizerFlags)

        obs_grid.AddF(obs_lat_label, self.sizerFlags)
        obs_grid.AddF(self.obs_lat_input, self.sizerFlags)

        obs_box_sizer.Add(obs_grid)
        options_sizer.Add(obs_box_sizer, 1, wx.EXPAND)
        
        notebookOptionsPane.SetSizer(options_sizer)

        return notebookOptionsPane

    def __create_graphPanel(self):
        self.graphDisplayPanel   = wx.Panel(self)
        self.graphPanelStaticbox = wx.StaticBox(self.graphDisplayPanel, wx.ID_ANY, "Graph")

        graphPanelSizer = wx.StaticBoxSizer(self.graphPanelStaticbox, wx.HORIZONTAL)
        self.graphDisplayPanel.SetSizer(graphPanelSizer)
        
        return self.graphDisplayPanel
        
    def __create_chart(self):
        self.sky_panel = wx.Panel(self)
        sky_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # control bar
        ctrl_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        self.chart_crdsys = wx.ComboBox(self.sky_panel, wx.ID_ANY,
            choices=["Horizontal (Azimuth, Altitude)",
                     "Equatorial (Right Asc, Declination)"],
            style=wx.CB_DROPDOWN | wx.CB_READONLY)
        self.chart_crdsys.SetSelection(0)
        ctrl_sizer.Add(self.chart_crdsys, 1, wx.EXPAND)
        
        # create field of view display
        fov_label = wx.StaticText(self.sky_panel, label="   Field of View: ")
        ctrl_sizer.Add(fov_label)
        self.chart_fov = wx.SpinCtrl(self.sky_panel, value="100", min=1, max=340)
        ctrl_sizer.Add(self.chart_fov)
        
        # create OpenGL canvas
        self.sky_chart = Chart(self.sky_panel, self.chart_fov,
            self.converter, self.planets)
        sky_sizer.Add(self.sky_chart, 1, wx.EXPAND)
        sky_sizer.Add(ctrl_sizer, 0, wx.EXPAND)
        
        self.sky_panel.SetSizer(sky_sizer)
        return self.sky_panel

    def __create_layout(self):
        
        print("Building header...")
        headerSizer = wx.BoxSizer(wx.HORIZONTAL)

        print("Building readout panel...")
        headerSizer.Add(self.__create_readoutPanel(), proportion=1, flag=wx.EXPAND)
        print("Building OpenGL sky chart display...")
        headerSizer.Add(self.__create_chart(), proportion=2, flag=wx.EXPAND)
        print("Building top-right controls...")
        headerSizer.Add(self.__create_controls_sizer(), proportion=1, flag=wx.EXPAND)
        
        print("Building footer...")
        footerSizer = wx.BoxSizer(wx.HORIZONTAL)
    
        self.controlNotebook = wx.Notebook(self, wx.ID_ANY, style=0)
        print("Building joy stick...")
        self.controlNotebook.AddPage(self.__create_joystick_pane(), "Joy Stick")
        print("Building targets panel...")
        self.controlNotebook.AddPage(self.__create_targets_pane(), "Targets")
        print("Building simple scans panel...")
        self.controlNotebook.AddPage(self.__create_simple_scans(), "Simple Scans")
        print("Building standard scans panel...")
        self.controlNotebook.AddPage(self.__create_scanning_pane(), "Scanning")
        print("Building options panel...")
        self.controlNotebook.AddPage(self.__create_options_pane(), "Options")
        print("Building graph of output...")
        footerSizer.Add(self.__create_graphPanel(), proportion=1, flag=wx.EXPAND)
        footerSizer.Add(self.controlNotebook, proportion=2, flag=wx.EXPAND)
        
        print("Collecting all UI elements together...")
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        mainSizer.Add(headerSizer, proportion=1, flag=wx.EXPAND)
        mainSizer.Add(footerSizer, proportion=1, flag=wx.EXPAND)
        self.SetSizer(mainSizer)
        mainSizer.Fit(self)
        
        print("Finalizing layout...")
        self.Layout()
        

def main():		# Shut up pylinter
    app = wx.App()
    mainFrame = TelescopeControlFrame(None, -1, "")
    app.SetTopWindow(mainFrame)
    mainFrame.Show()
    app.MainLoop()


if __name__ == "__main__":
    main()

