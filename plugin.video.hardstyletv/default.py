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

    playlists = []
    playlists.append(("Q-Base 2018","PLUKXSlbHWi2joC0am3Uhj_J2RGVI34K3t"))
    playlists.append(("Defqon.1 2018","PLUKXSlbHWi2jPniJM-0D3rWavFppOnHPy"))
    playlists.append(("Hard Bass 2018","PLUKXSlbHWi2jnzPKht6hbcbcXlPMOeOko"))
    playlists.append(("Qlimax 2017","PLUKXSlbHWi2gbP8-kRpPwzVnMJ8osz3fZ"))
    playlists.append(("Q-Base 2017","PLUKXSlbHWi2ifrVf6J7icaBrgjYxrl1dY"))
    playlists.append(("Defqon.1 2017","PLUKXSlbHWi2i-2j0Zv1EppYrDPdDbqoJp"))
    playlists.append(("Hard Bass 2017","PLUKXSlbHWi2jthONLKZm6YalKIUxMViEm"))
    playlists.append(("Qlimax 2016","PLUKXSlbHWi2g6Hp2Sq4Gz5Wte6MRpOX5U"))
    playlists.append(("Q-Base 2016","PLUKXSlbHWi2iWv8pO6ft101PaGS6Qjrv_"))
    playlists.append(("Defqon.1 2016","PLUKXSlbHWi2i9gLEWlV76dsS_I9pk4RbD"))
    playlists.append(("Hard Bass 2016","PLUKXSlbHWi2jv7VvXsh1XMNu_0E7LcrWJ"))
    playlists.append(("Defqon.1 2015","PLUKXSlbHWi2g9sdCH_6scus_EBOZGhq7C"))
    playlists.append(("Hard Bass 2015","PLUKXSlbHWi2hsUFxs1o2DukBJiqMDAcX2"))
    playlists.append(("Qapital Sets","PLUKXSlbHWi2jW3pkaYl34gDaUrJ34ncRI"))
    playlists.append(("Qlimax OLD","PLUKXSlbHWi2jLjh0TYWIde8LjdImdM38f"))
    playlists.append(("Defqon.1 OLD","PLUKXSlbHWi2hjXmAbhSXlzb33Kbe8MWBo"))
    playlists.append(("Hard Bass OLD","PLUKXSlbHWi2gpenEDab_9n-RKbRMUViB2"))


    for playlist in playlists:
        plugintools.add_item( 
            title=playlist[0],
            url="plugin://plugin.video.youtube/playlist/"+playlist[1]+"/",
            thumbnail=icon,
            folder=True )

run()