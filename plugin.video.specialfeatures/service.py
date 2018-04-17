# -*- coding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
"""
Main service module

This module handles all Special Features services in Kodi

This file is part of Special Features.

Special Features is free software: you can redistribute it and/or
modify it under the terms of the GNU General Public License as
published by the Free Software Foundation, either version 3 of
the License, or (at your option) any later version.

Special Features is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Special Features. If not, see <http://www.gnu.org/licenses/>.

@author: smitchell6879
@author: evertiro
@license: GPL-3.0
"""

from lib.sys_init import *
from lib.iteration import *


if __name__ == '__main__':
    if sys.version_info[0] < 3:
        encoding()
    while not monitor.abortRequested():
        showcon = addon.getSetting('showcon')
        home.setProperty('SpecialFeatures.ContextMenu', showcon)
        if home.getProperty('SpecialFeatures.Query') != 'true':
            listitem = xbmc.getInfoLabel('Container({}).ListItem.label'.format(xbmc.getInfoLabel('System.CurrentControlID')))
            if home.getProperty('SpecialFeatures.Listitem') != listitem:
                home.setProperty('SpecialFeatures.Listitem', listitem)
                dbEnterExit().initDb('quikchk2')
        if monitor.waitForAbort(1):
            break
