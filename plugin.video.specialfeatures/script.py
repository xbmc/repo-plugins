# -*- coding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
"""
Main script module

This module handles all Special Features scripts in Kodi

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
from lib.importexport import *


class Routines:
    def updateDB(self):
        query = 'movies'
        query2 = 'tvshows'
        note(txt=lang(30050))
        resultFILTER().router(query)
        resultFILTER().router(query2)
        dbEnterExit().initDb('update')
        exit()

    def cleanDb(self):
        dbEnterExit().initDb('clean')
        note(txt=lang(30065))

    def editInfo(self):
        dbEnterExit().quckEdit()

    def exportDb(self):
        dbEnterExit().initDb('export')

    def listItem(self):
        self.url = home.getProperty('SpecialFeatures.Path')
        if xbmc.getInfoLabel('System.CurrentWindow') == 'Videos':
            xbmc.executebuiltin('Container.Update({})'.format(self.url))
        else:
            xbmc.executebuiltin('ActivateWindow(videos, {} ,return)'.format(self.url))

    def get_url(self, **kwargs):
        return '{0}?{1}'.format("plugin://plugin.video.specialfeatures/", urlencode(kwargs))


if __name__ == '__main__':
    r = Routines()
    if sys.version_info[0] < 3:
        encoding()
    if len(sys.argv) > 1:
        if sys.argv[1] == 'scandb':
            r.updateDB()
        elif sys.argv[1] == 'listitem':
            r.listItem()
        elif sys.argv[1] == 'cleandb':
            r.cleanDb()
        elif sys.argv[1] == 'export':
            r.exportDb()
        elif sys.argv[1] == 'editinfo':
            r.editInfo()
        elif sys.argv[1] == 'test':
            text(xbmc.getInfoLabel('ListItem.Property(PlayAll)'))
            text(xbmc.getInfoLabel('String.StartsWith(Container.FolderPath,plugin://plugin.video.specialfeatures)'))
            text('Done')
    else:
        xbmc.executebuiltin('Addon.OpenSettings({})'.format(addonid))
