import json
import re
from xml.etree import ElementTree
import datetime
import time

from resources.lib.kodion.exceptions import KodionException
from resources.lib.kodion import simple_requests as requests


class UnsupportedStreamException(KodionException):
    def __init__(self):
        KodionException.__init__(self, 'DRM Protected stream not supported')
        pass

    pass


class Client(object):
    CHANNELS = {
        'rtl': {
            'id': 'rtl',
            'title': 'RTL',
            'hds': 'http://hds.fra.rtlnow.de/hds-vod-enc/%s.m3u8',
            'hls': 'http://hls.fra.rtlnow.de/hls-vod-enc/%s.m3u8',
            'thumb-url': 'http://autoimg.rtl.de/rtlnow/%s/660x660/formatimage.jpg'
        },
        'rtl2': {
            'id': 'rtl2',
            'title': 'RTL II',
            'hds': 'http://hds.fra.rtlnow.de/hds-vod-enc/%s.m3u8',
            'hls': 'http://hls.fra.rtlnow.de/hls-vod-enc/%s.m3u8',
            'thumb-url': 'http://autoimg.rtl.de/rtlnow/%s/660x660/formatimage.jpg'
        },
        'vox': {
            'id': 'vox',
            'title': 'VOX',
            'hds': 'http://hds.fra.rtlnow.de/hds-vod-enc/%s.m3u8',
            'hls': 'http://hls.fra.rtlnow.de/hls-vod-enc/%s.m3u8',
            'thumb-url': 'http://autoimg.rtl.de/rtlnow/%s/660x660/formatimage.jpg'
        },
        'ntv': {
            'id': 'ntv',
            'title': 'N-TV',
            'hds': 'http://hds.fra.rtlnow.de/hds-vod-enc/%s.m3u8',
            'hls': 'http://hls.fra.rtlnow.de/hls-vod-enc/%s.m3u8',
            'thumb-url': 'http://autoimg.rtl.de/rtlnow/%s/660x660/formatimage.jpg'
        },
        'nitro': {
            'id': 'nitro',
            'title': 'RTL Nitro',
            'hds': 'http://hds.fra.rtlnow.de/hds-vod-enc/%s.m3u8',
            'hls': 'http://hls.fra.rtlnow.de/hls-vod-enc/%s.m3u8',
            'thumb-url': 'http://autoimg.rtl.de/rtlnow/%s/660x660/formatimage.jpg'
        },
        'superrtl': {
            'id': 'superrtl',
            'title': 'Super RTL',
            'hds': 'http://hds.fra.rtlnow.de/hds-vod-enc/%s.m3u8',
            'hls': 'http://hls.fra.rtlnow.de/hls-vod-enc/%s.m3u8',
            'thumb-url': 'http://autoimg.rtl.de/rtlnow/%s/660x660/formatimage.jpg'
        }
    }
    CONFIG_NTV_NOW = {'rtmpe': 'rtmpe://fms-fra%d.rtl.de/ntvnow/',
                      'manifest_f4m': 'http://www.n-tvnow.de/hds/videos/%s/manifest-hds.f4m',
                      'images': {
                          'format-thumbnail-url': 'http://autoimg.rtl.de/ntvnow/%FORMAT_ID%-default_image_169_logo/500x281/8b6ba.jpg',
                          'format-fanart-url': 'http://autoimg.rtl.de/ntvnow/%FORMAT_ID%-default_image_169_format/768x432/8b6ba.jpg'
                      }
    }

    CONFIG_RTL_NOW = {'rtmpe': 'rtmpe://fms-fra%d.rtl.de/rtlnow/',
                      'manifest_f4m': 'http://rtlnow.de/hds/videos/%s/manifest-hds.f4m',
                      'images': {
                          'format-thumbnail-url': 'http://autoimg.rtl.de/rtlnow/%FORMAT_ID%-default_image_169_logo/500x281/8b6ba.jpg',
                          'format-fanart-url': 'http://autoimg.rtl.de/rtlnow/%FORMAT_ID%-default_image_169_format/768x432/8b6ba.jpg'
                      }
    }
    CONFIG_RTL2_NOW = {'rtmpe': 'rtmpe://fms-fra%d.rtl.de/rtl2now/',
                       'manifest_f4m': 'http://rtl2now.rtl2.de/hds/videos/%s/manifest-hds.f4m',
                       'images': {
                           'format-thumbnail-url': 'http://autoimg.rtl.de/rtl2now/%FORMAT_ID%-default_image_169_logo/500x281/659c3.jpg',
                           'format-fanart-url': 'http://autoimg.rtl.de/rtl2now/%FORMAT_ID%-default_image_169_format/768x432/659c3.jpg'
                       }
    }

    CONFIG_VOX_NOW = {'rtmpe': 'rtmpe://fms-fra%d.rtl.de/voxnow/',
                      'manifest_f4m': 'http://voxnow.de/hds/videos/%s/manifest-hds.f4m',
                      'images': {
                          'format-thumbnail-url': 'http://autoimg.rtl.de/voxnow/%FORMAT_ID%-default_image_169_logo/500x281/d9f9a.jpg',
                          'format-fanart-url': 'http://autoimg.rtl.de/voxnow/%FORMAT_ID%-default_image_169_format/768x432/d9f9a.jpg'
                      }
    }

    def __init__(self, amount=25, token='', user_id=''):
        self._amount = amount
        self._token = token
        self._user_id = user_id
        pass

    def get_film_streams(self, film_id):
        result = []

        def _browse(_url):
            headers = {'Connection': 'keep-alive',
                       'Cache-Control': 'max-age=0',
                       'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                       'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/40.0.2214.38 Safari/537.36',
                       'DNT': '1',
                       'Accept-Encoding': 'gzip',
                       'Accept-Language': 'en-US,en;q=0.8,de;q=0.6'}

            _result = requests.get(_url, headers=headers, verify=False)
            return _result.text

        def _get_xml(_xml_url):
            _xml = _browse(_xml_url)
            return ElementTree.fromstring(_xml)

        def _get_data_from_html(_video_url):
            html = _browse(_video_url)
            pos = html.find('PlayerWatchdog.ini')
            if pos and pos >= 0:
                html = html[pos:]
                pos = html.find('PlayerWatchdog.setTimer')
                if pos:
                    html = html[:pos]
                    pass
                pass
            else:
                player_url = re.search(r"var playerUrl = baseURL \+ \'(?P<url>.+)\'", html)
                if player_url:
                    url = self._config['url'] + player_url.group('url')
                    return _get_data_from_html(url)
                pass

            player_data_url = re.search(r"'playerdata': '(?P<playerdata_url>[^']+)'", html)
            if player_data_url:
                player_data_url = player_data_url.group('playerdata_url')
                pass
            else:
                player_data_url = None
                pass

            player_url = re.search(r"'playerurl': '(?P<player_url>[^']+)'", html)
            if player_url:
                player_url = player_url.group('player_url')
                pass
            else:
                player_url = None
                pass

            return player_data_url, player_url

        def _process_manifest(_url):
            try:
                headers = {'Connection': 'keep-alive',
                           'Cache-Control': 'max-age=0',
                           'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                           'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/40.0.2214.38 Safari/537.36',
                           'DNT': '1',
                           'Accept-Encoding': 'gzip, deflate, sdch',
                           'Accept-Language': 'en-US,en;q=0.8,de;q=0.6'}

                _result = requests.get(_url, headers=headers, verify=False)

                _xml = ElementTree.fromstring(_result.text)
                _url = ''
                _last_bit_rate = 0
                for _media in _xml:
                    _bit_rate = int(_media.get('bitrate'))
                    if _bit_rate > _last_bit_rate:
                        _url = _media.get('href')
                        _last_bit_rate = _bit_rate
                        pass
                    pass
                if _url:
                    return _url
            except:
                raise UnsupportedStreamException
            pass

        def _normalize_url(_url):
            """
            Transform rtmpe urls to hds urls
            """
            rtmpe_match = re.search(r'(?P<url>rtmpe://(?:[^/]+/){2})(?P<play_path>.+)', _url)
            if rtmpe_match:
                _url = self._config['hds'] % rtmpe_match.group('play_path')
                pass

            """
            Transform hds urls to hls urls
            """
            hds_match = re.search(r'http://hds.+/(?P<play_path>\d+/.+)', _url)
            if hds_match:
                _url = _url.replace('hds', 'hls').replace('f4m', 'm3u8')
                pass

            return _url

        """
        First test manifest *.f4m
        This is the fastest way and allows us to play US TV shows.
        """
        manifest_url = self._config['manifest_f4m'] % str(film_id)
        try:
            video_url = _process_manifest(manifest_url)
            if video_url:
                video_url = _normalize_url(video_url)
                return [video_url]
        except:
            # do nothing and let the fallback happen :)
            pass

        """
        Fallback
        """
        json_data = self.get_film_details(film_id)
        film = json_data.get('result', {}).get('content', {}).get('film', {})
        video_url = str(film.get('videourl', ''))
        if video_url:
            player_data_url, player_url = _get_data_from_html(video_url)
            if not player_data_url or not player_url:
                raise UnsupportedStreamException

            player_url = player_url.replace('.liveab.swf', '.swf')

            xml = _get_xml(player_data_url)
            video_info = xml.find('./playlist/videoinfo')
            for filename in video_info.findall('filename'):
                # FlashAccess DRM protection isn't supported yet
                meta_daten = filename.get('metadaten')
                header_daten = filename.get('headerdaten')
                if meta_daten and header_daten:
                    raise UnsupportedStreamException

                filename_text = filename.text

                """
                From *.manifest-hsd.f4m we extract the url with the highest bitrate
                """
                if re.search(r'http://.+/hds/.+/\d+/manifest-hds.f4m', filename_text):
                    filename_text = _process_manifest(filename.text)
                    pass

                filename_text = _normalize_url(filename_text)

                result.append(filename_text)
                pass
            pass

        return result

    def get_video_streams(self, channel_config, video_id):
        params = {'fields': 'fields=*,format,files,breakpoints,paymentPaytypes,trailers'}
        json_data = self._perform_request(channel_config, path='movies/%s/' % video_id, params=params)
        items = json_data.get('files', {}).get('items', [])
        result = []
        for item in items:
            video_type = item['type']
            path = item['path']
            if video_type == 'video/x-f4v':
                path = re.sub(r'/(.+)/((\d+)/(.*))', r'/\1/videos/\2', path)
                pass
            bitrate = int(item['bitrate'])
            video_url = channel_config['hls'] % path.strip('/')
            video_stream = {
                'title': '%s@%d' % (video_type, bitrate),
                'sort': [bitrate],
                'url': video_url,
                'video': {
                    'bitrate': bitrate,
                }
            }
            result.append(video_stream)
            pass
        return result

    def login(self, username_mail, password):
        login_fields = ['*', 'user', ['agb']]
        params = {'fields': json.dumps(login_fields)}
        post_data = {'email': username_mail,
                     'password': password}
        headers = {'Referer': 'http://www.nowtv.de/?login',
                   'Content-Type': 'application/json;charset=UTF-8'}
        return self._perform_request(method='POST', headers=headers, path='backend/login', post_data=post_data,
                                     params=params)

    def _simple_parse_datetime(self, datetime_string):
        result = []
        components = datetime_string.split(' ')
        result.extend(components[0].split('-'))
        result.extend(components[1].split(':'))

        return datetime(*result)

    def get_format_tabs(self, channel_config, seo_url):
        # first get the correct id for the format
        params = {
            'fields': '*,.*,formatTabs.*,formatTabs.formatTabPages.*',
            'name': '%s.php' % seo_url
        }
        json_data = self._perform_request(channel_config, params=params, path='formats/seo')

        result = []

        # years
        if not json_data.get('tabSeason', True):
            start_date = json_data['tabSeasonStartDate']
            start_date = datetime.datetime(*time.strptime(start_date, '%Y-%m-%d %H:%M:%S')[:6])

            end_date = str(json_data['tabSeasonEndDate'])
            end_date = datetime.datetime(*time.strptime(end_date, '%Y-%m-%d %H:%M:%S')[:6])

            # first normalize end date
            now_date = datetime.datetime.now()
            if end_date > now_date:
                end_date = now_date
                pass

            for year in range(start_date.year, end_date.year + 1):
                tab = {'title': str(year),
                       'type': 'date-span',
                       'images': {'thumb': json_data['defaultImage169Logo'],
                                  'fanart': json_data['defaultImage169Format']}}
                if year == start_date.year:
                    tab['start'] = start_date.strftime('%Y-%m-%d %H:%M:%S')
                    pass
                else:
                    tab['start'] = '%d-01-01 00:00:00' % year
                    pass

                if year == end_date.year:
                    tab['end'] = end_date.strftime('%Y-%m-%d %H:%M:%S')
                    pass
                else:
                    tab['end'] = '%d-12-31 00:00:00' % year
                    pass
                result.append(tab)
                pass

            # reverse order of the years
            result = result[::-1]
            pass

        # tabs
        if json_data.get('tabSeason', False) or json_data.get('tabSpecialTeaserPosition', '') != 'none':
            tab_items = json_data.get('formatTabs', {})
            if not tab_items:
                tab_items = {}
                pass
            tab_items = tab_items.get('items', [])
            for tab_item in tab_items:
                title = tab_item['headline']

                # only valid title
                if not title:
                    continue

                tab = {'title': title,
                       'id': tab_item['id'],
                       'images': {'thumb': json_data['defaultImage169Logo'],
                                  'fanart': json_data['defaultImage169Format']},
                       'type': 'tab'}
                result.append(tab)
                pass
            pass

        return result

    def _process_video_data(self, json_data):
        channel_id = json_data.get('format', {})
        if channel_id:
            channel_id = channel_id.get('station', '')
        if not channel_id:
            channel_id = json_data['cornerLogo']
            pass
        channel_config = self.CHANNELS[channel_id]

        video_path = '%s/%s' % (json_data['format']['seoUrl'], json_data['seoUrl'])

        # a list of possible pictures
        picture_id = ''
        pictures = json_data.get('pictures', {})
        if pictures:
            picture_id = pictures.get('default', [{'id': ''}])[0]['id']
            pass
        # last possible fallback
        if not picture_id:
            picture = json_data.get('picture', {})
            if not picture:
                picture = {}
                pass
            picture_id = picture.get('id', '')
            pass
        if picture_id:
            thumb = channel_config['thumb-url'] % str(picture_id)
            pass
        else:
            thumb = json_data.get('format', {}).get('defaultImage169Logo', '')
            pass

        # episode fix
        episode = json_data.get('episode', 0)
        if isinstance(episode, basestring):
            episode = 0
            pass
        video = {
            'title': json_data['title'],
            'channel': channel_id,
            'free': json_data.get('free', False),
            'payed': json_data.get('payed', False),
            'format': json_data.get('format', {}).get('title', ''),
            'id': json_data['id'],
            'path': video_path,
            'plot': json_data.get('articleShort', json_data.get('articleLong', '')),
            'published': json_data['broadcastStartDate'],
            'duration': json_data['duration'],
            'season': json_data.get('season', 0),
            'episode': episode,
            'images': {
                'thumb': thumb,
                'fanart': json_data.get('format', {}).get('defaultImage169Format', '')
            }
        }
        # add price
        if not video['free']:
            price = json_data['paymentPaytypes']['items'][0]
            price = '%s %s' % (price['price'], price['currency'])
            video['price'] = price
            pass

        return video

    def get_videos_by_date_filter(self, channel_config, format_id, start_date, end_date):
        video_list = []

        filter = {'BroadcastStartDate': {'between': {
            'start': start_date,
            'end': end_date}}, 'FormatId': int(format_id)}
        params = {
            'fields': '*,format,paymentPaytypes,pictures,trailers',
            'filter': json.dumps(filter),
            'maxPerPage': '50',
            'order': 'BroadcastStartDate desc'}
        json_data = self._perform_request(channel_config, params=params, path='movies')
        items = json_data.get('items', [])
        for item in items:
            video = self._process_video_data(item)
            video_list.append(video)
            pass

        return {'items': video_list}

    def get_videos_by_format_list(self, channel_config, format_list_id):
        video_list = []

        params = {
            'fields': '*,formatTabPages.*,formatTabPages.container.*,formatTabPages.container.movies.*,formatTabPages.container.movies.format.*,formatTabPages.container.movies.paymentPaytypes.*,formatTabPages.container.movies.pictures',
            'maxPerPage': '100',
            'page': '1'
        }
        json_data = self._perform_request(channel_config, params=params, path='formatlists/%s/' % str(format_list_id))
        format_tab_pages = json_data.get('formatTabPages', {})
        items = format_tab_pages.get('items', [])

        for item in items:
            container = item.get('container', {})
            movies = container.get('movies', {})
            if not movies:
                movies = {}
                pass
            _items = movies.get('items', [])
            for _item in _items:
                # in rare cases this property was missing. This also means the item on the webpage wont work either.
                format_exists = _item.get('format', None)
                if not format_exists:
                    continue
                    pass

                video = self._process_video_data(_item)
                video_list.append(video)
                pass
            pass

        return {'items': video_list}

    def _make_item_to_format(self, json_item):
        format_item = {
            'title': json_item['title'],
            'station': json_item.get('station', ''),
            'id': json_item['id'],
            'seoUrl': json_item['seoUrl'],
            'free': json_item['icon'] in ['free', 'new'],
            'images': {
                'fanart': json_item.get('defaultImage169Format', ''),
                'thumb': json_item.get('defaultImage169Logo')
            }
        }
        return format_item

    def get_favorites(self, page=1):
        params = {'fields': '*,format',
                  'maxPerPage': str(self._amount),
                  'page': str(page)}
        headers = {'Accept': 'application/json'}
        path = '/myprogramme/formats/%s' % self._user_id
        json_data = self._perform_request(method='GET', headers=headers, path=path, params=params)

        format_list = []
        items = json_data.get('items', [])
        for item in items:
            item = item.get('format', {})
            format_item = self._make_item_to_format(item)
            format_list.append(format_item)
            pass

        return {'items': format_list}

    def add_favorite_format(self, format_id):
        headers = {'Accept': '*/*'}
        # no idea what german developer thought by that...but I don't care anymore
        self._perform_request(method='OPTIONS', headers=headers, path='/myprogramme/formats/newitem/')

        json_data = {'formatId': str(format_id),
                     'userId': self._user_id}
        headers = {'Accept': 'application/json',
                   'Content-Type': 'application/json'}
        self._perform_request(method='POST', headers=headers, path='/myprogramme/formats/newitem/', post_data=json_data)

        # again !?!?! jesus
        path = '/myprogramme/formats/%s/' % self._user_id
        params = {'fields': '*,format',
                  'maxPerPage': '100',
                  'page': '1'}
        headers = {'Accept': 'application/json'}
        self._perform_request(method='OPTIONS', headers=headers, path=path, params=params)
        pass

    def remove_favorite_format(self, format_id):
        params = {'formatId': str(format_id),
                  'userId': self._user_id}
        headers = {'Accept': '*/*'}
        # no idea what german developer thought by that...but I don't care anymore
        self._perform_request(method='OPTIONS', headers=headers, path='/myprogramme/formats/delete/', params=params)
        self._perform_request(method='DELETE', path='/myprogramme/formats/delete/', params=params)

        # again !?!?! jesus
        path = '/myprogramme/formats/%s/' % self._user_id
        params = {'fields': '*,format',
                  'maxPerPage': '100',
                  'page': '1'}
        self._perform_request(method='OPTIONS', headers=headers, path=path, params=params)
        pass

    def get_watch_later(self, page=1):
        params = {'fields': '*,movie.*,movie.format,movie.picture,movie.preview,movie.paymentPaytypes',
                  'maxPerPage': str(self._amount),
                  'page': str(page)}
        headers = {'Accept': 'application/json'}
        path = '/myprogramme/playlist/%s' % self._user_id
        json_data = self._perform_request(method='GET', headers=headers, path=path, params=params)

        video_list = []
        items = json_data.get('items', [])
        for item in items:
            item = item.get('movie', {})
            video_item = self._process_video_data(item)
            video_list.append(video_item)
            pass

        return {'items': video_list}

    def add_watch_later_video(self, video_id):
        headers = {'Accept': '*/*'}
        # no idea what german developer thought by that...but I don't care anymore
        self._perform_request(method='OPTIONS', headers=headers, path='/myprogramme/playlist/newitem/')

        json_data = {'movieId': str(video_id),
                     'userId': self._user_id}
        headers = {'Accept': 'application/json',
                   'Content-Type': 'application/json'}
        self._perform_request(method='POST', headers=headers, path='/myprogramme/playlist/newitem/', post_data=json_data)

        # again !?!?! jesus
        path = '/myprogramme/playlist/%s/' % self._user_id
        params = {'fields': '*,movie.*,movie.format,movie.picture,movie.preview,movie.paymentPaytypes',
                  'maxPerPage': '50',
                  'page': '1'}
        headers = {'Accept': 'application/json'}
        self._perform_request(method='OPTIONS', headers=headers, path=path, params=params)
        pass

    def remove_watch_later_video(self, video_id):
        params = {'movieId': str(video_id),
                  'userId': self._user_id}
        headers = {'Accept': '*/*'}
        # no idea what german developer thought by that...but I don't care anymore
        self._perform_request(method='OPTIONS', headers=headers, path='/myprogramme/playlist/delete/', params=params)
        self._perform_request(method='DELETE', path='/myprogramme/playlist/delete/', params=params)

        # again !?!?! jesus
        path = '/myprogramme/playlist/%s/' % self._user_id
        params = {'fields': '*,movie.*,movie.format,movie.picture,movie.preview,movie.paymentPaytypes',
                  'maxPerPage': '50',
                  'page': '1'}
        self._perform_request(method='OPTIONS', headers=headers, path=path, params=params)
        pass

    def get_formats(self, channel_config):
        filter = {
            'Station': channel_config['id'],
            'Disabled': '0',
            'CategoryId': {
                'containsIn': ['serie', 'news']
            }
        }
        params = {
            'fields': 'title,station,title,titleGroup,seoUrl,categoryId,*',
            'filter': json.dumps(filter),
            'maxPerPage': '1000'
        }
        json_data = self._perform_request(channel_config, params=params, path='formats')

        format_list = []
        items = json_data.get('items', [])
        for item in items:
            format_item = self._make_item_to_format(item)
            format_list.append(format_item)
            pass

        return {'items': format_list}

    def search(self, q):
        def _search(_q, _page=1, _count=0):
            _result = []
            _params = {'fields': 'id,title,station,seoUrl,searchAliasName,icon,*',
                       'maxPerPage': '500',
                       'page': str(_page)}
            _json_data = self._perform_request(None, path='formats', params=_params)
            _total = _json_data.get('total', 0)
            _items = _json_data.get('items', [])
            _count += len(_items)

            for _item in _items:
                if re.search(_q, _item.get('title', ''), re.IGNORECASE):
                    _result.append(_item)
                    pass
                pass

            if _count < _total:
                _result.extend(_search(_q, _page + 1, _count))
                pass
            return _result

        items = _search(q, 1)
        format_list = []
        for item in items:
            format_item = self._make_item_to_format(item)
            format_list.append(format_item)
            pass

        return {'items': format_list}

    def _perform_request(self, channel_config=None, method='GET', headers=None, path=None, post_data=None, params=None,
                         allow_redirects=True):
        # params
        _params = {}
        if not params:
            params = {}
            pass
        _params.update(params)

        # headers
        if not headers:
            headers = {}
            pass
        _headers = {
            'Accept': 'application/json',
            'Origin': 'http://www.nowtv.de',
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.152 Safari/537.36',
            'DNT': '1',
            'Referer': 'http://www.nowtv.de/',
            'Accept-Encoding': 'gzip',
            'Accept-Language': 'en-US,en;q=0.8,de;q=0.6'
        }
        if channel_config:
            _headers['Referer'] = 'http://www.nowtv.de/%s' % channel_config['id']
            pass

        # set the login token
        if self._token:
            _headers['X-AUTH-TOKEN'] = self._token
            pass
        _headers.update(headers)

        # url
        _url = 'https://api.nowtv.de/v3/'
        if path:
            _url = _url + path.strip('/')
            pass

        result = None
        if method == 'GET':
            result = requests.get(_url, params=_params, headers=_headers, verify=False, allow_redirects=allow_redirects)
            pass
        elif method == 'POST':
            result = requests.post(_url, json=post_data, params=_params, headers=_headers, verify=False,
                                   allow_redirects=allow_redirects)
            pass
        elif method == 'OPTIONS':
            requests.options(_url, params=_params, headers=_headers, verify=False, allow_redirects=allow_redirects)
            return {}
        elif method == 'DELETE':
            requests.delete(_url, params=_params, headers=_headers, verify=False, allow_redirects=allow_redirects)
            return {}

        if result is None:
            return {}

        return result.json()

    pass