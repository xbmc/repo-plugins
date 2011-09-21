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

import iZECore 

izecore = iZECore.iZECore()


class YoutubeCore(object):
    def getVideosByTrackName(self, artist, name, limit=1):
        
        ''' try exact search first '''
        
        q = '"' + artist + " - " + name + '"'
        url = "http://gdata.youtube.com/feeds/api/videos?max-results=%d&v=2&category=Music&format=5&start-index=1&q=%s" % ( limit, urllib.quote_plus( q ) )
        
        xmldoc = izecore.getXmlResponse(url)
        
        entries = xmldoc.getElementsByTagName("entry")
        
        if (entries.length<=0):
            ''' try less exact search '''
            q = artist + " " + name
            url = "http://gdata.youtube.com/feeds/api/videos?max-results=%d&v=2&category=Music&format=5&start-index=1&q=%s" % ( limit, urllib.quote_plus( q ) )
            
            xmldoc = izecore.getXmlResponse(url)
            
            entries = xmldoc.getElementsByTagName("entry") 
        
        return entries