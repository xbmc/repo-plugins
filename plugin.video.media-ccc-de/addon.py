from __future__ import print_function

import operator
import requests

from xbmcswift2 import Plugin

BASE_URL = 'http://api.media.ccc.de/public/'
#BASE_URL = 'http://127.0.0.1:3000/public/'

plugin = Plugin()


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

    return sorted(items, key=operator.itemgetter('label'))

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
                'duration': str_length(event['length']),
                'cast': event['persons'],
                'plot': event['description'],
                'tagline': event['subtitle']
                },
                'path': plugin.url_for('resolve_event', event = event['url'].rsplit('/', 1)[1]),
            'is_playable': True
            })
    return sorted(items, key=operator.itemgetter('label'))

@plugin.route('/event/<event>')
def resolve_event(event):
    req = requests.get(BASE_URL + 'events/' + event)
    recs = req.json()['recordings']
    want = sorted(filter(is_video, recs), key=format_priority)
    if len(want) > 0:
        plugin.set_resolved_url(want[0]['recording_url'])

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

def is_video(entry):
    return entry['mime_type'].startswith('video/')

def format_priority(entry):
    enc = entry['mime_type'].split('/')[1]
    if enc == 'mp4':
        return 1 # Can be hardware-accelerated
    elif enc == 'webm':
        return 2
    else:
        return 99

def str_length(length):
    mins, secs = divmod(length, 60)
    return '%0i:%02i' % (mins, secs)

if __name__ == '__main__':
    plugin.run()
