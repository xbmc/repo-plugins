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
from lamlib import cache
from lamlib import directory
from lamlib import youtube


class indexer:
    def __init__(self):
        self.list = []
        self.base_link = 'https://www.motorstv.com'
        self.youtube_key = 'AIzaSyBOS4uSyd27OU0XV2KSdN3vT2UG_v0g9sI'
        self.youtube_link = 'UCgfKj2_ht3opycBXYuJZomw'


    def root(self):
        self.list = [
        {
        'title': 32001,
        'action': 'videos',
        'url': self.youtube_link,
        'icon': 'videos.png'
        },

        {
        'title': 32002,
        'action': 'categories',
        'icon': 'categories.png'
        },

        {
        'title': 32003,
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

        directory.add(self.list, content='videos')
        return self.list


    def categories(self):
        self.list = cache.get(youtube.youtube(key=self.youtube_key).playlists, 24, self.youtube_link)

        if self.list == None: return

        for i in self.list: i.update({'action': 'playlist'})

        directory.add(self.list, content='videos')
        return self.list


    def videos(self, url):
        self.list = cache.get(youtube.youtube(key=self.youtube_key).videos, 1, url, True)

        if self.list == None: return

        for i in self.list: i.update({'action': 'play', 'isFolder': 'False'})

        for i in self.list:
            bookmark = dict((k,v) for k, v in i.iteritems() if not k == 'next')
            bookmark['bookmark'] = i['url']
            i.update({'cm': [{'title': 32501, 'query': {'action': 'addBookmark', 'url': json.dumps(bookmark)}}]})

        for i in self.list: i.update({'nextlabel': 32500, 'nextaction': 'videos'})

        directory.add(self.list, content='videos')
        return self.list


    def playlist(self, url):
        self.list = cache.get(youtube.youtube(key=self.youtube_key).playlist, 1, url, True)

        if self.list == None: return

        for i in self.list: i.update({'action': 'play', 'isFolder': 'False'})

        for i in self.list:
            bookmark = dict((k,v) for k, v in i.iteritems() if not k == 'next')
            bookmark['bookmark'] = i['url']
            i.update({'cm': [{'title': 32501, 'query': {'action': 'addBookmark', 'url': json.dumps(bookmark)}}]})

        for i in self.list: i.update({'nextlabel': 32500, 'nextaction': 'playlist'})

        directory.add(self.list, content='videos')
        return self.list


    def play(self, url):
        directory.resolve(url)


