########################################################################################################################
# Volume Tab for use with sonospyGUI.py
########################################################################################################################
# virtualsTab.py copyright (c) 2010-2016 John Chowanec
# mutagen copyright (c) 2005 Joe Wreschnig, Michael Urman (mutagen is Licensed under GPL version 2.0)
# Sonospy Project copyright (c) 2010-2014 Mark Henkelis
#   (specifics for this file: scan.py)
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# virtualsTab.py Author: John Chowanec <chowanec@gmail.com>
########################################################################################################################
# TO DO:
# - Remove zones with fixed volume = true
# - Do not parse zones with <no zone found> -- since I am not relying on Sonospy for this anymore
#   I don't need zoneNAME, but I don't know how to parse the upnp stuff yet.
# - Gray out panel when volMon is active so people can't tweak thing
########################################################################################################################
# IMPORTS FOR PYTHON
########################################################################################################################
import wx
import re
import os
import subprocess
from threading import *
import guiFunctions
from wx.lib.pubsub import setuparg1
from wx.lib.pubsub import pub
import urllib
import socket
import sys
import time
import threading
import datetime
cmd_folder = os.path.dirname(os.path.abspath(__file__))
if cmd_folder not in sys.path:
    sys.path.insert(0, cmd_folder)



# Global Vars -------------------------------------------------------------------------------------------------------------------
list_checkboxIDNames = []                                                                   # Used later to store check box ids for retrieval
zonesToMonitor = []                                                                         # Global for storing zones to monitor.
maxVolPerZone = []                                                                          # Global to store max vol per zone checked.                                                                 
portNum = guiFunctions.configMe("INI", "controlpoint_port", file="../pycpoint.ini")         # Setting static port num -- can get this from pycpoint.ini
ip_address = guiFunctions.configMe("volume", "serverIP")                                    # get IP address of target server.
zoneNAME = []                                                                               # Getting active zones from Sonospy
debugMe=False                                                                               # Set to TRUE to turn on debug logging.
running=False
# -------------------------------------------------------------------------------------------------------------------------------



def EVT_RESULT(win, func):
    """Define Result Event."""
    win.Connect(-1, -1, EVT_RESULT_ID, func)
            
class ResultEvent(wx.PyEvent):
    """Simple event to carry arbitrary result data."""
    def __init__(self, data):
        """Init Result Event."""
        wx.PyEvent.__init__(self)
        self.SetEventType(EVT_RESULT_ID)
        self.data = data      

class WorkerThread(Thread):
    """Worker Thread Class."""
    def __init__(self):
        """Init Worker Thread Class."""
        Thread.__init__(self)
        self.ToKill = False
        self._want_abort = 0
        self.start()

    def run(self):
        """Run Worker Thread."""
        global running
        pass


########################################################################################################################
# VolumePanel: The layout and binding section for the frame.
########################################################################################################################
class VolumePanel(wx.Panel):
    """
    Volume Tab for creating subset databases.
    """
    #----------------------------------------------------------------------
    def __init__(self, parent):
        """"""
        wx.Panel.__init__(self, parent=parent, id=wx.ID_ANY)

        panel = self
        sizer = wx.GridBagSizer(13, 4)
        self.currentDirectory = os.getcwd()

        xIndex = 0
        curZoneNum = 0

        # SIZER VARIABLES - REFERENCED BELOW
        border = 5
        volDim = 32,20
        timeDim = 45,20
        sliderWidthHeight = 168, 5
        flag = wx.LEFT|wx.ALIGN_CENTER_VERTICAL
        sliderFlag = wx.LEFT|wx.EXPAND|wx.ALIGN_CENTER_VERTICAL

    # -------------------------------------------------------------------------
    # [1] - Server IP address and Port
        global zoneNAME
        
        label_serverIP = wx.StaticText(panel, label="Server IP:Port")
        help_serverIP = "The IP address of the running server"
        label_serverIP.SetToolTip(wx.ToolTip(help_serverIP))
        sizer.Add(label_serverIP, pos=(xIndex, 0), flag=flag|wx.TOP, border=border+5)
    
        self.tc_serverIP = wx.TextCtrl(panel)
        self.tc_serverIP.SetToolTip(wx.ToolTip(help_serverIP))
        self.tc_serverIP.Value = guiFunctions.configMe('volume', 'serveriP')
        sizer.Add(self.tc_serverIP, pos=(xIndex, 1), flag=wx.LEFT|wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.TOP, border=border+5)

        
        self.tc_serverPort = wx.TextCtrl(panel)
        help_serverPort = "The port number of the running server"
        self.tc_serverPort.SetToolTip(wx.ToolTip(help_serverPort))
        self.tc_serverPort.Value = portNum
        sizer.Add(self.tc_serverPort, pos=(xIndex, 2), flag=wx.LEFT|wx.ALIGN_CENTER_VERTICAL|wx.TOP, border=border+5)
        
        self.bt_serverIP = wx.Button(panel, label="Get IP Address")
        help_bt_serverIP = "Click here to get the local machine's IP address.  This service can work by pointing to a different machine's IP on the LAN."
        self.bt_serverIP.SetToolTip(wx.ToolTip(help_bt_serverIP))
        self.bt_serverIP.Bind(wx.EVT_BUTTON, self.serverIPClick, self.bt_serverIP)
        sizer.Add(self.bt_serverIP, pos=(xIndex, 3), span=(1,2), flag=wx.LEFT|wx.RIGHT|wx.ALIGN_RIGHT|wx.TOP, border=border+5)

        if self.tc_serverIP.Value == '':
            guiFunctions.errorMsg('ERROR!', 'Open GUIpref.ini and enter a valid IP address. Setting local machine IP instead.')

            ip_address = guiFunctions.getLocalIP()
            self.tc_serverIP.Value = ip_address

        zoneNAME = guiFunctions.getZones(self.tc_serverIP.Value, portNum)
             
        xIndex +=1


    # -------------------------------------------------------------------------
    # ZONES TO MONITOR
        zoneNum = 0                                     
        sbsIndex = 0
        mvName = {'ck0':'ck0', 'sl0':'sliderZone0', 'tc0':'tc_zone0', 
                  'ck1':'ck1', 'sl1':'sliderZone1', 'tc1':'tc_zone1', 
                  'ck2':'ck2', 'sl2':'sliderZone2', 'tc2':'tc_zone2', 
                  'ck3':'ck3', 'sl3':'sliderZone3', 'tc3':'tc_zone3', 
                  'ck4':'ck4', 'sl4':'sliderZone4', 'tc4':'tc_zone4', 
                  'ck5':'ck5', 'sl5':'sliderZone5', 'tc5':'tc_zone5', 
                  'ck6':'ck6', 'sl6':'sliderZone6', 'tc6':'tc_zone6', 
                  'ck7':'ck7', 'sl7':'sliderZone7', 'tc7':'tc_zone7', 
                  'ck8':'ck8', 'sl8':'sliderZone8', 'tc8':'tc_zone8', 
                  'ck9':'ck9', 'sl9':'sliderZone9', 'tc9':'tc_zone9'}
        qtName = {'qck0':'qck0', 'qsl0':'sliderq0', 'qtc0':'qtc_zone0', 'qstart0':'startquiet0', 'qstop0':'stopquiet0',
                  'qck1':'qck1', 'qsl1':'sliderq1', 'qtc1':'qtc_zone1', 'qstart1':'startquiet1', 'qstop1':'stopquiet1',
                  'qck2':'qck2', 'qsl2':'sliderq2', 'qtc2':'qtc_zone2', 'qstart2':'startquiet2', 'qstop2':'stopquiet2',
                  'qck3':'qck3', 'qsl3':'sliderq3', 'qtc3':'qtc_zone3', 'qstart3':'startquiet3', 'qstop3':'stopquiet3',
                  'qck4':'qck4', 'qsl4':'sliderq4', 'qtc4':'qtc_zone4', 'qstart4':'startquiet4', 'qstop4':'stopquiet4',
                  'qck5':'qck5', 'qsl5':'sliderq5', 'qtc5':'qtc_zone5', 'qstart5':'startquiet5', 'qstop5':'stopquiet5',
                  'qck6':'qck6', 'qsl6':'sliderq6', 'qtc6':'qtc_zone6', 'qstart6':'startquiet6', 'qstop6':'stopquiet6',
                  'qck7':'qck7', 'qsl7':'sliderq7', 'qtc7':'qtc_zone7', 'qstart7':'startquiet7', 'qstop7':'stopquiet7',
                  'qck8':'qck8', 'qsl8':'sliderq8', 'qtc8':'qtc_zone8', 'qstart8':'startquiet8', 'qstop8':'stopquiet8',
                  'qck9':'qck9', 'qsl9':'sliderq9', 'qtc9':'qtc_zone9', 'qstart9':'startquiet9', 'qstop9':'stopquiet9',
                  }
        mtName = {'mck0':'mck0', 'mstart0':'startmute0', 'mstop0':'stopmute0',
                  'mck1':'mck1', 'mstart1':'startmute1', 'mstop1':'stopmute1',
                  'mck2':'mck2', 'mstart2':'startmute2', 'mstop2':'stopmute2',
                  'mck3':'mck3', 'mstart3':'startmute3', 'mstop3':'stopmute3',
                  'mck4':'mck4', 'mstart4':'startmute4', 'mstop4':'stopmute4',
                  'mck5':'mck5', 'mstart5':'startmute5', 'mstop5':'stopmute5',
                  'mck6':'mck6', 'mstart6':'startmute6', 'mstop6':'stopmute6',
                  'mck7':'mck7', 'mstart7':'startmute7', 'mstop7':'stopmute7',
                  'mck8':'mck8', 'mstart8':'startmute8', 'mstop8':'stopmute8',
                  'mck9':'mck9', 'mstart9':'startmute9', 'mstop9':'stopmute9'}        

        # ---------------------------------------------------------------- ZONE 1 -
        if zoneNum < len(zoneNAME):
            zone = 'zone' + str(zoneNum)
    
            if guiFunctions.configMe('volume', zone) is '':
                zonename = zoneNAME[zoneNum]
            else:
                zonename = guiFunctions.configMe('volume', zone)
            
            if '(ZP)' in zonename:
                zonename = zonename.replace('(ZP)','')
                
            # Create a static box
            self.sb_Zone = wx.StaticBox(panel, label='Zones to Monitor', size=(300,300))
            sbs_Zone = wx.StaticBoxSizer(self.sb_Zone, wx.VERTICAL)
            OptionBoxSizer = wx.GridBagSizer(13, 4)     
        # -------------------------------------------------------------------------
        # Make Header Columns 
            self.label_Zone = wx.StaticText(panel, label="Zone") # Span 1-3
            self.label_maxVol = wx.StaticText(panel, label="Max. Volume %") # Span 1-3
            self.label_QuietVol = wx.StaticText(panel, label="Max. Quiet Volume %") # Span 5-7
            self.label_Qstart = wx.StaticText(panel, label="Start") # Span 8
            self.label_qEnd = wx.StaticText(panel, label="End") # Span 9
            self.label_mStart = wx.StaticText(panel, label="Start") # Span 10
            self.label_mEnd = wx.StaticText(panel, label="End") # Span 11
        
            OptionBoxSizer.Add(self.label_Zone, pos=(sbsIndex, 0), flag=flag|wx.ALIGN_CENTER_HORIZONTAL, border=2)
            OptionBoxSizer.Add(self.label_maxVol, pos=(sbsIndex, 1), span=(1,3), flag=flag|wx.ALIGN_CENTER_HORIZONTAL, border=2)
            OptionBoxSizer.Add(self.label_QuietVol, pos=(sbsIndex, 5), span=(1,3), flag=flag|wx.ALIGN_CENTER_HORIZONTAL, border=2)
            OptionBoxSizer.Add(self.label_Qstart, pos=(sbsIndex, 8), flag=flag|wx.ALIGN_CENTER_HORIZONTAL, border=2)
            OptionBoxSizer.Add(self.label_qEnd, pos=(sbsIndex, 9), flag=flag|wx.ALIGN_CENTER_HORIZONTAL, border=2)
            OptionBoxSizer.Add(self.label_mStart, pos=(sbsIndex, 11), flag=flag|wx.ALIGN_CENTER_HORIZONTAL, border=2)
            OptionBoxSizer.Add(self.label_mEnd, pos=(sbsIndex, 12), flag=flag|wx.ALIGN_CENTER_HORIZONTAL, border=2)

            sbsIndex += 1
    
            # -------------------------------------------------------------------------
            # Separator line 
                    
            hl_SepLine1 = wx.StaticLine(panel, 0, (300, 1), (300,1))
            OptionBoxSizer.Add(hl_SepLine1, pos=(sbsIndex, 0), span=(1,13), flag=wx.EXPAND, border=2)          
            
            sbsIndex += 1

            # MONITOR VOLUME - CK, SLIDER, TXTCTRL
            self.ck_Vol1 = wx.CheckBox(self, -1, zonename, name=mvName['ck0'])
            self.ck_Vol1.SetToolTip(wx.ToolTip("Click here to turn on volume monitoring for this zone"))
            self.ck_Vol1.Value = guiFunctions.configMe("volume", mvName['ck0'], bool=True)
            self.sliderZone1 = wx.Slider(self, -1, guiFunctions.configMe("volume", mvName['sl0'], integer=True), 0, 100, size=(sliderWidthHeight), name=mvName['sl0'], style=wx.SL_HORIZONTAL)
            self.tc_zone1 = wx.TextCtrl(panel, -1, guiFunctions.configMe("volume", mvName['sl0']), (0,0), name=mvName['tc0'])
            
            # QUIET VOLUME  - CK, SLIDER, MAX VOL, START, STOP
            self.ck_qVol1 = wx.CheckBox(self, -1, 'Quiet', name=qtName['qck0'])
            self.ck_qVol1.SetToolTip(wx.ToolTip("Click here to turn on quiet hours for this zone"))
            self.ck_qVol1.Value = guiFunctions.configMe("volume", qtName['qck0'], bool=True)
            self.sl_qZone1 = wx.Slider(self, -1, guiFunctions.configMe("volume", qtName['qsl0'], integer=True), 0, 100, size=(sliderWidthHeight), style=wx.SL_HORIZONTAL, name=qtName['qsl0'])
            self.tc_qZone1 = wx.TextCtrl(panel, -1, guiFunctions.configMe("volume", qtName['qsl0']), (0,0), name=qtName['qtc0'])
            self.tc_qZone1hrstart = wx.TextCtrl(panel, -1, guiFunctions.configMe("volume", qtName['qstart0']), (0,0), name=qtName['qstart0'])
            self.tc_qZone1hrstop = wx.TextCtrl(panel, -1, guiFunctions.configMe("volume", qtName['qstop0']), (0,0), name=qtName['qstop0'])
        
            # MUTE VOLUME  - CK, START, STOP
            self.ck_mVol1 = wx.CheckBox(self, -1, 'Mute', name=mtName['mck0'])
            self.ck_mVol1.SetToolTip(wx.ToolTip("Click here to turn on mute hours for this zone"))
            self.ck_mVol1.Value = guiFunctions.configMe("volume", mtName['mck0'], bool=True)
            self.tc_mZone1hrstart = wx.TextCtrl(panel, -1, guiFunctions.configMe("volume", mtName['mstart0']), (0,0), name=mtName['mstart0'])
            self.tc_mZone1hrstop = wx.TextCtrl(panel, -1, guiFunctions.configMe("volume", mtName['mstop0']), (0,0), name=mtName['mstop0'])
    
            # Bind events
            # Monitor
            wx.FindWindowByName(mvName['sl0']).Bind(wx.EVT_SLIDER, lambda event: self.sliderUpdate(event, wx.FindWindowByName(mvName['sl0']), wx.FindWindowByName(mvName['tc0']),), wx.FindWindowByName(mvName['sl0']))
            wx.FindWindowByName(mvName['tc0']).Bind(wx.EVT_CHAR, lambda event: self.tcVolUpdate(event, wx.FindWindowByName(mvName['sl0']), wx.FindWindowByName(mvName['tc0']),), wx.FindWindowByName(mvName['tc0']))
            wx.FindWindowByName(mvName['ck0']).Bind(wx.EVT_CHECKBOX, lambda event: self.zoneCkClick(event, wx.FindWindowByName(mvName['ck0']), wx.FindWindowByName(mvName['sl0']), wx.FindWindowByName(mvName['tc0']),), wx.FindWindowByName(mvName['ck0']))
            # Quiet
            wx.FindWindowByName(qtName['qsl0']).Bind(wx.EVT_SLIDER, lambda event: self.sliderUpdate(event, wx.FindWindowByName(qtName['qsl0']), wx.FindWindowByName(qtName['qtc0']),), wx.FindWindowByName(qtName['qsl0']))
            wx.FindWindowByName(qtName['qtc0']).Bind(wx.EVT_CHAR, lambda event: self.tcVolUpdate(event, wx.FindWindowByName(qtName['qsl0']), wx.FindWindowByName(qtName['qtc0']),), wx.FindWindowByName(qtName['qtc0']))
            wx.FindWindowByName(qtName['qck0']).Bind(wx.EVT_CHECKBOX, lambda event: self.quietCkClick(event, wx.FindWindowByName(qtName['qck0']), wx.FindWindowByName(qtName['qsl0']), wx.FindWindowByName(qtName['qtc0']),wx.FindWindowByName(qtName['qstart0']),wx.FindWindowByName(qtName['qstop0']),), wx.FindWindowByName(qtName['qck0']))
            # Mute
            wx.FindWindowByName(mtName['mck0']).Bind(wx.EVT_CHECKBOX, lambda event: self.muteHoursClick(event, wx.FindWindowByName(mtName['mck0']), wx.FindWindowByName(mtName['mstart0']), wx.FindWindowByName(mtName['mstop0']),), wx.FindWindowByName(mtName['mck0']))
            
            # Add to frame
            # Monitor
            OptionBoxSizer.Add(wx.FindWindowByName(mvName['ck0']), pos=(sbsIndex, 0), flag=flag, border=border)     
            OptionBoxSizer.Add(wx.FindWindowByName(mvName['sl0']), pos=(sbsIndex, 1), span=(1,2),flag=sliderFlag, border=border)
            OptionBoxSizer.Add(wx.FindWindowByName(mvName['tc0']), pos=(sbsIndex, 3), flag=flag, border=border).SetMinSize(volDim)       
            # Quiet
            OptionBoxSizer.Add(wx.FindWindowByName(qtName['qck0']), pos=(sbsIndex, 4), flag=flag, border=border)     
            OptionBoxSizer.Add(wx.FindWindowByName(qtName['qsl0']), pos=(sbsIndex, 5), span=(1,2),flag=sliderFlag, border=border)
            OptionBoxSizer.Add(wx.FindWindowByName(qtName['qtc0']), pos=(sbsIndex, 7), flag=flag, border=border).SetMinSize((volDim))
            OptionBoxSizer.Add(wx.FindWindowByName(qtName['qstart0']), pos=(sbsIndex, 8), flag=flag, border=border).SetMinSize(timeDim) 
            OptionBoxSizer.Add(wx.FindWindowByName(qtName['qstop0']), pos=(sbsIndex, 9), flag=flag, border=border).SetMinSize(timeDim)    
            # Mute
            OptionBoxSizer.Add(wx.FindWindowByName(mtName['mck0']), pos=(sbsIndex, 10), flag=flag, border=border)      
            OptionBoxSizer.Add(wx.FindWindowByName(mtName['mstart0']), pos=(sbsIndex,11), flag=flag, border=border).SetMinSize(timeDim) 
            OptionBoxSizer.Add(wx.FindWindowByName(mtName['mstop0']), pos=(sbsIndex,12), flag=flag, border=border).SetMinSize(timeDim)        
    
            sbsIndex += 1
            zoneNum += 1

        # ---------------------------------------------------------------- ZONE 2 -
        if zoneNum < len(zoneNAME):
            zone = 'zone' + str(zoneNum)
    
            if guiFunctions.configMe('volume', zone) is '':
                zonename = zoneNAME[zoneNum]
            else:
                zonename = guiFunctions.configMe('volume', zone)
            
            if '(ZP)' in zonename:
                zonename = zonename.replace('(ZP)','')  
    
            # MONITOR VOLUME - CK, SLIDER, TXTCTRL
            self.ck_Vol1 = wx.CheckBox(self, -1, zonename, name=mvName['ck1'])
            self.ck_Vol1.SetToolTip(wx.ToolTip("Click here to turn on volume monitoring for this zone"))
            self.ck_Vol1.Value = guiFunctions.configMe("volume", mvName['ck1'], bool=True)
            self.sliderZone1 = wx.Slider(self, -1, guiFunctions.configMe("volume", mvName['sl1'], integer=True), 0, 100, size=(sliderWidthHeight), name=mvName['sl1'], style=wx.SL_HORIZONTAL)
            self.tc_zone1 = wx.TextCtrl(panel, -1, guiFunctions.configMe("volume", mvName['sl1']), (0,0), name=mvName['tc1'])
            
            # QUIET VOLUME  - CK, SLIDER, MAX VOL, START, STOP
            self.ck_qVol1 = wx.CheckBox(self, -1, 'Quiet', name=qtName['qck1'])
            self.ck_qVol1.SetToolTip(wx.ToolTip("Click here to turn on quiet hours for this zone"))
            self.ck_qVol1.Value = guiFunctions.configMe("volume", qtName['qck1'], bool=True)
            self.sl_qZone1 = wx.Slider(self, -1, guiFunctions.configMe("volume", qtName['qsl1'], integer=True), 0, 100, size=(sliderWidthHeight), style=wx.SL_HORIZONTAL, name=qtName['qsl1'])
            self.tc_qZone1 = wx.TextCtrl(panel, -1, guiFunctions.configMe("volume", qtName['qsl1']), (0,0), name=qtName['qtc1'])
            self.tc_qZone1hrstart = wx.TextCtrl(panel, -1, guiFunctions.configMe("volume", qtName['qstart1']), (0,0), name=qtName['qstart1'])
            self.tc_qZone1hrstop = wx.TextCtrl(panel, -1, guiFunctions.configMe("volume", qtName['qstop1']), (0,0), name=qtName['qstop1'])
        
            # MUTE VOLUME  - CK, START, STOP
            self.ck_mVol1 = wx.CheckBox(self, -1, 'Mute', name=mtName['mck1'])
            self.ck_mVol1.SetToolTip(wx.ToolTip("Click here to turn on mute hours for this zone"))
            self.ck_mVol1.Value = guiFunctions.configMe("volume", mtName['mck1'], bool=True)
            self.tc_mZone1hrstart = wx.TextCtrl(panel, -1, guiFunctions.configMe("volume", mtName['mstart1']), (0,0), name=mtName['mstart1'])
            self.tc_mZone1hrstop = wx.TextCtrl(panel, -1, guiFunctions.configMe("volume", mtName['mstop1']), (0,0), name=mtName['mstop1'])
    
            # Bind events
            # Monitor
            wx.FindWindowByName(mvName['sl1']).Bind(wx.EVT_SLIDER, lambda event: self.sliderUpdate(event, wx.FindWindowByName(mvName['sl1']), wx.FindWindowByName(mvName['tc1']),), wx.FindWindowByName(mvName['sl1']))
            wx.FindWindowByName(mvName['tc1']).Bind(wx.EVT_CHAR, lambda event: self.tcVolUpdate(event, wx.FindWindowByName(mvName['sl1']), wx.FindWindowByName(mvName['tc1']),), wx.FindWindowByName(mvName['tc1']))
            wx.FindWindowByName(mvName['ck1']).Bind(wx.EVT_CHECKBOX, lambda event: self.zoneCkClick(event, wx.FindWindowByName(mvName['ck1']), wx.FindWindowByName(mvName['sl1']), wx.FindWindowByName(mvName['tc1']),), wx.FindWindowByName(mvName['ck1']))
            # Quiet
            wx.FindWindowByName(qtName['qsl1']).Bind(wx.EVT_SLIDER, lambda event: self.sliderUpdate(event, wx.FindWindowByName(qtName['qsl1']), wx.FindWindowByName(qtName['qtc1']),), wx.FindWindowByName(qtName['qsl1']))
            wx.FindWindowByName(qtName['qtc1']).Bind(wx.EVT_CHAR, lambda event: self.tcVolUpdate(event, wx.FindWindowByName(qtName['qsl1']), wx.FindWindowByName(qtName['qtc1']),), wx.FindWindowByName(qtName['qtc1']))
            wx.FindWindowByName(qtName['qck1']).Bind(wx.EVT_CHECKBOX, lambda event: self.quietCkClick(event, wx.FindWindowByName(qtName['qck1']), wx.FindWindowByName(qtName['qsl1']), wx.FindWindowByName(qtName['qtc1']),wx.FindWindowByName(qtName['qstart1']),wx.FindWindowByName(qtName['qstop1']),), wx.FindWindowByName(qtName['qck1']))
            # Mute
            wx.FindWindowByName(mtName['mck1']).Bind(wx.EVT_CHECKBOX, lambda event: self.muteHoursClick(event, wx.FindWindowByName(mtName['mck1']), wx.FindWindowByName(mtName['mstart1']), wx.FindWindowByName(mtName['mstop1']),), wx.FindWindowByName(mtName['mck1']))
            
            # Add to frame
            # Monitor
            OptionBoxSizer.Add(wx.FindWindowByName(mvName['ck1']), pos=(sbsIndex, 0), flag=flag, border=border)     
            OptionBoxSizer.Add(wx.FindWindowByName(mvName['sl1']), pos=(sbsIndex, 1), span=(1,2),flag=sliderFlag, border=border)
            OptionBoxSizer.Add(wx.FindWindowByName(mvName['tc1']), pos=(sbsIndex, 3), flag=flag, border=border).SetMinSize(volDim)       
            # Quiet
            OptionBoxSizer.Add(wx.FindWindowByName(qtName['qck1']), pos=(sbsIndex, 4), flag=flag, border=border)     
            OptionBoxSizer.Add(wx.FindWindowByName(qtName['qsl1']), pos=(sbsIndex, 5), span=(1,2),flag=sliderFlag, border=border)
            OptionBoxSizer.Add(wx.FindWindowByName(qtName['qtc1']), pos=(sbsIndex, 7), flag=flag, border=border).SetMinSize((volDim))
            OptionBoxSizer.Add(wx.FindWindowByName(qtName['qstart1']), pos=(sbsIndex, 8), flag=flag, border=border).SetMinSize(timeDim) 
            OptionBoxSizer.Add(wx.FindWindowByName(qtName['qstop1']), pos=(sbsIndex, 9), flag=flag, border=border).SetMinSize(timeDim)    
            # Mute
            OptionBoxSizer.Add(wx.FindWindowByName(mtName['mck1']), pos=(sbsIndex, 10), flag=flag, border=border)      
            OptionBoxSizer.Add(wx.FindWindowByName(mtName['mstart1']), pos=(sbsIndex,11), flag=flag, border=border).SetMinSize(timeDim) 
            OptionBoxSizer.Add(wx.FindWindowByName(mtName['mstop1']), pos=(sbsIndex,12), flag=flag, border=border).SetMinSize(timeDim)        
    
            sbsIndex += 1
            zoneNum += 1

        # ---------------------------------------------------------------- ZONE 3 -
        if zoneNum < len(zoneNAME):
            zone = 'zone' + str(zoneNum)
    
            if guiFunctions.configMe('volume', zone) is '':
                zonename = zoneNAME[zoneNum]
            else:
                zonename = guiFunctions.configMe('volume', zone)
            
            if '(ZP)' in zonename:
                zonename = zonename.replace('(ZP)','')  
    
            # MONITOR VOLUME - CK, SLIDER, TXTCTRL
            self.ck_Vol1 = wx.CheckBox(self, -1, zonename, name=mvName['ck2'])
            self.ck_Vol1.SetToolTip(wx.ToolTip("Click here to turn on volume monitoring for this zone"))
            self.ck_Vol1.Value = guiFunctions.configMe("volume", mvName['ck2'], bool=True)
            self.sliderZone1 = wx.Slider(self, -1, guiFunctions.configMe("volume", mvName['sl2'], integer=True), 0, 100, size=(sliderWidthHeight), name=mvName['sl2'], style=wx.SL_HORIZONTAL)
            self.tc_zone1 = wx.TextCtrl(panel, -1, guiFunctions.configMe("volume", mvName['sl2']), (0,0), name=mvName['tc2'])
            
            # QUIET VOLUME  - CK, SLIDER, MAX VOL, START, STOP
            self.ck_qVol1 = wx.CheckBox(self, -1, 'Quiet', name=qtName['qck2'])
            self.ck_qVol1.SetToolTip(wx.ToolTip("Click here to turn on quiet hours for this zone"))
            self.ck_qVol1.Value = guiFunctions.configMe("volume", qtName['qck2'], bool=True)
            self.sl_qZone1 = wx.Slider(self, -1, guiFunctions.configMe("volume", qtName['qsl2'], integer=True), 0, 100, size=(sliderWidthHeight), style=wx.SL_HORIZONTAL, name=qtName['qsl2'])
            self.tc_qZone1 = wx.TextCtrl(panel, -1, guiFunctions.configMe("volume", qtName['qsl2']), (0,0), name=qtName['qtc2'])
            self.tc_qZone1hrstart = wx.TextCtrl(panel, -1, guiFunctions.configMe("volume", qtName['qstart2']), (0,0), name=qtName['qstart2'])
            self.tc_qZone1hrstop = wx.TextCtrl(panel, -1, guiFunctions.configMe("volume", qtName['qstop2']), (0,0), name=qtName['qstop2'])
        
            # MUTE VOLUME  - CK, START, STOP
            self.ck_mVol1 = wx.CheckBox(self, -1, 'Mute', name=mtName['mck2'])
            self.ck_mVol1.SetToolTip(wx.ToolTip("Click here to turn on mute hours for this zone"))
            self.ck_mVol1.Value = guiFunctions.configMe("volume", mtName['mck2'], bool=True)
            self.tc_mZone1hrstart = wx.TextCtrl(panel, -1, guiFunctions.configMe("volume", mtName['mstart2']), (0,0), name=mtName['mstart2'])
            self.tc_mZone1hrstop = wx.TextCtrl(panel, -1, guiFunctions.configMe("volume", mtName['mstop2']), (0,0), name=mtName['mstop2'])
    
            # Bind events
            # Monitor
            wx.FindWindowByName(mvName['sl2']).Bind(wx.EVT_SLIDER, lambda event: self.sliderUpdate(event, wx.FindWindowByName(mvName['sl2']), wx.FindWindowByName(mvName['tc2']),), wx.FindWindowByName(mvName['sl2']))
            wx.FindWindowByName(mvName['tc2']).Bind(wx.EVT_CHAR, lambda event: self.tcVolUpdate(event, wx.FindWindowByName(mvName['sl2']), wx.FindWindowByName(mvName['tc2']),), wx.FindWindowByName(mvName['tc2']))
            wx.FindWindowByName(mvName['ck2']).Bind(wx.EVT_CHECKBOX, lambda event: self.zoneCkClick(event, wx.FindWindowByName(mvName['ck2']), wx.FindWindowByName(mvName['sl2']), wx.FindWindowByName(mvName['tc2']),), wx.FindWindowByName(mvName['ck2']))
            # Quiet
            wx.FindWindowByName(qtName['qsl2']).Bind(wx.EVT_SLIDER, lambda event: self.sliderUpdate(event, wx.FindWindowByName(qtName['qsl2']), wx.FindWindowByName(qtName['qtc2']),), wx.FindWindowByName(qtName['qsl2']))
            wx.FindWindowByName(qtName['qtc2']).Bind(wx.EVT_CHAR, lambda event: self.tcVolUpdate(event, wx.FindWindowByName(qtName['qsl2']), wx.FindWindowByName(qtName['qtc2']),), wx.FindWindowByName(qtName['qtc2']))
            wx.FindWindowByName(qtName['qck2']).Bind(wx.EVT_CHECKBOX, lambda event: self.quietCkClick(event, wx.FindWindowByName(qtName['qck2']), wx.FindWindowByName(qtName['qsl2']), wx.FindWindowByName(qtName['qtc2']),wx.FindWindowByName(qtName['qstart2']),wx.FindWindowByName(qtName['qstop2']),), wx.FindWindowByName(qtName['qck2']))
            # Mute
            wx.FindWindowByName(mtName['mck2']).Bind(wx.EVT_CHECKBOX, lambda event: self.muteHoursClick(event, wx.FindWindowByName(mtName['mck2']), wx.FindWindowByName(mtName['mstart2']), wx.FindWindowByName(mtName['mstop2']),), wx.FindWindowByName(mtName['mck2']))
            
            # Add to frame
            # Monitor
            OptionBoxSizer.Add(wx.FindWindowByName(mvName['ck2']), pos=(sbsIndex, 0), flag=flag, border=border)     
            OptionBoxSizer.Add(wx.FindWindowByName(mvName['sl2']), pos=(sbsIndex, 1), span=(1,2),flag=sliderFlag, border=border)
            OptionBoxSizer.Add(wx.FindWindowByName(mvName['tc2']), pos=(sbsIndex, 3), flag=flag, border=border).SetMinSize(volDim)       
            # Quiet
            OptionBoxSizer.Add(wx.FindWindowByName(qtName['qck2']), pos=(sbsIndex, 4), flag=flag, border=border)     
            OptionBoxSizer.Add(wx.FindWindowByName(qtName['qsl2']), pos=(sbsIndex, 5), span=(1,2),flag=sliderFlag, border=border)
            OptionBoxSizer.Add(wx.FindWindowByName(qtName['qtc2']), pos=(sbsIndex, 7), flag=flag, border=border).SetMinSize((volDim))
            OptionBoxSizer.Add(wx.FindWindowByName(qtName['qstart2']), pos=(sbsIndex, 8), flag=flag, border=border).SetMinSize(timeDim) 
            OptionBoxSizer.Add(wx.FindWindowByName(qtName['qstop2']), pos=(sbsIndex, 9), flag=flag, border=border).SetMinSize(timeDim)    
            # Mute
            OptionBoxSizer.Add(wx.FindWindowByName(mtName['mck2']), pos=(sbsIndex, 10), flag=flag, border=border)      
            OptionBoxSizer.Add(wx.FindWindowByName(mtName['mstart2']), pos=(sbsIndex,11), flag=flag, border=border).SetMinSize(timeDim) 
            OptionBoxSizer.Add(wx.FindWindowByName(mtName['mstop2']), pos=(sbsIndex,12), flag=flag, border=border).SetMinSize(timeDim)        
    
            sbsIndex += 1
            zoneNum += 1
        # ---------------------------------------------------------------- ZONE 4 -
        if zoneNum < len(zoneNAME):
            zone = 'zone' + str(zoneNum)
    
            if guiFunctions.configMe('volume', zone) is '':
                zonename = zoneNAME[zoneNum]
            else:
                zonename = guiFunctions.configMe('volume', zone)
            
            if '(ZP)' in zonename:
                zonename = zonename.replace('(ZP)','')  
    
            # MONITOR VOLUME - CK, SLIDER, TXTCTRL
            self.ck_Vol1 = wx.CheckBox(self, -1, zonename, name=mvName['ck3'])
            self.ck_Vol1.SetToolTip(wx.ToolTip("Click here to turn on volume monitoring for this zone"))
            self.ck_Vol1.Value = guiFunctions.configMe("volume", mvName['ck3'], bool=True)
            self.sliderZone1 = wx.Slider(self, -1, guiFunctions.configMe("volume", mvName['sl3'], integer=True), 0, 100, size=(sliderWidthHeight), name=mvName['sl3'], style=wx.SL_HORIZONTAL)
            self.tc_zone1 = wx.TextCtrl(panel, -1, guiFunctions.configMe("volume", mvName['sl3']), (0,0), name=mvName['tc3'])
            
            # QUIET VOLUME  - CK, SLIDER, MAX VOL, START, STOP
            self.ck_qVol1 = wx.CheckBox(self, -1, 'Quiet', name=qtName['qck3'])
            self.ck_qVol1.SetToolTip(wx.ToolTip("Click here to turn on quiet hours for this zone"))
            self.ck_qVol1.Value = guiFunctions.configMe("volume", qtName['qck3'], bool=True)
            self.sl_qZone1 = wx.Slider(self, -1, guiFunctions.configMe("volume", qtName['qsl3'], integer=True), 0, 100, size=(sliderWidthHeight), style=wx.SL_HORIZONTAL, name=qtName['qsl3'])
            self.tc_qZone1 = wx.TextCtrl(panel, -1, guiFunctions.configMe("volume", qtName['qsl3']), (0,0), name=qtName['qtc3'])
            self.tc_qZone1hrstart = wx.TextCtrl(panel, -1, guiFunctions.configMe("volume", qtName['qstart3']), (0,0), name=qtName['qstart3'])
            self.tc_qZone1hrstop = wx.TextCtrl(panel, -1, guiFunctions.configMe("volume", qtName['qstop3']), (0,0), name=qtName['qstop3'])
        
            # MUTE VOLUME  - CK, START, STOP
            self.ck_mVol1 = wx.CheckBox(self, -1, 'Mute', name=mtName['mck3'])
            self.ck_mVol1.SetToolTip(wx.ToolTip("Click here to turn on mute hours for this zone"))
            self.ck_mVol1.Value = guiFunctions.configMe("volume", mtName['mck3'], bool=True)
            self.tc_mZone1hrstart = wx.TextCtrl(panel, -1, guiFunctions.configMe("volume", mtName['mstart3']), (0,0), name=mtName['mstart3'])
            self.tc_mZone1hrstop = wx.TextCtrl(panel, -1, guiFunctions.configMe("volume", mtName['mstop3']), (0,0), name=mtName['mstop3'])
    
            # Bind events
            # Monitor
            wx.FindWindowByName(mvName['sl3']).Bind(wx.EVT_SLIDER, lambda event: self.sliderUpdate(event, wx.FindWindowByName(mvName['sl3']), wx.FindWindowByName(mvName['tc3']),), wx.FindWindowByName(mvName['sl3']))
            wx.FindWindowByName(mvName['tc3']).Bind(wx.EVT_CHAR, lambda event: self.tcVolUpdate(event, wx.FindWindowByName(mvName['sl3']), wx.FindWindowByName(mvName['tc3']),), wx.FindWindowByName(mvName['tc3']))
            wx.FindWindowByName(mvName['ck3']).Bind(wx.EVT_CHECKBOX, lambda event: self.zoneCkClick(event, wx.FindWindowByName(mvName['ck3']), wx.FindWindowByName(mvName['sl3']), wx.FindWindowByName(mvName['tc3']),), wx.FindWindowByName(mvName['ck3']))
            # Quiet
            wx.FindWindowByName(qtName['qsl3']).Bind(wx.EVT_SLIDER, lambda event: self.sliderUpdate(event, wx.FindWindowByName(qtName['qsl3']), wx.FindWindowByName(qtName['qtc3']),), wx.FindWindowByName(qtName['qsl3']))
            wx.FindWindowByName(qtName['qtc3']).Bind(wx.EVT_CHAR, lambda event: self.tcVolUpdate(event, wx.FindWindowByName(qtName['qsl3']), wx.FindWindowByName(qtName['qtc3']),), wx.FindWindowByName(qtName['qtc3']))
            wx.FindWindowByName(qtName['qck3']).Bind(wx.EVT_CHECKBOX, lambda event: self.quietCkClick(event, wx.FindWindowByName(qtName['qck3']), wx.FindWindowByName(qtName['qsl3']), wx.FindWindowByName(qtName['qtc3']),wx.FindWindowByName(qtName['qstart3']),wx.FindWindowByName(qtName['qstop3']),), wx.FindWindowByName(qtName['qck3']))
            # Mute
            wx.FindWindowByName(mtName['mck3']).Bind(wx.EVT_CHECKBOX, lambda event: self.muteHoursClick(event, wx.FindWindowByName(mtName['mck3']), wx.FindWindowByName(mtName['mstart3']), wx.FindWindowByName(mtName['mstop3']),), wx.FindWindowByName(mtName['mck3']))
            
            # Add to frame
            # Monitor
            OptionBoxSizer.Add(wx.FindWindowByName(mvName['ck3']), pos=(sbsIndex, 0), flag=flag, border=border)     
            OptionBoxSizer.Add(wx.FindWindowByName(mvName['sl3']), pos=(sbsIndex, 1), span=(1,2),flag=sliderFlag, border=border)
            OptionBoxSizer.Add(wx.FindWindowByName(mvName['tc3']), pos=(sbsIndex, 3), flag=flag, border=border).SetMinSize(volDim)       
            # Quiet
            OptionBoxSizer.Add(wx.FindWindowByName(qtName['qck3']), pos=(sbsIndex, 4), flag=flag, border=border)     
            OptionBoxSizer.Add(wx.FindWindowByName(qtName['qsl3']), pos=(sbsIndex, 5), span=(1,2),flag=sliderFlag, border=border)
            OptionBoxSizer.Add(wx.FindWindowByName(qtName['qtc3']), pos=(sbsIndex, 7), flag=flag, border=border).SetMinSize((volDim))
            OptionBoxSizer.Add(wx.FindWindowByName(qtName['qstart3']), pos=(sbsIndex, 8), flag=flag, border=border).SetMinSize(timeDim) 
            OptionBoxSizer.Add(wx.FindWindowByName(qtName['qstop3']), pos=(sbsIndex, 9), flag=flag, border=border).SetMinSize(timeDim)    
            # Mute
            OptionBoxSizer.Add(wx.FindWindowByName(mtName['mck3']), pos=(sbsIndex, 10), flag=flag, border=border)      
            OptionBoxSizer.Add(wx.FindWindowByName(mtName['mstart3']), pos=(sbsIndex,11), flag=flag, border=border).SetMinSize(timeDim) 
            OptionBoxSizer.Add(wx.FindWindowByName(mtName['mstop3']), pos=(sbsIndex,12), flag=flag, border=border).SetMinSize(timeDim)        
    
            sbsIndex += 1
            zoneNum += 1
        
        # ---------------------------------------------------------------- ZONE 5 -
        if zoneNum < len(zoneNAME):
            zone = 'zone' + str(zoneNum)
    
            if guiFunctions.configMe('volume', zone) is '':
                zonename = zoneNAME[zoneNum]
            else:
                zonename = guiFunctions.configMe('volume', zone)
            
            if '(ZP)' in zonename:
                zonename = zonename.replace('(ZP)','')  
    
            # MONITOR VOLUME - CK, SLIDER, TXTCTRL
            self.ck_Vol1 = wx.CheckBox(self, -1, zonename, name=mvName['ck4'])
            self.ck_Vol1.SetToolTip(wx.ToolTip("Click here to turn on volume monitoring for this zone"))
            self.ck_Vol1.Value = guiFunctions.configMe("volume", mvName['ck4'], bool=True)
            self.sliderZone1 = wx.Slider(self, -1, guiFunctions.configMe("volume", mvName['sl4'], integer=True), 0, 100, size=(sliderWidthHeight), name=mvName['sl4'], style=wx.SL_HORIZONTAL)
            self.tc_zone1 = wx.TextCtrl(panel, -1, guiFunctions.configMe("volume", mvName['sl4']), (0,0), name=mvName['tc4'])
            
            # QUIET VOLUME  - CK, SLIDER, MAX VOL, START, STOP
            self.ck_qVol1 = wx.CheckBox(self, -1, 'Quiet', name=qtName['qck4'])
            self.ck_qVol1.SetToolTip(wx.ToolTip("Click here to turn on quiet hours for this zone"))
            self.ck_qVol1.Value = guiFunctions.configMe("volume", qtName['qck4'], bool=True)
            self.sl_qZone1 = wx.Slider(self, -1, guiFunctions.configMe("volume", qtName['qsl4'], integer=True), 0, 100, size=(sliderWidthHeight), style=wx.SL_HORIZONTAL, name=qtName['qsl4'])
            self.tc_qZone1 = wx.TextCtrl(panel, -1, guiFunctions.configMe("volume", qtName['qsl4']), (0,0), name=qtName['qtc4'])
            self.tc_qZone1hrstart = wx.TextCtrl(panel, -1, guiFunctions.configMe("volume", qtName['qstart4']), (0,0), name=qtName['qstart4'])
            self.tc_qZone1hrstop = wx.TextCtrl(panel, -1, guiFunctions.configMe("volume", qtName['qstop4']), (0,0), name=qtName['qstop4'])
        
            # MUTE VOLUME  - CK, START, STOP
            self.ck_mVol1 = wx.CheckBox(self, -1, 'Mute', name=mtName['mck4'])
            self.ck_mVol1.SetToolTip(wx.ToolTip("Click here to turn on mute hours for this zone"))
            self.ck_mVol1.Value = guiFunctions.configMe("volume", mtName['mck4'], bool=True)
            self.tc_mZone1hrstart = wx.TextCtrl(panel, -1, guiFunctions.configMe("volume", mtName['mstart4']), (0,0), name=mtName['mstart4'])
            self.tc_mZone1hrstop = wx.TextCtrl(panel, -1, guiFunctions.configMe("volume", mtName['mstop4']), (0,0), name=mtName['mstop4'])
    
            # Bind events
            # Monitor
            wx.FindWindowByName(mvName['sl4']).Bind(wx.EVT_SLIDER, lambda event: self.sliderUpdate(event, wx.FindWindowByName(mvName['sl4']), wx.FindWindowByName(mvName['tc4']),), wx.FindWindowByName(mvName['sl4']))
            wx.FindWindowByName(mvName['tc4']).Bind(wx.EVT_CHAR, lambda event: self.tcVolUpdate(event, wx.FindWindowByName(mvName['sl4']), wx.FindWindowByName(mvName['tc4']),), wx.FindWindowByName(mvName['tc4']))
            wx.FindWindowByName(mvName['ck4']).Bind(wx.EVT_CHECKBOX, lambda event: self.zoneCkClick(event, wx.FindWindowByName(mvName['ck4']), wx.FindWindowByName(mvName['sl4']), wx.FindWindowByName(mvName['tc4']),), wx.FindWindowByName(mvName['ck4']))
            # Quiet
            wx.FindWindowByName(qtName['qsl4']).Bind(wx.EVT_SLIDER, lambda event: self.sliderUpdate(event, wx.FindWindowByName(qtName['qsl4']), wx.FindWindowByName(qtName['qtc4']),), wx.FindWindowByName(qtName['qsl4']))
            wx.FindWindowByName(qtName['qtc4']).Bind(wx.EVT_CHAR, lambda event: self.tcVolUpdate(event, wx.FindWindowByName(qtName['qsl4']), wx.FindWindowByName(qtName['qtc4']),), wx.FindWindowByName(qtName['qtc4']))
            wx.FindWindowByName(qtName['qck4']).Bind(wx.EVT_CHECKBOX, lambda event: self.quietCkClick(event, wx.FindWindowByName(qtName['qck4']), wx.FindWindowByName(qtName['qsl4']), wx.FindWindowByName(qtName['qtc4']),wx.FindWindowByName(qtName['qstart4']),wx.FindWindowByName(qtName['qstop4']),), wx.FindWindowByName(qtName['qck4']))
            # Mute
            wx.FindWindowByName(mtName['mck4']).Bind(wx.EVT_CHECKBOX, lambda event: self.muteHoursClick(event, wx.FindWindowByName(mtName['mck4']), wx.FindWindowByName(mtName['mstart4']), wx.FindWindowByName(mtName['mstop4']),), wx.FindWindowByName(mtName['mck4']))
            
            # Add to frame
            # Monitor
            OptionBoxSizer.Add(wx.FindWindowByName(mvName['ck4']), pos=(sbsIndex, 0), flag=flag, border=border)     
            OptionBoxSizer.Add(wx.FindWindowByName(mvName['sl4']), pos=(sbsIndex, 1), span=(1,2),flag=sliderFlag, border=border)
            OptionBoxSizer.Add(wx.FindWindowByName(mvName['tc4']), pos=(sbsIndex, 3), flag=flag, border=border).SetMinSize(volDim)       
            # Quiet
            OptionBoxSizer.Add(wx.FindWindowByName(qtName['qck4']), pos=(sbsIndex, 4), flag=flag, border=border)     
            OptionBoxSizer.Add(wx.FindWindowByName(qtName['qsl4']), pos=(sbsIndex, 5), span=(1,2),flag=sliderFlag, border=border)
            OptionBoxSizer.Add(wx.FindWindowByName(qtName['qtc4']), pos=(sbsIndex, 7), flag=flag, border=border).SetMinSize((volDim))
            OptionBoxSizer.Add(wx.FindWindowByName(qtName['qstart4']), pos=(sbsIndex, 8), flag=flag, border=border).SetMinSize(timeDim) 
            OptionBoxSizer.Add(wx.FindWindowByName(qtName['qstop4']), pos=(sbsIndex, 9), flag=flag, border=border).SetMinSize(timeDim)    
            # Mute
            OptionBoxSizer.Add(wx.FindWindowByName(mtName['mck4']), pos=(sbsIndex, 10), flag=flag, border=border)      
            OptionBoxSizer.Add(wx.FindWindowByName(mtName['mstart4']), pos=(sbsIndex,11), flag=flag, border=border).SetMinSize(timeDim) 
            OptionBoxSizer.Add(wx.FindWindowByName(mtName['mstop4']), pos=(sbsIndex,12), flag=flag, border=border).SetMinSize(timeDim)        
    
            sbsIndex += 1
            zoneNum += 1          

        # ---------------------------------------------------------------- ZONE 6 -
        if zoneNum < len(zoneNAME):
            zone = 'zone' + str(zoneNum)
    
            if guiFunctions.configMe('volume', zone) is '':
                zonename = zoneNAME[zoneNum]
            else:
                zonename = guiFunctions.configMe('volume', zone)
            
            if '(ZP)' in zonename:
                zonename = zonename.replace('(ZP)','')  
    
            # MONITOR VOLUME - CK, SLIDER, TXTCTRL
            self.ck_Vol1 = wx.CheckBox(self, -1, zonename, name=mvName['ck5'])
            self.ck_Vol1.SetToolTip(wx.ToolTip("Click here to turn on volume monitoring for this zone"))
            self.ck_Vol1.Value = guiFunctions.configMe("volume", mvName['ck5'], bool=True)
            self.sliderZone1 = wx.Slider(self, -1, guiFunctions.configMe("volume", mvName['sl5'], integer=True), 0, 100, size=(sliderWidthHeight), name=mvName['sl5'], style=wx.SL_HORIZONTAL)
            self.tc_zone1 = wx.TextCtrl(panel, -1, guiFunctions.configMe("volume", mvName['sl5']), (0,0), name=mvName['tc5'])
            
            # QUIET VOLUME  - CK, SLIDER, MAX VOL, START, STOP
            self.ck_qVol1 = wx.CheckBox(self, -1, 'Quiet', name=qtName['qck5'])
            self.ck_qVol1.SetToolTip(wx.ToolTip("Click here to turn on quiet hours for this zone"))
            self.ck_qVol1.Value = guiFunctions.configMe("volume", qtName['qck5'], bool=True)
            self.sl_qZone1 = wx.Slider(self, -1, guiFunctions.configMe("volume", qtName['qsl5'], integer=True), 0, 100, size=(sliderWidthHeight), style=wx.SL_HORIZONTAL, name=qtName['qsl5'])
            self.tc_qZone1 = wx.TextCtrl(panel, -1, guiFunctions.configMe("volume", qtName['qsl5']), (0,0), name=qtName['qtc5'])
            self.tc_qZone1hrstart = wx.TextCtrl(panel, -1, guiFunctions.configMe("volume", qtName['qstart5']), (0,0), name=qtName['qstart5'])
            self.tc_qZone1hrstop = wx.TextCtrl(panel, -1, guiFunctions.configMe("volume", qtName['qstop5']), (0,0), name=qtName['qstop5'])
        
            # MUTE VOLUME  - CK, START, STOP
            self.ck_mVol1 = wx.CheckBox(self, -1, 'Mute', name=mtName['mck5'])
            self.ck_mVol1.SetToolTip(wx.ToolTip("Click here to turn on mute hours for this zone"))
            self.ck_mVol1.Value = guiFunctions.configMe("volume", mtName['mck5'], bool=True)
            self.tc_mZone1hrstart = wx.TextCtrl(panel, -1, guiFunctions.configMe("volume", mtName['mstart5']), (0,0), name=mtName['mstart5'])
            self.tc_mZone1hrstop = wx.TextCtrl(panel, -1, guiFunctions.configMe("volume", mtName['mstop5']), (0,0), name=mtName['mstop5'])
    
            # Bind events
            # Monitor
            wx.FindWindowByName(mvName['sl5']).Bind(wx.EVT_SLIDER, lambda event: self.sliderUpdate(event, wx.FindWindowByName(mvName['sl5']), wx.FindWindowByName(mvName['tc5']),), wx.FindWindowByName(mvName['sl5']))
            wx.FindWindowByName(mvName['tc5']).Bind(wx.EVT_CHAR, lambda event: self.tcVolUpdate(event, wx.FindWindowByName(mvName['sl5']), wx.FindWindowByName(mvName['tc5']),), wx.FindWindowByName(mvName['tc5']))
            wx.FindWindowByName(mvName['ck5']).Bind(wx.EVT_CHECKBOX, lambda event: self.zoneCkClick(event, wx.FindWindowByName(mvName['ck5']), wx.FindWindowByName(mvName['sl5']), wx.FindWindowByName(mvName['tc5']),), wx.FindWindowByName(mvName['ck5']))
            # Quiet
            wx.FindWindowByName(qtName['qsl5']).Bind(wx.EVT_SLIDER, lambda event: self.sliderUpdate(event, wx.FindWindowByName(qtName['qsl5']), wx.FindWindowByName(qtName['qtc5']),), wx.FindWindowByName(qtName['qsl5']))
            wx.FindWindowByName(qtName['qtc5']).Bind(wx.EVT_CHAR, lambda event: self.tcVolUpdate(event, wx.FindWindowByName(qtName['qsl5']), wx.FindWindowByName(qtName['qtc5']),), wx.FindWindowByName(qtName['qtc5']))
            wx.FindWindowByName(qtName['qck5']).Bind(wx.EVT_CHECKBOX, lambda event: self.quietCkClick(event, wx.FindWindowByName(qtName['qck5']), wx.FindWindowByName(qtName['qsl5']), wx.FindWindowByName(qtName['qtc5']),wx.FindWindowByName(qtName['qstart5']),wx.FindWindowByName(qtName['qstop5']),), wx.FindWindowByName(qtName['qck5']))
            # Mute
            wx.FindWindowByName(mtName['mck5']).Bind(wx.EVT_CHECKBOX, lambda event: self.muteHoursClick(event, wx.FindWindowByName(mtName['mck5']), wx.FindWindowByName(mtName['mstart5']), wx.FindWindowByName(mtName['mstop5']),), wx.FindWindowByName(mtName['mck5']))
            
            # Add to frame
            # Monitor
            OptionBoxSizer.Add(wx.FindWindowByName(mvName['ck5']), pos=(sbsIndex, 0), flag=flag, border=border)     
            OptionBoxSizer.Add(wx.FindWindowByName(mvName['sl5']), pos=(sbsIndex, 1), span=(1,2),flag=sliderFlag, border=border)
            OptionBoxSizer.Add(wx.FindWindowByName(mvName['tc5']), pos=(sbsIndex, 3), flag=flag, border=border).SetMinSize(volDim)       
            # Quiet
            OptionBoxSizer.Add(wx.FindWindowByName(qtName['qck5']), pos=(sbsIndex, 4), flag=flag, border=border)     
            OptionBoxSizer.Add(wx.FindWindowByName(qtName['qsl5']), pos=(sbsIndex, 5), span=(1,2),flag=sliderFlag, border=border)
            OptionBoxSizer.Add(wx.FindWindowByName(qtName['qtc5']), pos=(sbsIndex, 7), flag=flag, border=border).SetMinSize((volDim))
            OptionBoxSizer.Add(wx.FindWindowByName(qtName['qstart5']), pos=(sbsIndex, 8), flag=flag, border=border).SetMinSize(timeDim) 
            OptionBoxSizer.Add(wx.FindWindowByName(qtName['qstop5']), pos=(sbsIndex, 9), flag=flag, border=border).SetMinSize(timeDim)    
            # Mute
            OptionBoxSizer.Add(wx.FindWindowByName(mtName['mck5']), pos=(sbsIndex, 10), flag=flag, border=border)      
            OptionBoxSizer.Add(wx.FindWindowByName(mtName['mstart5']), pos=(sbsIndex,11), flag=flag, border=border).SetMinSize(timeDim) 
            OptionBoxSizer.Add(wx.FindWindowByName(mtName['mstop5']), pos=(sbsIndex,12), flag=flag, border=border).SetMinSize(timeDim)        
    
            sbsIndex += 1
            zoneNum += 1     

        # ---------------------------------------------------------------- ZONE 7 -
        if zoneNum < len(zoneNAME):
            zone = 'zone' + str(zoneNum)
    
            if guiFunctions.configMe('volume', zone) is '':
                zonename = zoneNAME[zoneNum]
            else:
                zonename = guiFunctions.configMe('volume', zone)
            
            if '(ZP)' in zonename:
                zonename = zonename.replace('(ZP)','')  
    
            # MONITOR VOLUME - CK, SLIDER, TXTCTRL
            self.ck_Vol1 = wx.CheckBox(self, -1, zonename, name=mvName['ck6'])
            self.ck_Vol1.SetToolTip(wx.ToolTip("Click here to turn on volume monitoring for this zone"))
            self.ck_Vol1.Value = guiFunctions.configMe("volume", mvName['ck6'], bool=True)
            self.sliderZone1 = wx.Slider(self, -1, guiFunctions.configMe("volume", mvName['sl6'], integer=True), 0, 100, size=(sliderWidthHeight), name=mvName['sl6'], style=wx.SL_HORIZONTAL)
            self.tc_zone1 = wx.TextCtrl(panel, -1, guiFunctions.configMe("volume", mvName['sl6']), (0,0), name=mvName['tc6'])
            
            # QUIET VOLUME  - CK, SLIDER, MAX VOL, START, STOP
            self.ck_qVol1 = wx.CheckBox(self, -1, 'Quiet', name=qtName['qck6'])
            self.ck_qVol1.SetToolTip(wx.ToolTip("Click here to turn on quiet hours for this zone"))
            self.ck_qVol1.Value = guiFunctions.configMe("volume", qtName['qck6'], bool=True)
            self.sl_qZone1 = wx.Slider(self, -1, guiFunctions.configMe("volume", qtName['qsl6'], integer=True), 0, 100, size=(sliderWidthHeight), style=wx.SL_HORIZONTAL, name=qtName['qsl6'])
            self.tc_qZone1 = wx.TextCtrl(panel, -1, guiFunctions.configMe("volume", qtName['qsl6']), (0,0), name=qtName['qtc6'])
            self.tc_qZone1hrstart = wx.TextCtrl(panel, -1, guiFunctions.configMe("volume", qtName['qstart6']), (0,0), name=qtName['qstart6'])
            self.tc_qZone1hrstop = wx.TextCtrl(panel, -1, guiFunctions.configMe("volume", qtName['qstop6']), (0,0), name=qtName['qstop6'])
        
            # MUTE VOLUME  - CK, START, STOP
            self.ck_mVol1 = wx.CheckBox(self, -1, 'Mute', name=mtName['mck6'])
            self.ck_mVol1.SetToolTip(wx.ToolTip("Click here to turn on mute hours for this zone"))
            self.ck_mVol1.Value = guiFunctions.configMe("volume", mtName['mck6'], bool=True)
            self.tc_mZone1hrstart = wx.TextCtrl(panel, -1, guiFunctions.configMe("volume", mtName['mstart6']), (0,0), name=mtName['mstart6'])
            self.tc_mZone1hrstop = wx.TextCtrl(panel, -1, guiFunctions.configMe("volume", mtName['mstop6']), (0,0), name=mtName['mstop6'])
    
            # Bind events
            # Monitor
            wx.FindWindowByName(mvName['sl6']).Bind(wx.EVT_SLIDER, lambda event: self.sliderUpdate(event, wx.FindWindowByName(mvName['sl6']), wx.FindWindowByName(mvName['tc6']),), wx.FindWindowByName(mvName['sl6']))
            wx.FindWindowByName(mvName['tc6']).Bind(wx.EVT_CHAR, lambda event: self.tcVolUpdate(event, wx.FindWindowByName(mvName['sl6']), wx.FindWindowByName(mvName['tc6']),), wx.FindWindowByName(mvName['tc6']))
            wx.FindWindowByName(mvName['ck6']).Bind(wx.EVT_CHECKBOX, lambda event: self.zoneCkClick(event, wx.FindWindowByName(mvName['ck6']), wx.FindWindowByName(mvName['sl6']), wx.FindWindowByName(mvName['tc6']),), wx.FindWindowByName(mvName['ck6']))
            # Quiet
            wx.FindWindowByName(qtName['qsl6']).Bind(wx.EVT_SLIDER, lambda event: self.sliderUpdate(event, wx.FindWindowByName(qtName['qsl6']), wx.FindWindowByName(qtName['qtc6']),), wx.FindWindowByName(qtName['qsl6']))
            wx.FindWindowByName(qtName['qtc6']).Bind(wx.EVT_CHAR, lambda event: self.tcVolUpdate(event, wx.FindWindowByName(qtName['qsl6']), wx.FindWindowByName(qtName['qtc6']),), wx.FindWindowByName(qtName['qtc6']))
            wx.FindWindowByName(qtName['qck6']).Bind(wx.EVT_CHECKBOX, lambda event: self.quietCkClick(event, wx.FindWindowByName(qtName['qck6']), wx.FindWindowByName(qtName['qsl6']), wx.FindWindowByName(qtName['qtc6']),wx.FindWindowByName(qtName['qstart6']),wx.FindWindowByName(qtName['qstop6']),), wx.FindWindowByName(qtName['qck6']))
            # Mute
            wx.FindWindowByName(mtName['mck6']).Bind(wx.EVT_CHECKBOX, lambda event: self.muteHoursClick(event, wx.FindWindowByName(mtName['mck6']), wx.FindWindowByName(mtName['mstart6']), wx.FindWindowByName(mtName['mstop6']),), wx.FindWindowByName(mtName['mck6']))
            
            # Add to frame
            # Monitor
            OptionBoxSizer.Add(wx.FindWindowByName(mvName['ck6']), pos=(sbsIndex, 0), flag=flag, border=border)     
            OptionBoxSizer.Add(wx.FindWindowByName(mvName['sl6']), pos=(sbsIndex, 1), span=(1,2),flag=sliderFlag, border=border)
            OptionBoxSizer.Add(wx.FindWindowByName(mvName['tc6']), pos=(sbsIndex, 3), flag=flag, border=border).SetMinSize(volDim)       
            # Quiet
            OptionBoxSizer.Add(wx.FindWindowByName(qtName['qck6']), pos=(sbsIndex, 4), flag=flag, border=border)     
            OptionBoxSizer.Add(wx.FindWindowByName(qtName['qsl6']), pos=(sbsIndex, 5), span=(1,2),flag=sliderFlag, border=border)
            OptionBoxSizer.Add(wx.FindWindowByName(qtName['qtc6']), pos=(sbsIndex, 7), flag=flag, border=border).SetMinSize((volDim))
            OptionBoxSizer.Add(wx.FindWindowByName(qtName['qstart6']), pos=(sbsIndex, 8), flag=flag, border=border).SetMinSize(timeDim) 
            OptionBoxSizer.Add(wx.FindWindowByName(qtName['qstop6']), pos=(sbsIndex, 9), flag=flag, border=border).SetMinSize(timeDim)    
            # Mute
            OptionBoxSizer.Add(wx.FindWindowByName(mtName['mck6']), pos=(sbsIndex, 10), flag=flag, border=border)      
            OptionBoxSizer.Add(wx.FindWindowByName(mtName['mstart6']), pos=(sbsIndex,11), flag=flag, border=border).SetMinSize(timeDim) 
            OptionBoxSizer.Add(wx.FindWindowByName(mtName['mstop6']), pos=(sbsIndex,12), flag=flag, border=border).SetMinSize(timeDim)        
    
            sbsIndex += 1
            zoneNum += 1     

        # ---------------------------------------------------------------- ZONE 8 -
        if zoneNum < len(zoneNAME):
            zone = 'zone' + str(zoneNum)
    
            if guiFunctions.configMe('volume', zone) is '':
                zonename = zoneNAME[zoneNum]
            else:
                zonename = guiFunctions.configMe('volume', zone)
            
            if '(ZP)' in zonename:
                zonename = zonename.replace('(ZP)','')  
    
            # MONITOR VOLUME - CK, SLIDER, TXTCTRL
            self.ck_Vol1 = wx.CheckBox(self, -1, zonename, name=mvName['ck7'])
            self.ck_Vol1.SetToolTip(wx.ToolTip("Click here to turn on volume monitoring for this zone"))
            self.ck_Vol1.Value = guiFunctions.configMe("volume", mvName['ck7'], bool=True)
            self.sliderZone1 = wx.Slider(self, -1, guiFunctions.configMe("volume", mvName['sl7'], integer=True), 0, 100, size=(sliderWidthHeight), name=mvName['sl7'], style=wx.SL_HORIZONTAL)
            self.tc_zone1 = wx.TextCtrl(panel, -1, guiFunctions.configMe("volume", mvName['sl7']), (0,0), name=mvName['tc7'])
            
            # QUIET VOLUME  - CK, SLIDER, MAX VOL, START, STOP
            self.ck_qVol1 = wx.CheckBox(self, -1, 'Quiet', name=qtName['qck7'])
            self.ck_qVol1.SetToolTip(wx.ToolTip("Click here to turn on quiet hours for this zone"))
            self.ck_qVol1.Value = guiFunctions.configMe("volume", qtName['qck7'], bool=True)
            self.sl_qZone1 = wx.Slider(self, -1, guiFunctions.configMe("volume", qtName['qsl7'], integer=True), 0, 100, size=(sliderWidthHeight), style=wx.SL_HORIZONTAL, name=qtName['qsl7'])
            self.tc_qZone1 = wx.TextCtrl(panel, -1, guiFunctions.configMe("volume", qtName['qsl7']), (0,0), name=qtName['qtc7'])
            self.tc_qZone1hrstart = wx.TextCtrl(panel, -1, guiFunctions.configMe("volume", qtName['qstart7']), (0,0), name=qtName['qstart7'])
            self.tc_qZone1hrstop = wx.TextCtrl(panel, -1, guiFunctions.configMe("volume", qtName['qstop7']), (0,0), name=qtName['qstop7'])
        
            # MUTE VOLUME  - CK, START, STOP
            self.ck_mVol1 = wx.CheckBox(self, -1, 'Mute', name=mtName['mck7'])
            self.ck_mVol1.SetToolTip(wx.ToolTip("Click here to turn on mute hours for this zone"))
            self.ck_mVol1.Value = guiFunctions.configMe("volume", mtName['mck7'], bool=True)
            self.tc_mZone1hrstart = wx.TextCtrl(panel, -1, guiFunctions.configMe("volume", mtName['mstart7']), (0,0), name=mtName['mstart7'])
            self.tc_mZone1hrstop = wx.TextCtrl(panel, -1, guiFunctions.configMe("volume", mtName['mstop7']), (0,0), name=mtName['mstop7'])
    
            # Bind events
            # Monitor
            wx.FindWindowByName(mvName['sl7']).Bind(wx.EVT_SLIDER, lambda event: self.sliderUpdate(event, wx.FindWindowByName(mvName['sl7']), wx.FindWindowByName(mvName['tc7']),), wx.FindWindowByName(mvName['sl7']))
            wx.FindWindowByName(mvName['tc7']).Bind(wx.EVT_CHAR, lambda event: self.tcVolUpdate(event, wx.FindWindowByName(mvName['sl7']), wx.FindWindowByName(mvName['tc7']),), wx.FindWindowByName(mvName['tc7']))
            wx.FindWindowByName(mvName['ck7']).Bind(wx.EVT_CHECKBOX, lambda event: self.zoneCkClick(event, wx.FindWindowByName(mvName['ck7']), wx.FindWindowByName(mvName['sl7']), wx.FindWindowByName(mvName['tc7']),), wx.FindWindowByName(mvName['ck7']))
            # Quiet
            wx.FindWindowByName(qtName['qsl7']).Bind(wx.EVT_SLIDER, lambda event: self.sliderUpdate(event, wx.FindWindowByName(qtName['qsl7']), wx.FindWindowByName(qtName['qtc7']),), wx.FindWindowByName(qtName['qsl7']))
            wx.FindWindowByName(qtName['qtc7']).Bind(wx.EVT_CHAR, lambda event: self.tcVolUpdate(event, wx.FindWindowByName(qtName['qsl7']), wx.FindWindowByName(qtName['qtc7']),), wx.FindWindowByName(qtName['qtc7']))
            wx.FindWindowByName(qtName['qck7']).Bind(wx.EVT_CHECKBOX, lambda event: self.quietCkClick(event, wx.FindWindowByName(qtName['qck7']), wx.FindWindowByName(qtName['qsl7']), wx.FindWindowByName(qtName['qtc7']),wx.FindWindowByName(qtName['qstart7']),wx.FindWindowByName(qtName['qstop7']),), wx.FindWindowByName(qtName['qck7']))
            # Mute
            wx.FindWindowByName(mtName['mck7']).Bind(wx.EVT_CHECKBOX, lambda event: self.muteHoursClick(event, wx.FindWindowByName(mtName['mck7']), wx.FindWindowByName(mtName['mstart7']), wx.FindWindowByName(mtName['mstop7']),), wx.FindWindowByName(mtName['mck7']))
            
            # Add to frame
            # Monitor
            OptionBoxSizer.Add(wx.FindWindowByName(mvName['ck7']), pos=(sbsIndex, 0), flag=flag, border=border)     
            OptionBoxSizer.Add(wx.FindWindowByName(mvName['sl7']), pos=(sbsIndex, 1), span=(1,2),flag=sliderFlag, border=border)
            OptionBoxSizer.Add(wx.FindWindowByName(mvName['tc7']), pos=(sbsIndex, 3), flag=flag, border=border).SetMinSize(volDim)       
            # Quiet
            OptionBoxSizer.Add(wx.FindWindowByName(qtName['qck7']), pos=(sbsIndex, 4), flag=flag, border=border)     
            OptionBoxSizer.Add(wx.FindWindowByName(qtName['qsl7']), pos=(sbsIndex, 5), span=(1,2),flag=sliderFlag, border=border)
            OptionBoxSizer.Add(wx.FindWindowByName(qtName['qtc7']), pos=(sbsIndex, 7), flag=flag, border=border).SetMinSize((volDim))
            OptionBoxSizer.Add(wx.FindWindowByName(qtName['qstart7']), pos=(sbsIndex, 8), flag=flag, border=border).SetMinSize(timeDim) 
            OptionBoxSizer.Add(wx.FindWindowByName(qtName['qstop7']), pos=(sbsIndex, 9), flag=flag, border=border).SetMinSize(timeDim)    
            # Mute
            OptionBoxSizer.Add(wx.FindWindowByName(mtName['mck7']), pos=(sbsIndex, 10), flag=flag, border=border)      
            OptionBoxSizer.Add(wx.FindWindowByName(mtName['mstart7']), pos=(sbsIndex,11), flag=flag, border=border).SetMinSize(timeDim) 
            OptionBoxSizer.Add(wx.FindWindowByName(mtName['mstop7']), pos=(sbsIndex,12), flag=flag, border=border).SetMinSize(timeDim)        
    
            sbsIndex += 1
            zoneNum += 1    
    
        # ---------------------------------------------------------------- ZONE 9 -
        if zoneNum < len(zoneNAME):
            zone = 'zone' + str(zoneNum)
    
            if guiFunctions.configMe('volume', zone) is '':
                zonename = zoneNAME[zoneNum]
            else:
                zonename = guiFunctions.configMe('volume', zone)
            
            if '(ZP)' in zonename:
                zonename = zonename.replace('(ZP)','')  
    
            # MONITOR VOLUME - CK, SLIDER, TXTCTRL
            self.ck_Vol1 = wx.CheckBox(self, -1, zonename, name=mvName['ck8'])
            self.ck_Vol1.SetToolTip(wx.ToolTip("Click here to turn on volume monitoring for this zone"))
            self.ck_Vol1.Value = guiFunctions.configMe("volume", mvName['ck8'], bool=True)
            self.sliderZone1 = wx.Slider(self, -1, guiFunctions.configMe("volume", mvName['sl8'], integer=True), 0, 100, size=(sliderWidthHeight), name=mvName['sl8'], style=wx.SL_HORIZONTAL)
            self.tc_zone1 = wx.TextCtrl(panel, -1, guiFunctions.configMe("volume", mvName['sl8']), (0,0), name=mvName['tc8'])
            
            # QUIET VOLUME  - CK, SLIDER, MAX VOL, START, STOP
            self.ck_qVol1 = wx.CheckBox(self, -1, 'Quiet', name=qtName['qck8'])
            self.ck_qVol1.SetToolTip(wx.ToolTip("Click here to turn on quiet hours for this zone"))
            self.ck_qVol1.Value = guiFunctions.configMe("volume", qtName['qck8'], bool=True)
            self.sl_qZone1 = wx.Slider(self, -1, guiFunctions.configMe("volume", qtName['qsl8'], integer=True), 0, 100, size=(sliderWidthHeight), style=wx.SL_HORIZONTAL, name=qtName['qsl8'])
            self.tc_qZone1 = wx.TextCtrl(panel, -1, guiFunctions.configMe("volume", qtName['qsl8']), (0,0), name=qtName['qtc8'])
            self.tc_qZone1hrstart = wx.TextCtrl(panel, -1, guiFunctions.configMe("volume", qtName['qstart8']), (0,0), name=qtName['qstart8'])
            self.tc_qZone1hrstop = wx.TextCtrl(panel, -1, guiFunctions.configMe("volume", qtName['qstop8']), (0,0), name=qtName['qstop8'])
        
            # MUTE VOLUME  - CK, START, STOP
            self.ck_mVol1 = wx.CheckBox(self, -1, 'Mute', name=mtName['mck8'])
            self.ck_mVol1.SetToolTip(wx.ToolTip("Click here to turn on mute hours for this zone"))
            self.ck_mVol1.Value = guiFunctions.configMe("volume", mtName['mck8'], bool=True)
            self.tc_mZone1hrstart = wx.TextCtrl(panel, -1, guiFunctions.configMe("volume", mtName['mstart8']), (0,0), name=mtName['mstart8'])
            self.tc_mZone1hrstop = wx.TextCtrl(panel, -1, guiFunctions.configMe("volume", mtName['mstop8']), (0,0), name=mtName['mstop8'])
    
            # Bind events
            # Monitor
            wx.FindWindowByName(mvName['sl8']).Bind(wx.EVT_SLIDER, lambda event: self.sliderUpdate(event, wx.FindWindowByName(mvName['sl8']), wx.FindWindowByName(mvName['tc8']),), wx.FindWindowByName(mvName['sl8']))
            wx.FindWindowByName(mvName['tc8']).Bind(wx.EVT_CHAR, lambda event: self.tcVolUpdate(event, wx.FindWindowByName(mvName['sl8']), wx.FindWindowByName(mvName['tc8']),), wx.FindWindowByName(mvName['tc8']))
            wx.FindWindowByName(mvName['ck8']).Bind(wx.EVT_CHECKBOX, lambda event: self.zoneCkClick(event, wx.FindWindowByName(mvName['ck8']), wx.FindWindowByName(mvName['sl8']), wx.FindWindowByName(mvName['tc8']),), wx.FindWindowByName(mvName['ck8']))
            # Quiet
            wx.FindWindowByName(qtName['qsl8']).Bind(wx.EVT_SLIDER, lambda event: self.sliderUpdate(event, wx.FindWindowByName(qtName['qsl8']), wx.FindWindowByName(qtName['qtc8']),), wx.FindWindowByName(qtName['qsl8']))
            wx.FindWindowByName(qtName['qtc8']).Bind(wx.EVT_CHAR, lambda event: self.tcVolUpdate(event, wx.FindWindowByName(qtName['qsl8']), wx.FindWindowByName(qtName['qtc8']),), wx.FindWindowByName(qtName['qtc8']))
            wx.FindWindowByName(qtName['qck8']).Bind(wx.EVT_CHECKBOX, lambda event: self.quietCkClick(event, wx.FindWindowByName(qtName['qck8']), wx.FindWindowByName(qtName['qsl8']), wx.FindWindowByName(qtName['qtc8']),wx.FindWindowByName(qtName['qstart8']),wx.FindWindowByName(qtName['qstop8']),), wx.FindWindowByName(qtName['qck8']))
            # Mute
            wx.FindWindowByName(mtName['mck8']).Bind(wx.EVT_CHECKBOX, lambda event: self.muteHoursClick(event, wx.FindWindowByName(mtName['mck8']), wx.FindWindowByName(mtName['mstart8']), wx.FindWindowByName(mtName['mstop8']),), wx.FindWindowByName(mtName['mck8']))
            
            # Add to frame
            # Monitor
            OptionBoxSizer.Add(wx.FindWindowByName(mvName['ck8']), pos=(sbsIndex, 0), flag=flag, border=border)     
            OptionBoxSizer.Add(wx.FindWindowByName(mvName['sl8']), pos=(sbsIndex, 1), span=(1,2),flag=sliderFlag, border=border)
            OptionBoxSizer.Add(wx.FindWindowByName(mvName['tc8']), pos=(sbsIndex, 3), flag=flag, border=border).SetMinSize(volDim)       
            # Quiet
            OptionBoxSizer.Add(wx.FindWindowByName(qtName['qck8']), pos=(sbsIndex, 4), flag=flag, border=border)     
            OptionBoxSizer.Add(wx.FindWindowByName(qtName['qsl8']), pos=(sbsIndex, 5), span=(1,2),flag=sliderFlag, border=border)
            OptionBoxSizer.Add(wx.FindWindowByName(qtName['qtc8']), pos=(sbsIndex, 7), flag=flag, border=border).SetMinSize((volDim))
            OptionBoxSizer.Add(wx.FindWindowByName(qtName['qstart8']), pos=(sbsIndex, 8), flag=flag, border=border).SetMinSize(timeDim) 
            OptionBoxSizer.Add(wx.FindWindowByName(qtName['qstop8']), pos=(sbsIndex, 9), flag=flag, border=border).SetMinSize(timeDim)    
            # Mute
            OptionBoxSizer.Add(wx.FindWindowByName(mtName['mck8']), pos=(sbsIndex, 10), flag=flag, border=border)      
            OptionBoxSizer.Add(wx.FindWindowByName(mtName['mstart8']), pos=(sbsIndex,11), flag=flag, border=border).SetMinSize(timeDim) 
            OptionBoxSizer.Add(wx.FindWindowByName(mtName['mstop8']), pos=(sbsIndex,12), flag=flag, border=border).SetMinSize(timeDim)        
     
            
        # Finalize Static Sizer -----------------------------------------------------------------------------------------------------
        sbsIndex += 1
        zoneNum += 1     
        sbs_Zone.Add(OptionBoxSizer, flag=wx.TOP|wx.BOTTOM|wx.LEFT|wx.RIGHT|wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, border=border)
        sizer.Add(sbs_Zone, pos=(xIndex, 0), span=(1,4),flag=wx.TOP|wx.LEFT|wx.RIGHT|wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, border=5)

        xIndex += 1
    # -------------------------------------------------------------------------
    # [22,23] - LAUNCH / DEFAULTS / AUTOPOP BUTTONS

        # LAUNCH BUTTON
        self.bt_Launch = wx.Button(panel, label="Enable Volume Monitor")
        help_bt_Launch = "Click here to enable the volume monitor."
        self.bt_Launch.SetToolTip(wx.ToolTip(help_bt_Launch))
        self.bt_Launch.Bind(wx.EVT_BUTTON, self.launchVolClick, self.bt_Launch)    
    
        #self.bt_AutoPopulate = wx.Button(panel, label="Autopopulate Sonos Zones")
        #bt_AutoPopulate = "Click here to scan for available zones."
        #self.bt_AutoPopulate.SetToolTip(wx.ToolTip(help_bt_Launch))
        #self.bt_AutoPopulate.Bind(wx.EVT_BUTTON, self.autoPopulateClick, self.bt_AutoPopulate)   
        
        # SAVE AS DEFAULTS
        self.bt_SaveDefaults = wx.Button(panel, label="Save Defaults")
        help_SaveDefaults = "Save current settings as default."
        self.bt_SaveDefaults.SetToolTip(wx.ToolTip(help_SaveDefaults))
        self.bt_SaveDefaults.Bind(wx.EVT_BUTTON, self.bt_SaveDefaultsClick, self.bt_SaveDefaults)
    
        sizer.Add(self.bt_Launch, pos=(xIndex,0), flag=wx.LEFT|wx.EXPAND|wx.RIGHT|wx.ALIGN_LEFT, border=border)
        #sizer.Add(self.bt_AutoPopulate, pos=(xIndex,1), span=(1,2), flag=wx.RIGHT|wx.ALIGN_CENTER, border=border)
        sizer.Add(self.bt_SaveDefaults, pos=(xIndex,3), flag=wx.RIGHT|wx.ALIGN_RIGHT, border=border)

    # -------------------------------------------------------------------------
    # Finalize the sizer
        self.worker = None
        pub.subscribe(self.setVolumePanel, 'setVolumePanel')
        sizer.AddGrowableCol(3)
        panel.SetSizer(sizer)

        # Turn off all buttons/labels that are set to false
        for i in range(0, len(zoneNAME)):
            if wx.FindWindowByName(mvName['ck' + str(i)]).Value == False:
                wx.FindWindowByName(mvName['sl' + str(i)]).Disable()
                wx.FindWindowByName(mvName['tc' + str(i)]).Disable()
            if wx.FindWindowByName(qtName['qck' + str(i)]).Value == False:
                wx.FindWindowByName(qtName['qsl' + str(i)]).Disable()
                wx.FindWindowByName(qtName['qtc' + str(i)]).Disable()      
                wx.FindWindowByName(qtName['qstart' + str(i)]).Disable()      
                wx.FindWindowByName(qtName['qstop' + str(i)]).Disable()      
            if wx.FindWindowByName(mtName['mck' + str(i)]).Value == False:
                wx.FindWindowByName(mtName['mstart' + str(i)]).Disable()      
                wx.FindWindowByName(mtName['mstop' + str(i)]).Disable()  
            if wx.FindWindowByName(mvName['ck' + str(i)]).Label == '<no zone found>':
                wx.FindWindowByName(mvName['ck' + str(i)]).Disable()
                wx.FindWindowByName(mvName['sl' + str(i)]).Disable()
                wx.FindWindowByName(mvName['tc' + str(i)]).Disable()    
                wx.FindWindowByName(qtName['qck' + str(i)]).Disable()
                wx.FindWindowByName(qtName['qsl' + str(i)]).Disable()
                wx.FindWindowByName(qtName['qtc' + str(i)]).Disable()      
                wx.FindWindowByName(qtName['qstart' + str(i)]).Disable()      
                wx.FindWindowByName(qtName['qstop' + str(i)]).Disable()
                wx.FindWindowByName(mtName['mck' + str(i)]).Disable()
                wx.FindWindowByName(mtName['mstart' + str(i)]).Disable()      
                wx.FindWindowByName(mtName['mstop' + str(i)]).Disable()   
                
        # See if we're already running
        cmd_folder = os.path.dirname(os.path.abspath(__file__))
        os.chdir(cmd_folder)      
        os.chdir(os.pardir)     
        os.chdir(os.pardir)         
        if os.path.isfile('volMon.pid') == True: 
            self.bt_Launch.Label = "Disable Volume Monitor"    
            
########################################################################################################################
# BIND Events per the panel above
########################################################################################################################

    def sliderUpdate(self, event, slider, textctrl):
        textctrl.SetValue(str(slider.GetValue()))

    def tcVolUpdate(self, event, slider, textctrl):
        slider.SetValue(int(textctrl.GetValue()))
        
    def zoneCkClick(self, event, ck, slider, textctrl):
        if ck.Value == False:
            slider.Disable()
            textctrl.Disable()
        else:
            slider.Enable()
            textctrl.Enable()

    def quietCkClick(self, event, ck, slider, tc, start, stop):
        if ck.Value == False:
            slider.Disable()
            tc.Disable()
            start.Disable()
            stop.Disable()
        else:
            slider.Enable()
            tc.Enable()
            start.Enable()
            stop.Enable()


    def muteHoursClick(self, event, ck, start, stop):
        if ck.Value == False:
            start.Disable()
            stop.Disable()
        else:
            start.Enable()
            stop.Enable()     

    def serverIPClick(self, event):
        self.tc_serverIP.Value = guiFunctions.getLocalIP()

    def autoPopulateClick(self, event):
        ip_address = self.tc_serverIP.Value
        zoneNAME = guiFunctions.getZones(ip_address, portNum)


    def launchVolClick(self, event):
        cmd_folder = os.path.dirname(os.path.abspath(__file__))
        os.chdir(cmd_folder)        
        
        if self.bt_Launch.Label == "Enable Volume Monitor":
                if os.path.isfile('volMon.pid') == False:    # Then we're not yet running... 
                    os.chdir(os.pardir)             
                    function = subprocess.Popen('pythonw event.py', stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
                    os.chdir(os.pardir)                
                    temp = os.system('wmic process where ^(CommandLine like "pythonw%event%")get ProcessID > volMon.pid 2> nul') 
                    self.bt_Launch.Label = "Disable Volume Monitor"
        else:
            os.chdir(os.pardir)     
            os.chdir(os.pardir) 
            if os.path.isfile('volMon.pid') == True: 
                import codecs
                with codecs.open('volMon.pid', encoding='utf-16') as f:
                    f.readline()
                    windowsPid = f.readline()
                    windowsPid = windowsPid.splitlines()
                    function = subprocess.Popen("TASKKILL /F /PID " + windowsPid[0] + " > nul", stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
                    self.bt_Launch.Label = "Enable Volume Monitor"
            
########################################################################################################################
# setVolumePanel: This is for the pubsub to receive a call to disable or enable the panel buttons.
########################################################################################################################
    def setVolumePanel(self, msg):
        if msg.data == "Disable":
            self.Disable()
        else:
            self.Enable()

########################################################################################################################
# bt_SaveDefaultsClick: A simple function to write out the defaults for the panel to GUIpref.ini
########################################################################################################################
    def bt_SaveDefaultsClick(self, event):
        zoneNAME = guiFunctions.getZones(ip_address, portNum)
  
        section = "volume"
        guiFunctions.configWrite(section, "serverip", self.tc_serverIP.Value)
            
        curZoneNum = 0
        for i in range(0, len(zoneNAME)):
            guiFunctions.configWrite(section, "ck" + str(i), wx.FindWindowByName('ck' + str(i)).GetValue())
            guiFunctions.configWrite(section, "zone" + str(i), str(wx.FindWindowByName('ck' + str(i)).Label))
            guiFunctions.configWrite(section, "sliderzone" + str(i), wx.FindWindowByName('sliderZone' + str(i)).GetValue())
            
            guiFunctions.configWrite(section, "qck" + str(i), wx.FindWindowByName('qck' + str(i)).GetValue())
            guiFunctions.configWrite(section, "sliderq" + str(i), wx.FindWindowByName('sliderq' + str(i)).GetValue())
            guiFunctions.configWrite(section, "startquiet" + str(i), wx.FindWindowByName('startquiet' + str(i)).GetValue())
            guiFunctions.configWrite(section, "stopquiet" + str(i), wx.FindWindowByName('stopquiet' + str(i)).GetValue())
            guiFunctions.configWrite(section, "mck" + str(i), wx.FindWindowByName('mck' + str(i)).GetValue())
            guiFunctions.configWrite(section, "startmute" + str(i), wx.FindWindowByName('startmute' + str(i)).GetValue())
            guiFunctions.configWrite(section, "stopmute" + str(i), wx.FindWindowByName('stopmute' + str(i)).GetValue())
            
            if wx.FindWindowByName('ck' + str(i)).GetValue() == True:
                if guiFunctions.configMe(str(wx.FindWindowByName('ck' + str(i)).Label), "max_volume") != '':
                    guiFunctions.configWrite(str(wx.FindWindowByName('ck' + str(i)).Label), "max_volume", wx.FindWindowByName('sliderZone' + str(i)).GetValue())
                    guiFunctions.configWrite(str(wx.FindWindowByName('ck' + str(i)).Label), "quiet_volume", wx.FindWindowByName('sliderq' + str(i)).GetValue())
                    guiFunctions.configWrite(str(wx.FindWindowByName('ck' + str(i)).Label), "quiet_start", wx.FindWindowByName('startquiet' + str(i)).GetValue())
                    guiFunctions.configWrite(str(wx.FindWindowByName('ck' + str(i)).Label), "quiet_stop", wx.FindWindowByName('stopquiet' + str(i)).GetValue())
                    guiFunctions.configWrite(str(wx.FindWindowByName('ck' + str(i)).Label), "mute_start", wx.FindWindowByName('startmute' + str(i)).GetValue())
                    guiFunctions.configWrite(str(wx.FindWindowByName('ck' + str(i)).Label), "mute_stop", wx.FindWindowByName('stopmute' + str(i)).GetValue())
                else:
                    guiFunctions.configWrite(str(wx.FindWindowByName('ck' + str(i)).Label), "max_volume", wx.FindWindowByName('sliderZone' + str(i)).GetValue())
                    guiFunctions.configWrite(str(wx.FindWindowByName('ck' + str(i)).Label), "quiet_volume", wx.FindWindowByName('sliderq' + str(i)).GetValue())
                    guiFunctions.configWrite(str(wx.FindWindowByName('ck' + str(i)).Label), "quiet_start", wx.FindWindowByName('startquiet' + str(i)).GetValue())
                    guiFunctions.configWrite(str(wx.FindWindowByName('ck' + str(i)).Label), "quiet_stop", wx.FindWindowByName('stopquiet' + str(i)).GetValue())
                    guiFunctions.configWrite(str(wx.FindWindowByName('ck' + str(i)).Label), "mute_start", wx.FindWindowByName('startmute' + str(i)).GetValue())
                    guiFunctions.configWrite(str(wx.FindWindowByName('ck' + str(i)).Label), "mute_stop", wx.FindWindowByName('stopmute' + str(i)).GetValue())   
                    
        self.saveDefaults()
    
    def saveDefaults(self):
        zoneNAME = guiFunctions.getZones(ip_address, portNum)
            
        curZoneNum = 0
        for i in range(0, len(zoneNAME)): 
 # make this dynamic later when widgets are moved.
            if wx.FindWindowByName('ck' + str(i)).GetValue() == True:
                if guiFunctions.configMe(str(wx.FindWindowByName('ck' + str(i)).Label), "max_volume") != '':
                    guiFunctions.configWrite(str(wx.FindWindowByName('ck' + str(i)).Label), "max_volume", wx.FindWindowByName('sliderZone' + str(i)).GetValue())
                    guiFunctions.configWrite(str(wx.FindWindowByName('ck' + str(i)).Label), "quiet_volume", wx.FindWindowByName('sliderq' + str(i)).GetValue())
                    guiFunctions.configWrite(str(wx.FindWindowByName('ck' + str(i)).Label), "quiet_start", wx.FindWindowByName('startquiet' + str(i)).GetValue())
                    guiFunctions.configWrite(str(wx.FindWindowByName('ck' + str(i)).Label), "quiet_stop", wx.FindWindowByName('stopquiet' + str(i)).GetValue())
                    guiFunctions.configWrite(str(wx.FindWindowByName('ck' + str(i)).Label), "mute_start", wx.FindWindowByName('startmute' + str(i)).GetValue())
                    guiFunctions.configWrite(str(wx.FindWindowByName('ck' + str(i)).Label), "mute_stop", wx.FindWindowByName('stopmute' + str(i)).GetValue())
                else:
                    guiFunctions.configWrite(str(wx.FindWindowByName('ck' + str(i)).Label), "max_volume", wx.FindWindowByName('sliderZone' + str(i)).GetValue())
                    guiFunctions.configWrite(str(wx.FindWindowByName('ck' + str(i)).Label), "quiet_volume", wx.FindWindowByName('sliderq' + str(i)).GetValue())
                    guiFunctions.configWrite(str(wx.FindWindowByName('ck' + str(i)).Label), "quiet_start", wx.FindWindowByName('startquiet' + str(i)).GetValue())
                    guiFunctions.configWrite(str(wx.FindWindowByName('ck' + str(i)).Label), "quiet_stop", wx.FindWindowByName('stopquiet' + str(i)).GetValue())
                    guiFunctions.configWrite(str(wx.FindWindowByName('ck' + str(i)).Label), "mute_start", wx.FindWindowByName('startmute' + str(i)).GetValue())
                    guiFunctions.configWrite(str(wx.FindWindowByName('ck' + str(i)).Label), "mute_stop", wx.FindWindowByName('stopmute' + str(i)).GetValue())                    
        guiFunctions.statusText(self, "Defaults saved...")

    
    




        
        
        
        
        
        
        

        
    