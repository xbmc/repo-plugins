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


import json

from lamlib import bookmarks
from lamlib import directory
from lamlib import client
from lamlib import cache


class indexer:
    def __init__(self):
        self.list = []
        self.base_link = 'http://www.nrj.fr'
        self.image_link = 'http://players.nrjaudio.fm/live-metadata/player/img/player-files/nrj/logos/640x640/%s'
        self.player_link = 'http://players.nrjaudio.fm/wr_api/live?id_radio=1&act=get_setup&fmt=json&cp=UTF8'


    def root(self):
        self.list = [
        {
        'title': 32001,
        'action': 'radios'
        },

        {
        'title': 32002,
        'action': 'bookmarks'
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
            i.update({'cm': [{'title': 32502, 'query': {'action': 'deleteBookmark', 'url': json.dumps(bookmark)}}]})

        self.list = sorted(self.list, key=lambda k: k['title'].lower())

        directory.add(self.list, infotype='Music')
        return self.list


    def radios(self):
        self.list = cache.get(self.item_list, 0, self.player_link)

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


    def item_list(self, url):
        try:
            result = client.request(url, mobile=True)
            result = json.loads(result)

            items = result['webradios']
        except:
        	return

        for item in items:
            try:
                title = item['name'].strip()
                title = title.encode('utf-8')

                url = item['web_url'].strip()
                url = [i for i in url.split('/') if not i == ''][-1]
                url = url.encode('utf-8')

                uid = []
                uid.append(item['url_hd_aac'])
                uid.append(item['url_triton_64k_aac'])
                uid.append(item['url_64k_aac'])
                uid.append(item['url_triton_128k_mp3'])
                uid.append(item['url_128k_mp3'])
                uid.append(item['url_hls'])
                uid = [i for i in uid if '//' in i][0]
                uid = uid.encode('utf-8')

                image = item['logo'].strip()
                image = self.image_link % image
                image = image.encode('utf-8')

                self.list.append({'title': title, 'url': url, 'uid': uid, 'image': image})
            except:
                pass

        return self.list


    def resolve(self, url):
        try:
            item = cache.get(self.item_list, 24, self.player_link)
            item = [i for i in item if url == i['url']][0]

            title, url, image = item['title'], item['uid'], item['image']

            return (title, url, image)
        except:
        	pass


