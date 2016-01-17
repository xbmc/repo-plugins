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
import Addon
import cookielib
import os
import re
import urllib, urllib2
import xbmcgui

class Ustvnow:
    __BASE_URL = 'http://lv2.ustvnow.com'
    # __BASE_URL = 'http://lv7.ustvnow.com'
    # __BASE_URL = 'http://lv9.ustvnow.com'
    def __init__(self, user, password, premium):
        self.user = user
        self.password = password
        self.premium = premium
        self.dlg = xbmcgui.Dialog()
        
    def get_channels(self, quality=1, stream_type='rtmp', cache=False):
        if self._login():
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
                #tmp work around till ustvnow stabilizes changes.
                name = name.replace('\n','').replace('\t','').replace('\r','').replace('<fieldset> ','').replace('<div class=','').replace('>','').replace('"','').replace(' ','')
                if not name:
                    name = ((icon.rsplit('/',1)[1]).replace('.png','')).upper()
                    name = name.replace('WLYH','CW').replace('WHTM','ABC').replace('WPMT','FOX').replace('WPSU','PBS').replace('WHP','CBS').replace('WGAL','NBC').replace('WHVLLD','MY9').replace('AETV','AE')
                    name = name.replace('APL','Animal Planet').replace('TOON','Cartoon Network').replace('DSC','Discovery').replace('BRAVO','Bravo').replace('USA','USA Network').replace('SYFY','Syfy').replace('HISTORY','History')
                    name = name.replace('COMEDY','Comedy Central').replace('FOOD','Food Network').replace('NIK','Nickelodeon').replace('LIFE','Lifetime').replace('SPIKETV','Spike').replace('FNC','Fox News').replace('NGC','National Geographic')
                try:
                    if not url.startswith('http'):
                        now = {'title': title, 'plot': plot.strip()}
                        url = '%s%s%d' % (stream_type, url[4:-1], quality + 1)
                        aChannelname = {'name': name}
                        aChannel = {'name': name, 'url': url, 
                                    'icon': icon, 'now': now}
                        
                        if self.premium == False:
                            if name not in ['CW','ABC','FOX','PBS','CBS','NBC','MY9']:
                                raise  
                                
                        if aChannelname not in achannels:
                           achannels.append(aChannelname)
                           channels.append(aChannel)
                except:
                    pass

            channels.sort()
            return channels
        else:
            self.dlg.ok("USTVnow", "Connection FAILED!", "Please check your login credentials and try again later...")

    def get_recordings(self, quality=1, stream_type='rtmp'):
        if self._login():
            html = self._get_html('iphone_ajax', {'tab': 'iphone_viewdvrlist'})
            recordings = []
            for r in re.finditer('class="panel".+?title="(.+?)".+?src="(.+?)".+?' +
                                 'class="nowplaying_item">(.+?)<\/td>.+?(?:<\/a>' +
                                 '(.+?)<\/td>.+?)?vertical-align:bottom.+?">(.+?)' +
                                 '<\/div>.+?_self" href="(rtsp.+?)".+?href="(.+?)"', 
                                 html, re.DOTALL):
                chan, icon, title, plot, rec_date, url, del_url = r.groups()
                url = '%s%s%s' % (stream_type, url[4:-7], 
                                  ['350', '650', '950'][quality])
                if plot:
                    plot = plot.strip()
                else:
                    plot = ''
                recordings.append({'channel': chan,
                   'stream_url': url,

                   'title': title,
                   'episode_title': '',
                   'tvshowtitle': title,

                   'plot': plot,
                   'rec_date': rec_date.strip(),

                   'icon': icon,
                   'duration': 0,
                   'orig_air_date': '',
                   'synopsis': '',
                   'playable': (0),
                   'del_url': del_url

                   })
            return recordings
        else:
            self.dlg.ok("USTVnow", "Connection FAILED!", "Please check your login credentials and try again later...")
    
    def delete_recording(self, del_url):
        html = self._get_html(del_url)
    
    def _build_url(self, path, queries={}):
        if queries:
            query = Addon.build_query(queries)
            url = '%s/%s?%s' % (self.__BASE_URL, path, query)
        else:
            url = '%s/%s' % (self.__BASE_URL, path)
        print url
        return url

    def _fetch(self, url, form_data=False):
        if form_data:
            # Addon.log('posting: %s %s' % (url, str(form_data)))
            req = urllib2.Request(url, form_data)
        else:
            # Addon.log('getting: ' + url)
            req = url
        try:
            response = urllib2.urlopen(url)
            return response
        except urllib2.URLError, e:
            Addon.log(str(e), True)
            return False
        
    def _get_html(self, path, queries={}):
        html = False
        url = self._build_url(path, queries)
        response = self._fetch(url)
        if response:
            html = response.read()
        else:
            html = False
        return html

    def _login(self):
        Addon.log('logging in') 
        self.token = None
        self.cj = cookielib.CookieJar()
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(self.cj))
        urllib2.install_opener(opener)
        url = self._build_url('iphone_login', {'username': self.user, 
                                               'password': self.password})
        response = self._fetch(url)
        for cookie in self.cj:
            # print '%s: %s' % (cookie.name, cookie.value)
            if cookie.name == 'token':
                self.token = cookie.value
                return True
        return False