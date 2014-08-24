from chart import *
import wx

import scans

class TelescopeControlFrame(wx.Frame):
    def __init__(self, converter, *args, **kwds):
        kwds["style"] = wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)
        
        # unit converter (needed for sky chart)
        self.converter = converter

        # Common flags for adding things to sizers
        # Huzzah for {sizer}.AddF(item, SizerFlags)
        self.sizerFlags = wx.SizerFlags().Expand().Border(wx.ALL, 5).Align(wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER)

        self.__create_layout()
        self.__set_properties()

        
    def __set_properties(self):
        self.SetTitle("Telescope Control Code")
        self.coordsys_selector.SetSelection(0)
        self.comboBoxScanOptions.SetSelection(0)
        
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

        self.packet_num  = wx.StaticText(self.statusReadoutPanel, wx.ID_ANY, "RX Pkts: 0 (if you can see this,\nsomething is broken)")

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

    def __create_controls_sizer(self):

        controlButtonPanel = wx.Panel(self)
        sizer = wx.BoxSizer(wx.VERTICAL)

        sizer.Add(self.__create_motor_power_ctrl_StaticBox(controlButtonPanel), flag=wx.EXPAND)
        sizer.Add(self.__create_motion_control_StaticBox(controlButtonPanel), flag=wx.EXPAND)
        sizer.Add([1,1], proportion=1, flag=wx.EXPAND)


        controlButtonPanel.SetSizer(sizer)
        return controlButtonPanel


    def __create_goto_ra_dec_staticbox(self, parentNotebook):
        staticBoxGotoRaDec               = wx.StaticBox(parentNotebook, wx.ID_ANY, "Goto Ra/Dec")
        staticTextRaLabel                = wx.StaticText(parentNotebook, wx.ID_ANY, "Ra: ")
        staticTextDecLabel               = wx.StaticText(parentNotebook, wx.ID_ANY, "Dec:")

        self.textCtrlGotoRightAscension  = wx.TextCtrl(parentNotebook, wx.ID_ANY, "")
        self.textCtrlGotoDeclination     = wx.TextCtrl(parentNotebook, wx.ID_ANY, "")
        self.buttonGotoPosition          = wx.Button(parentNotebook, wx.ID_ANY, "Goto Position")

        gridSizer = wx.FlexGridSizer(3, 2)
        gridSizer.AddF(staticTextRaLabel, self.sizerFlags)
        gridSizer.AddF(self.textCtrlGotoRightAscension, self.sizerFlags)

        gridSizer.AddF(staticTextDecLabel, self.sizerFlags)
        gridSizer.AddF(self.textCtrlGotoDeclination, self.sizerFlags)
        
        gridSizer.Add([1,1])
        gridSizer.Add(self.buttonGotoPosition, flag=wx.EXPAND)

        baseSizer = wx.StaticBoxSizer(staticBoxGotoRaDec, wx.VERTICAL)
        baseSizer.Add(gridSizer, 1, wx.EXPAND)

        return baseSizer


    def __create_ra_dec_tracking_staticbox(self, parentNotebook):
        staticBoxRaDecTracking              = wx.StaticBox(parentNotebook, wx.ID_ANY, "Ra/Dec Tracking")
        staticTextDecLabel                  = wx.StaticText(parentNotebook, wx.ID_ANY, "Dec:")
        staticTextRaLabel                   = wx.StaticText(parentNotebook, wx.ID_ANY, "Ra: ")

        self.textCtrlTrackingRightAscension = wx.TextCtrl(parentNotebook, wx.ID_ANY, "")
        self.textCtrlTrackingDeclination    = wx.TextCtrl(parentNotebook, wx.ID_ANY, "")

        gridSizer = wx.FlexGridSizer(3, 4)
        gridSizer.AddGrowableCol(2, proportion=1)

        gridSizer.AddF(staticTextRaLabel, self.sizerFlags)
        gridSizer.AddF(self.textCtrlTrackingRightAscension, self.sizerFlags)
        gridSizer.Add([1,1])
        gridSizer.Add([1,1])

        gridSizer.AddF(staticTextDecLabel, self.sizerFlags)
        gridSizer.AddF(self.textCtrlTrackingDeclination, self.sizerFlags)
        gridSizer.Add([1,1])
        gridSizer.Add([1,1])

        # This is a bit hacky
        gridSizer.Add([1,1])
        gridSizer.Add(self.buttonTrackPosition, flag=wx.EXPAND)
        gridSizer.Add([1,1])
        gridSizer.Add(self.buttonTrackingToggle)


        baseSizer = wx.StaticBoxSizer(staticBoxRaDecTracking, wx.VERTICAL)
        baseSizer.Add(gridSizer, 1, wx.EXPAND)
        return baseSizer

    def __create_ra_dec_calibrate_staticbox(self, parentNotebook):
        staticBoxRaDecCal                   = wx.StaticBox(parentNotebook, wx.ID_ANY, "Calibrate Ra/Dec")
        staticTextDecLabel                  = wx.StaticText(parentNotebook, wx.ID_ANY, "Dec:")
        staticTextRaLabel                   = wx.StaticText(parentNotebook, wx.ID_ANY, "Ra: ")

        self.textCtrlRightAscensionCalInput = wx.TextCtrl(parentNotebook, wx.ID_ANY, "")
        self.textCtrlDeclinationCalInput    = wx.TextCtrl(parentNotebook, wx.ID_ANY, "")

        gridSizer = wx.FlexGridSizer(3, 2)

        gridSizer.AddF(staticTextRaLabel, self.sizerFlags)
        gridSizer.AddF(self.textCtrlRightAscensionCalInput, self.sizerFlags)

        gridSizer.AddF(staticTextDecLabel, self.sizerFlags)
        gridSizer.AddF(self.textCtrlDeclinationCalInput, self.sizerFlags)
        
        gridSizer.Add([1,1])
        gridSizer.Add(self.buttonDoRaDecCalibrate, flag=wx.EXPAND)
        
        baseSizer = wx.StaticBoxSizer(staticBoxRaDecCal, wx.VERTICAL)
        baseSizer.Add(gridSizer, 1, wx.EXPAND)
        return baseSizer

    def __create_ra_dec_pane(self):
        notebookRaDecPane                         = wx.Panel(self.controlNotebook)
        self.buttonDoRaDecCalibrate               = wx.Button(notebookRaDecPane, wx.ID_ANY, "Calibrate")
        self.buttonTrackPosition                  = wx.Button(notebookRaDecPane, wx.ID_ANY, "Track Position")
        self.buttonTrackingToggle                 = wx.ToggleButton(notebookRaDecPane, wx.ID_ANY, "Tracking On")
        
        sizerRaDecPanelUpper = wx.BoxSizer(wx.HORIZONTAL)
        sizerRaDecPanelUpper.Add(self.__create_goto_ra_dec_staticbox(notebookRaDecPane), 1, wx.EXPAND)
        sizerRaDecPanelUpper.Add(self.__create_ra_dec_calibrate_staticbox(notebookRaDecPane), 1, wx.EXPAND)

        sizerRaDecPane = wx.BoxSizer(wx.VERTICAL)
        sizerRaDecPane.Add(sizerRaDecPanelUpper, 1, wx.EXPAND)
        sizerRaDecPane.Add(self.__create_ra_dec_tracking_staticbox(notebookRaDecPane), 1, wx.EXPAND)


        notebookRaDecPane.SetSizer(sizerRaDecPane)
        return notebookRaDecPane

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
        calibrateStaticBox      = wx.StaticBox(parent, wx.ID_ANY, "Calibrate")
        azLabel                 = wx.StaticText(parent, wx.ID_ANY, "Az:")
        elLabel                 = wx.StaticText(parent, wx.ID_ANY, "El:")
        self.calibrate_az_input = wx.TextCtrl(parent, wx.ID_ANY, "")
        self.calibrate_el_input = wx.TextCtrl(parent, wx.ID_ANY, "")

        self.button_calibrate           = wx.Button(parent, wx.ID_ANY, "Calibrate")
        
        gridSizer = wx.FlexGridSizer(3,2)
        gridSizer.AddF(azLabel, self.sizerFlags)
        gridSizer.AddF(self.calibrate_az_input, self.sizerFlags)
        gridSizer.AddF(elLabel, self.sizerFlags)
        gridSizer.AddF(self.calibrate_el_input, self.sizerFlags)
        gridSizer.Add([1,1])
        gridSizer.AddF(self.button_calibrate, self.sizerFlags)

        baseSizer = wx.StaticBoxSizer(calibrateStaticBox, wx.VERTICAL)
        baseSizer.Add(gridSizer, 1, wx.EXPAND)

        return baseSizer

    def __create_absolute_move_pane(self, parent):

        absoluteMoveStaticBox      = wx.StaticBox(parent, wx.ID_ANY, "Absolute Move")
        azLabel                    = wx.StaticText(parent, wx.ID_ANY, "Az:")
        elLabel                    = wx.StaticText(parent, wx.ID_ANY, "El:")
        self.absolute_move_ctrl_az = wx.TextCtrl(parent, wx.ID_ANY, "0")
        self.absolute_move_ctrl_el = wx.TextCtrl(parent, wx.ID_ANY, "0")
        self.button_start_move     = wx.Button(parent, wx.ID_ANY, "Start Move")

        gridSizer = wx.FlexGridSizer(3,2)
        gridSizer.AddF(azLabel, self.sizerFlags)
        gridSizer.AddF(self.absolute_move_ctrl_az, self.sizerFlags)
        gridSizer.AddF(elLabel, self.sizerFlags)
        gridSizer.AddF(self.absolute_move_ctrl_el, self.sizerFlags)
        gridSizer.Add([1,1])
        gridSizer.AddF(self.button_start_move, self.sizerFlags)


        baseSizer = wx.StaticBoxSizer(absoluteMoveStaticBox, wx.VERTICAL)
        baseSizer.Add(gridSizer, 1, wx.EXPAND)

        return baseSizer

    def __create_index_button_pane(self, parent):
        axesIndexButtonsStaticBox = wx.StaticBox(parent, wx.ID_ANY, "Index")
        self.button_index_az      = wx.Button(parent, wx.ID_ANY, "Azimuth Axis")
        self.button_index_el      = wx.Button(parent, wx.ID_ANY, "Elevation Axis")

        baseSizer = wx.StaticBoxSizer(axesIndexButtonsStaticBox, wx.VERTICAL)
        baseSizer.Add(self.button_index_az, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.EXPAND)
        baseSizer.Add(self.button_index_el, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.EXPAND)

        return baseSizer


    def __create_joystick_pane(self):
        notebookJoystickPane = wx.Panel(self.controlNotebook)

        # The FlexGridSizer seems to have better rezise behavour when compressed then the 
        # plain GridSizer. Not sure why. 
        # Anyways, As such, I'm using a FlexGridSizer with all cells set to growable
        gridSizer = wx.FlexGridSizer(2,2)
        gridSizer.AddGrowableCol(0)
        gridSizer.AddGrowableCol(1)
        gridSizer.AddGrowableRow(0)
        gridSizer.AddGrowableRow(1)

        gridSizer.Add(self.__create_joystick_panel(notebookJoystickPane), 1, wx.EXPAND)
        gridSizer.Add(self.__create_absolute_move_pane(notebookJoystickPane), 1, wx.EXPAND)
        
        gridSizer.Add(self.__create_az_el_calibrate_panel(notebookJoystickPane), 1, wx.EXPAND)
        gridSizer.Add(self.__create_index_button_pane(notebookJoystickPane), 1, wx.EXPAND)
        
        notebookJoystickPane.SetSizer(gridSizer)

        return notebookJoystickPane

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
        horiz_sizer = wx.StaticBoxSizer(horiz_box, wx.VERTICAL)
        simple_sizer.Add(horiz_sizer, 1, wx.EXPAND)
        
        simple_panel.SetSizer(simple_sizer)
        return simple_panel

    # short scans: take the shortest angular distance between points
    def __create_scanning_pane(self):	
        # TODO: CLEANUP, name sizers sanely
        notebookScanningPane    = wx.Panel(self.controlNotebook)
        
        self.corner1_box        = wx.StaticBox(notebookScanningPane, wx.ID_ANY, "Corner 1")
        self.corner1_crda_label = wx.StaticText(notebookScanningPane, wx.ID_ANY, "A:")
        self.corner1_crda_box   = wx.TextCtrl(notebookScanningPane, wx.ID_ANY, "10")
        self.corner1_crdb_label = wx.StaticText(notebookScanningPane, wx.ID_ANY, "B:")
        self.corner1_crdb_box   = wx.TextCtrl(notebookScanningPane, wx.ID_ANY, "40")
        
        self.corner2_box        = wx.StaticBox(notebookScanningPane, wx.ID_ANY, "Corner 2")
        self.corner2_crda_label = wx.StaticText(notebookScanningPane, wx.ID_ANY, "A:")
        self.corner2_crda_box   = wx.TextCtrl(notebookScanningPane, wx.ID_ANY, "50")
        self.corner2_crdb_label = wx.StaticText(notebookScanningPane, wx.ID_ANY, "B:")
        self.corner2_crdb_box   = wx.TextCtrl(notebookScanningPane, wx.ID_ANY, "40")
        
        self.corner3_box        = wx.StaticBox(notebookScanningPane, wx.ID_ANY, "Corner 3")
        self.corner3_crda_label = wx.StaticText(notebookScanningPane, wx.ID_ANY, "A:")
        self.corner3_crda_box   = wx.TextCtrl(notebookScanningPane, wx.ID_ANY, "50")
        self.corner3_crdb_label = wx.StaticText(notebookScanningPane, wx.ID_ANY, "B:")
        self.corner3_crdb_box   = wx.TextCtrl(notebookScanningPane, wx.ID_ANY, "10")
        
        self.corner4_box        = wx.StaticBox(notebookScanningPane, wx.ID_ANY, "Corner 4")
        self.corner4_crda_label = wx.StaticText(notebookScanningPane, wx.ID_ANY, "A:")
        self.corner4_crda_box   = wx.TextCtrl(notebookScanningPane, wx.ID_ANY, "10")
        self.corner4_crdb_label = wx.StaticText(notebookScanningPane, wx.ID_ANY, "B:")
        self.corner4_crdb_box   = wx.TextCtrl(notebookScanningPane, wx.ID_ANY, "10")
        
        self.num_turns_label    = wx.StaticText(notebookScanningPane, wx.ID_ANY, "Num of Turns: ")
        self.num_turns_input    = wx.TextCtrl(notebookScanningPane, wx.ID_ANY, "5")
        self.scan_cycles_label  = wx.StaticText(notebookScanningPane, wx.ID_ANY, "Cycles to Run: ")
        self.scan_cycles_input  = wx.TextCtrl(notebookScanningPane, wx.ID_ANY, "1")
        self.scan_repeat_input  = wx.CheckBox(notebookScanningPane, wx.ID_ANY, "Repeat indefinitely")
        self.buttonScanStart    = wx.Button(notebookScanningPane, wx.ID_ANY, "Begin Scan")
        self.preview_scan       = wx.Button(notebookScanningPane, wx.ID_ANY, "Preview")

        coord_sys = ["Horizontal (A=Az, B=El)", "Equatorial (A=RA, B=DE)"]
        self.coordsys_selector = wx.ComboBox(notebookScanningPane, wx.ID_ANY,
            choices=coord_sys, style=wx.CB_DROPDOWN | wx.CB_READONLY)
        
        scanOptionsList = [func.__name__.capitalize() for func in scans.scan_list]
        self.comboBoxScanOptions = wx.ComboBox(notebookScanningPane, wx.ID_ANY,
            choices=scanOptionsList, style=wx.CB_DROPDOWN | wx.CB_READONLY)
        
        self.sizer_49_staticbox = wx.StaticBox(notebookScanningPane, wx.ID_ANY, "Scan Options")


        corner1_crda_sizer = wx.BoxSizer(wx.HORIZONTAL)
        corner1_crda_sizer.Add(self.corner1_crda_label)
        corner1_crda_sizer.Add(self.corner1_crda_box)

        corner1_crdb_sizer = wx.BoxSizer(wx.HORIZONTAL)
        corner1_crdb_sizer.Add(self.corner1_crdb_label)
        corner1_crdb_sizer.Add(self.corner1_crdb_box)
        
        corner1_sizer = wx.StaticBoxSizer(self.corner1_box, wx.VERTICAL)
        corner1_sizer.Add(corner1_crda_sizer, 1, wx.EXPAND)
        corner1_sizer.Add(corner1_crdb_sizer, 1, wx.EXPAND)
        
        corner2_crda_sizer = wx.BoxSizer(wx.HORIZONTAL)
        corner2_crda_sizer.Add(self.corner2_crda_label)
        corner2_crda_sizer.Add(self.corner2_crda_box)
                
        corner2_crdb_sizer = wx.BoxSizer(wx.HORIZONTAL)
        corner2_crdb_sizer.Add(self.corner2_crdb_label)
        corner2_crdb_sizer.Add(self.corner2_crdb_box)
        
        corner2_sizer = wx.StaticBoxSizer(self.corner2_box, wx.VERTICAL)
        corner2_sizer.Add(corner2_crda_sizer, 1, wx.EXPAND)
        corner2_sizer.Add(corner2_crdb_sizer, 1, wx.EXPAND)
        
        corner3_crda_sizer = wx.BoxSizer(wx.HORIZONTAL)
        corner3_crda_sizer.Add(self.corner3_crda_label)
        corner3_crda_sizer.Add(self.corner3_crda_box)
                
        corner3_crdb_sizer = wx.BoxSizer(wx.HORIZONTAL)
        corner3_crdb_sizer.Add(self.corner3_crdb_label)
        corner3_crdb_sizer.Add(self.corner3_crdb_box)
        
        corner3_sizer = wx.StaticBoxSizer(self.corner3_box, wx.VERTICAL)
        corner3_sizer.Add(corner3_crda_sizer, 1, wx.EXPAND)
        corner3_sizer.Add(corner3_crdb_sizer, 1, wx.EXPAND)
        
        corner4_crda_sizer = wx.BoxSizer(wx.HORIZONTAL)
        corner4_crda_sizer.Add(self.corner4_crda_label)
        corner4_crda_sizer.Add(self.corner4_crda_box)
                
        corner4_crdb_sizer = wx.BoxSizer(wx.HORIZONTAL)
        corner4_crdb_sizer.Add(self.corner4_crdb_label)
        corner4_crdb_sizer.Add(self.corner4_crdb_box)
        
        corner4_sizer = wx.StaticBoxSizer(self.corner4_box, wx.VERTICAL)
        corner4_sizer.Add(corner4_crda_sizer, 1, wx.EXPAND)
        corner4_sizer.Add(corner4_crdb_sizer, 1, wx.EXPAND)
        
        corners_sizer = wx.BoxSizer(wx.HORIZONTAL)
        corners_sizer.Add(corner1_sizer, 1, wx.EXPAND)
        corners_sizer.Add(corner2_sizer, 1, wx.EXPAND)
        corners_sizer.Add(corner3_sizer, 1, wx.EXPAND)
        corners_sizer.Add(corner4_sizer, 1, wx.EXPAND)
        
        turns_sizer = wx.BoxSizer(wx.HORIZONTAL)
        turns_sizer.Add(self.num_turns_label)
        turns_sizer.Add(self.num_turns_input)
        
        cycles_sizer = wx.BoxSizer(wx.HORIZONTAL)
        cycles_sizer.Add(self.scan_cycles_label)
        cycles_sizer.Add(self.scan_cycles_input)
        
        sizer_7_copy_4 = wx.BoxSizer(wx.VERTICAL)
        sizer_7_copy_4.Add(turns_sizer, 1, wx.EXPAND)
        sizer_7_copy_4.Add(cycles_sizer, 1, wx.EXPAND)
        sizer_7_copy_4.Add(self.scan_repeat_input)
        
        scan_select_sizer = wx.BoxSizer(wx.VERTICAL)
        scan_select_sizer.Add(self.coordsys_selector, 1, wx.EXPAND)
        scan_select_sizer.Add(self.comboBoxScanOptions, 1, wx.EXPAND)
        
        scan_button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        scan_button_sizer.Add(self.preview_scan, 1, wx.EXPAND)
        scan_button_sizer.Add(self.buttonScanStart, 1, wx.EXPAND)
        scan_select_sizer.Add(scan_button_sizer, 1, wx.EXPAND)
                
        sizer_49 = wx.StaticBoxSizer(self.sizer_49_staticbox, wx.HORIZONTAL)
        sizer_49.Add(sizer_7_copy_4, 1, wx.EXPAND)
        sizer_49.Add(scan_select_sizer, 1, wx.EXPAND)

        sizer_42 = wx.BoxSizer(wx.VERTICAL)
        sizer_42.Add(corners_sizer, 1, wx.EXPAND)
        sizer_42.Add(sizer_49, 1, wx.EXPAND)
        
        notebookScanningPane.SetSizer(sizer_42)

        return notebookScanningPane

    def __create_options_pane(self):
        notebookOptionsPane = wx.Panel(self.controlNotebook)
        
        scan_speed_label = wx.StaticText(notebookOptionsPane, wx.ID_ANY, "Speed (deg/s): ")
        self.scan_speed_input = wx.TextCtrl(notebookOptionsPane, wx.ID_ANY, "4")
        
        scan_accel_label = wx.StaticText(notebookOptionsPane, wx.ID_ANY, "Accel (deg/s^2):")
        self.scan_accel_input = wx.TextCtrl(notebookOptionsPane, wx.ID_ANY, "10")

        gridSizer = wx.FlexGridSizer(4,2)
        gridSizer.AddF(scan_speed_label, self.sizerFlags)
        gridSizer.AddF(self.scan_speed_input, self.sizerFlags)

        gridSizer.AddF(scan_accel_label, self.sizerFlags)
        gridSizer.AddF(self.scan_accel_input, self.sizerFlags)

        notebookOptionsPane.SetSizer(gridSizer)

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
        self.chart_fov = wx.SpinCtrl(self.sky_panel, value="90", min=1, max=180)
        ctrl_sizer.Add(self.chart_fov)
        
        # create OpenGL canvas
        self.sky_chart = Chart(self.sky_panel, self.chart_fov, self.converter)
        sky_sizer.Add(self.sky_chart, 1, wx.EXPAND)
        sky_sizer.Add(ctrl_sizer, 0, wx.EXPAND)
        
        self.sky_panel.SetSizer(sky_sizer)
        return self.sky_panel

    def __create_layout(self):
                
        headerSizer = wx.BoxSizer(wx.HORIZONTAL)

        headerSizer.Add(self.__create_readoutPanel(), proportion=1, flag=wx.EXPAND)
        headerSizer.Add(self.__create_chart(), proportion=2, flag=wx.EXPAND)
        headerSizer.Add(self.__create_controls_sizer(), proportion=1, flag=wx.EXPAND)
        
        footerSizer = wx.BoxSizer(wx.HORIZONTAL)
    
        self.controlNotebook = wx.Notebook(self, wx.ID_ANY, style=0)
        self.controlNotebook.AddPage(self.__create_joystick_pane(), "Joy Stick")
        self.controlNotebook.AddPage(self.__create_ra_dec_pane(), "RA/DEC")
        self.controlNotebook.AddPage(self.__create_simple_scans(), "Simple Scans ")
        self.controlNotebook.AddPage(self.__create_scanning_pane(), "Scanning ")
        self.controlNotebook.AddPage(self.__create_options_pane(), "Options")
        
        footerSizer.Add(self.__create_graphPanel(), proportion=1, flag=wx.EXPAND)
        footerSizer.Add(self.controlNotebook, proportion=2, flag=wx.EXPAND)
        
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        mainSizer.Add(headerSizer, proportion=1, flag=wx.EXPAND)
        mainSizer.Add(footerSizer, proportion=1, flag=wx.EXPAND)
        self.SetSizer(mainSizer)
        mainSizer.Fit(self)
        
        self.Layout()
        

def main():		# Shut up pylinter
    app = wx.App()
    mainFrame = TelescopeControlFrame(None, -1, "")
    app.SetTopWindow(mainFrame)
    mainFrame.Show()
    app.MainLoop()


if __name__ == "__main__":
    main()

