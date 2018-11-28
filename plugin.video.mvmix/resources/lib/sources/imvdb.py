# -*- coding: utf-8 -*-

import urllib
from resources.lib import simple_requests as requests
from .vimeo import VIMEO
from .youtube import YT

class IMVDB:

    def __init__(self, plugin):
        self.plugin = plugin
        self.SITE = 'imvdb'
        self.SEARCH_URL = 'https://imvdb.com/api/v1/search/videos'
        self.VIDEO_URL = 'http://imvdb.com/api/v1/video/{0}'
        self.HEADERS = {
            'IMVDB-APP-KEY': 'hjyG4SOzr73y6Prb95G1jeeIG1z5HwkYQTFULuud'
        }

    def get_videos(self, artist):
        json_data = {}
        videos = []
        params = {
            'q': urllib.quote_plus(artist),
            'per_page': '100',
            'page':'1'
        }
        json_data = requests.get(self.SEARCH_URL, headers=self.HEADERS, params=params).json()
        results = json_data.get('results', [])
        for v in results:
            name = self.plugin.tostr(v['artists'][0]['name'])
            if self.plugin.utfenc(name).lower() == artist.lower():
                id_ = v['id']
                title = self.plugin.tostr(v['song_title'])
                image = urllib.quote(self.plugin.utfenc(v['image']['o']), safe='%/:=&?~#+!$,;\'@()*[]')
                videos.append(
                    {
                        'site': self.SITE,
                        'artist': self.plugin.utfenc(artist),
                        'title': self.plugin.utfenc(title),
                        'id': str(id_),
                        'thumb': image
                    }
                )
        return videos

    def get_video_url(self, id_):
        video_url = None
        params = {
            'include': 'sources'
        }
        json_data = requests.get(self.VIDEO_URL.format(id_), headers=self.HEADERS, params=params).json()
        sources = json_data.get('sources', [])
        for q in sources:
            if q['source'] == 'vimeo':
                video_url = VIMEO(self.plugin).get_video_url(q['source_data'])
            elif q['source'] == 'youtube':
                video_url = YT(self.plugin).get_video_url(q['source_data'])
            if video_url:
                break
        return video_url
