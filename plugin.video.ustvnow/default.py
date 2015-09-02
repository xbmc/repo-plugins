'''
    ustvnow XBMC Plugin
    Copyright (C) 2015 t0mm0, Lunatixz

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

from resources.lib import Addon, ustvnow 
import sys
import urllib
import xbmc, xbmcgui, xbmcplugin

Addon.plugin_url = sys.argv[0]
Addon.plugin_handle = int(sys.argv[1])
Addon.plugin_queries = Addon.parse_query(sys.argv[2][1:])

email = Addon.get_setting('email')
password = Addon.get_setting('password')
premium = Addon.get_setting('subscription') == "true"
dlg = xbmcgui.Dialog()

if not email:
    dlg.ok("USTVnow", "Please visit www.ustvnow.com", "and register for your login credentials")
    retval = dlg.input('Enter USTVnow Account Email', type=xbmcgui.INPUT_ALPHANUM)
    if retval and len(retval) > 0:
        Addon.set_setting('email', str(retval))
        email = Addon.get_setting('email')
    retval = dlg.input('Enter USTVnow Account Password', type=xbmcgui.INPUT_ALPHANUM)
    if retval and len(retval) > 0:
        Addon.set_setting('password', str(retval))
        password = Addon.get_setting('password')
    if dlg.yesno("USTVnow", 'Are you a premium subscriber?'):
        Addon.set_setting('subscription', 'true')
    else:
        Addon.set_setting('subscription', 'false')
        
if premium == False:
    Addon.set_setting('quality', '0')
    
ustv = ustvnow.Ustvnow(email, password, premium)
Addon.log('plugin url: ' + Addon.plugin_url)
Addon.log('plugin queries: ' + str(Addon.plugin_queries))
Addon.log('plugin handle: ' + str(Addon.plugin_handle))
mode = Addon.plugin_queries['mode']

if mode == 'main':
    Addon.log(mode)
    Addon.add_directory({'mode': 'live'}, Addon.get_string(30001))
    if premium == True:
        Addon.add_directory({'mode': 'recordings'}, Addon.get_string(30002))

elif mode == 'live':
    Addon.log(mode)
    stream_type = ['rtmp', 'rtsp'][int(Addon.get_setting('stream_type'))]
    channels = ustv.get_channels(int(Addon.get_setting('quality')), 
                                     stream_type)
    if channels:
        for c in channels:
            rURL = "plugin://plugin.video.ustvnow/?name="+c['name']+"&mode=play"
            item = xbmcgui.ListItem(path=rURL)
            Addon.add_video_item(rURL,
                                 {'title': '%s - %s' % (c['name'], 
                                                        c['now']['title']),
                                  'plot': c['now']['plot']},
                                 img=c['icon'])
                             
elif mode == 'recordings':
    Addon.log(mode)
    stream_type = ['rtmp', 'rtsp'][int(Addon.get_setting('stream_type'))]
    recordings = ustv.get_recordings(int(Addon.get_setting('quality')), 
                                     stream_type)
    if recordings:
        for r in recordings:
            cm_del = (Addon.get_string(30003), 
                      'XBMC.RunPlugin(%s/?mode=delete&del=%s)' % 
                           (Addon.plugin_url, urllib.quote(r['del_url'])))
            title = '%s (%s on %s)' % (r['title'], r['rec_date'], r['channel'])
            Addon.add_video_item(r['stream_url'], {'title': title, 
                                                   'plot': r['plot']},
                                 img=r['icon'], cm=[cm_del], cm_replace=True)

elif mode == 'delete':
    dialog = xbmcgui.Dialog()
    ret = dialog.yesno(Addon.get_string(30000), Addon.get_string(30004), 
                       Addon.get_string(30005))
    if ret == 1:
        ustv.delete_recording(Addon.plugin_queries['del'])

elif mode=='play':
    name = Addon.plugin_queries['name']
    try:
       stream_type = 'rtmp'
       channels = []
       quality = int(Addon.get_setting('quality'))
       channels = ustv.get_channels(quality,stream_type)
       for c in channels:
         if c['name'] == name:
           print "setResolvedUrl"
           item = xbmcgui.ListItem(path=c['url'])
           xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)
    except:
        pass

Addon.end_of_directory()