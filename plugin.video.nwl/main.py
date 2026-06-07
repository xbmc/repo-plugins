# SPDX-License-Identifier: GPL-2.0-or-later
# Original plugin.video.mlbtv © eracknaphobia
# Modified for NWL compatibility and code cleanup

from resources.lib.nwl import *

params = get_params()
mode = None
page_start = 0
id = None

if 'mode' in params:
    mode = int(params["mode"])

if 'page_start' in params:
    page_start = int(params["page_start"])

if 'id' in params:
    id = urllib.unquote_plus(params["id"])

if mode is None:
    categories()

# Today's Games
elif mode == 100:
    list_games()

# On Demand
elif mode == 101:
    list_games('ondemand', page_start)

elif mode == 104:
    stream_select(id)

elif mode == 999:
    sys.exit()

if mode == 100:
    xbmcplugin.endOfDirectory(addon_handle, cacheToDisc=False)
else:
    xbmcplugin.endOfDirectory(addon_handle)
