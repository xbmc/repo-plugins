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

from lamlib import cache
from lamlib import client
from lamlib import control
from lamlib import directory
from lamlib import workers


class indexer:
    def __init__(self):
        self.list = []
        self.base_link = 'https://api.blitzr.com'
        self.key = 'adf5ec7ed948674f4a2453705323727a'
        self.email = control.setting('blitzr.email')
        self.password = control.setting('blitzr.password')
        self.key_link = '&key=%s' % self.key
        self.popular_link = '/top/50/?&start=0'
        self.trending_link = '/top/listens/?limit=50&start=0'
        self.radio_link = '/radio/tag/?limit=50&slug=%s'
        self.recommended_link = '/user/profile/recommendations/?limit=50'
        self.collection_link_1 = '/user/library/?category=artist&orderby=name'
        self.collection_link_2 = '/user/library/?category=release&orderby=name'
        self.history_link = '/user/history/?limit=1000&start=0'
        self.albums_link = '/artist/releases/?format=all&type=official&limit=1000&start=0&uuid=%s'
        self.simsongs_link = '/radio/artist/similar/?limit=50&uuid=%s'
        self.litesongs_link = '/radio/artist/?limit=50&uuid=%s'
        self.songs_link = '/release/?uuid=%s'
        self.search_artist_link = '/search/artist/?limit=50&query=%s'
        self.search_album_link = '/search/release/?limit=50&query=%s'
        self.search_song_link = '/search/track/?limit=50&query=%s'
        self.userlists_link = '/user/playlists/?start=0'
        self.userlist_link = '/user/playlist/?id=%s'
        self.play_link = '/track/sources/?uuid=%s'


    def root(self):
        self.list = [
        {
        'title': 30001,
        'action': 'search',
        'icon': 'search.png'
        },

        {
        'title': 30002,
        'action': 'litesongs',
        'url': self.trending_link,
        'icon': 'songTrending.png'
        },

        {
        'title': 30003,
        'action': 'radio',
        'icon': 'radio.png'
        },

        {
        'title': 30004,
        'action': 'liteartists',
        'url': self.popular_link,
        'icon': 'artistPopular.png'
        },

        {
        'title': 30005,
        'action': 'liteartists',
        'url': self.recommended_link,
        'icon': 'artistRecommendation.png'
        },

        {
        'title': 30006,
        'action': 'artists',
        'url': self.collection_link_1,
        'icon': 'artistCollection.png'
        },

        {
        'title': 30007,
        'action': 'albums',
        'url': self.collection_link_2,
        'icon': 'albumCollection.png'
        },

        {
        'title': 30008,
        'action': 'liteartists',
        'url': self.collection_link_1,
        'icon': 'songCollection.png'
        },

        {
        'title': 30009,
        'action': 'simartists',
        'url': self.collection_link_1,
        'icon': 'simsongCollection.png'
        },

        {
        'title': 30010,
        'action': 'userlists',
        'icon': 'userlists.png'
        },

        {
        'title': 30011,
        'action': 'litesongs',
        'url': self.history_link,
        'icon': 'songHistory.png'
        }
        ]

        directory.add(self.list)
        return self.list


    def search(self):
        self.list = [
        {
        'title': 30021,
        'action': 'artistSearch',
        'icon': 'artistSearch.png'
        },

        {
        'title': 30022,
        'action': 'albumSearch',
        'icon': 'albumSearch.png'
        },

        {
        'title': 30023,
        'action': 'songSearch',
        'icon': 'songSearch.png'
        }
        ]

        directory.add(self.list)
        return self.list


    def radio(self):
        self.list = [
        { 'title': 'Pop: Vocal', 'url': 'pop-vocal' },
        { 'title': 'Pop: Pop Rock', 'url': 'pop-pop-rock' },
        { 'title': 'Pop: Ballad', 'url': 'pop-ballad' },
        { 'title': 'Pop: Chanson', 'url': 'pop-chanson' },
        { 'title': 'Pop: Synth-pop', 'url': 'pop-synth-pop' },
        { 'title': 'Pop: Schlager', 'url': 'pop-schlager' },
        { 'title': 'Pop: Europop', 'url': 'pop-europop' },
        { 'title': 'Pop: Easy Listening', 'url': 'pop-easy-listening' },
        { 'title': 'Pop: Indie Rock', 'url': 'pop-indie-rock' },
        { 'title': 'Pop: Indie Pop', 'url': 'pop-indie-pop' },
        { 'title': 'Pop: J-pop', 'url': 'pop-j-pop' },
        { 'title': 'Pop: Classic Rock', 'url': 'pop-classic-rock' },
        { 'title': 'Pop: Acoustic', 'url': 'pop-acoustic' },
        { 'title': 'Pop: Novelty', 'url': 'pop-novelty' },
        { 'title': 'Rock: Pop Rock', 'url': 'rock-pop-rock' },
        { 'title': 'Rock: Punk', 'url': 'rock-punk' },
        { 'title': 'Rock: Alternative Rock', 'url': 'rock-alternative-rock' },
        { 'title': 'Rock: Indie Rock', 'url': 'rock-indie-rock' },
        { 'title': 'Rock: Hard Rock', 'url': 'rock-hard-rock' },
        { 'title': 'Rock: Hardcore', 'url': 'rock-hardcore' },
        { 'title': 'Rock: Heavy Metal', 'url': 'rock-heavy-metal' },
        { 'title': 'Rock: Rock & Roll', 'url': 'rock-rock-and-roll' },
        { 'title': 'Rock: Psychedelic Rock', 'url': 'rock-psychedelic-rock' },
        { 'title': 'Rock: Classic Rock', 'url': 'rock-classic-rock' },
        { 'title': 'Rock: Folk Rock', 'url': 'rock-folk-rock' },
        { 'title': 'Rock: Prog Rock', 'url': 'rock-prog-rock' },
        { 'title': 'Rock: Experimental', 'url': 'rock-experimental' },
        { 'title': 'Rock: New Wave', 'url': 'rock-new-wave' },
        { 'title': 'Rock: Black Metal', 'url': 'rock-black-metal' },
        { 'title': 'Rock: Blues Rock', 'url': 'rock-blues-rock' },
        { 'title': 'Rock: Synth-pop', 'url': 'rock-synth-pop' },
        { 'title': 'Rock: Death Metal', 'url': 'rock-death-metal' },
        { 'title': 'Rock: Garage Rock', 'url': 'rock-garage-rock' },
        { 'title': 'Rock: Soft Rock', 'url': 'rock-soft-rock' },
        { 'title': 'Rock: Thrash', 'url': 'rock-thrash' },
        { 'title': 'Rock: Acoustic', 'url': 'rock-acoustic' },
        { 'title': 'Rock: Country Rock', 'url': 'rock-country-rock' },
        { 'title': 'Rock: Noise', 'url': 'rock-noise' },
        { 'title': 'Rock: Art Rock', 'url': 'rock-art-rock' },
        { 'title': 'Rock: Avantgarde', 'url': 'rock-avantgarde' },
        { 'title': 'Rock: Doom Metal', 'url': 'rock-doom-metal' },
        { 'title': 'Rock: Grindcore', 'url': 'rock-grindcore' },
        { 'title': 'Electronic: House', 'url': 'electronic-house' },
        { 'title': 'Electronic: Synth-pop', 'url': 'electronic-synth-pop' },
        { 'title': 'Electronic: Techno', 'url': 'electronic-techno' },
        { 'title': 'Electronic: Experimental', 'url': 'electronic-experimental' },
        { 'title': 'Electronic: Electro', 'url': 'electronic-electro' },
        { 'title': 'Electronic: Ambient', 'url': 'electronic-ambient' },
        { 'title': 'Electronic: Trance', 'url': 'electronic-trance' },
        { 'title': 'Electronic: Disco', 'url': 'electronic-disco' },
        { 'title': 'Electronic: Downtempo', 'url': 'electronic-downtempo' },
        { 'title': 'Electronic: Tech House', 'url': 'electronic-tech-house' },
        { 'title': 'Electronic: Euro House', 'url': 'electronic-euro-house' },
        { 'title': 'Electronic: Deep House', 'url': 'electronic-deep-house' },
        { 'title': 'Electronic: Noise', 'url': 'electronic-noise' },
        { 'title': 'Electronic: Progressive House', 'url': 'electronic-progressive-house' },
        { 'title': 'Electronic: Drum n Bass', 'url': 'electronic-drum-n-bass' },
        { 'title': 'Electronic: Industrial', 'url': 'electronic-industrial' },
        { 'title': 'Electronic: Abstract', 'url': 'electronic-abstract' },
        { 'title': 'Electronic: Minimal', 'url': 'electronic-minimal' },
        { 'title': 'Electronic: Hardcore', 'url': 'electronic-hardcore' },
        { 'title': 'Electronic: Breakbeat', 'url': 'electronic-breakbeat' },
        { 'title': 'Electronic: Progressive Trance', 'url': 'electronic-progressive-trance' },
        { 'title': 'Electronic: Breaks', 'url': 'electronic-breaks' },
        { 'title': 'Electronic: Hard Trance', 'url': 'electronic-hard-trance' },
        { 'title': 'Electronic: New Wave', 'url': 'electronic-new-wave' },
        { 'title': 'Electronic: IDM', 'url': 'electronic-idm' },
        { 'title': 'Electronic: Drone', 'url': 'electronic-drone' },
        { 'title': 'Electronic: Hard House', 'url': 'electronic-hard-house' },
        { 'title': 'Electronic: Leftfield', 'url': 'electronic-leftfield' },
        { 'title': 'Electronic: Alternative Rock', 'url': 'electronic-alternative-rock' },
        { 'title': 'Folk: Folk', 'url': 'folk-world-country-folk' },
        { 'title': 'Country: Country', 'url': 'folk-world-country-country' },
        { 'title': 'Funk-Soul: Soul', 'url': 'funk-soul-soul' },
        { 'title': 'Funk-Soul: Disco', 'url': 'funk-soul-disco' },
        { 'title': 'Funk-Soul: Funk', 'url': 'funk-soul-funk' },
        { 'title': 'Funk-Soul: Rhythm & Blues', 'url': 'funk-soul-rhythm-and-blues' },
        { 'title': 'Funk-Soul: Gospel', 'url': 'funk-soul-gospel' },
        { 'title': 'Funk-Soul: RnB/Swing', 'url': 'funk-soul-rnb-swing' },
        { 'title': 'Funk-Soul: Synth-pop', 'url': 'funk-soul-synth-pop' },
        { 'title': 'Jazz: Easy Listening', 'url': 'jazz-easy-listening' },
        { 'title': 'Jazz: Contemporary Jazz', 'url': 'jazz-contemporary-jazz' },
        { 'title': 'Jazz: Big Band', 'url': 'jazz-big-band' },
        { 'title': 'Jazz: Swing', 'url': 'jazz-swing' },
        { 'title': 'Jazz: Jazz-Funk', 'url': 'jazz-jazz-funk' },
        { 'title': 'Jazz: Fusion', 'url': 'jazz-fusion' },
        { 'title': 'Jazz: Soul-Jazz', 'url': 'jazz-soul-jazz' },
        { 'title': 'Jazz: Vocal', 'url': 'jazz-vocal' },
        { 'title': 'Jazz: Free Improvisation', 'url': 'jazz-free-improvisation' },
        { 'title': 'Jazz: Free Jazz', 'url': 'jazz-free-jazz' },
        { 'title': 'Jazz: Jazz-Rock', 'url': 'jazz-jazz-rock' },
        { 'title': 'Jazz: Bop', 'url': 'jazz-bop' },
        { 'title': 'Jazz: Hard Bop', 'url': 'jazz-hard-bop' },
        { 'title': 'Jazz: Latin Jazz', 'url': 'jazz-latin-jazz' },
        { 'title': 'Jazz: Smooth Jazz', 'url': 'jazz-smooth-jazz' },
        { 'title': 'Jazz: Cool Jazz', 'url': 'jazz-cool-jazz' },
        { 'title': 'Jazz: Experimental', 'url': 'jazz-experimental' },
        { 'title': 'Jazz: Post Bop', 'url': 'jazz-post-bop' },
        { 'title': 'Hip Hop: RnB/Swing', 'url': 'hip-hop-rnb-swing' },
        { 'title': 'Hip Hop: Pop Rap', 'url': 'hip-hop-pop-rap' },
        { 'title': 'Hip Hop: Gangsta', 'url': 'hip-hop-gangsta' },
        { 'title': 'Hip Hop: Hip Hop', 'url': 'hip-hop-hip-hop' },
        { 'title': 'Hip Hop: Conscious', 'url': 'hip-hop-conscious' },
        { 'title': 'Classical: Contemporary', 'url': 'classical-contemporary' },
        { 'title': 'Classical: Classical', 'url': 'classical-classical' }
        ]

        for i in self.list: i.update({'url': self.radio_link % i['url']})

        for i in self.list: i.update({'action': 'litesongs'})

        for i in self.list: i.update({'icon': 'radio.png'})

        directory.add(self.list)
        return self.list


    def artistSearch(self, query=None):
        if query == None:
            t = control.lang(30021).encode('utf-8')
            k = control.keyboard('', t) ; k.doModal()
            query = k.getText() if k.isConfirmed() else None

        if (query == None or query == ''): return

        url = self.search_artist_link % urllib.quote_plus(query)
        url = urlparse.urljoin(self.base_link, url)
        url += self.key_link

        self.artists(url)


    def albumSearch(self, query=None):
        if query == None:
            t = control.lang(30022).encode('utf-8')
            k = control.keyboard('', t) ; k.doModal()
            query = k.getText() if k.isConfirmed() else None

        if (query == None or query == ''): return

        url = self.search_album_link % urllib.quote_plus(query)
        url = urlparse.urljoin(self.base_link, url)
        url += self.key_link

        self.albums(url)


    def songSearch(self, query=None):
        if query == None:
            t = control.lang(30023).encode('utf-8')
            k = control.keyboard('', t) ; k.doModal()
            query = k.getText() if k.isConfirmed() else None

        if (query == None or query == ''): return

        url = self.search_song_link % urllib.quote_plus(query)
        url = urlparse.urljoin(self.base_link, url)
        url += self.key_link

        self.litesongs(url)


    def artists(self, url):
        self.list = cache.get(self.item_list_1, 0, url)

        if self.list == None: return

        for i in self.list: i.update({'action': 'albums'})


        if url == self.collection_link_1:
            for i in self.list:
                i.update({'cm': [
                {'title': 30502, 'query': {'action': 'uncollectArtist', 'url': i['uuid']}}
                ]})
        else:
            for i in self.list:
                i.update({'cm': [
                {'title': 30501, 'query': {'action': 'collectArtist', 'url': i['uuid']}}
                ]})


        directory.add(self.list, infotype='Music')
        return self.list


    def liteartists(self, url):
        self.list = cache.get(self.item_list_1, 0, url)

        if self.list == None: return

        for i in self.list: i.update({'url': self.litesongs_link % i['uuid']})

        for i in self.list: i.update({'action': 'litesongs'})


        if url == self.popular_link:
            for i in self.list:
                i.update({'cm': [
                {'title': 30501, 'query': {'action': 'collectArtist', 'url': i['uuid']}}
                ]})

        elif url == self.recommended_link:
            for i in self.list:
                i.update({'cm': [
                {'title': 30501, 'query': {'action': 'collectArtist', 'url': i['uuid']}},
                {'title': 30503, 'query': {'action': 'unrecommendArtist', 'url': i['uuid']}}
                ]})

        elif url == self.collection_link_1:
            for i in self.list:
                i.update({'cm': [
                {'title': 30502, 'query': {'action': 'uncollectArtist', 'url': i['uuid']}}
                ]})


        directory.add(self.list, infotype='Music')
        return self.list


    def simartists(self, url):
        self.list = cache.get(self.item_list_1, 0, url)

        if self.list == None: return

        for i in self.list: i.update({'url': self.simsongs_link % i['uuid']})

        for i in self.list: i.update({'action': 'litesongs'})

        for i in self.list:
            i.update({'cm': [
            {'title': 30502, 'query': {'action': 'uncollectArtist', 'url': i['uuid']}}
            ]})

        directory.add(self.list, infotype='Music')
        return self.list


    def albums(self, url):
        self.list = cache.get(self.item_list_2, 0, url)

        if self.list == None: return

        for i in self.list: i.update({'action': 'songs'})


        if url == self.collection_link_2:
            for i in self.list:
                i.update({'cm': [
                {'title': 30502, 'query': {'action': 'uncollectAlbum', 'url': i['uuid']}}
                ]})
        else:
            for i in self.list:
                i.update({'cm': [
                {'title': 30501, 'query': {'action': 'collectAlbum', 'url': i['uuid']}}
                ]})


        directory.add(self.list, infotype='Music')
        return self.list


    def songs(self, url):
        self.list = cache.get(self.item_list_3, 1, url)

        if self.list == None: return

        for i in self.list: i.update({'action': 'play', 'isFolder': 'False'})

        for i in self.list:
            i.update({'cm': [
            {'title': 30504, 'query': {'action': 'joinPlaylist', 'url': i['uuid']}},
            {'title': 30505, 'query': {'action': 'newPlaylist', 'url': i['uuid']}}
            ]})

        directory.add(self.list, content='files', infotype='Music')
        return self.list


    def litesongs(self, url):
        self.list = cache.get(self.item_list_4, 0, url)

        if self.list == None: return

        for i in self.list: i.update({'action': 'play', 'isFolder': 'False'})

        for i in self.list:
            i.update({'cm': [
            {'title': 30504, 'query': {'action': 'joinPlaylist', 'url': i['uuid']}},
            {'title': 30505, 'query': {'action': 'newPlaylist', 'url': i['uuid']}}
            ]})

        directory.add(self.list, content='files', infotype='Music')
        return self.list


    def usersongs(self, url):
        self.list = cache.get(self.item_list_4, 0, url)

        if self.list == None: return

        for i in self.list: i.update({'action': 'play', 'isFolder': 'False'})

        for i in self.list:
            i.update({'cm': [
            {'title': 30504, 'query': {'action': 'joinPlaylist', 'url': i['uuid']}},
            {'title': 30505, 'query': {'action': 'newPlaylist', 'url': i['uuid']}},
            {'title': 30506, 'query': {'action': 'leavePlaylist', 'url': i['uuid']}}
            ]})

        directory.add(self.list, content='files', infotype='Music')
        return self.list


    def userlists(self):
        self.list = cache.get(self.item_list_5, 0, self.userlists_link)

        if self.list == None: return

        for i in self.list: i.update({'icon': 'userlists.png'})

        for i in self.list: i.update({'action': 'usersongs'})

        for i in self.list:
            i.update({'cm': [
            {'title': 30507, 'query': {'action': 'renamePlaylist', 'url': i['uuid']}},
            {'title': 30508, 'query': {'action': 'deletePlaylist', 'url': i['uuid']}}
            ]})

        self.list = sorted(self.list, key=lambda k: k['title'].lower())

        directory.add(self.list)
        return self.list


    def play(self, url):
        stream = self.resolve(url)

        if stream == None: return

        directory.resolve(stream)
        self.addHistory(url)


    def item_list_1(self, url):
        try:
            headers = self.login(url)
            if headers == None: raise Exception()

            url = urlparse.urljoin(self.base_link, url)
            url += self.key_link

            items = client.request(url, headers=headers)
            items = json.loads(items)
        except:
            return

        for item in items:
            try:
                title = item['name'].strip()
                title = title.encode('utf-8')

                image = item['image']
                image = image.encode('utf-8')

                url = item['uuid'].strip()
                url = self.albums_link % url
                url = url.encode('utf-8')

                uuid = item['uuid'].strip()
                uuid = uuid.encode('utf-8')

                try: genre = item['tags']
                except: genre = []
                genre = [i['name'] for i in genre if 'name' in i]
                genre = [x for y,x in enumerate(genre) if x not in genre[:y]]
                genre = '/'.join(genre).replace('/', ' / ')
                if genre == '': genre = '0'
                genre = genre.encode('utf-8')

                self.list.append({'title': title, 'artist': title, 'genre': genre, 'url': url, 'image': image, 'uuid': uuid})
            except:
                pass

        return self.list


    def item_list_2(self, url):
        try:
            headers = self.login(url)
            if headers == None: raise Exception()

            url = urlparse.urljoin(self.base_link, url)
            url += self.key_link

            items = client.request(url, headers=headers)
            items = json.loads(items)
        except:
            return

        for item in items:
            try:
                title = item['name'].strip()
                try: title += ' [%s]' % item['format'].title()
                except: pass
                title = title.encode('utf-8')

                try: format = item['format']
                except: format = '0'

                image = item['image']
                image = image.encode('utf-8')

                url = item['uuid'].strip()
                url = self.songs_link % url
                url = url.encode('utf-8')

                uuid = item['uuid'].strip()
                uuid = uuid.encode('utf-8')

                try: genre = item['tags']
                except: genre = []
                genre = [i['name'] for i in genre if 'name' in i]
                genre = [x for y,x in enumerate(genre) if x not in genre[:y]]
                genre = '/'.join(genre).replace('/', ' / ')
                if genre == '': genre = '0'
                genre = genre.encode('utf-8')

                self.list.append({'title': title, 'album': title, 'genre': genre, 'url': url, 'image': image, 'format': format, 'uuid': uuid})
            except:
                pass

        filter = []
        filter += [i for i in self.list if i['format'] == 'album']
        filter += [i for i in self.list if not i['format'] == 'album']
        self.list = filter

        return self.list


    def item_list_3(self, url):
        try:
            headers = self.login(url)
            if headers == None: raise Exception()

            url = urlparse.urljoin(self.base_link, url)
            url += self.key_link

            items = client.request(url, headers=headers)
            items = json.loads(items)

            album = items['name'].strip()
            album = album.encode('utf-8')

            artist = items['artists'][0]['name'].strip()
            artist = artist.encode('utf-8')

            image = items['artists'][0]['image']
            image = image.encode('utf-8')

            try: genre = items['tags']
            except: genre = []
            genre = [i['name'] for i in genre if 'name' in i]
            genre = [x for y,x in enumerate(genre) if x not in genre[:y]]
            genre = '/'.join(genre).replace('/', ' / ')
            if genre == '': genre = '0'
            genre = genre.encode('utf-8')

            items = items['tracklist']
        except:
        	return

        for item in items:
            try:
                title = item['title'].strip()
                title = title.encode('utf-8')

                uuid = item['uuid'].strip()
                uuid = uuid.encode('utf-8')

                self.list.append({'title': title, 'album': album, 'artist': artist, 'genre': genre, 'url': uuid, 'image': image, 'uuid': uuid})
            except:
                pass

        threads = []
        for i in range(0, len(self.list)): threads.append(workers.Thread(self.item_list_3_worker, i))
        [i.start() for i in threads]
        [i.join() for i in threads]

        self.list = [i for i in self.list if 'check' in i and i['check'] > 0]

        return self.list


    def item_list_3_worker(self, i):
        try:
            url = self.list[i]['url']
            check = self.resolve(url, check=True)
            self.list[i].update({'check': int(check)})
        except:
            pass


    def item_list_4(self, url):
        try:
            headers = self.login(url)
            if headers == None: raise Exception()

            url = urlparse.urljoin(self.base_link, url)
            url += self.key_link

            dupes = []

            items = client.request(url, headers=headers)
            items = json.loads(items)

            try: items = [i['track'] for i in items]
            except: pass
            try: items = items['content']
            except: pass
        except:
        	return

        for item in items:
            try:
                title = item['title'].strip()
                try: title = '%s - %s' % (item['artists'][0]['name'].strip(), title)
                except: pass
                title = title.encode('utf-8')

                album = item['release']['name'].strip()
                album = album.encode('utf-8')

                artist = item['artists'][0]['name'].strip()
                artist = artist.encode('utf-8')

                try: image = item['release']['image']
                except: image = item['artists'][0]['image']
                image = image.encode('utf-8')

                uuid = item['uuid'].strip()
                uuid = uuid.encode('utf-8')

                if uuid in dupes: raise Exception()
                dupes.append(uuid)

                try: genre = item['release']['tags']
                except: genre = []
                genre = [i['name'] for i in genre if 'name' in i]
                genre = [x for y,x in enumerate(genre) if x not in genre[:y]]
                genre = '/'.join(genre).replace('/', ' / ')
                if genre == '': genre = '0'
                genre = genre.encode('utf-8')

                self.list.append({'title': title, 'album': album, 'artist': artist, 'genre': genre, 'url': uuid, 'image': image, 'uuid': uuid})
            except:
                pass

        return self.list


    def item_list_5(self, url):
        try:
            headers = self.login(url)
            if headers == None: raise Exception()

            url = urlparse.urljoin(self.base_link, url)
            url += self.key_link

            items = client.request(url, headers=headers)
            items = json.loads(items)
        except:
        	return

        for item in items:
            try:
                title = item['name'].strip()
                title = title.encode('utf-8')

                url = item['id'].strip()
                url = self.userlist_link % url
                url = url.encode('utf-8')

                uuid = item['id'].strip()
                uuid = uuid.encode('utf-8')

                self.list.append({'title': title, 'url': url, 'uuid': uuid})
            except:
                pass

        return self.list


    def resolve(self, url, check=False):
        try:
            url = self.play_link % url
            url = urlparse.urljoin(self.base_link, url)
            url += self.key_link

            items = client.request(url)
            items = json.loads(items)
            items = [i for i in items if i['source'] == 'youtube']

            filter = [i for i in items if 'official' in i['tags']]
            filter += [i for i in items if not 'official' in i['tags']]
            items = [i['id'] for i in filter]

            if check == True: return len(items)
        except:
            return

        for item in items:
            try:
                url = 'http://www.youtube.com/watch?v=%s' % item

                result = client.request(url)

                msg = client.parseDOM(result, 'div', attrs = {'id': 'unavailable-submessage'})
                msg = re.search('[a-zA-Z]', ''.join(msg))

                nte = client.parseDOM(result, 'div', attrs = {'id': 'watch7-notification-area'})
                nte = (len(nte) > 0)

                if msg or nte: raise Exception()

                url = 'plugin://plugin.video.youtube/play/?video_id=%s' % item

                return url
            except:
                pass


    def login(self, url):
        try:
            if not ('/user/' in url or url == ''): return {}

            if (self.email == '' or self.password == ''):
        	    control.infoDialog(control.lang(30181).encode('utf-8'))
        	    return

            oauth = urlparse.urljoin(self.base_link, '/auth/login/')
            ohead = {'Content-Type': 'application/json;charset=utf-8'}
            opost = {'email': self.email, 'password': self.password, 'key': self.key}

            token = client.request(oauth, post=json.dumps(opost), headers=ohead)
            token = json.loads(token)['token']

            headers = {'Authorization': 'Bearer %s' % token}
            return headers
        except:
        	pass


    def addHistory(self, url):
        try:
            headers = self.login('')
            if headers == None: raise Exception()

            headers['Content-Type'] = 'application/json;charset=utf-8'
            headers['User-Agent'] = client.randomagent()

            u = '/player/history/?category=artist&uuid=%s' % url
            u = urlparse.urljoin(self.base_link, u)
            u += self.key_link

            post = {'uuid': url, 'source_provider': 'youtube', 'environment': 'web', 'key': self.key}

            import urllib2
            request = urllib2.Request(u, json.dumps(post), headers)
            request.get_method = lambda: 'PUT'
            response = urllib2.urlopen(request)
            response.close()
        except:
        	pass


    def collectArtist(self, url):
        try:
            icon = control.infoLabel('ListItem.Icon')
            head = control.infoLabel('ListItem.Label')

            headers = self.login('')
            if headers == None: raise Exception()

            headers['Content-Type'] = 'application/json;charset=utf-8'

            u = urlparse.urljoin(self.base_link, '/user/library/?limit=10')
            u += self.key_link

            post = {'category': 'artist', 'uuid': url, 'key': self.key}

            r = client.request(u, post=json.dumps(post), headers=headers, error=True)

            try: r = json.loads(r)['message']
            except: pass
            try: r = json.loads(r)['status']
            except: pass

            control.infoDialog(r, heading=head, icon=icon)
        except:
        	pass


    def uncollectArtist(self, url):
        try:
            headers = self.login('')
            if headers == None: raise Exception()

            headers['Content-Type'] = 'application/json;charset=utf-8'
            headers['User-Agent'] = client.randomagent()

            u = '/user/library/?category=artist&uuid=%s' % url
            u = urlparse.urljoin(self.base_link, u)
            u += self.key_link

            import urllib2
            request = urllib2.Request(u, None, headers)
            request.get_method = lambda: 'DELETE'
            response = urllib2.urlopen(request)
            response.close()

            control.refresh()
        except:
        	pass


    def collectAlbum(self, url):
        try:
            icon = control.infoLabel('ListItem.Icon')
            head = control.infoLabel('ListItem.Label')

            headers = self.login('')
            if headers == None: raise Exception()

            headers['Content-Type'] = 'application/json;charset=utf-8'

            u = urlparse.urljoin(self.base_link, '/user/library/?limit=10')
            u += self.key_link

            post = {'category': 'release', 'uuid': url, 'key': self.key}

            r = client.request(u, post=json.dumps(post), headers=headers, error=True)

            try: r = json.loads(r)['message']
            except: pass
            try: r = json.loads(r)['status']
            except: pass

            control.infoDialog(r, heading=head, icon=icon)
        except:
        	pass


    def uncollectAlbum(self, url):
        try:
            headers = self.login('')
            if headers == None: raise Exception()

            headers['Content-Type'] = 'application/json;charset=utf-8'
            headers['User-Agent'] = client.randomagent()

            u = '/user/library/?category=release&uuid=%s' % url
            u = urlparse.urljoin(self.base_link, u)
            u += self.key_link

            import urllib2
            request = urllib2.Request(u, None, headers)
            request.get_method = lambda: 'DELETE'
            response = urllib2.urlopen(request)
            response.close()

            control.refresh()
        except:
        	pass


    def unrecommendArtist(self, url):
        try:
            headers = self.login('')
            if headers == None: raise Exception()

            headers['Content-Type'] = 'application/json;charset=utf-8'

            u = '/user/profile/blacklist/?uuid=%s' % url
            u = urlparse.urljoin(self.base_link, u)
            u += self.key_link

            post = {'uuid': url}

            r = client.request(u, post=json.dumps(post), headers=headers, error=True)

            control.refresh()
        except:
        	pass


    def joinPlaylist(self, url):
        try:
            icon = control.infoLabel('ListItem.Icon')

            try:
                uuid = None
                path = control.infoLabel('Container.FolderPath')
                uurl = urlparse.parse_qs(urlparse.urlparse(path).query)['url'][0]
                uuid = urlparse.parse_qs(urlparse.urlparse(uurl).query)['id'][0]
            except:
                pass

            items = cache.get(self.item_list_5, 0, self.userlists_link)
            items = [i for i in items if 'uuid' in i and not i['uuid'] == uuid]

            t = control.lang(30184).encode('utf-8')
            s = control.selectDialog([i['title'] for i in items], t)

            if s == -1: return

            name = items[s]['title']
            uuid = items[s]['uuid']

            headers = self.login('')
            if headers == None: raise Exception()

            headers['Content-Type'] = 'application/json;charset=utf-8'

            u = '/user/playlist/?id=%s' % uuid
            u = urlparse.urljoin(self.base_link, u)
            u += self.key_link

            post = {'id': uuid, 'content': url, 'append': 'true', 'key': self.key}

            r = client.request(u, post=json.dumps(post), headers=headers, error=True)

            try: r = json.loads(r)['message']
            except: pass
            try: r = json.loads(r)['status']
            except: pass

            control.infoDialog(r, heading=name, icon=icon)
        except:
        	pass


    def newPlaylist(self, url):
        try:
            icon = control.infoLabel('ListItem.Icon')

            t = control.lang(30185).encode('utf-8')
            k = control.keyboard('', t) ; k.doModal()
            name = k.getText() if k.isConfirmed() else None

            if (name == None or name == ''): return

            headers = self.login('')
            if headers == None: raise Exception()

            headers['Content-Type'] = 'application/json;charset=utf-8'

            u = '/user/playlist/?limit=10'
            u = urlparse.urljoin(self.base_link, u)
            u += self.key_link

            post = {'name': name, 'content': url, 'key': self.key}

            r = client.request(u, post=json.dumps(post), headers=headers, error=True)

            try: r = json.loads(r)['message']
            except: pass
            try: r = json.loads(r)['status']
            except: pass

            control.infoDialog(r, heading=name, icon=icon)
        except:
        	pass


    def leavePlaylist(self, url):
        try:
            path = control.infoLabel('Container.FolderPath')
            uurl = urlparse.parse_qs(urlparse.urlparse(path).query)['url'][0]
            uuid = urlparse.parse_qs(urlparse.urlparse(uurl).query)['id'][0]

            content = cache.get(self.item_list_4, 0, uurl)
            content = [i['uuid'] for i in content if 'uuid' in i]
            content = [i for i in content if not i == url]
            content = ','.join(content)

            headers = self.login('')
            if headers == None: raise Exception()

            headers['Content-Type'] = 'application/json;charset=utf-8'

            u = '/user/playlist/?id=%s' % uuid
            u = urlparse.urljoin(self.base_link, u)
            u += self.key_link

            post = {'id': uuid, 'content':content, 'key': self.key}

            r = client.request(u, post=json.dumps(post), headers=headers, error=True)

            control.refresh()
        except:
        	pass


    def renamePlaylist(self, url):
        try:
            t = control.lang(30183).encode('utf-8')
            k = control.keyboard('', t) ; k.doModal()
            name = k.getText() if k.isConfirmed() else None

            if (name == None or name == ''): return

            headers = self.login('')
            if headers == None: raise Exception()

            headers['Content-Type'] = 'application/json;charset=utf-8'

            u = '/user/playlist/?id=%s' % url
            u = urlparse.urljoin(self.base_link, u)
            u += self.key_link

            post = {'id': url, 'name': name, 'key': self.key}

            r = client.request(u, post=json.dumps(post), headers=headers, error=True)

            control.refresh()
        except:
        	pass


    def deletePlaylist(self, url):
        try:
            yes = control.yesnoDialog(control.lang(30182).encode('utf-8'), '', '')
            if not yes: return

            headers = self.login('')
            if headers == None: raise Exception()

            headers['Content-Type'] = 'application/json;charset=utf-8'
            headers['User-Agent'] = client.randomagent()

            u = '/user/playlist/?id=%s' % url
            u = urlparse.urljoin(self.base_link, u)
            u += self.key_link

            import urllib2
            request = urllib2.Request(u, None, headers)
            request.get_method = lambda: 'DELETE'
            response = urllib2.urlopen(request)
            response.close()

            control.refresh()
        except:
        	pass


