# -*- coding: utf-8 -*-
"""
     
    Copyright (C) 2012-2019 Twitch-on-Kodi
    
    This file is part of Twitch-on-Kodi (plugin.video.twitch)

    SPDX-License-Identifier: GPL-3.0-only
    See LICENSES/GPL-3.0-only for more information.
"""

import re
import time
import os
import json as _json

try:
    import fcntl as _fcntl
except ImportError:
    _fcntl = None

from base64 import b64decode
from datetime import datetime
from urllib.parse import quote_plus

from .common import kodi, json_store, log_utils
from .strings import STRINGS
from .constants import CLIENT_ID, REDIRECT_URI, LIVE_PREVIEW_TEMPLATE, Images, ADDON_DATA_DIR, COLORS, Keys
from .search_history import StreamsSearchHistory, ChannelsSearchHistory, GamesSearchHistory, IdUrlSearchHistory

from twitch.api.parameters import Boolean, Period, ClipPeriod, Direction, Language, SortBy, VideoSort

import xbmcvfs

translations = kodi.Translations(STRINGS)
i18n = translations.i18n

if not xbmcvfs.exists(ADDON_DATA_DIR):
    mkdir_result = xbmcvfs.mkdir(ADDON_DATA_DIR)
storage = json_store.JSONStore(ADDON_DATA_DIR + 'storage.json')


def show_menu(menu, parent=None):
    setting_id = 'menu'
    if parent:
        setting_id += '_%s' % parent
    setting_id += '_%s' % menu
    return kodi.get_setting(setting_id) == 'true'


def to_string(value):
    return kodi.decode_utf8(value)


def loose_version(v):
    filled = []
    for point in v.split("."):
        filled.append(point.zfill(8))
    return tuple(filled)


def use_inputstream_adaptive():
    if kodi.get_setting('video_quality_ia') == 'true' or kodi.get_setting('video_quality') == '3':
        if kodi.get_setting('video_support_ia_builtin') == 'true':
            return True
        elif kodi.get_setting('video_support_ia_addon') == 'true':
            use_ia = kodi.get_setting('video_quality_ia') == 'true' or kodi.get_setting('video_quality') == '3'
            if not use_ia:
                return False

            ia_enabled = kodi.addon_enabled('inputstream.adaptive')
            if ia_enabled is False:
                if kodi.Dialog().yesno(kodi.get_name(), i18n('adaptive_is_disabled')):
                    ia_enabled = kodi.set_addon_enabled('inputstream.adaptive')

            if ia_enabled:
                ia_min_version = '2.0.10'
                ia_version = kodi.Addon('inputstream.adaptive').getAddonInfo('version')
                ia_enabled = loose_version(ia_version) >= loose_version(ia_min_version)
                if not ia_enabled:
                    result = kodi.Dialog().ok(kodi.get_name(), i18n('adaptive_version_check') % ia_min_version)

            if not ia_enabled:
                kodi.set_setting('video_quality_ia', 'false')
                kodi.set_setting('video_quality', '0')
                return False
            else:
                return True
        else:
            kodi.set_setting('video_quality_ia', 'false')
            kodi.set_setting('video_quality', '0')
            return False
    else:
        return False


def inputstream_adpative_supports(feature):
    try:
        ia_version = kodi.Addon('inputstream.adaptive').getAddonInfo('version')
    except RuntimeError:
        ia_version = '0.0.0'

    if feature == 'EXT-X-DISCONTINUITY':
        if loose_version(ia_version) >= loose_version('2.4.6'):
            return True

    # Kodi 21 detects the manifest type itself and warns that the property is deprecated;
    # Kodi 22 drops it entirely. Older versions still need it, so it is set conditionally.
    if feature == 'MANIFEST_TYPE_DETECTION':
        if loose_version(ia_version) >= loose_version('21.0.0'):
            return True

    return False


def format_isa_headers(headers):
    # key=value&... (url-encoded) for InputStream Adaptive stream_headers / manifest_headers properties.
    return '&'.join(['%s=%s' % (key, quote_plus(headers[key])) for key in headers])


def append_headers(headers):
    return '|%s' % format_isa_headers(headers)


# supported_codecs setting -> usher 'supported_codecs' value. Index 0 = Twitch default (omit param).
SUPPORTED_CODECS = ('', 'h265,h264')


def get_supported_codecs():
    try:
        return SUPPORTED_CODECS[int(kodi.get_setting('supported_codecs'))]
    except (ValueError, IndexError):
        return ''


# Drop sub-720p video variants from a usher quality list; keep Source/720p+/audio_only/Adaptive.
QUALITY_FLOOR_DROP = ('160p', '360p', '480p')


def filter_qualities(videos):
    if not videos:
        return videos
    filtered = [v for v in videos
                if not any(drop in v.get('name', '').lower() for drop in QUALITY_FLOOR_DROP)]
    return filtered if filtered else videos  # never return empty -> fall back to original list


def get_redirect_uri():
    settings_id = kodi.get_setting('oauth_redirecturi')
    stripped_id = settings_id.strip()
    if settings_id != stripped_id:
        settings_id = stripped_id
        kodi.set_setting('oauth_redirecturi', settings_id)
    if settings_id:
        return kodi.decode_utf8(settings_id)
    else:
        return kodi.decode_utf8(REDIRECT_URI)


def get_client_id(default=False):
    settings_id = kodi.get_setting('oauth_clientid')
    stripped_id = settings_id.strip()
    if settings_id != stripped_id:
        settings_id = stripped_id
        kodi.set_setting('oauth_clientid', settings_id)
    if settings_id and not default:
        return kodi.decode_utf8(settings_id)
    else:
        return kodi.decode_utf8(b64decode(CLIENT_ID))


def get_private_client_id():
    settings_id = kodi.get_setting('private_oauth_clientid')
    stripped_id = settings_id.strip()
    if settings_id != stripped_id:
        settings_id = stripped_id
        kodi.set_setting('private_oauth_clientid', settings_id)
    if not settings_id:
        return ""
    return kodi.decode_utf8(settings_id)


def get_oauth_token(token_only=True, required=False):
    oauth_token = _read_oauth_store().get('access', '')
    if not oauth_token or not oauth_token.strip():
        oauth_token = kodi.get_setting('oauth_token_helix')  # legacy fallback (manual entry)
    if not oauth_token or not oauth_token.strip():
        if not required: return ''
        kodi.notify(kodi.get_name(), i18n('token_required'), sound=False)
        kodi.show_settings()
        oauth_token = _read_oauth_store().get('access', '') or kodi.get_setting('oauth_token_helix')
    oauth_token = oauth_token.strip()
    if oauth_token:
        if token_only:
            idx = oauth_token.find(':')
            if idx >= 0:
                oauth_token = oauth_token[idx + 1:]
        else:
            if not oauth_token.lower().startswith('oauth:'):
                idx = oauth_token.find(':')
                if idx >= 0:
                    oauth_token = oauth_token[idx + 1:]
                oauth_token = 'oauth:{0}'.format(oauth_token)
    return kodi.decode_utf8(oauth_token)


def get_private_oauth_token():
    # Prefer the device-login store (Turbo/ad-free, auto-refreshed); fall back to the manual
    # `private_oauth_token` setting so an existing long-lived token keeps working.
    if (_read_private_store().get('access') or '').strip():
        token = ensure_valid_private_token()
        if token:
            return kodi.decode_utf8(token)
    settings_id = kodi.get_setting('private_oauth_token')
    stripped_id = settings_id.strip()
    if settings_id != stripped_id:
        settings_id = stripped_id
        kodi.set_setting('private_oauth_token', settings_id)
    if not settings_id:
        return ""
    return kodi.decode_utf8(settings_id)


# --- OAuth Device Code Flow: token storage + silent refresh -----------------------------
#
# The rotating, single-use refresh token must survive two hazards the Kodi settings store
# cannot: (a) concurrent refreshes from several add-on processes (service + plugin calls)
# racing to consume the same single-use token, and (b) one process clobbering another's
# settings.xml write from its in-memory cache. Both are solved by keeping the tokens in a
# dedicated JSON file that is read fresh every time, written atomically (os.replace), and
# guarded by a cross-process file lock for the whole refresh.

_OAUTH_STORE_FILE = os.path.join(ADDON_DATA_DIR, 'oauth_tokens.json')
_OAUTH_LOCK_FILE = os.path.join(ADDON_DATA_DIR, 'oauth_tokens.lock')


class _OAuthLock:
    """Serialise token refresh across processes (flock on POSIX; no-op fallback elsewhere)."""

    def __init__(self, lock_file=_OAUTH_LOCK_FILE):
        self._fh = None
        self._lock_file = lock_file

    def __enter__(self):
        if _fcntl is not None:
            try:
                self._fh = open(self._lock_file, 'a+')
                _fcntl.flock(self._fh.fileno(), _fcntl.LOCK_EX)
            except Exception as e:
                log_utils.log('OAuth: lock acquire failed: %s' % e, log_utils.LOGWARNING)
                self._fh = None
        return self

    def __exit__(self, *exc):
        if self._fh is not None:
            try:
                _fcntl.flock(self._fh.fileno(), _fcntl.LOCK_UN)
                self._fh.close()
            except Exception:
                pass
            self._fh = None
        return False


def _read_oauth_store():
    """Token dict {access, refresh, expiry}, read fresh from disk (never cached). Migrates
    once from the legacy Kodi settings so existing logins keep working. Never logs values."""
    data = {}
    try:
        if os.path.exists(_OAUTH_STORE_FILE):
            with open(_OAUTH_STORE_FILE, 'r') as fh:
                data = _json.load(fh) or {}
    except Exception as e:
        log_utils.log('OAuth: store read failed: %s' % e, log_utils.LOGWARNING)
        data = {}
    if not data.get('access') and not data.get('refresh'):
        access = (kodi.get_setting('oauth_token_helix') or '').strip()
        refresh = (kodi.get_setting('oauth_refresh_token') or '').strip()
        try:
            expiry = int(float(kodi.get_setting('oauth_token_expiry') or '0'))
        except (TypeError, ValueError):
            expiry = 0
        if access or refresh:
            data = {'access': access, 'refresh': refresh, 'expiry': expiry}
            _write_oauth_store(data)
    return data


def _write_oauth_store(data):
    """Atomically persist the token dict, then mirror it to the legacy settings for backward
    compatibility (the mirror is never read back for refresh, so a clobber is harmless). Never
    logs token values."""
    try:
        tmp = _OAUTH_STORE_FILE + '.tmp'
        with open(tmp, 'w') as fh:
            _json.dump(data, fh)
        os.replace(tmp, _OAUTH_STORE_FILE)
    except Exception as e:
        log_utils.log('OAuth: store write failed: %s' % e, log_utils.LOGERROR)
        return False
    try:
        kodi.set_setting('oauth_token_helix', data.get('access', ''))
        kodi.set_setting('oauth_refresh_token', data.get('refresh', ''))
        kodi.set_setting('oauth_token_expiry', str(int(data.get('expiry', 0) or 0)))
    except Exception:
        pass
    return True


def get_refresh_token():
    return (_read_oauth_store().get('refresh') or '').strip()


def store_oauth_tokens(access_token, refresh_token, expires_in):
    try:
        expiry = int(time.time()) + int(expires_in) - 120  # refresh ~2 min before expiry
    except (TypeError, ValueError):
        expiry = int(time.time()) + 3600
    _write_oauth_store({'access': (access_token or '').strip(),
                        'refresh': (refresh_token or '').strip(),
                        'expiry': expiry})
    kodi.set_setting('oauth_refresh_unsupported', '')  # fresh working tokens -> (re)enable auto-refresh


def clear_oauth_tokens():
    _write_oauth_store({'access': '', 'refresh': '', 'expiry': 0})


def ensure_valid_token(force=False):
    """Silently refresh the Helix OAuth token via the stored refresh_token when it is
    (near) expired. No-op for legacy implicit tokens (no refresh_token stored). Serialised
    across processes so the single-use refresh token is never consumed twice. Returns the
    (possibly refreshed) access token, or '' if none available."""
    from . import device_oauth
    client_id = get_client_id()
    # A confidential app (one registered with a secret) cannot refresh without that secret;
    # Twitch then replies 'missing client secret'. Once we have seen that for this client id we
    # stop retrying, so we neither spam the log every few minutes nor block API calls -> the user
    # falls back to the manual login until they configure a public client id.
    if not force and kodi.get_setting('oauth_refresh_unsupported') == client_id:
        return (_read_oauth_store().get('access') or '').strip()
    with _OAuthLock():
        store = _read_oauth_store()
        refresh_token = (store.get('refresh') or '').strip()
        access_token = (store.get('access') or '').strip()
        if not refresh_token:
            return access_token  # legacy implicit-grant token -> nothing to refresh
        try:
            expiry = float(store.get('expiry') or 0)
        except (TypeError, ValueError):
            expiry = 0
        # Re-check INSIDE the lock: if another process refreshed while we waited, the store
        # is now fresh -> reuse it instead of consuming the rotated token a second time.
        if access_token and not force and time.time() < expiry:
            return access_token
        ok, data = device_oauth.refresh_access_token(client_id, refresh_token)
        if ok and data.get('access_token'):
            store_oauth_tokens(data['access_token'], data.get('refresh_token', refresh_token),
                               data.get('expires_in', 3600))
            log_utils.log('OAuth: access token refreshed via refresh_token', log_utils.LOGNOTICE)
            return data['access_token']
        if 'client secret' in str(data.get('message', '')).lower():
            # Confidential client id -> a silent refresh is impossible. Remember it, and tell the
            # user once how to fix it (register a public app and set its Client-ID).
            kodi.set_setting('oauth_refresh_unsupported', client_id)
            log_utils.log('OAuth: refresh needs a public client id (this one is confidential); set your own '
                          'under Settings > Login. Falling back to manual login.', log_utils.LOGWARNING)
            kodi.notify(msg=i18n('oauth_refresh_needs_public_client'))
            return access_token
        log_utils.log('OAuth: token refresh failed |%s|' % (data.get('message') or data.get('error') or 'error'),
                      log_utils.LOGWARNING)  # log only the reason, never token values
        return access_token  # keep current; valid_token() will prompt re-login if truly invalid


# --- Private (Turbo/ad-free) OAuth token store -- device login + silent refresh ----------
#
# Mirrors the main store above but for the "private" credentials used by usher/GQL
# (Turbo/subscriber ad-free playback). Separate file from the main (login/Helix) token and
# additive: get_private_oauth_token() prefers this store (auto-refreshed) and falls back to
# the manual `private_oauth_token` setting, so an existing long-lived token keeps working.

_PRIVATE_STORE_FILE = os.path.join(ADDON_DATA_DIR, 'oauth_private_tokens.json')
_PRIVATE_LOCK_FILE = os.path.join(ADDON_DATA_DIR, 'oauth_private_tokens.lock')

_KIMNE_CLIENT_ID = 'kimne78kx3ncx6brgo4mv6wki5h1ko'  # Twitch public web client (Turbo-aware GQL)


def effective_private_client_id():
    return get_private_client_id() or _KIMNE_CLIENT_ID


def _read_private_store():
    try:
        if os.path.exists(_PRIVATE_STORE_FILE):
            with open(_PRIVATE_STORE_FILE, 'r') as fh:
                return _json.load(fh) or {}
    except Exception as e:
        log_utils.log('OAuth(private): store read failed: %s' % e, log_utils.LOGWARNING)
    return {}


def _write_private_store(data):
    try:
        tmp = _PRIVATE_STORE_FILE + '.tmp'
        with open(tmp, 'w') as fh:
            _json.dump(data, fh)
        os.replace(tmp, _PRIVATE_STORE_FILE)
    except Exception as e:
        log_utils.log('OAuth(private): store write failed: %s' % e, log_utils.LOGERROR)
        return False
    return True


def store_private_tokens(access_token, refresh_token, expires_in):
    try:
        expiry = int(time.time()) + int(expires_in) - 120  # refresh ~2 min before expiry
    except (TypeError, ValueError):
        expiry = int(time.time()) + 3600
    _write_private_store({'access': (access_token or '').strip(),
                          'refresh': (refresh_token or '').strip(),
                          'expiry': expiry})


def clear_private_tokens():
    _write_private_store({'access': '', 'refresh': '', 'expiry': 0})


def ensure_valid_private_token(force=False):
    """Refresh the private (Turbo) token via its stored refresh_token when (near)
    expired. No-op if no refresh_token (e.g. legacy long-lived token). Serialised across
    processes. Never logs token values."""
    from . import device_oauth
    with _OAuthLock(_PRIVATE_LOCK_FILE):
        store = _read_private_store()
        refresh_token = (store.get('refresh') or '').strip()
        access_token = (store.get('access') or '').strip()
        if not refresh_token:
            return access_token
        # The kimne78 web client is a *confidential* client: its tokens cannot be refreshed
        # without a client secret we don't have (-> "missing client secret"), but they also
        # never expire (Twitch /validate reports expires_in=0). Our stored expiry is just the
        # device-flow expires_in, which lapses while the token stays valid -> attempting a
        # refresh here only spams a doomed HTTP POST + warning on every API call. So for
        # kimne78 just use the stored access token. Only a user-supplied *public* private
        # client (own client id) is actually refreshable.
        if effective_private_client_id() == _KIMNE_CLIENT_ID:
            return access_token
        try:
            expiry = float(store.get('expiry') or 0)
        except (TypeError, ValueError):
            expiry = 0
        if access_token and not force and time.time() < expiry:
            return access_token
        ok, data = device_oauth.refresh_access_token(effective_private_client_id(), refresh_token)
        if ok and data.get('access_token'):
            store_private_tokens(data['access_token'], data.get('refresh_token', refresh_token),
                                 data.get('expires_in', 3600))
            log_utils.log('OAuth(private): token refreshed via refresh_token', log_utils.LOGNOTICE)
            return data['access_token']
        # Token (near) expired and refresh failed -> signal invalid so get_private_oauth_token()
        # falls back to the manual long-lived private_oauth_token instead of using a dead token.
        log_utils.log('OAuth(private): token refresh failed |%s|' % (data.get('message') or data.get('error') or 'error'),
                      log_utils.LOGWARNING)  # log only the reason, never token values
        return ''


def get_search_history_size():
    return int(kodi.get_setting('search_history_size'))


def use_gql_search():
    # search_backend: 0 = Website (GQL, fuzzy/relevance ranking), 1 = Helix (search/channels)
    try:
        return int(kodi.get_setting('search_backend')) == 0
    except (ValueError, TypeError):
        return True  # default to the website (GQL) search


def get_search_history(search_type):
    history = None
    history_size = get_search_history_size()
    if history_size > 0:
        if search_type == 'streams':
            history = StreamsSearchHistory(max_items=history_size)
        elif search_type == 'channels':
            history = ChannelsSearchHistory(max_items=history_size)
        elif search_type == 'games':
            history = GamesSearchHistory(max_items=history_size)
        elif search_type == 'id_url':
            history = IdUrlSearchHistory(max_items=history_size)
    return history


def get_items_per_page():
    return int(kodi.get_setting('items_per_page'))


def get_thumbnail_size():
    size_map = [Keys.SOURCE, Keys.LARGE, Keys.MEDIUM, Keys.SMALL]
    return size_map[int(kodi.get_setting('thumbnail_size'))]


def get_vodcast_color():
    color = int(kodi.get_setting('vodcast_highlight'))
    color = COLORS.split('|')[color]
    return kodi.decode_utf8(color)


def the_art(art=None):
    if not art:
        art = {}
    return {'icon': art.get('icon', Images.ICON),
            'thumb': art.get('thumb', Images.THUMB),
            'poster': art.get('poster', Images.POSTER),
            'banner': art.get('banner', Images.BANNER),
            'fanart': art.get('fanart', Images.FANART),
            'clearart': art.get('clearart', Images.CLEARART),
            'clearlogo': art.get('clearlogo', Images.CLEARLOGO),
            'landscape': art.get('landscape', Images.LANDSCAPE)}


def link_to_next_page(queries):
    return {'label': i18n('next_page'),
            'art': the_art(),
            'path': kodi.get_plugin_url(queries),
            'info': {'plot': i18n('next_page')}}


def notify_refresh():
    if kodi.get_setting('notify_refresh') == 'false':
        return False
    return True


def refresh_previews():
    refresh_interval = int(kodi.get_setting('refresh_interval')) * 60
    if refresh_interval > 0:
        if not get_refresh_stamp():
            set_refresh_stamp()
            return
        if get_refresh_diff() >= refresh_interval:
            set_refresh_stamp()
    else:
        clear_refresh_stamp()


def clear_refresh_stamp():
    window = kodi.Window(10000)
    window.clearProperty(key='%s-lpr_stamp' % kodi.get_id())


def set_refresh_stamp():
    window = kodi.Window(10000)
    window.setProperty(key='%s-lpr_stamp' % kodi.get_id(), value=str(datetime.now()))


def get_refresh_stamp():
    window = kodi.Window(10000)
    return window.getProperty(key='%s-lpr_stamp' % kodi.get_id())


def strptime(stamp, stamp_fmt):
    import _strptime
    try:
        time.strptime('01 01 2012', '%d %m %Y')  # dummy call
    except:
        pass
    return time.strptime(stamp, stamp_fmt)


def get_stamp_diff(current_stamp):
    stamp_format = '%Y-%m-%d %H:%M:%S.%f'
    current_datetime = datetime.now()
    if not current_stamp: return 86400  # 24 hrs
    try:
        stamp_datetime = datetime(*(strptime(current_stamp, stamp_format)[0:6]))
    except ValueError:  # current_stamp has no microseconds
        stamp_format = '%Y-%m-%d %H:%M:%S'
        stamp_datetime = datetime(*(strptime(current_stamp, stamp_format)[0:6]))

    time_delta = current_datetime - stamp_datetime
    total_seconds = 0
    if time_delta:
        total_seconds = ((time_delta.seconds + time_delta.days * 24 * 3600) * 10 ** 6) / 10 ** 6
    return total_seconds


def get_refresh_diff():
    return get_stamp_diff(get_refresh_stamp())


def extract_video(url):
    video_id = None
    seek_time = 0
    id_string = url  # http://twitch.tv/a/v/12345678?t=9m1s
    idx = id_string.find('?')
    if idx >= 0:
        id_string = id_string[:idx]  # https://twitch.tv/a/v/12345678
    idx = id_string.rfind('/')
    if idx >= 0:
        id_string = id_string[:idx] + id_string[idx + 1:]  # https://twitch.tv/a/v12345678
    idx = id_string.rfind('/')
    if idx >= 0:
        id_string = id_string[idx + 1:]  # v12345678
    if id_string.startswith("videos"):  # videos12345678
        id_string = "v" + id_string[6:]  # v12345678
    start_time = url  # http://twitch.tv/a/v/12345678?t=9m1s
    idx = url.find('?')
    if idx >= 0:
        time_string = start_time[idx:]  # t=9m1s
        pattern = re.compile('t=(?:(?P<hours>[0-9]+)(?:h))?(?:(?P<minutes>[0-9]+)(?:m))?(?:(?P<seconds>[0-9]+)(?:s))?')
        match = re.search(pattern, time_string)
        if match:
            hours = match.group('hours')
            minutes = match.group('minutes')
            seconds = match.group('seconds')
            if hours:
                seek_time += int(hours) * 3600
            if minutes:
                seek_time += int(minutes) * 60
            if seconds:
                seek_time += int(seconds)

    return id_string, seek_time


_sorting_defaults = \
    {
        'followed_channels':
            {
                'by': SortBy.LAST_BROADCAST,
                'direction': Direction.DESC,
                'period': None
            },
        'channel_videos':
            {
                'by': VideoSort.TIME,
                'direction': None,
                'period': None
            },
        'clips':
            {
                'by': Boolean.TRUE,
                'direction': None,
                'period': ClipPeriod.WEEK
            },
        'top_videos':
            {
                'by': None,
                'direction': None,
                'period': Period.WEEK
            }
    }


def get_stored_json():
    json_data = storage.load()
    needs_save = False
    if 'qualities' not in json_data:
        json_data['qualities'] = {'stream': [], 'video': [], 'clip': []}
        needs_save = True
    if 'sorting' not in json_data:
        json_data['sorting'] = _sorting_defaults
        needs_save = True
    if 'languages' not in json_data:
        json_data['languages'] = Language.ALL
        needs_save = True
    if 'languages' in json_data and isinstance(json_data['languages'], list):
        if len(json_data['languages']) == 1:
            json_data['languages'] = json_data['languages'][0]
        else:
            json_data['languages'] = Language.ALL
        needs_save = True
    if needs_save:
        storage.save(json_data)
    return json_data


def get_language():
    json_data = get_stored_json()
    language = json_data['languages']
    if language == 'all':
        language = ''
    return language


def change_language(language=Language.ALL):
    json_data = get_stored_json()
    language = Language.validate(language)
    json_data['languages'] = language
    storage.save(json_data)


def get_sort(for_type, key=None):
    json_data = get_stored_json()
    sorting = json_data['sorting'].get(for_type)
    if not sorting:
        return None
    if key and key in json_data['sorting'][for_type]:
        return json_data['sorting'][for_type][key]
    else:
        return json_data['sorting'][for_type]


def set_sort(for_type, sort_by, direction, period):
    json_data = get_stored_json()
    sorting = json_data['sorting'].get(for_type)
    if not sorting:
        if for_type in _sorting_defaults:
            json_data['sorting'][for_type] = _sorting_defaults[for_type]
        else:
            return False
    json_data['sorting'][for_type] = {'by': sort_by, 'direction': direction, 'period': period}
    storage.save(json_data)
    return True


def get_default_quality(content_type, target_id):
    json_data = get_stored_json()
    if content_type not in json_data['qualities']:
        json_data['qualities'][content_type] = []
    if any(str(target_id) in item for item in json_data['qualities'][content_type]):
        return next(item for item in json_data['qualities'][content_type] if str(target_id) in item)
    else:
        return None


def add_default_quality(content_type, target_id, name, quality):
    json_data = get_stored_json()
    current_quality = get_default_quality(content_type, target_id)
    if current_quality:
        current_quality = current_quality[target_id]['quality']
        if current_quality.lower() == quality.lower():
            return False
        else:
            index = next(index for index, item in enumerate(json_data['qualities'][content_type]) if str(target_id) in item)
            del json_data['qualities'][content_type][index]
    json_data['qualities'][content_type].append({target_id: {'name': name, 'quality': quality}})
    storage.save(json_data)
    return True


def remove_default_quality(content_type):
    json_data = get_stored_json()
    result = kodi.Dialog().select(i18n('remove_default_quality') % content_type,
                                  ['%s [%s]' % (user[user.keys()[0]]['name'], user[user.keys()[0]]['quality']) for user in json_data['qualities'][content_type]])
    if result == -1:
        return None
    else:
        result = json_data['qualities'][content_type].pop(result)
        storage.save(json_data)
        return result


def clear_list(list_type, list_name):
    json_data = get_stored_json()
    if (list_name in json_data) and (list_type in json_data[list_name]):
        json_data[list_name][list_type] = []
        storage.save(json_data)
        return True
    else:
        return False


def convert_duration(duration):
    payload = 0

    pattern = re.compile('(?:(?P<hours>[0-9]+)(?:h))?(?:(?P<minutes>[0-9]+)(?:m))?(?:(?P<seconds>[0-9]+)(?:s))?')
    match = re.search(pattern, duration)

    if match:
        hours = match.group('hours')
        minutes = match.group('minutes')
        seconds = match.group('seconds')
        if hours:
            payload += int(hours) * 3600
        if minutes:
            payload += int(minutes) * 60
        if seconds:
            payload += int(seconds)

    return payload


# Characters Kodi's default skin font (Estuary/Noto Sans) cannot render show up as an empty
# box ("tofu") -- mostly emoji/symbols in stream titles. Filter them out before display.
_TOFU_RE = re.compile(
    u'['
    u'\U0001F000-\U0001FAFF'  # emoji & pictographs (emoticons, transport, symbols & pictographs, flags ...)
    u'\U00002600-\U000027BF'  # misc symbols + dingbats
    u'\U00002B00-\U00002BFF'  # misc symbols and arrows
    u'\U000023E9-\U000023FA'  # media/clock emoji from misc technical
    u'\U0000FE00-\U0000FE0F'  # variation selectors (emoji presentation)
    u'\U0000200D'             # zero width joiner (emoji sequences)
    u'\U000020E3'             # combining enclosing keycap
    u']+'
)


def strip_tofu(text):
    # Replace non-renderable emoji/symbols (would show as tofu boxes) with a single space --
    # dropping them glues words together ("WEEKEND<emoji>Type" -> "WEEKENDType"). Only
    # horizontal whitespace is collapsed, line breaks are kept (matters for plots).
    if not isinstance(text, str):
        return text
    text = _TOFU_RE.sub(u' ', text)
    text = re.sub(u'[ \\t]{2,}', u' ', text)
    text = re.sub(u'[ \\t]*\\n[ \\t]*', u'\n', text)
    return text.strip()


class TitleBuilder(object):
    class Templates(object):
        TITLE = u"{title}"
        STREAMER = u"{streamer}"
        STREAMER_TITLE = u"{streamer} - {title}"
        VIEWERS_STREAMER_TITLE = u"{viewers} - {streamer} - {title}"
        STREAMER_GAME_TITLE = u"{streamer} - {game} - {title}"
        GAME_VIEWERS_STREAMER_TITLE = u"[{game}] {viewers} | {streamer} - {title}"
        GAME_STREAMER_TITLE = u"[{game}] | {streamer} - {title}"
        BROADCASTER_LANGUAGE_STREAMER_TITLE = u"{broadcaster_language} | {streamer} - {title}"
        ELLIPSIS = u'...'

    def __init__(self, line_length):
        self.line_length = line_length

    def format_title(self, title_values):
        title_setting = int(kodi.get_setting('title_display'))
        template = self.get_title_template(title_setting, title_values)

        for key, value in title_values.items():
            title_values[key] = self.clean_title_value(value)
        title = template.format(**title_values)

        return self.truncate_title(title)

    @staticmethod
    def get_title_template(title_setting, title_values):
        options = {
            0: TitleBuilder.Templates.STREAMER_TITLE,
            1: TitleBuilder.Templates.VIEWERS_STREAMER_TITLE,
            2: TitleBuilder.Templates.TITLE,
            3: TitleBuilder.Templates.STREAMER,
            4: TitleBuilder.Templates.STREAMER_GAME_TITLE,
            5: TitleBuilder.Templates.GAME_VIEWERS_STREAMER_TITLE,
            6: TitleBuilder.Templates.BROADCASTER_LANGUAGE_STREAMER_TITLE,
            7: TitleBuilder.Templates.GAME_STREAMER_TITLE,
        }

        if title_setting == 1:
            if not title_values.get('viewers'):
                title_setting = 0
        elif title_setting == 4:
            if not title_values.get('game'):
                title_setting = 0
        elif title_setting == 5:
            if not title_values.get('game') and not title_values.get('viewers'):
                title_setting = 0
            elif title_values.get('game') and not title_values.get('viewers'):
                title_setting = 7
            elif not title_values.get('game') and title_values.get('viewers'):
                title_setting = 1
        elif title_setting == 6:
            if not title_values.get('broadcaster_language'):
                title_setting = 0

        return options.get(title_setting, TitleBuilder.Templates.STREAMER)

    @staticmethod
    def clean_title_value(value):
        if isinstance(value, str):
            try:
                value = value.decode('utf-8', 'ignore')
            except (UnicodeEncodeError, AttributeError) as e:
                pass
            value = value.replace(u'\r\n', u' ')
            value = value.replace(u'\n', u' ')
            value = strip_tofu(value)  # drop emoji/symbols the skin font cannot render
            value = value.strip()
            return value
        else:
            return value

    def truncate_title(self, title):
        truncate_setting = kodi.get_setting('title_truncate') == 'true'

        if truncate_setting:
            short_title = title[:self.line_length]
            ending = (title[self.line_length:] and TitleBuilder.Templates.ELLIPSIS)
            return short_title + ending
        return title
