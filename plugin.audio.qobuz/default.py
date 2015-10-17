'''
    default (XBMC addon entry point)
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    :part_of: xbmc-qobuz
    :copyright: (c) 2012 by Joachim Basmaison, Cyril Leclerc
    :license: GPLv3, see LICENSE for more details.
'''

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
