'''
    gdrive (Google Drive ) for KODI / XBMC Plugin
    Copyright (C) 2013-2016 ddurdle

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.


'''

import re
import sys
KODI = True
if re.search(re.compile('.py', re.IGNORECASE), sys.argv[0]) is not None:
    KODI = False

from resources.lib import gdrive_api2
from resources.lib import gdrive_api3

PLUGIN_NAME = 'gdrive'

if KODI:
    # cloudservice - standard XBMC modules
    import xbmc, xbmcgui, xbmcplugin, xbmcaddon, xbmcvfs

    # global variables
    #addon = xbmcaddon.Addon(id='plugin.video.gdrive')
    addon = xbmcaddon.Addon(id='plugin.gdrive')

else:
    from resources.libgui import xbmcaddon
    addon = xbmcaddon.xbmcaddon()

cloudservice3 = gdrive_api3.gdrive
cloudservice2 = gdrive_api2.gdrive


class CONST():

    spreadsheet = True
    testing_features = False
    CACHE = True
    SRT = True
    CC = True
    DEBUG = False
    tvwindow = False
    tmdb = False