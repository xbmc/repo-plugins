#   Copyright (C) 2021 Lunatixz
#
#
# This file is part of PlutoTV.
#
# PlutoTV is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# PlutoTV is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with PlutoTV.  If not, see <http://www.gnu.org/licenses/>.

# -*- coding: utf-8 -*-

"""PseudoTV Live / IPTV Manager Integration module"""
import os, re, json
from simplecache import use_cache, SimpleCache
from kodi_six    import xbmc, xbmcaddon, xbmcgui, xbmcvfs

# Plugin Info
ADDON_ID      = 'plugin.video.plutotv'
PROP_KEY      = 'PseudoTV_Recommended.%s'%(ADDON_ID)
REAL_SETTINGS = xbmcaddon.Addon(id=ADDON_ID)
ADDON_NAME    = REAL_SETTINGS.getAddonInfo('name')
ADDON_PATH    = REAL_SETTINGS.getAddonInfo('path')
ADDON_VERSION = REAL_SETTINGS.getAddonInfo('version')
ICON          = REAL_SETTINGS.getAddonInfo('icon')
MONITOR       = xbmc.Monitor()
LOGO          = os.path.join('special://home/addons/%s/'%(ADDON_ID),'resources','images','logo.png')

def slugify(text):
    non_url_safe = [' ','"', '#', '$', '%', '&', '+',',', '/', ':', ';', '=', '?','@', '[', '\\', ']', '^', '`','{', '|', '}', '~', "'"]
    non_url_safe_regex = re.compile(r'[{}]'.format(''.join(re.escape(x) for x in non_url_safe)))
    text = non_url_safe_regex.sub('', text).strip()
    text = u'_'.join(re.split(r'\s+', text))
    return text

def load(text):
    try:    return json.loads(text)
    except: return {} 
    
class regPseudoTV:
    def __init__(self):
        self.cache = SimpleCache()
        

    @use_cache(1)
    def getDirs(self, path, version):
        json_query = '{"jsonrpc":"2.0","method":"Files.GetDirectory","params":{"directory":"%s","properties":["file","art"]},"id":1}'%(path)
        return xbmc.executeJSONRPC(json_query)

    
    def run(self):
        def buildVOD():
            items = load(self.getDirs('plugin://%s/ondemand'%(ADDON_ID),ADDON_VERSION)).get('result',{}).get('files',[])
            asset['vod'] = []
            for item in items:
                if item.get('filetype') == 'directory':
                    label = '%s (%s)'%(item.get('label'),ADDON_NAME)
                    plot  = (item.get("plot","") or item.get("plotoutline","") or item.get("description",""))
                    icon  = (item.get('art',{}).get('logo','') or item.get('art',{}).get('thumb','') or LOGO)
                    asset['vod'].append({'type':'vod','name':label,'description':plot,'icon':icon,'path':item.get('file'),'id':ADDON_ID})
            
        while not MONITOR.abortRequested():
            WAIT_TIME = 60
            if (xbmc.getCondVisibility('System.HasAddon(service.iptv.manager)') and xbmc.getCondVisibility('System.HasAddon(plugin.video.pseudotv.live)')):
                try:
                    # Manager Info
                    IPTV_MANAGER = xbmcaddon.Addon(id='service.iptv.manager')
                    IPTV_PATH    = IPTV_MANAGER.getAddonInfo('profile')
                    IPTV_M3U     = os.path.join(IPTV_PATH,'playlist.m3u8')
                    IPTV_XMLTV   = os.path.join(IPTV_PATH,'epg.xml')
                except Exception as e:
                    xbmc.log('%s-%s-regPseudoTV failed! %s'%(ADDON_ID,ADDON_VERSION,e),xbmc.LOGERROR)
                    break
                
                if REAL_SETTINGS.getSettingBool('iptv.enabled'):
                    asset = {'iptv':{'type':'iptv','name':ADDON_NAME,'icon':ICON.replace(ADDON_PATH,'special://home/addons/%s/'%(ADDON_ID)).replace('\\','/'),'m3u':{'path':IPTV_M3U,'slug':'@%s'%(slugify(ADDON_NAME))},'xmltv':{'path':IPTV_XMLTV},'id':ADDON_ID}}
                    buildVOD()
                    xbmcgui.Window(10000).setProperty(PROP_KEY, json.dumps(asset))
                    WAIT_TIME = 900
                else:
                    xbmcgui.Window(10000).clearProperty(PROP_KEY)
                    WAIT_TIME = 300
            if MONITOR.waitForAbort(WAIT_TIME): break
        
if __name__ == '__main__': regPseudoTV().run()