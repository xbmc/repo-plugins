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


import urlparse,urllib,json,re

from lamlib import bookmarks
from lamlib import directory
from lamlib import client
from lamlib import cache
from lamlib import workers


class indexer:
    def __init__(self):
        self.list = [] ; self.data = []
        self.base_link = 'http://www.antenna.gr'
        self.tvshows_link = 'http://www.antenna.gr/tv/doubleip/shows?version=3.0'
        self.tvshows_image = 'http://www.antenna.gr/imgHandler/326/'
        self.archive_link = ['http://www.antenna.gr/comedy', 'http://www.antenna.gr/drama', 'http://www.antenna.gr/family']
        self.episodes_link = 'http://www.antenna.gr/tv/doubleip/show?version=3.0&sid=%s'
        self.episodes_link_2 = 'http://www.antenna.gr/tv/doubleip/categories?version=3.0&howmany=1000&cid=%s'
        self.news_link = 'http://www.antenna.gr/webtv/categories?cid=3067'
        self.sports_link = 'http://www.antenna.gr/webtv/categories?cid=3062'
        self.weather_link = 'http://www.antenna.gr/webtv/categories?cid=3091'
        self.popular_link = 'http://www.antenna.gr/templates/data/webtvLatest?xsl=t&p=%s'
        self.play_link = 'http://www.antenna.gr/templates/data/jplayer?d=m&cid=%s'
        self.watch_link = 'http://www.antenna.gr/webtv/watch?cid=%s'
        self.live_link = 'http://antennatv-lh.akamaihd.net/i/live_1@329667/master.m3u8'


    def root(self):    
        self.list = [
        {
        'title': 30001,
        'action': 'tvshows',
        'icon': 'tvshows.png'
        },

        {
        'title': 30002,
        'action': 'archive',
        'icon': 'archive.png'
        },

        {
        'title': 30003,
        'action': 'popular',
        'icon': 'popular.png'
        },

        {
        'title': 30004,
        'action': 'news',
        'icon': 'news.png'
        },

        {
        'title': 30005,
        'action': 'sports',
        'icon': 'sports.png'
        },

        {
        'title': 30006,
        'action': 'weather',
        'icon': 'weather.png'
        },

        {
        'title': 30007,
        'action': 'bookmarks',
        'icon': 'bookmarks.png'
        },

        {
        'title': 30008,
        'action': 'live',
        'isFolder': 'False',
        'icon': 'live.png'
        }
        ]

        directory.add(self.list)
        return self.list


    def bookmarks(self):
        self.list = bookmarks.get()

        if self.list == None: return

        for i in self.list:
            bookmark = dict((k,v) for k, v in i.iteritems() if not k == 'next')
            bookmark['delbookmark'] = i['url']
            i.update({'cm': [{'title': 30502, 'query': {'action': 'deleteBookmark', 'url': json.dumps(bookmark)}}]})

        self.list = sorted(self.list, key=lambda k: k['title'].lower())

        directory.add(self.list)
        return self.list


    def tvshows(self):
        self.list = cache.get(self.item_list_1, 24, self.tvshows_link)

        if self.list == None: return

        for i in self.list: i.update({'action': 'episodes'})

        for i in self.list:
            bookmark = dict((k,v) for k, v in i.iteritems() if not k == 'next')
            bookmark['bookmark'] = i['url']
            i.update({'cm': [{'title': 30501, 'query': {'action': 'addBookmark', 'url': json.dumps(bookmark)}}]})

        self.list = sorted(self.list, key=lambda k: k['title'].lower())

        directory.add(self.list)
        return self.list


    def archive(self):
        self.list = cache.get(self.item_list_3, 24)

        if self.list == None: return

        for i in self.list: i.update({'action': 'reverseEpisodes'})

        for i in self.list:
            bookmark = dict((k,v) for k, v in i.iteritems() if not k == 'next')
            bookmark['bookmark'] = i['url']
            i.update({'cm': [{'title': 30501, 'query': {'action': 'addBookmark', 'url': json.dumps(bookmark)}}]})

        self.list = sorted(self.list, key=lambda k: k['title'].lower())

        directory.add(self.list)
        return self.list


    def episodes(self, url, reverse=False):
        self.list = cache.get(self.item_list_2, 1, url)

        if self.list == None: return

        for i in self.list: i.update({'action': 'play', 'isFolder': 'False'})

        if reverse == True:
            self.list = self.list[::-1]

        directory.add(self.list, content='files')
        return self.list


    def popular(self):
        self.list = cache.get(self.item_list_4, 1, self.popular_link)

        if self.list == None: return

        for i in self.list: i.update({'action': 'play', 'isFolder': 'False'})

        directory.add(self.list, content='files')
        return self.list


    def news(self):
        self.episodes(self.news_link)


    def sports(self):
        self.episodes(self.sports_link)


    def weather(self):
        self.episodes(self.weather_link)


    def play(self, url):
        directory.resolve(self.resolve(url))


    def live(self):
        directory.resolve(self.live_link, meta={'title': 'ANT1'})


    def item_list_1(self, url):
        try:
            result = client.request(url, mobile=True)

            items = re.findall('({.+?})', result)
        except:
            return

        for item in items:
            try:
                item = json.loads(item)

                title = item['teasertitle'].strip()
                title = client.replaceHTMLCodes(title)
                title = title.encode('utf-8')

                url = item['id'].strip()
                url = self.episodes_link % url
                url = client.replaceHTMLCodes(url)
                url = url.encode('utf-8')

                image = item['webpath'].strip()
                image = urlparse.urljoin(self.tvshows_image, image)
                if image == self.tvshows_image: raise Exception()
                image = client.replaceHTMLCodes(image)
                image = image.encode('utf-8')

                self.list.append({'title': title, 'url': url, 'image': image})
            except:
                pass

        return self.list


    def item_list_2(self, url):
        try:
            query = urlparse.parse_qs(urlparse.urlparse(url).query)

            if 'cid' in query:
        	    cid = query['cid'][0]
            elif 'sid' in query:
                result = client.request(url, mobile=True)
                cid = json.loads(result)['feed']['show']['videolib']
            else:
                result = client.request(url)
                cid = re.findall('/episodes\?cid=(\d+)', result)[0]

            url = self.episodes_link_2 % cid

            result = client.request(url, mobile=True)

            items = re.findall('({.+?})', result)
        except:
        	return

        for item in items:
            try:
                item = json.loads(item)

                title = item['caption'].strip()
                title = client.replaceHTMLCodes(title)
                title = title.encode('utf-8')

                url = item['contentid'].strip()
                url = self.watch_link % url
                url = client.replaceHTMLCodes(url)
                url = url.encode('utf-8')

                image = item['webpath'].strip()
                image = urlparse.urljoin(self.tvshows_image, image)
                if image == self.tvshows_image: raise Exception()
                image = client.replaceHTMLCodes(image)
                image = image.encode('utf-8')

                self.list.append({'title': title, 'url': url, 'image': image})
            except:
                pass

        return self.list


    def item_list_3(self):
        try:
            dupes = []

            threads = []
            for i in range(0, len(self.archive_link)):
                threads.append(workers.Thread(self.thread, self.archive_link[i], i))
                self.data.append('')
            [i.start() for i in threads]
            [i.join() for i in threads]

            result = ''
            for i in self.data: result += str(i)

            items = client.parseDOM(result, 'div', attrs = {'class': 'archiveFull'})
        except:
            return

        for item in items:
            try:
                title = client.parseDOM(item, 'span')[0]
                title = title.strip().upper()
                title = client.replaceHTMLCodes(title)
                title = title.encode('utf-8')

                url = client.parseDOM(item, 'a', ret='href')[0]
                if url in dupes: raise Exception()
                dupes.append(url)
                url = urlparse.urljoin(self.base_link, url)
                url = client.replaceHTMLCodes(url)
                url = url.encode('utf-8')

                image = client.parseDOM(item, 'img', ret='src')[0]
                image = urlparse.urljoin(self.base_link, image)
                image = client.replaceHTMLCodes(image)
                image = image.encode('utf-8')

                self.list.append({'title': title, 'url': url, 'image': image})
            except:
                pass

        return self.list


    def item_list_4(self, url):
        try:
            threads = []
            for i in range(0, 7):
                threads.append(workers.Thread(self.thread, url % str(i+1), i))
                self.data.append('')
            [i.start() for i in threads]
            [i.join() for i in threads]

            result = ''
            for i in self.data: result += str(i)

            items = result.replace('\n', '')
            items = re.findall('(<a\s.+?</a>)', items)
        except:
        	return

        for item in items:
            try:
                title = client.parseDOM(item, 'div')[0]
                title = title.strip().split('<')[0]
                title = client.replaceHTMLCodes(title)
                title = title.encode('utf-8')

                url = client.parseDOM(item, 'a', ret='href')[0]
                url = urlparse.urljoin(self.base_link, url)
                url = client.replaceHTMLCodes(url)
                url = url.encode('utf-8')

                image = client.parseDOM(item, 'img', ret='src')[0]
                image = urlparse.urljoin(self.base_link, image)
                image = client.replaceHTMLCodes(image)
                image = image.encode('utf-8')

                self.list.append({'title': title, 'url': url, 'image': image})
            except:
                pass

        return self.list


    def resolve(self, url):
        try:
            referer = url

            url = urlparse.parse_qs(urlparse.urlparse(url).query)['cid'][0]
            url = self.play_link % url

            result = client.request(url, referer=referer)

            url = client.parseDOM(result, '.+?', ret='file')[0]

            return url
        except:
            pass


    def thread(self, url, i):
        try:
            result = client.request(url)
            self.data[i] = result
        except:
            return


