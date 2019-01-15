# -*- coding: utf-8 -*-
#------------------------------------------------------------
# KODI Add-on for http://www.youtube.com/user/doomcomhr
#------------------------------------------------------------
# License: GPL (http://www.gnu.org/licenses/gpl-3.0.html)
# Based on code from youtube addon
#------------------------------------------------------------
# Changelog:
# 1.0.0
# - First release
# 1.0.2
# - Playable items no use isPlayable=True and folder=False
# 1.0.5
# - PluginTools library updated to 1.0.5
# 1.0.8
# - PluginTools library updated to 1.0.8
#---------------------------------------------------------------------------

import os
import sys
import plugintools
import xbmc,xbmcaddon
from addon.common.addon import Addon

addonID = 'plugin.video.doomcomhr'
addon = Addon(addonID, sys.argv)
local = xbmcaddon.Addon(id=addonID)
icon = local.getAddonInfo('icon')

YOUTUBE_CHANNEL_ID_1 = "UCuy3ApT1zlEcbSDPkb2j6cA"
YOUTUBE_CHANNEL_ID_2 = "UCfoaUAr2rLZBjLeIJzrS9NQ"
YOUTUBE_CHANNEL_ID_3 = "UCqcYluu5zm7uqBNGL8kextA"


# Entry point
def run():
    plugintools.log("docu.run")
    
    # Get params
    params = plugintools.get_params()
    
    if params.get("action") is None:
        main_list(params)
    else:
        action = params.get("action")
        exec action+"(params)"
    
    plugintools.close_item_list()

# Main menu
def main_list(params):
    plugintools.log("docu.main_list "+repr(params))

    plugintools.add_item( 
        #action="", 
        title="Competition Doom",
        url="plugin://plugin.video.youtube/channel/"+YOUTUBE_CHANNEL_ID_1+"/",
        thumbnail="http://www.doom.com.hr/cndoom/kodi/compet-n_logo.png",
        folder=True )

    plugintools.add_item( 
        #action="", 
        title="COMPET-N",
        url="plugin://plugin.video.youtube/channel/"+YOUTUBE_CHANNEL_ID_2+"/",
        thumbnail="http://www.doom.com.hr/cndoom/kodi/compet-n_logo_old.png",
        folder=True )

    plugintools.add_item( 
        #action="", 
        title="DSDA",
        url="plugin://plugin.video.youtube/channel/"+YOUTUBE_CHANNEL_ID_3+"/",
        thumbnail="http://www.doom.com.hr/cndoom/kodi/dsda.png",
        folder=True )
run()
