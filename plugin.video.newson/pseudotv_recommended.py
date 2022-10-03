#   Copyright (C) 2021 Lunatixz
#
#
# This file is part of NewsOn.
#
# NewsOn is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# NewsOn is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with NewsOn.  If not, see <http://www.gnu.org/licenses/>.

# -*- coding: utf-8 -*-
"""PseudoTV Live / IPTV Manager Integration module"""
import os, re, json
from kodi_six import xbmc, xbmcaddon, xbmcgui

# Plugin Info
ADDON_ID      = 'plugin.video.newson'
PROP_KEY      = 'PseudoTV_Recommended.%s'%(ADDON_ID)
REAL_SETTINGS = xbmcaddon.Addon(id=ADDON_ID)
ADDON_NAME    = REAL_SETTINGS.getAddonInfo('name')
ADDON_PATH    = REAL_SETTINGS.getAddonInfo('path')
ADDON_VERSION = REAL_SETTINGS.getAddonInfo('version')
ICON          = REAL_SETTINGS.getAddonInfo('icon')
LANGUAGE      = REAL_SETTINGS.getLocalizedString
LOGO          = os.path.join('special://home/addons/%s/'%(ADDON_ID),'resources','images','logo.png')
MONITOR       = xbmc.Monitor()

def slugify(text):
    non_url_safe = [' ','"', '#', '$', '%', '&', '+',',', '/', ':', ';', '=', '?','@', '[', '\\', ']', '^', '`','{', '|', '}', '~', "'"]
    non_url_safe_regex = re.compile(r'[{}]'.format(''.join(re.escape(x) for x in non_url_safe)))
    text = non_url_safe_regex.sub('', text).strip()
    text = u'_'.join(re.split(r'\s+', text))
    return text

def regPseudoTV():
    while not MONITOR.abortRequested():
        WAIT_TIME = 300
        
        if xbmc.getCondVisibility('System.HasAddon(plugin.video.pseudotv.live)'):
            WAIT_TIME = 900
            asset = {'vod':[{'type':'vod','name':'%s (%s)'%(LANGUAGE(30006),ADDON_NAME),'description':LANGUAGE(30002),'icon':LOGO,'path':'plugin://plugin.video.newson/local','id':ADDON_ID}]}
            xbmcgui.Window(10000).setProperty(PROP_KEY, json.dumps(asset))
        else:
            xbmcgui.Window(10000).clearProperty(PROP_KEY)
            
        if MONITOR.waitForAbort(WAIT_TIME): break
        
if __name__ == '__main__': regPseudoTV()