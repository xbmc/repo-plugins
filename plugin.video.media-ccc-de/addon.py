from __future__ import print_function

import operator

import routing
from xbmcgui import ListItem
from xbmcplugin import addDirectoryItem, endOfDirectory, setResolvedUrl, getSetting

from resources.lib.helpers import recording_list
import resources.lib.http as http

plugin = routing.Plugin()

QUALITY = ["sd", "hd"]
FORMATS = ["mp4", "webm"]

@plugin.route('/')
@plugin.route('/dir/<subdir>')
def show_dir(subdir = ''):
    try:
        data = get_index_data()
    except http.FetchError:
        return

    subdirs = set()
    if subdir == '':
        depth = 0

        addDirectoryItem(plugin.handle, plugin.url_for(show_live), ListItem('Live Streaming'), True)
    else:
        depth = len(subdir.split('/'))


    for event in sorted(data, key=operator.itemgetter('title')):
        top, down, children = split_pathname(event['webgen_location'], depth)

        if top != subdir or down in subdirs:
            continue
        if children:
            addDirectoryItem(plugin.handle, plugin.url_for(show_dir, subdir = build_path(top, down)),
                    ListItem(down.title()), True)
            subdirs.add(down)
        else:
            item = ListItem(event['title'])
            item.setLabel2(event['acronym'])
            item.setThumbnailImage(event['logo_url'])
            addDirectoryItem(plugin.handle, plugin.url_for(show_conference, conf = event['url'].rsplit('/', 1)[1]),
                    item, True)

    endOfDirectory(plugin.handle)


@plugin.route('/conference/<conf>')
def show_conference(conf):
    data = None
    try:
        data = http.fetch_data('conferences/' + conf)['events']
    except http.FetchError:
        return

    for event in sorted(data, key=operator.itemgetter('title')):
        item = ListItem(event['title'])
        item.setThumbnailImage(event['thumb_url'])
        item.setProperty('IsPlayable', 'true')
        item.setInfo('video', {
            'cast': event['persons'],
            'plot': event['description'],
            'tagline': event['subtitle']
        })
        item.addStreamInfo('video', {
            'duration': event['length']
        })

        addDirectoryItem(plugin.handle, plugin.url_for(resolve_event, event = event['url'].rsplit('/', 1)[1]),
                item, False)
    endOfDirectory(plugin.handle)

@plugin.route('/event/<event>')
@plugin.route('/event/<event>/<quality>/<format>')
def resolve_event(event, quality = None, format = None):
    if quality not in QUALITY:
        quality = get_set_quality()
    if format not in FORMATS:
        format = get_set_format()

    data = None
    try:
        data = http.fetch_data('events/' + event)['recordings']
    except http.FetchError:
        return
    want = recording_list(data, quality, format)

    if len(want) > 0:
        http.count_view(event, want[0].url)
        setResolvedUrl(plugin.handle, True, ListItem(path=want[0].url))

@plugin.route('/live')
def show_live():
    quality = get_set_quality()
    format = get_set_format()

    data = None
    try:
        data = http.fetch_live()
    except http.FetchError:
        return

    if len(data.rooms) == 0:
        addDirectoryItem(plugin.handle, plugin.url_for(show_dir),
                ListItem('No live event currently, go watch some recordings!'), True)

    for room in data.rooms:
        want = room.streams_sorted(quality, format)

        try:
            first_native = next(x for x in want if x.translated == False)
            item = ListItem(room.display)
            item.setProperty('IsPlayable', 'true')
            addDirectoryItem(plugin.handle, first_native.url, item, False)
        except StopIteration:
            pass

        try:
            first_trans = next(x for x in want if x.translated == True)
            item = ListItem(room.display + ' (Translated)')
            item.setProperty('IsPlayable', 'true')
            addDirectoryItem(plugin.handle, first_trans.url, item, False)
        except StopIteration:
            pass

    endOfDirectory(plugin.handle)


# FIXME: @plugin.cached()
def get_index_data():
    return http.fetch_data('conferences')['conferences']

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

def get_setting_int(name):
    val = getSetting(plugin.handle, name)
    if not val:
        val = '0'
    return int(val)

def get_set_quality():
    return QUALITY[get_setting_int('quality')]

def get_set_format():
    return FORMATS[get_setting_int('format')]

if __name__ == '__main__':
    plugin.run()
