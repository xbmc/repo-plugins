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

from os import path, makedirs, remove
from xbmc import *
from xbmcgui import *
from xbmcaddon import *

dialog = Dialog()

class XBMame:

    def __init__(self, ADDON_ID):
        self.__language__ = Addon(ADDON_ID).getLocalizedString
        self.__profile__ = Addon(ADDON_ID).getAddonInfo("profile")
        dialog.ok(self.__language__(30000), self.__language__(30001), self.__language__(30002), self.__language__(30003))
	executebuiltin("xbmc.activatewindow(addonbrowser)")
