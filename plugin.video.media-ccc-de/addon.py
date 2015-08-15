from __future__ import print_function

import operator
import requests

from xbmcswift2 import Plugin

from resources.lib.helpers import recording_list
from resources.lib.stream import Streams

BASE_URL = 'https://api.media.ccc.de/public/'
LIVE_URL = 'http://streaming.media.ccc.de/streams/v1.json'

#BASE_URL = 'http://127.0.0.1:3000/public/'
#LIVE_URL = 'http://127.0.0.1:3000/v1.json'

plugin = Plugin()

QUALITY = ["sd", "hd"]
FORMATS = ["mp4", "webm"]

@plugin.route('/', name='index')
@plugin.route('/dir/<subdir>')
def show_dir(subdir = ''):
    data = get_index_data()
    items = []
    subdirs = set()
    if subdir == '':
        depth = 0
    else:
        depth = len(subdir.split('/'))


    for event in data:
        top, down, children = split_pathname(event['webgen_location'], depth)

        if top != subdir or down in subdirs:
            continue
        if children:
            items.append({
                'label': down.title(),
                'path': plugin.url_for('show_dir', subdir = build_path(top, down))
            })
            subdirs.add(down)
        else:
            items.append({
                'label': event['title'],
                'label2': event['acronym'],
                'thumbnail': event['logo_url'],
                'path': plugin.url_for('show_conference', conf = event['url'].rsplit('/', 1)[1])
            })

    items.sort(key=operator.itemgetter('label'))

    if depth == 0:
        items.insert(0, {
            'label': 'Live Streaming',
            'path': plugin.url_for('show_live')
        })

    return items

@plugin.route('/conference/<conf>')
def show_conference(conf):
    req = requests.get(BASE_URL + 'conferences/' + conf)
    data = req.json()['events']
    items = []
    for event in data:
        items.append({
            'label': event['title'],
            'thumbnail': event['thumb_url'],
            'info': {
                'cast': event['persons'],
                'plot': event['description'],
                'tagline': event['subtitle']
            },
            'stream_info': {
                'video': {
                    'duration': event['length']
                },
            },
            'path': plugin.url_for('resolve_event_default', event = event['url'].rsplit('/', 1)[1]),
            'is_playable': True
            })
    return sorted(items, key=operator.itemgetter('label'))

@plugin.route('/event/<event>', name = 'resolve_event_default')
@plugin.route('/event/<event>/<quality>/<format>')
def resolve_event(event, quality = None, format = None):
    if quality not in QUALITY:
        quality = QUALITY[plugin.get_setting('quality', int)]
    if format not in FORMATS:
        format = FORMATS[plugin.get_setting('format', int)]

    req = requests.get(BASE_URL + 'events/' + event)
    want = recording_list(req.json()['recordings'], quality, format)

    if len(want) > 0:
        requests.post(BASE_URL + 'recordings/count', data = {'event_id': event, 'src': want[0].url})
        plugin.set_resolved_url(want[0].url)

@plugin.route('/live')
def show_live():
    quality = QUALITY[plugin.get_setting('quality', int)]
    format = FORMATS[plugin.get_setting('format', int)]

    req = requests.get(LIVE_URL)
    data = Streams(req.json())

    if len(data.rooms) == 0:
        return [{
            'label': 'No live event currently, go watch some recordings!',
            'path': plugin.url_for('index')
        }]

    items = []
    for room in data.rooms:
        want = room.streams_sorted(quality, format)

        try:
            item = next(x for x in want if x.translated == False)
            items.append({
                'label': room.display,
                'is_playable': True,
                'path': item.url
            })
        except StopIteration:
            pass

        try:
            item = next(x for x in want if x.translated == True)
            items.append({
                'label': room.display + ' (Translated)',
                'is_playable': True,
                'path': item.url
            })
        except StopIteration:
            pass

    return items


@plugin.cached()
def get_index_data():
    req = requests.get(BASE_URL + 'conferences')
    return req.json()['conferences']

def split_pathname(name, depth):
    path = name.split('/')
    top = '/'.join(path[0:depth])
    if depth < len(path):
        down = path[depth]
    else:
        down = None
    children = len(path)-1 > depth
    return (top, down, children)

def build_path(top, down):
    if top == '':
        return down
    else:
        return '/'.join((top, down))

if __name__ == '__main__':
    plugin.run()
