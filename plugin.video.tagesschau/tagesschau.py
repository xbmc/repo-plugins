# -*- coding: utf-8 -*-
# Copyright 2011 Jörn Schumacher, Henning Saul 
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

import sys, urllib, urlparse

import xbmc, xbmcplugin, xbmcgui, xbmcaddon

from tagesschau_json_api import VideoContentProvider, JsonSource, LazyVideoContent

# -- Constants ----------------------------------------------
ADDON_ID = 'plugin.video.tagesschau'
FANART = xbmc.translatePath('special://home/addons/' + ADDON_ID + '/fanart.jpg')
ACTION_PARAM = 'action'
FEED_PARAM = 'feed'
ID_PARAM = 'tsid'
URL_PARAM = 'url'

DEFAULT_IMAGE_URL = 'http://miss.tagesschau.de/image/sendung/ard_portal_vorspann_ts.jpg'

# -- Settings -----------------------------------------------
settings = xbmcaddon.Addon(id=ADDON_ID)
quality_id = settings.getSetting("quality")
quality = ['M', 'L'][int(quality_id)]

# -- I18n ---------------------------------------------------
language = xbmcaddon.Addon(id='plugin.video.tagesschau').getLocalizedString
strings = { 'latest_videos': language(30100),
            'latest_broadcasts': language(30101),
            'dossiers': language(30102),
            'archived_broadcasts': language(30103)
}

# ------------------------------------------------------------


def addVideoContentDirectory(title, method):
    url_data = { ACTION_PARAM: 'list_feed',
                 FEED_PARAM: method  }
    url = 'plugin://' + ADDON_ID + '/?' + urllib.urlencode(url_data)
    li = xbmcgui.ListItem(title, thumbnailImage=DEFAULT_IMAGE_URL)
    li.setProperty('Fanart_Image', FANART)
    xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=url, listitem=li, isFolder=True)    
    
def getListItem(videocontent):    
    title = videocontent.title
    image_url = videocontent.image_url()
    if(not image_url):
        image_url = DEFAULT_IMAGE_URL
    li = xbmcgui.ListItem(title, thumbnailImage=image_url)
    li.setProperty('Fanart_Image', FANART)
    li.setProperty('IsPlayable', 'true')
    li.setInfo(type="Video", infoLabels={ "Title": title,
                                          "Plot": videocontent.description,
                                          "Duration": str((videocontent.duration or 0) / 60) })    
    return li

def getUrl(videocontent, method):
    url_data = { ACTION_PARAM: 'play_video' }
    # for LazyVideoContent let's defer its expensive video_url call
    if isinstance(videocontent, LazyVideoContent):
        url_data[FEED_PARAM] = method
        url_data[ID_PARAM] = urllib.quote(videocontent.tsid)
    else:
        url_data[URL_PARAM] = urllib.quote(videocontent.video_url(quality))
    return 'plugin://' + ADDON_ID + '?' + urllib.urlencode(url_data)
    
def addVideoContentItem(videocontent, method):
    li = getListItem(videocontent)
    url = getUrl(videocontent, method)  
    return xbmcplugin.addDirectoryItem(int(sys.argv[1]), url, li, False)

def addVideoContentItems(videocontents, method):
    items = []
    for videocontent in videocontents:
        li = getListItem(videocontent)
        url = getUrl(videocontent, method)
        items.append((url, li, False))   
    return xbmcplugin.addDirectoryItems(int(sys.argv[1]), items, len(items))

def get_params():
    paramstring = sys.argv[2]
    params = urlparse.parse_qs(urlparse.urlparse(paramstring).query)
    
    for key in params:
        params[key] = params[key][0]
    return params
    
# TODO: can't figure out how to set fanart for root/back folder of plugin
# http://trac.xbmc.org/ticket/8228? 
xbmcplugin.setPluginFanart(int(sys.argv[1]), 'special://home/addons/' + ADDON_ID + '/fanart.jpg')

params = get_params()
provider = VideoContentProvider(JsonSource())

if params.get(ACTION_PARAM) == 'play_video':
    # expecting either url or feed and id param
    url = params.get(URL_PARAM)
    if url:
        url = urllib.unquote(url) 
    else: 
        videos_method = getattr(provider, params[FEED_PARAM])
        videos = videos_method()    
        tsid = urllib.unquote(params[ID_PARAM])
        # find video with matching tsid
        for video in videos:
            if video.tsid == tsid:
                url = video.video_url(quality)    
    listitem = xbmcgui.ListItem(path=url)
    xbmcplugin.setResolvedUrl(handle=int(sys.argv[1]), succeeded=(url != None), listitem=listitem)

elif params.get(ACTION_PARAM) == 'list_feed':
    # list video for a directory
    videos_method = getattr(provider, params[FEED_PARAM])
    videos = videos_method()
    addVideoContentItems(videos, params[FEED_PARAM])

else:
    # populate root directory
    # check whether there is a livestream
    videos = provider.livestreams()
    if(len(videos) == 1):
        addVideoContentItem(videos[0], "livestreams")

    # add directories for other feeds        
    add_named_directory = lambda x: addVideoContentDirectory(strings[x], x)
    add_named_directory('latest_videos')
    add_named_directory('latest_broadcasts')
    add_named_directory('dossiers')
    add_named_directory('archived_broadcasts')   
        
xbmcplugin.endOfDirectory(int(sys.argv[1]))


