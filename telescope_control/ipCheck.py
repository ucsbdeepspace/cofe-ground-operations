try:
    import configparser
except:
    import ConfigParser as configparser

import wx
import sys
import globalConf

import socket

import traceback

class MyFrame(wx.Frame):

    def __init__(self, * args, ** kwds):
        # begin wxGlade: MyFrame.__init__
        kwds["style"] = wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, * args, ** kwds)

        self.__set_properties()
        self.__do_layout()

        self.ipOK = False
        
        self.config = configparser.ConfigParser()
        self.config.read("config.ini")
        self.ipTextCtrl.SetValue(self.config.get("connection", "ip"))

        self.Bind(wx.EVT_CLOSE, self.quitApp)
        # end wxGlade

    def __set_properties(self):
        # begin wxGlade: MyFrame.__set_properties
        self.SetTitle("Controller IP Setup")
        self.SetSize((600, 110))
        self.SetBackgroundColour(wx.SystemSettings_GetColour(wx.SYS_COLOUR_BTNFACE))
        # end wxGlade

    def __mainPanel(self):
        ipEntrySizer = wx.BoxSizer(wx.HORIZONTAL)

        self.ipWindowStaticText = wx.StaticText(self, -1, "Galil Controller IP: ")
        ipEntrySizer.Add(self.ipWindowStaticText, 0, wx.ALL, 5)

        self.ipTextCtrl = wx.TextCtrl(self, -1, "", style = wx.TE_PROCESS_ENTER)
        self.ipTextCtrl.Bind(wx.EVT_TEXT_ENTER, self.evtIpEnter)
        
        textCtrlFont = wx.Font(10, wx.MODERN, wx.NORMAL, wx.NORMAL, False, u'Consolas')
        self.ipTextCtrl.SetFont(textCtrlFont)
        ipEntrySizer.Add(self.ipTextCtrl, 1, wx.ALL | wx.EXPAND, 3)

        self.selectIpButton = wx.Button(self, -1, "Ok")
        self.selectIpButton.SetDefault()
        ipEntrySizer.Add(self.selectIpButton, 0, wx.ALL, 3)
        self.selectIpButton.Bind(wx.EVT_BUTTON, self.evtIpEnter)

        return ipEntrySizer

    def __subPanel(self):

        statusSizer = wx.BoxSizer(wx.HORIZONTAL)

        self.noticeText = wx.StaticText(self, -1, "Please Enter Galil Controller IP", name = "")
        statusSizer.Add(self.noticeText, 1, wx.ALL|wx.EXPAND, 5)

        self.fakeGalilCheckbox = wx.CheckBox(self, style = wx.ALIGN_CENTRE, label = "Fake Galil")
        self.fakeGalilCheckbox.SetValue(True)
        globalConf.fakeGalil = self.fakeGalilCheckbox.IsChecked()
        self.fakeGalilCheckbox.Bind(wx.EVT_CHECKBOX, self.changeFakeGalilState)
        statusSizer.Add(self.fakeGalilCheckbox, 0, wx.ALL, 5)

        return statusSizer
    
    def __do_layout(self):
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        mainSizer.Add(self.__mainPanel(), 0, wx.EXPAND, 0)
        mainSizer.Add(self.__subPanel(), 1, wx.EXPAND | wx.ALL, 5)

        self.SetSizer(mainSizer)
        self.Layout()

    def changeFakeGalilState(self, event):
        globalConf.fakeGalil = self.fakeGalilCheckbox.IsChecked()
        if not self.fakeGalilCheckbox.IsChecked():
            self.ipOK = False
            self.evtIpEnter(None)

    def evtIpEnter(self, event):
        self.noticeText.SetLabel("Checking IP")
        wx.GetApp().Yield()
        ipAddress = self.ipTextCtrl.GetValue()
        
        port = int(self.config.get("connection", "port"))
        globalConf.galilPort = port

        if self.fakeGalilCheckbox.IsChecked():
            self.ipOK = True
            self.Destroy()
        elif len(ipAddress.split(".")) == 4:
            try:
                con = socket.create_connection((ipAddress, port+1), 1)
                con.shutdown(socket.SHUT_RDWR)
                con.close()

                self.noticeText.SetLabel("IP Valid")
                self.ipOK = True

                self.config.set("connection", "ip", str(ipAddress))
                with open("config.ini", "w") as configfile:
                    self.config.write(configfile)

                self.Destroy()
            except socket.timeout:
                traceback.print_exc()
                self.noticeText.SetLabel("Failed to open connection. Are you sure the IP is correct?")
            globalConf.galilIP = ipAddress
            
        else:
            self.noticeText.SetLabel("Error: Invalid IP")


    def quitApp(self, event): # wxGlade: MainFrame.<event_handler>
        print "Exiting"

        if self.ipOK:

            self.Destroy()
        else:
            sys.exit()



class IpChecker(wx.App):
    def OnInit(self):
        #wx.InitAllImageHandlers()
        mainFrame = MyFrame(None, -1, "")
        self.SetTopWindow(mainFrame)
        mainFrame.Show()
        return 1

