# -*- coding: utf-8 -*-
from datetime import datetime
import itertools
import requests
from xbmcswift2 import Plugin

plugin = Plugin()

STRINGS = {
    'Sveriges_Radio': 30000,
    'unable_to_communicate': 30010,
    'unable_to_parse': 30011,
    'no_stream_found': 30012,
    'live': 30013,
    'channels': 30014,
    'categories': 30015,
    'all_programs': 30016
}


def _(string_id):
    return plugin.get_string(STRINGS[string_id])


def show_error(error):
    dialog = xbmcgui.Dialog()
    ok = dialog.ok(_('Sveriges_Radio'), error)


def load_url(url, params=None, headers=None):
    try:
        r = requests.get(url, headers=headers, params=params)
        r.raise_for_status()
        return r
    except Exception, e:
        plugin.log.error("plugin.audio.sverigesradio: unable to load url: '%s' due to '%s'" % (url, e))
        show_error(_('unable_to_communicate'))
        return None


def load_json(url, params):
    try:
        headers = {'Accept': 'application/json', 'Accept-Charset': 'utf-8'}
        r = load_url(url, params, headers)
        if r:
            return r.json()
    except Exception, e:
        plugin.log.error("plugin.audio.sverigesradio: unable to parse result from url: '%s' due to '%s'" % (url, e))
        show_error(_('unable_to_parse'))
        return None


@plugin.cached()
def load_channels():
    SRAPI_CHANNEL_URL = "http://api.sr.se/api/v2/channels"
    params = {'format': 'json', 'pagination': 'false'}
    channels = load_json(SRAPI_CHANNEL_URL, params)
    return channels


@plugin.cached(TTL=60 * 6)
def load_programs(channel_id='', category_id=''):
    SRAPI_PROGRAM_URL = "http://api.sr.se/api/v2/programs/index"
    params = {'format': 'json', 'pagination': 'false', 'filter': 'program.hasondemand', 'filterValue': 'true'}
    if channel_id:
        params['channelid'] = channel_id
    if category_id:
        params['programcategoryid'] = category_id
    programs = load_json(SRAPI_PROGRAM_URL, params)
    return programs


@plugin.cached(TTL=60 * 6)
def load_program_episodes(program_id, quality):
    SRAPI_EPISODE_URL = "http://api.sr.se/api/v2/episodes"
    params = {'format': 'json', 'pagination': 'false', 'audioquality': quality, 'programid': program_id}
    episodes = load_json(SRAPI_EPISODE_URL, params)
    return episodes


@plugin.cached()
def load_program_info(program_id):
    SRAPI_PROGRAM_URL = "http://api.sr.se/api/v2/programs/{0}"
    params = {'format': 'json', 'pagination': 'false'}
    url = SRAPI_PROGRAM_URL.format(program_id)
    program_info = load_json(url, params)
    return program_info


@plugin.cached()
def load_categories():
    SRAPI_PROGRAM_CATEGORIES = "http://api.sr.se/api/v2/programcategories"
    params = {'format': 'json', 'pagination': 'false'}
    categories = load_json(SRAPI_PROGRAM_CATEGORIES, params)
    return categories


def create_live_channel(channel):
    name = channel['name']
    url = channel['liveaudio']['url']
    logo = channel['image']
    item = {'label': name, 'path': url, 'icon': logo, 'is_playable': True}
    return item


def create_channel(channel):
    name = channel['name']
    logo = channel['image']
    id = channel['id']
    item = {'label': name, 'path': plugin.url_for('list_channel_programs', id=id), 'icon': logo, 'is_playable': False}
    return item


def create_program(program):
    name = program['name']
    logo = program['programimage']
    id = program['id']
    item = {'label': name, 'path': plugin.url_for('list_program', id=id), 'icon': logo, 'is_playable': False}
    return item


def create_category(category):
    name = category['name']
    id = category['id']
    item = {'label': name, 'path': plugin.url_for('list_category', id=id), 'is_playable': False}
    return item


def create_broadcast(episode, program_name, prefer_broadcasts):
    name = episode['title']
    logo = episode['imageurl']
    description = episode['description']
    name = "%s - %s" % (name, description)
    items = []
    if prefer_broadcasts and 'broadcast' in episode:
        extract_broadcasts(items, episode['broadcast'], logo, name, program_name)
    elif 'listenpodfile' in episode:
        extract_pod_file(items, episode['listenpodfile'], logo, name, program_name)
    elif 'downloadpodfile' in episode:
        extract_pod_file(items, episode['downloadpodfile'], logo, name, program_name)
    elif not prefer_broadcasts and 'broadcast' in episode:
        extract_broadcasts(items, episode['broadcast'], logo, name, program_name)
    return items


def extract_pod_file(items, pod_info, logo, name, program_name):
    url = pod_info['url']
    date_str = pod_info['publishdateutc']
    date_object = datetime.fromtimestamp(float(int(date_str[6:-2]) / 1000)).date()
    date_strftime = date_object.strftime("%d.%m.%Y")
    duration = pod_info['duration']
    size = pod_info['filesizeinbytes']
    info = {'duration': duration, 'date': date_strftime, 'title': name, 'size': size, 'album': program_name,
            'artist': _('Sveriges_Radio')}
    item = {'label': name, 'path': url, 'icon': logo, 'is_playable': True, 'info': info}
    items.append(item)


def extract_broadcasts(items, broadcast, logo, name, program_name):
    for file in broadcast['broadcastfiles']:
        url = file['url']
        date_str = file['publishdateutc']
        date_object = datetime.fromtimestamp(float(int(date_str[6:-2]) / 1000)).date()
        date_strftime = date_object.strftime("%d.%m.%Y")
        duration = file['duration']
        info = {'duration': duration, 'date': date_strftime, 'title': name, 'album': program_name,
                'artist': _('Sveriges_Radio')}
        item = {'label': name, 'path': url, 'icon': logo, 'is_playable': True, 'info': info}
        items.append(item)


@plugin.route('/channel/<id>')
def list_channel_programs(id):
    response = load_programs(channel_id=id)
    if response:
        items = [create_program(program) for program in response['programs']]
        plugin.add_sort_method('playlist_order')
        plugin.add_sort_method('label')
        return items


@plugin.route('/program/<id>')
def list_program(id):
    QUALITIES = ["lo", "normal", "hi"]
    quality = plugin.get_setting('quality', choices=QUALITIES)
    response = load_program_episodes(id, quality)
    program_info = load_program_info(id)
    program_name = program_info["program"]["name"]
    if response:
        PREFERENCE_CHOICES = [True, False]
        prefer_broadcasts = plugin.get_setting('preference', choices=PREFERENCE_CHOICES)
        items = [create_broadcast(episode, program_name, prefer_broadcasts) for episode in response['episodes']]
        items = list(itertools.chain(*items))
        plugin.add_sort_method('playlist_order')
        plugin.add_sort_method('label')
        plugin.add_sort_method('date')
        return items


@plugin.route('/category/<id>')
def list_category(id):
    response = load_programs(category_id=id)
    if response:
        items = [create_program(program) for program in response['programs']]
        plugin.add_sort_method('playlist_order')
        plugin.add_sort_method('label')
        return items


@plugin.route('/live/')
def list_live():
    response = load_channels()
    if response:
        items = [create_live_channel(channel) for channel in response['channels']]
        plugin.add_sort_method('playlist_order')
        plugin.add_sort_method('label')
        return items


@plugin.route('/channels/')
def list_channels():
    response = load_channels()
    if response:
        items = [create_channel(channel) for channel in response['channels']]
        plugin.add_sort_method('playlist_order')
        plugin.add_sort_method('label')
        return items


@plugin.route('/categories/')
def list_categories():
    response = load_categories()
    if response:
        items = [create_category(category) for category in response['programcategories']]
        plugin.add_sort_method('playlist_order')
        plugin.add_sort_method('label')
        return items


@plugin.route('/allprograms/')
def list_all_programs():
    response = load_programs()
    if response:
        items = [create_program(program) for program in response['programs']]
        plugin.add_sort_method('label')
        return items


@plugin.route('/')
def index():
    items = [
        {'label': _('live'), 'path': plugin.url_for('list_live')},
        {'label': _('channels'), 'path': plugin.url_for('list_channels')},
        {'label': _('categories'), 'path': plugin.url_for('list_categories')},
        {'label': _('all_programs'), 'path': plugin.url_for('list_all_programs')},
    ]
    return items


if __name__ == '__main__':
    plugin.run()
