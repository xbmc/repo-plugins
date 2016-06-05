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

from resources.lib.modules import directory
from resources.lib.modules import client
from resources.lib.modules import cache


class indexer:
    def __init__(self):
        self.list = []
        self.base_link = 'http://webtv.ert.gr'
        self.base_image = 'http://www.ert.gr/wp-content/uploads/2015/12/ERT-logo-864x400_c.jpg'
        self.episodes_link = 'http://webtv.ert.gr/?cat=%s'
        self.news_link = 'http://webtv.ert.gr/?cat=38'
        self.sports_link = 'http://webtv.ert.gr/?cat=87'
        self.weather_link = 'http://webtv.ert.gr/?cat=374'
        self.popular_link = 'http://webtv.ert.gr/feed/'
        self.ert1_link = 'http://webtv.ert.gr/webtv/ert/tv/ytb/ert1_ipinfo-geo.html'
        self.ert2_link = 'http://webtv.ert.gr/webtv/ert/tv/ytb/ert2_ipinfo-geo.html'
        self.ert3_link = 'http://webtv.ert.gr/webtv/ert/tv/ytb/ert3_ipinfo-geo.html'
        self.ertw_link = 'http://webtv.ert.gr/webtv/ert/tv/ytb/ertworld.html'


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
            'action': 'categories',
            'icon': 'categories.png'
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
            'url': self.ert1_link,
            'isFolder': 'False',
            'icon': 'live1.png'
            },

            {
            'title': 30009,
            'action': 'live',
            'url': self.ert2_link,
            'isFolder': 'False',
            'icon': 'live2.png'
            },

            {
            'title': 30010,
            'action': 'live',
            'url': self.ert3_link,
            'isFolder': 'False',
            'icon': 'live3.png'
            },

            {
            'title': 30011,
            'action': 'live',
            'url': self.ertw_link,
            'isFolder': 'False',
            'icon': 'livew.png'
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
            self.list = cache.get(self.item_list_1, 24)

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


    def categories(self):
        try:
            self.list = [
            {
            'title': 'ахкгтийа'.decode('iso-8859-7').encode('utf-8'),
            'url': '87'
            },

            {
            'title': 'алеа'.decode('iso-8859-7').encode('utf-8'),
            'url': '2076'
            },

            {
            'title': 'дектиа еидгсеым'.decode('iso-8859-7').encode('utf-8'),
            'url': '38'
            },

            {
            'title': 'ейпаидеусг'.decode('iso-8859-7').encode('utf-8'),
            'url': '1055'
            },

            {
            'title': 'еккгмийес сеияес'.decode('iso-8859-7').encode('utf-8'),
            'url': '4188'
            },

            {
            'title': 'емглеяысг'.decode('iso-8859-7').encode('utf-8'),
            'url': '39'
            },

            {
            'title': 'йаияос'.decode('iso-8859-7').encode('utf-8'),
            'url': '374'
            },

            {
            'title': 'мтойиламтея'.decode('iso-8859-7').encode('utf-8'),
            'url': '4686'
            },

            {
            'title': 'немес сеияес'.decode('iso-8859-7').encode('utf-8'),
            'url': '1575'
            },

            {
            'title': 'паидийа'.decode('iso-8859-7').encode('utf-8'),
            'url': '4794'
            },

            {
            'title': 'покитислос'.decode('iso-8859-7').encode('utf-8'),
            'url': '63'
            },

            {
            'title': 'ьувацыциа'.decode('iso-8859-7').encode('utf-8'),
            'url': '40'
            }
            ]

            for i in self.list: i.update({'image': self.base_image})

            for i in self.list: i.update({'url': self.episodes_link % i['url']})

            for i in self.list: i.update({'action': 'episodes'})

            for i in self.list:
                bookmark = dict((k,v) for k, v in i.iteritems() if not k == 'next')
                bookmark['bookmark'] = i['url']
                i.update({'cm': [{'title': 30501, 'query': {'action': 'addBookmark', 'url': json.dumps(bookmark)}}]})

            directory.add(self.list)
            return self.list
        except:
            pass


    def episodes(self, url):
        try:
            self.list = cache.get(self.item_list_2, 1, url)

            for i in self.list: i.update({'action': 'play', 'isFolder': 'False'})

            for i in self.list: i.update({'nextlabel': 30500, 'nextaction': 'episodes'})

            directory.add(self.list, content='files')
            return self.list
        except:
            pass


    def popular(self):
        try:
            self.list = cache.get(self.item_list_3, 1, self.popular_link)

            for i in self.list: i.update({'action': 'play', 'isFolder': 'False'})

            directory.add(self.list, content='files')
            return self.list
        except:
            pass


    def news(self):
        self.episodes(self.news_link)


    def sports(self):
        self.episodes(self.sports_link)


    def weather(self):
        self.episodes(self.weather_link)


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

                image = self.base_image

                self.list.append({'title': title, 'url': url, 'image': image})
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
                url = url.replace('geo=true', 'geo=false')

                url = client.request(url, referer=referer)

                url = re.findall('(?:\"|\')(http.+?)(?:\"|\')', url)
                url = [i for i in url if '.m3u8' in i][-1]
                url = url.replace(' ', '%20')

                r = client.request(url, output='geturl')
                if r == None: url = re.sub('nerithd\d*', 'nerithd1', url)

                return url
            except:
                pass

        except:
            pass


    def resolve_live(self, url):
        try:
            result = client.request(url)

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

        except:
            return


