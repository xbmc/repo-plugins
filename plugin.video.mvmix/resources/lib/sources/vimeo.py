# -*- coding: utf-8 -*-

from resources.lib import simple_requests as requests

class VIMEO:

    def __init__(self, plugin):
        self.plugin = plugin
        self.SITE = 'vimeo'
        self.VIDEO_URL = 'https://player.vimeo.com/video/{0}/config'
        self.HEADERS = {
            'X-Requested-With': 'XMLHttpRequest'
        }

    def get_video_url(self, id_):
        video_url = None
        height = 0
        json_data = requests.get(self.VIDEO_URL.format(str(id_)), headers=self.HEADERS).json()
        for q in json_data['request']['files']['progressive']:
            if height < q['height']:
                height = q['height']
                video_url = q['url']
                if height == 720:
                    break
        return video_url
