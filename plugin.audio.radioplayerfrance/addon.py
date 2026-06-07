import sys
#from pathlib import Path
from urllib.parse import parse_qsl
from resources.lib.ui import KodiUI
from resources.lib.navigator import Navigator

#from xbmcaddon import Addon
#from xbmcvfs import translatePath

# Get the plugin url in plugin:// notation.
BASE_URL = sys.argv[0]
# Get a plugin handle as an integer number.
HANDLE = int(sys.argv[1])
# Get parameters
PARAMS = dict(parse_qsl(sys.argv[2][1:]))

# Get the addon base path
# ADDON_PATH = Path(translatePath(Addon().getAddonInfo('path')))

# Instantiate UI and navigator
ui = KodiUI(HANDLE, BASE_URL)
nav = Navigator(ui)

def router(params):
    """Dispatch based on 'action' parameter."""
    action = params.get('action')

    if action is None:
        # If the plugin is called from Kodi UI without any parameters,
        nav.list_root()
    elif action == "list_recommended":
        nav.list_recommended()
    elif action == "list_categories":
        nav.list_categories()
    elif action == "list_radios":
        nav.list_radios(params["category_id"])
    elif action == "play_stream":
        nav.play_stream(params["stream_id"])
    else:
        raise ValueError(f'Invalid params: {params}!')
        # xbmcgui.Dialog().notification("Error", f"Unknown action: {action}")


if __name__ == '__main__':
    # Call the router function and pass the plugin call parameters to it.
    router(PARAMS)