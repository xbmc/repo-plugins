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


import urlparse,json,re

from resources.lib.modules import client
from resources.lib.modules import cache
from resources.lib.modules import directory
from resources.lib.modules import youtube


class indexer:
    def __init__(self):
        self.list = []
        self.base_link = 'http://screenrant.com'
        self.youtube_key = 'AIzaSyBOS4uSyd27OU0XV2KSdN3vT2UG_v0g9sI'
        self.youtube_link = 'UC2iUwfYi_1FCGGqhOUNx-iA'
        self.trailers_link = '/movie-trailers/page/1/'
        self.podcasts_link = '/podcasts/page/1/'


    def root(self):
        try:
            self.list = [
            {
            'title': 30001,
            'action': 'youtube',
            'url': self.youtube_link,
            'icon': 'news.png'
            },

            {
            'title': 30002,
            'action': 'videos',
            'url': self.trailers_link,
            'icon': 'trailers.png'
            },

            {
            'title': 30003,
            'action': 'videos',
            'url': self.podcasts_link,
            'icon': 'podcasts.png'
            },

            {
            'title': 30004,
            'action': 'bookmarks',
            'icon': 'bookmarks.png'
            }
            ]

            directory.add(self.list)
            return self.list
        except:
            pass


    def bookmarks(self):
        try:
            from resources.lib.modules import bookmarks

            self.list = bookmarks.get()

            for i in self.list:
                bookmark = dict((k,v) for k, v in i.iteritems() if not k == 'next')
                bookmark['delbookmark'] = i['url']
                i.update({'cm': [{'title': 30502, 'query': {'action': 'deleteBookmark', 'url': json.dumps(bookmark)}}]})

            directory.add(self.list, content='files')
            return self.list
        except:
            pass


    def youtube(self, url):
        try:
            self.list = cache.get(youtube.youtube(key=self.youtube_key).videos, 1, url, True)

            for i in self.list: i.update({'action': 'play', 'isFolder': 'False'})

            for i in self.list:
                bookmark = dict((k,v) for k, v in i.iteritems() if not k == 'next')
                bookmark['bookmark'] = i['url']
                i.update({'cm': [{'title': 30501, 'query': {'action': 'addBookmark', 'url': json.dumps(bookmark)}}]})

            for i in self.list: i.update({'nextlabel': 30500, 'nextaction': 'youtube'})

            directory.add(self.list, content='files')
            return self.list
        except:
            pass


    def videos(self, url):
        try:
            self.list = cache.get(self.item_list, 1, url)

            for i in self.list: i.update({'action': 'play', 'isFolder': 'False'})

            for i in self.list:
                bookmark = dict((k,v) for k, v in i.iteritems() if not k == 'next')
                bookmark['bookmark'] = i['url']
                i.update({'cm': [{'title': 30501, 'query': {'action': 'addBookmark', 'url': json.dumps(bookmark)}}]})

            for i in self.list: i.update({'nextlabel': 30500, 'nextaction': 'videos'})

            directory.add(self.list, content='files')
            return self.list
        except:
            pass


    def play(self, url):
        try:
            url = self.resolve(url)
            directory.resolve(url)
        except:
            pass


    def item_list(self, url):
        try:
            url = urlparse.urljoin(self.base_link, url)

            result = client.request(url)

            items = client.parseDOM(result, 'article')[0]
            items = client.parseDOM(items, 'li')
        except:
            return

        try:
            next, num = re.findall('(.+?/page/)(\d+)', url)[0]
            num = int(num) + 1
            if num > 10: raise Exception()
            next = '%s%s/' % (next, num)
            next = client.replaceHTMLCodes(next)
            next = next.encode('utf-8')
        except:
            next = ''

        for item in items:
            try:
                title = client.parseDOM(item, 'span', ret='data-alt')[0]
                title = client.replaceHTMLCodes(title)
                title = title.encode('utf-8')

                url = client.parseDOM(item, 'a', ret='href')[0]
                url = client.replaceHTMLCodes(url)
                url = url.encode('utf-8')

                image = client.parseDOM(item, 'img', ret='src')[0]
                image = client.replaceHTMLCodes(image)
                image = image.encode('utf-8')

                self.list.append({'title': title, 'url': url, 'image': image, 'next': next})
            except:
                pass

        return self.list


    def resolve(self, url):
        try:
            if url.startswith('plugin://'): return url

            url = urlparse.urljoin(self.base_link, url)

            result = client.request(url)

            netloc = ['brightcove', 'youtube', 'soundcloud', 'podcasts.screenrant', 'media.blubrry']

            src = client.parseDOM(result, 'iframe', ret='src')
            src += client.parseDOM(result, 'audio', ret='src')
            src = [(i, urlparse.urlparse(i).netloc) for i in src]
            src = [i[0] for i in src if any(x in i[1] for x in netloc)][0]
            src = client.replaceHTMLCodes(src)

            try:
                url = re.findall('(?:youtube.com|youtu.be)/(?:embed/|.+?\?v=|.+?\&v=|v/)([0-9A-Za-z_\-]+)', src)[0]
                url = 'plugin://plugin.video.youtube/play/?video_id=%s' % url
                return url
            except:
                pass

            try:
                if not 'brightcove' in src: raise Exception()

                pk = client.request('http:' + re.findall('(//.+)', src)[0])
                pk = re.findall('policyKey\s*:\s*(?:[\\\]"|"|[\\\]\'|\')(.+?)(?:[\\\]"|"|[\\\]\'|\')', pk)[0]

                headers = {'Accept': 'application/json;pk=%s' % pk}

                url = re.findall('(?:brightcove).+?/(.+?)/.+?videoId=([0-9A-Za-z_\-]+)', src)[0]
                url = 'https://edge.api.brightcove.com/playback/v1/accounts/%s/videos/%s' % url

                url = client.request(url, headers=headers)
                url = json.loads(url)['sources']
                url = [(i['src'], i['size']) for i in url if 'size' in i and 'src' in i]
                url = sorted(url, key=lambda x: x[1], reverse=True)
                url = url[0][0]

                return url
            except:
                pass

            try:
                url = re.findall('soundcloud.+?/tracks/([0-9A-Za-z_\-]+)', src)[0]
                url = 'https://api.soundcloud.com:443/tracks/%s/stream?client_id=cUa40O3Jg3Emvp6Tv4U6ymYYO50NUGpJ' % url

                url = client.request(url, output='geturl')
                return url
            except:
                pass

            try:
                if not ('podcasts.screenrant' in src or 'media.blubrry' in src): raise Exception()
                return src
            except:
                pass

        except:
            pass


