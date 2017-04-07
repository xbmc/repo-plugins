# -*- coding: utf-8 -*-
#------------------------------------------------------------
# License: GPL (http://www.gnu.org/licenses/gpl-3.0.html)
# Based on code from youtube addon
#------------------------------------------------------------

import os
import sys
import plugintools
import xbmc,xbmcaddon
from addon.common.addon import Addon

addonID = 'plugin.video.hardstyletv'
addon = Addon(addonID, sys.argv)
local = xbmcaddon.Addon()
icon = local.getAddonInfo('icon')

YOUTUBE_PLAYLIST_ID = "PLUKXSlbHWi2huhANVImh3RxMQ19ASXw6p"

# Entry point
def run():
    plugintools.log("hardstyletv.run")
    
    # Get params
    params = plugintools.get_params()
    
    if params.get("action") is None:
        main_list(params)
    else:
        pass
    
    plugintools.close_item_list()

# Main menu
def main_list(params):
    plugintools.log("hardstyletv.main_list "+repr(params))

    plugintools.add_item( 
        title="Qlimax 2016",
        url="plugin://plugin.video.youtube/playlist/PLUKXSlbHWi2g6Hp2Sq4Gz5Wte6MRpOX5U/",
        thumbnail=icon,
        folder=True )

    plugintools.add_item( 
        title="Q-Base 2016",
        url="plugin://plugin.video.youtube/playlist/PLUKXSlbHWi2iWv8pO6ft101PaGS6Qjrv_/",
        thumbnail=icon,
        folder=True )

    plugintools.add_item( 
        title="Defqon.1 2016",
        url="plugin://plugin.video.youtube/playlist/PLUKXSlbHWi2i9gLEWlV76dsS_I9pk4RbD/",
        thumbnail=icon,
        folder=True )

    plugintools.add_item( 
        title="QAPITAL 2016",
        url="plugin://plugin.video.youtube/playlist/PLUKXSlbHWi2jW3pkaYl34gDaUrJ34ncRI/",
        thumbnail=icon,
        folder=True )

    plugintools.add_item( 
        title="Hard Bass 2016",
        url="plugin://plugin.video.youtube/playlist/PLUKXSlbHWi2jv7VvXsh1XMNu_0E7LcrWJ/",
        thumbnail=icon,
        folder=True )

    plugintools.add_item( 
        title="Qlimax 2015",
        url="plugin://plugin.video.youtube/playlist/PLUKXSlbHWi2guDBcyAxQgWuU-uDx8ZL5s/",
        thumbnail=icon,
        folder=True )

    plugintools.add_item( 
        title="Defqon.1 2015",
        url="plugin://plugin.video.youtube/playlist/PLUKXSlbHWi2g9sdCH_6scus_EBOZGhq7C/",
        thumbnail=icon,
        folder=True )

    plugintools.add_item( 
        title="QAPITAL 2015",
        url="plugin://plugin.video.youtube/playlist/PLUKXSlbHWi2gCKp8OLVZzmGxZI5FAZmSU/",
        thumbnail=icon,
        folder=True )

    plugintools.add_item( 
        title="Hard Bass 2015",
        url="plugin://plugin.video.youtube/playlist/PLUKXSlbHWi2hsUFxs1o2DukBJiqMDAcX2/",
        thumbnail=icon,
        folder=True )

    plugintools.add_item( 
        title="Qlimax OLD",
        url="plugin://plugin.video.youtube/playlist/PLUKXSlbHWi2jLjh0TYWIde8LjdImdM38f/",
        thumbnail=icon,
        folder=True )

    plugintools.add_item( 
        title="Defqon.1 OLD",
        url="plugin://plugin.video.youtube/playlist/PLUKXSlbHWi2hjXmAbhSXlzb33Kbe8MWBo/",
        thumbnail=icon,
        folder=True )

    plugintools.add_item( 
        title="Hard Bass OLD",
        url="plugin://plugin.video.youtube/playlist/PLUKXSlbHWi2gpenEDab_9n-RKbRMUViB2/",
        thumbnail=icon,
        folder=True )


run()