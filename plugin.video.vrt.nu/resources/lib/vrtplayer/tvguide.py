# -*- coding: utf-8 -*-

# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, unicode_literals
from datetime import datetime, timedelta
import dateutil.parser
import dateutil.tz
import json

try:
    from urllib.request import build_opener, install_opener, ProxyHandler, urlopen
except ImportError:
    from urllib2 import build_opener, install_opener, ProxyHandler, urlopen

from resources.lib.helperobjects import helperobjects
from resources.lib.vrtplayer import CHANNELS, actions, metadatacreator, statichelper

DATE_STRINGS = {
    '-2': 30330,  # 2 days ago
    '-1': 30331,  # Yesterday
    '0': 30332,  # Today
    '1': 30333,  # Tomorrow
    '2': 30334,  # In 2 days
}


class TVGuide:

    VRT_TVGUIDE = 'https://www.vrt.be/bin/epg/schedule.%Y-%m-%d.json'

    def __init__(self, kodi_wrapper):
        self._kodi_wrapper = kodi_wrapper
        self._proxies = self._kodi_wrapper.get_proxies()
        install_opener(build_opener(ProxyHandler(self._proxies)))
        kodi_wrapper.set_locale()

    def show_tvguide(self, params):
        date = params.get('date')
        channel = params.get('channel')

        if not date:
            now = datetime.now(dateutil.tz.tzlocal())
            date_items = []
            for i in range(7, -31, -1):
                day = now + timedelta(days=i)
                title = day.strftime(self._kodi_wrapper.get_localized_datelong())
                if str(i) in DATE_STRINGS:
                    if i == 0:
                        title = '[COLOR yellow][B]%s[/B], %s[/COLOR]' % (self._kodi_wrapper.get_localized_string(DATE_STRINGS[str(i)]), title)
                    else:
                        title = '[B]%s[/B], %s' % (self._kodi_wrapper.get_localized_string(DATE_STRINGS[str(i)]), title)
                date_items.append(
                    helperobjects.TitleItem(title=title,
                                            url_dict=dict(action=actions.LISTING_TVGUIDE, date=day.strftime('%Y-%m-%d')),
                                            is_playable=False,
                                            art_dict=dict(thumb='DefaultYear.png', icon='DefaultYear.png', fanart='DefaultYear.png'),
                                            video_dict=dict(plot=day.strftime(self._kodi_wrapper.get_localized_datelong()))),
                )
            self._kodi_wrapper.show_listing(date_items, content_type='files')

        elif not channel:
            dateobj = dateutil.parser.parse(date)
            datelong = dateobj.strftime(self._kodi_wrapper.get_localized_datelong())

            fanart_path = 'resource://resource.images.studios.white/%(studio)s.png'
            icon_path = 'resource://resource.images.studios.white/%(studio)s.png'
            # NOTE: Wait for resource.images.studios.coloured v0.16 to be released
            # icon_path = 'resource://resource.images.studios.coloured/%(studio)s.png'

            channel_items = []
            for channel in CHANNELS:
                if channel.get('name') not in ('een', 'canvas', 'ketnet'):
                    continue

                icon = icon_path % channel
                fanart = fanart_path % channel
                plot = self._kodi_wrapper.get_localized_string(30301) % channel.get('label') + '\n' + datelong
                channel_items.append(
                    helperobjects.TitleItem(
                        title=channel.get('label'),
                        url_dict=dict(action=actions.LISTING_TVGUIDE, date=date, channel=channel.get('name')),
                        is_playable=False,
                        art_dict=dict(thumb=icon, icon=icon, fanart=fanart),
                        video_dict=dict(plot=plot, studio=channel.get('studio')),
                    ),
                )
            self._kodi_wrapper.show_listing(channel_items)

        else:
            now = datetime.now(dateutil.tz.tzlocal())
            dateobj = dateutil.parser.parse(date)
            datelong = dateobj.strftime(self._kodi_wrapper.get_localized_datelong())
            api_url = dateobj.strftime(self.VRT_TVGUIDE)
            schedule = json.loads(urlopen(api_url).read())
            name = channel
            try:
                channel = next(c for c in CHANNELS if c.get('name') == name)
                episodes = schedule[channel.get('id')]
            except StopIteration:
                episodes = []
            episode_items = []
            for episode in episodes:
                metadata = metadatacreator.MetadataCreator()
                title = episode.get('title')
                start = episode.get('start')
                end = episode.get('end')
                start_date = dateutil.parser.parse(episode.get('startTime'))
                end_date = dateutil.parser.parse(episode.get('endTime'))
                url = episode.get('url')
                label = '%s - %s' % (start, title)
                metadata.tvshowtitle = title
                metadata.datetime = dateobj
                # NOTE: Do not use startTime and endTime as we don't want duration in seconds
                metadata.duration = (dateutil.parser.parse(end) - dateutil.parser.parse(start)).total_seconds()
                metadata.plot = '[B]%s[/B]\n%s\n%s - %s\n[I]%s[/I]' % (title, datelong, start, end, channel.get('label'))
                metadata.brands = [channel]
                metadata.mediatype = 'episode'
                thumb = episode.get('image', 'DefaultAddonVideo.png')
                metadata.icon = thumb
                if url:
                    video_url = statichelper.add_https_method(url)
                    url_dict = dict(action=actions.PLAY, video_url=video_url)
                    if start_date < now <= end_date:  # Now playing
                        metadata.title = '[COLOR yellow]%s[/COLOR] %s' % (label, self._kodi_wrapper.get_localized_string(30302))
                    else:
                        metadata.title = label
                else:
                    # FIXME: Find a better solution for non-actionable items
                    url_dict = dict(action=actions.LISTING_TVGUIDE, date=date, channel=channel)
                    if start_date < now <= end_date:  # Now playing
                        metadata.title = '[COLOR brown]%s[/COLOR] %s' % (label, self._kodi_wrapper.get_localized_string(30302))
                    else:
                        metadata.title = '[COLOR gray]%s[/COLOR]' % label
                episode_items.append(helperobjects.TitleItem(
                    title=metadata.title,
                    url_dict=url_dict,
                    is_playable=bool(url),
                    art_dict=dict(thumb=thumb, icon='DefaultAddonVideo.png', fanart=thumb),
                    video_dict=metadata.get_video_dict(),
                ))
            self._kodi_wrapper.show_listing(episode_items, content_type='episodes', cache=False)
