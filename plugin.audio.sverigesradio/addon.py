# -*- coding: utf-8 -*-
from datetime import datetime
from datetime import timedelta
from datetime import date
from distutils.util import strtobool
import sys
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

QUALITIES = ["lo", "normal", "hi"]
FORMATS = ["mp3", "aac"]


def json_date_as_datetime(jd):
    sign = jd[-7]
    if sign not in '-+' or len(jd) == 13:
        millisecs = int(jd[6:-2])
    else:
        millisecs = int(jd[6:-7])
        hh = int(jd[-7:-4])
        mm = int(jd[-4:-2])
        if sign == '-': mm = -mm
        millisecs += (hh * 60 + mm) * 60000
    return datetime.datetime(1970, 1, 1) + datetime.timedelta(microseconds=millisecs * 1000)


def format_datetime(dt):
    return dt.strftime("%Y-%m-%d %H:%M")


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
    except Exception as e:
        plugin.log.error("plugin.audio.sverigesradio: unable to load url: '%s' due to '%s'" % (url, e))
        show_error(_('unable_to_communicate'))
        return None


def load_json(url, params):
    try:
        headers = {'Accept': 'application/json', 'Accept-Charset': 'utf-8'}
        r = load_url(url, params, headers)
        if r:
            return r.json()
    except Exception as e:
        plugin.log.error("plugin.audio.sverigesradio: unable to parse result from url: '%s' due to '%s'" % (url, e))
        show_error(_('unable_to_parse'))
        return None


def load_channels():
    SRAPI_CHANNEL_URL = "http://api.sr.se/api/v2/channels"
    quality = plugin.get_setting('quality', choices=QUALITIES)
    params = {'format': 'json', 'pagination': 'false', 'audioquality': quality, 'liveaudiotemplateid': 5}
    channels = load_json(SRAPI_CHANNEL_URL, params)
    return channels


@plugin.cached()
def load_programs(channel_id='', category_id=''):
    SRAPI_PROGRAM_URL = "http://api.sr.se/api/v2/programs/index"
    params = {'format': 'json', 'pagination': 'false', 'filter': 'program.hasondemand', 'filterValue': 'true'}
    if channel_id:
        params['channelid'] = channel_id
    if category_id:
        params['programcategoryid'] = category_id
    programs = load_json(SRAPI_PROGRAM_URL, params)
    return programs


# @plugin.cached()
def load_program_episodes(program_id, quality, page='1'):
    page_size = str(plugin.get_setting('page_size'))
    SRAPI_EPISODE_URL = "http://api.sr.se/api/v2/episodes"
    params = {'format': 'json', 'pagination': 'true', 'page': page, 'size': page_size, 'audioquality': quality,
              'programid': program_id}
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
    if 'image' in channel:
        logo = channel['image']
    else:
        logo = None
    item = {'label': name, 'path': url, 'icon': logo, 'is_playable': True}
    return item


def create_channel(channel):
    name = channel['name']
    if 'image' in channel:
        logo = channel['image']
    else:
        logo = None
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
    plugin.set_content('albums')
    prefix_name = bool(strtobool(str(plugin.get_setting('prefix'))))
    url = pod_info['url']
    date_fmt = xbmc.getRegion('dateshort') + " " + xbmc.getRegion('time')
    #   Remove seconds from timestamp
    date_fmt = date_fmt[:-3]
    date_str = pod_info['publishdateutc']
    date_object = datetime.fromtimestamp(float(int(date_str[6:-5])))
    date_strftime = date_object.strftime(date_fmt)
    duration = pod_info['duration']
    pn = program_name + " " + date_strftime
    mediatype = 'album'
    album_description = date_strftime + "[CR]" + name
    size = pod_info['filesizeinbytes']
    if prefix_name:
        name = date_strftime + " " + name
    info = {'duration': duration, 'date': date_strftime, 'title': name, 'size': size, 'album': pn,
            'artist': _('Sveriges_Radio'), 'mediatype': mediatype}
    properties = {'Album_Description': album_description}
    item = {'label': name, 'path': url, 'icon': logo, 'is_playable': True, 'info': info, 'properties': properties}
    items.append(item)


def extract_broadcasts(items, broadcast, logo, name, program_name):
    plugin.set_content('albums')
    for file in broadcast['broadcastfiles']:
        url = file['url']
        prefix_name = bool(strtobool(str(plugin.get_setting('prefix'))))
        date_fmt = xbmc.getRegion('dateshort') + " " + xbmc.getRegion('time')
        #       Remove seconds from timestamp
        date_fmt = date_fmt[:-3]
        plugin.log.debug(date_fmt)
        try:
            date_str = file['publishdateutc']
            date_object = datetime.fromtimestamp(float(int(date_str[6:-2]) / 1000)).date()
            date_object = datetime.fromtimestamp(float(int(date_str[6:-5])))
            date_strftime = date_object.strftime(date_fmt)
            duration = file['duration']
            pn = program_name + " " + date_strftime
            info_type = 'music'
            album_description = date_strftime + "[CR]" + name
            dbtype = 'album'
            mediatype = 'album'
            if prefix_name:
                name = date_strftime + " " + name
            info = {'duration': duration, 'date': date_strftime, 'title': name, 'album': pn,
                    'artist': _('Sveriges_Radio'), 'comment': date_str, 'mediatype': mediatype}
            properties = {'album_description': album_description}
            item = {'label': name, 'info_type': info_type, 'path': url, 'icon': logo, 'is_playable': True, 'info': info,
                    'properties': properties}
            items.append(item)
        except KeyError:
            plugin.log.error("Oops!  Missing values! " + file)


@plugin.route('/channel/<id>')
def list_channel_programs(id):
    response = load_programs(channel_id=id)
    if response:
        items = [create_program(program) for program in response['programs']]
        plugin.add_sort_method('playlist_order')
        plugin.add_sort_method('label')
        return items


@plugin.route('/program/<id>/<page>/', name='list_program_a')
@plugin.route('/program/<id>/', name='list_program', options={'page': '1'})
def list_program(id, page):
    page = int(page)
    page_size = plugin.get_setting('page_size')
    QUALITIES = ["lo", "normal", "hi"]
    quality = plugin.get_setting('quality', choices=QUALITIES)
    response = load_program_episodes(id, quality, str(page))
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

        if page > 1:
            items.insert(0, {
                'label': '<< Prev',
                'path': plugin.url_for('list_program_a', id=id, page=str(page - 1))
            })
        if len(items) > int(page_size) - 1:
            items.append({
                'label': 'Next >>',
                'path': plugin.url_for('list_program_a', id=id, page=str(page + 1))
            })

        if page > 1:
            return plugin.finish(items, update_listing=True)

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
