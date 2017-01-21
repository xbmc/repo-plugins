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

from lamlib import directory
from lamlib import client
from lamlib import cache


class indexer:
    def __init__(self):
        self.list = []
        self.base_link = 'http://www.novasports.gr'
        self.menus_link = '/nsmobile/v3/CompetitionsMenu/List'
        self.showmenus_link = '/nsmobile/v3/Shows?mode=2&pagesize=100&page=1'
        self.competitions_link = '/nsmobile/v3/CompetitionsMenu/CompetitionsOnDemand/?cat=%s'
        self.videos_link = '/nsmobile/v3/VideosOnDemand/?pagesize=100&page=1&content_request=all&categoryID=%s&teamId='
        self.shows_link = '/nsmobile/v3/Shows?pagesize=100&page=1&mode=1&show=%s'
        self.popvideos_link = '/nsmobile/v3/VideosOnDemand/?pagesize=100&page=1&content_request=all&categoryID=-1&teamId='
        self.popshows_link = '/nsmobile/v3/Shows?pagesize=100&page=1&mode=1&show='


    def root(self):
        self.list = [
        {
        'title': 32001,
        'action': 'videos',
        'url': self.popvideos_link
        },

        {
        'title': 32002,
        'action': 'videos',
        'url': self.popshows_link
        },

        {
        'title': 32003,
        'action': 'categories'
        },

        {
        'title': 32004,
        'action': 'competitionsMenu'
        },

        {
        'title': 32005,
        'action': 'shows'
        }
        ]

        directory.add(self.list, content='videos')
        return self.list


    def categories(self):
        self.list = cache.get(self.item_list_1, 24, self.menus_link)

        if self.list == None: return

        for i in self.list: i.update({'url': self.videos_link % i['cat']})

        for i in self.list: i.update({'action': 'videos'})

        directory.add(self.list, content='videos')
        return self.list


    def competitionsMenu(self):
        self.list = cache.get(self.item_list_1, 24, self.menus_link)

        if self.list == None: return

        self.list = [i for i in self.list if i['row'] in ['1', '2', '3', '8']]

        for i in self.list: i.update({'url': self.competitions_link % i['row']})

        for i in self.list: i.update({'action': 'competitions'})

        directory.add(self.list, content='videos')
        return self.list


    def competitions(self, url):
        self.list = cache.get(self.item_list_1, 24, url)

        if self.list == None: return

        for i in self.list: i.update({'url': self.videos_link % i['cat']})

        for i in self.list: i.update({'action': 'videos'})

        directory.add(self.list, content='videos')
        return self.list


    def shows(self):
        self.list = cache.get(self.item_list_1, 24, self.showmenus_link)

        if self.list == None: return

        for i in self.list: i.update({'url': self.shows_link % i['show']})

        for i in self.list: i.update({'action': 'videos'})

        directory.add(self.list, content='videos')
        return self.list


    def videos(self, url):
        self.list = cache.get(self.item_list_2, 1, url)

        if self.list == None: return

        for i in self.list: i.update({'action': 'play', 'isFolder': 'False'})

        directory.add(self.list, content='videos')
        return self.list


    def play(self, url):
        directory.resolve(url)


    def item_list_1(self, url):
        try:
            url = urlparse.urljoin(self.base_link, url)

            result = client.request(url, mobile=True)

            result = json.loads(result)

            if 'onDemandCategories' in result:
                items = result['onDemandCategories']

            elif 'competitionsMenu' in result:
                items = result['competitionsMenu']

            elif 'showsSpinner' in result:
                items = result['showsSpinner']
        except:
            return

        for item in items:
            try:
                if 'artCatName' in item: title = item['artCatName']
                elif 'showTitle' in item: title = item['showTitle']
                elif 'title' in item: title = item['title']
                title = title.strip()
                title = title.encode('utf-8')

                cat = str(item['artCatID']) if 'artCatID' in item else '0'
                cat = cat.encode('utf-8')

                show = str(item['showID']) if 'showID' in item else '0'
                show = show.encode('utf-8')

                row = str(item['rowID']) if 'rowID' in item else '0'
                row = row.encode('utf-8')

                self.list.append({'title': title, 'cat': cat, 'row': row, 'show': show})
            except:
                pass

        return self.list


    def item_list_2(self, url):
        try:
            url = urlparse.urljoin(self.base_link, url)

            result = client.request(url, mobile=True)

            result = json.loads(result)

            if 'showsMedia' in result:
                items = result['showsMedia']

            elif 'onDemandLatest' in result:
                items = result['onDemandLatest']
        except:
            return

        for item in items:
            try:
                if 'mediaTitle' in item: title = item['mediaTitle']
                elif 'title' in item: title = item['title']
                title = title.strip()
                title = title.encode('utf-8')

                url = item['file']
                url = url.encode('utf-8')

                image = item['thumb']
                image = image.replace(' ', '%20')
                image = image.encode('utf-8')

                self.list.append({'title': title, 'url': url, 'image': image})
            except:
                pass

        return self.list


