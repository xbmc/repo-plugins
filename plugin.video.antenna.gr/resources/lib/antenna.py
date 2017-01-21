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


import json,re

from lamlib import bookmarks
from lamlib import directory
from lamlib import client
from lamlib import cache
from lamlib import workers


class indexer:
    def __init__(self):
        self.list = [] ; self.data = []
        self.tvshows_link = 'http://mservices.antenna.gr/services/mobile/getshowbymenucategory.ashx?menu='
        self.episodes_link = 'http://mservices.antenna.gr/services/mobile/getepisodesforshow.ashx?show='
        self.archive_link = 'http://mservices.antenna.gr/services/mobile/getshowsbygenre.ashx?islive=0&genre=a0f33045-dfda-459a-8e4f-a65b015a0bc2'
        self.popular_link = 'http://mservices.antenna.gr/services/mobile/getlatestepisodes.ashx?'
        self.recommended_link = 'http://mservices.antenna.gr/services/mobile/getrecommended.ashx?'
        self.news_link = 'http://mservices.antenna.gr/services/mobile/getepisodesforshow.ashx?show=eaa3d856-9d11-4c3f-a048-a617011cee3d'
        self.weather_link = 'http://mservices.antenna.gr/services/mobile/getepisodesforshow.ashx?show=ffff8dbf-8600-4f4a-9eb8-a617012eebab'
        self.getlive_link = 'http://mservices.antenna.gr/services/mobile/getLiveStream.ashx?'
        self.live_link = 'http://antglantennatv-lh.akamaihd.net/i/live_1@421307/master.m3u8'


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
        'action': 'archive',
        'icon': 'archive.png'
        },

        {
        'title': 32004,
        'action': 'popular',
        'icon': 'popular.png'
        },

        {
        'title': 32005,
        'action': 'recommended',
        'icon': 'recommended.png'
        },

        {
        'title': 32006,
        'action': 'news',
        'icon': 'news.png'
        },

        {
        'title': 32007,
        'action': 'weather',
        'icon': 'weather.png'
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
        self.list = [i for i in self.list if 'url' in i and self.episodes_link in i['url']]

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


    def archive(self):
        self.list = cache.get(self.item_list_1, 24, self.archive_link)

        if self.list == None: return

        for i in self.list: i.update({'action': 'reverseEpisodes'})

        for i in self.list:
            bookmark = dict((k,v) for k, v in i.iteritems() if not k == 'next')
            bookmark['bookmark'] = i['url']
            i.update({'cm': [{'title': 32501, 'query': {'action': 'addBookmark', 'url': json.dumps(bookmark)}}]})

        self.list = sorted(self.list, key=lambda k: k['title'].lower())

        directory.add(self.list, content='videos')
        return self.list


    def episodes(self, url, reverse=False):
        self.list = cache.get(self.item_list_1, 1, url)

        if self.list == None: return

        for i in self.list: i.update({'action': 'play', 'isFolder': 'False'})

        if reverse == True:
            self.list = self.list[::-1]

        directory.add(self.list, content='videos')
        return self.list


    def popular(self):
        self.episodes(self.popular_link)


    def recommended(self):
        self.episodes(self.recommended_link)


    def news(self):
        self.episodes(self.news_link)


    def weather(self):
        self.episodes(self.weather_link)


    def play(self, url):
        directory.resolve(url)


    def live(self):
        directory.resolve(self.resolve_live(), meta={'title': 'ANT1'})


    def item_list_1(self, url):
        try:
            page = url + '&page=1'

            result = client.request(page, mobile=True)
            result = re.findall('\((.+?)\);$', result)[0]
            result = json.loads(result)

            items = result['data']

            if 'total_pages' in result:
                pages = int(result['total_pages'])
                pages = range(2, pages+1)[:16]

                threads = []
                for i in pages:
                    threads.append(workers.Thread(self.thread, url + '&page=%s' % str(i), i-2))
                    self.data.append('')
                [i.start() for i in threads]
                [i.join() for i in threads]

                for i in self.data:
                    result = re.findall('\((.+?)\);$', i)
                    try: items += json.loads(result[0])['data']
                    except: pass
        except:
            return

        for item in items:
            try:
                if 'OwnerTitle' in item:
                    title = item['OwnerTitle'].strip()
                elif 'Title' in item:
                    title = item['Title'].strip()
                title = client.replaceHTMLCodes(title)
                title = title.encode('utf-8')

                if 'MediaFileRef' in item:
                    url = item['MediaFileRef'].strip()
                elif 'ShowId' in item:
                    url = item['ShowId'].strip()
                    url = self.episodes_link + url
                url = client.replaceHTMLCodes(url)
                url = url.encode('utf-8')

                if 'CoverImage' in item:
                    image = item['CoverImage'].strip()
                elif 'Image' in item:
                    image = item['Image'].strip()
                if 'MediaFileRef' in item:
                    image = re.sub('w=\d*','w=600', image)
                    image = re.sub('h=\d*','h=400', image)
                else:
                    image = re.sub('w=\d*','w=500', image)
                    image = re.sub('h=\d*','h=500', image)
                image = client.replaceHTMLCodes(image)
                image = image.encode('utf-8')

                self.list.append({'title': title, 'url': url, 'image': image})
            except:
                pass

        return self.list


    def resolve_live(self):
        url = client.request(self.getlive_link)
        if url == None: url = ''
        url = re.findall('(?:\"|\')(http(?:s|)://.+?)(?:\"|\')', url)
        url = [i for i in url if '.m3u8' in i]
        try: return url[-1]
        except: return self.live_link


    def thread(self, url, i):
        try:
            result = client.request(url, mobile=True)
            self.data[i] = result
        except:
            return


