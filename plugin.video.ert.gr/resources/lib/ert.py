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
from lamlib import directory
from lamlib import client
from lamlib import cache


class indexer:
    def __init__(self):
        self.list = []
        self.base_link = 'http://webtv.ert.gr'
        self.episodes_link = 'http://webtv.ert.gr/?cat=%s'
        self.sports_link = 'http://webtv.ert.gr/?cat=87'
        self.news_link = 'http://webtv.ert.gr/?cat=38'
        self.info_link = 'http://webtv.ert.gr/?cat=39'
        self.weather_link = 'http://webtv.ert.gr/?cat=374'
        self.documentary_link = 'http://webtv.ert.gr/?cat=224'
        self.culture_link = 'http://webtv.ert.gr/?cat=63'
        self.cartoons_link = 'http://webtv.ert.gr/?cat=76'
        self.entertainment_link = 'http://webtv.ert.gr/?cat=40'
        self.popular_link = 'http://webtv.ert.gr/feed/'
        self.ert1_link = 'http://webtv.ert.gr/ert1/'
        self.ert2_link = 'http://webtv.ert.gr/ert2/'
        self.ert3_link = 'http://webtv.ert.gr/ert3/'
        self.ertw_link = 'http://webtv.ert.gr/ertworld/'


    def root(self):
        self.list = [
        {
        'title': 32001,
        'action': 'channels',
        'icon': 'channels.png'
        },

        {
        'title': 32002,
        'action': 'popular',
        'icon': 'popular.png'
        },

        {
        'title': 32003,
        'action': 'episodes',
        'url': self.sports_link,
        'icon': 'sports.png'
        },

        {
        'title': 32004,
        'action': 'episodes',
        'url': self.news_link,
        'icon': 'news.png'
        },

        {
        'title': 32005,
        'action': 'episodes',
        'url': self.info_link,
        'icon': 'info.png'
        },

        {
        'title': 32006,
        'action': 'episodes',
        'url': self.weather_link,
        'icon': 'weather.png'
        },

        {
        'title': 32007,
        'action': 'episodes',
        'url': self.documentary_link,
        'icon': 'documentary.png'
        },

        {
        'title': 32008,
        'action': 'episodes',
        'url': self.culture_link,
        'icon': 'culture.png'
        },

        {
        'title': 32009,
        'action': 'episodes',
        'url': self.cartoons_link,
        'icon': 'cartoons.png'
        },

        {
        'title': 32010,
        'action': 'episodes',
        'url': self.entertainment_link,
        'icon': 'entertainment.png'
        },

        {
        'title': 32011,
        'action': 'categories',
        'icon': 'categories.png'
        },

        {
        'title': 32012,
        'action': 'bookmarks',
        'icon': 'bookmarks.png'
        }
        ]

        directory.add(self.list, content='videos')
        return self.list


    def channels(self):
        self.list = [
        {
        'title': 32021,
        'action': 'live',
        'url': 'ert1',
        'isFolder': 'False',
        'icon': 'live1.png'
        },

        {
        'title': 32022,
        'action': 'live',
        'url': 'ert2',
        'isFolder': 'False',
        'icon': 'live2.png'
        },

        {
        'title': 32023,
        'action': 'live',
        'url': 'ert3',
        'isFolder': 'False',
        'icon': 'live3.png'
        },

        {
        'title': 32024,
        'action': 'live',
        'url': 'ertw',
        'isFolder': 'False',
        'icon': 'livew.png'
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


    def categories(self):
        self.list = cache.get(self.item_list_1, 24)

        if self.list == None: return

        for i in self.list: i.update({'action': 'episodes'})

        for i in self.list:
            bookmark = dict((k,v) for k, v in i.iteritems() if not k == 'next')
            bookmark['bookmark'] = i['url']
            i.update({'cm': [{'title': 32501, 'query': {'action': 'addBookmark', 'url': json.dumps(bookmark)}}]})

        self.list = sorted(self.list, key=lambda k: k['title'].lower())

        directory.add(self.list, content='videos')
        return self.list


    def episodes(self, url):
        self.list = cache.get(self.item_list_2, 1, url)

        if self.list == None: return

        for i in self.list: i.update({'action': 'play', 'isFolder': 'False'})

        for i in self.list: i.update({'nextlabel': 32500, 'nextaction': 'episodes'})

        directory.add(self.list, content='videos')
        return self.list


    def popular(self):
        self.list = cache.get(self.item_list_3, 1, self.popular_link)

        if self.list == None: return

        for i in self.list: i.update({'action': 'play', 'isFolder': 'False'})

        directory.add(self.list, content='videos')
        return self.list


    def play(self, url):
        directory.resolve(self.resolve(url))


    def live(self, url):
        directory.resolve(self.resolve_live(url), meta={'title': 'ERT'})


    def item_list_1(self):
        try:
            result = client.request(self.base_link)

            items = re.findall('(<option\s.+?</option>)', result)
        except:
            return

        for item in items:
            try:
                title = client.parseDOM(item, 'option', attrs = {'class': 'level-[1-9]'})[0]
                title = client.replaceHTMLCodes(title)
                title = title.strip().upper()
                title = title.encode('utf-8')

                url = client.parseDOM(item, 'option', ret='value', attrs = {'class': 'level-[1-9]'})[0]
                url = self.episodes_link % url
                url = client.replaceHTMLCodes(url)
                url = url.encode('utf-8')

                self.list.append({'title': title, 'url': url})
            except:
                pass

        return self.list


    def item_list_2(self, url):
        try:
            result = client.request(url)

            items = client.parseDOM(result, 'div', attrs = {'class': 'blog-listing-con.+?'})[0]
            items = client.parseDOM(items, 'div', attrs = {'class': 'item-thumbnail'})
        except:
        	return

        try:
            next = client.parseDOM(result, 'a', ret='href', attrs = {'rel': 'next'})[0]
            next = urlparse.urljoin(self.base_link, next)
            next = client.replaceHTMLCodes(next)
            next = next.encode('utf-8')
        except:
            next = ''

        for item in items:
            try:
                title = client.parseDOM(item, 'a', ret='title')[0]
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

                self.list.append({'title': title, 'url': url, 'image': image, 'next': next})
            except:
                pass

        return self.list


    def item_list_3(self, url):
        try:
            result = client.request(url)

            items = client.parseDOM(result, 'item')
        except:
        	return

        for item in items:
            try:
                title = client.parseDOM(item, 'title')[0]
                title = client.replaceHTMLCodes(title)
                title = title.encode('utf-8')

                url = client.parseDOM(item, 'link')[0]
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

            result = client.request(url)

            url = client.parseDOM(result, 'div', attrs = {'class': 'play.+?'})[0]
            url = client.parseDOM(url, 'iframe', ret='src')[0]

            try:
                url = re.findall('(?:youtube.com|youtu.be)/(?:embed/|.+?\?v=|.+?\&v=|v/)([0-9A-Za-z_\-]+)', url)[0]
                url = 'plugin://plugin.video.youtube/play/?video_id=%s' % url
                return url
            except:
                pass

            try:
                if not 'ert-archives.gr' in url: raise Exception()
                url = urlparse.parse_qs(urlparse.urlparse(url).query)['tid'][0]
                url = 'http://www.ert-archives.gr/V3/media.hFLV?tid=%s' % url
                return url
            except:
                pass

            try:
                url = url.replace(' ', '%20')

                url = client.request(url, referer=referer)

                url = re.findall('(?:\"|\')(http.+?)(?:\"|\')', url)
                url = [i for i in url if '.m3u8' in i]
                url = [i.replace(' ', '%20') for i in url]

                u = client.request(url[0], output='geturl')
                if u == None and len(url) > 1:
                    u = client.request(url[1], output='geturl')

                return u
            except:
                pass

        except:
            pass


    def resolve_live(self, url):
        if url == 'ert1':
            url = self.ert1_link
        elif url == 'ert2':
            url = self.ert2_link
        elif url == 'ert3':
            url = self.ert3_link
        elif url == 'ertw':
            url = self.ertw_link

        try:
            result = client.request(url)
            result = client.parseDOM(result, 'iframe', ret='src')[0]
            result = client.request(result)
        except:
            pass

        try:
            url = re.findall('(?:\"|\')(http(?:s|)://.+?\.m3u8(?:.+?|))(?:\"|\')', result)[-1]
            url = client.request(url, output='geturl')

            if not url == None: return url
        except:
            pass


        result = re.findall('(?:youtube.com|youtu.be)/(?:embed/|.+?\?v=|.+?\&v=|v/)([0-9A-Za-z_\-]+)', result)

        for r in result:
            try:
                url = 'http://www.youtube.com/watch?v=%s' % r

                url = client.request(url)
                url = re.findall('"hlsvp"\s*:\s*"(.+?)"', url)[0]
                url = urllib.unquote(url).replace('\\/', '/')

                url = client.request(url)
                url = url.replace('\n','')
                url = re.findall('RESOLUTION\s*=\s*(\d*)x\d{1}.+?(http.+?\.m3u8)', url)

                url = [(int(i[0]), i[1]) for i in url]
                url.sort()
                url = url[-1][1]

                return url
            except:
                pass


