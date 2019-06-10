#!/usr/bin/env python
# -*- coding: UTF-8 -*-

#
# Imports
#
from future import standard_library
standard_library.install_aliases()
from builtins import str
import os
import sys
import urllib.parse
import xbmc
import xbmcaddon


LIB_DIR = xbmc.translatePath(
    os.path.join(xbmcaddon.Addon(id="plugin.video.roosterteeth").getAddonInfo('path'), 'resources', 'lib'))
sys.path.append(LIB_DIR)

# Parse parameters...
if len(sys.argv[2]) == 0:
    #
    # Main menu
    #
    import roosterteeth_main as plugin
else:
    action = urllib.parse.parse_qs(urllib.parse.urlparse(sys.argv[2]).query)['action'][0]
    #
    # List
    #
    if action == 'list-episodes':
        import roosterteeth_list_episodes as plugin
    #
    # List Series
    #
    if action == 'list-series':
        import roosterteeth_list_series as plugin
    #
    # List Serie seasons
    #
    if action == 'list-serie-seasons':
        import roosterteeth_list_serie_seasons as plugin
    #
    # Play
    #
    elif action == 'play':
        import roosterteeth_play as plugin

plugin.Main()
