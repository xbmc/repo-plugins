# -*- coding: utf-8 -*-
"""

    Copyright (C) 2011-2018 PleXBMC (plugin.video.plexbmc) by hippojay (Dave Hawes-Johnson)
    Copyright (C) 2018-2020 Composite (plugin.video.composite_for_plex)

    This file is part of Composite (plugin.video.composite_for_plex)

    SPDX-License-Identifier: GPL-2.0-or-later
    See LICENSES/GPL-2.0-or-later.txt for more information.
"""

import json
import uuid

from kodi_six import xbmc  # pylint: disable=import-error
from kodi_six import xbmcaddon  # pylint: disable=import-error
from kodi_six import xbmcgui  # pylint: disable=import-error
from kodi_six import xbmcvfs  # pylint: disable=import-error
from six.moves import xrange

from .constants import CONFIG

try:
    xbmc.translatePath = xbmcvfs.translatePath
except AttributeError:
    pass


class AddonSettings:  # pylint: disable=too-many-public-methods

    def __init__(self):
        self.settings = self._get_addon()
        self.addon_name = CONFIG['name']
        xbmc.log(self.addon_name + '.settings -> Reading settings configuration', xbmc.LOGDEBUG)
        self.stream = self.settings.getSetting('streaming')
        self.picture_mode = False
        self._settings = {}

    @staticmethod
    def _get_addon():
        return xbmcaddon.Addon(CONFIG['id'])

    def open_settings(self):
        return self.settings.openSettings()

    def _get_setting(self, name, fresh=False):
        value = self._settings.get(name)
        if value is None or fresh:
            if fresh:
                value = self._get_addon().getSetting(name)
            else:
                value = self.settings.getSetting(name)

            self._settings[name] = value

        if value == 'true':
            return True

        if value == 'false':
            return False

        return value

    def _set_setting(self, name, value):
        if isinstance(value, bool):
            value = str(value).lower()

        self.settings.setSetting(name, value)
        self._settings[name] = value

    def dump_settings(self):
        return self.__dict__

    def get_debug(self):
        return int(self._get_setting('debug'))

    def cache_directory(self):
        return self._get_setting('kodicache')

    def privacy(self):
        return self._get_setting('privacy')

    def stream_control(self, fresh=False):
        return self._get_setting('streamControl', fresh=fresh)

    def full_resolution_thumbnails(self):
        return self._get_setting('fullres_thumbs')

    def full_resolution_fanart(self):
        return self._get_setting('fullres_fanart')

    def force_dvd(self):
        return self._get_setting('forcedvd')

    def show_delete_context_menu(self):
        return self._get_setting('showdeletecontextmenu')

    def skip_context_menus(self):
        return self._get_setting('skipcontextmenus')

    def skip_flags(self):
        return self._get_setting('skipflags')

    def skip_images(self):
        return self._get_setting('skipimages')

    def skip_metadata(self):
        return self._get_setting('skipmetadata')

    def get_picture_mode(self):
        return self.picture_mode

    def set_picture_mode(self, value):
        self.picture_mode = bool(value)

    def wake_on_lan(self):
        return self._get_setting('wolon')

    def get_wakeservers(self):
        get_setting = self._get_setting
        return list(map(lambda x: get_setting('wol%s' % x), xrange(1, 12)))

    def get_stream(self):
        return self.stream

    def set_stream(self, value):
        self.stream = value

    def default_forced_subtitles(self):
        return self._get_setting('default_forced_subs')

    def master_server(self):
        return self._get_setting('masterServer')

    def set_master_server(self, value):
        xbmc.log(self.addon_name + '.settings -> Updating master server to %s' %
                 value, xbmc.LOGDEBUG)
        self.settings.setSetting('masterServer', '%s' % value)

    def prefix_server(self):
        return self._get_setting('prefix_server') == '1'

    def prefix_server_in_combined(self):
        return self._get_setting('prefix_server_sections')

    def recently_added_item_count(self):
        return int(self._get_setting('ra_sections_items_per_server'))

    def recently_added_include_watched(self):
        return self._get_setting('ra_sections_include_watched')

    def flatten_seasons(self):
        return self._get_setting('flatten')

    def all_season_disabled(self):
        return self._get_setting('disable_all_season')

    def playback_monitor_disabled(self, fresh=False):
        return self._get_setting('monitoroff', fresh=fresh)

    def secondary_menus(self):
        return self._get_setting('secondary')

    def show_menus(self):
        return {
            'queue': self._get_setting('show_myplex_queue_menu'),
            'channels': self._get_setting('show_channels_menu'),
            'online': self._get_setting('show_plex_online_menu'),
            'playlists': self._get_setting('show_playlists_menu'),
            'widgets': self._get_setting('show_widget_menu'),
            'composite_playlist': self._get_setting('show_composite_playlist_menu'),
        }

    def episode_sort_method(self):
        method = self._get_setting('ep_sort_method')
        if method == '0':
            return 'kodi'
        if method == '1':
            return 'plex'
        raise Exception('Unknown sort method')

    def mixed_content_type(self):
        method = self._get_setting('mixed_content_type')
        if method == '0':
            return 'default'
        if method == '1':
            return 'majority'
        raise Exception('Unknown mixed content type method')

    def device_name(self):
        return self._get_setting('devicename')

    def client_id(self):
        return self._get_setting('client_id')

    def set_client_id(self, value):
        return self._set_setting('client_id', value)

    def ip_address(self):
        return self._get_setting('ipaddress')

    def port(self):
        return self._get_setting('port')

    def https(self):
        return self._get_setting('manual_https')

    def certificate_verification(self):
        return self._get_setting('manual_certificate_verification')

    def discovery(self):
        return self._get_setting('discovery')

    def servers_detected_notification(self):
        return self._get_setting('detected_notification')

    def myplex_user(self):
        return self._get_setting('myplex_user')

    def replacement(self):
        return self._get_setting('replacement')

    def set_replacement(self, value):
        self._set_setting('replacement', value)

    def intro_skipping(self):
        return self._get_setting('intro_skipping')

    def get_lyrics_priorities(self):
        if not self._get_setting('lyrics'):
            return None

        formats = {
            '0': 'lrc',
            '1': 'txt',
        }

        fmt = formats.get(self._get_setting('default_lyrics_format'))

        priorities = {
            'lrc': 100 if fmt == 'lrc' else 50,
            'txt': 100 if fmt == 'txt' else 50,
            'none': 0,
        }

        return priorities

    def override_info(self):
        return {
            'override': self._get_setting('nasoverride'),
            'root': self._get_setting('nasroot'),
            'ip_address': self._get_setting('nasoverrideip'),
            'user_id': self._get_setting('nasuserid'),
            'password': self._get_setting('naspass'),
        }

    def always_transcode(self):
        return self._get_setting('transcode')

    def transcode_hevc(self):
        return self._get_setting('transcode_hevc')

    def transcode_g1080(self):
        return self._get_setting('transcode_g1080')

    def transcode_g8bit(self):
        return self._get_setting('transcode_g8bit')

    def transcode_profile(self, value):
        try:
            value = int(value)
        except ValueError:
            value = 0

        enabled = True if value == 0 else self._get_setting('transcode_target_enabled_%d' % value)
        return {
            'enabled': enabled,
            'quality': self._get_setting('transcode_target_quality_%d' % value),
            'subtitle_size': self._get_setting('transcode_target_sub_size_%d' % value),
            'audio_boost': self._get_setting('transcode_target_audio_size_%d' % value),
        }

    def use_up_next(self):
        upnext_id = 'service.upnext'
        s_upnext_enabled = self._get_setting('use_up_next', fresh=True)

        try:
            _ = xbmcaddon.Addon(upnext_id)
            has_upnext = True
            upnext_disabled = False
        except RuntimeError:
            addon_xml = xbmc.translatePath('special://home/addons/%s/addon.xml' % upnext_id)
            if xbmcvfs.exists(addon_xml):  # if addon.xml exists, add-on is disabled
                has_upnext = True
                upnext_disabled = True
            else:
                has_upnext = False
                upnext_disabled = False

        if s_upnext_enabled and has_upnext and upnext_disabled:
            enable_upnext = xbmcgui.Dialog().yesno(self.addon_name,
                                                   self.settings.getLocalizedString(30688))
            if enable_upnext:
                upnext_disabled = not self.enable_addon(upnext_id)

        if (not has_upnext or upnext_disabled) and s_upnext_enabled:
            self._set_setting('use_up_next', False)
            return False

        return s_upnext_enabled and has_upnext and not upnext_disabled

    def up_next_encoding(self):
        return self._get_setting('up_next_data_encoding', fresh=True)

    def up_next_episode_thumbs(self):
        return self._get_setting('up_next_episode_thumbs', fresh=True)

    def cache(self):
        return self._get_setting('cache')

    def cache_ttl(self):
        return int(self._get_setting('cache_ttl')) * 60

    def cache_clear_on_refresh(self):
        return self._get_setting('clear_data_cache_refresh')

    def data_cache(self):
        return self._get_setting('data_cache')

    def data_cache_ttl(self):
        return int(self._get_setting('data_cache_ttl', fresh=True)) * 60

    def use_companion(self):
        return self._get_setting('use_companion_receiver', fresh=True)

    def companion_receiver(self):
        receiver_uuid = str(self._get_setting('receiver_uuid')) or str(uuid.uuid4())
        self._set_setting('receiver_uuid', receiver_uuid)

        port = self._get_setting('receiver_port')
        try:
            port = int(port)
        except ValueError:
            port = 3005

        return {
            'name': self._get_setting('receiver_name'),
            'port': port,
            'uuid': receiver_uuid,
        }

    def kodi_web_server(self):
        port = self._get_setting('web_server_port')
        try:
            port = int(port)
        except ValueError:
            port = 8080

        return {
            'name': self._get_setting('web_server_username'),
            'password': self._get_setting('web_server_password'),
            'port': port,
        }

    def addon_status(self, addon_id):
        request = {
            "jsonrpc": "2.0",
            "method": "Addons.GetAddonDetails",
            "id": 1,
            "params": {
                "addonid": "%s" % addon_id,
                "properties": ["enabled"]
            }
        }
        response = xbmc.executeJSONRPC(json.dumps(request))
        response = json.loads(response)
        try:
            is_enabled = response['result']['addon']['enabled'] is True
            xbmc.log(self.addon_name + '.settings -> %s is %s' %
                     (addon_id, 'enabled' if is_enabled else 'disabled'), xbmc.LOGDEBUG)
            return is_enabled
        except KeyError:
            xbmc.log(self.addon_name + '.settings -> addon_status received an unexpected response',
                     xbmc.LOGERROR)
            return False

    def disable_addon(self, addon_id):
        request = {
            "jsonrpc": "2.0",
            "method": "Addons.SetAddonEnabled",
            "params": {
                "addonid": "%s" % addon_id,
                "enabled": False
            },
            "id": 1
        }

        xbmc.log(self.addon_name + '.settings -> disabling %s' % addon_id, xbmc.LOGDEBUG)
        response = xbmc.executeJSONRPC(json.dumps(request))
        response = json.loads(response)
        try:
            return response['result'] == 'OK'
        except KeyError:
            xbmc.log(self.addon_name + '.settings -> disable_addon received an unexpected response',
                     xbmc.LOGERROR)
            return False

    def enable_addon(self, addon_id):
        request = {
            "jsonrpc": "2.0",
            "method": "Addons.SetAddonEnabled",
            "params": {
                "addonid": "%s" % addon_id,
                "enabled": True
            },
            "id": 1
        }

        xbmc.log(self.addon_name + '.settings -> enabling %s' % addon_id, xbmc.LOGDEBUG)

        response = xbmc.executeJSONRPC(json.dumps(request))
        response = json.loads(response)
        try:
            return response['result'] == 'OK'
        except KeyError:
            xbmc.log(self.addon_name + '.settings -> enable_addon received an unexpected response',
                     xbmc.LOGERROR)
            return False
