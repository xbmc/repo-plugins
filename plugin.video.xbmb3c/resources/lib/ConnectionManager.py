#################################################################################################
# connection manager class
#################################################################################################

import xbmc
import xbmcgui
import xbmcaddon

import json
import threading
from datetime import datetime
from DownloadUtils import DownloadUtils
import urllib
import sys

#define our global download utils
downloadUtils = DownloadUtils()
logLevel = 1
###########################################################################
class ConnectionManager():
    
    addonSettings = None
    __addon__       = xbmcaddon.Addon(id='plugin.video.xbmb3c')
    __addondir__    = xbmc.translatePath( __addon__.getAddonInfo('profile') ) 
    __language__     = __addon__.getLocalizedString
    
    def printDebug(self, msg, level = 1):
        if(logLevel >= level):
            if(logLevel == 2):
                try:
                    xbmc.log("XBMB3C " + str(level) + " -> " + inspect.stack()[1][3] + " : " + str(msg))
                except UnicodeEncodeError:
                    xbmc.log("XBMB3C " + str(level) + " -> " + inspect.stack()[1][3] + " : " + str(msg.encode('utf-8')))
            else:
                try:
                    xbmc.log("XBMB3C " + str(level) + " -> " + str(msg))
                except UnicodeEncodeError:
                    xbmc.log("XBMB3C " + str(level) + " -> " + str(msg.encode('utf-8')))

    def checkServer(self):
        
        self.printDebug ("XBMB3C Connection Manager Called")
        self.addonSettings = xbmcaddon.Addon(id='plugin.video.xbmb3c')
        port = self.addonSettings.getSetting('port')
        host = self.addonSettings.getSetting('ipaddress')
        
        if(len(host) != 0 and host != "<none>"):
            self.printDebug ("XBMB3C server already set")
            return
        
        serverInfo = self.getServerDetails()
        
        if(serverInfo == None):
            self.printDebug ("XBMB3C getServerDetails failed")
            return
            
        index = serverInfo.find(":")
        
        if(index <= 0):
            self.printDebug ("XBMB3C getServerDetails data not correct : " + serverInfo)
            return
        
        server_address = serverInfo[:index]
        server_port = serverInfo[index+1:]
        self.printDebug ("XBMB3C detected server info " + server_address + " : " + server_port)
        
        xbmcgui.Dialog().ok(__language__(30167), __language__(30168), __language__(30169) + server_address, __language__(30030) + server_port)
    
        # get a list of users
        self.printDebug ("Getting user list")
        jsonData = None
        try:
            jsonData = downloadUtils.downloadUrl(server_address + ":" + server_port + "/mediabrowser/Users/Public?format=json")
        except Exception, msg:
            error = "Get User unable to connect to " + server_address + ":" + server_port + " : " + str(msg)
            xbmc.log (error)
            return ""
        
        if(jsonData == False):
            return
    
        self.printDebug("jsonData : " + str(jsonData), level=2)
        result = json.loads(jsonData)
        
        names = []
        userList = []
        for user in result:
            name = user.get("Name")
            userList.append(name)
            if(user.get("HasPassword") == True):
                name = name + " (Secure)"
            names.append(name)
    
        self.printDebug ("User List : " + str(names))
        self.printDebug ("User List : " + str(userList))
        return_value = xbmcgui.Dialog().select(__language__(30200), names)
        
        if(return_value > -1):
            selected_user = userList[return_value]
            self.printDebug("Setting Selected User : " + selected_user)
            if self.addonSettings.getSetting("port") != server_port:
                self.addonSettings.setSetting("port", server_port)
            if self.addonSettings.getSetting("ipaddress") != server_address:        
                self.addonSettings.setSetting("ipaddress", server_address)        
            if self.addonSettings.getSetting("username") != selected_user:          
                self.addonSettings.setSetting("username", selected_user)
                
    def getServerDetails(self):

        self.printDebug("Getting Server Details from Network")
    
        MESSAGE = "who is MediaBrowserServer?"
        #MULTI_GROUP = ("224.3.29.71", 7359)
        #MULTI_GROUP = ("127.0.0.1", 7359)
        MULTI_GROUP = ("<broadcast>", 7359)
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(6.0)
        
        #ttl = struct.pack('b', 20)
        #sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 20)
        
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.setsockopt(socket.SOL_IP, socket.IP_MULTICAST_LOOP, 1)
        sock.setsockopt(socket.IPPROTO_IP, socket.SO_REUSEADDR, 1)
        
        xbmc.log("MutliGroup       : " + str(MULTI_GROUP));
        xbmc.log("Sending UDP Data : " + MESSAGE);
        sock.sendto(MESSAGE, MULTI_GROUP)
    
        try:
            data, addr = sock.recvfrom(1024) # buffer size is 1024 bytes
            xbmc.log("Received Response : " + data)
            if(data[0:18] == "MediaBrowserServer"):
                xbmc.log("Found Server : " + data[19:])
                return data[19:]
        except:
            xbmc.log("No UDP Response")
            pass
        
        return None
      
