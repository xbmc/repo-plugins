# -*- coding: utf-8 -*-
# Copyright 2011 Jörn Schumacher, Henning Saul
# Copyright 2021 Christian Prasch
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

import sys, os, urllib, urllib.parse, logging
import xbmc, xbmcplugin, xbmcgui, xbmcaddon, xbmcvfs
#import web_pdb

from libs.tagesschau_json_api import VideoContentProvider, JsonSource, addon
from libs.subtitles import download_subtitles

# -- Constants ----------------------------------------------
ADDON_ID = 'plugin.video.tagesschau'
FANART = xbmcvfs.translatePath('special://home/addons/' + ADDON_ID + '/resources/assets/fanart.jpg')
ACTION_PARAM = 'action'
FEED_PARAM = 'feed'
ID_PARAM = 'tsid'
URL_PARAM = 'url'

DEFAULT_IMAGE_URL = 'https://www.tagesschau.de/image/sendung/ard_portal_vorspann_ts.jpg'

# -- Settings -----------------------------------------------
logger = logging.getLogger("plugin.video.tagesschau.api")

# -- Settings -----------------------------------------------
quality_id = addon.getSetting('quality')
quality = ['M', 'L', 'X'][int(quality_id)]

# -- I18n ---------------------------------------------------
language = addon.getLocalizedString
strings = { 'latest_videos':       language(30100),
            'latest_broadcasts':   language(30101),
            'livestreams':         language(30102),
            'tagesschau_20':       language(30104),
            'tagesthemen':         language(30105)
}

#-- Subtitles ------------------------------------------------

profile_dir = xbmcvfs.translatePath(addon.getAddonInfo('profile'))
subtitles_dir  = os.path.join(profile_dir, 'Subtitles')

# ------------------------------------------------------------


def addVideoContentDirectory(title, method):
    url_data = { ACTION_PARAM: 'list_feed', FEED_PARAM: method  }
    url = 'plugin://' + ADDON_ID + '/?' + urllib.parse.urlencode(url_data)
    li = xbmcgui.ListItem(str(title))
    li.setArt({'thumb':DEFAULT_IMAGE_URL})
    li.setProperty('Fanart_Image', FANART)
    xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=url, listitem=li, isFolder=True)

def getListItem(videocontent):
    title = str(videocontent.title)
    image_url = videocontent.image_url()
    if(not image_url):
        image_url = DEFAULT_IMAGE_URL
    li = xbmcgui.ListItem(title)
    li.setArt({'thumb':image_url})
    li.setProperty('Fanart_Image', FANART)
    li.setProperty('IsPlayable', 'true')
    li.setInfo(type="Video",
               infoLabels={ "Title": str(title),
                            "Plot": str(videocontent.description),
                            "Duration": str((videocontent.duration or 0)/60)
                          }
              )
    if( videocontent.timestamp ):
        li.setInfo(type="Video",
                   infoLabels={ "premiered": str(videocontent.timestamp.strftime('%d.%m.%Y')),
                                "aired": str(videocontent.timestamp.strftime('%d.%m.%Y')),
                                "date": str(videocontent.timestamp.strftime('%d.%m.%Y'))
                              }
                  )

    return li

def getUrl(videocontent, method):
    url_data = { ACTION_PARAM: 'play_video' }
    url_data[URL_PARAM] = urllib.parse.quote(videocontent.video_url(quality))
    return 'plugin://' + ADDON_ID + '?' + urllib.parse.urlencode(url_data)

def addVideoContentItem(videocontent, method):
    li = getListItem(videocontent)
    url = getUrl(videocontent, method)
    return xbmcplugin.addDirectoryItem(int(sys.argv[1]), url, li, False)

def addVideoContentItems(videocontents, method):
    items = []
    videocontents = sorted(videocontents)
    for videocontent in videocontents:
        li = getListItem(videocontent)
        url = getUrl(videocontent, method)
        items.append((url, li, False))
    return xbmcplugin.addDirectoryItems(int(sys.argv[1]), items, len(items))

def get_params():
    paramstring = sys.argv[2]
    params = urllib.parse.parse_qs(urllib.parse.urlparse(paramstring).query)

    for key in params:
        params[key] = params[key][0]
    return params


def tagesschau():
    # TODO: can't figure out how to set fanart for root/back folder of plugin
    # http://trac.xbmc.org/ticket/8228?
    xbmcplugin.setPluginFanart(int(sys.argv[1]), 'special://home/addons/' + ADDON_ID + '/resources/assets/fanart.jpg')
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_NONE)

    params = get_params()
    provider = VideoContentProvider(JsonSource())

    if params.get(ACTION_PARAM) == 'play_video':
        subtitles_file = None
        # expecting either url or feed and id param
        url = params.get(URL_PARAM)
        if url:
            url = urllib.parse.unquote(url)
        else:
            videos_method = getattr(provider, params[FEED_PARAM])
            videos = videos_method()
            tsid = urllib.parse.unquote(params[ID_PARAM])
            # find video with matching tsid
            for video in videos:
                if video.tsid == tsid:
                    url = video.video_url(quality)
                    # try to download and and convert subtitles to local SRT file
                    subtitles_url = 'https://www.tagesschau.de/multimedia/video/' + str(video.video_id()) + '~subtitle.html'
                    subtitles_file = download_subtitles(subtitles_url, subtitles_dir)

        listitem = xbmcgui.ListItem(path=url)
        if(subtitles_file != None):
            # the following only works in Gotham, see
            # http://forum.xbmc.org/showthread.php?tid=154805&page=7&highlight=subtitle
            listitem.setProperty('upnp:subtitle:1', subtitles_file)
            listitem.setSubtitles((subtitles_file,))

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
        add_named_directory('tagesschau_20')
        add_named_directory('tagesthemen')

    xbmcplugin.endOfDirectory(int(sys.argv[1]))
