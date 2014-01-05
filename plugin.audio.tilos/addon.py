"""
    Plugin to browse the archive and listen to 
    live stream of Radio Tilos
"""

import sys, os, os.path, xbmcaddon
import xbmc, xbmcgui, xbmcplugin
from urllib2 import Request, urlopen, URLError
import urlparse
import urllib
from HTMLParser import HTMLParser
from shutil import rmtree, copy
import traceback
from pprint import pprint
import json
import time
import calendar
import datetime

############################################
# Define required statics
############################################

__plugin__ = "Tilos"
__version__ = '0.0.2'
__author__ = 'Gabor Boros'
__date__ = '2013-12-28'
__addon__ = xbmcaddon.Addon()
__addonname__ = __addon__.getAddonInfo('name')

BASE_URL = 'http://tilos.hu'
BASE_URL_SHOWS = BASE_URL + '/api/v0/show'
BASE_URL_EPISODES = BASE_URL_SHOWS + '/%s/episodes?from=%d&to=%d'
HEADERS = {'User-Agent' : 'Mozilla 5.10'} 
LIVE_URL_256 = 'http://stream.tilos.hu/tilos.m3u'
LIVE_URL_128 = 'http://stream.tilos.hu/tilos_128.mp3.m3u'

dialogProgress = xbmcgui.DialogProgress()
dialog = xbmcgui.Dialog()

base_url = sys.argv[0]
addon_handle = int(sys.argv[1])
args = urlparse.parse_qs(sys.argv[2][1:])

xbmcplugin.setContent(addon_handle, 'songs')
Addon = xbmcaddon.Addon("plugin.audio.tilos")

mode = args.get('mode', None)

############################################
# Functions
############################################

def log(msg):
    if type(msg) not in (str, unicode):
        xbmc.log("[%s]: %s" % (__plugin__, type(msg)))
        pprint (msg)
    else:
        if type(msg) in (unicode,):
            msg = msg.encode('utf-8')
        xbmc.log("[%s]: %s" % (__plugin__, msg))


def build_url(query):
    return base_url + '?' + urllib.urlencode(query)
    
def getURL(url):
    # log(' > getURL(%s)' % (url))
    req = Request(url, None, HEADERS)
     
    try:
        response = urlopen(req)
     
    except URLError, e:
     
        if hasattr(e, 'reason'):
            log(getString(30003))
            log(getString(30004) + str(e.reason))
            xbmcgui.Dialog().ok(__addonname__, getString(30003), '', getString(30004) + str(e.reason))
     
        elif hasattr(e, 'code'):
            log(getString(30005))
            log(getString(30006) + str(e.code))
            xbmcgui.Dialog().ok(__addonname__, getString(30005), '', getString(30006) + str(e.code))
    
    except Exception, e:
        
        if hasattr(e, 'reason'):
            log(e.reason)
        
    else:
        return response.read()
        
    
def getString(stringID):
    return Addon.getLocalizedString(stringID)
    
def getUString(string):
    return string.encode('utf8')

def showRootMenu():
    # log(' > showRootMenu()')

    url = build_url({'mode': 'talkShows', 'foldername': getString(30001)})
    li = xbmcgui.ListItem(getString(30001), iconImage = '')
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)
    
    url = build_url({'mode': 'musicShows', 'foldername': getString(30002)})
    li = xbmcgui.ListItem(getString(30002), iconImage = '')
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)
    
    url = build_url({'mode': 'play_%s' % (LIVE_URL_256), 'foldername': getString(30007)})
    li = xbmcgui.ListItem(getString(30007), iconImage = '')
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)
    
    url = build_url({'mode': 'play_%s' % (LIVE_URL_128), 'foldername': getString(30008)})
    li = xbmcgui.ListItem(getString(30008), iconImage = '')
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)
    
    
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_LABEL )    
    xbmcplugin.endOfDirectory(addon_handle)

def showShows(type):
    # log(' > showShows(%s)' % type)
  
    page_data = getURL(BASE_URL_SHOWS)  
    jdata = json.loads(page_data)
 
    for show in jdata:
        if (show['type'] == type):
            url = build_url({'mode': '%s_%s' % ('show', getUString(show['alias'])), 'foldername': getUString(show['name'])})
            li = xbmcgui.ListItem(getUString(show['name']))
            #li.setIconImage('')
            #li.setThumbnailImage(getUString(show['banner']))
            xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)
            
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_LABEL )    
    xbmcplugin.endOfDirectory(addon_handle)

def showShow(alias):
    # log(' > showShow(%s)' % alias)
    
    # Get Show information
    page_data = getURL(BASE_URL_SHOWS + '/' + alias)
    jdata_show = json.loads(page_data)
    
    artist = ''
    for contributor in jdata_show['contributors']:
        artist += ' %s (%s)' % (getUString(contributor['author']['name'])\
            , getUString(contributor['author']['alias']))
    
    # Get all available episodes since 2009.01.01
    startDate = calendar.timegm(datetime.datetime(2009,01,01,0,0).utctimetuple())
    endDate = calendar.timegm(datetime.datetime.now().utctimetuple())
    #log(' Show Episode URL: ' + BASE_URL_EPISODES % (jdata_show['id'], startDate, endDate))
    page_data = getURL(BASE_URL_EPISODES % (jdata_show['id'], startDate, endDate))
    jdata_episode = json.loads(page_data)
    
    for episode in jdata_episode:
        episode_date = time.strftime('%Y-%m-%d %H:%M', time.localtime(episode['plannedFrom']))
        episode_year = time.strftime('%Y', time.localtime(episode['plannedFrom']))
        
        url = build_url({'mode': 'play_%s' % (episode['m3uUrl']), 'foldername': episode_date})
        li = xbmcgui.ListItem(episode_date)
        li.setInfo('music', {'artist' : artist, 'year' : episode_year })
        xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li)
    
    #xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_LABEL )    
    xbmcplugin.endOfDirectory(addon_handle)

def playShow(file):
    # log(' > playShow(%s)' % file)

    # log(' Play file: ' + file)

    xbmc.Player().play(file)
#    if (xbmc.Player().isPlaying()):
#         log(' Playing..')

############################################
# Start plugin
############################################
# log(' > mode: ' + mode[0] if mode is not None else '')

if mode is None:
    showRootMenu()
elif mode[0] == 'talkShows':
    showShows(1)
elif mode[0] == 'musicShows':
    showShows(0)
elif mode[0].startswith('show_'):
    showShow(mode[0].split('_')[1])
elif mode[0].startswith('play_'):
    playShow(''.join(mode[0].split('_')[1:]))