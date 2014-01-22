
import wx


class TelescopeControlFrame(wx.Frame):
	def __init__(self, *args, **kwds):
		kwds["style"] = wx.DEFAULT_FRAME_STYLE
		wx.Frame.__init__(self, *args, **kwds)


		self.__create_layout()
		self.__set_properties()

		self.Bind(wx.EVT_BUTTON, self.stop, self.button_stop_all)
		self.Bind(wx.EVT_BUTTON, self.stop, self.button_stop_az)
		self.Bind(wx.EVT_TOGGLEBUTTON, self.toggle_motor_state, self.buttton_az_motor)
		self.Bind(wx.EVT_BUTTON, self.stop, self.button_stop_el)
		self.Bind(wx.EVT_TOGGLEBUTTON, self.toggle_motor_state, self.button_el_motor)
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
		
	def __set_properties(self):
		self.SetTitle("Telescope Control Code")
		self.comboBoxScanOptions.SetSelection(0)
		
	def __create_readoutPanel(self):

		self.statusReadoutPanel                   = wx.Panel(self, wx.ID_ANY)
		
		self.statusReadoutPanel.SetDoubleBuffered(True)   # Fix text flickering by forcing the container to be double-buffered.

		self.az_status     = wx.StaticText(self.statusReadoutPanel, wx.ID_ANY, "Az: 0.00 Degrees")
		self.el_status     = wx.StaticText(self.statusReadoutPanel, wx.ID_ANY, "El: 0.00 Degrees")
		self.ra_status     = wx.StaticText(self.statusReadoutPanel, wx.ID_ANY, "Ra: 0.00 Degrees")
		self.dec_status    = wx.StaticText(self.statusReadoutPanel, wx.ID_ANY, "Dec: 0.00 Degrees")
		self.utc_status    = wx.StaticText(self.statusReadoutPanel, wx.ID_ANY, "Utc: 0.00")
		self.lst_status    = wx.StaticText(self.statusReadoutPanel, wx.ID_ANY, "Lst: 0.00")
		self.local_status  = wx.StaticText(self.statusReadoutPanel, wx.ID_ANY, "Local: 0.00")
		self.packet_num  = wx.StaticText(self.statusReadoutPanel, wx.ID_ANY, "RX Pkts: 0 (if you can see this,\nsomething is broken)")

		textItems = [self.az_status, 
					self.el_status, 
					self.ra_status, 
					self.dec_status, 
					self.utc_status, 
					self.lst_status, 
					self.local_status, 
					self.packet_num]


		for item in textItems:
			item.SetFont(wx.Font(12, wx.DEFAULT, wx.NORMAL, wx.NORMAL, 0, "MS Shell Dlg 2"))

		self.statusSizerStaticbox = wx.StaticBox(self.statusReadoutPanel, wx.ID_ANY, "Status")
		sizer = wx.StaticBoxSizer(self.statusSizerStaticbox, wx.VERTICAL)
		sizer.AddMany(textItems)

		sizer.Insert(len(textItems)-1, [10, 10], proportion=1, flag=wx.EXPAND)
		self.statusReadoutPanel.SetSizer(sizer)

		return self.statusReadoutPanel

	def __create_controls_sizer(self):

		self.controlButtonPanel                   = wx.Panel(self, wx.ID_ANY)

		self.button_stop_all          = wx.Button(self.controlButtonPanel, wx.ID_ANY, "Stop All")
		self.button_stop_az           = wx.Button(self.controlButtonPanel, wx.ID_ANY, "Stop AZ")
		self.buttton_az_motor         = wx.ToggleButton(self.controlButtonPanel, wx.ID_ANY, "AZ Motor On")
		self.button_goto_balloon      = wx.Button(self.controlButtonPanel, wx.ID_ANY, "Goto Balloon")
		self.button_stop_el           = wx.Button(self.controlButtonPanel, wx.ID_ANY, "Stop EL")
		self.button_el_motor          = wx.ToggleButton(self.controlButtonPanel, wx.ID_ANY, "EL Motor On")

		gridSizer = wx.GridSizer(rows=3, cols=2)

		items = [self.button_stop_all, self.button_stop_az, self.buttton_az_motor, self.button_goto_balloon, self.button_stop_el, self.button_el_motor]
		for item in items:
			gridSizer.Add(item, proportion=0, flag=wx.ALIGN_CENTER_HORIZONTAL|wx.EXPAND)
		
		
		self.controlButtonsStaticBox        = wx.StaticBox(self.controlButtonPanel, wx.ID_ANY, "Universal Controls")
		sizer = wx.StaticBoxSizer(self.controlButtonsStaticBox, wx.HORIZONTAL)
		sizer.Add(gridSizer, 1, 0)


		self.controlButtonPanel.SetSizer(sizer)

		return self.controlButtonPanel

	def __create_ra_dec_pane(self):
		# TODO: CLEANUP, name sizers sanely
		self.notebookRaDecPane                    = wx.Panel(self.controlNotebook, wx.ID_ANY)
		self.label_1                              = wx.StaticText(self.notebookRaDecPane, wx.ID_ANY, "Ra: ")
		self.textCtrlGotoRightAscension           = wx.TextCtrl(self.notebookRaDecPane, wx.ID_ANY, "")
		self.label_2                              = wx.StaticText(self.notebookRaDecPane, wx.ID_ANY, "Dec:")
		self.textCtrlGotoDeclination              = wx.TextCtrl(self.notebookRaDecPane, wx.ID_ANY, "")
		self.buttonGotoPosition                   = wx.Button(self.notebookRaDecPane, wx.ID_ANY, "Goto Position")
		self.sizer_6_staticbox                    = wx.StaticBox(self.notebookRaDecPane, wx.ID_ANY, "Goto Ra/Dec")
		self.label_1_copy                         = wx.StaticText(self.notebookRaDecPane, wx.ID_ANY, "Ra: ")
		self.textCtrlRightAscensionCalInput       = wx.TextCtrl(self.notebookRaDecPane, wx.ID_ANY, "")
		self.label_2_copy                         = wx.StaticText(self.notebookRaDecPane, wx.ID_ANY, "Dec:")
		self.textCtrlDeclinationCalInput          = wx.TextCtrl(self.notebookRaDecPane, wx.ID_ANY, "")
		self.buttonDoRaDecCalibrate               = wx.Button(self.notebookRaDecPane, wx.ID_ANY, "Calibrate")
		self.sizer_16_staticbox                   = wx.StaticBox(self.notebookRaDecPane, wx.ID_ANY, "Calibrate Ra/Dec")
		self.label_1_copy_1                       = wx.StaticText(self.notebookRaDecPane, wx.ID_ANY, "Ra: ")
		self.textCtrlTrackingRightAscension       = wx.TextCtrl(self.notebookRaDecPane, wx.ID_ANY, "")
		self.label_2_copy_1                       = wx.StaticText(self.notebookRaDecPane, wx.ID_ANY, "Dec:")
		self.textCtrlTrackingDeclination          = wx.TextCtrl(self.notebookRaDecPane, wx.ID_ANY, "")
		self.buttonTrackPosition                  = wx.Button(self.notebookRaDecPane, wx.ID_ANY, "Track Position")
		self.buttonTrackingToggle                 = wx.ToggleButton(self.notebookRaDecPane, wx.ID_ANY, "Tracking On")
		self.sizer_17_staticbox                   = wx.StaticBox(self.notebookRaDecPane, wx.ID_ANY, "Ra/Dec Tracking")


		sizer_13 = wx.BoxSizer(wx.HORIZONTAL)
		sizer_13.Add(self.label_1)
		sizer_13.Add(self.textCtrlGotoRightAscension)

		sizer_14 = wx.BoxSizer(wx.HORIZONTAL)
		sizer_14.Add(self.label_2)
		sizer_14.Add(self.textCtrlGotoDeclination)
		

		sizer_6 = wx.StaticBoxSizer(self.sizer_6_staticbox, wx.VERTICAL)
		sizer_6.Add(sizer_13, 1, wx.EXPAND)
		sizer_6.Add(sizer_14, 1, wx.EXPAND)
		sizer_6.Add(self.buttonGotoPosition)

		sizer_13_copy = wx.BoxSizer(wx.HORIZONTAL)
		sizer_13_copy.Add(self.label_1_copy)
		sizer_13_copy.Add(self.textCtrlRightAscensionCalInput)

		sizer_14_copy = wx.BoxSizer(wx.HORIZONTAL)
		sizer_14_copy.Add(self.label_2_copy)
		sizer_14_copy.Add(self.textCtrlDeclinationCalInput)
		
		
		sizer_16 = wx.StaticBoxSizer(self.sizer_16_staticbox, wx.VERTICAL)
		sizer_16.Add(sizer_13_copy, 1, wx.EXPAND)
		sizer_16.Add(sizer_14_copy, 1, wx.EXPAND)
		sizer_16.Add(self.buttonDoRaDecCalibrate)
		
		sizer_5 = wx.BoxSizer(wx.HORIZONTAL)
		sizer_5.Add(sizer_6, 1, wx.EXPAND)
		sizer_5.Add(sizer_16, 1, wx.EXPAND)

		sizer_13_copy_1 = wx.BoxSizer(wx.HORIZONTAL)
		sizer_13_copy_1.Add(self.label_1_copy_1)
		sizer_13_copy_1.Add(self.textCtrlTrackingRightAscension, 0, wx.LEFT)

		sizer_14_copy_1 = wx.BoxSizer(wx.HORIZONTAL)
		sizer_14_copy_1.Add(self.label_2_copy_1)
		sizer_14_copy_1.Add(self.textCtrlTrackingDeclination)
		
		sizer_22 = wx.BoxSizer(wx.HORIZONTAL)
		sizer_22.Add(self.buttonTrackPosition)
		sizer_22.Add((90, 20), proportion=1)
		sizer_22.Add(self.buttonTrackingToggle)
				
		sizer_17 = wx.StaticBoxSizer(self.sizer_17_staticbox, wx.VERTICAL)
		sizer_17.Add(sizer_13_copy_1, 1, wx.EXPAND)
		sizer_17.Add(sizer_14_copy_1, 1, wx.EXPAND)
		sizer_17.Add(sizer_22, 1, wx.EXPAND)
		
		sizer_1 = wx.BoxSizer(wx.VERTICAL)
		sizer_1.Add(sizer_5, 1, wx.EXPAND)
		sizer_1.Add(sizer_17, 1, wx.EXPAND)


		self.notebookRaDecPane.SetSizer(sizer_1)
		return self.notebookRaDecPane

	def __create_joystick_pane(self):	
		# TODO: CLEANUP, name sizers sanely
		self.notebookJoystickPane                 = wx.Panel(self.controlNotebook, wx.ID_ANY)
		self.step_size_input                      = wx.TextCtrl(self.notebookJoystickPane, wx.ID_ANY, "", style=wx.TE_PROCESS_ENTER)
		self.label_6                              = wx.StaticText(self.notebookJoystickPane, wx.ID_ANY, "Degrees")
		self.button_up                            = wx.Button(self.notebookJoystickPane, wx.ID_ANY, "^")
		self.button_left                          = wx.Button(self.notebookJoystickPane, wx.ID_ANY, "<")
		self.button_right                         = wx.Button(self.notebookJoystickPane, wx.ID_ANY, ">")
		self.button_down                          = wx.Button(self.notebookJoystickPane, wx.ID_ANY, "v")
		self.sizer_21_staticbox                   = wx.StaticBox(self.notebookJoystickPane, wx.ID_ANY, "Relative Move")
		self.label_7                              = wx.StaticText(self.notebookJoystickPane, wx.ID_ANY, "AZ")
		self.ctrl_az                              = wx.TextCtrl(self.notebookJoystickPane, wx.ID_ANY, "")
		self.label_8                              = wx.StaticText(self.notebookJoystickPane, wx.ID_ANY, "EL")
		self.ctrl_el                              = wx.TextCtrl(self.notebookJoystickPane, wx.ID_ANY, "")
		self.button_start_move                    = wx.Button(self.notebookJoystickPane, wx.ID_ANY, "Start Move")
		self.sizer_32_staticbox                   = wx.StaticBox(self.notebookJoystickPane, wx.ID_ANY, "Absolute Move")
		self.label_9                              = wx.StaticText(self.notebookJoystickPane, wx.ID_ANY, "AZ")
		self.calibrate_az_input                   = wx.TextCtrl(self.notebookJoystickPane, wx.ID_ANY, "")
		self.label_10                             = wx.StaticText(self.notebookJoystickPane, wx.ID_ANY, "EL")
		self.calibrate_el_input                   = wx.TextCtrl(self.notebookJoystickPane, wx.ID_ANY, "")
		self.button_calibrate                     = wx.Button(self.notebookJoystickPane, wx.ID_ANY, "Calibrate")
		self.sizer_36_staticbox                   = wx.StaticBox(self.notebookJoystickPane, wx.ID_ANY, "Calibrate")
		self.button_index_az                      = wx.Button(self.notebookJoystickPane, wx.ID_ANY, "AZ")
		self.button_index_el                      = wx.Button(self.notebookJoystickPane, wx.ID_ANY, "EL")
		self.sizer_37_staticbox                   = wx.StaticBox(self.notebookJoystickPane, wx.ID_ANY, "Index")

		sizer_24 = wx.BoxSizer(wx.HORIZONTAL)
		sizer_24.Add(self.step_size_input)
		sizer_24.Add(self.label_6)

		leftRightButtonSizer = wx.BoxSizer(wx.HORIZONTAL)
		leftRightButtonSizer.Add(self.button_left, 0, wx.EXPAND)
		leftRightButtonSizer.Add([1,1], 1, wx.EXPAND)
		leftRightButtonSizer.Add(self.button_right, 0, wx.EXPAND)
		
		sizer_21 = wx.StaticBoxSizer(self.sizer_21_staticbox, wx.VERTICAL)
		sizer_21.Add(sizer_24, 1, wx.EXPAND)
		sizer_21.Add(self.button_up, 0, wx.ALIGN_CENTER_HORIZONTAL)
		sizer_21.Add(leftRightButtonSizer, 1, wx.EXPAND)
		sizer_21.Add(self.button_down, 0, wx.ALIGN_CENTER_HORIZONTAL)

		sizer_34 = wx.BoxSizer(wx.HORIZONTAL)
		sizer_34.Add(self.label_7)
		sizer_34.Add(self.ctrl_az)
		sizer_34.Add(self.label_8)
		sizer_34.Add(self.ctrl_el)

		sizer_32 = wx.StaticBoxSizer(self.sizer_32_staticbox, wx.VERTICAL)
		sizer_32.Add(sizer_34, 1, wx.EXPAND)
		sizer_32.Add(self.button_start_move)
		
		sizer_20 = wx.BoxSizer(wx.HORIZONTAL)
		sizer_20.Add(sizer_21, 1, wx.EXPAND)
		sizer_20.Add(sizer_32, 1, wx.ALIGN_CENTER_HORIZONTAL|wx.EXPAND)
		
		sizer_39 = wx.BoxSizer(wx.HORIZONTAL)
		sizer_39.Add(self.label_9)
		sizer_39.Add(self.calibrate_az_input)
		sizer_39.Add(self.label_10)
		sizer_39.Add(self.calibrate_el_input)
		
		sizer_36 = wx.StaticBoxSizer(self.sizer_36_staticbox, wx.VERTICAL)
		sizer_36.Add(sizer_39, 1, wx.EXPAND)
		sizer_36.Add(self.button_calibrate, 0, wx.EXPAND)
		
		sizer_37 = wx.StaticBoxSizer(self.sizer_37_staticbox, wx.HORIZONTAL)
		sizer_37.Add(self.button_index_az, 1, wx.ALIGN_CENTER_HORIZONTAL)
		sizer_37.Add(self.button_index_el, 1, wx.ALIGN_CENTER_HORIZONTAL)
		
		sizer_35 = wx.BoxSizer(wx.HORIZONTAL)
		sizer_35.Add(sizer_36, 1, wx.EXPAND)
		sizer_35.Add(sizer_37, 1, wx.EXPAND)
		
		sizer_19 = wx.BoxSizer(wx.VERTICAL)
		sizer_19.Add(sizer_20, 1, wx.EXPAND)
		sizer_19.Add(sizer_35, 1, wx.EXPAND)
		
		self.notebookJoystickPane.SetSizer(sizer_19)



		return self.notebookJoystickPane

	def __create_scanning_pane(self):	
		# TODO: CLEANUP, name sizers sanely
		self.notebookScanningPane                 = wx.Panel(self.controlNotebook, wx.ID_ANY)
		self.label_1_copy_2                       = wx.StaticText(self.notebookScanningPane, wx.ID_ANY, "Min: ")
		self.textCtrlScanMinAz                    = wx.TextCtrl(self.notebookScanningPane, wx.ID_ANY, "")
		self.label_2_copy_2                       = wx.StaticText(self.notebookScanningPane, wx.ID_ANY, "Max:")
		self.textCtrlScanMaxAz                    = wx.TextCtrl(self.notebookScanningPane, wx.ID_ANY, "")
		self.sizer_44_staticbox                   = wx.StaticBox(self.notebookScanningPane, wx.ID_ANY, "Az")
		self.label_1_copy_3                       = wx.StaticText(self.notebookScanningPane, wx.ID_ANY, "Min: ")
		self.textCtrlScanMinEl                    = wx.TextCtrl(self.notebookScanningPane, wx.ID_ANY, "")
		self.label_2_copy_3                       = wx.StaticText(self.notebookScanningPane, wx.ID_ANY, "Max:")
		self.textCtrlScanMaxEl                    = wx.TextCtrl(self.notebookScanningPane, wx.ID_ANY, "")
		self.sizer_45_staticbox                   = wx.StaticBox(self.notebookScanningPane, wx.ID_ANY, "El")
		self.label_scan_period                    = wx.StaticText(self.notebookScanningPane, wx.ID_ANY, "Period:")
		self.scan_period_input                    = wx.TextCtrl(self.notebookScanningPane, wx.ID_ANY, "")
		self.label_scan_cycles                    = wx.StaticText(self.notebookScanningPane, wx.ID_ANY, "Cycles:")
		self.scan_cycles_input                    = wx.TextCtrl(self.notebookScanningPane, wx.ID_ANY, "")
		self.scan_continuous_input                = wx.CheckBox(self.notebookScanningPane, wx.ID_ANY, "Continuous")
		self.checkbox_radec                       = wx.CheckBox(self.notebookScanningPane, wx.ID_ANY, "Ra/Dec")
		self.buttonScanStart                      = wx.Button(self.notebookScanningPane, wx.ID_ANY, "Scan")

		scanOptionsList = ["Azimuth", "Elevation", "Square", "Serpentine", "Spin"]
		self.comboBoxScanOptions                  = wx.ComboBox(self.notebookScanningPane, wx.ID_ANY, choices=scanOptionsList, style=wx.CB_DROPDOWN | wx.CB_READONLY)
		
		self.sizer_49_staticbox                   = wx.StaticBox(self.notebookScanningPane, wx.ID_ANY, "Scan Options")




		sizer_13_copy_2 = wx.BoxSizer(wx.HORIZONTAL)
		sizer_13_copy_2.Add(self.label_1_copy_2)
		sizer_13_copy_2.Add(self.textCtrlScanMinAz)

		sizer_14_copy_2 = wx.BoxSizer(wx.HORIZONTAL)
		sizer_14_copy_2.Add(self.label_2_copy_2)
		sizer_14_copy_2.Add(self.textCtrlScanMaxAz)
		
		sizer_44 = wx.StaticBoxSizer(self.sizer_44_staticbox, wx.VERTICAL)
		sizer_44.Add(sizer_13_copy_2, 1, wx.EXPAND)
		sizer_44.Add(sizer_14_copy_2, 1, wx.EXPAND)
		
		sizer_13_copy_3 = wx.BoxSizer(wx.HORIZONTAL)
		sizer_13_copy_3.Add(self.label_1_copy_3)
		sizer_13_copy_3.Add(self.textCtrlScanMinEl)
				
		sizer_14_copy_3 = wx.BoxSizer(wx.HORIZONTAL)
		sizer_14_copy_3.Add(self.label_2_copy_3)
		sizer_14_copy_3.Add(self.textCtrlScanMaxEl)
		
		sizer_45 = wx.StaticBoxSizer(self.sizer_45_staticbox, wx.VERTICAL)
		sizer_45.Add(sizer_13_copy_3, 1, wx.EXPAND)
		sizer_45.Add(sizer_14_copy_3, 1, wx.EXPAND)
		
		sizer_43 = wx.BoxSizer(wx.HORIZONTAL)
		sizer_43.Add(sizer_44, 1, wx.EXPAND)
		sizer_43.Add(sizer_45, 1, wx.EXPAND)
		
		sizer_13_copy_4 = wx.BoxSizer(wx.HORIZONTAL)
		sizer_13_copy_4.Add(self.label_scan_period)
		sizer_13_copy_4.Add(self.scan_period_input)
		
		sizer_14_copy_4 = wx.BoxSizer(wx.HORIZONTAL)
		sizer_14_copy_4.Add(self.label_scan_cycles)
		sizer_14_copy_4.Add(self.scan_cycles_input)
		
		sizer_7_copy_4 = wx.BoxSizer(wx.VERTICAL)
		sizer_7_copy_4.Add(sizer_13_copy_4, 1, wx.EXPAND)
		sizer_7_copy_4.Add(sizer_14_copy_4, 1, wx.EXPAND)
		sizer_7_copy_4.Add(self.scan_continuous_input)
		sizer_7_copy_4.Add(self.checkbox_radec)
		
		sizer_51 = wx.BoxSizer(wx.HORIZONTAL)
		sizer_51.Add(self.buttonScanStart)
		sizer_51.Add(self.comboBoxScanOptions)
				
		sizer_49 = wx.StaticBoxSizer(self.sizer_49_staticbox, wx.HORIZONTAL)
		sizer_49.Add(sizer_7_copy_4, 1, wx.EXPAND)
		sizer_49.Add(sizer_51, 1, wx.EXPAND)

		sizer_42 = wx.BoxSizer(wx.VERTICAL)
		sizer_42.Add(sizer_43, 1, wx.EXPAND)
		sizer_42.Add(sizer_49, 1, wx.EXPAND)
		
		self.notebookScanningPane.SetSizer(sizer_42)


		
		return self.notebookScanningPane

	def __create_options_pane(self):	
		# TODO: CLEANUP, name sizers sanely

		self.notebookOptionsPane                  = wx.Panel(self.controlNotebook, wx.ID_ANY)
		self.label_1_copy_5                       = wx.StaticText(self.notebookOptionsPane, wx.ID_ANY, "Velocity:       ")  # TODO: Fix this padding issue by using proper sizer structures
		self.ctrl_velocity                        = wx.TextCtrl(self.notebookOptionsPane, wx.ID_ANY, "")
		self.label_2_copy_5                       = wx.StaticText(self.notebookOptionsPane, wx.ID_ANY, "Acceleration:")
		self.ctrl_acceleration                    = wx.TextCtrl(self.notebookOptionsPane, wx.ID_ANY, "")
		self.button_set_accel_vel                 = wx.Button(self.notebookOptionsPane, wx.ID_ANY, "Set Accel/Vel")
		self.radio_btn_az                         = wx.RadioButton(self.notebookOptionsPane, wx.ID_ANY, "AZ")
		self.radio_btn_el                         = wx.RadioButton(self.notebookOptionsPane, wx.ID_ANY, "EL")
		self.button_open_config                   = wx.Button(self.notebookOptionsPane, wx.ID_ANY, "Open Config File")
		self.panel_5                              = wx.Panel(self.notebookOptionsPane, wx.ID_ANY)
		self.sizer_52_staticbox                   = wx.StaticBox(self.notebookOptionsPane, wx.ID_ANY, "Move Options")


		sizer_13_copy_5 = wx.BoxSizer(wx.HORIZONTAL)
		sizer_13_copy_5.Add(self.label_1_copy_5)
		sizer_13_copy_5.Add(self.ctrl_velocity)

		sizer_14_copy_5 = wx.BoxSizer(wx.HORIZONTAL)
		sizer_14_copy_5.Add(self.label_2_copy_5)
		sizer_14_copy_5.Add(self.ctrl_acceleration)
		
		sizer_7_copy_5 = wx.BoxSizer(wx.VERTICAL)
		sizer_7_copy_5.Add(sizer_13_copy_5, 1, wx.EXPAND)
		sizer_7_copy_5.Add(sizer_14_copy_5, 1, wx.EXPAND)
		sizer_7_copy_5.Add(self.button_set_accel_vel)
		
		sizer_54_copy = wx.BoxSizer(wx.VERTICAL)
		sizer_54_copy.Add(self.radio_btn_az)
		sizer_54_copy.Add(self.radio_btn_el)

		sizer_53 = wx.BoxSizer(wx.HORIZONTAL)
		sizer_53.Add(sizer_7_copy_5, 1, wx.EXPAND)
		sizer_53.Add(sizer_54_copy, 1, wx.EXPAND)
		
		
		sizer_52 = wx.StaticBoxSizer(self.sizer_52_staticbox, wx.VERTICAL)
		sizer_52.Add(sizer_53, 1, wx.EXPAND)
		sizer_52.Add(self.button_open_config)
		sizer_52.Add(self.panel_5, 1, wx.EXPAND)

		self.notebookOptionsPane.SetSizer(sizer_52)

		return self.notebookOptionsPane

	def __create_graphPanel(self):
		self.graphDisplayPanel                    = wx.Panel(self, wx.ID_ANY)
		self.graphPanelStaticbox                  = wx.StaticBox(self.graphDisplayPanel, wx.ID_ANY, "Graph")

		graphPanelSizer = wx.StaticBoxSizer(self.graphPanelStaticbox, wx.HORIZONTAL)
		self.graphDisplayPanel.SetSizer(graphPanelSizer)
		
		return self.graphDisplayPanel

	def __create_layout(self):
				
		headerSizer = wx.BoxSizer(wx.HORIZONTAL)

		headerSizer.Add(self.__create_readoutPanel(), proportion=1, flag=wx.EXPAND)
		headerSizer.Add(self.__create_graphPanel(), proportion=1, flag=wx.EXPAND)
		headerSizer.Add(self.__create_controls_sizer(), proportion=1, flag=wx.EXPAND)
	
		self.controlNotebook = wx.Notebook(self, wx.ID_ANY, style=0)
		self.controlNotebook.AddPage(self.__create_joystick_pane(), "Joy Stick")
		self.controlNotebook.AddPage(self.__create_ra_dec_pane(), "RA/DEC")
		self.controlNotebook.AddPage(self.__create_scanning_pane(), "Scanning ")
		self.controlNotebook.AddPage(self.__create_options_pane(), "Options")
		
		mainSizer = wx.BoxSizer(wx.VERTICAL)
		mainSizer.Add(headerSizer, proportion=1, flag=wx.EXPAND)
		mainSizer.Add(self.controlNotebook, proportion=1, flag=wx.EXPAND)
		self.SetSizer(mainSizer)
		mainSizer.Fit(self)
		
		self.Layout()
		

	def stop(self, event):  # wxGlade: TelescopeControlFrame.<event_handler>
		pass

	def toggle_motor_state(self, event):  # wxGlade: TelescopeControlFrame.<event_handler>
		pass

	def set_step_size(self, event):  # wxGlade: TelescopeControlFrame.<event_handler>
		pass

	def move_rel(self, event):  # wxGlade: TelescopeControlFrame.<event_handler>
		pass

	def move_abs(self, event):  # wxGlade: TelescopeControlFrame.<event_handler>
		pass

	def goto(self, event):  # wxGlade: TelescopeControlFrame.<event_handler>
		pass

	def calibrate(self, event):  # wxGlade: TelescopeControlFrame.<event_handler>
		pass

	def track_radec(self, event):  # wxGlade: TelescopeControlFrame.<event_handler>
		pass

	def scan(self, event):  # wxGlade: TelescopeControlFrame.<event_handler>
		pass
