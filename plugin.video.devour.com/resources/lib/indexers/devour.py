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

from resources.lib.modules import cache
from resources.lib.modules import client
from resources.lib.modules import control
from resources.lib.modules import directory


class indexer:
    def __init__(self):
        self.list = []
        self.base_link = 'http://devour.com'
        self.channels_link = '/channels/'
        self.latest_link = '/1/'
        self.popular_link = '/popular/1/'
        self.leftovers_link = '/leftovers/1/'
        self.search_link = '/search/%s/1/'


    def root(self):
        try:
            self.list = [
            {
            'title': 30001,
            'action': 'videos',
            'url': self.latest_link,
            'icon': 'latest.png'
            },

            {
            'title': 30002,
            'action': 'videos',
            'url': self.popular_link,
            'icon': 'popular.png'
            },

            {
            'title': 30003,
            'action': 'videos',
            'url': self.leftovers_link,
            'icon': 'leftovers.png'
            },

            {
            'title': 30004,
            'action': 'channels',
            'icon': 'channels.png'
            },

            {
            'title': 30005,
            'action': 'bookmarks',
            'icon': 'bookmarks.png'
            },

            {
            'title': 30006,
            'action': 'search',
            'icon': 'search.png'
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

            for i in self.list: i.update({'genre': i['plot']})

            directory.add(self.list, content='files')
            return self.list
        except:
            pass


    def channels(self):
        try:
            self.list = cache.get(self.item_list_1, 24, self.channels_link)

            for i in self.list: i.update({'action': 'videos'})

            directory.add(self.list)
            return self.list
        except:
            pass


    def search(self):
        try:
            t = control.lang(30006).encode('utf-8')
            k = control.keyboard('', t) ; k.doModal()
            query = k.getText() if k.isConfirmed() else None

            if (query == None or query == ''): return

            url = self.search_link % urllib.quote_plus(query.lower())

            self.videos(url)
        except:
            pass


    def videos(self, url):
        try:
            self.list = cache.get(self.item_list_2, 1, url)

            for i in self.list: i.update({'action': 'play', 'isFolder': 'False'})

            for i in self.list:
                bookmark = dict((k,v) for k, v in i.iteritems() if not k == 'next')
                bookmark['bookmark'] = i['url']
                i.update({'cm': [{'title': 30501, 'query': {'action': 'addBookmark', 'url': json.dumps(bookmark)}}]})

            for i in self.list: i.update({'nextlabel': 30500, 'nextaction': 'videos'})

            for i in self.list: i.update({'genre': i['plot']})

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


    def item_list_1(self, url):
        try:
            url = urlparse.urljoin(self.base_link, url)

            result = client.request(url)

            items = client.parseDOM(result, 'li', attrs = {'class': 'article.+?'})
        except:
            return

        for item in items:
            try:
                title = client.parseDOM(item, 'h1', attrs = {'class': 'article.+?'})[0]
                title = client.parseDOM(title, 'a')[0]
                title = re.sub('<.+?/>|\n|\t', ' ', title).strip()
                title = client.replaceHTMLCodes(title)
                title = title.encode('utf-8')

                url = client.parseDOM(item, 'a', ret='href')[0]
                url = re.sub('.+?//.+?/','/', url)
                url = re.sub('(?:/|)(\d+)(?:/|)$|/$', '', url)
                url += '/1/'
                url = client.replaceHTMLCodes(url)
                url = url.encode('utf-8')

                image = client.parseDOM(item, 'img', ret='src')[0]
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

            items = client.parseDOM(result, 'li', attrs = {'class': 'article.+?'})
        except:
            return

        try:
            nurl = re.findall('(.+?/)(\d+)(/)$', url)[0]
            nurl = nurl[0] + str(int(nurl[1]) + 1) + nurl[2]

            next = client.parseDOM(result, 'a', ret='href')
            next = [urlparse.urljoin(self.base_link, i) for i in next]
            next = [i + '/' if not i.endswith('/') else i for i in next]
            next = [i for i in next if i == nurl][0]
            next = re.sub('.+?//.+?/','/', next)
            next = next.encode('utf-8')
        except:
            next = ''

        for item in items:
            try:
                title = client.parseDOM(item, 'h1', attrs = {'class': 'article.+?'})[0]
                title = client.parseDOM(title, 'a')[0]
                title = re.sub('<.+?/>|\n|\t', ' ', title).strip()
                title = client.replaceHTMLCodes(title)
                title = title.encode('utf-8')

                plot = client.parseDOM(item, 'p')
                try: plot = client.parseDOM(plot[-1], 'a')[0]
                except: plot = '0'
                plot = re.sub('<.+?/>|\n|\t', ' ', plot).strip()
                plot = client.replaceHTMLCodes(plot)
                plot = plot.encode('utf-8')

                url = client.parseDOM(item, 'a', ret='href')[0]
                url = re.sub('.+?//.+?/','/', url)
                url = client.replaceHTMLCodes(url)
                url = url.encode('utf-8')

                image = client.parseDOM(item, 'img', ret='src')[0]
                image = client.replaceHTMLCodes(image)
                image = image.encode('utf-8')

                self.list.append({'title': title, 'plot': plot, 'url': url, 'image': image, 'next': next})
            except:
                pass

        return self.list


    def resolve(self, url):
        try:
            url = urlparse.urljoin(self.base_link, url)

            result = client.request(url)


            url = re.findall('(?:youtube.com|youtu.be)/(?:embed/|.+?\?v=|.+?\&v=|v/)([0-9A-Za-z_\-]+)', result)

            if len(url) > 0:
                return 'plugin://plugin.video.youtube/play/?video_id=%s' % url[0]


            url = re.findall('vimeo\.com/(?:video/)?([0-9a-zA-Z]+)', result)

            if len(url) > 0:
                url = 'http://player.vimeo.com/video/%s/config' % url[0]

                url = client.request(url) ; url = json.loads(url)

                url = url['request']['files']['progressive']
                url = [i['url'] for i in url if 'url' in i][-1]

                return url
        except:
            pass


