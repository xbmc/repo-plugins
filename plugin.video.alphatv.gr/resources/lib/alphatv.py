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

from lamlib import bookmarks
from lamlib import directory
from lamlib import client
from lamlib import cache
from lamlib import workers


class indexer:
    def __init__(self):
        self.list = [] ; self.data = []
        self.base_link = 'http://www.alphatv.gr'
        self.tvshows_link = 'http://www.alphatv.gr/shows'
        self.cytvshows_link = 'http://www.alphacyprus.com.cy/shows'
        self.tvshows_link_2 = '/views/ajax'
        self.tvshows_link_3 = 'view_name=alpha_shows_category_view&view_display_id=page_3&view_path=shows&view_base_path=shows&page=%s'
        self.popular_link = 'http://www.alphatv.gr/webtv/all/shows/populars'
        self.popular_link_2 = 'http://www.alphatv.gr/webtv/all/episodes/populars'
        self.news_link = 'http://www.alphatv.gr/shows/informative/news'
        self.cynews_link = 'http://www.alphacyprus.com.cy/shows/informative/news'
        self.live_link = 'http://www.alphatv.gr/webtv/live'
        self.live_link_2 = 'http://www.alphacyprus.com.cy/webtv/live'


    def root(self):
        self.list = [
        {
        'title': 32001,
        'action': 'channels',
        'icon': 'channels.png'
        },

        {
        'title': 32002,
        'action': 'tvshows',
        'url': self.tvshows_link,
        'icon': 'tvshows.png'
        },

        {
        'title': 32003,
        'action': 'tvshows',
        'url': self.cytvshows_link,
        'icon': 'tvshows.png'
        },

        {
        'title': 32004,
        'action': 'archive',
        'url': self.tvshows_link,
        'icon': 'archive.png'
        },

        {
        'title': 32005,
        'action': 'popularShows',
        'icon': 'popular.png'
        },

        {
        'title': 32006,
        'action': 'popularEpisodes',
        'icon': 'popular.png'
        },

        {
        'title': 32007,
        'action': 'news',
        'icon': 'news.png'
        },

        {
        'title': 32008,
        'action': 'cynews',
        'icon': 'news.png'
        },

        {
        'title': 32009,
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
        'isFolder': 'False'
        },

        {
        'title': 32022,
        'action': 'live',
        'url': 'cy',
        'isFolder': 'False'
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


    def archive(self, url):
        self.list = cache.get(self.item_list_3, 24, url)

        if self.list == None: return

        self.list = [i for i in self.list if '/agapimena/' in i['url']]

        for i in self.list: i.update({'action': 'reverseEpisodes'})

        for i in self.list:
            bookmark = dict((k,v) for k, v in i.iteritems() if not k == 'next')
            bookmark['bookmark'] = i['url']
            i.update({'cm': [{'title': 32501, 'query': {'action': 'addBookmark', 'url': json.dumps(bookmark)}}]})

        directory.add(self.list, content='videos')
        return self.list


    def tvshows(self, url):
        self.list = cache.get(self.item_list_3, 24, url)

        if self.list == None: return

        self.list = [i for i in self.list if i['filter'] == True]

        for i in self.list: i.update({'action': 'episodes'})

        for i in self.list:
            bookmark = dict((k,v) for k, v in i.iteritems() if not k == 'next')
            bookmark['bookmark'] = i['url']
            i.update({'cm': [{'title': 32501, 'query': {'action': 'addBookmark', 'url': json.dumps(bookmark)}}]})

        self.list = sorted(self.list, key=lambda k: k['title'].lower())

        directory.add(self.list, content='videos')
        return self.list


    def episodes(self, url, fulltitle=False, reverse=False):
        self.list = cache.get(self.item_list_2, 1, url)

        if self.list == None: return

        for i in self.list: i.update({'action': 'play', 'isFolder': 'False'})

        if fulltitle == True: 
            for i in self.list: i.update({'title': '%s - %s' % (i['tvshowtitle'], i['title'])})

        if reverse == True:
            self.list = self.list[::-1]

        directory.add(self.list, content='videos')
        return self.list


    def popularShows(self):
        self.episodes(self.popular_link, fulltitle=True)


    def popularEpisodes(self):
        self.episodes(self.popular_link_2, fulltitle=True)


    def cynews(self):
        self.episodes(self.cynews_link)


    def news(self):
        self.episodes(self.news_link)


    def play(self, url):
        directory.resolve(self.resolve(url))


    def live(self, url):
        directory.resolve(self.resolve_live(url), meta={'title': 'ALPHA'})


    def item_list_3(self, url):
        try:
            base_link = re.findall('(http(?:s|)://.+?)/', url)

            if base_link:
                base_link = base_link[0]
            else:
                base_link = self.base_link

            tvshows_link_2 = urlparse.urljoin(base_link, self.tvshows_link_2)

            result = client.request(url)

            filter = client.parseDOM(result, 'div', attrs = {'class': 'panel-row row-.+?'})[0]
            filter = client.parseDOM(filter, 'div', attrs = {'class': 'views.+?limit-'})
            filter = client.parseDOM(filter, 'a', ret='href')
            filter = [x for y,x in enumerate(filter) if x not in filter[:y]]

            threads = []
            for i in range(0, 7):
                threads.append(workers.Thread(self.thread, i, tvshows_link_2, self.tvshows_link_3 % str(i)))
                self.data.append('')
            [i.start() for i in threads]
            [i.join() for i in threads]

            items = ''
            for i in self.data: items += json.loads(i)[1]['data']
            items = client.parseDOM(items, 'li')
        except:
            return

        for item in items:
            try:
                title = client.parseDOM(item, 'div', attrs = {'class': 'views-field-title'})[0]
                title = client.parseDOM(title, 'a')[0]
                title = client.replaceHTMLCodes(title)
                title = title.encode('utf-8')

                url = client.parseDOM(item, 'a', ret='href')[0]
                flt = True if any(url == i for i in filter) else False
                url = urlparse.urljoin(base_link, url)
                url = client.replaceHTMLCodes(url)
                url = url.encode('utf-8')

                image = client.parseDOM(item, "img", ret="src")[0]
                image = urlparse.urljoin(base_link, image)
                image = client.replaceHTMLCodes(image)
                image = image.encode('utf-8')

                self.list.append({'title': title, 'url': url, 'image': image, 'filter': flt})
            except:
                pass

        return self.list


    def item_list_2(self, url):
        try:
            base_link = re.findall('(http(?:s|)://.+?)/', url)

            if base_link:
                base_link = base_link[0]
            else:
                base_link = self.base_link

            if not '/webtv/' in url:
                result = client.request(url + '/webtv/')
                result = re.findall('"actual_args"\s*:\s*\["(.+?)"', result)[0]
            else:
                url, result = url.split('/webtv/')

            url = '%s/webtv/%s?page=%s' % (url, result.lower(), '%s')

            self.data.append('')
            self.thread(0, url % '0', None)

            try:
                result = client.parseDOM(self.data[0], 'div', attrs = {'role': 'main'})[0]
                result = client.parseDOM(result, 'div', attrs = {'class': 'view.+?'})[0]

                num = client.parseDOM(result, 'li', attrs = {'class': 'pager__item pager__item--last'})[0]
                num = re.findall('page=(\d+)', num)[0]
                if num > 9: num = 9
                num = int(num)+1

                threads = []
                for i in range(1, num):
                    self.data.append('')
                    threads.append(workers.Thread(self.thread, i, url % str(i), None))
                [i.start() for i in threads]
                [i.join() for i in threads]
            except:
                pass

            items = ''
            for i in self.data: items += i

            items = client.parseDOM(items, 'div', attrs = {'role': 'main'})
            items = [client.parseDOM(i, 'div', attrs = {'class': 'view.+?'}) for i in items]
            items = [i[0] for i in items if len(i) > 0]
            items = client.parseDOM(items, 'article')
        except:
        	return

        for item in items:
            try:
                t = client.parseDOM(item, 'div', attrs = {'class': 'itemtitle'})[0]
                title = client.parseDOM(t, 'span')
                if title: title = title[0]
                else: title = t
                if title == '' or 'sneak preview' in title.lower(): raise Exception()

                tvshowtitle = client.parseDOM(item, 'figcaption', attrs = {'class': 'showtitle'})
                tvshowtitle += client.parseDOM(item, 'div', attrs = {'class': 'showtitle'})
                if tvshowtitle: tvshowtitle = tvshowtitle[0]
                else: tvshowtitle = title

                title = client.replaceHTMLCodes(title)
                title = title.encode('utf-8')

                tvshowtitle = client.replaceHTMLCodes(tvshowtitle)
                tvshowtitle = tvshowtitle.encode('utf-8')

                url = client.parseDOM(item, 'a', ret='href')[0]
                url = urlparse.urljoin(base_link, url)
                url = client.replaceHTMLCodes(url)
                url = url.encode('utf-8')

                image = client.parseDOM(item, 'img', ret='src')[0]
                image = urlparse.urljoin(base_link, image)
                image = client.replaceHTMLCodes(image)
                image = image.encode('utf-8')

                self.list.append({'title': title, 'url': url, 'image': image, 'tvshowtitle': tvshowtitle})
            except:
                pass

        return self.list


    def resolve(self, url):
        result = client.request(url)

        if result == None: return

        result = result.replace('\n','')

        try:
            url = re.findall('sources\s*:\s*\[(.+?)\]', result)[0]
            url = re.findall('"(.+?)"', url)
            url = [i for i in url if i.startswith('rtmp')][0]
            p = re.findall('/([a-zA-Z0-9]{3,}\:)', url)
            if len(p) > 0: url = url.replace(p[0], ' playpath=%s' % p[0])
            url += ' timeout=15'
            return url
        except:
            pass

        try:
            url = re.findall('sources\s*:\s*\[(.+?)\]', result)[0]
            url = re.findall('"(.+?)"', url)
            url = [i for i in url if '.m3u8' in i][0]
            return url
        except:
            pass

        try:
            url = re.findall('(?:youtube.com|youtu.be)/(?:embed/|.+?\?v=|.+?\&v=|v/)([0-9A-Za-z_\-]+)', result)[0]
            url = 'plugin://plugin.video.youtube/play/?video_id=%s' % url
            return url
        except:
            pass


    def resolve_live(self, url):
        links = [self.live_link, self.live_link_2]

        if not url == None: links = links[::-1]

        for link in links:
            try:
                url = client.request(link)
                url = re.findall('(?:\"|\')(http(?:s|)://.+?\.m3u8(?:.+?|))(?:\"|\')', url)[-1]
                url = client.request(url, output='geturl')
                return url
            except:
                pass


    def thread(self, i, url, post):
        try:
            result = client.request(url, post=post)
            self.data[i] = result
        except:
            return


