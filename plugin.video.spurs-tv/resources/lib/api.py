import re
import json
from collections import namedtuple

import requests


VIDEO_DATA_RE = (
    r"React\.createElement\(Components\.TrendingGridModule, (.*?)\)"
    r", document.getElementById\("
)

URL_FMT = "https://www.tottenhamhotspur.com/{}/loadmore"

Video = namedtuple('Video', 'entry_id title caption thumbnail')


def image_url(path, height=720):
    return 'https://tot-tmp.azureedge.net/media/{0}?height={1}'.format(path, height)


def search_results(term, max_results=10):
    page = 1
    num_results = 0
    while num_results < max_results:
        data = requests.get(URL_FMT.format('searchpage'), dict(searchTerm=term, page=page)).json()
        search_result_data = data['searchResults']
        if search_result_data['loadMoreLink'] is None:
            break
        for item in _media_items(search_result_data['results']):
            num_results += 1
            if num_results <= max_results:
                yield item
        page += 1
        print(page)


def videos(tag_id, page=1, items=100):
    response = requests.get(
        URL_FMT.format('trendinggrid'),
        dict(tagIds=tag_id, fromPage=page-1, toPage=page, itemsPerGrid=items)
    ).text
    data = json.loads(re.search(VIDEO_DATA_RE, response,
                                re.DOTALL).group(1))['data']
    end = data['loadMoreLink'] is None

    items = (item['data']['article'] for item in data['modules'])
    return _media_items(items), end


def _media_items(items):
    for item in items:
        video_data = item['media']

        if video_data is not None:
            yield Video(
                entry_id=video_data['entryId'],
                title=item['title'],
                caption=video_data['caption'],
                thumbnail=_thumbnail(video_data)
            )


def _thumbnail(video_data):
    for key in ['thumbnail', 'image']:
        try:
            return video_data.get(key) and video_data[key]['smallUrl']
        except KeyError:
            continue
