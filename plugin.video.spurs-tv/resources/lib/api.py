import re
import json
from collections import namedtuple

import requests


VIDEO_DATA_RE = (
    r"React\.createElement\(Components\.TrendingGridModule, (.*?)\)"
    r", document.getElementById\("
)

URL = "https://www.tottenhamhotspur.com/trendinggrid/loadmore"

Video = namedtuple('Video', 'entry_id title caption thumbnail')


def videos():
    response = requests.get(URL, dict(tagIds=56552, page=1, itemsPerGrid=1000)).text
    data = re.search(VIDEO_DATA_RE, response, re.DOTALL).group(1)
    modules = json.loads(data)['data']['modules']
    for module in modules:
        article = module['data']['article']
        video_data = article['media']
        if video_data is not None:
            yield Video(
                entry_id=video_data['entryId'],
                title=article['title'],
                caption=video_data['caption'],
                thumbnail=video_data['thumbnail']['smallUrl']
            )
