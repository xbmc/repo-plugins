# -*- coding: utf-8 -*-

import urllib
import urlparse
import re
from resources.lib import simple_requests as requests
from .signature.cipher import Cipher

class YT:

    def __init__(self, plugin):
        self.plugin = plugin
        self.SITE = 'youtube'
        self.YT_ADDON = self.plugin.get_setting('yt_addon') == 'true'
        self.API_KEY = 'AIzaSyCky6iU_p2VjvpXwTSOpPVLsGFIdR51lQE'
        self.SEARCH_URL = 'https://www.googleapis.com/youtube/v3/search'
        self.VIDEO_URL = 'https://youtube.com/watch'
        self.HEADERS = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.36 Safari/537.36'
        }

    def get_videos(self, artist):
        json_data = {}
        videos = []
        self.HEADERS['Host'] = 'www.googleapis.com'
        self.HEADERS['Accept-Encoding'] = 'gzip, deflate'
        params = {
            'part': 'snippet',
            'type': 'video',
            'maxResults': '50',
            'q': '{0} video'.format(artist),
            'key': self.API_KEY
        }
        json_data = requests.get(self.SEARCH_URL, headers=self.HEADERS, params=params).json()
        items = json_data.get('items', [])
        videos = self.add_videos(videos, items, artist)
        if len(videos) > 1:
            json_data, items = self.get_more_items(json_data, params)
            videos = self.add_videos(videos, items, artist)
        if len(videos) > 3:
            json_data, items = self.get_more_items(json_data, params)
            videos = self.add_videos(videos, items, artist)
        return videos

    def add_videos(self, videos, items, artist):
        for item in items:
            id_ = item['id']['videoId']
            snippet = item['snippet']
            t = self.plugin.utfenc(snippet['title'])
            spl = self.split_title(t)
            if len(spl) > 1:
                name = self.plugin.utfdec(spl[0].strip())
                title = self.plugin.utfdec(spl[1].strip())
                if len(spl) > 2:
                    title = '{0} - {1}'.format(self.plugin.utfenc(title), self.plugin.utfenc(spl[2].strip()))
                description = self.plugin.utfenc(snippet['description'].lower())
                channel = self.plugin.utfenc(snippet['channelTitle'].lower().replace(' ',''))
                name = self.check_name(artist, name)
                name_2 = self.check_name(artist, title)
                if artist.lower() == self.plugin.utfenc(name).lower() or artist.lower() == self.plugin.utfenc(name_2).lower():
                    if artist.lower() == self.plugin.utfenc(name_2).lower():
                        title = name
                    if self.status(channel, artist, title, description):
                        image = snippet.get('thumbnails', {}).get('medium', {}).get('url', '')
                        title = self.clean_title(title)
                        videos.append(
                            {
                                'site': self.SITE,
                                'artist': self.plugin.utfenc(name),
                                'title': self.plugin.utfenc(title),
                                'id': id_,
                                'thumb': image
                            }
                        )
        return videos

    def get_more_items(self, json_data, params):
        items = []
        json_data2 = {}
        npt = json_data['nextPageToken']
        if npt:
            params['pageToken'] = npt
            json_data2 = requests.get(self.SEARCH_URL, headers=self.HEADERS, params=params).json()
            items = json_data2['items']
        return json_data2, items

    def get_video_url(self, id_):
        if self.YT_ADDON:
            return 'plugin://plugin.video.youtube/play/?video_id=' + id_
        video_url = None
        self.HEADERS['Host'] = 'www.youtube.com'
        self.HEADERS['Referer'] = 'https://www.youtube.com'
        params = {
            'v': id_
        }
        html = ''
        cookie = ''
        html = requests.get(self.VIDEO_URL, params=params, headers=self.HEADERS).text
        pos = html.find('<script>var ytplayer')
        if pos >= 0:
            html2 = html[pos:]
            pos = html2.find('</script>')
            if pos:
                html = html2[:pos]
        re_match_js = re.search(r'\"js\"[^:]*:[^"]*\"(?P<js>.+?)\"', html)
        js = ''
        cipher = None
        if re_match_js:
            js = re_match_js.group('js').replace('\\', '').strip('//')
            if not js.startswith('http'):
                js = 'http://www.youtube.com/{0}'.format(js)
            cipher = Cipher(java_script_url=js)

        re_match = re.search(r'\"url_encoded_fmt_stream_map\"\s*:\s*\"(?P<url_encoded_fmt_stream_map>[^"]*)\"', html)
        if re_match:
            url_encoded_fmt_stream_map = re_match.group('url_encoded_fmt_stream_map')
            url_encoded_fmt_stream_map = url_encoded_fmt_stream_map.split(',')
            for value in url_encoded_fmt_stream_map:
                value = value.replace('\\u0026', '&')
                attr = dict(urlparse.parse_qsl(value))
                url = attr.get('url', None)
                if url:
                    url = urllib.unquote(attr['url'])
                    if 'signature' in url:
                        video_url = url
                        break
                    signature = ''
                    if attr.get('s', ''):
                        signature = cipher.get_signature(attr['s'])
                    elif attr.get('sig', ''):
                        signature = attr.get('sig', '')
                    if signature:
                        url += '&signature=%s' % signature
                        video_url = url
                        break
        return video_url

    def status(self, channel, artist, title, description):
        title = self.plugin.utfenc(title.lower())
        artist = self.plugin.utfenc(artist.lower().replace(' ',''))
        channel = self.plugin.utfenc(channel.lower())
        description = self.plugin.utfenc(description.lower())
        a = ['lyric', 'no official', 'not official', 'unofficial', 'un-official', 'non-official', 'vevo',
             'cover by', 'hq remake', 'remake by'
        ]
        if any(x in title for x in a) and not 'lyric video' in title:
            return False
        b = [
            'parody', 'parodie', 'fan made', 'fan-made', 'fanmade', 'fan mv', 'fan edit', 'vocal cover',
            'dance cover', 'dance practice', 'practice video', 'guide video',
            'custom video', 'music video cover', 'music video montage', 'video preview',
            'guitar cover', 'drum through', 'guitar walk', 'drum walk', 'drum video', 'drum solo',
            'guitar demo', '(drums)', 'drum cam', 'drumcam', '(guitar)',
            'our cover of', 'in this episode of', 'official comment', 'short video about', '(short)',
            'short ver', 'full set', 'full album stream', 'hour version',
            '"reaction"', 'reaction!', 'video reaction', 'video - reaction', 'video) react', 'reaction video',
            'v reaction', '[reaction]', '| reaction', ') reaction', '] reaction', '#reaction',
            'reaction/review', '(review)', '(preview)',
            'splash news', 'not an official', 'music video awards'
        ]
        if any(x in title for x in b) or any(x in description for x in b):
            return False
        c = [' animated ', 'i don\'t own', 'i do not own', 'preview of', 'podcast',
             'no official', 'not official', 'unofficial', 'un-official', 'non-official',
             'live from', 'original video'
        ]
        if any(x in description for x in c):
            return False
        j = ['tmz']
        if any(channel == x for x in j):
            return False
        e = ['official video', 'taken from', 'itunes.apple.com', 'itunes.com', 'smarturl.it', 'j.mp']
        if any(x in description for x in e):
            return True
        f = ['official video', 'official music video', 'offizielles video', 'official lyric video', 'us version']
        if any(x in title for x in f) and description:
            return True
        g = ['records', 'official']
        if any(x in channel for x in g):
            return True
        h = ['vevo']
        if any(channel.endswith(x) for x in h):
            return True
        return False

    def split_title(self, t):
        if t.startswith('[') and '「' in t:
            t = re.sub('\[\w{2}\]|\[official.+\]', '', t, flags=re.I) + ' official music video'
        elif t.startswith('【') and ' - ' in t:
            t = re.sub('\【\w{2}\】|\【official.+\】', '', t, flags=re.I) + ' official music video'
        t = t.replace('「','"').replace('」','"')
        t = t.replace('–', '-')
        if not '-' in t and '"' in t:
            t = re.sub('"', ' - ', t, 1)
        if not '-' in t and ' / ' in t:
            t = re.sub(' / ', ' - ', t)
        if not '-' in t and ':' in t:
            t = re.sub(':', ' - ', t, 1)
        if re.search(' - ', t):
            return t.split(' - ')
        elif re.search(' -', t):
            return t.split(' -')
        elif re.search('- ', t):
            return t.split('- ')
        else:
            return t.split('-')

    def clean_title(self, title):
        if '|' in title:
            title = title.split('|')[0]
        if not re.findall('\(.+?-.+?\)', title) and ' - ' in title:
            title = title.split(' - ')[0]
        return title

    def check_name(self, artist, name):
        if not artist.lower() == self.plugin.utfenc(name).lower():
            split_tags = [',','&','(feat','feat','ft']
            for tag in split_tags:
                if tag in name:
                    splitted = name.split(tag)
                    if len(splitted) > 1:
                        name = splitted[0].strip()
                        break
        return name
