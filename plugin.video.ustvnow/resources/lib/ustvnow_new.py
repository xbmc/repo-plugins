'''
    ustvnow XBMC Plugin
    Copyright (C) 2015 t0mm0, jwdempsey, esxbr, Lunatixz, yrabl

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
import sys, os, re
import urllib, urllib2, socket, cookielib
import simplejson as json
import xbmcgui, xbmc, xbmcvfs
import Addon
import time, datetime, calendar

from xml.dom import minidom
from time import time
from datetime import datetime, timedelta

# Commoncache plugin import
try:
    import StorageServer
except Exception,e:
    import storageserverdummy as StorageServer

socket.setdefaulttimeout(30)

class Ustvnow:
    def __init__(self, user, password, premium):
        Addon.log('__init__')
        self.dlg = xbmcgui.Dialog()
        self.mBASE_URL = 'http://m.ustvnow.com'
        self.uBASE_URL = 'http://lv2.ustvnow.com';
        # self.uBASE_URL = 'http://lv5.ustvnow.com';
        # self.uBASE_URL = 'http://lv7.ustvnow.com';
        # self.uBASE_URL = 'http://lv9.ustvnow.com';
        self.user = user
        self.password = password
        self.premium = premium
        self.write_type = int(Addon.get_setting('write_type'))     
        self.LIVETV     = self.mBASE_URL + '/iphone/1/live/playingnow?pgonly=true&token=%s'
        self.RECORDINGS = self.mBASE_URL + '/iphone/1/dvr/viewdvrlist?pgonly=true&token=%s'
        try:   
            self.cache = StorageServer.StorageServer("plugin://plugin.video.ustvnow/" + "cache",.5)
            self.cache_token  = StorageServer.StorageServer("plugin://plugin.video.ustvnow/" + "self.cache_token",.5)
            self.cache_guide  = StorageServer.StorageServer("plugin://plugin.video.ustvnow/" + "guide",4)
        except:
            pass
            
    def get_tvguide(self, filename, type='channels', name=''):
        Addon.log('get_tvguide,' + type + ',' + name)
        return Addon.readXMLTV(filename, type, name)
        
        
    def get_channels(self, quality, stream_type):
        Addon.log('get_channels')
        try:
            result = self.cache_guide.cacheFunction(self.get_channels_NEW, quality, stream_type)
            if not result:
                raise Exception()
        except:
            result = self.get_channels_NEW(quality, stream_type)
        if not result:
            result = [({
                'name': 'USTVnow is temporarily unavailable, Try again...',
                'sname' : 'callsign',
                'url': 'url',
                'icon': 'img'
                })]
        return result  
        
        
    def get_channels_NEW(self, quality, stream_type):
        Addon.log('get_channels_NEW,' + str(quality) + ',' + stream_type)
        self.token = self._login()
        content = self._get_json('gtv/1/live/channelguide', {'token': self.token,'format': stream_type, 'l': '1'})
        channels = []
        results = content['results'];
        for i in results:
            try:
                if i['order'] == 1:
                    name = Addon.cleanChanName(i['stream_code'])
                    url = "plugin://plugin.video.ustvnow/?name="+name+"&mode=play"
                    mediatype = i['mediatype']
                    poster_url = 'http://mc.ustvnow.com/gtv/1/live/viewposter?srsid=' + str(i['srsid']) + '&cs=' + i['callsign'] + '&tid=' + mediatype
                    mediatype = mediatype.replace('SH', 'tvshow').replace('EP', 'episode').replace('MV', 'movie')
                    if self.premium == False:
                        if name not in ['CW','ABC','FOX','PBS','CBS','NBC','MY9']:
                            raise Exception()
                    channels.append({
                        'name': name,
                        'sname' : i['callsign'],
                        'url': url,
                        'episode_title': i['episode_title'],
                        'title': i['title'],
                        'plot': i['description'],
                        'plotoutline': i['synopsis'],
                        'mediatype': mediatype,
                        'playable': True,
                        'icon': self.uBASE_URL + '/' + i['img'],
                        'poster_url': poster_url
                        })
                        
                    if self.write_type == 1:
                        Addon.makeSTRM(name, url)
                    self.make_Playlists(quality, stream_type)
            except:
                pass
        return channels

        
    def make_Playlists(self, quality, stream_type):
        Addon.log('make_Playlists')
        if self.write_type > 1:
            Addon.makeM3U(self.get_link(quality, stream_type))

            
    def set_favorites(self, channel):
        Addon.log('set_favorites')
        # <div class="ui-block-b"><label><input rel="external" class="updateFavorite" href="/iphone/1/live/updatefavs?prgsvcid=11534&token=bceayjtsg04lmlrknc3h" type="checkbox" id="favcb-11534static" name="favcb-11534static"/>Favorite</label>
            
            
    def get_favorites(self, quality, stream_type):
        Addon.log('get_favorites')
        self.token = self._login()
        FAVORITES  = self._get_html('iphone/1/live/showfavs', {'token': self.token, 'l': '1440'})
        # content = self._get_json('gtv/1/live/listchannels', {'token': self.token, 'l': '1440'})
        # channels = []
        # results = content['results']['streamnames'];
        # print results

        # for i in range(len(results)):
            # name = Addon.cleanChanName(results[i]['sname'])
            # id = results[i]['prgsvcid']
            # free = results[i]['t'] == 1 # free sub switch 1=free, 0=pay
            # print name, id, fav

          
            # url = "plugin://plugin.video.ustvnow/?name="+i['sname']+"&mode=play"
            # name = Addon.cleanChanName(i['sname'])
            # channels.append({
                # 'name': name,
                # 'sname' : i['callsign'],
                # 'url': url, 
                # 'icon': self.uBASE_URL + '/' + i['img']
                # })  
        # return channels

    
    def get_recordings(self, quality, stream_type, type='recordings'):
        if quality == 3:
            quality -= 1
        Addon.log('get_recordings,' + str(quality) + ',' + stream_type)
        self.token = self._login()
        content = self._get_json('gtv/1/live/viewdvrlist', {'token': self.token, 'format': stream_type})
        recordings = []
        scheduled = []
        now = datetime.now();
        results = content['results'];
        for i in results:
            start_time = datetime.fromtimestamp(float(i['ut_start']));
            chan = Addon.cleanChanName(i['callsign'])
            icon = 'http://mc.ustvnow.com/gtv/1/live/viewposter?srsid=' + str(i['srsid']) + '&cs=' + i['callsign'] + '&tid=SH'
            title = i['title']
            plot = i['description']
            orig_air_date = i['orig_air_date']
            rec_date = i['recordedonmmddyyyy']
            synopsis = i['synopsis']
            duration = i['runtime']
            episode_title = i['episode_title']
            url = stream_type + '://' + i['dvrlocation'] + '.ustvnow.com:1935/' + i['app_name'] + '/mp4:' + [i['filename_low'], i['filename_med'], i['filename_high']][quality]
            del_url = 'iphone_ajax?tab=updatedvr&scheduleid=' + str(i['scheduleid']) + '&token=' + self.token + '&action=remove'
            if (type == 'recordings' and (now > start_time)):
                recordings.append({'channel': chan,
                                   'stream_url': url,

                                   'title': title,
                                   'episode_title': episode_title,
                                   'tvshowtitle': title,

                                   'plot': plot,
                                   'rec_date': rec_date,

                                   'icon': icon,
                                   'duration': duration,
                                   'orig_air_date': orig_air_date,
                                   'synopsis': synopsis,
                                   'playable': (now > start_time),
                                   'del_url': del_url

                                   })
            elif (type == 'scheduled' and (now < start_time)):
                scheduled.append({'channel': chan,
                                   'stream_url': url,
                                   'title': title,
                                   'episode_title': episode_title,
                                   'tvshowtitle': title,
                                   'plot': plot,
                                   'rec_date': rec_date,
                                   'icon': icon,
                                   'duration': duration,
                                   'orig_air_date': orig_air_date,
                                   'synopsis': synopsis,
                                   'playable': (now > start_time),
                                   'del_url': del_url
                                   })
        if (type == 'recordings'):
            return recordings
        elif (type == 'scheduled'):
            return scheduled
        else:
            return []

            
    def delete_recording(self, del_url):
        html = self._get_html(del_url)
        

    def get_guidedata(self, quality, stream_type):
        Addon.log('get_guidedata')
        try:
            result = self.cache_guide.cacheFunction(self.get_guidedata_NEW, quality, stream_type)
            if not result:
                raise Exception()              
        except:
            Addon.log('get_guidedata Failed')
            result = self.get_guidedata_NEW(quality, stream_type)
        if not result:
            result = []
        return result  

        
    def get_guidedata_NEW(self, quality, stream_type):
        Addon.log('get_guidedata_NEW')
        self.token = self._login()
        content = self._get_json('gtv/1/live/channelguide', {'token': self.token, 'l': '1440'})
        results = content['results'];
        now = time();
        doc = minidom.Document();
        base = doc.createElement('tv');
        base.setAttribute("cache-version", str(now));
        base.setAttribute("cache-time", str(now));
        base.setAttribute("generator-info-name", "IPTV Plugin");
        base.setAttribute("generator-info-url", "http://www.xmltv.org/");
        doc.appendChild(base)
        channels = self.get_channels(quality, stream_type);

        for channel in channels:
            name = channel['name'];
            id = channel['sname'];
            c_entry = doc.createElement('channel');
            c_entry.setAttribute("id", id);
            base.appendChild(c_entry)
            dn_entry = doc.createElement('display-name');
            dn_entry_content = doc.createTextNode(Addon.cleanChanName(name));
            dn_entry.appendChild(dn_entry_content);
            c_entry.appendChild(dn_entry);
            dn_entry = doc.createElement('display-name');
            dn_entry_content = doc.createTextNode(Addon.cleanChanName(id));
            dn_entry.appendChild(dn_entry_content);
            c_entry.appendChild(dn_entry);
            icon_entry = doc.createElement('icon');
            icon_entry.setAttribute("src", channel['icon']);
            c_entry.appendChild(icon_entry);

        for programme in results:
            start_time 	= datetime.fromtimestamp(float(programme['ut_start']));
            stop_time	= start_time + timedelta(seconds=int(programme['guideremainingtime']));
            
            pg_entry = doc.createElement('programme');
            pg_entry.setAttribute("start", start_time.strftime('%Y%m%d%H%M%S 0'));
            pg_entry.setAttribute("stop", stop_time.strftime('%Y%m%d%H%M%S 0'));
            pg_entry.setAttribute("channel", programme['callsign']);
            base.appendChild(pg_entry);
            
            t_entry = doc.createElement('title');
            t_entry.setAttribute("lang", "en");
            t_entry_content = doc.createTextNode(programme['title']);
            t_entry.appendChild(t_entry_content);
            pg_entry.appendChild(t_entry);
            
            st_entry = doc.createElement('sub-title');
            st_entry.setAttribute("lang", "en");
            st_entry_content = doc.createTextNode(programme['episode_title']);
            st_entry.appendChild(st_entry_content);
            pg_entry.appendChild(st_entry);

            d_entry = doc.createElement('desc');
            d_entry.setAttribute("lang", "en");
            d_entry_content = doc.createTextNode(programme['description']);
            d_entry.appendChild(d_entry_content);
            pg_entry.appendChild(d_entry);

            dt_entry = doc.createElement('date');
            dt_entry_content = doc.createTextNode(start_time.strftime('%Y%m%d'));
            dt_entry.appendChild(dt_entry_content);
            pg_entry.appendChild(dt_entry);

            c_entry = doc.createElement('category');
            c_entry_content = doc.createTextNode(programme['xcdrappname']);
            c_entry.appendChild(c_entry_content);
            pg_entry.appendChild(c_entry);
            d_entry = doc.createElement('length');
            d_entry.setAttribute("units", "seconds");
            d_entry_content = doc.createTextNode(str(programme['actualremainingtime']));
            d_entry.appendChild(d_entry_content);
            pg_entry.appendChild(d_entry);
            en_entry = doc.createElement('episode-num');
            en_entry.setAttribute('system', 'dd_progid');
            en_entry_content = doc.createTextNode(programme['content_id']);
            en_entry.appendChild(en_entry_content);
            pg_entry.appendChild(en_entry);

            i_entry = doc.createElement('icon');
            i_entry.setAttribute("src", 'http://mc.ustvnow.com/gtv/1/live/viewposter?srsid=' + str(programme['srsid']) + '&cs=' + programme['callsign'] + '&tid=' + programme['mediatype']);
            pg_entry.appendChild(i_entry);
        return doc


    def _build_url(self, path, queries={}):
        Addon.log('_build_url')
        if queries:
            query = Addon.build_query(queries)
            return '%s/%s?%s' % (self.uBASE_URL, path, query)
        else:
            return '%s/%s' % (self.uBASE_URL, path)
            
            
    def _login_url(self, path, queries={}):
        Addon.log('_login_url')
        if queries:
            query = urllib.urlencode(queries)
            return '%s/%s?%s' % (self.uBASE_URL, path, query)
        else:
            return '%s/%s' % (self.uBASE_URL, path)
            
            
    def _build_json(self, path, queries={}):
        Addon.log('_build_json')
        if queries:
            query = urllib.urlencode(queries)
            return '%s/%s?%s' % (self.mBASE_URL, path, query)
        else:
            return '%s/%s' % (self.mBASE_URL, path)

            
    def _fetch(self, url, form_data=False):
        Addon.log('_fetch')
        if form_data:
            req = urllib2.Request(url, form_data)
        else:
            req = url
        try:
            response = urllib2.urlopen(req)
            return response
        except urllib2.URLError, e:
            return False

            
    def _get_json(self, path, queries={}):
        Addon.log('_get_json')
        content = False
        url = self._build_json(path, queries)
        response = self._fetch(url)
        if response:
            content = json.loads(response.read())
        else:
            content = False
        return content

        
    def _get_html(self, path, queries={}):
        Addon.log('_get_html')
        html = False
        url = self._build_url(path, queries)
        # #print url    
        response = self._fetch(url)
        if response:
            html = response.read()
        else:
            html = False
        return html

        
    def get_link(self, quality, stream_type):
        Addon.log('get_link')
        try:
            result = self.cache.cacheFunction(self.get_link_NEW, quality, stream_type)
            if not result:
                raise Exception()
        except:
            result = self.get_link_NEW(quality, stream_type)
        if not result:
            result = [({
                'name': 'USTVnow is temporarily unavailable, Try again...',
                'now' : 'N/A',
                'url': 'url',
                'icon': 'img'
                })]
        return result  
        
        
    def get_link_NEW(self, quality, stream_type):
        Addon.log('get_link')
        self.token = self._login(True)
        html = self._get_html('iphone_ajax', {'tab': 'iphone_playingnow', 
                                              'token': self.token})
        channels = []
        achannels = []
        for channel in re.finditer('class="panel".+?title="(.+?)".+?src="' +
                                   '(.+?)".+?class="nowplaying_item">(.+?)' +
                                   '<\/td>.+?class="nowplaying_itemdesc".+?' +
                                   '<\/a>(.+?)<\/td>.+?href="(.+?)"',
                                   html, re.DOTALL):
            name, icon, title, plot, url = channel.groups()
            name = name.replace('\n','').replace('\t','').replace('\r','').replace('<fieldset> ','').replace('<div class=','').replace('>','').replace('"','').replace(' ','')
            if not name:
                name = ((icon.rsplit('/',1)[1]).replace('.png','')).upper()
                name = Addon.cleanChanName(name)
            try:
                if not url.startswith('http'):
                    now = {'title': title, 'plot': plot.strip()}
                    url = '%s%s%d' % (stream_type, url[4:-1], quality + 1)
                    aChannelname = {'name': name}
                    aChannel = {'name': name, 'url': url, 
                                'icon': icon, 'now': now}
                    if aChannelname not in achannels:
                       achannels.append(aChannelname)
                       channels.append(aChannel)
            except:
                pass
        return channels
             

    def _login(self, force=False):
        Addon.log('_login')
        result = 'False'
        if force == True:
            try:
                self.cache_token.delete("%")
            except:
                pass
        try:
            result = self.cache_token.cacheFunction(self._login_NEW)
            if result == 'False':
                raise Exception()
        except Exception,e:
            Addon.log('_login, Failed!')
            result = self._login_NEW()
        if result == 'False':
            self.dlg.ok("USTVnow", "Connection FAILED!", "Please check your login credentials and try again later...")
        return result  
        
        
    def _login_NEW(self):
        Addon.log('_login_NEW')
        token = self._login_ORG() 
        if token == 'False':
            token = self._login_ALT()
        return token
        
        
    def _login_ALT(self):
        Addon.log('_login_NEW_ALT')
        try:
            self.cj = cookielib.CookieJar()
            opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(self.cj)) 
            urllib2.install_opener(opener)
            url = self._build_json('gtv/1/live/login', {'username': self.user, 
                                                   'password': self.password, 
                                                   'device':'gtv', 
                                                   'redir':'0'})
            response = opener.open(url)
            for cookie in self.cj:
                if cookie.name == 'token':
                    return cookie.value
        except:
            pass
        return 'False'
    
    
    def _login_ORG(self):
        Addon.log('_login_ORG')
        try:
            self.cj = cookielib.CookieJar()
            opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(self.cj))
            urllib2.install_opener(opener)
            url = self._build_url('iphone_login', {'username': self.user, 
                                                   'password': self.password})
            response = opener.open(url)
            for cookie in self.cj:
                if cookie.name == 'token':
                    return cookie.value
        except:
            pass
        return 'False'

        
    def clearCache(self):
        Addon.log('clearCache')
        try:
            self.cache.delete("%")
            self.guide.delete("%")
            self.token.delete("%")
        except:
            pass