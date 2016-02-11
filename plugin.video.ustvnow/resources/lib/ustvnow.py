'''
    USTVnow Add-on
    
    This version of USTVnow has been built by combining the best of all
    available version of USTVnow found online. This version has been streamlined 
    to use the USTVnow API directly to avoid many of the issues in previous versions.

    The following developers have all contributed to this version directly or indirectly.

    mhancoc7, t0mm0, jwdempsey, esxbr, Lunatixz, yrabl, ddurdle

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
import json
import xbmcgui, xbmc, xbmcvfs
import Addon

import time, datetime

from xml.dom import minidom
from time import time
from datetime import datetime, timedelta

class Ustvnow:

    def __init__(self, user, password):
        self.user = user
        self.password = password
        self.dlg = xbmcgui.Dialog()
        self.mBASE_URL = 'http://m-api.ustvnow.com'

    def build_main(self):
        mode = Addon.plugin_queries['mode']
        Addon.add_directory({'mode': 'live'}, Addon.get_string(30001))
        if Addon.get_setting('show_tv_guide') == 'true':
            Addon.add_directory({'mode': 'tvguide'}, Addon.get_string(40005))
        if Addon.get_setting('show_movies_section') == 'true':
            Addon.add_directory({'mode': 'movies_now'}, Addon.get_string(20006))
            Addon.add_directory({'mode': 'movies_today'}, Addon.get_string(20007))
            Addon.add_directory({'mode': 'movies_later'}, Addon.get_string(20008))
        if Addon.get_setting('show_sports_section') == 'true':
            Addon.add_directory({'mode': 'sports_now'},  Addon.get_string(30028))
            Addon.add_directory({'mode': 'sports_today'},  Addon.get_string(30029))
            Addon.add_directory({'mode': 'sports_later'},  Addon.get_string(30030))
        if Addon.get_setting('rec_live') == 'true':
            Addon.add_directory({'mode': 'recordings'}, Addon.get_string(30003))
            Addon.add_directory({'mode': 'scheduled'}, Addon.get_string(30012))
        if Addon.get_setting('rec_live') == 'true' and Addon.get_setting('dvr') == 'true':
            Addon.add_directory({'mode': 'recurring'}, Addon.get_string(30006))
        if Addon.get_setting('show_settings_option') == 'true':
            Addon.add_directory({'mode': 'settings'}, Addon.get_string(30002)) 

    def get_channels(self, quality, stream_type):
        Addon.log('get_channels,' + str(quality) + ',' + stream_type)
        token_check = self._get_json('gtv/1/live/getcustomerkey', {'token': Addon.get_setting('token')})['username']
        if token_check != Addon.get_setting('email'):
            self.token = self._login()
        else:
            self.token = Addon.get_setting('token')
        account_type = self._get_json('gtv/1/live/getuserbytoken', {'token': self.token})['data']['plan_free']
        if account_type == 1:
            Addon.set_setting('free_package', 'true')
            if Addon.get_setting('quality') == '3':
                Addon.set_setting('quality', '2')
        else:
            Addon.set_setting('free_package', 'false')
        dvr_check = self._get_json('gtv/1/live/getuserbytoken', {'token': self.token})['data']['plan_name']
        if 'DVR' in dvr_check:
            Addon.set_setting('dvr', 'true')
        else:
            Addon.set_setting('dvr', 'false')
        content = self._get_json('gtv/1/live/channelguide', {'token': self.token})
        channels = []
        results = content['results'];
        for i in results:
            try:
                if i['order'] == 1:
                    from datetime import datetime
                    event_date_time = datetime.fromtimestamp(i['ut_start']).strftime('%I:%M %p').lstrip('0')
                    name = Addon.cleanChanName(i['stream_code'])
                    mediatype = i['mediatype']
                    poster_url = self.mBASE_URL + '/gtv/1/live/viewposter?srsid=' + str(i['srsid']) + '&cs=' + i['callsign'] + '&tid=' + mediatype
                    mediatype = mediatype.replace('SH', 'tvshow').replace('EP', 'episode').replace('MV', 'movie')
                    rec_url = '/gtv/1/dvr/updatedvr?scheduleid=' + str(i['scheduleid']) + '&token=' + self.token + '&action=add'
                    set_url = '/gtv/1/dvr/updatedvrtimer?connectorid=' + str(i['connectorid']) + '&prgsvcid=' + str(i['prgsvcid']) + '&eventtime=' + str(i['event_time']) + '&token=' + self.token + '&action=add'
                    if Addon.get_setting('free_package') == 'true':
                        if name in ['CW','ABC','FOX','PBS','CBS','NBC','MY9']:
                            channels.append({
                                'name': name,
                                'episode_title': i['episode_title'],
                                'title': i['title'],
                                'plot': i['description'],
                                'mediatype': mediatype,
                                'playable': True,
                                'poster_url': poster_url,
                                'rec_url': rec_url,
                                'set_url': set_url,
                                'event_date_time': event_date_time
                                })
                    else:
                        channels.append({
                            'name': name,
                            'episode_title': i['episode_title'],
                            'title': i['title'],
                            'plot': i['description'],
                            'mediatype': mediatype,
                            'playable': True,
                            'poster_url': poster_url,
                            'rec_url': rec_url,
                            'set_url': set_url,
                            'event_date_time': event_date_time
                            })
            except:
                pass
        return channels 

    def get_link(self, quality, stream_type, src):
        Addon.log('get_link,' + str(quality) + ',' + stream_type)
        token_check = self._get_json('gtv/1/live/getcustomerkey', {'token': Addon.get_setting('token')})['username']
        if token_check != Addon.get_setting('email'):
            self.token = self._login()
        else:
            self.token = Addon.get_setting('token')
        content = self._get_json('gtv/1/live/channelguide', {'token': self.token})
        channels = []
        results = content['results'];
        passkey = self._get_json('gtv/1/live/viewdvrlist', {'token': self.token})['globalparams']['passkey']
        quality = (quality + 1)
        for i in results:
            try:
                if i['order'] == 1:
                    name = Addon.cleanChanName(i['stream_code'])
                    url = stream_type + '://' + str(src) + '.ustvnow.com:1935/dvrtest?key=' + passkey + '/mp4:' + i['streamname'] + str(quality)
                    if Addon.get_setting('free_package') == 'true':
                        if name in ['CW','ABC','FOX','PBS','CBS','NBC','MY9']:
                            channels.append({ 
                                'name': name,    
                                'url': url
                                })
                    else:
                        channels.append({
                            'name': name,
                            'url': url
                            })
            except:
                pass
        return channels    

    def get_recordings(self, quality, stream_type, type='recordings'):
        from datetime import datetime
        if quality == 3:
            quality -= 1
        Addon.log('get_recordings,' + str(quality) + ',' + stream_type)
        token_check = self._get_json('gtv/1/live/getcustomerkey', {'token': Addon.get_setting('token')})['username']
        if token_check != Addon.get_setting('email'):
            self.token = self._login()
        else:
            self.token = Addon.get_setting('token')
        account_type = self._get_json('gtv/1/live/getuserbytoken', {'token': self.token})['data']['plan_free']
        if account_type == 1:
            Addon.set_setting('free_package', 'true')
            if Addon.get_setting('quality') == '3':
                Addon.set_setting('quality', '2')
        else:
            Addon.set_setting('free_package', 'false')
        dvr_check = self._get_json('gtv/1/live/getuserbytoken', {'token': self.token})['data']['plan_name']
        if 'DVR' in dvr_check:
            Addon.set_setting('dvr', 'true')
        else:
            Addon.set_setting('dvr', 'false')
        content = self._get_json('gtv/1/live/viewdvrlist', {'token': self.token})
        recordings = []
        scheduled = []
        recurring = []
        achannels = []
        results = content['results'];
        for i in results:
            chan = Addon.cleanChanName(i['callsign'])
            mediatype = i['connectorid'][:2]
            icon = self.mBASE_URL + '/gtv/1/live/viewposter?srsid=' + str(i['srsid']) + '&cs=' + i['callsign'] + '&tid=' + mediatype
            title = i['title']
            plot = i['description']
            plot = plot.replace("&amp;", "&").replace('&quot;','"')
            orig_air_date = i['orig_air_date']
            event_time = datetime.fromtimestamp(i['ut_start']).strftime('%I:%M %p').lstrip('0')
            event_date_month = datetime.fromtimestamp(i['ut_start']).strftime('%m').lstrip('0')
            event_date_day = datetime.fromtimestamp(i['ut_start']).strftime('%d').lstrip('0')
            event_date_year = datetime.fromtimestamp(i['ut_start']).strftime('%y')
            event_date_name = datetime.fromtimestamp(i['ut_start']).strftime('%A - ')
            event_date_time = event_date_name + event_date_month + '/' + event_date_day + '/' + event_date_year + ' at ' + event_time
            dvrtimertype = i['dvrtimertype']
            event_inprogress = i['event_inprogress']
            if event_inprogress == 0:
                expire_time = datetime.fromtimestamp(i['ut_expires']).strftime('%I:%M %p').lstrip('0')
                expire_date_month = datetime.fromtimestamp(i['ut_expires']).strftime('%m').lstrip('0')
                expire_date_day = datetime.fromtimestamp(i['ut_expires']).strftime('%d').lstrip('0')
                expire_date_year = datetime.fromtimestamp(i['ut_expires']).strftime('%y')
                expire_date_name = datetime.fromtimestamp(i['ut_expires']).strftime('%A - ')
                expire_date_time = expire_date_name + expire_date_month + '/' + expire_date_day + '/' + expire_date_year + ' at ' + expire_time
            rec_date = i['recordedonmmddyyyy']
            synopsis = i['synopsis']
            duration = i['runtime']
            episode_title = i['episode_title']
            app_name = 'dvrrokuplay'
            url = stream_type + '://' + i['dvrlocation'] + '.ustvnow.com:1935/' + app_name + '/mp4:' + [i['filename_low'], i['filename_med'], i['filename_high']][quality]
            del_url = '/gtv/1/dvr/updatedvr?scheduleid=' + str(i['scheduleid']) + '&token=' + self.token + '&action=remove'
            remove_url = '/gtv/1/dvr/updatedvrtimer?connectorid=' + str(i['connectorid']) + '&prgsvcid=' + str(i['prgsvcid']) + '&eventtime=' + str(i['event_time']) + '&token=' + self.token + '&action=remove'
            set_url = '/gtv/1/dvr/updatedvrtimer?connectorid=' + str(i['connectorid']) + '&prgsvcid=' + str(i['prgsvcid']) + '&eventtime=' + str(i['event_time']) +'&token=' + self.token + '&action=add'
            if (type == 'recordings' and event_inprogress == 0):
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
                                   'event_date_time': event_date_time,
                                   'expire_date_time': expire_date_time,
                                   'synopsis': synopsis,
                                   'playable': (event_inprogress == 0),
                                   'del_url': del_url,
                                   'set_url': set_url,
                                   'remove_url': remove_url,
                                   'dvrtimertype': dvrtimertype,
                                   'mediatype': mediatype,
                                   })
            elif (type == 'scheduled' and event_inprogress != 0):
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
                                   'event_date_time': event_date_time,
                                   'synopsis': synopsis,
                                   'playable': False,
                                   'del_url': del_url,
                                   'set_url': set_url,
                                   'remove_url': remove_url,
                                   'dvrtimertype': dvrtimertype,
                                   'mediatype': mediatype,
                                   })
            elif (type == 'recurring' and dvrtimertype !=0):
                aChannelname = {'title': title}
                aChannel = {'title': title}
                if aChannelname not in achannels:
                    achannels.append(aChannelname)
                    recurring.append({'channel': chan,
                                   'stream_url': url,
                                   'title': title,
                                   'episode_title': episode_title,
                                   'tvshowtitle': title,
                                   'plot': plot,
                                   'rec_date': rec_date,
                                   'icon': icon,
                                   'duration': duration,
                                   'orig_air_date': orig_air_date,
                                   'event_date_time': event_date_time,
                                   'synopsis': synopsis,
                                   'playable': False,
                                   'remove_url': remove_url
                                   })
        if (type == 'recordings'):
            return recordings
        elif (type == 'scheduled'):
            return scheduled
        elif (type == 'recurring'):
            return recurring
        else:
            return []
        return recordings

    def get_movies(self, quality, stream_type, type='now'):
        from datetime import datetime
        Addon.log('get_movies' + str(quality) + ',' + stream_type)
        token_check = self._get_json('gtv/1/live/getcustomerkey', {'token': Addon.get_setting('token')})['username']
        if token_check != Addon.get_setting('email'):
            self.token = self._login()
        else:
            self.token = Addon.get_setting('token')
        account_type = self._get_json('gtv/1/live/getuserbytoken', {'token': self.token})['data']['plan_free']
        if account_type == 1:
            Addon.set_setting('free_package', 'true')
            if Addon.get_setting('quality') == '3':
                Addon.set_setting('quality', '2')
        else:
            Addon.set_setting('free_package', 'false')
        dvr_check = self._get_json('gtv/1/live/getuserbytoken', {'token': self.token})['data']['plan_name']
        if 'DVR' in dvr_check:
            Addon.set_setting('dvr', 'true')
        else:
            Addon.set_setting('dvr', 'false')
        content = self._get_json('gtv/1/live/upcoming', {'token': self.token})
        now = []
        today = []
        later = []
        results = content;
        for i in results:
            chan = Addon.cleanChanName(i['callsign'])
            mediatype = i['connectorid'][:2]
            icon = self.mBASE_URL + '/gtv/1/live/viewposter?srsid=' + str(i['srsid']) + '&cs=' + i['callsign'] + '&tid=' + mediatype
            title = i['title']
            plot = i['description']
            plot = plot.replace("&amp;", "&").replace('&quot;','"')
            orig_air_date = i['orig_air_date']
            event_time = datetime.fromtimestamp(i['ut_start']).strftime('%I:%M %p').lstrip('0')
            event_date_month = datetime.fromtimestamp(i['ut_start']).strftime('%m').lstrip('0')
            event_date_day = datetime.fromtimestamp(i['ut_start']).strftime('%d').lstrip('0')
            event_date_year = datetime.fromtimestamp(i['ut_start']).strftime('%y')
            event_date_name = datetime.fromtimestamp(i['ut_start']).strftime('%A - ')
            event_date_time = event_date_name + event_date_month + '/' + event_date_day + '/' + event_date_year + ' at ' + event_time
            event_date_time_now = datetime.fromtimestamp(i['ut_start']).strftime('%I:%M %p').lstrip('0')
            dvrtimertype = i['dvrtimertype']
            event_inprogress = i['event_inprogress']
            timecat = i['timecat']
            synopsis = i['synopsis']
            duration = i['runtime']
            episode_title = i['episode_title']
            app_name = 'dvrrokuplay'
            rec_url = '/gtv/1/dvr/updatedvr?scheduleid=' + str(i['scheduleid']) + '&token=' + self.token + '&action=add'

            if (type == 'now' and event_inprogress == 1):
                if Addon.get_setting('free_package') == 'true':
                    if chan in ['CW','ABC','FOX','PBS','CBS','NBC','MY9']:
                        now.append({'channel': chan,
                                       'title': title,
                                       'episode_title': episode_title,
                                       'tvshowtitle': title,
                                       'plot': plot,
                                       'icon': icon,
                                       'duration': duration,
                                       'orig_air_date': orig_air_date,
                                       'event_date_time_now': event_date_time_now,
                                       'synopsis': synopsis,
                                       'playable': (event_inprogress == 1),
                                       'dvrtimertype': dvrtimertype,
                                       'mediatype': mediatype,
                                       'rec_url': rec_url
                                       })
                else:
                    now.append({'channel': chan,
                                       'title': title,
                                       'episode_title': episode_title,
                                       'tvshowtitle': title,
                                       'plot': plot,
                                       'icon': icon,
                                       'duration': duration,
                                       'orig_air_date': orig_air_date,
                                       'event_date_time_now': event_date_time_now,
                                       'synopsis': synopsis,
                                       'playable': (event_inprogress == 1),
                                       'dvrtimertype': dvrtimertype,
                                       'mediatype': mediatype,
                                       'rec_url': rec_url
                                       })
            elif (type == 'today' and event_inprogress != 1 and timecat == 'Today'):
                if Addon.get_setting('free_package') == 'true':
                    if chan in ['CW','ABC','FOX','PBS','CBS','NBC','MY9']:
                        today.append({'channel': chan,
                                       'title': title,
                                       'episode_title': episode_title,
                                       'tvshowtitle': title,
                                       'plot': plot,
                                       'icon': icon,
                                       'duration': duration,
                                       'orig_air_date': orig_air_date,
                                       'event_date_time': event_date_time,
                                       'synopsis': synopsis,
                                       'playable': (event_inprogress == 1),
                                       'dvrtimertype': dvrtimertype,
                                       'mediatype': mediatype,
                                       'rec_url': rec_url
                                       })
                else:
                    today.append({'channel': chan,
                                       'title': title,
                                       'episode_title': episode_title,
                                       'tvshowtitle': title,
                                       'plot': plot,
                                       'icon': icon,
                                       'duration': duration,
                                       'orig_air_date': orig_air_date,
                                       'event_date_time': event_date_time,
                                       'synopsis': synopsis,
                                       'playable': (event_inprogress == 1),
                                       'dvrtimertype': dvrtimertype,
                                       'mediatype': mediatype,
                                       'rec_url': rec_url
                                       })
            elif (type == 'later' and event_inprogress !=0  and timecat == 'Tomorrow'):
                if Addon.get_setting('free_package') == 'true':
                    if chan in ['CW','ABC','FOX','PBS','CBS','NBC','MY9']:
                        later.append({'channel': chan,
                                       'title': title,
                                       'episode_title': episode_title,
                                       'tvshowtitle': title,
                                       'plot': plot,
                                       'icon': icon,
                                       'duration': duration,
                                       'orig_air_date': orig_air_date,
                                       'event_date_time': event_date_time,
                                       'synopsis': synopsis,
                                       'playable': (event_inprogress == 1),
                                       'dvrtimertype': dvrtimertype,
                                       'mediatype': mediatype,
                                       'rec_url': rec_url
                                       })
                else:
                    later.append({'channel': chan,
                                       'title': title,
                                       'episode_title': episode_title,
                                       'tvshowtitle': title,
                                       'plot': plot,
                                       'icon': icon,
                                       'duration': duration,
                                       'orig_air_date': orig_air_date,
                                       'event_date_time': event_date_time,
                                       'synopsis': synopsis,
                                       'playable': (event_inprogress == 1),
                                       'dvrtimertype': dvrtimertype,
                                       'mediatype': mediatype,
                                       'rec_url': rec_url
                                       })
        if (type == 'now'):
            return now
        elif (type == 'today'):
            return today
        elif (type == 'later'):
            return later
        else:
            return []
        return now

    def get_sports(self, quality, stream_type, type='now'):
        Addon.log('get_sports,' + str(quality) + ',' + stream_type)
        token_check = self._get_json('gtv/1/live/getcustomerkey', {'token': Addon.get_setting('token')})['username']
        if token_check != Addon.get_setting('email'):
            self.token = self._login()
        else:
            self.token = Addon.get_setting('token')
        account_type = self._get_json('gtv/1/live/getuserbytoken', {'token': self.token})['data']['plan_free']
        if account_type == 1:
            Addon.set_setting('free_package', 'true')
            if Addon.get_setting('quality') == '3':
                Addon.set_setting('quality', '2')
        else:
            Addon.set_setting('free_package', 'false')
        dvr_check = self._get_json('gtv/1/live/getuserbytoken', {'token': self.token})['data']['plan_name']
        if 'DVR' in dvr_check:
            Addon.set_setting('dvr', 'true')
        else:
            Addon.set_setting('dvr', 'false')
        content = self._get_json('gtv/1/live/channelguide', {'token': self.token})
        now = []
        today = []
        later = []
        results = content['results'];
        import time, datetime
        date_today = datetime.date.today()
        sports = ['Basketball', 'Football', 'Baseball', 'Soccer', 'Tennis', 'Golf', 'Skating', 'Skateboarding', 'Skiing', 'Snowboarding', 'Rugby', 'Nascar']
        for i in results:
            from datetime import datetime
            event_time = datetime.fromtimestamp(i['ut_start']).strftime('%I:%M %p').lstrip('0')
            event_date_month = datetime.fromtimestamp(i['ut_start']).strftime('%m').lstrip('0')
            event_date_day = datetime.fromtimestamp(i['ut_start']).strftime('%d').lstrip('0')
            event_date_year = datetime.fromtimestamp(i['ut_start']).strftime('%y')
            event_date_name = datetime.fromtimestamp(i['ut_start']).strftime('%A - ')
            event_date_time = event_date_name + event_date_month + '/' + event_date_day + '/' + event_date_year + ' at ' + event_time
            event_date_time_now = datetime.fromtimestamp(i['ut_start']).strftime('%I:%M %p').lstrip('0')
            try:
                if type == 'now' and i['order'] == 1:
                    name = Addon.cleanChanName(i['stream_code'])
                    mediatype = i['mediatype']
                    poster_url = self.mBASE_URL + '/gtv/1/live/viewposter?srsid=' + str(i['srsid']) + '&cs=' + i['callsign'] + '&tid=' + mediatype
                    mediatype = mediatype.replace('SH', 'tvshow').replace('EP', 'episode').replace('MV', 'movie')
                    rec_url = '/gtv/1/dvr/updatedvr?scheduleid=' + str(i['scheduleid']) + '&token=' + self.token + '&action=add'
                    set_url = '/gtv/1/dvr/updatedvrtimer?connectorid=' + str(i['connectorid']) + '&prgsvcid=' + str(i['prgsvcid']) + '&eventtime=' + str(i['event_time']) + '&token=' + self.token + '&action=add'
                    if i['title'] in sports or name == 'ESPN':
                        if Addon.get_setting('free_package') == 'true':
                            if name in ['CW','ABC','FOX','PBS','CBS','NBC','MY9']:
                                now.append({
                                    'name': name,
                                    'episode_title': i['episode_title'],
                                    'title': i['title'],
                                    'plot': i['description'],
                                    'mediatype': mediatype,
                                    'playable': True,
                                    'poster_url': poster_url,
                                    'rec_url': rec_url,
                                    'set_url': set_url,
                                    'event_date_time_now': event_date_time_now
                                    })
                        else:
                            now.append({
                                'name': name,
                                'episode_title': i['episode_title'],
                                'title': i['title'],
                                'plot': i['description'],
                                'mediatype': mediatype,
                                'playable': True,
                                'poster_url': poster_url,
                                'rec_url': rec_url,
                                'set_url': set_url,
                                'event_date_time_now': event_date_time_now
                                })

                elif type == 'today' and i['order'] != 1 and str(date_today) == str(i['event_date']):
                    name = Addon.cleanChanName(i['stream_code'])
                    mediatype = i['mediatype']
                    poster_url = self.mBASE_URL + '/gtv/1/live/viewposter?srsid=' + str(i['srsid']) + '&cs=' + i['callsign'] + '&tid=' + mediatype
                    mediatype = mediatype.replace('SH', 'tvshow').replace('EP', 'episode').replace('MV', 'movie')
                    rec_url = '/gtv/1/dvr/updatedvr?scheduleid=' + str(i['scheduleid']) + '&token=' + self.token + '&action=add'
                    set_url = '/gtv/1/dvr/updatedvrtimer?connectorid=' + str(i['connectorid']) + '&prgsvcid=' + str(i['prgsvcid']) + '&eventtime=' + str(i['event_time']) + '&token=' + self.token + '&action=add'
                    if i['title'] in sports or name == 'ESPN':
                        if Addon.get_setting('free_package') == 'true':
                            if name in ['CW','ABC','FOX','PBS','CBS','NBC','MY9']:
                                today.append({
                                    'name': name,
                                    'episode_title': i['episode_title'],
                                    'title': i['title'],
                                    'plot': i['description'],
                                    'mediatype': mediatype,
                                    'playable': True,
                                    'poster_url': poster_url,
                                    'rec_url': rec_url,
                                    'set_url': set_url,
                                    'event_date_time': event_date_time
                                    })
                        else:
                            today.append({
                                'name': name,
                                'episode_title': i['episode_title'],
                                'title': i['title'],
                                'plot': i['description'],
                                'mediatype': mediatype,
                                'playable': True,
                                'poster_url': poster_url,
                                'rec_url': rec_url,
                                'set_url': set_url,
                                'event_date_time': event_date_time
                                })

                elif type == 'later' and i['order'] != 1 and str(date_today) != str(i['event_date']):
                    name = Addon.cleanChanName(i['stream_code'])
                    mediatype = i['mediatype']
                    poster_url = self.mBASE_URL + '/gtv/1/live/viewposter?srsid=' + str(i['srsid']) + '&cs=' + i['callsign'] + '&tid=' + mediatype
                    mediatype = mediatype.replace('SH', 'tvshow').replace('EP', 'episode').replace('MV', 'movie')
                    rec_url = '/gtv/1/dvr/updatedvr?scheduleid=' + str(i['scheduleid']) + '&token=' + self.token + '&action=add'
                    set_url = '/gtv/1/dvr/updatedvrtimer?connectorid=' + str(i['connectorid']) + '&prgsvcid=' + str(i['prgsvcid']) + '&eventtime=' + str(i['event_time']) + '&token=' + self.token + '&action=add'
                    if i['title'] in sports or name == 'ESPN':
                        if Addon.get_setting('free_package') == 'true':
                            if name in ['CW','ABC','FOX','PBS','CBS','NBC','MY9']:
                                later.append({
                                    'name': name,
                                    'episode_title': i['episode_title'],
                                    'title': i['title'],
                                    'plot': i['description'],
                                    'mediatype': mediatype,
                                    'playable': True,
                                    'poster_url': poster_url,
                                    'rec_url': rec_url,
                                    'set_url': set_url,
                                    'event_date_time': event_date_time
                                    })
                        else:
                            later.append({
                                'name': name,
                                'episode_title': i['episode_title'],
                                'title': i['title'],
                                'plot': i['description'],
                                'mediatype': mediatype,
                                'playable': True,
                                'poster_url': poster_url,
                                'rec_url': rec_url,
                                'set_url': set_url,
                                'event_date_time': event_date_time
                                })
            except:
                pass
        if (type == 'now'):
            return now
        elif (type == 'today'):
            return today
        elif (type == 'later'):
            return later
        else:
            return []
        return now

    def get_guidedata(self, quality, stream_type):
        Addon.log('get_guidedata')
        token_check = self._get_json('gtv/1/live/getcustomerkey', {'token': Addon.get_setting('token')})['username']
        if token_check != Addon.get_setting('email'):
            self.token = self._login()
        else:
            self.token = Addon.get_setting('token')
        content = self._get_json('gtv/1/live/channelguide', {'token': self.token})
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
            id = channel['name'];
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

        for programme in results:

            event_time = datetime.fromtimestamp(programme['ut_start']).strftime('%I:%M %p').lstrip('0')
            event_date_month = datetime.fromtimestamp(programme['ut_start']).strftime('%m').lstrip('0')
            event_date_day = datetime.fromtimestamp(programme['ut_start']).strftime('%d').lstrip('0')
            event_date_year = datetime.fromtimestamp(programme['ut_start']).strftime('%y')
            event_date_name = datetime.fromtimestamp(programme['ut_start']).strftime('%A - ')
            event_date_time = event_date_name + event_date_month + '/' + event_date_day + '/' + event_date_year + ' at ' + event_time
            if programme['event_inprogress'] == 1:
                event_date_time = 'Started at ' + datetime.fromtimestamp(programme['ut_start']).strftime('%I:%M %p').lstrip('0')
                event_inprogress = '1'
            else:
                event_inprogress= '0'
            mediatype = programme['mediatype']
            mediatype = mediatype.replace('SH', 'tvshow').replace('EP', 'episode').replace('MV', 'movie')
            rec_url = '/gtv/1/dvr/updatedvr?scheduleid=' + str(programme['scheduleid']) + '&token=' + self.token + '&action=add'
            set_url = '/gtv/1/dvr/updatedvrtimer?connectorid=' + str(programme['connectorid']) + '&prgsvcid=' + str(programme['prgsvcid']) + '&eventtime=' + str(programme['event_time']) + '&token=' + self.token + '&action=add'

            start_time 	= datetime.fromtimestamp(float(programme['ut_start']));
            stop_time	= start_time + timedelta(seconds=int(programme['runtime']));
            
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
            i_entry.setAttribute("src", self.mBASE_URL + '/gtv/1/live/viewposter?srsid=' + str(programme['srsid']) + '&cs=' + programme['callsign'] + '&tid=' + programme['mediatype']);
            pg_entry.appendChild(i_entry);

            d_entry = doc.createElement('event_date_time');
            d_entry_content = doc.createTextNode(str(event_date_time));
            d_entry.appendChild(d_entry_content);
            pg_entry.appendChild(d_entry);

            d_entry = doc.createElement('mediatype');
            d_entry_content = doc.createTextNode(str(mediatype));
            d_entry.appendChild(d_entry_content);
            pg_entry.appendChild(d_entry);

            i_entry = doc.createElement('rec_url');
            i_entry.setAttribute("src", rec_url);
            pg_entry.appendChild(i_entry);

            i_entry = doc.createElement('set_url');
            i_entry.setAttribute("src", set_url);
            pg_entry.appendChild(i_entry);

            d_entry = doc.createElement('event_inprogress');
            d_entry_content = doc.createTextNode(str(event_inprogress));
            d_entry.appendChild(d_entry_content);
            pg_entry.appendChild(d_entry);

        return doc

    def get_tvguide(self, filename, type='channels', name=''):
        Addon.log('get_tvguide,' + type + ',' + name)
        return Addon.readXMLTV(filename, type, name)
    
    def delete_recording(self, del_url):
        Addon.log('delete_recording')
        html = self._get_html(del_url)
        if 'success' in html:
            self.dlg.ok(Addon.get_string(30000), Addon.get_string(30017))
        else:
            self.dlg.ok(Addon.get_string(30000), Addon.get_string(30018))

    def remove_recurring(self, remove_url):
        Addon.log('remove_recurring')
        html = self._get_html(remove_url)
        if 'success' in html:
            self.dlg.ok(Addon.get_string(30000), Addon.get_string(30020))
        else:
            self.dlg.ok(Addon.get_string(30000), Addon.get_string(30021))

    def set_recurring(self, set_url):
        Addon.log('set_recurring')
        html = self._get_html(set_url)
        if 'success' in html:
            self.dlg.ok(Addon.get_string(30000), Addon.get_string(30024))
        else:
            self.dlg.ok(Addon.get_string(30000), Addon.get_string(30025))

    def record_show(self, rec_url):
        Addon.log('record_show')
        html = self._get_html(rec_url)
        if 'success' in html:
            self.dlg.ok(Addon.get_string(30000), Addon.get_string(30013))
        else:
            self.dlg.ok(Addon.get_string(30000), Addon.get_string(30016))
            
    def _build_url(self, path, queries={}):
        Addon.log('_build_url')
        if queries:
            query = Addon.build_query(queries)
            return '%s/%s?%s' % (self.mBASE_URL, path, query)
        else:
            return '%s/%s' % (self.mBASE_URL, path)

    def _build_json(self, path, queries={}):
        Addon.log('_build_json')
        if queries:
            query = urllib.urlencode(queries)
            return '%s/%s?%s' % (self.mBASE_URL, path, query)
        else:
            return '%s/%s' % (self.mBASE_URL, path)

            
    def _fetch(self, url, form_data=False):
        Addon.log('_fetch')
        opener = urllib2.build_opener()
        opener.addheaders = [('User-agent', 'Mozilla/5.0')]
        if form_data:
            req = urllib2.Request(url, form_data)
        else:
            req = url
        try:
            response = opener.open(req)
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
   
        response = self._fetch(url)
        if response:
            html = response.read()
        else:
            html = False
        return html
        
    def _login(self):
        Addon.log('_login')
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
                Addon.set_setting('token', cookie.value)
                return cookie.value
            else:
                self.dlg.ok(Addon.get_string(30000), Addon.get_string(30011))
        return 'False'
