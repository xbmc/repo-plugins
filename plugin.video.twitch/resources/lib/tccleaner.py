# -*- coding: utf-8 -*-
"""
    TextureCacheCleaner for Kodi Add-ons

    A simple module to remove cached items from Kodi's Texture13.db and the corresponding cached image

    usage:
        from tccleaner import TextureCacheCleaner
        TextureCacheCleaner().remove_like('http%domain.com/%.jpg')
        # remove all cached items matching sqlite LIKE pattern http%domain.com/%.jpg

    Copyright (C) 2016 anxdpanic

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program. If not, see <http://www.gnu.org/licenses/>.
"""

import os
import sqlite3
import xbmc
import xbmcgui
import xbmcaddon
import xbmcvfs


class TextureCacheCleaner(object):
    ICON = xbmc.translatePath('special://home/addons/%s/icon.png' % xbmcaddon.Addon().getAddonInfo('id'))
    NAME = xbmcaddon.Addon().getAddonInfo('name')
    DATABASE = xbmc.translatePath('special://database/Textures13.db')

    def notification(self, message, time=2000, sound=False):
        xbmcgui.Dialog().notification(self.NAME, message, self.ICON, time, sound)

    def remove_like(self, pattern, notify=True):
        """
        Removes cached items with urls LIKE pattern
            from sqlite database(Textures13.db) and deletes cached image
        :param pattern: string: an sqlite LIKE pattern of image url(s) to be removed
        :param notify: bool: enable/disable informational notifications
        :return:
        """
        do_notification = False
        if notify:
            do_notification = True
        if xbmcvfs.exists(self.DATABASE):
            connection = sqlite3.connect(self.DATABASE)
            connection.isolation_level = None
            cursor = connection.cursor()
            try:
                if do_notification:
                    self.notification('Removing cached items ...')
                cursor.execute('BEGIN')
                cursor.execute('SELECT id, cachedurl FROM texture WHERE url LIKE "{0}"'.format(pattern))
                rows_list = cursor.fetchall()
                for row in rows_list:
                    thumbnail_path = xbmc.translatePath("special://thumbnails/{0}".format(row[1]))
                    cursor.execute('DELETE FROM sizes WHERE idtexture LIKE "{0}"'.format(row[0]))
                    if xbmcvfs.exists(thumbnail_path):
                        try:
                            xbmcvfs.delete(thumbnail_path)
                        except:
                            try:
                                os.remove(thumbnail_path)
                            except:
                                raise OSError
                cursor.execute('DELETE FROM texture WHERE url LIKE "{0}"'.format(pattern))
                cursor.execute('COMMIT')
                cursor.execute('VACUUM texture')
                cursor.execute('VACUUM sizes')
                connection.commit()
                if do_notification:
                    self.notification('Cached items removed')
            except:
                message = 'Error removing cached items, rolling back'
                self.notification(message, sound=True)
                xbmc.log(message, xbmc.LOGDEBUG)
                connection.rollback()
            finally:
                cursor.close()
                connection.close()
        else:
            message = 'Database not found ({0})'.format(self.DATABASE)
            if do_notification:
                self.notification(message)
            xbmc.log(message, xbmc.LOGDEBUG)
