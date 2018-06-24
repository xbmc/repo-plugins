# -*- coding: utf-8 -*-

'''
    Montreal Greek TV Add-on
    Author: greektimes

        License summary below, for more details please read license.txt file

        This program is free software: you can redistribute it and/or modify
        it under the terms of the GNU General Public License as published by
        the Free Software Foundation, either version 2 of the License, or
        (at your option) any later version.
        This program is distributed in the hope that it will be useful,
        but WITHOUT ANY WARRANTY; without even the implied warranty of
        MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
        GNU General Public License for more details.
        You should have received a copy of the GNU General Public License
        along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''
from __future__ import absolute_import, division, unicode_literals

import re, json
from resources.lib.compat import urlparse, parse_qs, quote_plus, range
from resources.lib import control, directory
import requests
from CommonFunctions import parseDOM


class youtube(object):

    def __init__(self, key='', api_key_setting='yt_api_key'):

        self.list = [];  self.data = []

        self.base_link = 'http://www.youtube.com/'
        self.base_addon = 'plugin://plugin.video.youtube/'
        self.google_base_link = 'https://www.googleapis.com/youtube/v3/'
        self.key_link = '&key={0}'.format(control.setting(api_key_setting) or key)
        self.playlists_link = self.google_base_link + 'playlists?part=snippet&maxResults=50&channelId=%s'
        self.playlist_link = self.google_base_link + 'playlistItems?part=snippet&maxResults=50&playlistId=%s'
        self.videos_link = self.google_base_link + 'search?part=snippet&order=date&maxResults=50&channelId=%s'
        self.content_link = self.google_base_link + 'videos?part=contentDetails&id=%s'
        self.search_link = self.google_base_link + 'search?part=snippet&type=video&maxResults=5&q=%s'
        self.youtube_search = self.google_base_link + 'search?q='
        self.play_link = self.base_addon + 'play/?video_id={}'

    def playlists(self, url, limit=5):

        url = self.playlists_link % url + self.key_link
        return self._playlist(url, limit)

    def playlist(self, url, pagination=False, limit=5):

        cid = url.split('&')[0]
        url = self.playlist_link % url + self.key_link
        return self._video_list(cid, url, pagination, limit)

    def videos(self, url, pagination=False, limit=5):

        cid = url.split('&')[0]
        url = self.videos_link % url + self.key_link
        return self._video_list(cid, url, pagination, limit)

    def _playlist(self, url, limit):

        try:
            result = requests.get(url).text
            result = json.loads(result)
            items = result['items']
        except BaseException:
            pass

        for i in list(range(1, limit)):
            try:
                if not 'nextPageToken' in result:
                    raise BaseException()
                next_ = url + '&pageToken=' + result['nextPageToken']
                result = requests.get(next_).text
                result = json.loads(result)
                items += result['items']
            except BaseException:
                pass

        for item in items:
            try:
                title = item['snippet']['title']
                try:
                    title = title.encode('utf-8')
                except AttributeError:
                    pass

                url = item['id']
                try:
                    url = url.encode('utf-8')
                except AttributeError:
                    pass

                image = item['snippet']['thumbnails']['high']['url']
                if '/default.jpg' in image:
                    raise BaseException()
                try:
                    image = image.encode('utf-8')
                except AttributeError:
                    pass

                self.list.append({'title': title, 'url': url, 'image': image})
            except BaseException:
                pass

        return self.list

    def _video_list(self, cid, url, pagination, limit):

        try:
            result = requests.get(url).text
            result = json.loads(result)
            items = result['items']
        except BaseException:
            pass

        for i in list(range(1, limit)):

            try:
                if pagination is True:
                    raise BaseException()
                if not 'nextPageToken' in result:
                    raise BaseException()
                page = url + '&pageToken=' + result['nextPageToken']
                result = requests.get(page).text
                result = json.loads(result)
                items += result['items']
            except BaseException:
                pass

        try:
            if pagination is False:
                raise BaseException()
            next = cid + '&pageToken=' + result['nextPageToken']
        except BaseException:
            next = ''

        for item in items:
            try:
                title = item['snippet']['title']
                try:
                    title = title.encode('utf-8')
                except AttributeError:
                    pass

                try:
                    url = item['id']['videoId']
                except KeyError:
                    url = item['snippet']['resourceId']['videoId']

                try:
                    url = url.encode('utf-8')
                except AttributeError:
                    pass

                image = item['snippet']['thumbnails']['high']['url']
                if '/default.jpg' in image:
                    raise BaseException()
                try:
                    image = image.encode('utf-8')
                except AttributeError:
                    pass

                append = {'title': title, 'url': url, 'image': image}
                if next != '':
                    append['next'] = next
                self.list.append(append)
            except BaseException:
                pass

        for item in list(range(0, len(self.list))):
            try:
                vid = self.list[item]['url']

                self.list[item]['url'] = self.play_link.format(vid)

                d = [(i['id'], i['contentDetails']) for i in items]
                d = [i for i in d if i[0] == vid]
                d = d[0][1]['duration']

                duration = 0
                try:
                    duration += 60 * 60 * int(re.findall('(\d*)H', d)[0])
                except BaseException:
                    pass
                try:
                    duration += 60 * int(re.findall('(\d*)M', d)[0])
                except BaseException:
                    pass
                try:
                    duration += int(re.findall('(\d*)S', d)[0])
                except BaseException:
                    pass
                duration = str(duration)

                self.list[item]['duration'] = duration
            except BaseException:
                pass

        return self.list

    def thread(self, url, i):

        try:
            result = requests.get(url).text
            self.data[i] = result
        except BaseException:
            return

    def play(self, name, url=None, as_script=True):

        try:

            url = self.worker(name, url)
            if url is None:
                return

            title = control.infoLabel('listitem.title')
            if title == '':
                title = control.infoLabel('listitem.label')
            icon = control.infoLabel('listitem.icon')

            item = control.item(path=url, iconImage=icon, thumbnailImage=icon)

            try:
                item.setArt({'icon': icon})
            except BaseException:
                pass

            item.setInfo(type='Video', infoLabels={'title': title})

            if as_script:
                control.player.play(url, item)
            else:
                directory.resolve(url, meta={'title': title}, icon=icon)

        except BaseException:

            pass

    def worker(self, name, url):

        try:

            if url.startswith(self.base_link):
                url = self.resolve(url)
                if url is None:
                    raise BaseException()
                return url
            elif not url.startswith('http://'):
                url = self.play_link.format(url)
                url = self.resolve(url)
                if url is None:
                    raise BaseException()
                return url
            else:
                raise BaseException()

        except BaseException:

            query = name + ' trailer'
            query = self.youtube_search + query
            url = self.search(query)

            if url is None:
                return

            return url

    def search(self, url):

        try:
            query = parse_qs(urlparse(url).query)['q'][0]

            url = self.search_link % quote_plus(query) + self.key_link

            result = requests.get(url).text

            items = json.loads(result)['items']
            items = [(i['id']['videoId']) for i in items]

            for url in items:
                url = self.resolve(url)
                if url is not None:
                    return url
        except BaseException:
            return

    def resolve(self, url):

        try:

            id = url.split('?v=')[-1].split('/')[-1].split('?')[0].split('&')[0]
            result = requests.get('http://www.youtube.com/watch?v=%s' % id).text

            message = parseDOM(result, 'div', attrs={'id': 'unavailable-submessage'})
            message = ''.join(message)

            alert = parseDOM(result, 'div', attrs={'id': 'watch7-notification-area'})

            if len(alert) > 0:
                raise BaseException()
            if re.search('[a-zA-Z]', message):
                raise BaseException()

            url = self.play_link.format(id)

            return url

        except BaseException:

            return
