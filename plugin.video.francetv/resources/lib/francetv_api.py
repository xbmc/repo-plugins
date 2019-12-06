# Copyright (C) 2018 melmorabity

# This program is free software; you can redistribute it and/or modify it under the terms of the GNU
# General Public License as published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.

# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without
# even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.

# You should have received a copy of the GNU General Public License along with this program; if not,
# write to the Free Software Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301, USA.


from __future__ import unicode_literals

import time
import sys

import dateutil.parser
from requests import Session
from requests.exceptions import RequestException


class FranceTVAPIException(Exception):
    pass


class FranceTVAPI(object):
    _BASE_URL = 'https://www.france.tv'
    _API_URL = 'http://api-front.yatta.francetv.fr'
    _VIDEO_API_URL = 'http://sivideo.webservices.francetelevisions.fr/tools/getInfosOeuvre/v2/'
    _GEOLOCATION_API_URL = 'http://geo.francetv.fr/ws/edgescape.json'
    _VIDEO_TOKEN_URL = 'http://hdfauthftv-a.akamaihd.net/esi/TA'

    class _UTF8DictNotEmpty(dict):
        def __setitem__(self, key, value):
            if value:
                dict.__setitem__(self, key, value)
            else:
                if key in self:
                    del self[key]

    def _http_request(self, _url, json=True, **query):
        if _url and not _url.startswith(('http://', 'https://')):
            _url = self._API_URL + _url

        try:
            with Session() as session:
                response = session.get(_url, params=query)
                return response.json() if json else response.text
        except RequestException as ex:
            raise FranceTVAPIException(ex)

    def _parse_media_data(self, media_data):
        result = self._UTF8DictNotEmpty()
        if not media_data:
            return result

        for pattern in media_data.get('patterns') or []:
            if pattern.get('type') == 'carre' and 'w:400' in pattern.get('urls') or {}:
                thumb_file = pattern['urls'].get('w:400')
                if thumb_file:
                    result['thumb'] = self._BASE_URL + thumb_file
            elif pattern.get('type') == 'vignette_16x9' and 'w:1024' in pattern.get('urls') or {}:
                fanart_file = pattern['urls'].get('w:1024')
                if fanart_file:
                    result['fanart'] = self._BASE_URL + fanart_file

        return result

    def _parse_topic_data(self, data, artwork=False):
        metadata = self._UTF8DictNotEmpty()
        info = self._UTF8DictNotEmpty()
        art = self._UTF8DictNotEmpty()

        result = (metadata, info, art)

        if not data:
            return result

        metadata['channel_id'] = data.get('channel')

        topic_id = data.get('url_complete')
        if topic_id:
            metadata['id'] = topic_id.replace('/', '_')

        info['title'] = data.get('label')
        if 'title' in info:
            info['title'] = info['title'].capitalize()
        info['plot'] = data.get('description') or data.get('synopsis') or data.get('base_line') \
                       or info.get('title')

        if artwork:
            art.update(self._parse_media_data(data.get('media_image')))

        return result

    def _parse_video_data(self, data, live=False):
        metadata = self._UTF8DictNotEmpty()
        info = self._UTF8DictNotEmpty()
        art = self._UTF8DictNotEmpty()

        if not data:
            return (metadata, info, art)

        info['mediatype'] = 'video'
        info['plot'] = data.get('text')
        info['plotoutline'] = data.get('headline_title')
        info['director'] = data.get('director')
        info['year'] = data.get('year') or data.get('production_year')
        info['season'] = data.get('saison')
        info['episode'] = data.get('episode')

        presenter = data.get('presenter')
        if presenter:
            info['cast'] = [presenter]
        cast = [d for d in (data.get('casting') or '').split(', ') if d]
        info['cast'] = info.get('cast', []) + cast

        if live:
            metadata['channel_id'] = data.get('channel')

        for media in data.get('content_has_medias') or []:
            if media.get('type') == 'main':
                media_data = media.get('media')
                if media_data:
                    metadata['video_id'] = media_data.get('si_direct_id' if live else 'si_id')
                    metadata['mpaa'] = media_data.get('rating_csa')
                if not live:
                    info['duration'] = media_data.get('duration')
                begin_date = media_data.get('begin_date')
                if begin_date:
                    begin_date = dateutil.parser.parse(begin_date)
                    info['date'] = begin_date.strftime('%d.%m.%Y')
                    info['dateadded'] = begin_date.strftime('%Y-%m-%d %H:%M:%S')
            elif media.get('type') == 'image':
                art.update(self._parse_media_data(media.get('media')))

        program_title = None
        program_subtitle = data.get('title')
        for taxonomy in data.get('content_has_taxonomys') or []:
            taxonomy_data = taxonomy.get('taxonomy') or {}
            if taxonomy.get('type') == 'channel':
                # A video may have been broadcasted on several channels. Take the first one
                # available
                if 'channel_name' not in metadata:
                    metadata['channel_name'] = taxonomy_data.get('label')
                if 'channel_id' not in metadata:
                    metadata['channel_id'] = taxonomy_data.get('url')
            elif taxonomy.get('type') == 'program':
                program_title = taxonomy_data.get('label')
                if not art:
                    # Use program artwork if TV show artwork is unavailable
                    art.update(self._parse_media_data(taxonomy_data.get('media_image')))
            elif taxonomy.get('type') == 'category':
                if taxonomy_data.get('type') == 'sous_categorie':
                    info['genre'] = taxonomy_data.get('label')
                elif 'genre' not in info and taxonomy_data.get('type') == 'categorie':
                    info['genre'] = taxonomy_data.get('label')

        if 'genre' in info:
            info['genre'] = info['genre'].capitalize()

        if not program_title and program_subtitle:
            program_title = program_subtitle
        if program_title and program_subtitle and program_title != program_subtitle:
            program_title += ' - ' + program_subtitle

        if live:
            info['title'] = metadata.get('channel_name')
            info['plot'] = program_title
        else:
            info['title'] = program_title

        return (metadata, info, art)

    def get_channels(self):
        result = []
        data = self._http_request('/standard/publish/channels')
        if not data:
            return result

        for item in data.get('result') or []:
            result.append(self._parse_topic_data(item))

        return result

    def get_categories(self, channel=None):
        result = []
        if channel:
            url = '/standard/publish/channels/{}/categories'.format(channel)
        else:
            url = '/standard/publish/categories'

        data = self._http_request(url)
        if not data:
            return result

        for item in data.get('result') or []:
            result.append(self._parse_topic_data(item))

        return result

    def get_subcategories(self, category):
        result = []
        data = self._http_request('/standard/publish/categories/{}'.format(category))
        if not data:
            return result

        for item in data.get('sub') or []:
            result.append(self._parse_topic_data(item))

        return result

    def get_tv_shows(self, channel=None, category=None):
        result = []
        if category:
            url = '/standard/publish/categories/{}/programs'.format(category)
            if channel:
                url += '/' + channel
        elif channel:
            url = '/standard/publish/channels/{}/programs'.format(channel)
        else:
            return result

        data = self._http_request(url, sort='title', filter='with-no-vod,only-visible')
        if not data:
            return result

        for item in data.get('result') or []:
            result.append(self._parse_topic_data(item, artwork=True))

        return result

    def get_lives(self):
        result = []
        data = self._http_request('/standard/edito/directs')
        if not data:
            return result

        for item in [d['collection'][0] for d in (data.get('result') or []) if d.get('collection')]:
            result.append(self._parse_video_data(item, live=True))

        return result

    def get_videos(self, channel=None, category=None, tv_show=None, size=20, page=0):
        result = {'videos': [], 'next': False}
        if tv_show:
            url = '/standard/publish/taxonomies/{}/contents'.format(tv_show)
        elif category:
            url = '/standard/publish/categories/{}/contents'.format(category)
            if channel:
                url += '/' + channel
        elif channel:
            url = '/standard/publish/channels/{}/contents'.format(channel)
        else:
            return result

        data = self._http_request(url, size=size, page=page, sort='begin_date:desc',
                                  filter='with-no-vod,only-visible')
        if not data:
            return result

        for item in data.get('result') or []:
            result['videos'].append(self._parse_video_data(item))

        if data.get('cursor'):
            result['next'] = bool(data['cursor'].get('next') and data['cursor'].get('last'))

        return result

    def _get_country_code(self):
        data = self._http_request(self._GEOLOCATION_API_URL)
        try:
            return data['reponse']['geo_info']['country_code']
        except (KeyError, TypeError):
            return None

    def get_video_stream(self, video_id, subtitles=False):
        results = self._UTF8DictNotEmpty()
        data = self._http_request(self._VIDEO_API_URL, idDiffusion=video_id)
        if not data:
            return results

        for video in data.get('videos') or []:
            video_url = video.get('url')
            if not video_url:
                continue

            # Ignore georestricted streams
            countries = video.get('geoblocage')
            if countries and self._get_country_code() not in countries:
                continue

            # Ignore streaming protocols not natively supported by Kodi
            video_format = video.get('format')
            if not video_format or video_format == 'dash' or 'hds' in video_format:
                continue

            # Ignore expired content
            now = time.time()
            for interval in video.get('plages_ouverture') or []:
                if (interval.get('debut') or 0) <= now <= (interval.get('fin') or sys.maxsize):
                    break
            else:
                continue

            video_url = self._http_request(self._VIDEO_TOKEN_URL, json=False, url=video_url)
            results['video'] = video_url
            break

        if subtitles:
            subtitle_urls = []
            for sub in data.get('subtitles') or []:
                # TTML subtitles may be available but are not supported by Kodi
                if sub.get('format') == 'vtt':
                    subtitle_urls.append(sub.get('url'))

            results['subtitles'] = subtitle_urls

        return results
