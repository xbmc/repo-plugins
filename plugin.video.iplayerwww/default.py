# -*- coding: utf-8 -*-

from __future__ import division

import os
import sys
import urllib

import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin


plugin_handle = int(sys.argv[1])
ADDON = xbmcaddon.Addon(id='plugin.video.iplayerwww')

try:
    from resources.lib import ipwww_common as Common
    from resources.lib import ipwww_video as Video
    from resources.lib import ipwww_radio as Radio
except ImportError as error:
    d = xbmcgui.Dialog()
    d.ok(str(error), xbmcaddon.Addon(Common.addonid).getLocalizedString(30413))
    raise


def get_params():
    param = []
    paramstring = sys.argv[2]
    if len(paramstring) >= 2:
        params = sys.argv[2]
        cleanedparams = params.replace('?', '')
        if (params[len(params) - 1] == '/'):
            params = params[0:len(params) - 2]
        pairsofparams = cleanedparams.split('&')
        param = {}
        for i in range(len(pairsofparams)):
            splitparams = {}
            splitparams = pairsofparams[i].split('=')
            if (len(splitparams)) == 2:
                param[splitparams[0]] = splitparams[1]
    return param


params = get_params()
content_type = None
url = None
name = None
mode = None
iconimage = None
description = None
subtitles_url = None
keyword = None


try:
    content_type = Common.utf8_unquote_plus(params["content_type"])
except:
    pass
try:
    url = Common.utf8_unquote_plus(params["url"])
except:
    pass
try:
    name = Common.utf8_unquote_plus(params["name"])
except:
    pass
try:
    iconimage = Common.utf8_unquote_plus(params["iconimage"])
except:
    pass
try:
    mode = int(params["mode"])
except:
    pass
try:
    description = Common.utf8_unquote_plus(params["description"])
except:
    pass
try:
    subtitles_url = Common.utf8_unquote_plus(params["subtitles_url"])
except:
    pass
try:
    keyword = Common.utf8_unquote_plus(params["keyword"])
except:
    pass

episode_id = Common.utf8_unquote_plus(params.get('episode_id', ''))
stream_id = Common.utf8_unquote_plus(params.get('stream_id', ''))
resume_time = params.get('resume_time', '')
total_time = params.get('total_time', '')
watch_from_start = params.get('watch_from_start') == 'True'
replay_chan_id = params.get('replay_chan_id', '')


try:
    # These are the modes which tell the plugin where to go.
    if mode == 1:
        Common.KidsMode()

    elif mode is None or url is None or len(url) < 1:
        Common.CreateBaseDirectory(content_type)

    # Modes 101-119 will create a main directory menu entry
    elif mode == 101:
        Video.ListLive()

    elif mode == 102:
        Video.ListAtoZ()

    elif mode == 103:
        Video.ListCategories()

    elif mode == 104:
        Video.Search(keyword)

    elif mode == 105:
        Video.ListMostPopular()

    elif mode == 106:
        Video.ListHighlights(url)

    elif mode == 107:
        Video.ListWatching()

    elif mode == 108:
        Video.ListFavourites()

    elif mode == 109:
        Video.ListChannelHighlights()

    elif mode == 112:
        Radio.ListAtoZ()

    elif mode == 113:
        Radio.ListLive()

    elif mode == 114:
        Radio.ListGenres()

    elif mode == 115:
        Radio.Search(keyword)

    elif mode == 116:
        Radio.ListMostPopular()

    elif mode == 117:
        Radio.ListListenList()

    elif mode == 199:
        Radio.ListFollowing()

    elif mode == 118:
        Video.RedButtonDialog()

    elif mode == 119:
        Common.SignOutBBCiD()

    elif mode == 120:
        Video.ListChannelAtoZ()

        # Modes 121-199 will create a sub directory menu entry
    elif mode == 121:
        Video.GetEpisodes(url)

    elif mode == 122:
        Video.GetAvailableStreams(name, url, iconimage, description, resume_time, total_time)

    elif mode == 123:
        Video.AddAvailableLiveStreamsDirectory(name, url, iconimage, watch_from_start)

    elif mode == 124:
        Video.GetAtoZPage(url)

    elif mode == 125:
        Video.ListCategoryFilters(url)

    elif mode == 126:
        Video.GetFilteredCategory(url)

    elif mode == 127:
        Video.GetGroup(url)

    elif mode == 128:
        Video.ScrapeEpisodes(url)

    elif mode == 129:
        Video.AddAvailableRedButtonDirectory(name, url)

    elif mode == 131:
        Radio.GetEpisodes(url)

    elif mode == 132:
        Radio.GetAvailableStreams(name, url, iconimage, description)

    elif mode == 133:
        Radio.AddAvailableLiveStreamsDirectory(name, url, iconimage)

    elif mode == 134:
        Video.ScrapeAtoZEpisodes(url)

    elif mode == 136:
        Radio.GetPage(url)

    elif mode == 137:
        Radio.GetCategoryPage(url)

    elif mode == 138:
        Radio.GetAtoZPage(url)

    elif mode == 139:
        Video.ScrapeEpisodes(url)

    # Modes 201-299 will create a playable menu entry, not a directory
    elif mode == 201:
        Video.PlayStream(name, url, iconimage, description, subtitles_url, episode_id, stream_id, replay_chan_id)

    elif mode == 202:
        Video.AddAvailableStreamItem(name, url, iconimage, description)

    elif mode == 203:
        Video.AddAvailableLiveStreamItemSelector(name, url, iconimage, watch_from_start)

    elif mode == 204:
        Video.AddAvailableRedButtonItem(name, url)

    elif mode == 205:
        Video.AddAvailableUHDTrialItem(name, url)

    elif mode == 211:
        Radio.PlayStream(name, url, iconimage, description, subtitles_url)

    elif mode == 212:
        Radio.AddAvailableStreamItem(name, url, iconimage, description)

    elif mode == 213:
        Radio.AddAvailableLiveStreamItem(name, url, iconimage)

    elif mode == 197:
        Video.ListUHDTrial()

    elif mode == 198:
        Video.ListRecommendations()

    # Modes 301 - 399: Context menu handlers
    elif mode == 301:
        Video.RemoveWatching(episode_id)

except Common.IpwwwError as err:
    xbmcgui.Dialog().ok(Common.translation(30400), str(err))
    sys.exit(1)

xbmcplugin.endOfDirectory(int(sys.argv[1]))
