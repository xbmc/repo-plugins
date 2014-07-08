# -*- coding: utf-8 -*-

import urllib2
import json
import re
import os

class SevenTv:
    def __init__(self, favsFile=None):
        # opener for loading json content
        self._opener = urllib2.build_opener()
        self._opener.addheaders = [('User-Agent', 'stagefright/1.2 (Linux;Android 4.4.2)')]
        self._favsFile = favsFile
        
    def getFavoriteShows(self, ids=[]):
        result = {}
        
        idString=''
        for id in ids:
            idString+=id+','
            
        if len(idString)>0:
            idString = idString[:-1] # remove ','
            idString = '['+idString+']'            
            content = self._opener.open("http://contentapi.sim-technik.de/mega-app/v1/tablet/format?ids="+idString)
            data = json.load(content)
            result = self.getSortedScreenObjects(data, False)
        
        return result
    
    def getNewVideos(self, ids=[]):
        result = {}
        
        idString=''
        for id in ids:
            idString+=id+','
            
        if len(idString)>0:
            idString = idString[:-1] # remove ','
            idString = '['+idString+']'            
            content = self._opener.open("http://contentapi.sim-technik.de/mega-app/v1/tablet/videos/favourites?ids="+idString)
            data = json.load(content)
            result = self.getSortedScreenObjects(data, True)
        
        return result

    def getChannels(self):
    
        # sort function for the channels
        def _sort_key(d):
            return d.get('channel_display_name', '')
        
        result = []
        
        content = self._opener.open("http://common-app-st.sim-technik.de/applications/mega-app/mega.json")
        data = json.load(content)
        menubar = data.get('menubar', {})
        channels = menubar.get('channels', {})
        
        result = sorted(channels, key=_sort_key, reverse=False)
        
        return result;
    
    def getChannelHighlights(self, channel):
        result = []
        content = self._opener.open("http://contentapi.sim-technik.de/mega-app/v1/"+channel+"/tablet/homepage")
        data = json.load(content)
        screen = data.get('screen', {})
        result = screen.get('screen_objects', {})
        
        return result
    
    def getChannelLibrary(self, channel):
        result = []
        content = self._opener.open("http://contentapi.sim-technik.de/mega-app/v1/"+channel+"/tablet/format")
        data = json.load(content)
        screen = data.get('screen', {})
        screen_objects = screen.get('screen_objects', {})
        if len(screen_objects)>0:
            result = screen_objects[0].get('screen_objects', {})
        
        return result
    
    def getShowsFromScreenObject(self, screen_object):
        result= []
        
        # sort function for the channels
        def _sort_key(d):
            return d.get('title', '').lower()
        
        screen_objects = screen_object.get('screen_objects', {})
        result = sorted(screen_objects, key=_sort_key, reverse=False)
        
        return result
    
    def getShowContent(self, channel, show):
        result = []
        
        content = self._opener.open("http://contentapi.sim-technik.de/mega-app/v1/"+channel+"/tablet/format/show/"+show)
        data = json.load(content)
        screen = data.get('screen', {})
        result = screen.get('screen_objects', {})
        
        return result
    
    def getSortedScreenObjects(self, screen_object, forcedReverseSort=None):
        
        def _sort_key(d):
            if d.has_key('publishing_date'):
                match = re.compile('(\d*)\.(\d*)\.(\d*)', re.DOTALL).findall(d['publishing_date'])
                if match!=None and len(match[0])>=3:
                    return match[0][2]+"-"+match[0][1]+"-"+match[0][0]
            
            if d.has_key('title'):
                return d['title']
            
            if d.has_key('video_title'):
                return d['video_title']
            
            return ""
        
        link = screen_object.get('link', '')
        reverse=True
        if link.find('/format')>0:
            reverse=False
            
        if forcedReverseSort!=None:
            reverse = forcedReverseSort
        screen_objects = screen_object.get('screen_objects', {})
        
        result = sorted(screen_objects, key=_sort_key, reverse=reverse)
        return result
        
    
    def getFanartFromShowContent(self, screen_objects):
        for screen_object in screen_objects:
            if screen_object.get('type', '')=='format_teaser_header_item':
                return screen_object.get('image_url', None)
            
        return None
    
    def getVideoUrl(self, episode):
        content = self._opener.open("http://vas.sim-technik.de/video/video.json?clipid="+episode+"&app=megapp&method=6")
        data = json.load(content)
        if data.has_key('VideoURL'):
            VideoURL = data['VideoURL']
            return VideoURL
        return None
    
    def search(self, text):
        content = self._opener.open("http://contentapi.sim-technik.de/mega-app/v1/tablet/search?query="+text.encode('utf-8'))
        data = json.load(content)
        screen = data.get('screen', {})
        screen_objects = screen.get('screen_objects', {})
        return screen_objects 