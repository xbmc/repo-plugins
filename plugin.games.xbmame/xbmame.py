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
import sys
from xbmcaddon import Addon

# Shared resources
ADDON_ID = "plugin.games.xbmame"
sys.path.append(os.path.join(Addon(ADDON_ID).getAddonInfo("path"), "resources", "lib" ))

if __name__ == "__main__":
    from XBMame import XBMame
    XBMame(ADDON_ID)
