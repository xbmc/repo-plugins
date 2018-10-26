# -*- coding: utf-8 -*-

# Copyright (C) 2018 Alexander Seiler
#
#
# This file is part of plugin.video.telezueri.
#
# plugin.video.telezueri is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# plugin.video.telezueri is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with plugin.video.telezueri.
# If not, see <http://www.gnu.org/licenses/>.

import xbmcaddon
import azmedien

ADDON_ID = 'plugin.video.telezueri'
REAL_SETTINGS = xbmcaddon.Addon(id=ADDON_ID)
ICON = REAL_SETTINGS.getAddonInfo('icon')
FANART = REAL_SETTINGS.getAddonInfo('fanart')
LANGUAGE = REAL_SETTINGS.getLocalizedString
HOST = 'telezueri.ch'


def run():
    """
    Run the plugin.
    """
    customer = azmedien.CustomerAddon(addon_id=ADDON_ID,
                                      real_settings=REAL_SETTINGS,
                                      icon=ICON, fanart=FANART)
    azmedien.run(customer, host=HOST)
