"""
    Copyright (C) 2020 Scott Ware
    This file is part of Scoot Media Streamer (plugin.video.sms)
    SPDX-License-Identifier: GPL-3.0-only
    See LICENSE.txt for more information
"""

################################################################################################

from operator import itemgetter
from bottle import route, run
from threading import Thread
import os
import sys
import copy
import urllib
import requests
import time
import uuid
import json
import xbmcaddon
import xbmcgui
import xbmcplugin
import xbmc

################################################################################################

addon = xbmcaddon.Addon('plugin.video.sms')
addon_path = addon.getAddonInfo('path')
libs = xbmc.translatePath(os.path.join(addon_path, 'resources', 'lib'))
sys.path.append(libs)

################################################################################################

import sms
import client
import bottle_ext

################################################################################################

CLIENT = 4
FORMATS = [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18]
CODECS = [10,11,12,13,20,30,31,32,40,1000,1001,1002,1003,1004,1005,1006,1007,1008,1009,1010,1011,2000,2001,2002,2003,2004]
MCH_CODECS = [1000,1001,1002,1003,1004,1005,1006,1008,1009,1010,1011]
FORMAT = 9

class Service(object):
    def __init__(self):
        # Settings
        self.settings = {\
            'serverUrl': addon.getSettingString('serverUrl'), \
            'serverPort': addon.getSettingInt('serverPort'), \
            'username': addon.getSettingString('username'), \
            'password': addon.getSettingString('password'), \
            'audioQuality': addon.getSettingInt('audioQuality'), \
            'videoQuality': addon.getSettingInt('videoQuality'), \
            'maxSampleRate': addon.getSettingString('maxSampleRate'), \
            'multichannel': addon.getSettingBool('multichannel'), \
            'directPlay': addon.getSettingBool('directPlay'),
            'servicePort': addon.getSettingInt('servicePort')}

        # SMS Server Client
        self.serverClient = client.RESTClient(self.settings)
        
        # Session ID
        self.sessionId = uuid.uuid4()
        
        # Client Profile
        self.updateClientProfile()
        
        # Monitor
        self.monitor = SMSMonitor(settings_action = self.updateSettings)
        
        # REST Service
        @route('/session')
        def getSession():
            return str(self.sessionId)
            
        @route('/update')
        def update():
            self.updateSettings()
            
        self.server = bottle_ext.WSGIServer(host='localhost', port=self.settings['servicePort'])
        
        self.start()

    def start(self):
        # Initialise session
        self.serverClient.addSession(self.sessionId, self.clientProfile.__dict__)
        
        # Start REST server
        Thread(target=self.rest).start()
     
        # Main Loop
        while not self.monitor.abortRequested():
            if self.monitor.waitForAbort(1):
                # Abort was requested while waiting.
                self.shutdown()
                break
    
    def shutdown(self):
        self.serverClient.endSession(self.sessionId)
        self.server.shutdown()
        
    def rest(self):
        run(server=self.server)
        
    def updateSettings(self):
        # Make a copy of our existing settings and client profile
        old_settings = copy.deepcopy(self.settings)
        old_client_profile = copy.deepcopy(self.clientProfile)
        
        self.settings = {\
            'serverUrl': addon.getSettingString('serverUrl'), \
            'serverPort': addon.getSettingInt('serverPort'), \
            'username': addon.getSettingString('username'), \
            'password': addon.getSettingString('password'), \
            'audioQuality': addon.getSettingInt('audioQuality'), \
            'videoQuality': addon.getSettingInt('videoQuality'), \
            'maxSampleRate': addon.getSettingString('maxSampleRate'), \
            'multichannel': addon.getSettingBool('multichannel'), \
            'directPlay': addon.getSettingBool('directPlay'),
            'servicePort': addon.getSettingInt('servicePort')}
            
        # Update client profile
        self.updateClientProfile()
            
        # Check server URL and port
        if old_settings['serverUrl'] != self.settings['serverUrl'] or old_settings['serverPort'] != self.settings['serverPort']:
            # Create a new REST client and add session
            self.serverClient = client.RESTClient(self.settings)
            self.serverClient.addSession(self.sessionId, self.clientProfile.__dict__)
        elif old_client_profile.__dict__ != self.clientProfile.__dict__:
            # Update client profile
            self.serverClient.updateClientProfile(self.sessionId, self.clientProfile.__dict__)
            
        # Check service port
        if old_settings['servicePort'] != self.settings['servicePort']:
            # Shutdown existing REST server
            self.server.shutdown()
            
            # Create new REST server
            self.server = bottle_ext.WSGIServer(host='localhost', port=self.settings['servicePort'])
            Thread(target=self.rest).start()
            
    def updateClientProfile(self):
        # Get Kodi native settings
        replaygain = json.loads(xbmc.executeJSONRPC('{ "jsonrpc": "2.0", "method": "Settings.GetSettingValue", "params":{"setting":"musicplayer.replaygaintype"}, "id":1 }'))["result"]["value"]
        
        self.clientProfile = sms.ClientProfile(CLIENT, FORMAT, FORMATS, CODECS, None, self.settings['videoQuality'], self.settings['audioQuality'], 0, self.settings['maxSampleRate'], sms.replaygain[replaygain], self.settings['directPlay'])
        
        if self.settings['multichannel'] == True:
            self.clientProfile.mchCodecs = MCH_CODECS
        
class SMSMonitor(xbmc.Monitor):
     def __init__(self, *args, **kwargs):
         xbmc.Monitor.__init__(self)
         self.settingsAction = kwargs['settings_action']
         
     def onSettingsChanged(self):
         self.settingsAction()

if __name__ == '__main__':
    Service()

