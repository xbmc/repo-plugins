# -*- coding: utf-8 -*-

"""
Version 1.0.1 (2014.07.06)
- initial release
"""

import urllib
import urllib2
import json
import time
import hashlib
import uuid
import re
import random

__CONFIG_DMAX_DE__ = {'url': 'http://m.app.dmax.de',
                      'token': 'XoVA15ecuocTY5wBbxNImXVFbQd72epyxxVcH3ZVmOA.'
                      }

__CONFIG_TLC_DE__ = {'url': 'http://m.app.tlc.de',
                     'token': 'XoVA15ecuocTY5wBbxNImXVFbQd72epyxxVcH3ZVmOA.'
                     }

class Client:
    def __init__(self, config):
        self.Config = config
        
    def _getContentAsJson(self, url):
        result = {}
        
        try:
            opener = urllib2.build_opener()
            opener.addheaders = [('User-Agent', 'stagefright/1.2 (Linux;Android 4.4.2)')]
            
            content = opener.open(url)
            result = json.load(content)
        except:
            # do nothing
            pass
        
        return result
        
    def _doBrightcove(self, command, params={}):
        result = {}
        
        try:
            opener = urllib2.build_opener()
            opener.addheaders = [('User-Agent', 'stagefright/1.2 (Linux;Android 4.4.2)')]
            
            url = 'https://api.brightcove.com/services/library'
            
            _params = {}
            _params.update(params)
            _params['command'] = command
            _params['token']= self.Config.get('token', '')
            url = url + '?' + urllib.urlencode(_params)
            
            content = opener.open(url)
            result = json.load(content)
        except:
            # do nothing
            pass
        
        return result
    
    def _createUrl(self, url_path):
        url = self.Config.get('url', '')
        if not url.endswith('/') and not url_path.startswith('/'):
            url = url+'/'
        url = url+url_path
        
        return url
    
    def getVideoStreams(self, episode_id):
        params = {'video_id': episode_id,
                  'video_fields': 'name,renditions'}
        return self._doBrightcove('find_video_by_id', params=params)
    
    def getEpisodes(self, series_id):
        url = self._createUrl('/free-to-air/android/genesis/series//'+series_id+'/episodes/')
        return self._getContentAsJson(url)
    
    def getLibrary(self):
        url = self._createUrl('/free-to-air/android/genesis/series/')
        return self._getContentAsJson(url)
    
    def getHighlights(self):
        url = self._createUrl('/free-to-air/android/genesis/targets/featured/')
        return self._getContentAsJson(url)