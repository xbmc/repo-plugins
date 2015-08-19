# -*- coding: utf-8 -*-
#------------------------------------------------------------
# TRUTH VIDEOS Addon by L33TGUY
#------------------------------------------------------------
# License: GPL (http://www.gnu.org/licenses/gpl-3.0.html)
# Based on code from youtube addon
#
# Author: L33TGUY
# Twitter:  @truth_videos
#------------------------------------------------------------

import os
import sys
import plugintools
import xbmc,xbmcaddon
from addon.common.addon import Addon

addonID = 'plugin.video.docu'
addon = Addon(addonID, sys.argv)
local = xbmcaddon.Addon(id=addonID)
icon = local.getAddonInfo('icon')

YOUTUBE_CHANNEL_ID_1 = "UFOTVstudios"
YOUTUBE_CHANNEL_ID_2 = "vice"
YOUTUBE_CHANNEL_ID_3 = "journeymanpictures"
YOUTUBE_CHANNEL_ID_4 = "RTDocumentaries"
YOUTUBE_CHANNEL_ID_5 = "davidicke"
YOUTUBE_CHANNEL_ID_6 = "TheAlexJonesChannel"
YOUTUBE_CHANNEL_ID_7 = "MisterMachine1977"
YOUTUBE_CHANNEL_ID_8 = "thirdphaseofmoon"
YOUTUBE_CHANNEL_ID_9 = "corbettreport"
YOUTUBE_CHANNEL_ID_10 = "StormCloudsGathering"
YOUTUBE_CHANNEL_ID_11 = "PowerfulJRE"
YOUTUBE_CHANNEL_ID_12 = "wearechange"
YOUTUBE_CHANNEL_ID_13 = "GrahamHancockDotCom"
YOUTUBE_CHANNEL_ID_14 = "TZMOfficialChannel"

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
        title="UFOTV Studios",
        url="plugin://plugin.video.youtube/user/"+YOUTUBE_CHANNEL_ID_1+"/",
        thumbnail=icon,
        folder=True )

    plugintools.add_item( 
        #action="", 
        title="Vice",
        url="plugin://plugin.video.youtube/user/"+YOUTUBE_CHANNEL_ID_2+"/",
        thumbnail=icon,
        folder=True )

    plugintools.add_item( 
        #action="", 
        title="Journeyman Pictures",
        url="plugin://plugin.video.youtube/user/"+YOUTUBE_CHANNEL_ID_3+"/",
        thumbnail=icon,
        folder=True )

    plugintools.add_item( 
        #action="", 
        title="Russia Today Documentaries",
        url="plugin://plugin.video.youtube/user/"+YOUTUBE_CHANNEL_ID_4+"/",
        thumbnail=icon,
        folder=True )

    plugintools.add_item( 
        #action="", 
        title="David Icke",
        url="plugin://plugin.video.youtube/user/"+YOUTUBE_CHANNEL_ID_5+"/",
        thumbnail=icon,
        folder=True )

    plugintools.add_item( 
        #action="", 
        title="Alex Jones",
        url="plugin://plugin.video.youtube/user/"+YOUTUBE_CHANNEL_ID_6+"/",
        thumbnail=icon,
        folder=True )

    plugintools.add_item( 
        #action="", 
        title="Mister Enigma",
        url="plugin://plugin.video.youtube/user/"+YOUTUBE_CHANNEL_ID_7+"/",
        thumbnail=icon,
        folder=True )

    plugintools.add_item( 
        #action="", 
        title="ThirdPhaseOfMoon",
        url="plugin://plugin.video.youtube/user/"+YOUTUBE_CHANNEL_ID_8+"/",
        thumbnail=icon,
        folder=True )
        
    plugintools.add_item( 
        #action="", 
        title="The Corbett Report",
        url="plugin://plugin.video.youtube/user/"+YOUTUBE_CHANNEL_ID_9+"/",
        thumbnail=icon,
        folder=True )

    plugintools.add_item( 
        #action="", 
        title="Storm Clouds Gathering",
        url="plugin://plugin.video.youtube/user/"+YOUTUBE_CHANNEL_ID_10+"/",
        thumbnail=icon,
        folder=True )                

    plugintools.add_item( 
        #action="", 
        title="The Joe Rogan Experience",
        url="plugin://plugin.video.youtube/user/"+YOUTUBE_CHANNEL_ID_11+"/",
        thumbnail=icon,
        folder=True )    

    plugintools.add_item( 
        #action="", 
        title="We Are Change",
        url="plugin://plugin.video.youtube/user/"+YOUTUBE_CHANNEL_ID_12+"/",
        thumbnail=icon,
        folder=True )  

    plugintools.add_item( 
        #action="", 
        title="Graham Hancock",
        url="plugin://plugin.video.youtube/user/"+YOUTUBE_CHANNEL_ID_13+"/",
        thumbnail=icon,
        folder=True )  

    plugintools.add_item( 
        #action="", 
        title="The Zeitgeist Movement",
        url="plugin://plugin.video.youtube/user/"+YOUTUBE_CHANNEL_ID_14+"/",
        thumbnail=icon,
        folder=True ) 

run()
