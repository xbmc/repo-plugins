import re
import urllib2

import xbmc


def get_live_video_id_from_channel_id(channel_id):
    request = urllib2.Request("https://www.youtube.com/c/%s/live" % channel_id)
    response = urllib2.urlopen(request)
    string_data = response.read()
    lines = string_data.splitlines()

    re_video_url = re.compile(r'http://www.youtube.com/v/(?P<video_id>[^\?]+)')
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
            return (re_video_url_match.group('video_id'), re_video_title_match.group('title'))
