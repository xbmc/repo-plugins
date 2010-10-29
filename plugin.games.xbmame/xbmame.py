import os
import re
import sys
import xbmc
from xbmcaddon import Addon
import platform

# Shared resources

ADDON_ID = "plugin.games.xbmame"
ADDON_PATH = Addon(ADDON_ID).getAddonInfo("path")
BASE_RESOURCE_PATH = os.path.join(ADDON_PATH, "resources")
sys.path.append( os.path.join( BASE_RESOURCE_PATH, "lib" ) )
sys.path.append( os.path.join( BASE_RESOURCE_PATH, "lib", "obj" ) )

env = ( os.environ.get( "OS", "win32" ), "win32", )[ os.environ.get( "OS", "win32" ) == "xbox" ]
if re.match("Linux", env):
    if(platform.machine()=="x86_64"): env = "Linux64"
sys.path.append( os.path.join( BASE_RESOURCE_PATH, "platform_libraries", env ) )

if __name__ == "__main__":
    if len(sys.argv)>1:
        from XBMame import XBMame
        XBMame()
    else:
        xbmc.executebuiltin("ActivateWindow(10001,plugin://%s)" % ADDON_ID)