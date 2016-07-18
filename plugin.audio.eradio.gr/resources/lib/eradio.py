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


import urlparse,json

from lamlib import bookmarks
from lamlib import directory
from lamlib import client
from lamlib import cache


class indexer:
    def __init__(self):
        self.list = []
        self.base_link = 'http://eradio.mobi'
        self.image_link = 'http://cdn.e-radio.gr/logos/%s'
        self.all_link = 'http://eradio.mobi/cache/1/1/medialist.json'
        self.trending_link = 'http://eradio.mobi/cache/1/1/medialistTop_trending.json'
        self.popular_link = 'http://eradio.mobi/cache/1/1/medialist_top20.json'
        self.new_link = 'http://eradio.mobi/cache/1/1/medialist_new.json'
        self.categories_link = 'http://eradio.mobi/cache/1/1/categories.json'
        self.regions_link = 'http://eradio.mobi/cache/1/1/regions.json'
        self.category_link = 'http://eradio.mobi/cache/1/1/medialist_categoryID%s.json'
        self.region_link = 'http://eradio.mobi/cache/1/1/medialist_regionID%s.json'
        self.resolve_link = 'http://eradio.mobi/cache/1/1/media/%s.json'


    def root(self):
        radios = [
        {
        'title': 32001,
        'action': 'radios',
        'url': self.all_link,
        'icon': 'all.png'
        },

        {
        'title': 32002,
        'action': 'bookmarks',
        'icon': 'bookmarks.png'
        },

        {
        'title': 32003,
        'action': 'radios',
        'url': self.trending_link,
        'icon': 'trending.png'
        },

        {
        'title': 32004,
        'action': 'radios',
        'url': self.popular_link,
        'icon': 'popular.png'
        },

        {
        'title': 32005,
        'action': 'radios',
        'url': self.new_link,
        'icon': 'new.png'
        }
        ]

        categories = cache.get(self.item_list_1, 24, self.categories_link)

        if categories == None: return

        for i in categories: i.update({'icon': 'categories.png', 'action': 'radios'})

        regions = cache.get(self.item_list_1, 24, self.regions_link)

        if regions == None: return

        for i in regions: i.update({'icon': 'regions.png', 'action': 'radios'})

        self.list = radios + categories + regions

        directory.add(self.list)
        return self.list


    def bookmarks(self):
        self.list = bookmarks.get()

        if self.list == None: return

        for i in self.list:
            bookmark = dict((k,v) for k, v in i.iteritems() if not k == 'next')
            bookmark['delbookmark'] = i['url']
            i.update({'cm': [{'title': 32502, 'query': {'action': 'deleteBookmark', 'url': json.dumps(bookmark)}}]})

        self.list = sorted(self.list, key=lambda k: k['title'].lower())

        directory.add(self.list, infotype='Music')
        return self.list


    def radios(self, url):
        self.list = cache.get(self.item_list_2, 1, url)

        if self.list == None: return

        for i in self.list: i.update({'action': 'play', 'isFolder': 'False'})

        for i in self.list:
            bookmark = dict((k,v) for k, v in i.iteritems() if not k == 'next')
            bookmark['bookmark'] = i['url']
            i.update({'cm': [{'title': 32501, 'query': {'action': 'addBookmark', 'url': json.dumps(bookmark)}}]})

        directory.add(self.list, infotype='Music')
        return self.list


    def play(self, url):
        resolved = self.resolve(url)

        if resolved == None: return

        title, url, image = resolved

        directory.resolve(url, {'title': title}, image)


    def item_list_1(self, url):
        try:
            self.list = []

            result = client.request(url, mobile=True)
            result = json.loads(result)

            if 'categories' in result:
                items = result['categories']
            elif 'countries' in result:
                items = result['countries']
        except:
            return

        for item in items:
            try:
                if 'categoryName' in item:
                    title = item['categoryName']
                elif 'regionName' in item:
                    title = item['regionName']
                title = client.replaceHTMLCodes(title)
                title = title.encode('utf-8')

                if 'categoryID' in item:
                    url = self.category_link % str(item['categoryID'])
                elif 'regionID' in item:
                    url = self.region_link % str(item['regionID'])
                url = client.replaceHTMLCodes(url)
                url = url.encode('utf-8')

                self.list.append({'title': title, 'url': url})
            except:
                pass

        return self.list


    def item_list_2(self, url):
        try:
            result = client.request(url, mobile=True)
            result = json.loads(result)

            items = result['media']
        except:
        	return

        for item in items:
            try:
                title = item['name'].strip()
                title = client.replaceHTMLCodes(title)
                title = title.encode('utf-8')

                url = str(item['stationID'])
                url = client.replaceHTMLCodes(url)
                url = url.encode('utf-8')

                image = item['logo']
                image = self.image_link % image
                image = image.replace('/promo/', '/500/')
                if image.endswith('/nologo.png'): image = '0'
                image = client.replaceHTMLCodes(image)
                image = image.encode('utf-8')

                self.list.append({'title': title, 'url': url, 'image': image})
            except:
                pass

        return self.list


    def resolve(self, url):
        try:
            url = self.resolve_link % url

            result = client.request(url, mobile=True)
            result = json.loads(result)

            item = result['media'][0]

            url = item['mediaUrl'][0]['liveURL']
            if not url.startswith('http://'): url = '%s%s' % ('http://', url)
            url = client.replaceHTMLCodes(url)
            url = url.encode('utf-8')

            #url = client.request(url, output='geturl')

            title = item['name'].strip()
            title = client.replaceHTMLCodes(title)
            title = title.encode('utf-8')

            image = item['logo']
            image = self.image_link % image
            image = image.replace('/promo/', '/500/')
            if image.endswith('/nologo.png'): image = '0'
            image = client.replaceHTMLCodes(image)
            image = image.encode('utf-8')

            return (title, url, image)
        except:
            pass


