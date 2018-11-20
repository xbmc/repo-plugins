# -*- coding: utf-8 -*-
"""
    screensaver.kaster
    Copyright (C) 2017 enen92

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
"""

from resources.lib.screensaver import Kaster
import xbmcaddon

PATH = xbmcaddon.Addon().getAddonInfo("path")

if __name__ == '__main__':
    screensaver = Kaster(
        'screensaver-kaster.xml',
        PATH,
        'default',
        '',
    )
    screensaver.doModal()
    del screensaver
