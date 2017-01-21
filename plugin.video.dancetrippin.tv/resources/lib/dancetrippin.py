# -*- coding: utf-8 -*-

'''
    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''


import urllib,urlparse,json,re

from lamlib import bookmarks
from lamlib import cache
from lamlib import client
from lamlib import control
from lamlib import directory


class indexer:
    def __init__(self):
        self.list = []
        self.base_link = 'http://www.dancetrippin.tv'
        self.videos_link = '/ajax.cfm?datatype=videos&cat=12'
        self.djsets_link = '/ajax.cfm?datatype=videos&cat=-12'
        self.djmixes_link = '/ajax.cfm?datatype=djmixes'
        self.channels_link = '/channels/'
        self.playlists_link = '/playlists/'
        self.artists_link = '/artists/'


    def root(self):
        self.list = [
        {
        'title': 32001,
        'action': 'videos',
        'url': self.videos_link,
        'icon': 'videos.png'
        },

        {
        'title': 32002,
        'action': 'videos',
        'url': self.djsets_link,
        'icon': 'djsets.png'
        },

        {
        'title': 32003,
        'action': 'videos',
        'url': self.djmixes_link,
        'icon': 'djmixes.png'
        },

        {
        'title': 32004,
        'action': 'videos2',
        'url': self.channels_link,
        'icon': 'channels.png'
        },

        {
        'title': 32005,
        'action': 'categories',
        'url': self.artists_link,
        'icon': 'artists.png'
        },

        {
        'title': 32006,
        'action': 'categories2',
        'url': self.playlists_link,
        'icon': 'playlists.png'
        },

        {
        'title': 32007,
        'action': 'bookmarks',
        'icon': 'bookmarks.png'
        }
        ]

        directory.add(self.list, content='videos')
        return self.list


    def bookmarks(self):
        self.list = bookmarks.get()

        if self.list == None: return

        for i in self.list:
            bookmark = dict((k,v) for k, v in i.iteritems() if not k == 'next')
            bookmark['delbookmark'] = i['url']
            i.update({'cm': [{'title': 32502, 'query': {'action': 'deleteBookmark', 'url': json.dumps(bookmark)}}]})

        directory.add(self.list, content='videos')
        return self.list


    def categories(self, url):
        self.list = cache.get(self.item_list_2, 24, url)

        if self.list == None: return

        for i in self.list: i.update({'action': 'videos2'})

        directory.add(self.list, content='videos')
        return self.list


    def categories2(self, url):
        self.list = cache.get(self.item_list_3, 24, url)

        if self.list == None: return

        for i in self.list: i.update({'action': 'videos2'})

        directory.add(self.list, content='videos')
        return self.list


    def videos(self, url):
        self.list = cache.get(self.item_list_1, 1, url)

        if self.list == None: return

        for i in self.list: i.update({'action': 'play', 'isFolder': 'False'})

        for i in self.list:
            bookmark = dict((k,v) for k, v in i.iteritems() if not k == 'next')
            bookmark['bookmark'] = i['url']
            i.update({'cm': [{'title': 32501, 'query': {'action': 'addBookmark', 'url': json.dumps(bookmark)}}]})

        directory.add(self.list, content='videos')
        return self.list


    def videos2(self, url):
        self.list = cache.get(self.item_list_2, 1, url)

        if self.list == None: return

        for i in self.list: i.update({'action': 'play', 'isFolder': 'False'})

        for i in self.list:
            bookmark = dict((k,v) for k, v in i.iteritems() if not k == 'next')
            bookmark['bookmark'] = i['url']
            i.update({'cm': [{'title': 32501, 'query': {'action': 'addBookmark', 'url': json.dumps(bookmark)}}]})

        directory.add(self.list, content='videos')
        return self.list


    def play(self, url):
        url = self.resolve(url)
        if url == None: return

        directory.resolve(url)


    def item_list_1(self, url):
        try:
            url = urlparse.urljoin(self.base_link, url)

            result = client.request(url)

            items = json.loads(result)
        except:
            return

        for item in items:
            try:
                title = item['title']
                title = title.strip().strip('-').strip()
                title = client.replaceHTMLCodes(title)
                title = title.encode('utf-8')

                url = item['videourl']
                url = re.sub('.+?//.+?/','/', url)
                url = url.replace('/videos/dj-mixes/', '/djmixes/play/')
                url = client.replaceHTMLCodes(url)
                url = url.encode('utf-8')

                image = item['image']
                image = image.replace(' ', '%20')
                image = urlparse.urljoin(self.base_link, image)
                image = client.replaceHTMLCodes(image)
                image = image.encode('utf-8')

                self.list.append({'title': title, 'url': url, 'image': image})
            except:
                pass

        return self.list


    def item_list_2(self, url):
        try:
            url = urlparse.urljoin(self.base_link, url)

            result = client.request(url)

            items = client.parseDOM(result, 'div', attrs = {'class': 'singl.+?'})
        except:
            return

        for item in items:
            try:
                t = client.parseDOM(item, 'div', attrs = {'class': 'channel-info'})
                t = client.parseDOM(t, 'strong')
                t = ' - [I]%s[/I]' % t[0] if t else ''

                title = client.parseDOM(item, 'a', ret='title')
                title += client.parseDOM(item, 'h3')
                title = title[0].strip() + t
                title = client.replaceHTMLCodes(title)
                title = title.encode('utf-8')

                url = client.parseDOM(item, 'a', ret='href')[0]
                url = re.sub('.+?//.+?/','/', url)
                url = client.replaceHTMLCodes(url)
                url = url.encode('utf-8')

                image = re.findall('url\((.+?)\)', item)[0]
                image = image.strip('\'').strip('\"')
                if not '/' in image: image = '/assets/www.dancetrippin.tv/artists/' + image
                image = image.replace(' ', '%20')
                image = urlparse.urljoin(self.base_link, image)
                image = client.replaceHTMLCodes(image)
                image = image.encode('utf-8')

                self.list.append({'title': title, 'url': url, 'image': image})
            except:
                pass

        return self.list


    def item_list_3(self, url):
        try:
            url = urlparse.urljoin(self.base_link, url)

            result = client.request(url)

            items = client.parseDOM(result, 'div', attrs = {'class': 'global-playlist-holder'})
        except:
            return

        for item in items:
            try:
                title = client.parseDOM(item, 'h2')[0]
                title = [i for i in title.splitlines() if 'strong' in i][0]
                title = re.sub('<.+?>', '', title).strip()
                title = client.replaceHTMLCodes(title)
                title = title.encode('utf-8')

                url = client.parseDOM(item, 'a', ret='href')[0]
                url = re.sub('.+?//.+?/','/', url)
                url = client.replaceHTMLCodes(url)
                url = url.encode('utf-8')

                image = re.findall('url\((.+?)\)', item)[0]
                image = image.strip('\'').strip('\"')
                if not '/' in image: image = '/assets/www.dancetrippin.tv/artists/' + image
                image = image.replace(' ', '%20')
                image = urlparse.urljoin(self.base_link, image)
                image = client.replaceHTMLCodes(image)
                image = image.encode('utf-8')

                self.list.append({'title': title, 'url': url, 'image': image})
            except:
                pass

        return self.list


    def resolve(self, url):
        try:
            url = urlparse.urljoin(self.base_link, url)

            result = client.request(url)

            src = client.parseDOM(result, 'div', attrs = {'id': 'videoplayer'})
            src += client.parseDOM(result, 'div', attrs = {'id': 'player-holder'})

            try:
                url = re.findall('(?:youtube.com|youtu.be)/(?:embed/|.+?\?v=|.+?\&v=|v/)([0-9A-Za-z_\-]+)', src[0])[0]
                url = 'plugin://plugin.video.youtube/play/?video_id=%s' % url
                return url
            except:
                pass

            try:
                url = re.findall('soundcloud.+?/tracks/([0-9A-Za-z_\-]+)', src[0])[0]
                url = 'https://api.soundcloud.com:443/tracks/%s/stream?client_id=cUa40O3Jg3Emvp6Tv4U6ymYYO50NUGpJ' % url
                url = client.request(url, output='geturl')
                return url
            except:
                pass

            try:
                url = client.parseDOM(src[0], 'source', ret='src')[0]
                url = client.replaceHTMLCodes(url)
                url = urlparse.urljoin(self.base_link, url)
                url = client.request(url, output='geturl')
                return url
            except:
                pass
        except:
            pass


