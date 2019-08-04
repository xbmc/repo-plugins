#===============================================================================
# LICENSE Retrospect-Framework - CC BY-NC-ND
#===============================================================================
# This work is licenced under the Creative Commons
# Attribution-Non-Commercial-No Derivative Works 3.0 Unported License. To view a
# copy of this licence, visit http://creativecommons.org/licenses/by-nc-nd/3.0/
# or send a letter to Creative Commons, 171 Second Street, Suite 300,
# San Francisco, California 94105, USA.
#===============================================================================

import menu

# import sys
# import xbmcgui
# sys.listitem = xbmcgui.ListItem("Test", path="plugin://plugin.video.retrospect/?action=listfolder&channelcode=uzgjson&channel=chn_nos2010")

with menu.Menu("Select Channels") as m:
    m.select_channels()
