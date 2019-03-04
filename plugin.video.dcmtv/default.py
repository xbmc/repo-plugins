import os
import sys
import plugintools
import xbmc,xbmcaddon
from addon.common.addon import Addon
addonID = 'plugin.video.dcmtv'
addon = Addon(addonID, sys.argv)
local = xbmcaddon.Addon(id=addonID)
icon = local.getAddonInfo('icon')
YOUTUBE_CHANNEL_ID = "MrMrtonyangelo"
def run():
    plugintools.log("dcmtv.run")
    params = plugintools.get_params()
    if params.get("action") is None:
        main_list(params)
    else:
        pass
    plugintools.close_item_list()
def main_list(params):
    plugintools.log("dcmtv.main_list "+repr(params))
    plugintools.add_item(
        title="DCM is a fast evolving multimedia company",
        url="plugin://plugin.video.youtube/user/"+YOUTUBE_CHANNEL_ID+"/",
        thumbnail=icon,
        folder=True )
run()