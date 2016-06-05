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


import urlparse,re

from resources.lib.modules import cache
from resources.lib.modules import client
from resources.lib.modules import directory
from resources.lib.modules import workers


class indexer:
    def __init__(self):
        self.list = []
        self.base_link = 'http://extreme.com'
        self.videos_link = '/rss'
        self.users_link = '/rss/extreme'
        self.mountainbike_link = '/rss/mountainbike'
        self.bmx_link = '/rss/bmx'
        self.skate_link = '/rss/skate'
        self.snowboard_link = '/rss/snowboard'
        self.freeski_link = '/rss/freeski'
        self.fmx_link = '/rss/fmx'
        self.mx_link = '/rss/mx'
        self.surf_link = '/rss/surf'
        self.autosports_link = '/rss/autosports'
        self.kayak_link = '/rss/kayak'
        self.kite_link = '/rss/kite'
        self.outdoor_link = '/rss/outdoor'
        self.wake_link = '/rss/wake'
        self.windsurf_link = '/rss/windsurf'


    def root(self):
        try:
            self.list = [
            {
            'title': 30001,
            'action': 'videos',
            'url': self.videos_link,
            'icon': 'videos.png'
            },

            {
            'title': 30002,
            'action': 'videos',
            'url': self.mountainbike_link,
            'icon': 'mountainbike.png'
            },

            {
            'title': 30003,
            'action': 'videos',
            'url': self.bmx_link,
            'icon': 'bmx.png'
            },

            {
            'title': 30004,
            'action': 'videos',
            'url': self.skate_link,
            'icon': 'skate.png'
            },

            {
            'title': 30005,
            'action': 'videos',
            'url': self.snowboard_link,
            'icon': 'snowboard.png'
            },

            {
            'title': 30006,
            'action': 'videos',
            'url': self.freeski_link,
            'icon': 'freeski.png'
            },

            {
            'title': 30007,
            'action': 'videos',
            'url': self.fmx_link,
            'icon': 'fmx.png'
            },

            {
            'title': 30008,
            'action': 'videos',
            'url': self.mx_link,
            'icon': 'mx.png'
            },

            {
            'title': 30009,
            'action': 'videos',
            'url': self.surf_link,
            'icon': 'surf.png'
            },

            {
            'title': 30010,
            'action': 'videos',
            'url': self.autosports_link,
            'icon': 'autosports.png'
            },

            {
            'title': 30011,
            'action': 'videos',
            'url': self.kayak_link,
            'icon': 'kayak.png'
            },

            {
            'title': 30012,
            'action': 'videos',
            'url': self.kite_link,
            'icon': 'kite.png'
            },

            {
            'title': 30013,
            'action': 'videos',
            'url': self.outdoor_link,
            'icon': 'outdoor.png'
            },

            {
            'title': 30014,
            'action': 'videos',
            'url': self.wake_link,
            'icon': 'wake.png'
            },

            {
            'title': 30015,
            'action': 'videos',
            'url': self.windsurf_link,
            'icon': 'windsurf.png'
            }
            ]

            directory.add(self.list)
            return self.list
        except:
            pass


    def videos(self, url):
        try:
            self.list = cache.get(self.item_list, 6, url)

            for i in self.list: i.update({'action': 'play', 'isFolder': 'False'})

            directory.add(self.list)
            return self.list
        except:
            pass


    def play(self, url):
        try:
            url = self.resolve(url)
            directory.resolve(url)
        except:
            pass


    def item_list(self, url):
        try:
            url = urlparse.urljoin(self.base_link, url)

            result = client.request(url)

            items = client.parseDOM(result, 'item')
        except:
            return

        for item in items:
            try:
                title = client.parseDOM(item, 'title')[0]
                title = client.replaceHTMLCodes(title)
                title = title.encode('utf-8')

                image = client.parseDOM(item, 'media:thumbnail', ret='url')[0]
                image = image.split('?')[0]
                image = client.replaceHTMLCodes(image)
                image = image.encode('utf-8')

                url = client.parseDOM(item, 'enclosure', ret='url')
                check = False if len(url) > 0 else True
                url = url[0] if len(url) > 0 else '0'
                url = client.replaceHTMLCodes(url)
                url = url.encode('utf-8')

                link = client.parseDOM(item, 'link')[0]
                link = re.sub('.+?//.+?/','/', link)
                link = client.replaceHTMLCodes(link)
                link = link.encode('utf-8')

                self.list.append({'title': title, 'url': url, 'image': image, 'link': link, 'check': check})
            except:
                pass

        threads = []
        for i in range(0, len(self.list)): threads.append(workers.Thread(self.item_list_worker, i))
        [i.start() for i in threads]
        [i.join() for i in threads]

        self.list = [i for i in self.list if i['check'] == False]

        return self.list


    def item_list_worker(self, i):
        try:
            if self.list[i]['check'] == False: raise Exception()

            url = urlparse.urljoin(self.base_link, self.list[i]['link'])
            result = client.request(url)

            url = re.findall('(?:youtube.com|youtu.be)/(?:embed/|.+?\?v=|.+?\&v=|v/)([0-9A-Za-z_\-]+)', result)[0]
            url = 'plugin://plugin.video.youtube/play/?video_id=%s' % url

            self.list[i].update({'url': url, 'check': False})
        except:
            pass


    def resolve(self, url):
        try:
            if url.startswith('plugin://'): return url

            try: u = re.findall('(.+?)(\d+p)(.+)', url)[0]
            except: return url

            r = u[0] + '480p' + u[2]
            r = client.request(r, output='geturl')
            if not r == None: return r

            r = u[0] + '360p' + u[2]
            r = client.request(r, output='geturl')
            if not r == None: return r

            return url
        except:
            pass


