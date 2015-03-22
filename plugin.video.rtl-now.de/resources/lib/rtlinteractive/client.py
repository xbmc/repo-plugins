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
    CONFIG_NTV_NOW = {'salt_phone': 'ba647945-6989-477b-9767-870790fcf552',
                      'salt_tablet': 'ba647945-6989-477b-9767-870790fcf552',
                      'key_phone': '46f63897-89aa-44f9-8f70-f0052050fe59',
                      'key_tablet': '56f63897-89aa-44f9-8f70-f0052050fe59',
                      'url': 'https://www.n-tvnow.de/',
                      'id': '49',
                      'rtmpe': 'rtmpe://fms-fra%d.rtl.de/ntvnow/',
                      'supports': [
                          'library',
                          # 'new',
                          'tips',
                          # 'top10',
                          'search'
                      ],
                      'images': {
                          'episode-thumbnail-url': 'http://autoimg.rtl.de/ntvnow/%PIC_ID%/660x660/formatimage.jpg',
                          'format-thumbnail-url': 'http://autoimg.rtl.de/ntvnow/%FORMAT_ID%-default_image_169_logo/500x281/8b6ba.jpg',
                          'format-fanart-url': 'http://autoimg.rtl.de/ntvnow/%FORMAT_ID%-default_image_169_format/768x432/8b6ba.jpg'
                      },
                      'http-header': {'X-App-Name': 'N-TV NOW App',
                                      'X-Device-Type': 'ntvnow_android',
                                      'X-App-Version': '1.3.1',
                                      # 'X-Device-Checksum': 'ed0226e4e613e4cd81c6257bced1cb1b',
                                      'Host': 'www.n-tvnow.de',
                                      'User-Agent': 'Mozilla/5.0 (Linux; Android 4.4.2; GT-I9505 Build/KOT49H) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/30.0.0.0 Mobile Safari/537.36'}}

    CONFIG_RTL_NOW = {'salt_phone': 'ba647945-6989-477b-9767-870790fcf552',
                      'salt_tablet': 'ba647945-6989-477b-9767-870790fcf552',
                      'key_phone': '46f63897-89aa-44f9-8f70-f0052050fe59',
                      'key_tablet': '56f63897-89aa-44f9-8f70-f0052050fe59',
                      'url': 'https://rtl-now.rtl.de/',
                      'id': '9',
                      'rtmpe': 'rtmpe://fms-fra%d.rtl.de/rtlnow/',
                      'supports': [
                          'library',
                          'new',
                          'tips',
                          'top10',
                          'search'
                      ],
                      'images': {
                          'episode-thumbnail-url': 'http://autoimg.rtl.de/ntvnow/%PIC_ID%/660x660/formatimage.jpg',
                          'format-thumbnail-url': 'http://autoimg.rtl.de/ntvnow/%FORMAT_ID%-default_image_169_logo/500x281/8b6ba.jpg',
                          'format-fanart-url': 'http://autoimg.rtl.de/ntvnow/%FORMAT_ID%-default_image_169_format/768x432/8b6ba.jpg'
                      },
                      'http-header': {'X-App-Name': 'RTL NOW App',
                                      'X-Device-Type': 'rtlnow_android',
                                      'X-App-Version': '1.3.1',
                                      # 'X-Device-Checksum': 'ed0226e4e613e4cd81c6257bced1cb1b',
                                      'Host': 'rtl-now.rtl.de',
                                      'User-Agent': 'Mozilla/5.0 (Linux; Android 4.4.2; GT-I9505 Build/KOT49H) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/30.0.0.0 Mobile Safari/537.36'}}

    CONFIG_RTL2_NOW = {'salt_phone': '9be405a6-2d5c-4e62-8ba0-ba2b5f11072d',
                       'salt_tablet': '4bfab4aa-705a-4e8c-b1a7-b551b1b2613f',
                       'key_phone': '26c0d1ac-e6a0-4df9-9f79-e07727f33380',
                       'key_tablet': '83bbc955-c96e-4b50-b263-bc7bcbcdf8c8',
                       'url': 'https://rtl2now.rtl2.de/',
                       'id': '37',
                       'rtmpe': 'rtmpe://fms-fra%d.rtl.de/rtl2now/',
                       'supports': [
                           'library',
                           'new',
                           'tips',
                           'top10',
                           'search'
                       ],
                       'images': {
                           'episode-thumbnail-url': 'http://autoimg.rtl.de/rtl2now/%PIC_ID%/660x660/formatimage.jpg',
                           'format-thumbnail-url': 'http://autoimg.rtl.de/rtl2now/%FORMAT_ID%-default_image_169_logo/500x281/659c3.jpg',
                           'format-fanart-url': 'http://autoimg.rtl.de/rtl2now/%FORMAT_ID%-default_image_169_format/768x432/659c3.jpg'
                       },
                       'http-header': {'X-App-Name': 'RTL II NOW App',
                                       'X-Device-Type': 'rtl2now_android',
                                       'X-App-Version': '1.3.1',
                                       # 'X-Device-Checksum': 'ed0226e4e613e4cd81c6257bced1cb1b',
                                       'Host': 'rtl2now.rtl2.de',
                                       'User-Agent': 'Mozilla/5.0 (Linux; Android 4.4.2; GT-I9505 Build/KOT49H) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/30.0.0.0 Mobile Safari/537.36'}}

    CONFIG_VOX_NOW = {'salt_phone': '9fb130b5-447e-4bbc-a44a-406f2d10d963',
                      'salt_tablet': '0df2738e-6fce-4c44-adaf-9981902de81b',
                      'key_phone': 'b11f23ac-10f1-4335-acb8-ebaaabdb8cde',
                      'key_tablet': '2e99d88e-088e-4108-a319-c94ba825fe29',
                      'url': 'https://www.voxnow.de/',
                      'id': '41',
                      'rtmpe': 'rtmpe://fms-fra%d.rtl.de/voxnow/',
                      'supports': [
                          'library',
                          'new',
                          'tips',
                          'top10',
                          'search'
                      ],
                      'images': {
                          'episode-thumbnail-url': 'http://autoimg.rtl.de/voxnow/%PIC_ID%/660x660/formatimage.jpg',
                          'format-thumbnail-url': 'http://autoimg.rtl.de/voxnow/%FORMAT_ID%-default_image_169_logo/500x281/d9f9a.jpg',
                          'format-fanart-url': 'http://autoimg.rtl.de/voxnow/%FORMAT_ID%-default_image_169_format/768x432/d9f9a.jpg'
                      },
                      'http-header': {'X-App-Name': 'VOX NOW App',
                                      'X-Device-Type': 'voxnow_android',
                                      'X-App-Version': '1.3.1',
                                      # 'X-Device-Checksum': 'a5fabf8ef3f4425c0b8ff716562dd1a3',
                                      'Host': 'www.voxnow.de',
                                      'User-Agent': 'Mozilla/5.0 (Linux; Android 4.4.2; GT-I9505 Build/KOT49H) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/30.0.0.0 Mobile Safari/537.36'}}

    def __init__(self, config, amount=25):
        self._config = config
        self._amount = amount
        pass

    @staticmethod
    def get_server_id():
        """
        For HDS streams we need a valid server id ('fms-fraXX'). We use the show 'RTL Nachtjournal' of rtlnow.de for all
        other NOW services (because the use all the same server).
        :return:
        """
        rtl_client = Client(Client.CONFIG_RTL_NOW)
        json_data = rtl_client.get_films(290)
        film_list = json_data.get('result', {}).get('content', {}).get('filmlist', {})
        film_id = None
        for key in film_list:
            film = film_list[key]
            if int(film.get('free', 1)) == 1:
                film_id = film['id']
                break
            pass

        if film_id is not None:
            streams = rtl_client.get_film_streams(film_id)
            if streams:
                stream = streams[0]
                re_match = re.search(r'rtmpe://fms-fra(?P<server_id>\d+).*', stream)
                if re_match:
                    server_id = int(re_match.group('server_id'))
                    return server_id
                pass
            pass

        return 22

    def get_config(self):
        return self._config

    def get_film_streams(self, film_id, server_id=22):
        result = []

        def _browse(_url):
            headers = {'Connection': 'keep-alive',
                       'Cache-Control': 'max-age=0',
                       'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                       'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/40.0.2214.38 Safari/537.36',
                       'DNT': '1',
                       'Accept-Encoding': 'gzip, deflate, sdch',
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
                    url = self._config['url']+player_url.group('url')
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

        json_data = self.get_film_details(film_id)
        film = json_data.get('result', {}).get('content', {}).get('film', {})
        video_url = str(film.get('videourl', ''))
        if video_url:
            player_data_url, player_url = _get_data_from_html(video_url)
            player_url = player_url.replace('.liveab.swf', '.swf')

            xml = _get_xml(player_data_url)
            video_info = xml.find('./playlist/videoinfo')
            for filename in video_info.findall('filename'):
                # FlashAccess DRM protection isn't supported yet
                metadaten = filename.get('metadaten')
                headerdaten = filename.get('headerdaten')
                if metadaten and headerdaten:
                    raise UnsupportedStreamException

                # No support for HDS MANIFEST
                if (re.search(r'http://.+/hds/.+/\d+/manifest-hds.f4m', filename.text)):
                    raise UnsupportedStreamException

                rtmpe_match = re.search(r'(?P<url>rtmpe://(?:[^/]+/){2})(?P<play_path>.+)', filename.text)
                hds_match = re.search(r'http://hds.+/(?P<play_path>\d+/.+)', filename.text)
                if rtmpe_match:
                    play_path = 'mp4:' + rtmpe_match.group('play_path')
                    url = '%s playpath=%s swfVfy=1 swfUrl=%s pageUrl=%s' % (
                        filename.text, play_path, player_url, video_url)
                    result.append(url)
                    pass
                elif hds_match:
                    play_path = hds_match.group('play_path').replace('.f4m', '')
                    rtmpe = self._config['rtmpe'] % server_id
                    url = '%s%s playpath=%s swfVfy=1 swfUrl=%s pageUrl=%s' % (
                        rtmpe, play_path, 'mp4:' + play_path, player_url, video_url)
                    result.append(url)
                    pass
                else:
                    result.append(filename.text)
                pass
            pass

        return result

    def get_film_details(self, film_id):
        params = {'filmid': str(film_id)}
        return self._perform_request(path='/api/query/json/content.film_details', params=params)

    def get_films(self, format_id, page=1):
        params = {'userid': '0',
                  'formatid': str(format_id),
                  'amount': str(self._amount),
                  'page': str(page)}
        return self._perform_request(path='/api/query/json/content.list_films', params=params)

    def get_formats(self):
        return self._perform_request(path='/api/query/json/content.list_formats')

    def search(self, q):
        params = {'word': q,
                  'extend': '1'}
        return self._perform_request(path='/api/query/json/content.format_search', params=params)

    def get_newest(self):
        return self._perform_request(path='/api/query/json/content.toplist_newest')

    def get_tips(self):
        return self._perform_request(path='/api/query/json/content_redaktion.tipplist')

    def get_top_10(self):
        return self._perform_request(path='/api/query/json/content.toplist_views')

    def get_live_streams(self):
        params = {'sessionid': self._create_session_id()}
        return self._perform_request(path='/api/query/json/livestream.available', params=params)

    def _create_session_id(self):
        session_id = str(uuid.uuid4())
        session_id = session_id.replace('-', '')
        return session_id

    def _calculate_token(self, timestamp, params):
        token = ""

        hash_map = {}
        hash_map.update(params)

        string_builder = ''
        string_builder += self._config['key_tablet']
        string_builder += ';'
        string_builder += self._config['salt_tablet']
        string_builder += ';'
        string_builder += timestamp

        params = sorted(hash_map.items())

        for param in params:
            string_builder += ';'
            string_builder += param[1]
            pass

        if len(hash_map) == 0:
            string_builder += ';'
            pass

        try:
            message_digest = hashlib.md5()
            message_digest.update(string_builder)
            abyte0 = message_digest.digest()
            length = len(abyte0)

            for b in bytearray(abyte0):
                val = b
                val = 0x100 | 0xFF & val
                hval = hex(val).lower()
                token += hval[3:]
        except:
            token = ''

        return token

    def _perform_request(self, method='GET', headers=None, path=None, post_data=None, params=None,
                         allow_redirects=True):
        # params
        _params = {}
        if not params:
            params = {}
            pass
        # always set the id
        params['id'] = self._config['id']

        _params.update(params)
        _params['_key'] = self._config['key_tablet']
        timestamp = str(int(time.time()))
        _params['_ts'] = timestamp
        _params['_tk'] = self._calculate_token(timestamp, params)
        _params['_auth'] = 'integrity'

        # headers
        if not headers:
            headers = {}
            pass
        _headers = self._config['http-header']
        _headers.update(headers)

        # url
        _url = self._config['url']
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