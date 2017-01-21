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


import urlparse,urllib,json,datetime,re

from lamlib import bookmarks
from lamlib import directory
from lamlib import control
from lamlib import client
from lamlib import cache
from lamlib import workers


class indexer:
    def __init__(self):
        self.list = [] ; self.data = []
        self.base_link = 'http://www.skai.gr'
        self.archive_link = 'http://www.skai.gr/player/tvlive/'
        self.tvshows_link = 'http://www.skai.gr/Ajax.aspx?m=Skai.TV.ProgramListView&la=0&Type=TV&Day=%s'
        self.podcasts_link = 'http://www.skai.gr/Ajax.aspx?m=Skai.TV.ProgramListView&la=0&Type=Radio&Day=%s'
        self.popular_link = 'http://www.skai.gr/Ajax.aspx?m=Skai.Player.ItemView&cid=0'
        self.news_link = 'http://www.skai.gr/Ajax.aspx?m=Skai.Player.ItemView&cid=6&alid=43505'
        self.sports_link = 'http://www.skai.gr/Ajax.aspx?m=Skai.Player.ItemView&cid=6&alid=14'
        self.episodes_link = 'http://www.skai.gr/Ajax.aspx?m=Skai.Player.ItemView&cid=6&alid=%s'
        self.live_link = 'http://www.skai.gr/ajax.aspx?m=NewModules.LookupMultimedia&mmid=/Root/TVLive'


    def root(self):
        self.list = [
        {
        'title': 32001,
        'action': 'live',
        'isFolder': 'False',
        'icon': 'live.png'
        },

        {
        'title': 32002,
        'action': 'tvshows',
        'icon': 'tvshows.png'
        },

        {
        'title': 32003,
        'action': 'podcasts',
        'icon': 'podcasts.png'
        },

        {
        'title': 32004,
        'action': 'archive',
        'icon': 'archive.png'
        },

        {
        'title': 32005,
        'action': 'popular',
        'icon': 'popular.png'
        },

        {
        'title': 32006,
        'action': 'news',
        'icon': 'news.png'
        },

        {
        'title': 32007,
        'action': 'sports',
        'icon': 'sports.png'
        },

        {
        'title': 32008,
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

        self.list = sorted(self.list, key=lambda k: k['title'].lower())

        directory.add(self.list, content='videos')
        return self.list


    def archive(self):
        self.list = cache.get(self.item_list_3, 24, self.archive_link)

        if self.list == None: return

        for i in self.list: i.update({'action': 'reverseEpisodes'})

        for i in self.list:
            bookmark = dict((k,v) for k, v in i.iteritems() if not k == 'next')
            bookmark['bookmark'] = i['url']
            i.update({'cm': [{'title': 32501, 'query': {'action': 'addBookmark', 'url': json.dumps(bookmark)}}]})

        directory.add(self.list, content='videos')
        return self.list


    def tvshows(self):
        self.list = cache.get(self.item_list_1, 24, self.tvshows_link)

        if self.list == None: return

        for i in self.list: i.update({'action': 'episodes'})

        for i in self.list:
            bookmark = dict((k,v) for k, v in i.iteritems() if not k == 'next')
            bookmark['bookmark'] = i['url']
            i.update({'cm': [{'title': 32501, 'query': {'action': 'addBookmark', 'url': json.dumps(bookmark)}}]})

        self.list = sorted(self.list, key=lambda k: k['title'].lower())

        directory.add(self.list, content='videos')
        return self.list


    def podcasts(self):
        self.list = cache.get(self.item_list_1, 24, self.podcasts_link)

        if self.list == None: return

        for i in self.list: i.update({'action': 'episodes'})

        for i in self.list:
            bookmark = dict((k,v) for k, v in i.iteritems() if not k == 'next')
            bookmark['bookmark'] = i['url']
            i.update({'cm': [{'title': 32501, 'query': {'action': 'addBookmark', 'url': json.dumps(bookmark)}}]})

        self.list = sorted(self.list, key=lambda k: k['title'].lower())

        directory.add(self.list, content='videos')
        return self.list


    def episodes(self, url, reverse=False):
        self.list = cache.get(self.item_list_2, 1, url)

        if self.list == None: return

        for i in self.list: i.update({'action': 'play', 'isFolder': 'False'})

        if reverse == True:
            self.list = self.list[::-1]

        directory.add(self.list, content='videos')
        return self.list


    def popular(self):
        self.episodes(self.popular_link)


    def news(self):
        self.episodes(self.news_link)


    def sports(self):
        self.episodes(self.sports_link)


    def play(self, url):
        directory.resolve(self.resolve(url))


    def live(self):
        directory.resolve(self.resolve_live(), meta={'title': 'SKAI'})


    def item_list_1(self, url):
        try:
            u = []
            d = datetime.datetime.utcnow()
            for i in range(0, 7):
                u.append(url % d.strftime('%d.%m.%Y'))
                d = d - datetime.timedelta(hours=24)
            u = u[::-1]

            threads = []
            for i in range(0, 7):
                threads.append(workers.Thread(self.thread, u[i], i))
                self.data.append('')
            [i.start() for i in threads]
            [i.join() for i in threads]

            items = ''.join(self.data)
            items = client.parseDOM(items, 'Show', attrs = {'TVonly': '0'})
        except:
            return

        for item in items:
            try:
                title = client.parseDOM(item, 'Show')[0]
                title = title.split('[')[-1].split(']')[0]
                title = client.replaceHTMLCodes(title)
                title = title.encode('utf-8')

                url = client.parseDOM(item, 'Link')[0]
                url = url.split('[')[-1].split(']')[0]
                url = urlparse.urljoin(self.base_link, url)
                url = client.replaceHTMLCodes(url)
                url = url.encode('utf-8')

                image = client.parseDOM(item, 'ShowImage')[0]
                image = image.split('[')[-1].split(']')[0]
                image = urlparse.urljoin(self.base_link, image)
                image = client.replaceHTMLCodes(image)
                image = image.encode('utf-8')

                if image in str(self.list): raise Exception()
                if not 'mmid=' in url: raise Exception()

                self.list.append({'title': title, 'url': url, 'image': image})
            except:
                pass

        return self.list


    def item_list_2(self, url):
        try:
            try:
                mid = urlparse.parse_qs(urlparse.urlparse(url).query)['mmid'][0]
                url = client.request(url)
                url = client.parseDOM(url, 'li', ret='id', attrs = {'class': 'active_sub'})[0]
                url = self.episodes_link % url
            except:
                pass

            threads = []
            for i in range(1, 10):
                threads.append(workers.Thread(self.thread, url + '&Page=%s' % str(i), i))
                self.data.append('')
            [i.start() for i in threads]
            [i.join() for i in threads]

            items = ''.join(self.data)
            items = client.parseDOM(items, 'Item')
        except:
        	return

        for item in items:
            try:
                date = client.parseDOM(item, 'Date')[0]
                date = date.split('[')[-1].split(']')[0]
                date = date.split('T')[0]

                title = client.parseDOM(item, 'Title')[0]
                title = title.split('[')[-1].split(']')[0]
                title = '%s (%s)' % (title, date)
                title = client.replaceHTMLCodes(title)
                title = title.encode('utf-8')

                url = client.parseDOM(item, 'File')[0]
                url = url.split('[')[-1].split(']')[0]
                url = client.replaceHTMLCodes(url)
                url = url.encode('utf-8')

                image = client.parseDOM(item, 'Photo1')[0]
                image = image.split('[')[-1].split(']')[0]
                image = urlparse.urljoin(self.base_link, image)
                image = client.replaceHTMLCodes(image)
                image = image.encode('utf-8')

                self.list.append({'title': title, 'url': url, 'image': image})
            except:
                pass

        return self.list


    def item_list_3(self, url):
        try:
            result = client.request(url)

            items = client.parseDOM(result, 'div', attrs = {'class': 'col_.+?'})
            items = client.parseDOM(items, 'li')
        except:
            return

        for item in items:
            try:
                title = client.parseDOM(item, 'a')[0]
                title = client.replaceHTMLCodes(title)
                title = title.encode('utf-8')

                url = client.parseDOM(item, 'a', ret='href')[0]
                url = re.findall('\((.+?)\)', url)[0]
                url = re.findall('(\d+)', url)[0]
                url = self.episodes_link % url
                url = url.encode('utf-8')

                self.list.append({'title': title, 'url': url, 'image': '0'})
            except:
                pass

        return self.list


    def resolve(self, url):
        try:
            try:
                if not url.startswith('rtmp'): raise Exception()

                p = re.findall('/([a-zA-Z0-9]{3,}\:)', url)
                if len(p) > 0: url = url.replace(p[0], ' playpath=%s' % p[0])
                url += ' timeout=10'

                return url
            except:
                pass

            return url
        except:
            return


    def resolve_live(self):
        try:
            url = client.request(self.live_link)

            url = client.parseDOM(url, 'File')[0]
            url = re.findall('([0-9A-Za-z_\-]+)', url)[-1]
            url = 'http://www.youtube.com/watch?v=%s' % url

            result = client.request(url)
            url = re.findall('"hlsvp"\s*:\s*"(.+?)"', result)[0]
            url = urllib.unquote(url).replace('\\/', '/')

            result = client.request(url)
            result = result.replace('\n','')
            url = re.findall('RESOLUTION\s*=\s*(\d*)x\d{1}.+?(http.+?\.m3u8)', result)

            url = [(int(i[0]), i[1]) for i in url]
            url.sort()
            url = url[-1][1]

            return url
        except:
            return


    def thread(self, url, i):
        try:
            result = client.request(url)
            self.data[i] = result
        except:
            return


