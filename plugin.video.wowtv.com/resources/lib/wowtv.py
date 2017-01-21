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



class indexer:
    def __init__(self):
        self.list = []
        self.base_link = 'http://am.wowtv.com'
        self.menu_link = 'http://am.wowtv.com/Json/VOD/Grouplist.json'
        self.email = control.setting('wowtv.email')
        self.password = control.setting('wowtv.password')


    def root(self):
        self.list = cache.get(self.item_list_1, 24, self.menu_link)

        if self.list == None: return

        for i in self.list: i.update({'action': 'categories'})

        directory.add(self.list, content='videos')
        return self.list


    def categories(self, url):
        self.list = cache.get(self.item_list_2, 24, url)

        if self.list == None: return

        for i in self.list: i.update({'action': 'videos'})

        directory.add(self.list, content='videos')
        return self.list


    def videos(self, url):
        self.list = cache.get(self.item_list_3, 1, url)

        if self.list == None: return

        for i in self.list: i.update({'action': 'play', 'isFolder': 'False'})

        directory.add(self.list, content='videos', mediatype='movie')
        return self.list


    def play(self, url):
        directory.resolve(self.resolve(url))


    def item_list_1(self, url):
        try:
            result = client.request(url, mobile=True)

            items = json.loads(result)['menu']
        except:
            return

        for item in items:
            try:
                title = item['title'].strip()
                title = title.encode('utf-8')

                url = item['url']
                if not '/VOD/' in url: raise Exception()
                url = url.encode('utf-8')

                image = item['image']
                image = image.encode('utf-8')

                self.list.append({'title': title, 'url': url, 'image': image})
            except:
                pass

        return self.list


    def item_list_2(self, url):
        try:
            result = client.request(url, mobile=True)

            items = json.loads(result)
        except:
            return

        for item in items:
            try:
                title = item['title'].strip()
                title = title.encode('utf-8')

                url = item['nextpage']
                url = url.encode('utf-8')

                image = item['poster']
                image = image.encode('utf-8')

                plot = item['description'].strip()
                plot = plot.encode('utf-8')

                self.list.append({'title': title, 'url': url, 'image': image, 'plot': plot})
            except:
                pass

        return self.list


    def item_list_3(self, url):
        try:
            result = client.request(url, mobile=True)

            items = json.loads(result)
        except:
            return

        for item in items:
            try:
                title = item['title'].strip()
                title = title.encode('utf-8')

                url = item['videopath']
                url = url.encode('utf-8')

                image = item['image']
                image = image.encode('utf-8')

                genre = item['category'] if 'category' in item else '0'
                if genre == None: genre = '0'
                genre = genre.encode('utf-8')

                duration = 0
                try: d = re.findall('(\d*):(\d*):(\d*)', item['runtime'])[0]
                except: pass
                try: duration = (60 * 60 * int(d[0])) + (60 * int(d[1])) + int(d[2])
                except: pass
                duration = str(duration)
                duration = duration.encode('utf-8')

                cast = item['starring'] if 'starring' in item else '0'
                cast = client.replaceHTMLCodes(cast)
                cast = cast.encode('utf-8')
                cast = [i.strip() for i in cast.split(',')]
                if cast == []: cast = '0'

                plot = item['description'].strip() if 'description' in item else '0'
                if plot == None: plot = '0'
                plot = plot.replace('\n', '')
                plot = client.replaceHTMLCodes(plot)
                plot = plot.encode('utf-8')

                self.list.append({'title': title, 'url': url, 'image': image, 'genre': genre, 'duration': duration, 'cast': cast, 'plot': plot})
            except:
                pass

        return self.list


    def resolve(self, url):
        try:
            if (self.email == '' or self.password == ''):
        	    control.infoDialog(control.lang(32181).encode('utf-8'))
        	    return control.openSettings()

            login_link = 'http://www.wowtv.com/webservice/service.asmx/loginuser'

            login_post = '{"username": "%s", "spname": "WOW_authdata", "parameterNamelist": "opr,regid,email,password,promocode,Mailme,ipaddress,Session", "parameterValuelist": "2,0,%s,%s,,0,,", "numberofparameters": "8", "password": "%s"}' % (self.email, self.email, self.password, self.password)

            login_headers = {
            'Content-Type': 'application/json; charset=UTF-8',
            'X-Requested-With': 'XMLHttpRequest'
            }

            result = client.request(login_link, post=login_post, headers=login_headers)
            result = json.loads(result)['d']

            if not 'yes' in result:
        	    control.infoDialog(str(result).encode('utf-8'))
        	    return control.openSettings()

            return url
        except:
            return


