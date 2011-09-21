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


class LastFMCore(object):     
    __lastfmapikey__ = sys.modules["__main__"].__lastfmapikey__
    
    def Tag_getTopTracks(self, tag, limit=150):
        ''' retrieve genre tracks'''
        url = "http://ws.audioscrobbler.com/2.0/?method=tag.gettoptracks&tag=%s&limit=%d&api_key=%s" % ( urllib.quote_plus(tag), limit, self.__lastfmapikey__ )
        
        xmldoc = izecore.getXmlResponse(url)
        
        return xmldoc.getElementsByTagName("track")
    
    def Tag_getTopAlbums(self, tag, limit=50):
        url = "http://ws.audioscrobbler.com/2.0/?method=tag.gettopalbums&tag=%s&limit=%d&api_key=%s" % ( urllib.quote_plus(tag), limit, self.__lastfmapikey__ )
        
        xmldoc = izecore.getXmlResponse(url)
        
        return xmldoc.getElementsByTagName("album")
    
    def Tag_getTopArtists(self, tag, limit=50):
        url = "http://ws.audioscrobbler.com/2.0/?method=tag.gettopartists&tag=%s&limit=%d&api_key=%s" % ( urllib.quote_plus(tag), limit, self.__lastfmapikey__ )
        
        xmldoc = izecore.getXmlResponse(url)
        
        return xmldoc.getElementsByTagName("artist")
    
    def Artist_getTopAlbums(self, artist, limit=50):
        url = "http://ws.audioscrobbler.com/2.0/?method=artist.gettopalbums&artist=%s&limit=%d&api_key=%s" % ( urllib.quote_plus(artist), limit, self.__lastfmapikey__ )
        
        xmldoc = izecore.getXmlResponse(url)
        
        return xmldoc.getElementsByTagName("album")
    
    def Artist_getTopTracks(self, artist, limit=150):
        url = "http://ws.audioscrobbler.com/2.0/?method=artist.gettoptracks&artist=%s&limit=%d&api_key=%s" % ( urllib.quote_plus(artist), limit, self.__lastfmapikey__ )
        
        xmldoc = izecore.getXmlResponse(url)
        
        return xmldoc.getElementsByTagName("track")
    
    def Artist_getSimilar(self, artist, limit=50):
        url = "http://ws.audioscrobbler.com/2.0/?method=artist.getsimilar&artist=%s&limit=%d&api_key=%s" % ( urllib.quote_plus(artist), limit, self.__lastfmapikey__ )
        
        xmldoc = izecore.getXmlResponse(url)
        
        return xmldoc.getElementsByTagName("artist")
    
    def Chart_getHypedArtists(self, limit=50):
        url = "http://ws.audioscrobbler.com/2.0/?method=chart.gethypedartists&limit=%d&api_key=%s" % ( limit, self.__lastfmapikey__ )
        
        xmldoc = izecore.getXmlResponse(url)
        
        return xmldoc.getElementsByTagName("artist")
        
    def Chart_getHypedTracks(self, limit=150):
        url = "http://ws.audioscrobbler.com/2.0/?method=chart.gethypedtracks&limit=%d&api_key=%s" % ( limit, self.__lastfmapikey__ )
        
        xmldoc = izecore.getXmlResponse(url)
        
        return xmldoc.getElementsByTagName("track")       
    
    def Chart_getLovedTracks(self, limit=150):
        url = "http://ws.audioscrobbler.com/2.0/?method=chart.getlovedtracks&limit=%d&api_key=%s" % ( limit, self.__lastfmapikey__ )
        
        xmldoc = izecore.getXmlResponse(url)
        
        return xmldoc.getElementsByTagName("track")  
    
    def Chart_getTopArtists(self, limit=50):
        url = "http://ws.audioscrobbler.com/2.0/?method=chart.gettopartists&limit=%d&api_key=%s" % ( limit, self.__lastfmapikey__ )
        
        xmldoc = izecore.getXmlResponse(url)
        
        return xmldoc.getElementsByTagName("artist")
    
    def Chart_getTopTracks(self, limit=150):
        url = "http://ws.audioscrobbler.com/2.0/?method=chart.gettoptracks&limit=%d&api_key=%s" % ( limit, self.__lastfmapikey__ )
        
        xmldoc = izecore.getXmlResponse(url)
        
        return xmldoc.getElementsByTagName("track")
    
    def Album_getInfo(self, artist, album):
        url = "http://ws.audioscrobbler.com/2.0/?method=album.getinfo&artist=%s&album=%s&api_key=%s" % ( urllib.quote_plus(artist), urllib.quote_plus(album), self.__lastfmapikey__ )
        
        xmldoc = izecore.getXmlResponse(url)
        
        return xmldoc.getElementsByTagName("track")
    
    def Album_getInfoByMBID(self, mbid):
        url = "http://ws.audioscrobbler.com/2.0/?method=album.getinfo&mbid=%s&api_key=%s" % ( urllib.quote_plus(mbid), self.__lastfmapikey__ )
        
        xmldoc = izecore.getXmlResponse(url)
        
        return xmldoc.getElementsByTagName("track")
    
    def Artist_search(self, artist):       
        url = "http://ws.audioscrobbler.com/2.0/?method=artist.search&api_key=%s&%s" % ( self.__lastfmapikey__,  urllib.urlencode( { "artist" : artist.encode("utf-8") }) )
        
        xmldoc = izecore.getXmlResponse(url)
            
        return xmldoc.getElementsByTagName('artist')
        
        
        