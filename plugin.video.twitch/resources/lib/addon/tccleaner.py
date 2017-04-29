# -*- coding: utf-8 -*-
"""
    TextureCacheCleaner for Kodi Add-ons

    A simple module to remove cached items from Kodi's Texture13.db and the corresponding cached image

    usage:
        from tccleaner import TextureCacheCleaner
        TextureCacheCleaner().remove_like('http%domain.com/%.jpg')
        # remove all cached items matching sqlite LIKE pattern http%domain.com/%.jpg

    Copyright (C) 2016 anxdpanic

    Modified by Twitch-on-Kodi/plugin.video.twitch Dec. 12, 2016

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
        if xbmcvfs.exists(self.DATABASE):
            connection = sqlite3.connect(self.DATABASE)
            connection.isolation_level = None
            cursor = connection.cursor()
            dialog = None
            thumbnails = list()
            if notify:
                dialog = xbmcgui.DialogProgressBG()
                dialog.create(self.NAME + ' Cache Removal', 'Removing cached items ...')
            try:
                cursor.execute('BEGIN')
                cursor.execute('SELECT id, cachedurl FROM texture WHERE url LIKE "{0}"'.format(pattern))
                rows_list = cursor.fetchall()
                row_count = len(rows_list)
                percent = 100 / (row_count + 5)
                if row_count > 0:
                    for index, row in enumerate(rows_list):
                        if dialog:
                            dialog.update(percent * (index + 1), message='Removing cached item ... {0}'.format(row[1]))
                        thumbnail_path = xbmc.translatePath("special://thumbnails/{0}".format(row[1]))
                        cursor.execute('DELETE FROM sizes WHERE idtexture LIKE "{0}"'.format(row[0]))
                        if xbmcvfs.exists(thumbnail_path):
                            thumbnails.append(thumbnail_path)
                    if dialog:
                        dialog.update(percent * (row_count + 1), message='Removing cached items from texture ...')
                    cursor.execute('DELETE FROM texture WHERE url LIKE "{0}"'.format(pattern))
                if dialog:
                    dialog.update(percent * (row_count + 2), message='Committing ...')
                    cursor.execute('COMMIT')
                    dialog.update(percent * (row_count + 3), message='Recovering free space ...')
                    cursor.execute('VACUUM')
                    dialog.update(percent * (row_count + 4), message='Committing ...')
                    connection.commit()
                    dialog.update(100, message='Cached items removed')
                else:
                    cursor.execute('COMMIT')
                    cursor.execute('VACUUM')
                    connection.commit()
            except:
                if dialog:
                    dialog.close()
                thumbnails = list()
                message = 'Error removing cached items, rolling back ...'
                self.notification(message, sound=True)
                xbmc.log(message, xbmc.LOGDEBUG)
                connection.rollback()
            finally:
                cursor.close()
                connection.close()
                if thumbnails:
                    percent = 100 / len(thumbnails)
                    for index, thumb in enumerate(thumbnails):
                        if dialog:
                            dialog.update(percent * (index + 1), message='Deleting cached item ... {0}'.format(thumb))
                        try:
                            xbmcvfs.delete(thumb)
                        except:
                            try:
                                os.remove(thumb)
                            except:
                                message = 'Failed to delete |{0}|'.format(thumb)
                                xbmc.log(message, xbmc.LOGERROR)
                if dialog:
                    dialog.close()
        else:
            message = 'Database not found ({0})'.format(self.DATABASE)
            self.notification(message)
            xbmc.log(message, xbmc.LOGDEBUG)
