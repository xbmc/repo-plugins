# -*- coding: utf-8 -*-

'''
    Tulip routine libraries, based on lambda's lamlib
    Author Twilight0

        License summary below, for more details please read license.txt file

        This program is free software: you can redistribute it and/or modify
        it under the terms of the GNU General Public License as published by
        the Free Software Foundation, either version 2 of the License, or
        (at your option) any later version.
        This program is distributed in the hope that it will be useful,
        but WITHOUT ANY WARRANTY; without even the implied warranty of
        MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
        GNU General Public License for more details.
        You should have received a copy of the GNU General Public License
        along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

import xbmc, xbmcaddon, xbmcplugin, xbmcgui, xbmcvfs
import os

integer = 1000
lang = xbmcaddon.Addon().getLocalizedString
setting = xbmcaddon.Addon().getSetting
setSetting = xbmcaddon.Addon().setSetting
addon = xbmcaddon.Addon
addonInfo = xbmcaddon.Addon().getAddonInfo

addItem = xbmcplugin.addDirectoryItem
addItems = xbmcplugin.addDirectoryItems
directory = xbmcplugin.endOfDirectory
content = xbmcplugin.setContent
property = xbmcplugin.setProperty
resolve = xbmcplugin.setResolvedUrl
sortmethod = xbmcplugin.addSortMethod

infoLabel = xbmc.getInfoLabel
condVisibility = xbmc.getCondVisibility
jsonrpc = xbmc.executeJSONRPC
keyboard = xbmc.Keyboard
sleep = xbmc.sleep
execute = xbmc.executebuiltin
skin = xbmc.getSkinDir()
player = xbmc.Player()
playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
monitor = xbmc.Monitor()
wait = monitor.waitForAbort
aborted = monitor.abortRequested

transPath = xbmc.translatePath
skinPath = xbmc.translatePath('special://skin/')
addonPath = xbmc.translatePath(addonInfo('path'))
dataPath = xbmc.translatePath(addonInfo('profile')).decode('utf-8')

window = xbmcgui.Window(10000)
dialog = xbmcgui.Dialog()
progressDialog = xbmcgui.DialogProgress()
windowDialog = xbmcgui.WindowDialog()
button = xbmcgui.ControlButton
image = xbmcgui.ControlImage
alphanum_input = xbmcgui.INPUT_ALPHANUM
password_input = xbmcgui.INPUT_PASSWORD
hide_input = xbmcgui.ALPHANUM_HIDE_INPUT
verify = xbmcgui.PASSWORD_VERIFY
item = xbmcgui.ListItem

openFile = xbmcvfs.File
makeFile = xbmcvfs.mkdir
deleteFile = xbmcvfs.delete
deleteDir = xbmcvfs.rmdir
listDir = xbmcvfs.listdir
exists = xbmcvfs.exists
copy = xbmcvfs.copy

join = os.path.join
settingsFile = os.path.join(dataPath, 'settings.xml')
bookmarksFile = os.path.join(dataPath, 'bookmarks.db')
cacheFile = os.path.join(dataPath, 'cache.db')


def infoDialog(message, heading=addonInfo('name'), icon='', time=3000):
    if icon == '':
        icon = addonInfo('icon')

    try:

        dialog.notification(heading, message, icon, time, sound=False)

    except:

        execute("Notification(%s, %s, %s, %s)" % (heading, message, time, icon))


def okDialog(heading, line1):
    return dialog.ok(heading, line1)


def yesnoDialog(line1, line2='', line3='', heading=addonInfo('name'), nolabel=None, yeslabel=None):
    return dialog.yesno(heading, line1, line2, line3, nolabel, yeslabel)


def selectDialog(list, heading=addonInfo('name')):
    return dialog.select(heading, list)


def openSettings(query=None, id=addonInfo('id')):

    try:

        idle()
        execute('Addon.OpenSettings({0})'.format(id))
        if query is None:
            raise Exception()
        c, f = query.split('.')
        execute('SetFocus(%i)' % (int(c) + 100))
        execute('SetFocus(%i)' % (int(f) + 200))

    except:

        return


def refresh():
    return execute('Container.Refresh')


def idle():
    return execute('Dialog.Close(busydialog)')
