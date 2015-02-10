# -*- coding: utf-8 -*-
# 
# Massengeschmack XBMC add-on
# Copyright (C) 2013 by Janek Bevendorff
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

import xbmcgui
import urllib
import urllib2
import email.utils
import json
import time
import re
from datetime import datetime, tzinfo, timedelta
from xml.dom import minidom
from HTMLParser import HTMLParser

from globalvars import *
from resources.lib.listing import Listing, ListItem
from resources.lib.datasource import DataSource, FKTVDataSource

# enable non-GET HTTP requests using urllib2
class PostRequest(urllib2.Request):
    def get_method(self):
        return 'POST'

class HeadRequest(urllib2.Request):
    def get_method(self):
        return 'HEAD'

# helper functions
def openHTTPConnection(uri, requestMethod='GET'):
    """
    Open an HTTP(S) connection and return the connection handle.
    
    @type uri: str
    @param uri: the request URI
    @type requestMethod: str
    @param requestMethod: the HTTP request method (either GET, POST or HEAD)
    @return: urllib2 request handle
    """
    requestMethod = requestMethod.upper()
    request = None
    if 'POST' == requestMethod:
        request = PostRequest(uri)
    elif 'HEAD' == requestMethod:
        request = HeadRequest(uri)
    else:
        request = urllib2.Request(uri)
    
    request.add_header('User-Agent', HTTP_USER_AGENT)
    return urllib2.urlopen(request, None, HTTP_TIMEOUT)

def installHTTPLoginData(username, password):
    """
    Register the HTTP login data for accessing feeds later on.
    
    @type username: str
    @type password: str
    """
    passwordManager = urllib2.HTTPPasswordMgrWithDefaultRealm()
    passwordManager.add_password(None, HTTP_BASE_URI, username, password)
    authHandler = urllib2.HTTPBasicAuthHandler(passwordManager)
    opener      = urllib2.build_opener(authHandler)
    urllib2.install_opener(opener)

def fetchSubscriptions(showDialog=False):
    """
    Test if the given login credentials are correct and get a list of subscriptions
    (numeric IDs) in case the login data were correct.
    
    Login data need to be installed beforehand using installHTTPLoginData().
    Returns a dict of the following structure:
    
    {
        'code'          : HTTP response code,
        'reason'        : error description if code is not 200,
        'subscriptions' : [ list of numeric IDs of subscribed shows ]
    }
    
    If a network error occurs, code is -1 and reason contains an error description.
    If the login fails, 'subscription' will contain an empty list-
    
    @type showDialog: bool
    @param showDialog: whether to show a progress dialog while testing
    @return: dict of return HTTP status code, an error description if applicable and the
             subscriptions if login was successful
    """
    
    response = {
        'code'          : 200,
        'reason'        : '',
        'subscriptions' : []
    }
    
    if showDialog:
        dialog = xbmcgui.DialogProgress()
        dialog.create(ADDON.getLocalizedString(30104))
        dialog.update(50)
    
    try:
        handle = openHTTPConnection(HTTP_BASE_URI + 'api/?action=listSubscriptionsID')
    except urllib2.HTTPError, e:
        response['code']   = e.code
        response['reason'] = e.reason
    except urllib2.URLError, e:
        response['code']   = -1
        response['reason'] = e.reason
    else:
        response['subscriptions'] = json.loads(handle.read())
        handle.close()
    
    if showDialog:
        dialog.update(100)
        del dialog
    
    return response

# subscriptions cache
__subscriptions = None

def cacheSubscriptions(subscriptions):
    """
    Cache active subscriptions to the add-on settings.
    
    @type subscriptions: subscriptions: list
    @param: subscriptions: list of numeric IDs for all active subscriptions
    """
    __subscriptions = subscriptions
    ADDON.setSetting('account.subscriptions', json.dumps(subscriptions))

def getSubscriptions():
    """
    Return a list with numeric IDs for all active subscriptions.
    
    This method will only read from the cache. It won't fetch any new data
    from the server. Use fetchSubscriptions() for that and then write
    the fetched data to the cache using cacheSubscriptions().
    
    @return: list of subscriptions
    """
    global __subscriptions
    
    subscriptions = []
    if None == __subscriptions:
        tmp = ADDON.getSetting('account.subscriptions')
        if '' != tmp:
            subscriptions = json.loads(tmp)
    else:
        subscriptions == __subscriptions
    
    return subscriptions

# live streams cache
__liveShows = {}

def getLiveShows():
    """
    Return a list of dictionaries with information about current and upcoming live shows.
    This method does no exception handling, so make sure the login credentials are correct.
    
    @return: dictionary list of live streams
    """
    global __liveShows
    if {} == __liveShows:
        handle = openHTTPConnection(HTTP_BASE_URI + 'api/?action=listLiveShows')
        __liveShows = json.loads(handle.read())
        handle.close()
    
    return __liveShows

def getLiveStreamInfo(id):
    """
    Fetch information about a particular live stream.
    
    @type id: str
    @param id: the GUID of the live stream, False on error
    """
    try:
        handle = openHTTPConnection(HTTP_BASE_URI + 'api/?action=getPlaylistUrl&id=' + id)
    except urllib2.HTTPError, e:
        return False
    except urllib2.URLError, e:
        return False
    else:
        streamInfo = handle.read()
        handle.close()
    
    streamInfo = json.loads(streamInfo)
    
    return streamInfo
    

# feed cache
__fetchedFeeds = {}

def parseRSSFeed(feed, fetch=False):
    """
    Parse an RSS feed and create a list of dicts from the XML data.
    This function is necessary because we can't rely on any third-party
    RSS modules.
    
    if fetch is true, feed is assumed to be a URI to an RSS feed instead of
    its XML contents.
    
    The returned list has to following format:
    [
        {
            'title'       : summary1,
            'subtitle'    : subtitle1,
            'pubdate'     : pubdate1,
            'description' : description1,
            'link'        : link1,
            'guid'        : guid1,
            'url'         : url1,
            'duration'    : duration1
        },
        {
            'title'       : summary2,
            'subtitle'    : subtitle2,
            'pubdate'     : pubdate2,
            'description' : description2,
            'link'        : link2,
            'guid'        : guid2,
            'url'         : url2,
            'duration'    : duration2
        },
        ...
    ]
    
    @type feed: str
    @param feed: the RSS feed as XML string or a URI if fetch is true
    @type fetch: bool
    @param fetch: True if feed is a URI, default is false
    @return a list of dicts with the parsed feed data
    """
    if fetch:
        if not feed in __fetchedFeeds:
            response = None
            try:
                response = openHTTPConnection(feed)
            except urllib2.HTTPError, e:
                if 401 == e.code:
                    xbmcgui.Dialog().ok(ADDON.getLocalizedString(30102), ADDON.getLocalizedString(30105))
                else:
                    xbmcgui.Dialog().ok(ADDON.getLocalizedString(30902), ADDON.getLocalizedString(30904) + '[CR]Error: {0} {1}'.format(e.code, e.reason))
            except urllib2.URLError, e:
                xbmcgui.Dialog().ok(ADDON.getLocalizedString(30902), ADDON.getLocalizedString(30903) + '[CR]Error: {0}'.format(e.reason))
                return domDict
            __fetchedFeeds[feed] = response.read()
        feed = __fetchedFeeds[feed]
    
    dom = minidom.parseString(feed)
    
    data   = []
    parser = HTMLParser()
    for node in dom.getElementsByTagName('item'):
        # convert duration string to seconds
        duration = node.getElementsByTagName('itunes:duration')[0].firstChild.nodeValue
        h, m, s  = map(int, duration.split(':'))
        duration = timedelta(hours=h, minutes=m, seconds=s).seconds
        
        description = parser.unescape(node.getElementsByTagName('description')[0].firstChild.nodeValue).encode('utf-8')
        
        # get thumbnail URL
        thumbUrl = ''
        thumbUrlMatch = re.search('^<img src="([^"]+)" /><br>', description)
        if None != thumbUrlMatch:
            thumbUrl = thumbUrlMatch.group(1)
            if None == re.match('^https?://', thumbUrl):
                thumbUrl = HTTP_BASE_URI + re.sub('^/', '', thumbUrl)

        # strip HTML tags
        description = re.sub('<[^>]*>', '', description).strip()

        # combine whitespace
        description = re.sub(' {2,}', ' ', description)
        
        data.append({
            'title'       : parser.unescape(node.getElementsByTagName('title')[0].firstChild.nodeValue).encode('utf-8'),
            'subtitle'    : parser.unescape(node.getElementsByTagName('itunes:subtitle')[0].firstChild.nodeValue).encode('utf-8'),
            'pubdate'     : parser.unescape(node.getElementsByTagName('pubDate')[0].firstChild.nodeValue).encode('utf-8'),
            'description' : description,
            'link'        : parser.unescape(node.getElementsByTagName('link')[0].firstChild.nodeValue).encode('utf-8'),
            'thumbUrl'    : thumbUrl,
            'guid'        : parser.unescape(node.getElementsByTagName('guid')[0].firstChild.nodeValue).encode('utf-8'),
            'url'         : parser.unescape(node.getElementsByTagName('enclosure')[0].getAttribute('url')).encode('utf-8'),
            'duration'    : duration
        })
    
    return data

class TZOffset(tzinfo):
    """Represent fixed timezone offset east from UTC."""
    
    def __init__(self, offset):
        self.__offset = timedelta(minutes=offset)
    
    def utcoffset(self, dt):
        return self.__offset
    
    def dst(self, dt):
        return timedelta(0)

def parseUTCDateString(datestr):
    """
    Parse an RFC 2822 date format to a datetime object.
    
    @type datestr: str
    @param datestr: the date string
    @return a datetime object
    """
    # work around Python bug
    date   = None
    format = '%a, %d %b %Y %H:%M:%S'
    try:
        date = datetime.strptime(datestr[:-6], format)
    except TypeError:
        date = datetime(*(time.strptime(datestr[:-6], format)[0:6]))
    
    # add timezone info which isn't possible using %z in Python 2
    offset  = int(datestr[-5:-2]) * 60
    offset += int(datestr[-5:-4] + '1') * int(datestr[-2:])
    offset  = TZOffset(offset)
    date    = date.replace(tzinfo=offset)
    
    return date

def dictUrlEncode(data):
    """
    Create a URL encoded JSON string from a given dict or list.
    
    @type data: dict
    @param data: the data structure
    @return URL encoded string
    """
    return urllib.quote(json.dumps(data, separators=(',', ':')))

def getPluginBaseURL():
    """
    Return the base plugin:// URL for this plugin (may be different on different platforms)
    
    @return the URL string
    """
    
    url = 'plugin://'
    
    if IS_XBOX:
        url += 'video/' + ADDON_NAME
    else:
        url += ADDON_ID
    
    return url

def assembleListURL(module=None, submodule=None, mode=None):
    """
    Assemble a plugin:// url with a list command.
    
    @type module: str
    @param module: the name of the module to list
    @type submodule: str
    @param submodule: the name of the sub module to list (requires module to be set)
    @type mode: str
    @param mode: a mode for a submodule (requires submodule to be set)
    @return the URL
    """
    
    url = getPluginBaseURL() + '/?cmd=list'
    
    if None == module:
        return url
    
    url += '&module=' + urllib.quote(module)
    if None != submodule:
        url += '&submodule=' + urllib.quote(submodule)
    if None != submodule and None != mode:
        url += '&mode=' + urllib.quote(mode)
    
    return url
    

def assemblePlayURL(url, name='', iconImage='', metaData={}, streamInfo={}):
    """
    Assemble a plugin:// URL with a play command for a given URL.
    
    @type url: str
    @param url: the real URL of the media file
    @type name: str
    @param name: a nice human-readable name
    @type iconImage: str
    @param iconImage: a URL to a thumbnail image
    @type metaData: dict
    @param metaData: metaData for the media file
    @type streamInfo: dict
    @param: streamInfo: technical info about the stream (such as the duration or resolution)
    """
    if '#' == url or '' == url:
        return '#'
    
    return getPluginBaseURL() + '/?cmd=play&url=' + urllib.quote(url) + \
          '&name=' + urllib.quote(name) + '&iconimage=' + urllib.quote(iconImage) + \
          '&metadata=' + dictUrlEncode(metaData) + \
          '&streaminfo=' + dictUrlEncode(streamInfo)
