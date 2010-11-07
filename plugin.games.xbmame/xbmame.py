# The contents of this file are subject to the Mozilla Public License
# Version 1.1 (the "License"); you may not use this file except in
# compliance with the License. You may obtain a copy of the License at
# http://www.mozilla.org/MPL/
#
# Software distributed under the License is distributed on an "AS IS"
# basis, WITHOUT WARRANTY OF ANY KIND, either express or implied. See the
# License for the specific language governing rights and limitations
# under the License.
#
# The Original Code is plugin.games.xbmame.
#
# The Initial Developer of the Original Code is Olivier LODY aka Akira76.
# Portions created by the XBMC team are Copyright (C) 2003-2010 XBMC.
# All Rights Reserved.

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
    if len(sys.argv)>2:
        from XBMame import XBMame
        XBMame()
    else:
        xbmc.executebuiltin("ActivateWindow(10001,\"plugin://%s\")" % (ADDON_ID))
