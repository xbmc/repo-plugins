#!/usr/bin/env python
# encoding: UTF-8

import sys
import urlparse
import sarpur
import xbmcplugin
from sarpur import actions, logger

xbmcplugin.setContent(sarpur.ADDON_HANDLE, 'episodes')

params = dict(urlparse.parse_qsl(sys.argv[2][1:]))
action_key = params.get("action_key")
action_value = params.get("action_value")
name = params.get("name")

try:
    if action_key is None:
        actions.index()
    elif action_key == 'view_category':
        actions.view_category(action_value, name)
    elif action_key == 'play_file':
        actions.play_video(action_value, name)
    elif action_key == 'play_url':
        actions.play_url(action_value, name)
    elif action_key == 'view_podcast_index':
        actions.podcast_index()
    elif action_key == 'view_podcast_show':
        actions.podcast_show(action_value, name)
    elif action_key == 'play_podcast':
        actions.play_podcast(action_value, name)
    elif action_key == 'play_live':
        actions.play_live_stream(action_value, name)
    elif action_key == 'search':
        actions.search()
    elif action_key == "view_live_index":
        actions.live_index()
    else:
        logger.log("Action: {0}, Value: {1}, Name: {2}".format(
            action_key, action_value, name))

finally:
    xbmcplugin.endOfDirectory(sarpur.ADDON_HANDLE)
