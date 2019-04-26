# -*- coding: utf-8 -*-

# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, unicode_literals
from datetime import datetime, timedelta
import dateutil.parser
import dateutil.tz
import os
import requests

from resources.lib.helperobjects import helperobjects
from resources.lib.vrtplayer import actions, metadatacreator, statichelper

CHANNELS = dict(
    een=dict(
        id='O8',
        name='Eén',
    ),
    canvas=dict(
        id='1H',
        name='Canvas',
    ),
    ketnet=dict(
        id='O9',
        name='Ketnet',
    ),
)

DATE_STRINGS = {
    '-2': 32330,  # 2 days ago
    '-1': 32331,  # Yesterday
    '0': 32332,  # Today
    '1': 32333,  # Tomorrow
    '2': 32334,  # In 2 days
}


class TVGuide:

    VRT_TVGUIDE = 'https://www.vrt.be/bin/epg/schedule.%Y-%m-%d.json'

    def __init__(self, addon_path, kodi_wrapper):
        self._addon_path = addon_path
        self._kodi_wrapper = kodi_wrapper
        self._proxies = self._kodi_wrapper.get_proxies()

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
            self._kodi_wrapper.show_listing(date_items, sort='unsorted', content_type='files')

        elif not channel:
            dateobj = dateutil.parser.parse(date)
            datelong = dateobj.strftime(self._kodi_wrapper.get_localized_datelong())
            channel_items = []
            for channel in ('een', 'canvas', 'ketnet'):
                plot = self._kodi_wrapper.get_localized_string(32301) % CHANNELS[channel]['name'] + '\n' + datelong
                channel_items.append(
                    helperobjects.TitleItem(
                        title=CHANNELS[channel]['name'],
                        url_dict=dict(action=actions.LISTING_TVGUIDE, date=date, channel=channel),
                        is_playable=False,
                        art_dict=dict(thumb=self.__get_media(channel + '.png'), icon='DefaultAddonPVRClient.png', fanart='DefaultAddonPVRClient.png'),
                        video_dict=dict(plot=plot),
                    ),
                )
            self._kodi_wrapper.show_listing(channel_items, content_type='files')

        else:
            now = datetime.now(dateutil.tz.tzlocal())
            dateobj = dateutil.parser.parse(date)
            datelong = dateobj.strftime(self._kodi_wrapper.get_localized_datelong())
            api_url = dateobj.strftime(self.VRT_TVGUIDE)
            schedule = requests.get(api_url, proxies=self._proxies).json()
            episodes = schedule[CHANNELS[channel]['id']]
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
                metadata.plot = '[B]%s[/B]\n%s\n%s - %s\n[I]%s[/I]' % (title, datelong, start, end, CHANNELS[channel]['name'])
                metadata.brands = [channel]
                metadata.mediatype = 'episode'
                thumb = episode.get('image', 'DefaultAddonVideo.png')
                metadata.icon = thumb
                if url:
                    video_url = statichelper.add_https_method(url)
                    url_dict = dict(action=actions.PLAY, video_url=video_url)
                    if start_date < now <= end_date:  # Now playing
                        metadata.title = '[COLOR yellow]%s[/COLOR] %s' % (label, self._kodi_wrapper.get_localized_string(32302))
                    else:
                        metadata.title = label
                else:
                    # FIXME: Find a better solution for non-actionable items
                    url_dict = dict(action=actions.LISTING_TVGUIDE, date=date, channel=channel)
                    if start_date < now <= end_date:  # Now playing
                        metadata.title = '[COLOR brown]%s[/COLOR] %s' % (label, self._kodi_wrapper.get_localized_string(32302))
                    else:
                        metadata.title = '[COLOR gray]%s[/COLOR]' % label
                episode_items.append(helperobjects.TitleItem(
                    title=metadata.title,
                    url_dict=url_dict,
                    is_playable=bool(url),
                    art_dict=dict(thumb=thumb, icon='DefaultAddonVideo.png', fanart=thumb),
                    video_dict=metadata.get_video_dict(),
                ))
            self._kodi_wrapper.show_listing(episode_items, sort='unsorted', content_type='episodes')

    def __get_media(self, file_name):
        return os.path.join(self._addon_path, 'resources', 'media', file_name)
