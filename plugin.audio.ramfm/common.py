#
#      Copyright (C) 2013 Sean Poyser
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

#import urllib
import geturllib
import os
import xbmc
import xbmcaddon

ADDONID = 'plugin.audio.ramfm'

geturllib.SetCacheDir(os.path.join(xbmc.translatePath(xbmcaddon.Addon(ADDONID).getAddonInfo('profile')).decode('utf-8'), 'cache'))


def GetHTML(url, useCache = True, referer=None):
    if useCache:
        html = geturllib.GetURL(url, 1800, referer=referer)
    else:
        html = geturllib.GetURLNoCache(url, referer=referer)

    html  = html.replace('\n', '')
    return html