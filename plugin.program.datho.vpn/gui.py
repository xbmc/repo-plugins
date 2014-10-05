#
#       Copyright (C) 2014 Datho Digital Inc
#       Martin Candurra (martincandurra@dathovpn.com)
#
#  This Program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2, or (at your option)
#  any later version.
#
#  This Program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with XBMC; see the file COPYING.  If not, write to
#  the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.
#  http://www.gnu.org/copyleft/gpl.html
#


import xbmcgui
import xbmcplugin

import urllib
import config

from utils import Logger

def DialogOK(line1, line2='', line3=''):
    d = xbmcgui.Dialog()
    #d.ok(TITLE + ' - ' + VERSION, line1, line2 , line3)
    Logger.log("Dialog:%s %s %s" % (line1, line2 , line3), Logger.LOG_DEBUG)
    d.ok(config.TITLE, line1, line2 , line3)


def ShowBusy():
    busy = None
    try:
        busy = xbmcgui.WindowXMLDialog('DialogBusy.xml', '')
        busy.show()

        try:    busy.getControl(10).setVisible(False)
        except: pass
    except:
        busy = None

    return busy

def ShowSettings():
    config.ADDON.openSettings()


def addDir(args, label, mode, abrv='', thumbnail='', server='', isFolder=True, countryName = ''):
    #if thumbnail=''
    #    thumbnail = ICON


    u  = args[0]
    u += '?mode='     + str(mode)
    u += '&label='    + urllib.quote_plus(label)
    u += '&abrv='     + urllib.quote_plus(abrv)
    u += '&server='   + urllib.quote_plus(server)
    u += '&country='   + urllib.quote_plus(countryName)

    liz = xbmcgui.ListItem(label, iconImage=thumbnail, thumbnailImage=thumbnail)

    #liz.setProperty('Fanart_Image', FANART)

    xbmcplugin.addDirectoryItem(handle=int(args[1]), url=u, listitem=liz, isFolder=isFolder)