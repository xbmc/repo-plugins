#################################################################################################
# http image proxy server 
# This acts as a HTTP Image proxy server for all thumbs and artwork requests
# this is needed due to the fact XBMC can not use the MB3 API as it has issues with the HTTP response format
# this proxy handles all the requests and allows XBMC to call the MB3 server
#################################################################################################

import xbmc
import xbmcgui
import xbmcaddon
import time
from urlparse import parse_qs
import urllib

from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from threading import Thread
from SocketServer import ThreadingMixIn

class ThreadingHTTPServer(ThreadingMixIn, HTTPServer):
    pass
    
class MyHandler(BaseHTTPRequestHandler):
    
    logLevel = 0
    
    def __init__(self, *args):
        addonSettings = xbmcaddon.Addon(id='plugin.video.xbmb3c')
        level = addonSettings.getSetting('logLevel')
        self.logLevel = 0
        if(level != None):
            self.logLevel = int(level)
        BaseHTTPRequestHandler.__init__(self, *args)
    
    def logMsg(self, msg, level = 1):
        if(self.logLevel >= level):
            xbmc.log("XBMB3C ImageProxy -> " + msg)
    
    #overload the default log func to stop stderr message from showing up in the xbmc log
    def log_message(self, format, *args):
        if(self.logLevel >= 1):
            the_string = [str(i) for i in range(len(args))]
            the_string = '"{' + '}" "{'.join(the_string) + '}"'
            the_string = the_string.format(*args)
            xbmc.log("XBMB3C ImageProxy -> BaseHTTPRequestHandler : " + the_string)
        return    
    
    def do_GET(self):
    
        addonSettings = xbmcaddon.Addon(id='plugin.video.xbmb3c')
        mb3Host = addonSettings.getSetting('ipaddress')
        mb3Port = addonSettings.getSetting('port')
        
        params = parse_qs(self.path[2:])
        self.logMsg("Params : " + str(params))
        
        if(params.get("id") == None and params.get("name") == None):
            return
            
        if(params.get("id") != None):
            itemId = params.get("id")[0]
        else:
            itemId = None
            
        imageType = params.get("type")[0]
        indexParam = params.get("index")
        maxheight = params.get("maxheight")
            
        if (indexParam != None):
          self.logMsg("Params with Index: " + str(params), level=2)  
          index = indexParam[0]
        else:
          index = None
          
        if(params.get("name") != None):
            name = params.get("name")[0]
        else:
            name = None;
          
        # TODO: add option to return PNG or JPG
        if (name != None):
            remoteUrl = "http://" + mb3Host + ":" + mb3Port + "/mediabrowser/Persons/" + name + "/Images/" + imageType  + "?Format=original"
        elif (index == None):  
            remoteUrl = "http://" + mb3Host + ":" + mb3Port + "/mediabrowser/Items/" + itemId + "/Images/" + imageType  + "?Format=original"
        else:
            remoteUrl = "http://" + mb3Host + ":" + mb3Port + "/mediabrowser/Items/" + itemId + "/Images/" + imageType +  "/" + index  + "?Format=original"
          
        if(maxheight != None):
            remoteUrl = remoteUrl + "&maxheight=" + maxheight[0]
                  
        self.logMsg("MB3 Host : " + mb3Host, level=2)
        self.logMsg("MB3 Port : " + mb3Port, level=2)
        self.logMsg("Item ID : " + str(itemId), level=2)
        self.logMsg("Image Type : " + imageType, level=2)
        self.logMsg("Remote URL : " + remoteUrl, level=2)
        
        # get the remote image
        self.logMsg("Downloading Image", level=2)
        
        try:
            requesthandle = urllib.urlopen(remoteUrl, proxies={})
            pngData = requesthandle.read()
            requesthandle.close()            
        except Exception, e:
            xbmc.log("XBMB3C ImageProxy -> MyHandler urlopen : " + str(e) + " (" + remoteUrl + ")")
            return

        datestring = time.strftime('%a, %d %b %Y %H:%M:%S GMT')
        length = len(pngData)
        
        self.logMsg("ReSending Image", level=2)
        self.send_response(200)
        self.send_header('Content-type', 'image/png')
        self.send_header('Content-Length', length)
        self.send_header('Last-Modified', datestring)        
        self.end_headers()
        self.wfile.write(pngData)
        self.logMsg("Image Sent")
        
    def do_HEAD(self):
        datestring = time.strftime('%a, %d %b %Y %H:%M:%S GMT')
        self.send_response(200)
        self.send_header('Content-type', 'image/png')
        self.send_header('Last-Modified', datestring)
        self.end_headers()        
        
