# -*- coding: utf-8 -*-

# GNU General Public License v2.0 (see COPYING or https://www.gnu.org/licenses/gpl-2.0.txt)

import requests
from resources.lib.vrtplayer import statichelper, metadatacreator, actions
from resources.lib.helperobjects import helperobjects
from resources.lib.kodiwrappers import sortmethod
from bs4 import BeautifulSoup
from datetime import datetime
import time


class VRTApiHelper:

    _VRT_BASE = 'https://www.vrt.be'
    _VRTNU_API_BASE = 'https://vrtnu-api.vrt.be'
    _VRTNU_SEARCH_URL = ''.join((_VRTNU_API_BASE, '/search'))
    _VRTNU_SUGGEST_URL = ''.join((_VRTNU_API_BASE, '/suggest'))
    _VRTNU_SCREENSHOT_URL = ''.join((_VRTNU_API_BASE, '/screenshots'))

    def __init__(self, kodi_wrapper):
        self._kodi_wrapper = kodi_wrapper
        self._proxies = self._kodi_wrapper.get_proxies()

    def get_tvshow_items(self, path):
        if path == 'az':
            api_url = ''.join((self._VRTNU_SUGGEST_URL, '?facets[transcodingStatus]=AVAILABLE'))
        else:
            api_url = ''.join((self._VRTNU_SUGGEST_URL, '?facets[categories]=', path))
        tvshows = requests.get(api_url, proxies=self._proxies).json()
        tvshow_items = []
        for tvshow in tvshows:
            metadata_creator = metadatacreator.MetadataCreator()
            metadata_creator.mediatype = 'tvshow'
            metadata_creator.tvshowtitle = tvshow.get('title')
            metadata_creator.plot = statichelper.unescape(tvshow.get('description'))
            metadata_creator.url = statichelper.add_https_method(tvshow.get('targetUrl'))
            metadata_creator.brands = tvshow.get('brands')
            thumbnail = statichelper.add_https_method(tvshow.get('thumbnail'))
            # Cut vrtbase url off since it will be added again when searching for episodes
            # (with a-z we dont have the full url)
            video_url = statichelper.add_https_method(tvshow.get('targetUrl')).replace(self._VRT_BASE, '')
            tvshow_items.append(helperobjects.TitleItem(title=tvshow.get('title'),
                                                        url_dict=dict(action=actions.LISTING_EPISODES, video_url=video_url),
                                                        is_playable=False,
                                                        art_dict=dict(thumb=thumbnail, icon='DefaultAddonVideo.png', fanart=thumbnail),
                                                        video_dict=metadata_creator.get_video_dict()))
        return tvshow_items

    def _get_season_items(self, api_url, facets):
        season_items = None
        # Check if program has seasons
        for facet in facets:
            if facet['name'] == 'seasons' and len(facet['buckets']) > 1:
                # Found multiple seasons, make list of seasons
                season_items = self._map_to_season_items(api_url, facet['buckets'])
        return season_items

    def get_episode_items(self, path):
        episode_items = None
        sort_method = None
        if path == 'recent':
            api_url = ''.join((self._VRTNU_SEARCH_URL, '?i=video&size=50&facets[transcodingStatus]=AVAILABLE&facets[brands]=[een,canvas,sporza,radio1,klara,stubru,mnm]'))
            api_json = requests.get(api_url, proxies=self._proxies).json()
            episode_items, sort_method = self._map_to_episode_items(api_json['results'], path)
        else:
            api_url = ''.join((self._VRTNU_SEARCH_URL, '?i=video&size=150&facets[programUrl]=//www.vrt.be', path.replace('.relevant', ''))) if '.relevant/' in path else path
            api_json = requests.get(api_url, proxies=self._proxies).json()
            # Look for seasons items if not yet done
            if 'facets[seasonTitle]' not in path:
                episode_items = self._get_season_items(api_url, api_json['facets']['facets'])
            # No season items, generate episode items
            if episode_items is None:
                episode_items, sort_method = self._map_to_episode_items(api_json['results'])

        return episode_items, sort_method

    def _map_to_episode_items(self, episodes, titletype=None):
        episode_items = []
        sort = None
        for episode in episodes:
            display_options = episode.get('displayOptions', dict())

            if episode['programType'] == 'reeksoplopend' and titletype is None:
                titletype = 'reeksoplopend'

            metadata_creator = metadatacreator.MetadataCreator()
            metadata_creator.tvshowtitle = episode.get('program')
            metadata_creator.url = episode.get('permalink')
            json_broadcast_date = episode.get('broadcastDate')
            if json_broadcast_date != -1:
                metadata_creator.datetime = datetime.fromtimestamp(episode.get('broadcastDate', 0)/1000)

            metadata_creator.duration = (episode.get('duration', 0) * 60)  # Minutes to seconds
            metadata_creator.plot = BeautifulSoup(episode.get('description'), 'html.parser').text
            metadata_creator.brands = episode.get('programBrands', episode.get('brands'))
            metadata_creator.geolocked = episode.get('allowedRegion') == 'BE'
            if display_options.get('showShortDescription'):
                short_description = BeautifulSoup(episode.get('shortDescription'), 'html.parser').text
                metadata_creator.plotoutline = short_description
                metadata_creator.subtitle = short_description
            else:
                metadata_creator.plotoutline = episode.get('subtitle')
                metadata_creator.subtitle = episode.get('subtitle')
            metadata_creator.season = episode.get('seasonName')
            metadata_creator.episode = episode.get('episodeNumber')
            metadata_creator.mediatype = episode.get('type', 'episode')
            if episode.get('assetOnTime') is not None:
                metadata_creator.ontime = datetime(*time.strptime(episode.get('assetOnTime'), '%Y-%m-%dT%H:%M:%S+0000')[0:6])
            if episode.get('assetOffTime') is not None:
                metadata_creator.offtime = datetime(*time.strptime(episode.get('assetOffTime'), '%Y-%m-%dT%H:%M:%S+0000')[0:6])

            # Add additional metadata to plot
            plot_meta = ''
            if metadata_creator.geolocked:
                plot_meta += self._kodi_wrapper.get_localized_string(32201)
            # Only display when a video disappears if it is within the next 3 months
            if metadata_creator.offtime is not None and (metadata_creator.offtime - datetime.utcnow()).days < 92:
                plot_meta += self._kodi_wrapper.get_localized_string(32202) % metadata_creator.offtime.strftime(self._kodi_wrapper.get_localized_dateshort())
                if (metadata_creator.offtime - datetime.utcnow()).days > 0:
                    plot_meta += self._kodi_wrapper.get_localized_string(32203) % (metadata_creator.offtime - datetime.utcnow()).days
                else:
                    plot_meta += self._kodi_wrapper.get_localized_string(32204) % int((metadata_creator.offtime - datetime.utcnow()).seconds/3600)
            if plot_meta:
                plot_meta += '\n'
            metadata_creator.plot = plot_meta + metadata_creator.plot

            thumb = statichelper.add_https_method(episode.get('videoThumbnailUrl'))
            video_url = statichelper.add_https_method(episode.get('url'))
            title, sort = self._make_title(episode, titletype)
            episode_items.append(helperobjects.TitleItem(title=title,
                                                         url_dict=dict(action=actions.PLAY, video_url=video_url, video_id=episode.get('videoId'), publication_id=episode.get('publicationId')),
                                                         is_playable=True,
                                                         art_dict=dict(thumb=thumb, icon='DefaultAddonVideo.png', fanart=thumb),
                                                         video_dict=metadata_creator.get_video_dict()))
        return episode_items, sort

    def _map_to_season_items(self, api_url, buckets):
        season_items = []
        for bucket in buckets:
            metadata_creator = metadatacreator.MetadataCreator()
            metadata_creator.mediatype = 'season'
            season_title = bucket.get('key')
            title = ''.join((self._kodi_wrapper.get_localized_string(32094), ' ', season_title))
            season_facet = '&facets[seasonTitle]='
            if ' ' in season_title:
                season_title = season_title.replace(' ', '-')
                season_facet = '&facets[seasonName]='
            path = ''.join((api_url, season_facet, season_title))
            season_items.append(helperobjects.TitleItem(title=title,
                                                        url_dict=dict(action=actions.LISTING_EPISODES, video_url=path),
                                                        is_playable=False,
                                                        art_dict=dict(thumb='DefaultSets.png', icon='DefaultSets.png', fanart='DefaultSets.png'),
                                                        video_dict=metadata_creator.get_video_dict()))
        return season_items

    def get_live_screenshot(self, channel):
        url = ''.join((self._VRTNU_SCREENSHOT_URL, '/', channel, '.jpg'))
        self.__delete_cached_thumbnail(url)
        return url

    def __delete_cached_thumbnail(self, url):
        crc = self.__get_crc32(url)
        ext = url.split('.')[-1]
        path = ''.join(('special://thumbnails/', crc[0], '/', crc, '.', ext))
        self._kodi_wrapper.delete_path(path)

    @staticmethod
    def __get_crc32(string):
        string = string.lower()
        string_bytes = bytearray(string.encode())
        crc = 0xffffffff
        for b in string_bytes:
            crc = crc ^ (b << 24)
            for _ in range(8):
                if crc & 0x80000000:
                    crc = (crc << 1) ^ 0x04C11DB7
                else:
                    crc = crc << 1
            crc = crc & 0xFFFFFFFF
        return '%08x' % crc

    def _make_title(self, result, titletype):
        sort = None
        if titletype == 'recent':
            title = ''.join((result['program'], ' - ', BeautifulSoup(result['shortDescription'], 'html.parser').text))
        elif titletype == 'reeksoplopend' or result['formattedBroadcastShortDate'] == '':
            title = ''.join((self._kodi_wrapper.get_localized_string(32095), ' ', str(result['episodeNumber']), ' - ', BeautifulSoup(result['shortDescription'], 'html.parser').text if result['shortDescription'] != '' else BeautifulSoup(result['title'], 'html.parser').text))
            sort = sortmethod.ALPHABET
        else:
            title = ''.join((result['formattedBroadcastShortDate'], ' - ', BeautifulSoup(result['shortDescription'], 'html.parser').text if result['shortDescription'] != '' else BeautifulSoup(result['title'], 'html.parser').text))

        return title, sort
