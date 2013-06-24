#-*- encoding: utf-8 -*-
import urllib2
from urllib import quote_plus
import re
try:
    import json
except:
    import simplejson as json

USER_AGENT = 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:6.0) Gecko/20100101 Firefox/6.0'

class JSONScraper(object):
    '''
    Encapsulates execution request and parsing of response
    '''
    def _downloadWebData(self, url, headers = None):
        req = urllib2.Request(url)
        req.add_header(Keys.USER_AGENT, USER_AGENT)
        response = urllib2.urlopen(req)
        data = response.read()
        response.close()
        return data

    def getJson(self, url, headers = None):
        try:
            jsonString = self._downloadWebData(url, headers)
        except:
            raise GagException(GagException.HTTP_ERROR)
        try:
            return json.loads(jsonString)
        except:
            raise GagException(GagException.JSON_ERROR)

class GagTV(object):
    def __init__(self):
        self.scraper = JSONScraper()

    def getTodaysVideos(self):
        url = Urls.CURRENT_PLAYLIST
        return self.scraper.getJson(url)

    def getArchivedVideos(self, pid):
        url = Urls.ARCHIVED_PLAYLIST.format(pid)
        return self.scraper.getJson(url)

    def getArchives(self):
        url = Urls.ARCHIVED
        return self.scraper.getJson(url)

    def _fetchItems(self, url, key):
        items = self.scraper.getJson(url)
        return items[key] if items else []


class Urls(object):
    '''
    Should not be instantiated, just used to categorize 
    string-constants
    '''
    API_BASE = 'http://d1nmj8esheg8s6.cloudfront.net/api/'
    CURRENT_PLAYLIST = API_BASE + 'playlist'
    ARCHIVED = API_BASE + 'playlist/archive'
    ARCHIVED_PLAYLIST = API_BASE + 'playlist/archive/{0}'

class Keys(object):
    '''
    Should not be instantiated, just used to categorize 
    string-constants
    '''

    PLAYLIST_ID = 'pid'
    THUMBNAIL = 'thumbnail_url'
    TITLE = 'title'
    USER_AGENT = 'User-Agent'
    YOUTUBE_VIDEO_ID = 'youtubeVideoId'

class GagException(Exception):

    HTTP_ERROR = 1
    JSON_ERROR = 2

    def __init__(self, code):
        Exception.__init__(self)
        self.code = code

    def __str__(self):
        return repr(self.code)
