# -*- coding: utf-8 -*-
import re
import time
import html.parser
import urllib.request, urllib.error, urllib.parse


class YoutubeStream:
    def get_live_video_info_from_channel_id(self, channel_id):
        request = urllib.request.Request("https://www.youtube.com/c/%s/live" % channel_id)
        video_id, title = self.get_video_info(request)
        livestream_url = "plugin://plugin.video.youtube/play/?video_id=%s" % video_id
        livestream_thumbnail = "https://i.ytimg.com/vi/%s/hqdefault_live.jpg#%s" % (
            video_id, time.localtime())
        return livestream_url, title, livestream_thumbnail

    def get_video_info(self, request):
        response = urllib.request.urlopen(request)
        string_data = response.read()
        lines = string_data.decode('utf-8').splitlines()

        re_video_url = re.compile(r'https://i.ytimg.com/vi/(?P<video_id>[^\/]+)/maxresdefault_live.jpg')
        re_video_title = re.compile(r'<title>(?P<title>[^\?]+) - YouTube</title>')

        re_video_url_match = ""
        re_video_title_match = ""

        for line in lines:
            #xbmc.log(line)
            if not re_video_url_match:
                re_video_url_match = re.search(re_video_url, line)
            if not re_video_title_match:
                re_video_title_match = re.search(re_video_title, line)

            if re_video_url_match and re_video_title_match:
                title = re_video_title_match.group('title')
                return (re_video_url_match.group('video_id'), html.parser.HTMLParser().unescape(title))

