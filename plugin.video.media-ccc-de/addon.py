from __future__ import print_function

import operator

import routing
from xbmcgui import ListItem
from xbmcplugin import addDirectoryItem, endOfDirectory, setResolvedUrl, getSetting, setContent

import resources.lib.http as http
from resources.lib.helpers import maybe_json, calc_aspect, json_date_to_info

plugin = routing.Plugin()

QUALITY = ["sd", "hd"]
FORMATS = ["mp4", "webm"]


@plugin.route('/')
@plugin.route('/dir/<path:subdir>')
def show_dir(subdir=''):
    try:
        data = get_index_data()
    except http.FetchError:
        return

    subdirs = set()
    if subdir == '':
        depth = 0

        addDirectoryItem(plugin.handle, plugin.url_for(show_live),
                         ListItem('Live Streaming'), True)
    else:
        depth = len(subdir.split('/'))

    for event in sorted(data, key=operator.itemgetter('title')):
        top, down, children = split_pathname(event['slug'], depth)

        if top != subdir or down in subdirs:
            continue
        if children:
            addDirectoryItem(plugin.handle, plugin.url_for(show_dir,
                             subdir=build_path(top, down)),
                             ListItem(down.title()), True)
            subdirs.add(down)
        else:
            item = ListItem(event['title'])
            item.setLabel2(event['acronym'])
            item.setArt({'thumb': event['logo_url']})
            url = plugin.url_for(show_conference,
                                 conf=event['url'].rsplit('/', 1)[1])
            addDirectoryItem(plugin.handle, url, item, True)

    endOfDirectory(plugin.handle)


@plugin.route('/conference/<conf>')
def show_conference(conf):
    data = None
    try:
        data = http.fetch_data('conferences/' + conf)
    except http.FetchError:
        return

    setContent(plugin.handle, 'movies')

    aspect = calc_aspect(maybe_json(data, 'aspect_ratio', '16:9'))

    for event in sorted(data['events'], key=operator.itemgetter('title')):
        item = ListItem(event['title'])
        item.setArt({'thumb': event['thumb_url']})
        item.setProperty('IsPlayable', 'true')

        info = {
            'cast': maybe_json(event, 'persons', []),
            'credits': ", ".join(maybe_json(event, 'persons', [])),
            'genre': " / ".join(maybe_json(event, 'tags', [])),
            'plot': maybe_json(event, 'description', ''),
            'tagline': maybe_json(event, 'subtitle', '')
        }
        json_date_to_info(event, 'date', info)
        item.setInfo('video', info)

        streamInfo = {}
        length = maybe_json(event, 'length', 0)
        if length > 0:
            streamInfo['duration'] = length
        if aspect:
            streamInfo['aspect'] = aspect
        item.addStreamInfo('video', streamInfo)

        url = plugin.url_for(resolve_event,
                             event=event['url'].rsplit('/', 1)[1])
        addDirectoryItem(plugin.handle, url, item, False)
    endOfDirectory(plugin.handle)


@plugin.route('/event/<event>')
@plugin.route('/event/<event>/<quality>/<format>')
def resolve_event(event, quality=None, format=None):
    if quality not in QUALITY:
        quality = get_set_quality()
    if format not in FORMATS:
        format = get_set_format()

    data = None
    try:
        data = http.fetch_recordings(event)
    except http.FetchError:
        return
    want = data.recordings_sorted(quality, format)

    if len(want) > 0:
        http.count_view(event, want[0].url)
        setResolvedUrl(plugin.handle, True, ListItem(path=want[0].url))


@plugin.route('/live')
def show_live():
    quality = get_set_quality()
    format = get_set_format()

    data = None
    try:
        data = http.fetch_live(wants_insecure())
    except http.FetchError:
        return

    if len(data.conferences) == 0:
        entry = ListItem('No live event currently, go watch some recordings!')
        addDirectoryItem(plugin.handle, plugin.url_for(show_dir), entry, True)

    for conference in data.conferences:
        for room in conference.rooms:
            want = room.streams_sorted(quality, format)

            try:
                first_native = next(x for x in want if x.translated is False)
                item = ListItem(conference.name + ': ' + room.display)
                item.setProperty('IsPlayable', 'true')
                addDirectoryItem(plugin.handle, first_native.url, item, False)
            except StopIteration:
                pass

            try:
                first_trans = next(x for x in want if x.translated is True)
                item = ListItem(conference.name + ': ' + room.display + ' (Translated)')
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


def wants_insecure():
    return getSetting(plugin.handle, 'insecure') == 'true'


if __name__ == '__main__':
    plugin.run()
