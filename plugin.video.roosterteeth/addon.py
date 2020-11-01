#!/usr/bin/env python
# -*- coding: UTF-8 -*-

#
# Imports
#
from future import standard_library
standard_library.install_aliases()
from builtins import str
import sys
import urllib.parse

# Parse parameters...
if len(sys.argv[2]) == 0:
    #
    # Main menu
    #
    from resources.lib import roosterteeth_main as plugin
else:
    action = urllib.parse.parse_qs(urllib.parse.urlparse(sys.argv[2]).query)['action'][0]
    #
    # List
    #
    if action == 'list-episodes':
        from resources.lib import roosterteeth_list_episodes as plugin
    #
    # List Series
    #
    elif action == 'list-series':
        from resources.lib import roosterteeth_list_series as plugin
    #
    # List Serie seasons
    #
    elif action == 'list-serie-seasons':
        from resources.lib import roosterteeth_list_serie_seasons as plugin
    #
    # Play
    #
    elif action == 'play':
        from resources.lib import roosterteeth_play as plugin

plugin.Main()
