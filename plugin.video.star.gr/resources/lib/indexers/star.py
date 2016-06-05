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

from resources.lib.modules import directory
from resources.lib.modules import client
from resources.lib.modules import cache
from resources.lib.modules import workers
from resources.lib.modules import youtube


class indexer:
    def __init__(self):
        self.list = [] ; self.data = []
        self.base_link = 'http://www.star.gr'
        self.news_link = 'http://www.star.gr/_layouts/handlers/tv/feeds.program.ashx?catTitle=News&artId=9'
        self.news_image = 'http://www.star.gr/tv/PublishingImages/2015/04/080415181740_0653.jpg'
        self.tvshows_link = 'http://www.star.gr/_layouts/handlers/tv/feeds.program.ashx?catTitle=hosts'
        self.episodes_link = 'http://www.star.gr/_layouts/handlers/tv/feeds.program.ashx?catTitle=%s&artId=%s'
        self.cartoon_link = 'http://www.star.gr/tv/el/Pages/StarlandIndex.aspx'
        self.play_link = 'http://cdnapi.kaltura.com/p/21154092/sp/2115409200/playManifest/entryId/%s/flavorId/%s/format/url/protocol/http/a.mp4'
        self.youtube_key = 'AIzaSyBOS4uSyd27OU0XV2KSdN3vT2UG_v0g9sI'
        self.youtube_link = 'UCwUNbp_4Y2Ry-asyerw2jew'


    def root(self):
        try:
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
            'action': 'cartoon',
            'icon': 'cartoon.png'
            },

            {
            'title': 30004,
            'action': 'popular',
            'icon': 'popular.png'
            },

            {
            'title': 30005,
            'action': 'news',
            'icon': 'news.png'
            },

            {
            'title': 30006,
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

            self.list = sorted(self.list, key=lambda k: k['title'].lower())

            directory.add(self.list)
            return self.list
        except:
            pass


    def tvshows(self):
        try:
            self.list = cache.get(self.item_list_1, 24, self.tvshows_link)

            for i in self.list: i.update({'action': 'episodes'})

            for i in self.list:
                bookmark = dict((k,v) for k, v in i.iteritems() if not k == 'next')
                bookmark['bookmark'] = i['url']
                i.update({'cm': [{'title': 30501, 'query': {'action': 'addBookmark', 'url': json.dumps(bookmark)}}]})

            self.list = sorted(self.list, key=lambda k: k['title'].lower())

            directory.add(self.list)
            return self.list
        except:
            pass


    def cartoon(self):
        try:
            self.list = cache.get(self.item_list_3, 24, self.cartoon_link)

            for i in self.list: i.update({'action': 'episodes'})

            for i in self.list:
                bookmark = dict((k,v) for k, v in i.iteritems() if not k == 'next')
                bookmark['bookmark'] = i['url']
                i.update({'cm': [{'title': 30501, 'query': {'action': 'addBookmark', 'url': json.dumps(bookmark)}}]})

            self.list = sorted(self.list, key=lambda k: k['title'].lower())

            directory.add(self.list)
            return self.list
        except:
            pass


    def episodes(self, url, image):
        try:
            self.list = cache.get(self.item_list_2, 1, url, image)

            for i in self.list: i.update({'action': 'play', 'isFolder': 'False'})

            directory.add(self.list, content='files')
            return self.list
        except:
            pass


    def archive(self):
        try:
            self.list = cache.get(youtube.youtube(key=self.youtube_key).playlists, 24, self.youtube_link)

            for i in self.list: i.update({'action': 'youtube'})

            for i in self.list:
                bookmark = dict((k,v) for k, v in i.iteritems() if not k == 'next')
                bookmark['bookmark'] = i['url']
                i.update({'cm': [{'title': 30501, 'query': {'action': 'addBookmark', 'url': json.dumps(bookmark)}}]})

            self.list = sorted(self.list, key=lambda k: k['title'].lower())

            directory.add(self.list)
            return self.list
        except:
            pass


    def youtube(self, url):
        try:
            self.list = cache.get(youtube.youtube(key=self.youtube_key).playlist, 1, url)

            self.list = [i for i in self.list if int(i['duration']) > 120]

            for i in self.list: i.update({'action': 'play', 'isFolder': 'False'})

            directory.add(self.list, content='files')
            return self.list
        except:
            pass


    def popular(self):
        try:
            self.list = cache.get(youtube.youtube(key=self.youtube_key).videos, 1, self.youtube_link)

            self.list = [i for i in self.list if int(i['duration']) > 120]

            for i in self.list: i.update({'action': 'play', 'isFolder': 'False'})

            directory.add(self.list, content='files')
            return self.list
        except:
            pass


    def news(self):
        self.episodes(self.news_link, self.news_image)


    def play(self, url):
        directory.resolve(url)


    def item_list_1(self, url):
        try:
            result = client.request(url, mobile=True)
            result = json.loads(result)
            items = result['hosts']
        except:
            return

        for item in items:
            try:
                title = item['Title'].strip()
                title = client.replaceHTMLCodes(title)
                title = title.encode('utf-8')

                id = item['ProgramId']
                cat = item['ProgramCat'].strip()
                url = self.episodes_link % (cat, id)
                url = client.replaceHTMLCodes(url)
                url = url.encode('utf-8')

                image = item['Image'].strip()
                image = urlparse.urljoin(self.base_link, image)
                image = client.replaceHTMLCodes(image)
                image = image.encode('utf-8')

                self.list.append({'title': title, 'url': url, 'image': image})
            except:
                pass

        return self.list


    def item_list_2(self, url, image):
        try:
            result = client.request(url, mobile=True)
            result = json.loads(result)
            items = result['videosprogram']
        except:
        	return

        for item in items:
            try:
                title = item['Title'].strip()
                title = client.replaceHTMLCodes(title)
                title = title.encode('utf-8')

                url = item['VideoID'].strip()
                url = self.play_link % (url, url)
                url = client.replaceHTMLCodes(url)
                url = url.encode('utf-8')

                self.list.append({'title': title, 'url': url, 'image': image})
            except:
                pass

        return self.list


    def item_list_3(self, url):
        try:
            result = client.request(url)

            result = client.parseDOM(result, 'a', ret='href')
            result = [i for i in result if 'starland' in i.lower()]
            result = [re.findall('artId=(\d*)', i) for i in result]
            result = [i[0] for i in result if len(i) > 0]
            result = [x for y,x in enumerate(result) if x not in result[:y]]
            result = [self.episodes_link % ('Starland', i) for i in result]

            threads = []
            for i in range(0, len(result)):
                threads.append(workers.Thread(self.thread, result[i], i))
                self.data.append('')
            [i.start() for i in threads]
            [i.join() for i in threads]

            items = self.data
        except:
            return

        for item in items:
            try:
                item = json.loads(item)

                videos = item['videosprogram'][0]['VideoID']

                title = item['programme']['Title'].strip()
                title = client.replaceHTMLCodes(title)
                title = title.encode('utf-8')

                id = item['programme']['ProgramId']
                cat = item['programme']['ProgramCat'].strip()
                url = self.episodes_link % (cat, id)
                url = client.replaceHTMLCodes(url)
                url = url.encode('utf-8')

                image = item['programme']['Image'].strip()
                image = urlparse.urljoin(self.base_link, image)
                image = client.replaceHTMLCodes(image)
                image = image.encode('utf-8')

                self.list.append({'title': title, 'url': url, 'image': image})
            except:
                pass

        return self.list


    def thread(self, url, i):
        try:
            result = client.request(url)
            self.data[i] = result
        except:
            return


