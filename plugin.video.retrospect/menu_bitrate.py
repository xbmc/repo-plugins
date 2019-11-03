# SPDX-License-Identifier: CC-BY-NC-SA-4.0

from resources.lib import menu

# import sys
# import xbmcgui
# sys.listitem = xbmcgui.ListItem("Test", path="plugin://plugin.video.retrospect/?action=listfolder&channelcode=uzgjson&channel=chn_nos2010")

with menu.Menu("Set Bitrate") as m:
    m.set_bitrate()
