# coding: utf-8
'''
Created on 18 sep 2011

@author: Emuller
'''
import os,sys
import urllib,urllib2,re
import string
from xml.dom import minidom
import xbmc,xbmcplugin,xbmcgui,xbmcaddon

class iZECore(object):
    __addonname__ = sys.modules["__main__"].__addonname__
    
    # control id's
    CONTROL_MAIN_LIST_START  = 50
    CONTROL_MAIN_LIST_END    = 59
    
    def getParameters(self, parameters):
        ''' Convert parameters encoded in a URL to a dict. '''
        paramDict = {}
        if parameters:
            paramPairs = parameters[1:].split("&")
            for paramsPair in paramPairs:
                paramSplits = paramsPair.split('=')
                if (len(paramSplits)) == 2:
                    if type(paramSplits[1]).__name__ == "str":
                        paramDict[paramSplits[0]] = urllib.unquote_plus(paramSplits[1])
                    else:
                        paramDict[paramSplits[0]] = paramSplits[1]
                        
        return paramDict

    def getJsonResponse(self, url):
    
        response = urllib2.urlopen(url)
        responsetext = response.read()
        objs = xbmc.executeJSONRPC(responsetext)
        response.close()
        
        return objs
    
    def getXmlResponse(self, url):
        self.log_notice("getXmlResponse from " + url)
        response = urllib2.urlopen(url)
        encoding = re.findall("charset=([a-zA-Z0-9\-]+)", response.headers['content-type'])
        responsetext = unicode( response.read(), encoding[0] );
        xmldoc = minidom.parseString(responsetext.encode("utf-8"))
        response.close()
        return xmldoc
    
    def getHttpResponse(self, url):
        self.log_notice("getHttpResponse from " + url)
        response = urllib2.urlopen(url)
        encoding = re.findall("charset=([a-zA-Z0-9\-]+)", response.headers['content-type'])
        responsetext = unicode( response.read(), encoding[0] );
        response.close()
        return responsetext.encode("utf-8")
    
    
    def getKeyboardInput(self, title = "Input", default="", hidden=False):
        result = None
            
        kbd = xbmc.Keyboard(default, title)
        kbd.setHiddenInput(hidden)
        kbd.doModal()
        
        if kbd.isConfirmed():
            result = kbd.getText()
        
        return result
    
    def getCurrentViewmode(self):
        for id in range( self.CONTROL_MAIN_LIST_START, self.CONTROL_MAIN_LIST_END + 1 ):
            try:
                if xbmc.getCondVisibility( "Control.IsVisible(%i)" % id ):
                    break
            except:
                print_exc()
        return id

    def log_notice(self, msg):
        xbmc.output("### [%s] - %s" % (self.__addonname__,msg,),level=xbmc.LOGNOTICE )
    
    def showMessage(self, heading, message, duration=10):
        xbmc.executebuiltin('XBMC.Notification("%s", "%s", %s)' % ( heading, message, duration) )
    
    def parseBoolString(self, theString):
        return theString[0].upper()=='T'
        