import hashlib
import re
import uuid
import time
from xml.etree import ElementTree

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

    def __init__(self, amount=25):
        self._amount = amount
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

    def get_videos(self, channel_config, format_id):
        # first get the correct id for the format
        params = {
            'fields': '*,.*,formatTabs.*,formatTabs.formatTabPages.*',
            'name': '%s.php' % format_id
        }
        json_data = self._perform_request(channel_config, params=params, path='formats/seo')
        items = json_data.get('formatTabs', {}).get('items', [])
        format_title = json_data.get('title', '')

        video_list = []
        if len(items) > 0:
            _format_id = items[0]['id']
            params = {
                'fields': '*,formatTabPages.*,formatTabPages.container.*,formatTabPages.container.movies.*,formatTabPages.container.movies.format.*,formatTabPages.container.movies.paymentPaytypes.*,formatTabPages.container.movies.pictures'
            }
            json_data = self._perform_request(channel_config, params=params, path='formatlists/%s/' % str(_format_id))
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
                    if _item.get('free', False):
                        video_path = '%s/%s' % (_item['format']['seoUrl'], _item['seoUrl'])
                        thumb = ''
                        thumbs = _item.get('pictures', {})
                        if not thumbs:
                            thumbs = {}
                            pass
                        thumbs = thumbs.get('default', [])
                        if len(thumbs):
                            thumb = channel_config['thumb-url'] % str(thumbs[0]['id'])
                            pass
                        else:
                            thumb = _item.get('format', {}).get('defaultImage169Logo', '')
                            pass
                        video = {
                            'title': _item['title'],
                            'format': format_title,
                            'id': _item['id'],
                            'path': video_path,
                            'plot': _item['articleLong'],
                            'published': _item['broadcastStartDate'],
                            'duration': _item['duration'],
                            'season': int(_item.get('season', 0)),
                            'episode': int(_item.get('episode', 0)),
                            'images': {
                                'thumb': thumb,
                                'fanart': _item.get('format', {}).get('defaultImage169Format', '')
                            }
                        }
                        video_list.append(video)
                        pass
                    pass
                pass
            pass

        return {'items': video_list}

    def get_formats(self, channel_config):
        params = {
            'fields': 'title,station,title,titleGroup,seoUrl,categoryId,*',
            'filter': '{"Station":"%s","Disabled":"0","CategoryId":{"containsIn":["serie","news"]}}' % channel_config[
                'id'],
            'maxPerPage': '1000'
        }
        json_data = self._perform_request(channel_config, params=params, path='formats')

        format_list = []
        items = json_data.get('items', [])
        for item in items:
            if item['icon'] in ['free', 'new']:
                format_list.append(
                    {
                        'title': item['title'],
                        'id': item['seoUrl'],
                        'images': {
                            'fanart': item.get('defaultImage169Format', ''),
                            'thumb': item.get('defaultImage169Logo')
                        }
                    }
                )
                pass
            pass

        return {'items': format_list}

    def search(self, q):
        params = {'word': q,
                  'extend': '1'}
        return self._perform_request(path='/api/query/json/content.format_search', params=params)

    def _perform_request(self, channel_config, method='GET', headers=None, path=None, post_data=None, params=None,
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
            'Accept': 'application/json, text/plain, */*',
            'Origin': 'http://www.nowtv.de',
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.152 Safari/537.36',
            'DNT': '1',
            'Referer': 'http://www.nowtv.de/%s' % channel_config['id'],
            'Accept-Encoding': 'gzip',
            'Accept-Language': 'en-US,en;q=0.8,de;q=0.6'
        }
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

        if result is None:
            return {}

        return result.json()

    pass