#   Copyright (C) 2021 Lunatixz
#
#
# This file is part of HDHomerun Simple
#
# HDHomerun Simple is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# HDHomerun Simple is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with HDHomerun Simple. If not, see <http://www.gnu.org/licenses/>.

# -*- coding: utf-8 -*-
"""PseudoTV Live / IPTV Manager Integration module"""
import os, re, json
from kodi_six import xbmc, xbmcaddon, xbmcgui

# Plugin Info
ADDON_ID      = 'plugin.video.hdhomerun.simple'
PROP_KEY      = 'PseudoTV_Recommended.%s'%(ADDON_ID)
REAL_SETTINGS = xbmcaddon.Addon(id=ADDON_ID)
ADDON_NAME    = REAL_SETTINGS.getAddonInfo('name')
ADDON_PATH    = REAL_SETTINGS.getAddonInfo('path')
ADDON_VERSION = REAL_SETTINGS.getAddonInfo('version')
ICON          = REAL_SETTINGS.getAddonInfo('icon')
LOGO          = os.path.join('special://home/addons/%s/'%(ADDON_ID),'resources','images','logo.png')
LANGUAGE      = REAL_SETTINGS.getLocalizedString
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
            try:    asset = json.loads(xbmcgui.Window(10000).getProperty(PROP_KEY))
            except: asset = {}
            asset['vod'] = [{'type':'vod','name':'HDHomerun %s'%(LANGUAGE(30111)),'description':'','icon':LOGO,'path':'plugin://%s/recordings/All'%(ADDON_ID),'id':ADDON_ID}]
        
            if xbmc.getCondVisibility('System.HasAddon(service.iptv.manager)'):
                if REAL_SETTINGS.getSettingBool('iptv.enabled'):
                    WAIT_TIME = 900
                    try: # Manager Info
                        IPTV_MANAGER = xbmcaddon.Addon(id='service.iptv.manager')
                        IPTV_PATH    = IPTV_MANAGER.getAddonInfo('profile')
                        IPTV_M3U     = os.path.join(IPTV_PATH,'playlist.m3u8')
                        IPTV_XMLTV   = os.path.join(IPTV_PATH,'epg.xml')
                        asset['iptv'] = {'type':'iptv','name':ADDON_NAME,'icon':ICON.replace(ADDON_PATH,'special://home/addons/%s/'%(ADDON_ID)).replace('\\','/'),'m3u':{'path':IPTV_M3U,'slug':'@%s'%(slugify(ADDON_NAME))},'xmltv':{'path':IPTV_XMLTV},'id':ADDON_ID}
                    except Exception as e:
                        asset['iptv'] = {}
                        xbmc.log('%s-%s-regPseudoTV failed! %s'%(ADDON_ID,ADDON_VERSION,e),xbmc.LOGERROR)
                else: 
                    asset['iptv'] = {}
                    
            xbmcgui.Window(10000).setProperty(PROP_KEY, json.dumps(asset))
        else:
            xbmcgui.Window(10000).clearProperty(PROP_KEY)
                    
        if MONITOR.waitForAbort(WAIT_TIME): break
        
if __name__ == '__main__': regPseudoTV()