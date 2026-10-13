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
#  along with this Program; see the file LICENSE.txt.  If not, write to
#  the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.
#  http://www.gnu.org/copyleft/gpl.html
#
"""DR API client: auth token bookkeeping, listings, schedules and streams.

Auth protocol functions live in drauth, subtitle handling in subtitles and
shared constants in constants. The names are re-exported here so existing
imports of tvapi keep working.
"""

import os
import pickle
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Optional, Union
from urllib.parse import parse_qsl, urlencode, urlparse

import requests
import requests_cache
from dateutil import parser
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

from resources.lib import subtitles

# Re-export the names that used to live in this module
from resources.lib.constants import A_AA, CHANNEL_IDS, CHANNEL_PRESET, GET_TIMEOUT, URL  # noqa: F401
from resources.lib.drauth import (  # noqa: F401
    CLIENT_ID,
    anonymous_tokens,
    deviceid,
    exchange_token,
    full_login,
    generate_code_challenge,
    generate_code_verifier,
    oidc_token,
    refresh_token,
)
from resources.lib.subtitles import vtt2srt  # noqa: F401


def cache_path(path: str) -> bool:
    NO_CACHING = ['/liste/drtv-hero']
    return not any(path.startswith(item) for item in NO_CACHING)


def fix_query(url: str, remove: Optional[dict[str, str]] = None, add: Optional[dict[str, str]] = None, remove_keys: Optional[list[str]] = None) -> str:
    if remove is None:
        remove = {}
    if add is None:
        add = {}
    if remove_keys is None:
        remove_keys = []
    o = urlparse(url)
    qs = dict(parse_qsl(o.query))
    for k in remove_keys:
        if k in qs:
            del qs[k]
    for k, v in remove.items():
        if qs.get(k) == v:
            del qs[k]
    qs.update(add)
    qs = dict(sorted(qs.items()))
    return o._replace(query=urlencode(qs)).geturl()


class Api:
    def __init__(self, cachePath: Path, getLocalizedString: Callable[[int], str], get_setting: Callable[[str], str], log_func: Optional[Callable] = None) -> None:
        self.cachePath = cachePath
        self.tr = getLocalizedString
        self.log = log_func
        self.cleanup_every = int(get_setting('recache.cleanup'))
        self.expire_hours = int(get_setting('recache.expiration'))
        self.caching = get_setting('recache.enabled') == 'true'
        self.fetch_full_plot = get_setting('fetch.full_plot') == 'true'
        self.expire_seconds = 3600*self.expire_hours if self.expire_hours >= 0 else None
        retry = Retry(total=3, backoff_factor=2, status_forcelist=[429, 500, 502, 503, 504])
        self.adapter = HTTPAdapter(max_retries=retry)
        self.init_sqlite_db()

        self.token_file = Path(f'{self.cachePath}/token.p')
        self.access_tokens = {}
        self._user_token = None
        self.get_setting = get_setting
        self._refresh_settings()
        self.refresh_tokens()

    def _refresh_settings(self) -> None:
        self.user = self.get_setting('drtv_username')
        self.password = self.get_setting('drtv_password')
        self._user_name = ''

    def init_sqlite_db(self) -> None:
        if not (self.cachePath/'requests_cleaned').exists() and (self.cachePath/'requests.cache.sqlite').exists():
            (self.cachePath/'requests.cache.sqlite').unlink()
        request_fname = str(self.cachePath/'requests.cache')
        self.session = requests_cache.CachedSession(
            request_fname, backend='sqlite', expire_after=self.expire_seconds)
        self.session.mount('https://', self.adapter)

        if (self.cachePath/'requests_cleaned').exists() and (time.time() - (self.cachePath/'requests_cleaned').stat().st_mtime)/3600/24 < self.cleanup_every:
            # less than self.cleanup_every days since last cleaning, no need...
            return

        # doing recache.db cleanup
        try:
            self.session.remove_expired_responses()
        except Exception:
            if (self.cachePath/'requests.cache.sqlite').exists():
                (self.cachePath/'requests.cache.sqlite').unlink()
            self.session = requests_cache.CachedSession(
                request_fname, backend='sqlite', expire_after=self.expire_seconds)
            self.session.mount('https://', self.adapter)
        (self.cachePath/'requests_cleaned').write_text(str(datetime.now()))

    @property
    def user_name(self) -> str:
        if self._user_name == '':
            self._user_name = self.get_profile()['name']
        return self._user_name

    def read_tokens(self, tokens: list[dict]) -> None:
        if 'value' in tokens[0]:
            # old flow, anonymous
            time_str = tokens[0]['expirationDate'].split('.')[0]
            self._user_token = tokens[0]['value']
            self._profile_token = tokens[1]['value']
            self._user_name = 'anonymous'
        else:
            time_str = tokens[0]['Expires'].split('.')[0]
            self._user_token = tokens[0]['Token']
            self._profile_token = tokens[1]['Token']

        try:
            self._token_expire = datetime.strptime(time_str + 'Z', '%Y-%m-%dT%H:%M:%S%z')
        except Exception:
            time_struct = time.strptime(time_str, '%Y-%m-%dT%H:%M:%S')
            self._token_expire = datetime(*time_struct[0:6], tzinfo=timezone.utc)

    def write_tokens(self, tokens: list[dict]) -> None:
        """Persist the tokens by writing a temp file and atomically replacing
        token.p, so a concurrent reader (the service and the plugin share this
        file) can never observe an empty or partially written file.

        The temp name carries the process id: the service and the plugin are
        separate processes and may both save tokens, so a shared temp path
        could be corrupted by two interleaved writes and then be installed
        over token.p by os.replace.
        """
        tmp_file = self.token_file.with_name(f'{self.token_file.name}.{os.getpid()}.tmp')
        with tmp_file.open('wb') as fh:
            pickle.dump([tokens, self.access_tokens], fh)
        os.replace(tmp_file, self.token_file)

    def request_tokens(self) -> Optional[str]:
        self._user_token = None
        self._profile_token = None

        if self.user:
            access_tokens = full_login(self.user, self.password, self.log)
            if 'error' in access_tokens:
                err = access_tokens['error']
                return err
            self.access_tokens = access_tokens
            tokens = exchange_token(access_tokens)
        else:
            self.access_tokens = {}
            tokens = anonymous_tokens()
        # the token endpoints report failures as {'error': ...} instead of a
        # token list; reading them would raise KeyError, so surface the error
        if isinstance(tokens, dict) and 'error' in tokens:
            return tokens['error']
        self.read_tokens(tokens)
        self.write_tokens(tokens)
        return None

    def refresh_tokens(self) -> None:
        if self._user_token is None and self.token_file.exists():
            try:
                with self.token_file.open('rb') as fh:
                    [tokens, self.access_tokens] = pickle.load(fh)
            except (pickle.UnpicklingError, EOFError, ValueError, OSError):
                # a truncated or unreadable token file must not crash startup;
                # drop it and log in again below
                tokens = None
            if isinstance(tokens, list):
                self.read_tokens(tokens)

        if self._user_token is None:
            err = self.request_tokens()
            if err:
                raise ApiException(f'Login failed with: "{err}"')
            return

        if (self._token_expire - datetime.now(timezone.utc)) < timedelta(hours=10):
            failed_refresh = False
            tokens = []
            if self.user and 'refresh_token' in self.access_tokens:
                # oidc flow
                access_tokens = refresh_token(self.access_tokens['refresh_token'])
                if 'error' in access_tokens:
                    failed_refresh = True
                    self.access_tokens = {}
                else:
                    tokens = exchange_token(access_tokens)
                    if isinstance(tokens, dict) and 'error' in tokens:
                        # the exchange failed too; fall back to a fresh login
                        # instead of reading the error dict as a token list
                        failed_refresh = True
                        self.access_tokens = {}
                    else:
                        self.access_tokens = access_tokens
            else:
                # old flow, anonymous
                failed_refresh = True

            if failed_refresh:
                err = self.request_tokens()
                if err:
                    raise ApiException(f'Login failed with: "{err}"')
            else:
                self.read_tokens(tokens)
                self.write_tokens(tokens)

    def user_token(self) -> Optional[str]:
        self.refresh_tokens()
        return self._user_token

    def profile_token(self) -> Optional[str]:
        self.refresh_tokens()
        return self._profile_token

    def _request_get(self, url: str, params: Optional[dict] = None, headers: Optional[dict] = None, use_cache: bool = True) -> Any:
        u = self.session.get(url, params=params, headers=headers, timeout=GET_TIMEOUT) if use_cache and self.caching else requests.get(url, params=params, headers=headers, timeout=GET_TIMEOUT)

        if u.status_code == 200:
            return u.json()
        else:
            raise ApiException(u.text)

    def get_programcard(self, path: str, data: Optional[dict] = None, use_cache: bool = True) -> dict:
        url = URL + '/page?'
        if data is None:
            data = {
                'item_detail_expand': 'all',
                'list_page_size': '24',
                'max_list_prefetch': '3',
                'path': path,
            }
        return self._request_get(url, params=data, use_cache=use_cache)

    def get_item(self, id: Union[int, str], use_cache: bool = True) -> dict:
        url = URL + f'/items/{int(id)}?'
        return self._request_get(url)

    def get_next(self, path: str, use_cache: bool = True, headers: Optional[dict] = None) -> dict:
        remove = {'sub': 'Emergency'}
        remove_keys = ['lang', 'segments', 'isDeviceAbroad', 'isLive2VodSupported']
        url = URL + fix_query(path, remove=remove, remove_keys=remove_keys)
        return self._request_get(url, headers=headers, use_cache=use_cache)

    def get_list(self, id: Union[int, str], param: str, use_cache: bool = True) -> dict:
        if isinstance(id, str):
            id = int(id.replace('ID_', ''))
        url = URL + f'/lists/{id}'
        data = {'page_size': '24'}
        if param != 'NoParam':
            data['param'] = param
        ret = self._request_get(url, params=data, use_cache=use_cache)
        if len(ret['items']) == 0:
            ret = self.get_recommendations(id, use_cache=use_cache, param=param)
        return ret

    def get_recommendations(self, id: int, use_cache: bool = True, param: Optional[str] = None) -> dict:
        url = URL + f'/recommendations/{id}'
        data = {'page_size': '24'}
        if param:
            data['param'] = param
        headers = {"X-Authorization": f'Bearer {self.profile_token()}'}
        return self._request_get(url, params=data, headers=headers, use_cache=use_cache)

    def delete_from_watched(self, id: int) -> None:
        url = f'{URL}/account/profile/continue-watching/{id}'
        headers = {"X-Authorization": f'Bearer {self.profile_token()}'}
        u = self.session.delete(url, headers=headers)
        if u.status_code != 204:
            raise ApiException(u.text)

    def delete_from_mylist(self, id: int) -> None:
        url = f'{URL}/account/profile/bookmarks/{id}'
        headers = {"X-Authorization": f'Bearer {self.profile_token()}'}
        u = self.session.delete(url, headers=headers)
        if u.status_code != 204:
            raise ApiException(u.text)

    def add_to_mylist(self, id: int) -> None:
        url = f'{URL}/account/profile/bookmarks/{id}'
        headers = {"X-Authorization": f'Bearer {self.profile_token()}'}
        u = self.session.put(url, headers=headers)
        if u.status_code != 200:
            raise ApiException(u.text)

    def get_mylist(self, use_cache: bool = False) -> list[dict]:
        url = URL + '/account/profile/bookmarks/list'
        data = {'page_size': '24'}
        headers = {"X-Authorization": f'Bearer {self.profile_token()}'}
        item = self._request_get(url, params=data, headers=headers, use_cache=use_cache)
        items = self.unfold_list(item, headers=headers, use_cache=use_cache)
        for item in items:
            item['in_mylist'] = True
        return items

    def get_continue(self, use_cache: bool = False) -> list[dict]:
        url = URL + '/account/profile/continue-watching/list'
        data = {'page_size': '24'}
        headers = {"X-Authorization": f'Bearer {self.profile_token()}'}
        item = self._request_get(url, params=data, headers=headers, use_cache=use_cache)
        items = self.unfold_list(item, headers=headers, use_cache=use_cache)
        # resume positions used to ride along in /account/profile as 'watched';
        # DR moved them to their own endpoint returning {item id: {position, ...}}
        watched = self._request_get(URL + '/account/profile/watched',
                                    headers=headers, use_cache=use_cache)
        for item in items:
            item['ResumeTime'] = float(watched.get(str(item['id']), {}).get('position', 0.0))
        return items

    def get_profile(self, use_cache: bool = False) -> dict:
        url = URL + '/account/profile'
        headers = {'X-Authorization': 'Bearer ' + self.profile_token()}
        params = {"ff": "idp,ldp,rpt", "lang": "da"}
        return self._request_get(url, headers=headers, params=params, use_cache=use_cache)

    def item_area(self, item: dict) -> str:
        label = ''
        if 'classification' in item:
            label = item['classification']['code'].lower()
        elif 'categories' in item:
            label = ' '.join(item['categories']).lower()
        if label:
            for area in A_AA:
                if area in label:
                    return area
        return 'drtv'  # fall back to general

    def kids_item(self, item: dict) -> bool:
        if 'classification' in item and item['classification']['code'] in ['DR-Ramasjang', 'DR-Minisjang']:
            return True
        if 'categories' in item:
            for cat in ['dr minisjang', 'dr ramasjang']:
                if cat in item['categories']:
                    return True
        return False

    def unfold_list(self, item: dict, filter_kids: bool = False, headers: Optional[dict] = None,
                    progress: Any = None, use_cache: bool = True) -> list[dict]:
        items = item['items']
        if 'next' in item['paging']:
            if progress is not None:
                if progress.iscanceled():
                    return items
                progress.update(self.progress_prc, self.msg + f"page {item['paging']['page']} of {item['paging']['total']}")

            next_js = self.get_next(item['paging']['next'], headers=headers, use_cache=use_cache)
            items += next_js['items']
            while 'next' in next_js['paging']:
                if progress is not None:
                    if progress.iscanceled():
                        return items
                    progress.update(self.progress_prc, self.msg + f"page {next_js['paging']['page']} of {next_js['paging']['total']}")
                next_js = self.get_next(next_js['paging']['next'], headers=headers, use_cache=use_cache)
                items += next_js['items']
        if filter_kids:
            items = [item for item in items if not self.kids_item(item)]
        return items

    def search(self, term: str) -> dict:
        url = URL + '/search'
        headers = {"X-Authorization": f'Bearer {self.profile_token()}'}
        data = {
            'item_detail_expand': 'all',
            'list_page_size': '24',
            'group': 'true',
            'term': term
        }
        # search results must always be live, never a cached copy of an
        # earlier query, so bypass the request cache (still using the session
        # for its retry adapter)
        with self.session.cache_disabled():
            u = self.session.get(url, params=data, headers=headers, timeout=GET_TIMEOUT)
        if u.status_code == 200:
            return u.json()
        else:
            raise ApiException(u.text)

    def get_home(self, area: str = 'drtv') -> list[dict]:
        data = {
            'list_page_size': 24,
            'max_list_prefetch': 1,
            'item_detail_expand': 'all',
            'path': '/',
            'segments': 'drtv,optedin',
        }
        if area != 'drtv':
            data['path'] = '/' + area
        js = self.get_programcard(data['path'], data=data)
        items = [{'title': 'Programmer A-Å', 'path': A_AA[area], 'icon': 'all.png'}]
        for item in js['entries']:
            title = item['title']
            if title not in ['Se live tv']:
                if title == '' and item['type'] == 'ListEntry':
                    title = item['list'].get('title', '')  # get the top spinner item
                for HERO in ['DRTV Hero', 'Ramasjang: Hero', 'Ultra Hero']:
                    if title.startswith(HERO):
                        title = 'Daglige forslag'
                if title:
                    items.append({'title': title, 'path': item['list']['path']})
        return items

    def getLiveTV(self) -> list[dict]:
        channels = []
        schedules = self.get_channel_schedule_strings()
        for id in CHANNEL_IDS:
            card = self.get_programcard(f'/kanal/{id}')
            card['entries'][0]['schedule_str'] = schedules[id]
            channels += card['entries']
        return channels

    def recache_items(self, progress: Any = None, clear_expired: bool = False) -> None:
        if clear_expired:
            self.session.remove_expired_responses()
            (self.cachePath/'requests_cleaned').write_text(str(datetime.now()))

        js = self.get_programcard('/kategorier/a-aa')
        maxidx = len(js['entries']) + 3
        i = 0
        for item in js['entries']:
            if item['type'] == 'ListEntry':
                self.msg = f"{self.tr(30523)}'{item['title']}'\n"
                self.progress_prc = int(100 * (i + 1) / maxidx)
                try:
                    for sub_item in self.unfold_list(item['list'], progress=progress):
                        if self.fetch_full_plot:
                            if progress is not None:
                                if progress.iscanceled():
                                    return
                                progress.update(self.progress_prc, self.msg + 'updating descriptions...')
                            self.fix_item_description(sub_item)
                except Exception as e:
                    self._log_recache_error(f"'{item['title']}'", e)
            i += 1
        for channel in ['ramasjang', 'minisjang', 'ultra']:
            msg = f"{self.tr(30523)}'{channel}'\n"
            if progress is not None:
                if progress.iscanceled():
                    return
                progress.update(int(100*(i+1)/maxidx), msg)
            try:
                self.get_children_front_items(channel, progress=progress)
            except Exception as e:
                self._log_recache_error(channel, e)
            i += 1

    def _log_recache_error(self, what: str, exc: Exception) -> None:
        """Log a recache failure and let the crawl carry on with the next item."""
        if self.log is not None:
            self.log(f'recache: skipped {what}: {exc}')

    def get_children_front_items(self, channel: str, progress: Any = None) -> list[dict]:
        name = A_AA[channel]
        js = self.get_programcard(name)
        items = []
        for item in js['entries']:
            if item['type'] == 'ListEntry':
                items += self.unfold_list(item['list'], progress=progress)
        return items

    def get_stream(self, id: int) -> Optional[dict]:
        url = URL + f'/account/items/{int(id)}/videos?'
        headers = {"X-Authorization": f'Bearer {self.user_token()}'}
        data = {
            'delivery': 'stream',
            'device': 'web_browser',
            'ff': 'idp,ldp,rpt',
            'lang': 'da',
            'resolution': 'HD-1080',
            'sub': 'Registered',
        }
        # playback URLs carry signed tokens and must always be requested live,
        # never served from the request cache (while keeping the session's
        # retry adapter)
        with self.session.cache_disabled():
            u = self.session.get(url, params=data, headers=headers, timeout=GET_TIMEOUT)
            if u.status_code != 200:
                del data['sub']
                u = self.session.get(url, params=data, headers=headers, timeout=GET_TIMEOUT)

        if u.status_code == 200:
            for stream in u.json():
                if stream['accessService'] == 'StandardVideo':
                    stream['srt_subtitles'] = subtitles.handle_subtitle_vtts(
                        stream['subtitles'], self.cachePath, self.tr, self.session)
                    return stream
            return None
        else:
            raise ApiException(u.text)

    def get_livestream(self, path: str, with_subtitles: bool = False) -> dict:
        channel = self.get_programcard(path)['entries'][0]
        stream = {
            'subtitles': [],
            'url': self.get_channel_url(channel, with_subtitles)
            }
        return stream

    def get_channel_url(self, channel: dict, with_subtitles: bool = False, use_cache: bool = True) -> str:
        id = channel['item']['id']
        url = URL + f'/channels/{id}/liveStreams?'
        headers = {"X-Authorization": f'Bearer {self.profile_token()}'}
        js = self._request_get(url, headers=headers, use_cache=use_cache)
        links = {item['type']: item['link'] for item in js}

        EU = 'Eu' if 'hlsURLEu' in links else ''
        url = links['hlsWithSubtitlesURL' + EU] if with_subtitles else links['hlsURL' + EU]
        return url

    def get_title(self, item: dict) -> str:
        title = item['title']
        if item['type'] == 'season':
            title += f" {item['seasonNumber']}"
        elif item.get('contextualTitle'):
            cont = item['contextualTitle']
            if cont.count('.') >= 1 and cont.split('.', 1)[1].strip() not in title:
                title += f" ({item['contextualTitle']})"
        return title

    def fix_item_description(self, item: dict) -> dict:
        if len(item.get('shortDescription', '')) >= 255 and item.get('description', '') == '':
            resumetime_save = float(item.get('ResumeTime', 0.0))
            item = self.get_item(item['id'])
            if resumetime_save > 0:
                item['ResumeTime'] = resumetime_save
        return item

    def set_info(self, item: dict, tag: Any, title: str) -> None:
        if self.fetch_full_plot:
            item = self.fix_item_description(item)
        tag.setTitle(title)
        if item.get('shortDescription', '') and item['shortDescription'] != 'LinkItem':
            tag.setPlot(item['shortDescription'])
        if item.get('description', ''):
            tag.setPlot(item['description'])
        if item.get('tagline', ''):
            tag.setPlotOutline(item['tagline'])
        if item.get('customFields') and item['customFields'].get('BroadcastTimeDK'):
            broadcast = parser.parse(item['customFields']['BroadcastTimeDK'])
            tag.setFirstAired(broadcast.strftime('%Y-%m-%d'))
            tag.setYear(int(broadcast.strftime('%Y')))
        if item.get('seasonNumber'):
            tag.setSeason(int(item['seasonNumber']))
        if item.get('episodeNumber'):
            tag.setEpisode(int(item['episodeNumber']))
        if item['type'] in ["movie", "season", "episode"]:
            tag.setMediaType(item['type'])
        elif item['type'] == 'program':
            tag.setMediaType('tvshow')
        if item.get('ResumeTime', False):
            tag.setResumePoint(float(item['ResumeTime']))

    @staticmethod
    def _schedule_windows(duration: int) -> list[tuple[int, int]]:
        """Split a duration in hours into (day_offset, hours) windows of max 24h.

        Each window starts at the requested hour of the day, matching the
        pre-divmod behavior, and the total is capped at 7 days (a remainder
        that would need an 8th day is dropped).
        """
        days, remainder = divmod(duration, 24)
        if days >= 7:
            days, remainder = 7, 0
        windows = [(i, 24) for i in range(days)]
        if remainder:
            windows.append((days, remainder))
        return windows

    def get_schedules(self, channels: list[int] = CHANNEL_IDS, date: Optional[str] = None, hour: Optional[int] = None, duration: int = 6) -> list[dict]:
        url = URL + '/schedules?'
        now = datetime.now(timezone.utc)
        if date is None:
            date = now.strftime("%Y-%m-%d")
        if hour is None:
            hour = int(now.strftime("%H"))
        if duration <= 24:
            data = {
                'date': date,
                'hour': hour,
                'duration': duration,
                'channels': channels,
            }
            u = requests.get(url, params=data, timeout=GET_TIMEOUT)
            if u.status_code == 200:
                return u.json()
            else:
                raise ApiException(u.text)

        schedules = []
        for day_offset, hours in self._schedule_windows(duration):
            iter_date = (now + timedelta(days=day_offset)).strftime("%Y-%m-%d")
            schedules += self.get_schedules(channels=channels, date=iter_date, hour=hour, duration=hours)
        return schedules

    def get_channel_schedule_strings(self, channels: list[int] = CHANNEL_IDS) -> dict[int, str]:
        out = {}
        now = datetime.now(timezone.utc)
        for channel in self.get_schedules():
            id = int(channel['channelId'])
            out[id] = ''
            for item in channel['schedules']:
                if parser.parse(item['endDate']) > now and out[id].count('\n') < 5:
                    t = parser.parse(item['startTimeInDefaultTimeZone'])
                    start = t.strftime('%H:%M')
                    out[id] += f"{start} {item['item']['title']} \n"
        return out


class ApiException(Exception):
    pass
