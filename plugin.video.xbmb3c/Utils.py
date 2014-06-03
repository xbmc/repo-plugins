#################################################################################################
# utils class
#################################################################################################

import xbmc
import xbmcgui
import xbmcaddon

import json
import threading
from datetime import datetime
import urllib

###########################################################################
class PlayUtils():
    @staticmethod
    def getPlayUrl(server, id, result):
      addonSettings = xbmcaddon.Addon(id='plugin.video.xbmb3c')  
      if addonSettings.getSetting('playFromStream') == 'false':
        playurl = result.get("Path")
        if ":\\" in playurl:
            xbmcgui.Dialog().ok(addonSettings.getLocalizedString(30130), addonSettings.getLocalizedString(30131) + playurl)
            sys.exit()
        USER_AGENT = 'QuickTime/7.7.4'
        
        if (result.get("VideoType") == "Dvd"):
            playurl = playurl + "/VIDEO_TS/VIDEO_TS.IFO"
        if (result.get("VideoType") == "BluRay"):
            playurl = playurl + "/BDMV/index.bdmv"            
        if addonSettings.getSetting('smbusername') == '':
            playurl = playurl.replace("\\\\", "smb://")
        else:
            playurl = playurl.replace("\\\\", "smb://" + addonSettings.getSetting('smbusername') + ':' + addonSettings.getSetting('smbpassword') + '@')
        playurl = playurl.replace("\\", "/")
        
        if ("apple.com" in playurl):
            playurl += '?|User-Agent=%s' % USER_AGENT
            
      elif addonSettings.getSetting('transcode') == 'true':
          if result.get("Type") == "Audio":
            playurl = 'http://' + server + '/mediabrowser/Audio/' + id + '/stream.mp3'
          else:
            playurl = 'http://' + server + '/mediabrowser/Videos/' + id + '/stream.ts'  
      else:
          if result.get("Type") == "Audio":
            playurl = 'http://' + server + '/mediabrowser/Audio/' + id + '/stream?static=true'
          else:
            playurl = 'http://' + server + '/mediabrowser/Videos/' + id + '/stream?static=true' 
            
      return playurl.encode('utf-8')

        
