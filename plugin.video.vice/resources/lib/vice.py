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


import urlparse,json,zlib,re,os,sys

from lamlib import bookmarks
from lamlib import cache
from lamlib import client
from lamlib import control
from lamlib import directory


class indexer:
    def __init__(self):
        self.list = [] ; self.settings()
        self.base_link = 'http://www.vice.com'
        self.main_link = '/%s/videos'
        self.latest_link = '/%s/ajax/getlatestvideos?limit=500'
        self.episode_link = '/%s/ajax/getseriesepisodes?limit=500&series_id='
        self.img_link = 'http://vice-images.vice.com/%s%s'
        self.resolve_link = 'http://player.ooyala.com/player/ipad/%s.m3u8'
        self.nuplayer_link = 'https://player.ooyala.com/nuplayer?embedCode=%s'


    def root(self):
        self.list = [
        {
        'title': 32001,
        'action': 'videos',
        'url': self.latest_link,
        'icon': 'topvideos.png'
        },

        {
        'title': 32002,
        'action': 'countries',
        'icon': 'videos.png'
        },

        {
        'title': 32003,
        'action': 'topshows',
        'icon': 'topshows.png'
        },

        {
        'title': 32004,
        'action': 'shows',
        'icon': 'shows.png'
        },

        {
        'title': 32005,
        'action': 'bookmarks',
        'icon': 'bookmarks.png'
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

        directory.add(self.list, content='files', mediatype='episode')
        return self.list


    def videos(self, url):
        self.list = cache.get(self.item_list_1, 1, url, self.country)

        if self.list == None: return

        for i in self.list: i.update({'action': 'play', 'isFolder': 'False'})

        for i in self.list:
            bookmark = dict((k,v) for k, v in i.iteritems() if not k == 'next')
            bookmark['bookmark'] = i['url']
            i.update({'cm': [{'title': 32501, 'query': {'action': 'addBookmark', 'url': json.dumps(bookmark)}}]})

        directory.add(self.list, content='files', mediatype='episode')
        return self.list


    def countries(self):
        for i in self.countryDict: 
            self.list.append({'title': i['title'], 'url': self.latest_link % i['code']})

        for i in self.list: i.update({'action': 'videos'})

        directory.add(self.list)
        return self.list


    def topshows(self):
        self.list = cache.get(self.item_list_2, 24, self.country)

        if self.list == None: return

        for i in self.list: i.update({'action': 'videos'})

        directory.add(self.list, mediatype='tvshow')
        return self.list


    def shows(self):
        self.list = cache.get(self.item_list_3, 24, self.country)

        if self.list == None: return

        for i in self.list: i.update({'action': 'videos'})

        directory.add(self.list, mediatype='tvshow')
        return self.list


    def play(self, url):
        url, subtitle = self.resolve(url)

        item = control.item(path=url)

        if not subtitle == None:
            item.setSubtitles([subtitle])

        control.resolve(int(sys.argv[1]), True, item)


    def item_list_1(self, url, country):
        try:
            if not '/ajax/' in url:
                url = urlparse.urljoin(self.base_link, url)

                url = client.request(url)
                url = re.findall('data-series-id\s*=\s*(?:"|\')(.+?)(?:"|\')', url)[0]
                url = self.episode_link + url

            url = urlparse.urljoin(self.base_link, url)

            if '%s' in url:
                url = url % country

            result = client.request(url)

            result = json.loads(result)

            items = result['items']
        except:
            return

        for item in items:
            try:
                title = item['info']['title']
                title = client.replaceHTMLCodes(title)
                title = title.encode('utf-8')

                try: tvshowtitle = item['series']['title']
                except: tvshowtitle = '0'
                tvshowtitle = client.replaceHTMLCodes(tvshowtitle)
                tvshowtitle = tvshowtitle.encode('utf-8')

                url = item['url']
                url = url.encode('utf-8')

                try: image = self.img_link % (item['info']['image_path'], item['info']['image_file_name'])
                except: image = '0'
                image = image.encode('utf-8')

                premiered = item['publish_date'].split()[0] if 'publish_date' in item else '0'
                premiered = premiered.encode('utf-8')

                d = str(item['video_duration_visual']) if 'video_duration_visual' in item else 0
                d = re.findall('(\d+)', d)

                duration = 0
                try: duration = (60 * int(d[0])) + int(d[1])
                except: pass
                try: duration = (60 * 60 * int(d[0])) + (60 * int(d[1])) + int(d[2])
                except: pass
                duration = str(duration)

                plot = item['excerpt'] if 'excerpt' in item else '0'
                plot = re.sub('<.+?>|</.+?>', '', plot)
                plot = client.replaceHTMLCodes(plot)
                plot = plot.encode('utf-8')

                self.list.append({'title': title, 'tvshowtitle': tvshowtitle, 'url': url, 'image': image, 'fanart': image, 'premiered': premiered, 'duration': duration, 'plot': plot})
            except:
                pass

        return self.list


    def item_list_2(self, country):
        try:
            url = urlparse.urljoin(self.base_link, self.main_link)
            url = url % country

            result = client.request(url)

            items = client.parseDOM(result, 'div', attrs = {'class': '[^"]*featured-shows'})

            items = client.parseDOM(items, 'article', attrs = {'class': 'item'})
        except:
            return

        for item in items:
            try:
                title = client.parseDOM(item, 'div', attrs = {'class': 'title.+?'})[0]
                title = re.sub('<.+?>|</.+?>', '', title).strip()
                title = client.replaceHTMLCodes(title)
                title = title.encode('utf-8')

                url = client.parseDOM(item, 'a', ret='href')[0]
                url = re.findall('(?://.+?|)(/.+)', url)[0]
                url = client.replaceHTMLCodes(url)
                url = url.encode('utf-8')

                image = client.parseDOM(item, 'img', ret='data.+?')[0]
                image = re.sub('-crop_.+?\.', '.', image)
                image = image.split('?')[0].replace('/crops/', '/meta/')
                image = client.replaceHTMLCodes(image)
                image = image.encode('utf-8')

                plot = client.parseDOM(item, 'p', attrs = {'class': 'item-description'})[0]
                plot = re.sub('<.+?>|</.+?>', '', plot).strip()
                plot = client.replaceHTMLCodes(plot)
                plot = plot.encode('utf-8')

                self.list.append({'title': title, 'url': url, 'image': image, 'fanart': image, 'plot': plot})
            except:
                pass

        return self.list


    def item_list_3(self, country):
        try:
            url = urlparse.urljoin(self.base_link, self.main_link)
            url = url % country

            result = client.request(url)

            items = client.parseDOM(result, 'div', attrs = {'class': '[^"]*all-shows[^"]*'})

            items = client.parseDOM(items, 'li')
        except:
            return

        for item in items:
            try:
                title = client.parseDOM(item, 'a')[0]
                title = re.sub('<.+?>|</.+?>', '', title).strip()
                title = client.replaceHTMLCodes(title)
                title = title.encode('utf-8')

                url = client.parseDOM(item, 'a', ret='href')[0]
                url = re.findall('(?://.+?|)(/.+)', url)[0]
                url = client.replaceHTMLCodes(url)
                url = url.encode('utf-8')

                self.list.append({'title': title, 'url': url})
            except:
                pass

        return self.list


    def resolve(self, url):
        try:
            url = urlparse.urljoin(self.base_link, url)

            result = client.request(url)

            yid = client.parseDOM(result, 'div', ret='data-youtube-id', attrs = {'class': 'youtube-video'})

            if yid:
                return ('plugin://plugin.video.youtube/play/?video_id=%s' % yid[0], None)

            pid = re.findall('embedCode=(.+?)(?:\&|\n)', result)[0]

            url = self.resolve_link % pid

            subtitle = self.subtitle_resolve(pid)

            return (url, subtitle)
        except:
            pass


    def subtitle_resolve(self, pid):
        try:
            import pyaes,timer

            result = client.request(self.nuplayer_link % pid)

            iv = '00020406080a0c0ea0a2a4a6a8aaacae'.decode('hex')

            key = '4b3d32bed59fb8c54ab8a190d5d147f0e4f0cbe6804c8e0721175ab68b40cb01'.decode('hex')

            unpad = lambda s : s[0:-ord(s[-1])]

            result = unpad(pyaes.new(key, pyaes.MODE_CBC, IV=iv).decrypt(result.decode('base64')))

            result = zlib.decompress(result[4:])[16:]

            lang = client.parseDOM(result, 'closedCaptions', ret='available_languages')[0].split()

            multi = True if len(lang) > 1 else False

            if not self.lang in lang: return

            lang = lang.index(self.lang) + 1

            result = client.parseDOM(result, 'closedCaptions', ret='url')[0]

            result = client.request(result)

            regex = '(<p .+?d%s_p\d+.+?</p>)' % lang if multi == True  else '(<p .+?</p>)'

            result = re.findall(regex, result)

            srt = '' ; count = 1

            for i in result:
                try:
                    s1 = client.parseDOM(i, 'p', ret='begin')[0]
                    d1 = timer.to_str(timer.to_seconds(s1))

                    s2 = client.parseDOM(i, 'p', ret='dur')
                    if s2:
                        d2 = timer.to_str(timer.to_seconds(s1) + timer.to_seconds(s2[0]))

                    s2 = client.parseDOM(i, 'p', ret='end')
                    if s2:
                        d2 = timer.to_str(timer.to_seconds(s2[0]))

                    txt = client.parseDOM(i, 'p')[0]
                    txt = txt.replace('<br/>', '\n')

                    srt += '%s\n%s --> %s\n%s\n\n' % (count, d1, d2, txt)

                    count += 1
                except:
                    pass

            srt = client.replaceHTMLCodes(srt)
            srt = srt.encode('utf-8')

            path = os.path.join(control.dataPath, 'srt')
            path = path.decode('utf-8')

            control.deleteDir(os.path.join(path, ''), force=True)

            control.makeFile(control.dataPath)

            control.makeFile(path)

            subtitle = os.path.join(path, 'file.srt')

            with open(subtitle, 'wb') as f:
                f.write(srt)

            return subtitle
        except:
            pass


    def settings(self):

        self.countryDict = [

        #Australia
        { 'setting': 0,  'title': 32201,  'iso': '',  'code': 'en_au' },

        #Austria
        { 'setting': 1,  'title': 32202,  'iso': 'de',  'code': 'alps' },

        #Belgium
        { 'setting': 2,  'title': 32203,  'iso': 'fr',  'code': 'be' },

        #Brazil
        { 'setting': 3,  'title': 32204,  'iso': 'pt',  'code': 'pt_br' },

        #Canada
        { 'setting': 4,  'title': 32205,  'iso': '',  'code': 'en_ca' },

        #Czech Republic
        { 'setting': 5,  'title': 32206,  'iso': 'cs',  'code': 'cs' },

        #Colombia
        { 'setting': 6,  'title': 32207,  'iso': 'es',  'code': 'es_co' },

        #Denmark
        { 'setting': 7,  'title': 32208,  'iso': 'da',  'code': 'en_dk' },

        #France
        { 'setting': 8,  'title': 32209,  'iso': 'fr',  'code': 'fr' },

        #Germany
        { 'setting': 9,  'title': 32210,  'iso': 'de',  'code': 'de' },

        #Greece
        { 'setting': 10,  'title': 32211,  'iso': 'el',  'code': 'gr' },

        #Italy
        { 'setting': 11,  'title': 32212,  'iso': 'it',  'code': 'it' },

        #Mexico
        { 'setting': 12,  'title': 32213,  'iso': 'es',  'code': 'es_mx' },

        #Netherlands
        { 'setting': 13,  'title': 32214,  'iso': 'nl',  'code': 'nl' },

        #Poland
        { 'setting': 14,  'title': 32215,  'iso': 'pl',  'code': 'pl' },

        #Portugal
        { 'setting': 15,  'title': 32216,  'iso': 'pt',  'code': 'pt' },

        #Romania
        { 'setting': 16,  'title': 32217,  'iso': 'ro',  'code': 'ro' },

        #Russia
        { 'setting': 17,  'title': 32218,  'iso': 'ru',  'code': 'ru' },

        #Serbia
        { 'setting': 18,  'title': 32219,  'iso': 'sr',  'code': 'rs' },

        #Spain
        { 'setting': 19,  'title': 32220,  'iso': 'es',  'code': 'es' },

        #Sweden
        { 'setting': 20,  'title': 32221,  'iso': 'sv',  'code': 'en_se' },

        #United Kingdom
        { 'setting': 21,  'title': 32222,  'iso': '',  'code': 'en_uk' },

        #United States
        { 'setting': 22,  'title': 32223,  'iso': '',  'code': 'en_us' }

        ]

        setting = control.setting('country')
        setting = [i for i in self.countryDict if setting == str(i['setting'])]

        try: self.country = setting[0]['code']
        except: self.country = 'en_us'

        try: self.lang = setting[0]['iso']
        except: self.lang = ''


