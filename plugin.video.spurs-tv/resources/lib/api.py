import re
import json
from collections import namedtuple

import requests


VIDEO_DATA_RE = (
    r"React\.createElement\(Components\.TrendingGridModule, (.*?)\)"
    r", document.getElementById\("
)

URL = "https://www.tottenhamhotspur.com/spurs-tv/"

Video = namedtuple('Video', 'entry_id caption thumbnail')


def videos():
    data = re.search(VIDEO_DATA_RE, requests.get(URL).text).group(1)
    videos = json.loads(data)['data']['modules']
    for video in videos:
        video_data = video['data']
        yield Video(video_data['entryId'], video_data['caption'], video_data['thumbnail']['smallUrl'])
