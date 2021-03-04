# -*- coding: utf-8 -*-
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, unicode_literals
import logging
import inputstreamhelper
import xbmcgui
import xbmcplugin

from data import USER_AGENT
from helpers.helperclasses import PluginCache
from helpers.helpermethods import widevine_payload_package
from yelo_api import YeloApi
from kodiutils import kodi_version_major

try:  # Python 3
    from urllib.parse import quote
except ImportError:  # Python 2
    from urllib2 import quote


PROTOCOL = 'mpd'
DRM = 'com.widevine.alpha'
LICENSE_URL = 'https://lwvdrm.yelo.prd.telenet-ops.be/WvLicenseProxy'

_LOGGER = logging.getLogger('plugin')


class Yelo(YeloApi):
    def play(self, channel):
        manifest_url = self.get_manifest(channel)
        device_id = PluginCache.get_by_key("device_id")
        customer_id = PluginCache.get_by_key("entitlements")["customer_id"]

        is_helper = inputstreamhelper.Helper(PROTOCOL, drm=DRM)
        if is_helper.check_inputstream():
            from addon import plugin
            play_item = xbmcgui.ListItem(path=manifest_url)
            play_item.setMimeType('application/xml+dash')
            play_item.setContentLookup(False)

            if kodi_version_major() >= 19:
                play_item.setProperty('inputstream', is_helper.inputstream_addon)
            else:
                play_item.setProperty('inputstreamaddon', is_helper.inputstream_addon)

            play_item.setProperty('inputstream.adaptive.manifest_type', PROTOCOL)
            play_item.setProperty('inputstream.adaptive.license_type', DRM)
            play_item.setProperty('inputstream.adaptive.manifest_update_parameter', 'full')
            play_item.setProperty('inputstream.adaptive.license_key',
                                  '%(url)s|Content-Type=text/plain;charset=UTF-8&User-Agent=%(ua)s|b{%(payload)s}|JBlicense'
                                  % dict(
                                      url=LICENSE_URL,
                                      ua=quote(USER_AGENT),
                                      payload=widevine_payload_package(device_id, customer_id),
                                  ))
            play_item.setProperty('inputstream.adaptive.license_flags', "persistent_storage")
            xbmcplugin.setResolvedUrl(plugin.handle, True, listitem=play_item)

    def list_channels_without_epg(self, is_folder=False):
        from kodiwrapper import KodiWrapper

        listing = []

        tv_channels = self.get_channels()

        for tv_channel in tv_channels:
            name = tv_channel.get('channelIdentification').get('name')
            square_logo = tv_channel.get('channelProperties').get('squareLogo')
            channel_id = tv_channel.get('channelIdentification').get('stbUniqueName')

            list_item = KodiWrapper.create_list_item(name, square_logo, "", {"plot": ""}, True, True)
            url = KodiWrapper.url_for('play_id', channel_id=channel_id)
            listing.append((url, list_item, is_folder))

        KodiWrapper.add_dir_items(listing)
        KodiWrapper.end_directory()

    def list_channels(self, is_folder=False):
        from kodiwrapper import KodiWrapper
        import datetime
        import dateutil.parser
        from dateutil.tz import UTC

        listing = []

        tv_channels = self.get_channels()
        epg = self.get_cached_epg()

        for tv_channel in tv_channels:
            name = tv_channel.get('channelIdentification').get('name')
            square_logo = tv_channel.get('channelProperties').get('squareLogo')
            channel_id = tv_channel.get('channelIdentification').get('stbUniqueName')

            poster = ""
            guide = ""

            for index, item in enumerate(epg[name]):
                now = datetime.datetime.utcnow().replace(second=0, microsecond=0, tzinfo=UTC)

                end = dateutil.parser.parse(item.get('stop'))
                if end <= now:
                    continue

                start = dateutil.parser.parse(item.get('start'))
                if start >= now:
                    continue

                try:
                    prev_title = epg.get(name, [])[index - 1].get('title', '')
                except IndexError:
                    prev_title = ''

                try:
                    next_title = epg.get(name, [])[index + 1].get('title', '')
                except IndexError:
                    next_title = ''

                title = item.get('title', '')
                guide = self._create_guide_from_channel_info(prev_title, title, next_title)
                poster = item.get('image', '')

            list_item = KodiWrapper.create_list_item(name, square_logo, poster, {"plot": guide}, True, True)
            url = KodiWrapper.url_for('play_id', channel_id=channel_id)
            listing.append((url, list_item, is_folder))

        KodiWrapper.add_dir_items(listing)
        KodiWrapper.end_directory()
