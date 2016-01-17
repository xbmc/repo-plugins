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

import sys, os, urllib
import xbmc, xbmcgui, xbmcplugin, xbmcaddon

from resources.lib import Addon
from resources.lib import ustvnow_new

Addon.plugin_url = sys.argv[0]
Addon.plugin_handle = int(sys.argv[1])
Addon.plugin_queries = Addon.parse_query(sys.argv[2][1:])

email = Addon.get_setting('email')
password = Addon.get_setting('password')
premium = Addon.get_setting('subscription') == "true"
premium_last = Addon.get_setting('subscription_last') == "true"

dlg = xbmcgui.Dialog()
plugin_path = xbmcaddon.Addon(id='plugin.video.ustvnow').getAddonInfo('path')
write_path = xbmc.translatePath(Addon.get_setting('write_folder'))

ustv = ustvnow_new.Ustvnow(email, password, premium)

if premium != premium_last:
    ustv.clearCache()
    Addon.set_setting('subscription_last', Addon.get_setting('subscription'))
         
if premium == False:
    Addon.set_setting('quality_type', '0')     

if not email:
    dlg.ok("USTVnow", "Please visit www.ustvnow.com", "to register for login credentials.")
    # Enter Email
    retval = dlg.input('Enter USTVnow Account Email', type=xbmcgui.INPUT_ALPHANUM)
    if retval and len(retval) > 0:
        Addon.set_setting('email', str(retval))
        email = Addon.get_setting('email')
    # Enter Password
    retval = dlg.input('Enter USTVnow Account Password', type=xbmcgui.INPUT_ALPHANUM)
    if retval and len(retval) > 0:
        Addon.set_setting('password', str(retval))
        password = Addon.get_setting('password')
    # Subscription type
    if dlg.yesno("USTVnow", 'Are you a Premium Subscriber?'):
        Addon.set_setting('subscription', 'true')
    else:
        Addon.set_setting('subscription', 'false')
    
quality_type = int(Addon.get_setting('quality_type'))
stream_type = ['rtmp', 'rtsp'][int(Addon.get_setting('stream_type'))]
    
Addon.log('plugin url: ' + Addon.plugin_url)
Addon.log('plugin queries: ' + str(Addon.plugin_queries))
Addon.log('plugin handle: ' + str(Addon.plugin_handle))
mode = Addon.plugin_queries['mode']
Addon.log(mode)

if mode == 'main':
    Addon.add_directory({'mode': 'live'}, Addon.get_string(30001))
    # Addon.add_directory({'mode': 'favorites'}, Addon.get_string(30006))
    Addon.add_directory({'mode': 'tvguide'}, Addon.get_string(30007))
    Addon.add_directory({'mode': 'scheduled'}, Addon.get_string(30111))
    Addon.add_directory({'mode': 'recordings'}, Addon.get_string(30002))

elif mode == 'live':
    channels = ustv.get_channels_NEW(quality_type, stream_type)
    if channels:
        for c in channels:
            rURL = "plugin://plugin.video.ustvnow/?name="+c['name']+"&mode=play"
            logo = xbmc.translatePath(os.path.join(plugin_path, 'resources', 'images', c['name']+'.png'))
            item = xbmcgui.ListItem(path=rURL)
            name = c["name"];
            sname = c["sname"];
            icon = c["icon"];
            poster_url = c["poster_url"];
            episode_title = c["episode_title"];
            title = c["title"];
            plot = c["plot"];
            plotoutline = c["plotoutline"];
            mediatype = c["mediatype"];
            if mediatype != "movie":
                tvshowtitle = title
            if episode_title != "":
                title = '%s - %s - %s' % (name, (title).replace('&amp;','&').replace('&quot;','"'), (episode_title).replace('&amp;','&').replace('&quot;','"'))
            else:
                title = '%s - %s' % (name, (title).replace('&amp;','&').replace('&quot;','"'))
            for quality in range(1,4):
                parameters = urllib.urlencode( {
                    'c': sname,
                    'i': icon,
                    'q': str(quality),
                    'u': email,
                    'p': password } );
                    
                if quality==1:
                    quality_name = 'Low';
                elif quality==2:
                    quality_name = 'Medium';
                else:
                    quality_name = 'High';
                    
            Addon.add_video_item(rURL,
            
                                 {'title': title,
                                 'plot': plot,
                                 'mediatype': mediatype,
                                 'plotoutline': plotoutline},
                                 img=logo, fanart=poster_url, HD=quality_name, playable=c['playable'])
            xbmcplugin.setContent(Addon.plugin_handle, 'episodes')
                             
elif mode == 'recordings':
    stream_type = ['rtmp', 'rtsp'][int(Addon.get_setting('stream_type'))]
    recordings = ustv.get_recordings(quality_type, stream_type, 'recordings')
        
    if recordings:
        for r in recordings:
            cm_del = (Addon.get_string(30003), 
                      'XBMC.RunPlugin(%s/?mode=delete&del=%s)' % 
                           (Addon.plugin_url, urllib.quote(r['del_url'])))
            title = '%s - %s (%s on %s)' % (r['title'], r['episode_title'], r['rec_date'], r['channel'])
            if quality_type==3:
                quality_name = 'High';
            elif quality_type==2:
                quality_name = 'High';
            elif quality_type==1:
                quality_name = 'Medium';
            else:
                quality_name = 'Low';
            Addon.add_video_item(r['stream_url'], {'title': title, 
                                                   'plot': r['plot'],
                                                   'plotoutline': r['synopsis'],
                                                   'tvshowtitle': r['tvshowtitle'],
                                                   'duration': r['duration'],
                                                   'aired': r['orig_air_date'],
                                                   'dateadded': r['rec_date']},
                                 img=r['icon'], cm=[cm_del], cm_replace=True, HD=quality_name, playable=r['playable'])
        xbmcplugin.setContent(Addon.plugin_handle, 'episodes')
        
elif mode == 'scheduled':
    stream_type = ['rtmp', 'rtsp'][int(Addon.get_setting('stream_type'))]
    scheduled = ustv.get_recordings(quality_type, 
                                 stream_type, 'scheduled')
    if scheduled:
        for r in scheduled:
            #print r
            cm_del = (Addon.get_string(30003), 
                      'XBMC.RunPlugin(%s/?mode=delete&del=%s)' % 
                           (Addon.plugin_url, urllib.quote(r['del_url'])))
            title = '%s - %s (%s on %s)' % (r['title'], r['episode_title'], r['rec_date'], r['channel'])
            if quality_type==3:
                quality_name = 'High';
            elif quality_type==2:
                quality_name = 'High';
            elif quality_type==1:
                quality_name = 'Medium';
            else:
                quality_name = 'Low';
            Addon.add_video_item(r['stream_url'], {'title': title, 
                                                   'plot': r['plot'],
                                                   'plotoutline': r['synopsis'],
                                                   'tvshowtitle': r['tvshowtitle'],
                                                   'duration': r['duration'],
                                                   'aired': r['orig_air_date'],
                                                   'dateadded': r['rec_date']},
                                 img=r['icon'], cm=[cm_del], cm_replace=True, HD=quality_name, playable=False)
        xbmcplugin.setContent(Addon.plugin_handle, 'episodes')
        
elif mode == 'delete':
    dialog = xbmcgui.Dialog()
    ret = dialog.yesno(Addon.get_string(30000), Addon.get_string(30004), 
                       Addon.get_string(30005))
    if ret == 1:
        ustv.delete_recording(Addon.plugin_queries['del'])

elif mode == 'favorites':
    favorites = ustv.get_favorites(quality_type, stream_type)
    
elif mode == 'guidedata':
    # ex. xbmc.executebuiltin("XBMC.RunPlugin(plugin://plugin.video.ustvnow/?file=%s&mode=guidedata)" %urllib.quote(fpath))
    fpath = Addon.plugin_queries['file']               
    Addon.makeXMLTV(ustv.get_guidedata(quality_type, stream_type),urllib.unquote(fpath))
    
elif mode == 'playlist':
    ustv.get_channels(quality_type, stream_type)
    Addon.makeXMLTV(ustv.get_guidedata(quality_type, stream_type),urllib.unquote(os.path.join(write_path, 'xmltv.xml')))    
    
elif mode == 'tvguide':  
    fpath = os.path.join(write_path, 'xmltv.xml')  
    try:
        name = Addon.plugin_queries['name']
        listings = ustv.get_tvguide(fpath, 'programs', name)
        if listings:
            for l in range(len(listings)):
                rURL = "plugin://plugin.video.ustvnow/?name="+listings[l][0]+"&mode=play"
                if listings[l][3] == 'No description available':
                    title = '%s - %s' % (listings[l][1], (listings[l][2]).replace('&amp;','&'))
                else:
                    title = '%s - %s - %s' % (listings[l][1], (listings[l][2]).replace('&amp;','&'), (listings[l][3]).replace('&amp;','&').replace('&quot;','"'))
                Addon.add_video_item(rURL,
                                     {'title': title,
                                      'Plot': listings[l][4],
                                      'TVShowTitle': (listings[l][2]).replace('&amp;','&'),
                                      'ChannelName': listings[l][0]},
                                     img=listings[l][6])
    except:
        if Addon.makeXMLTV(ustv.get_guidedata(quality_type, stream_type),urllib.unquote(fpath)) == True:
            listings = ustv.get_tvguide(fpath)
            if listings:
                for l in range(len(listings)):
                    url = "plugin://plugin.video.ustvnow/?name="+listings[l]+"&mode=tvguide"
                    Addon.log('adding dir: %s' % (listings[l]))
                    img = xbmc.translatePath(os.path.join(plugin_path, 'resources', 'images', listings[l])+'.png')
                    fanart = ''
                    listitem = xbmcgui.ListItem(listings[l], iconImage=img, thumbnailImage=img)
                    if not fanart:
                        fanart = plugin_path + '/fanart.jpg'
                    listitem.setProperty('fanart_image', fanart)
                    xbmcplugin.addDirectoryItem(Addon.plugin_handle, url, listitem, 
                                                isFolder=True, totalItems=len(listings))
                    xbmcplugin.setContent(Addon.plugin_handle, 'episodes')
        
elif mode=='play':
    name = Addon.plugin_queries['name']
    Addon.log(name)
    channels = []
    channels = ustv.get_link(quality_type, stream_type)
    if channels:
        Addon.log(str(channels))
        for c in channels:
            if c['name'] == name:
                url = c['url']
                Addon.log(url)
                item = xbmcgui.ListItem(path=url)
                xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)
                
Addon.end_of_directory()