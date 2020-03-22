# SPDX-License-Identifier: CC-BY-NC-SA-4.0

from resources.lib import menu

# Debug code
# import sys
# import xbmcgui
# sys.listitem = xbmcgui.ListItem("Test", path="plugin://plugin.video.retrospect/?action=listfolder&channel=chn_kijknl&channelcode=net5")
# sys.listitem = xbmcgui.ListItem("Test", path="plugin://plugin.video.retrospect/?action=listfolder&channel=chn_kijknl")

with menu.Menu("Set InputStream Adaptive") as m:
    m.set_inputstream_adaptive()
