#
#      Copyright (C) 2014 Tommy Winther, TermeHansen
#
#  https://github.com/xbmc-danish-addons/plugin.video.drnu
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

import hashlib
import json
from pathlib import Path
import requests
import requests_cache
import time
from dateutil import parser
from datetime import datetime, timezone, timedelta


CHANNEL_IDS = [20875, 20876, 192099, 192100, 20892]
URL = 'https://production.dr-massive.com/api'
GET_TIMEOUT = 5


class Api():
    def __init__(self, cachePath, getLocalizedString, get_setting):
        self.cachePath = cachePath
        self.tr = getLocalizedString
        self.cleanup_every = int(get_setting('recache.cleanup'))
        self.expire_hours = int(get_setting('recache.expiration'))
        self.init_sqlite_db()

        self.token_file = Path(f'{self.cachePath}/token.json')
        self._user_token = None
        self.refresh_tokens()

    def init_sqlite_db(self):
        if not (self.cachePath/'requests_cleaned').exists():
            if (self.cachePath/'requests.cache.sqlite').exists():
                (self.cachePath/'requests.cache.sqlite').unlink()
        request_fname = str(self.cachePath/'requests.cache')
        self.session = requests_cache.CachedSession(
            request_fname, backend='sqlite', expire_after=3600*self.expire_hours)

        if (self.cachePath/'requests_cleaned').exists():
            if (time.time() - (self.cachePath/'requests_cleaned').stat().st_mtime)/3600/24 < self.cleanup_every:
                # less than self.cleanup_every days since last cleaning, no need...
                return

        # doing recache.db cleanup
        try:
            self.session.remove_expired_responses()
        except Exception:
            if (self.cachePath/'requests.cache.sqlite').exists():
                (self.cachePath/'requests.cache.sqlite').unlink()
            self.session = requests_cache.CachedSession(
                request_fname, backend='sqlite', expire_after=3600*self.expire_hours)
        (self.cachePath/'requests_cleaned').write_text(str(datetime.now()))

    def deviceid(self):
        v = int(Path(__file__).stat().st_mtime)
        h = hashlib.md5(str(v).encode('utf-8')).hexdigest()
        return '-'.join([h[:8], h[8:12], h[12:16], h[16:20], h[20:32]])

    def read_token(self, s):
        tokens = json.loads(s)
        time_struct = time.strptime(tokens[0]['expirationDate'].split('.')[0], '%Y-%m-%dT%H:%M:%S')
        self._token_expire = datetime(*time_struct[0:6])
        self._user_token = tokens[0]['value']
        self._profile_token = tokens[1]['value']

    def request_tokens(self):
        data = {"deviceId": self.deviceid(), "scopes": ["Catalog"], "optout": False}
        params = {'device': 'web_browser', 'ff': 'idp,ldp,rpt', 'lang': 'da', 'supportFallbackToken': True}

        url = URL + '/authorization/anonymous-sso?'
        u = requests.post(url, json=data, params=params)
        self._user_token = None
        if u.status_code == 200:
            self.token_file.write_bytes(u.content)
            self.read_token(u.content)
        else:
            raise ApiException(f'Failed to get new token from: {url}')

    def refresh_tokens(self):
        if self._user_token is None:
            if self.token_file.exists():
                self.read_token(self.token_file.read_bytes())
            else:
                self.request_tokens()
        if (self._token_expire - datetime.now()).total_seconds() < 120:
            self.request_tokens()

    def user_token(self):
        self.refresh_tokens()
        return self._user_token

    def profile_token(self):
        self.refresh_tokens()
        return self._profile_token

    def get_programcard(self, path, data=None, use_cache=True):
        url = URL + '/page?'
        if data is None:
            data = {
                'item_detail_expand': 'all',
                'list_page_size': '24',
                'max_list_prefetch': '3',
                'path': path
            }
        if use_cache:
            u = self.session.get(url, params=data, timeout=GET_TIMEOUT)
        else:
            u = requests.get(url, params=data, timeout=GET_TIMEOUT)
        if u.status_code == 200:
            return u.json()
        else:
            raise ApiException(u.text)

    def get_next(self, path, use_cache=True):
        url = URL + path
        if use_cache:
            u = self.session.get(url, timeout=GET_TIMEOUT)
        else:
            u = requests.get(url, timeout=GET_TIMEOUT)
        if u.status_code == 200:
            return u.json()
        else:
            raise ApiException(u.text)

    def get_list(self, id, param, use_cache=True):
        if isinstance(id, str):
            id = int(id.replace('ID_', ''))
        url = URL + f'/lists/{id}'
        data = {'page_size': '24'}
        if param != 'NoParam':
            data['param'] = param

        if use_cache:
            u = self.session.get(url, params=data, timeout=GET_TIMEOUT)
        else:
            u = requests.get(url, params=data, timeout=GET_TIMEOUT)
        if u.status_code == 200:
            return u.json()
        else:
            raise ApiException(u.text)

    def kids_item(self, item):
        if 'classification' in item:
            if item['classification']['code'] in ['DR-Ramasjang', 'DR-Minisjang']:
                return True
        if 'categories' in item:
            for cat in ['dr minisjang', 'dr ramasjang', 'dr ultra']:
                if cat in item['categories']:
                    return True
        return False

    def unfold_list(self, item, filter_kids=False):
        items = []
        if 'next' in item['paging']:
            next_js = self.get_next(item['paging']['next'])
            items += next_js['items']
            while 'next' in next_js['paging']:
                next_js = self.get_next(next_js['paging']['next'])
                items += next_js['items']
        else:
            items += item['items']
        if filter_kids:
            items = [item for item in items if not self.kids_item(item)]
        return items

    def search(self, term):
        url = URL + '/search'
        headers = {"X-Authorization": f'Bearer {self.profile_token()}'}
        data = {
            'item_detail_expand': 'all',
            'list_page_size': '24',
            'group': 'true',
            'term': term
        }
        u = self.session.get(url, params=data, headers=headers, timeout=GET_TIMEOUT)
        if u.status_code == 200:
            return u.json()
        else:
            raise ApiException(u.text)

    def get_home(self):
        data = dict(
            list_page_size=24,
            max_list_prefetch=1,
            item_detail_expand='all',
            path='/',
            segments='drtv,mt_K8q4Nz3,optedin',
        )
        js = self.get_programcard('/', data=data)
        items = [{'title': 'Programmer A-Å', 'path': '/a-aa', 'icon': 'all.png'}]
        for item in js['entries']:
            if item['title'] not in ['', 'Se Live TV', 'Vi tror, du kan lide']:  # TODO activate again when login works
                items.append({'title': item['title'], 'path': item['list']['path']})
        return items

    def getLiveTV(self):
        channels = []
        schedules = self.get_channel_schedule_strings()
        for id in CHANNEL_IDS:
            card = self.get_programcard(f'/kanal/{id}')
            card['entries'][0]['schedule_str'] = schedules[id]
            channels += card['entries']
        return channels

    def recache_items(self, progress=None, clear_expired=False):
        if clear_expired:
            self.session.remove_expired_responses()
            (self.cachePath/'requests_cleaned').write_text(str(datetime.now()))

        js = self.get_programcard('/a-aa')
        maxidx = len(js['entries']) + 3
        i = 0
        for item in js['entries']:
            if item['type'] == 'ListEntry':
                st2 = time.time()
                self.unfold_list(item['list'])
                msg = f"{self.tr(30523)}'{item['title']}'\n{time.time() - st2:.1f}s"
                if progress is not None:
                    if progress.iscanceled():
                        return
                    progress.update(int(100*(i+1)/maxidx), msg)
            i += 1

        for channel in ['dr-ramasjang', 'dr-minisjang', 'dr-ultra']:
            self.get_children_front_items(channel)
            msg = f"{self.tr(30523)}'{channel}'\n{time.time() - st2:.1f}s"
            if progress is not None:
                if progress.iscanceled():
                    return
                progress.update(int(100*(i+1)/maxidx), msg)
            i += 1

    def get_children_front_items(self, channel):
        names = {
            'dr-ramasjang': '/ramasjang_a-aa',
            'dr-minisjang': '/minisjang/a-aa',
            'dr-ultra': '/ultra_a-aa',
            'dr': '/a-aa',
            }
        name = names[channel]
        js = self.get_programcard(name)
        items = []
        for item in js['entries']:
            if item['type'] == 'ListEntry':
                items += self.unfold_list(item['list'])
        return items

    def get_stream(self, id):
        url = URL + f'/account/items/{int(id)}/videos?'
        headers = {"X-Authorization": f'Bearer {self.user_token()}'}
        data = {
            'delivery': 'stream',
            'device': 'web_browser',
            'ff': 'idp,ldp,rpt',
            'lang': 'da',
            'resolution': 'HD-1080',
            'sub': 'Anonymous'
        }

        u = self.session.get(url, params=data, headers=headers, timeout=GET_TIMEOUT)
        if u.status_code == 200:
            for stream in u.json():
                if stream['accessService'] == 'StandardVideo':
                    return stream
            return None
        else:
            raise ApiException(u.text)

    def get_info(self, item):
        title = item['title']
        if item['type'] == 'season':
            title += f" {item['seasonNumber']}"
        elif item.get('contextualTitle', None):
            cont = item['contextualTitle']
            if cont.count('.') >= 1 and cont.split('.', 1)[1].strip() not in title:
                title += f" ({item['contextualTitle']})"

        infoLabels = {'title': title}
        if item.get('shortDescription', ''):
            infoLabels['plot'] = item['shortDescription']
        if item.get('tagline', ''):
            infoLabels['plotoutline'] = item['tagline']
        if item.get('customFields'):
            if item['customFields'].get('BroadcastTimeDK'):
                broadcast = parser.parse(item['customFields']['BroadcastTimeDK'])
                infoLabels['date'] = broadcast.strftime('%d.%m.%Y')
                infoLabels['aired'] = broadcast.strftime('%Y-%m-%d')
                infoLabels['year'] = int(broadcast.strftime('%Y'))
        if item.get('seasonNumber'):
            infoLabels['season'] = item['seasonNumber']
        if item['type'] in ["movie", "season", "episode"]:
            infoLabels['mediatype'] = item['type']
        elif item['type'] == 'program':
            infoLabels['mediatype'] = 'tvshow'
        return title, infoLabels

    def get_schedules(self, channels=CHANNEL_IDS, date=None, hour=None):
        url = URL + '/schedules?'
        now = datetime.now()
        if date is None:
            date = now.strftime("%Y-%m-%d")
        if hour is None:
            hour = int(now.strftime("%H"))
        data = {
            'date': date,
            'hour': hour-2,
            'duration': 6,
            'channels': channels,
        }
        u = requests.get(url, params=data, timeout=GET_TIMEOUT)
        if u.status_code == 200:
            return u.json()
        else:
            raise ApiException(u.text)

    def get_channel_schedule_strings(self, channels=CHANNEL_IDS):
        out = {}
        now = datetime.now(timezone.utc)
        for channel in self.get_schedules():
            id = int(channel['channelId'])
            out[id] = ''
            for item in channel['schedules']:
                if parser.parse(item['endDate']) > now and out[id].count('\n') < 5:
                    t = parser.parse(item['startDate']) + timedelta(hours=2)
                    start = t.strftime('%H:%M')
                    out[id] += f"{start} {item['item']['title']} \n"
        return out


class ApiException(Exception):
    pass
