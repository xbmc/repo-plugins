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
import pickle
import re
import requests
import requests_cache
import time
from dateutil import parser
from datetime import datetime, timezone, timedelta
from urllib.parse import urlparse, parse_qs, parse_qsl, urlencode
from requests.adapters import HTTPAdapter
from urllib3.util import Retry
import secrets
import base64

CHANNEL_IDS = [20875, 20876, 192099, 192100, 20892]
CHANNEL_PRESET = {
    'DR1': 1,
    'DR2': 2,
    'DR Ramasjang': 3,
    'TVA Live': 4,
    'DRTV Ekstra': 5
}
URL = 'https://production.dr-massive.com/api'
URL2 = 'https://prod95.dr-massive.com/api'
CLIENT_ID = "283ba39a2cf31d3b81e922b8"
GET_TIMEOUT = 10


def cache_path(path):
    NO_CACHING = ['/liste/drtv-hero']
    if any([path.startswith(item) for item in NO_CACHING]):
        return False
    return True


def fix_query(url, remove={}, add={}, remove_keys=[]):
    o = urlparse(url)
    qs = dict(parse_qsl(o.query))
    for k in remove_keys:
        if k in qs:
            del qs[k]
    for k,v in remove.items():
        if qs.get(k) == v:
            del qs[k]
    qs.update(add)
    qs = dict(sorted(qs.items()))
    return o._replace(query=urlencode(qs)).geturl()


def generate_code_verifier(length: int = 64) -> str:
    # Generate a secure random string (length between 43 and 128 chars)
    return secrets.token_urlsafe(length)[:length]


def generate_code_challenge(code_verifier: str) -> str:
    # SHA256 hash of the verifier, then base64-url encode without padding
    sha256 = hashlib.sha256(code_verifier.encode()).digest()
    return base64.urlsafe_b64encode(sha256).decode().rstrip('=')


def full_login(user, password):
    ses = requests.Session()

    # start login flow
    code_verifier = generate_code_verifier()
    code_challenge = generate_code_challenge(code_verifier)
    
    params = {
        "client_id": CLIENT_ID,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
        "redirect_uri": "https://www.dr.dk/drtv/callback",
        "state": f'{{"code_verifier":"{code_verifier}","logonRedirectPath":"/","optout":false}}',
        "response_type": "code",
        "scope": "openid roles tracking profile email offline_access"
    }
    res = ses.get('https://login.dr.dk/oidc/authorize', params=params)
    if res.status_code != 200:
        return {'status_code': res.status_code, 'error': res.text}

    trans = urlparse(res.url).path.split('/')[-1]
    headers = {'content-type': 'application/json'}

    transaction_fragment = "fragment useTransactionTransactionFragment on Transaction { ... on AuthenticatedAuthenticationTransaction { id email registration href __typename } ... on UnauthenticatedAuthenticationTransaction { id email __typename } ... on UnverifiedAuthenticationTransaction { id email name __typename } ... on UnrecognizedAuthenticationTransaction { id email statisticsConsentDefinition { id type version locale permissions headline summary body __typename } preferencesConsentDefinition { id type version locale permissions headline summary body __typename } newsletterConsentDefinition { id type version locale permissions headline summary body __typename } __typename } ... on UnidentifiedAuthenticationTransaction { id __typename } ... on CompletedEmailVerificationTransaction { id emailVerificationVariant: variant email __typename } ... on PendingEmailVerificationTransaction { id emailVerificationVariant: variant email __typename } ... on CompletedPasswordChangeTransaction { id passwordChangeVariant: variant __typename } ... on PendingPasswordChangeTransaction { id passwordChangeVariant: variant __typename } ... on PendingDeletionConfirmationTransaction { id __typename } ... on CompletedDeletionConfirmationTransaction { id __typename } ... on SettingsTransaction { id identity { id email name roles __typename } statisticsConsentDefinition { id type version locale permissions headline summary body __typename } preferencesConsentDefinition { id type version locale permissions headline summary body __typename } newsletterConsentDefinition { id type version locale permissions headline summary body __typename } statisticsConsentRevision { id status definition createdAt __typename } preferencesConsentRevision { id status definition createdAt __typename } newsletterConsentRevision { id status definition createdAt __typename } referBackUri referBackName sessionState expiresAt __typename } ... on PendingEUPTransaction { id href __typename } ... on CompletedEUPTransaction { id __typename } __typename }"  # noqa: E501
    trans_query = "query useTransactionTransactionQuery($id: ID!) { transaction(id: $id) { ... on Node { id __typename } ...useTransactionTransactionFragment  __typename } }" + transaction_fragment  # noqa: E501
    identify_query = "mutation useTransactionIdentificationMutation($input: IdentificationInput!) { identify(input: $input) { ... on Node { id __typename } ... on Error { code message __typename } ...useTransactionTransactionFragment __typename } } " + transaction_fragment  # noqa: E501
    authenticate_query = "mutation useTransactionAuthenticationMutation($input: AuthenticationInput!) { authenticate(input: $input) { ... on Node { id __typename } ... on Error { code message __typename } ...useTransactionTransactionFragment __typename } } " + transaction_fragment  # noqa: E501
    
    trans_data = {
        "operationName": "useTransactionTransactionQuery",
        "variables": {"id": trans}, "query": trans_query
    }
    identify_data = {
        "operationName": "useTransactionIdentificationMutation",
        "variables": {"input": {"transaction": trans, "email": user }}, "query": identify_query
    }
    authenticate_data = {
        "operationName": "useTransactionAuthenticationMutation",
        "variables": {"input": {"transaction": trans, "password": password }}, "query": authenticate_query
    }

    url = 'https://login.dr.dk/graphql'

    u1 = ses.post(url, json=trans_data, headers=headers)
    print(u1.json())
    u2 = ses.post(url, json=identify_data, headers=headers)
    print(u2.json())

    u3 = ses.post(url, json=authenticate_data, headers=headers)
    print(u3.json())

    res2 = ses.get(u3.json()['data']['authenticate']['href'])
    if res2.status_code != 200:
        return {'status_code': res2.status_code, 'error': res2.text}
    code = parse_qs(urlparse(res2.url).query)['code'][0]

    data = {
        "client_id": CLIENT_ID,
        "redirect_uri": "https://www.dr.dk/drtv/callback",
        "code_verifier": code_verifier, "code": code,
        "grant_type": "authorization_code",
    }
    return oidc_token(data)


def oidc_token(data):
    headers = {"Content-Type": "application/x-www-form-urlencoded", "Accept": "application/json"}
    res = requests.post('https://login.dr.dk/oidc/token', data=data, headers=headers)
    if res.status_code != 200:
        return {'status_code': res.status_code, 'error': res.text}
    return res.json()


def refresh_token(refresh_token):
    data = {"client_id": CLIENT_ID, "refresh_token": refresh_token, "grant_type": "refresh_token"}
    return oidc_token(data)


def exchange_token(tokens):
    data = {
        "accessToken": tokens['access_token'], "identityToken": tokens['id_token'],
        "scopes": ["Catalog"], "device": "web_browser", "optout": False,
    }
    
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    res = requests.post(URL + '/authorization/exchange', json=data, headers=headers)
    if res.status_code != 200:
        return {'status_code': res.status_code, 'error': res.text}
    return res.json()


def deviceid():
    v = int(Path(__file__).stat().st_mtime)
    h = hashlib.md5(str(v).encode('utf-8')).hexdigest()
    return '-'.join([h[:8], h[8:12], h[12:16], h[16:20], h[20:32]])


def anonymous_tokens():
    data = {"deviceId": deviceid(), "scopes": ["Catalog"], "optout": False}
    params = {'device': 'web_browser', 'ff': 'idp,ldp,rpt', 'lang': 'da', 'supportFallbackToken': True} 

    url = URL + '/authorization/anonymous-sso?'
    u = requests.post(url, json=data, params=params)
    if u.status_code != 200:
        return {'status_code': u.status_code, 'error': u.text}
    tokens = json.loads(u.content)
    return tokens

class Api():
    def __init__(self, cachePath, getLocalizedString, get_setting):
        self.cachePath = cachePath
        self.tr = getLocalizedString
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
        self.user = get_setting('drtv_username')
        self.password = get_setting('drtv_password')
        self._user_name = ''
        self.refresh_tokens()

    def init_sqlite_db(self):
        if not (self.cachePath/'requests_cleaned').exists():
            if (self.cachePath/'requests.cache.sqlite').exists():
                (self.cachePath/'requests.cache.sqlite').unlink()
        request_fname = str(self.cachePath/'requests.cache')
        self.session = requests_cache.CachedSession(
            request_fname, backend='sqlite', expire_after=self.expire_seconds)
        self.session.mount('https://', self.adapter)

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
                request_fname, backend='sqlite', expire_after=self.expire_seconds)
            self.session.mount('https://', self.adapter)
        (self.cachePath/'requests_cleaned').write_text(str(datetime.now()))

    def read_tokens(self, tokens):
        if 'value' in tokens[0]:
            #old flow, anonymous
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
        if self.access_tokens:
            self._user_name = self.get_profile()['name']

    def request_tokens(self):
        self._user_token = None
        self._profile_token = None

        if self.user:
            access_tokens = full_login(self.user, self.password)
            if 'error' in access_tokens:
                err = access_tokens['error']
                return err
            self.access_tokens = access_tokens
            tokens = exchange_token(access_tokens)
        else:
            tokens = anonymous_tokens()
        self.read_tokens(tokens)
        with self.token_file.open('wb') as fh:
            pickle.dump([tokens, self.access_tokens], fh)
        return None

    def refresh_tokens(self):
        if self._user_token is None:
            if self.token_file.exists():
                with self.token_file.open('rb') as fh:
                    [tokens, self.access_tokens] = pickle.load(fh)
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
            # oidc flow
            access_tokens = refresh_token(self.access_tokens['refresh_token'])
            if 'error' in access_tokens:
                failed_refresh = True
            else:
                tokens = exchange_token(access_tokens)
                self.access_tokens = access_tokens

            if failed_refresh:
                self.request_tokens()
                err = self.request_tokens()
                if err:
                    raise ApiException(f'Login failed with: "{err}"')
            else:
                self.read_tokens(tokens)
                with self.token_file.open('wb') as fh:
                    pickle.dump([tokens, self.access_tokens], fh)

    def user_token(self):
        self.refresh_tokens()
        return self._user_token

    def profile_token(self):
        self.refresh_tokens()
        return self._profile_token

    def _request_get(self, url, params=None, headers=None, use_cache=True):
        if use_cache and self.caching:
            u = self.session.get(url, params=params, headers=headers, timeout=GET_TIMEOUT)
        else:
            u = requests.get(url, params=params, headers=headers, timeout=GET_TIMEOUT)

        if u.status_code == 200:
            return u.json()
        else:
            raise ApiException(u.text)

    def get_programcard(self, path, data=None, use_cache=True):
        url = URL + '/page?'
        if data is None:
            data = {
                'item_detail_expand': 'all',
                'list_page_size': '24',
                'max_list_prefetch': '3',
                'path': path,
            }
        return self._request_get(url, params=data, use_cache=use_cache)

    def get_item(self, id, use_cache=True):
        url = URL + f'/items/{int(id)}?'
        return self._request_get(url)

    def get_next(self, path, use_cache=True, headers=None):
        remove = {'sub':'Emergency'}
        remove_keys = ['lang', 'segments', 'isDeviceAbroad', 'isLive2VodSupported']
        url = URL + fix_query(path, remove=remove, remove_keys=remove_keys)
        return self._request_get(url, headers=headers, use_cache=use_cache)

    def get_list(self, id, param, use_cache=True):
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

    def get_recommendations(self, id, use_cache=True, param=[]):
        url = URL + f'/recommendations/{id}'
        data = {'page_size': '24'}
        if param:
            data['param'] = param
        headers = {"X-Authorization": f'Bearer {self.profile_token()}'}
        return self._request_get(url, params=data, headers=headers, use_cache=use_cache)

    def delete_from_watched(self, id):
        url = f'{URL}/account/profile/continue-watching/{id}'
        headers = {"X-Authorization": f'Bearer {self.profile_token()}'}
        u = self.session.delete(url, headers=headers)
        if u.status_code != 204:
            raise ApiException(u.text)

    def add_to_watched(self, id, duration):
        url = f'{URL}/account/profile/continue-watching/{id}&position={int(duration)}'
        headers = {"X-Authorization": f'Bearer {self.profile_token()}'}
        u = self.session.put(url, headers=headers)
        if u.status_code != 200:
            raise ApiException(u.text)

    def delete_from_mylist(self, id):
        url = f'{URL}/account/profile/bookmarks/{id}'
        headers = {"X-Authorization": f'Bearer {self.profile_token()}'}
        u = self.session.delete(url, headers=headers)
        if u.status_code != 204:
            raise ApiException(u.text)

    def add_to_mylist(self, id):
        url = f'{URL}/account/profile/bookmarks/{id}'
        headers = {"X-Authorization": f'Bearer {self.profile_token()}'}
        u = self.session.put(url, headers=headers)
        if u.status_code != 200:
            raise ApiException(u.text)

    def get_mylist(self, use_cache=False):
        url = URL + '/account/profile/bookmarks/list'
        data = {'page_size': '24'}
        headers = {"X-Authorization": f'Bearer {self.profile_token()}'}
        item = self._request_get(url, params=data, headers=headers, use_cache=use_cache)
        items = self.unfold_list(item, headers=headers)
        for item in items:
            item['in_mylist'] = True
        return items

    def get_continue(self, use_cache=False):
        url = URL + '/account/profile/continue-watching/list'
        data = {'page_size': '24'}
        headers = {"X-Authorization": f'Bearer {self.profile_token()}'}
        item = self._request_get(url, params=data, headers=headers, use_cache=use_cache)
        items = self.unfold_list(item, headers=headers)
        watched = self.get_profile()['watched']
        for item in items:
            item['ResumeTime'] = float(watched.get(str(item['id']), {'position':0.0})['position'])
        return items

    def get_profile(self, use_cache=False):
        url = URL + '/account/profile'
        headers = {'X-Authorization': 'Bearer ' + self.profile_token()}
        params = {"ff": "idp,ldp,rpt", "lang": "da"}
        return self._request_get(url, headers=headers, params=params, use_cache=use_cache)

    def kids_item(self, item):
        if 'classification' in item:
            if item['classification']['code'] in ['DR-Ramasjang', 'DR-Minisjang']:
                return True
        if 'categories' in item:
            for cat in ['dr minisjang', 'dr ramasjang']:
                if cat in item['categories']:
                    return True
        return False

    def unfold_list(self, item, filter_kids=False, headers=None, progress=None):
        items = item['items']
        if 'next' in item['paging']:
            if progress is not None:
                if progress.iscanceled():
                    return items
                progress.update(self.progress_prc, self.msg + f"page {item['paging']['page']} of {item['paging']['total']}")

            next_js = self.get_next(item['paging']['next'], headers=headers)
            items += next_js['items']
            while 'next' in next_js['paging']:
                if progress is not None:
                    if progress.iscanceled():
                        return items
                    progress.update(self.progress_prc, self.msg + f"page {next_js['paging']['page']} of {next_js['paging']['total']}")
                next_js = self.get_next(next_js['paging']['next'], headers=headers)
                items += next_js['items']
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
            segments='drtv,optedin',
        )
        js = self.get_programcard('/', data=data)
        items = [{'title': 'Programmer A-Å', 'path': '/kategorier/a-aa', 'icon': 'all.png'}]
        for item in js['entries']:
            title = item['title']
            if title not in ['Se live tv']:
                if title == '' and item['type'] == 'ListEntry':
                    title = item['list'].get('title', '') # get the top spinner item
                if title.startswith('DRTV Hero'):
                    title = 'Daglige forslag'
                if title:
                    items.append({'title': title, 'path': item['list']['path']})
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

        js = self.get_programcard('/kategorier/a-aa')
        maxidx = len(js['entries']) + 3
        i = 0
        for item in js['entries']:
            if item['type'] == 'ListEntry':
                self.msg = f"{self.tr(30523)}'{item['title']}'\n"
                self.progress_prc = int(100 * (i + 1) / maxidx)
                for sub_item in self.unfold_list(item['list'], progress=progress):
                    if self.fetch_full_plot:
                        if progress is not None:
                            if progress.iscanceled():
                                return
                            progress.update(self.progress_prc, self.msg + 'updating descriptions...')
                        self.fix_item_description(sub_item)
            i += 1
        for channel in ['dr-ramasjang', 'dr-minisjang', 'dr-ultra']:
            msg = f"{self.tr(30523)}'{channel}'\n"
            if progress is not None:
                if progress.iscanceled():
                    return
                progress.update(int(100*(i+1)/maxidx), msg)
            self.get_children_front_items(channel)
            i += 1

    def get_children_front_items(self, channel):
        names = {
            'dr-ramasjang': '/ramasjang_a-aa',
            'dr-minisjang': '/minisjang/a-aa',
            'dr-ultra': '/ultra_a-aa',
            'dr': '/kategorier/a-aa',
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
            'sub': 'Registered',
        }
        u = self.session.get(url, params=data, headers=headers, timeout=GET_TIMEOUT)
        if u.status_code != 200:
            del data['sub']
            u = self.session.get(url, params=data, headers=headers, timeout=GET_TIMEOUT)

        if u.status_code == 200:
            for stream in u.json():
                if stream['accessService'] == 'StandardVideo':
                    stream['srt_subtitles'] = self.handle_subtitle_vtts(stream['subtitles'])
                    return stream
            return None
        else:
            raise ApiException(u.text)

    def handle_subtitle_vtts(self, subs):
        subtitlesUri = []
        for sub in subs:
            if sub['language'] in ['DanishLanguageSubtitles', 'CombinedLanguageSubtitles']:
                name = f'{self.cachePath}/{self.tr(30050)}.da.srt'
            else:
                name = f'{self.cachePath}/{self.tr(30051)}.da.srt'
            u = self.session.get(sub['link'], timeout=10)
            if u.status_code != 200:
                u.close()
                break
            srt = self.vtt2srt(u.content)
            with open(name.encode('utf-8'), 'wb') as fh:
                fh.write(srt.encode('utf-8'))
            u.close()
            subtitlesUri.append(name)
        return subtitlesUri

    def vtt2srt(self, vtt):
        if isinstance(vtt, bytes):
            vtt = vtt.decode('utf-8')
        srt = vtt.replace("\r\n", "\n")
        srt = re.sub(r'([\d]+)\.([\d]+)', r'\1,\2', srt)
        srt = re.sub(r'WEBVTT\n\n', '', srt)
        srt = re.sub(r'^\d+\n', '', srt)
        srt = re.sub(r'\n\d+\n', '\n', srt)
        srt = re.sub(r'\n([\d]+)', r'\nputINDEXhere\n\1', srt)

        srtout = ['1']
        idx = 2
        for line in srt.splitlines():
            if line == 'putINDEXhere':
                line = str(idx)
                idx += 1
            srtout.append(line)
        return '\n'.join(srtout)

    def get_livestream(self, path, with_subtitles=False):
        channel = self.get_programcard(path)['entries'][0]
        stream = {
            'subtitles': [],
            'url': self.get_channel_url(channel, with_subtitles)
            }
        return stream

    def get_channel_url(self, channel, with_subtitles=False, use_cache=True):
        id = channel['item']['id']
        url = URL + f'/channels/{id}/liveStreams?'
        headers = {"X-Authorization": f'Bearer {self.profile_token()}'}
        js = self._request_get(url, headers=headers, use_cache=use_cache)
        links = {item['type']:item['link'] for item in js}

        EU = 'Eu' if 'hlsURLEu' in links else ''
        if with_subtitles:
            url = links['hlsWithSubtitlesURL' + EU]
        else:
            url = links['hlsURL' + EU]
        return url

    def get_title(self, item):
        title = item['title']
        if item['type'] == 'season':
            title += f" {item['seasonNumber']}"
        elif item.get('contextualTitle', None):
            cont = item['contextualTitle']
            if cont.count('.') >= 1 and cont.split('.', 1)[1].strip() not in title:
                title += f" ({item['contextualTitle']})"
        return title

    def fix_item_description(self, item):
        if len(item.get('shortDescription', '')) >= 255 and item.get('description', '') == '':
            resumetime_save = float(item.get('ResumeTime', 0.0))
            item = self.get_item(item['id'])
            if resumetime_save > 0:
                item['ResumeTime'] = resumetime_save
        return item

    def set_info(self, item, tag, title):
        if self.fetch_full_plot:
            item = self.fix_item_description(item)
        tag.setTitle(title)
        if item.get('shortDescription', '') and item['shortDescription'] != 'LinkItem':
            tag.setPlot(item['shortDescription'])
        if item.get('description', ''):
            tag.setPlot(item['description'])
        if item.get('tagline', ''):
            tag.setPlotOutline(item['tagline'])
        if item.get('customFields'):
            if item['customFields'].get('BroadcastTimeDK'):
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

    def get_schedules(self, channels=CHANNEL_IDS, date=None, hour=None, duration=6):
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
        for i in range(1, 8):
            iter_date = (now + timedelta(days=i-1)).strftime("%Y-%m-%d")
            if i*24 > duration:
                hours = duration % ((i-1)*24)
                if hours != 0:
                    schedules += self.get_schedules(channels=channels, date=iter_date, hour=hour, duration=hours)
                break
            else:
                schedules += self.get_schedules(channels=channels, date=iter_date, hour=hour, duration=24)
        return schedules

    def get_channel_schedule_strings(self, channels=CHANNEL_IDS):
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
