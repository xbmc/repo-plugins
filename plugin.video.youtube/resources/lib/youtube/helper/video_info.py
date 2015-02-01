__author__ = 'bromix'

import urllib
import urlparse
import re

from resources.lib.kodion import simple_requests as requests
from ..youtube_exceptions import YouTubeException
from .signature.cipher import Cipher


class VideoInfo(object):
    DEFAULT_ITAG_MAP = {'5': {'format': 'FLV', 'width': 320, 'height': 240},
                        '17': {'format': '3GP', 'width': 176, 'height': 144},
                        '18': {'format': 'MP4', 'width': 480, 'height': 360},
                        '22': {'format': 'MP4', 'width': 1280, 'height': 720},
                        '34': {'format': 'FLV', 'width': 480, 'height': 360},
                        '35': {'format': 'FLV', 'width': 640, 'height': 480},
                        '36': {'format': '3GP', 'width': 320, 'height': 240},
                        '37': {'format': 'MP4', 'width': 1920, 'height': 1080},
                        '38': {'format': 'MP4', 'width': 2048, 'height': 1080},
                        '43': {'format': 'WEB', 'width': 480, 'height': 360},
                        '44': {'format': 'WEB', 'width': 640, 'height': 480},
                        '45': {'format': 'WEB', 'width': 1280, 'height': 720},
                        '46': {'format': 'WEB', 'width': 1920, 'height': 1080},
                        '82': {'format': 'MP4', 'width': 480, 'height': 360, '3D': True},
                        '83': {'format': 'MP4', 'width': 640, 'height': 480, '3D': True},
                        '84': {'format': 'MP4', 'width': 1280, 'height': 720, '3D': True},
                        '85': {'format': 'MP4', 'width': 1920, 'height': 1080, '3D': True},
                        '100': {'format': 'WEB', 'width': 480, 'height': 360, '3D': True},
                        '101': {'format': 'WEB', 'width': 640, 'height': 480, '3D': True},
                        '102': {'format': 'WEB', 'width': 1280, 'height': 720, '3D': True},
                        '133': {'format': 'MP4', 'width': 320, 'height': 240, 'VO': True},
                        '134': {'format': 'MP4', 'width': 480, 'height': 360, 'VO': True},
                        '135': {'format': 'MP4', 'width': 640, 'height': 480, 'VO': True},
                        '136': {'format': 'MP4', 'width': 1280, 'height': 720, 'VO': True},
                        '137': {'format': 'MP4', 'width': 1920, 'height': 1080, 'fps': 30},
                        '140': {'format': 'audio/mp4'},
                        '160': {'format': 'MP4', 'width': 256, 'height': 144, 'VO': True},
                        '171': {'format': 'audio/webm'},
                        '242': {'format': 'WEB', 'width': 320, 'height': 240, 'VOX': True},
                        '243': {'format': 'WEB', 'width': 480, 'height': 360, 'VOX': True},
                        '244': {'format': 'WEB', 'width': 640, 'height': 480, 'VOX': True},
                        '245': {'format': 'WEB', 'width': 640, 'height': 480, 'VOX': True},
                        '246': {'format': 'WEB', 'width': 640, 'height': 480, 'VOX': True},
                        '247': {'format': 'WEB', 'width': 1280, 'height': 720, 'VOX': True},
                        '248': {'format': 'WEB', 'width': 1920, 'height': 1080, 'VOX': True},
                        '264': {'format': 'MP4', 'width': 1920, 'height': 1080, 'VOX': True},
                        '298': {'format': 'video/mp4; codecs="avc1.4d4020', 'width': 1280, 'height': 720, 'fps': 60},
                        '299': {'format': 'video/mp4; codecs="avc1.64002a', 'width': 1920, 'height': 1080, 'fps': 60},
                        '302': {'format': 'video/webm; codecs="vp9', 'width': 1280, 'height': 720, 'fps': 60},
                        '303': {'format': 'video/webm; codecs="vp9', 'width': 1920, 'height': 1080, 'fps': 60}}

    def __init__(self, context, access_token='', language='en-US'):
        self._context = context
        self._language = language.replace('-', '_')
        self._access_token = access_token
        pass

    def load_stream_infos(self, video_id):
        return self._method_get_video_info(video_id)

    def _method_watch(self, video_id, reason=u''):
        stream_list = []

        headers = {'Host': 'www.youtube.com',
                   'Connection': 'keep-alive',
                   'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.36 Safari/537.36',
                   'Accept': '*/*',
                   'DNT': '1',
                   'Referer': 'https://www.youtube.com',
                   'Accept-Encoding': 'gzip, deflate',
                   'Accept-Language': 'en-US,en;q=0.8,de;q=0.6'}

        params = {'v': video_id}

        url = 'https://www.youtube.com/watch'

        result = requests.get(url, params=params, headers=headers, verify=False, allow_redirects=True)
        html = result.text

        """
        This will almost double the speed for the regular expressions, because we only must match
        a small portion of the whole html. And only if we find positions, we cut down the html.

        """
        pos = html.find('ytplayer.config')
        if pos:
            html2 = html[pos:]
            pos = html2.find('</script>')
            if pos:
                html = html2[:pos]
                pass
            pass

        itag_map = {}
        itag_map.update(self.DEFAULT_ITAG_MAP)
        re_match = re.match('.+\"fmt_list\": \"(?P<fmt_list>.+?)\".+', html)
        if re_match:
            fmt_list = re_match.group('fmt_list')
            fmt_list = fmt_list.split(',')

            for value in fmt_list:
                value = value.replace('\/', '|')

                try:
                    attr = value.split('|')
                    sizes = attr[1].split('x')
                    itag_map[attr[0]] = {'width': int(sizes[0]),
                                         'height': int(sizes[1])}
                except:
                    # do nothing
                    pass
                pass
            pass

        re_match = re.search(r'\"js\"[^:]*:[^"]*\"(?P<js>.+?)\"', html)
        js = ''
        cipher = None
        if re_match:
            js = re_match.group('js').replace('\\', '').strip('//')
            cipher = Cipher(self._context, java_script_url=js)
            pass

        re_match = re.search(r'\"url_encoded_fmt_stream_map\"[^:]*:[^"]*\"(?P<url_encoded_fmt_stream_map>[^"]*\")', html)
        if re_match:
            url_encoded_fmt_stream_map = re_match.group('url_encoded_fmt_stream_map')
            url_encoded_fmt_stream_map = url_encoded_fmt_stream_map.split(',')

            for value in url_encoded_fmt_stream_map:
                value = value.replace('\\u0026', '&')
                attr = dict(urlparse.parse_qsl(value))

                try:
                    url = urllib.unquote(attr['url'])

                    signature = ''
                    if attr.get('s', ''):
                        signature = cipher.get_signature(attr['s'])
                        pass
                    elif attr.get('sig', ''):
                        signature = attr.get('sig', '')
                        pass

                    if signature:
                        url += '&signature=%s' % signature
                        pass

                    video_stream = {'url': url,
                                    'format': itag_map[attr['itag']]}

                    stream_list.append(video_stream)
                except Exception, ex:
                    x=0
                    pass
                pass
            pass

        # this is a reason from get_video_info. We should at least display the reason why the video couldn't be loaded
        if len(stream_list) == 0 and reason:
            raise YouTubeException(reason)

        return stream_list

    def _load_manifest(self, url, video_id):
        headers = {'Host': 'manifest.googlevideo.com',
                   'Connection': 'keep-alive',
                   'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.36 Safari/537.36',
                   'Accept': '*/*',
                   'DNT': '1',
                   'Referer': 'https://www.youtube.com/watch?v=%s' % video_id,
                   'Accept-Encoding': 'gzip, deflate',
                   'Accept-Language': 'en-US,en;q=0.8,de;q=0.6'}
        result = requests.get(url, headers=headers, verify=False, allow_redirects=True)
        lines = result.text.splitlines()
        streams = []
        for i in range(len(lines)):
            re_match = re.search(r'RESOLUTION=(?P<width>\d+)x(?P<height>\d+)', lines[i])
            if re_match:
                line = lines[i+1]
                width = int(re_match.group('width'))
                height = int(re_match.group('height'))
                video_stream = {'url': line,
                                'format': {'width': width, 'height': height}}
                streams.append(video_stream)
                pass
            pass
        return streams

    def _method_get_video_info(self, video_id):
        headers = {'Host': 'www.youtube.com',
                   'Connection': 'keep-alive',
                   'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.36 Safari/537.36',
                   'Accept': '*/*',
                   'DNT': '1',
                   'Referer': 'https://www.youtube.com/tv',
                   'Accept-Encoding': 'gzip, deflate',
                   'Accept-Language': 'en-US,en;q=0.8,de;q=0.6'}
        params = {'video_id': video_id,
                  'hl': self._language}
        if self._access_token:
            params['access_token'] = self._access_token
            pass

        url = 'https://www.youtube.com/get_video_info'

        result = requests.get(url, params=params, headers=headers, verify=False, allow_redirects=True)

        stream_list = []

        data = result.text
        params = dict(urlparse.parse_qsl(data))

        if params.get('status', '') == 'fail':
            return self._method_watch(video_id, reason=params.get('reason', 'UNKNOWN'))

        if params.get('live_playback', '0') == '1':
            url = params.get('hlsvp', '')
            if url:
                return self._load_manifest(url, video_id)
            pass

        itag_map = {}
        itag_map.update(self.DEFAULT_ITAG_MAP)

        # update itag map
        fmt_list = params.get('fmt_list', '')
        if fmt_list:
            fmt_list = fmt_list.split(',')
            for item in fmt_list:
                data = item.split('/')

                size = data[1].split('x')
                itag_map[data[0]] = {'width': int(size[0]),
                                     'height': int(size[1])}
                pass
            pass

        # read adaptive_fmts
        """
        adaptive_fmts = params['adaptive_fmts']
        adaptive_fmts = adaptive_fmts.split(',')
        for item in adaptive_fmts:
            stream_map = dict(urlparse.parse_qsl(item))

            if stream_map['itag'] != '140' and stream_map['itag'] != '171':
                video_stream = {'url': stream_map['url'],
                                'format': itag_map[stream_map['itag']]}
                stream_list.append(video_stream)
                pass
            pass
        """

        # extract streams from map
        url_encoded_fmt_stream_map = params.get('url_encoded_fmt_stream_map', '')
        if url_encoded_fmt_stream_map:
            url_encoded_fmt_stream_map = url_encoded_fmt_stream_map.split(',')
            for item in url_encoded_fmt_stream_map:
                stream_map = dict(urlparse.parse_qsl(item))

                url = stream_map['url']
                if 'sig' in stream_map:
                    url += '&signature=%s' % stream_map['sig']
                elif 's' in stream_map:
                    # fuck!!! in this case we must call the web page
                    return self._method_watch(video_id)

                video_stream = {'url': url,
                                'format': itag_map[stream_map['itag']]}

                stream_list.append(video_stream)
                pass
            pass

        # last fallback
        if not stream_list:
            return self._method_watch(video_id)

        return stream_list

    pass
