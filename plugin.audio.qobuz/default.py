#     Copyright 2011 Stephen Denham, Joachim Basmaison, Cyril Leclerc
#
#     This file is part of xbmc-qobuz.
#
#     xbmc-qobuz is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     xbmc-qobuz is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.   See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with xbmc-qobuz.   If not, see <http://www.gnu.org/licenses/>.

import os
import sys
import xbmcaddon
import xbmc

pluginId = 'plugin.audio.qobuz'
__addon__ = xbmcaddon.Addon(id=pluginId)
__addonversion__ = __addon__.getAddonInfo('version')
__addonid__ = __addon__.getAddonInfo('id')
__cwd__ = __addon__.getAddonInfo('path')
__addondir__ = __addon__.getAddonInfo('path')
__libdir__ = xbmc.translatePath(os.path.join(__addondir__, 'resources', 'lib'))
__qobuzdir__ = xbmc.translatePath(os.path.join(__libdir__, 'qobuz'))
sys.path.append(__libdir__)
sys.path.append(__qobuzdir__)

from exception import QobuzXbmcError
from bootstrap import QobuzBootstrap
from debug import warn

__handle__ = int(sys.argv[1])
boot = QobuzBootstrap(__addon__, __handle__)

try:
    boot.bootstrap_app()
    boot.dispatch()
except QobuzXbmcError as e:
    warn('[' + pluginId + ']', "Exception while running plugin")
