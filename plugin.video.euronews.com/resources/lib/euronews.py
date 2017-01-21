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


import urllib,json,re

from lamlib import cache
from lamlib import client
from lamlib import control
from lamlib import directory
from lamlib import workers



class indexer:
    def __init__(self):
        self.list = []
        self.base_link = 'http://www.euronews.com'
        self.api_link = 'http://api.euronews.com/ipad/'
        self.top_link = '"methodName":"content.getHome","params":{}'
        self.programs_link = '"methodName":"content.getPrograms","params":{}'
        self.program_link = '"methodName":"content.getProgramDetails","params":{"pId":"%s"}'
        self.theme_link = '"methodName":"content.getThemeDetails","params":{"tId":"%s"}'
        self.resolve_link = '"methodName":"content.getArticle","params":{"id":"%s"}'
        self.post_link = '{%s,"apiKey":"windows8Euronews-1.0","language":"%s"}'
        self.live_link = 'http://www.euronews.com/api/watchlive.json'
        self.img_link = 'http://static.euronews.com/articles/programs/650x365_%s'
        self.img2_link = 'http://static.euronews.com/articles/%s/650x365_%s.jpg'
        self.lang = self.languages()


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
        'action': 'videos',
        'url': self.top_link,
        'icon': 'top.png'
        },

        {
        'title': 32003,
        'action': 'videos',
        'url': self.theme_link % '1',
        'icon': 'news.png'
        },

        {
        'title': 32004,
        'action': 'videos',
        'url': self.theme_link % '8',
        'icon': 'sports.png'
        },

        {
        'title': 32005,
        'action': 'videos',
        'url': self.theme_link % '7',
        'icon': 'business.png'
        },

        {
        'title': 32006,
        'action': 'videos',
        'url': self.theme_link % '5',
        'icon': 'europe.png'
        },

        {
        'title': 32007,
        'action': 'videos',
        'url': self.theme_link % '2',
        'icon': 'culture.png'
        },

        {
        'title': 32008,
        'action': 'videos',
        'url': self.theme_link % '3',
        'icon': 'scitech.png'
        },

        {
        'title': 32009,
        'action': 'videos',
        'url': self.theme_link % '4',
        'icon': 'environment.png'
        },

        {
        'title': 32010,
        'action': 'programs',
        'icon': 'programs.png'
        }
        ]

        directory.add(self.list, content='videos')
        return self.list


    def programs(self):
        self.list = cache.get(self.item_list_1, 24, self.programs_link, self.lang)

        if self.list == None: return

        for i in self.list: i.update({'action': 'videos'})

        directory.add(self.list, content='videos')
        return self.list


    def videos(self, url):
        self.list = cache.get(self.item_list_2, 1, url, self.lang)

        if self.list == None: return

        for i in self.list: i.update({'action': 'play', 'isFolder': 'False'})

        directory.add(self.list, content='videos')
        return self.list


    def play(self, url):
        directory.resolve(self.resolve(url, self.lang))


    def live(self):
        directory.resolve(self.resolve_live(self.lang), meta={'title': 'Euronews'})


    def languages(self):
        setting = control.setting('language')

        if setting == '0':
            langDict = {'French': 'fr', 'German': 'de', 'Greek': 'gr', 'Hungarian': 'hu', 'Italian': 'it', 'Portuguese': 'pt', 'Russian': 'ru', 'Spanish': 'es', 'Turkish': 'tr', 'Ukrainian': 'ua'}

            try: import xbmc ; lang = langDict[xbmc.getLanguage(xbmc.ENGLISH_NAME).split(' ')[0]]
            except: lang = 'en'

        else:
            langDict = {'2': 'fr', '3': 'de', '4': 'gr', '5': 'hu', '6': 'it', '7': 'pt', '8': 'ru', '9': 'es', '10': 'tr', '11': 'ua'}

            try: lang = langDict[setting]
            except: lang = 'en'

        return lang


    def item_list_1(self, url, lang):
        try:
            request = urllib.urlencode({'request': self.post_link % (url, lang)})

            result = client.request(self.api_link, post=request)

            result = json.loads(result)

            items = result['programs']
        except:
            return

        for item in items:
            try:
                title = item['title']
                title = client.replaceHTMLCodes(title)
                title = title.encode('utf-8')

                url = str(item['pId'])
                url = self.program_link % url
                url = url.encode('utf-8')

                image = item['img']
                image = self.img_link % image
                image = image.encode('utf-8')

                self.list.append({'title': title, 'url': url, 'image': image})
            except:
                pass

        return self.list


    def item_list_2(self, url, lang):
        try:
            request = urllib.urlencode({'request': self.post_link % (url, lang)})

            result = client.request(self.api_link, post=request)

            result = json.loads(result)

            items = []

            if 'themedetailslist' in result:
                items = result['themedetailslist']

            elif 'programDetailsList' in result:
                items = result['programDetailsList']

            elif 'homelist' in result:
                items = result['homelist']
        except:
            return

        for item in items:
            try:
                title = item['title']
                title = client.replaceHTMLCodes(title)
                title = title.encode('utf-8')

                url = str(item['id'])
                url = url.encode('utf-8')

                image = self.img2_link % (url, url)
                image = image.encode('utf-8')

                self.list.append({'title': title, 'url': url, 'image': image})
            except:
                pass

        threads = []
        for i in range(0, len(self.list)): threads.append(workers.Thread(self.item_list_2_worker, i, lang))
        [i.start() for i in threads]
        [i.join() for i in threads]

        self.list = [i for i in self.list if 'check' in i and not (i['check'] == '' or i['check'] == None)]

        return self.list


    def item_list_2_worker(self, i, lang):
        try:
            url = self.list[i]['url']
            check = self.resolve(url, lang)
            self.list[i].update({'check': check})
        except:
            pass


    def resolve(self, url, lang):
        try:
            url = self.resolve_link % url

            request = urllib.urlencode({'request': self.post_link % (url, lang)})

            result = client.request(self.api_link, post=request)

            url = json.loads(result)['articlelist']['videoUri']

            return url
        except:
            pass


    def resolve_live(self, lang):
        try:
            result = client.request(self.live_link)
            result = json.loads(result)['url']

            result = client.request(result)
            result = json.loads(result)['primary']

            if lang in result:
                url = result['%s' % lang]['hls']
            elif 'en' in result:
                url = result['en']['hls']
            else:
                url = result.items()[0][1]['hls']

            return url
        except:
            pass


