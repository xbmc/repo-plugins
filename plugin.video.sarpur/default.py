#!/usr/bin/env python
# encoding: UTF-8

from __future__ import absolute_import
import sys
import urllib.parse
import sarpur
import xbmcplugin
from sarpur import actions, logger

xbmcplugin.setContent(sarpur.ADDON_HANDLE, 'episodes')

params = dict(urllib.parse.parse_qsl(sys.argv[2][1:]))
action_key = params.get("action_key")
action_value = params.get("action_value")
name = params.get("name")

try:
    if action_key is None:
        actions.index()
    elif hasattr(actions, action_key):
        getattr(actions, action_key)(action_value, name)
    else:
        logger.log("Action: {0}, Value: {1}, Name: {2}".format(
            action_key, action_value, name))

finally:
    xbmcplugin.endOfDirectory(sarpur.ADDON_HANDLE)
