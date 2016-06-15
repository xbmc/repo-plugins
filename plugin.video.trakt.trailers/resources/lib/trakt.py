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


import urlparse,json,re,time

from lamlib import client
from lamlib import control
from lamlib import cache
from lamlib import directory



class indexer:
    def __init__(self):
        self.list = []
        self.base_link = 'http://api-v2launch.trakt.tv'
        self.key = '1216080fe3176062b664d78eb525f9a8a61a74e73b992ffb4e5a90fa1c283071'
        self.secret = 'ae115c2e4f0fc777f2114cd4e8192319ffb0207e17d221d46551cef33af2f087'
        self.trending_link = '/movies/trending?extended=full,images&limit=100&page=1'
        self.popular_link = '/movies/popular?extended=full,images&limit=100&page=1'
        self.played_link = '/movies/played/yearly?extended=full,images&limit=100&page=1'
        self.watched_link = '/movies/watched/yearly?extended=full,images&limit=100&page=1'
        self.anticipated_link = '/movies/anticipated?extended=full,images&limit=500'
        self.tvpopular_link = '/shows/popular?extended=full,images&limit=500'


    def root(self):
        self.list = [
        {
        'title': 32001,
        'action': 'movies',
        'url': self.anticipated_link,
        'icon': 'anticipated.png'
        },

        {
        'title': 32002,
        'action': 'movies',
        'url': self.trending_link,
        'icon': 'trending.png'
        },

        {
        'title': 32003,
        'action': 'movies',
        'url': self.popular_link,
        'icon': 'popular.png'
        },

        {
        'title': 32004,
        'action': 'movies',
        'url': self.played_link,
        'icon': 'played.png'
        },

        {
        'title': 32005,
        'action': 'movies',
        'url': self.watched_link,
        'icon': 'watched.png'
        },

        {
        'title': 32006,
        'action': 'tvshows',
        'url': self.tvpopular_link,
        'icon': 'tvshows.png'
        }
        ]

        directory.add(self.list)
        return self.list


    def movies(self, url):
        self.list = cache.get(self.item_list, 24, url)

        if self.list == None: return

        for i in self.list: i.update({'action': 'play', 'isFolder': 'False'})

        if self.getTraktCredentialsInfo() == True:
            for i in self.list:
                i.update({'cm': [
                {'title': 32501, 'query': {'action': 'collectMovie', 'url': i['trakt']}},
                {'title': 32502, 'query': {'action': 'watchlistMovie', 'url': i['trakt']}},
                {'title': 32503, 'query': {'action': 'newlistMovie', 'url': i['trakt']}},
                {'title': 32504, 'query': {'action': 'listMovie', 'url': i['trakt']}}
                ]})

        for i in self.list: i.update({'nextlabel': 32500, 'nextaction': 'movies'})

        directory.add(self.list, cacheToDisc=False, content='movies', mediatype='movie')
        return self.list


    def tvshows(self, url):
        self.list = cache.get(self.item_list, 24, url)

        if self.list == None: return

        for i in self.list: i.update({'action': 'play', 'isFolder': 'False'})

        if self.getTraktCredentialsInfo() == True:
            for i in self.list:
                i.update({'cm': [
                {'title': 32501, 'query': {'action': 'collectTVShow', 'url': i['trakt']}},
                {'title': 32502, 'query': {'action': 'watchlistTVShow', 'url': i['trakt']}},
                {'title': 32503, 'query': {'action': 'newlistTVShow', 'url': i['trakt']}},
                {'title': 32504, 'query': {'action': 'listTVShow', 'url': i['trakt']}}
                ]})

        for i in self.list: i.update({'nextlabel': 32500, 'nextaction': 'tvshows'})

        directory.add(self.list, cacheToDisc=False, content='tvshows', mediatype='tvshow')
        return self.list


    def play(self, url):
        directory.resolve(self.resolve(url))


    def item_list(self, url):
        try:
            result = self.getTrakt(url)
            result = json.loads(result)

            items = []
            for i in result:
                try: items.append(i['movie'])
                except: pass
                try: items.append(i['show'])
                except: pass
            if len(items) == 0:
                items = result
        except:
            return

        try:
            next, num = re.findall('(.+?\&page=)(\d+)', url)[0]
            num = int(num) + 1
            if num > 10: raise Exception()
            next = '%s%s' % (next, num)
            next = client.replaceHTMLCodes(next)
            next = next.encode('utf-8')
        except:
            next = ''

        for item in items:
            try:
                title = item['title']
                title = client.replaceHTMLCodes(title)
                title = title.encode('utf-8')

                year = item['year']
                year = re.sub('[^0-9]', '', str(year))
                year = year.encode('utf-8')

                trakt = item['ids']['trakt']
                trakt = re.sub('[^0-9]', '', str(trakt))
                trakt = trakt.encode('utf-8')

                url = item['trailer']
                if url == None: raise Exception()
                url = url.encode('utf-8')

                poster = '0'
                try: poster = item['images']['poster']['medium']
                except: pass
                if poster == None or not '/posters/' in poster: poster = '0'
                poster = poster.rsplit('?', 1)[0]
                poster = poster.encode('utf-8')

                banner = poster
                try: banner = item['images']['banner']['full']
                except: pass
                if banner == None or not '/banners/' in banner: banner = '0'
                banner = banner.rsplit('?', 1)[0]
                banner = banner.encode('utf-8')

                fanart = '0'
                try: fanart = item['images']['fanart']['full']
                except: pass
                if fanart == None or not '/fanarts/' in fanart: fanart = '0'
                fanart = fanart.rsplit('?', 1)[0]
                fanart = fanart.encode('utf-8')

                premiered = '0'
                if 'released' in item: premiered = item['released']
                elif 'first_aired' in item: premiered = item['first_aired']
                try: premiered = re.compile('(\d{4}-\d{2}-\d{2})').findall(premiered)[0]
                except: premiered = '0'
                premiered = premiered.encode('utf-8')

                try: studio = item['network']
                except: studio = '0'
                if studio == None: studio = '0'
                studio = studio.encode('utf-8')

                try: genre = item['genres']
                except: genre = '0'
                genre = [i.title() for i in genre]
                if genre == []: genre = '0'
                genre = ' / '.join(genre)
                genre = genre.encode('utf-8')

                try: duration = str(item['runtime'])
                except: duration = '0'
                if duration == None: duration = '0'
                try: duration = str(60 * int(duration))
                except: pass
                duration = duration.encode('utf-8')

                try: rating = str(item['rating'])
                except: rating = '0'
                if rating == None or rating == '0.0': rating = '0'
                rating = rating.encode('utf-8')

                try: votes = str(item['votes'])
                except: votes = '0'
                try: votes = str(format(int(votes),',d'))
                except: pass
                if votes == None: votes = '0'
                votes = votes.encode('utf-8')

                try: mpaa = item['certification']
                except: mpaa = '0'
                if mpaa == None: mpaa = '0'
                mpaa = mpaa.encode('utf-8')

                try: plot = item['overview']
                except: plot = '0'
                if plot == None: plot = '0'
                plot = client.replaceHTMLCodes(plot)
                plot = plot.encode('utf-8')

                self.list.append({'title': title, 'year': year, 'trakt': trakt, 'url': url, 'premiered': premiered, 'studio': studio, 'genre': genre, 'duration': duration, 'rating': rating, 'votes': votes, 'mpaa': mpaa, 'plot': plot, 'poster': poster, 'banner': banner, 'fanart': fanart, 'next': next})
            except:
                pass

        return self.list


    def resolve(self, url):
        try:
            url = re.findall('(?:youtube.com|youtu.be)/(?:embed/|.+?\?v=|.+?\&v=|v/)([0-9A-Za-z_\-]+)', url)[0]
            url = 'plugin://plugin.video.youtube/play/?video_id=%s' % url
            return url
        except:
            return


    def lookup(self, id_content, id_type, id_key):
        try:
            if not id_type in ['imdb', 'trakt', 'slug']:

                item = self.getTrakt('/search?id_type=%s&id=%s' % (id_type, id_key))
                item = json.loads(item)

                if id_content == 'movie':
                    id_key = item[0]['movie']['ids']['slug']

                elif id_content == 'show':
                    id_key = item[0]['show']['ids']['slug']

            if id_content == 'movie':
                item = self.getTrakt('/movies/%s?extended=full' % id_key)

            elif id_content == 'show':
                item = self.getTrakt('/shows/%s?extended=full' % id_key)


            url = json.loads(item)['trailer']
            url = self.resolve(url)

            control.player.play(url, control.item(path=url))
        except:
            return


    def getTraktCredentialsInfo(self):
        user = control.setting('trakt.user').strip()
        token = control.setting('trakt.token')
        refresh = control.setting('trakt.refresh')
        if (user == '' or token == '' or refresh == ''): return False
        return True


    def getTrakt(self, url, post=None):
        try:
            url = urlparse.urljoin(self.base_link, url)

            headers = {'Content-Type': 'application/json', 'trakt-api-key': self.key, 'trakt-api-version': '2'}

            if not post == None: post = json.dumps(post)


            if self.getTraktCredentialsInfo() == False:
                result = client.request(url, post=post, headers=headers)
                return result


            headers['Authorization'] = 'Bearer %s' % control.setting('trakt.token')

            result = client.request(url, post=post, headers=headers, output='response', error=True)
            if not (result[0] == '401' or result[0] == '405'): return result[1]


            oauth = urlparse.urljoin(self.base_link, '/oauth/token')
            opost = {'client_id': self.key, 'client_secret': self.secret, 'redirect_uri': 'urn:ietf:wg:oauth:2.0:oob', 'grant_type': 'refresh_token', 'refresh_token': control.setting('trakt.refresh')}

            result = client.request(oauth, post=json.dumps(opost), headers=headers)
            result = json.loads(result)

            token, refresh = result['access_token'], result['refresh_token']

            control.setSetting(id='trakt.token', value=token)
            control.setSetting(id='trakt.refresh', value=refresh)

            headers['Authorization'] = 'Bearer %s' % token

            result = client.request(url, post=post, headers=headers)
            return result
        except:
            pass


    def authTrakt(self):
        try:
            if self.getTraktCredentialsInfo() == True:
                if control.yesnoDialog(control.lang(32181).encode('utf-8'), control.lang(32182).encode('utf-8'), '', 'Trakt'):
                    control.setSetting(id='trakt.user', value='')
                    control.setSetting(id='trakt.token', value='')
                    control.setSetting(id='trakt.refresh', value='')
                raise Exception()

            result = self.getTrakt('/oauth/device/code', {'client_id': self.key})
            result = json.loads(result)
            verification_url = (control.lang(32183) + '[COLOR skyblue]%s[/COLOR]' % result['verification_url']).encode('utf-8')
            user_code = (control.lang(32184) + '[COLOR skyblue]%s[/COLOR]' % result['user_code']).encode('utf-8')
            expires_in = int(result['expires_in'])
            device_code = result['device_code']
            interval = result['interval']

            progressDialog = control.progressDialog
            progressDialog.create('Trakt', verification_url, user_code)

            for i in range(0, expires_in):
                try:
                    if progressDialog.iscanceled(): break
                    time.sleep(1)
                    if not float(i) % interval == 0: raise Exception()
                    r = self.getTrakt('/oauth/device/token', {'client_id': self.key, 'client_secret': self.secret, 'code': device_code})
                    r = json.loads(r)
                    if 'access_token' in r: break
                except:
                    pass

            try: progressDialog.close()
            except: pass

            token, refresh = r['access_token'], r['refresh_token']

            headers = {'Content-Type': 'application/json', 'trakt-api-key': self.key, 'trakt-api-version': '2', 'Authorization': 'Bearer %s' % token}

            result = client.request('http://api-v2launch.trakt.tv/users/me', headers=headers)
            result = json.loads(result)

            user = result['username']

            control.setSetting(id='trakt.user', value=user)
            control.setSetting(id='trakt.token', value=token)
            control.setSetting(id='trakt.refresh', value=refresh)
            raise Exception()
        except:
            control.openSettings('0.1')


    def traktLists(self, url, action):
        try:
            if action in ['newlistMovie', 'newlistTVShow']:
                t = control.lang(32185).encode('utf-8')
                k = control.keyboard('', t) ; k.doModal()
                new = k.getText() if k.isConfirmed() else None
                if (new == None or new == ''): return
                result = self.getTrakt('/users/me/lists', post={'name': new, 'privacy': 'private'})
                try: slug = json.loads(result)['ids']['slug']
                except: return control.infoDialog(control.lang(32190).encode('utf-8'), heading=head, icon=icon)
                add = total = '/users/me/lists/%s/items' % slug
                remove = '/users/me/lists/%s/items/remove' % slug
                media = 'movies' if action == 'newlistMovie' else 'shows'

            elif action in ['listMovie', 'listTVShow']:
                result = self.getTrakt('/users/me/lists')
                result = json.loads(result)
                result = [(i['name'], i['ids']['slug']) for i in result]
                t = control.lang(32186).encode('utf-8')
                s = control.selectDialog([i[0] for i in result], t)
                if s == -1: return
                slug = result[s][1]
                add = total = '/users/me/lists/%s/items' % slug
                remove = '/users/me/lists/%s/items/remove' % slug
                media = 'movies' if action == 'listMovie' else 'shows'

            elif action == 'collectMovie':
                add = '/sync/collection'
                remove = '/sync/collection/remove'
                total = '/users/me/collection/movies'
                media = 'movies'

            elif action == 'collectTVShow':
                add = '/sync/collection'
                remove = '/sync/collection/remove'
                total = '/users/me/collection/shows'
                media = 'shows'

            elif action == 'watchlistMovie':
                add = '/sync/watchlist'
                remove = '/sync/watchlist/remove'
                total = '/users/me/watchlist/movies'
                media = 'movies'

            elif action == 'watchlistTVShow':
                add = '/sync/watchlist'
                remove = '/sync/watchlist/remove'
                total = '/users/me/watchlist/shows'
                media = 'shows'


            icon = control.infoLabel('ListItem.Icon')
            head = control.infoLabel('ListItem.Label')

            check = self.getTrakt(total)
            check = json.loads(check)

            try: ids = [str(i['movie']['ids']['trakt']) for i in check if 'movie' in i]
            except: pass
            try: ids += [str(i['show']['ids']['trakt']) for i in check if 'show' in i]
            except: pass
            try: ids += [str(i['ids']['trakt']) for i in check if 'ids' in i]
            except: pass

            if url in ids:
                yes = control.yesnoDialog(control.lang(32187).encode('utf-8'), control.lang(32188).encode('utf-8'), '', 'Trakt')
                if not yes: return
                call = remove
            else:
                call = add

            result = self.getTrakt(call, post={media: [{'ids': {'trakt': url}}]})

            info = control.lang(32189) if not result == None else control.lang(32190)
            control.infoDialog(info.encode('utf-8'), heading=head, icon=icon)
        except:
        	pass


