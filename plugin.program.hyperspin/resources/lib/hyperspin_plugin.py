

"""
    Plugin for Launching HyperSpin
"""

import sys
import os
import fnmatch
import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon

import time
import re
import urllib
import subprocess_hack
import xml.dom.minidom
import socket
import exceptions

import random
from traceback import print_exc

import shutil



from xbmcaddon import Addon






class Main:
    
   


    def __init__( self ):
        addon = xbmcaddon.Addon()
        icon = addon.getAddonInfo('icon')
        language = addon.getLocalizedString
        path = addon.getSetting('hyperspinexe')
        if path == "":
        	xbmc.executebuiltin("XBMC.Notification(%s,%s,10000,%s)"%(language(30003), language(30002), icon))
        	addon.openSettings()
        path = addon.getSetting('hyperspinexe')
        if path == "":
        	return
        path2 = addon.getSetting('hyperspinfolder')
        if path2 == "":
        	xbmc.executebuiltin("XBMC.Notification(%s,%s,10000,%s)"%(language(30003), language(30002), icon))
        	addon.openSettings()
        path2 = addon.getSetting('hyperspinfolder')
        if path2 == "":
        	return
        if ( xbmc.Player().isPlaying() ):
        	xbmc.executebuiltin('PlayerControl(Play)')
        xbmc.sleep(400)            
        
        
        


        info = None
        ap = path
        arguments = "-quick"
        apppath = path2
        startproc = subprocess_hack.Popen(r'%s %s' % (ap, arguments), cwd=apppath, startupinfo=info)
   


 
        startproc.wait()
        xbmc.sleep(200)

        systemLabel = xbmc.getInfoLabel("System.BuildVersion")
        majorVersion = int(systemLabel[:2])
        if(majorVersion > 13):
            ap = xbmc.translatePath("special://xbmc") + "\\xbmc.exe"
        else:
            ap = xbmc.translatePath("special://xbmc") + "\\kodi.exe"
        
        
        arguments = ""
        apppath = xbmc.translatePath("special://xbmc")
        startproc = subprocess_hack.Popen(r'%s %s' % (ap, arguments), cwd=apppath, startupinfo=info)
 
        # startproc.wait()
        xbmc.sleep(200)
        xbmc.executebuiltin('PlayerControl(Play)') 
	xbmc.sleep(400)
	xbmc.executebuiltin('ActivateWindow(home)')
        
        

 


