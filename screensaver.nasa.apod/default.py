#   Copyright (C) 2021 Evinr
#
#
# This file is part of NASA APOD ScreenSaver.
#
# NASA APOD ScreenSaver is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# NASA APOD ScreenSaver is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with NASA APOD ScreenSaver.  If not, see <http://www.gnu.org/licenses/>.

from resources.lib.gui import GUI
from kodi_six          import xbmcaddon

# Plugin Info
ADDON_ID       = 'screensaver.nasa.apod'
REAL_SETTINGS  = xbmcaddon.Addon(id=ADDON_ID)
ADDON_PATH     = REAL_SETTINGS.getAddonInfo('path')

if __name__ == '__main__':
    ui = GUI("default.xml", ADDON_PATH, "default")
    ui.doModal()
    del ui