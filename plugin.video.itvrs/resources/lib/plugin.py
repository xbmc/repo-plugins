import os
import sys
import plugintools
import xbmc,xbmcaddon
from addon.common.addon import Addon

addonID = 'plugin.video.itvrs'
addon = Addon(addonID, sys.argv)
local = xbmcaddon.Addon()
icon = local.getAddonInfo('icon')

YOUTUBE_CHANNEL_ID_1 = "UCB2U9Zvptf24QzBnNKHUtsw"

# Entry point
def run():
    plugintools.log("itvrs.run")
    
    # Get params
    params = plugintools.get_params()
    
    if params.get("action") is None:
        main_list(params)
    else:
        pass
    
    plugintools.close_item_list()

# Main menu
def main_list(params):
    plugintools.log("itvrs.main_list "+repr(params))
    
    plugintools.add_item( 
        #action="", 
        title="ITVRS Live TV",
        url="https://www.youtube.com/embed/live_stream?channel="+YOUTUBE_CHANNEL_ID_1+"/",
        thumbnail=icon,
        fanart="fanart.jpg",
        folder=True )    

    plugintools.add_item( 
        #action="", 
        title="Playlists, Live, Broadcasts And Search",
        url="plugin://plugin.video.youtube/channel/"+YOUTUBE_CHANNEL_ID_1+"/",
        thumbnail=icon,
        fanart="fanart.jpg",
        folder=True )    
    
 
        
    playlists = []
    playlists.append(("Movies From Maverick Entertainment","PLDySQNnzfMCqoBxquMEhCOi0GUEB1RbCf"))
    playlists.append(("Scottish Movies","PLmRZGLKXlU2AllRch_NW-MKySlV89M5Vk"))
    playlists.append(("Animated Movies","PLwk819jJ5CdpW41PWVp9wtDrw_KBC9h8y"))
    playlists.append(("Classic Movies - Action","PLwk819jJ5CdqFIs_zKIV4arQeCiItlhlQ"))
    playlists.append(("Classic Movies - Adventure","PLwk819jJ5CdosuzWibf_E6ZmErWt78BZn"))
    playlists.append(("Classic Movies - Crime","PLwk819jJ5Cdqffh8uP9-0F5FB_NJUBGb1"))
    playlists.append(("Classic Movies - Drama","PLwk819jJ5CdoquDFHXiu7vk_pvOLDlhvA"))
    playlists.append(("Classic Movies - Fantasy","PLwk819jJ5CdrF_b1oht-tC0O0HxFP6D4g"))
    playlists.append(("Classic Movies - Westerns","PLwk819jJ5CdqSi7GIeguKeU3ul-byTEF2"))
    playlists.append(("News","PLwk819jJ5Cdo9jItpKsCZINK1R-cVCl5X"))


    for playlist in playlists:
        plugintools.add_item( 
            title=playlist[0],
            url="plugin://plugin.video.youtube/playlist/"+playlist[1]+"/",
            thumbnail=icon,
            fanart="fanart.jpg",
        folder=True )

run()

