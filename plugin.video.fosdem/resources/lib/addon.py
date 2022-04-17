# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, unicode_literals

from datetime import datetime, timedelta

import routing
from xbmcgui import Dialog, ListItem
from xbmcplugin import addDirectoryItem, addSortMethod, endOfDirectory, getSetting, setContent, setResolvedUrl, SORT_METHOD_LABEL, SORT_METHOD_UNSORTED

from fosdem import fetch_xml, contains_videos
from utils import html_to_kodi

FORMAT_URL = 'https://fosdem.org/{}/schedule/xml'
FORMATS = ['mp4', 'webm']
START_YEAR = 2012

plugin = routing.Plugin()  # pylint: disable=invalid-name


def years():
    now = datetime.now()
    year = now.year

    # Determine if FOSDEM happened this year already
    if now.month < 2 and now.day < 3:
        year -= 1

    return list(range(year, START_YEAR - 1, -1))


def get_setting_int(name):
    val = getSetting(plugin.handle, name)
    if not val:
        val = '0'
    return int(val)


def get_format():
    return FORMATS[get_setting_int('format')]


def get_metadata(event):
    track = event.find('track').text
    subtitle = event.find('subtitle').text
    plot = ''

    abstract = event.find('abstract').text
    if abstract:
        abstract = html_to_kodi(abstract)
    else:
        abstract = ''

    description = event.find('description').text or event.find('abstract').text
    if description:
        description = html_to_kodi(description)
    else:
        description = ''

    person_items = event.findall('./persons/person')
    persons = [p.text for p in person_items] if person_items is not None else []
    if persons:
        plot += '[COLOR=blue]Presenter:[/COLOR] ' + ', '.join(persons) + '\n'

    attachments = event.findall('./attachments/attachment')
    if attachments:
        plot += '[COLOR=red]Slides available[/COLOR]\n'

    if plot:
        plot += '\n'

    if abstract:
        plot += '[I]' + abstract + '[/I]\n'

    if description:
        if abstract:
            plot += '\n'
        plot += description

    return dict(
        cast=persons,
        genre=track,
        plot=plot,
        tagline=subtitle,
    )


@plugin.route('/')
def main_menu():
    for year in years():
        year = str(year)
        url = plugin.url_for(show_dir, subdir=year)
        addDirectoryItem(plugin.handle, url, ListItem(year), True)
    endOfDirectory(plugin.handle)


@plugin.route('/noop')
def noop():
    """The API interface to do nothing"""
    endOfDirectory(plugin.handle)


@plugin.route('/dir/<path:subdir>')
def show_dir(subdir=''):
    root = fetch_xml(subdir)
    for day in root.findall('day'):
        number = day.attrib['index']
        date = day.attrib['date']
        text = '[B]Day {number}[/B] ({date})'.format(number=number, date=date)
        url = plugin.url_for(show_day, year=subdir, day=number)
        addDirectoryItem(plugin.handle, url,
                         ListItem(text), True)
    endOfDirectory(plugin.handle)


@plugin.route('/day/<year>/<day>')
def show_day(year, day):
    exp = './day[@index="{day}"]/room'.format(day=day)
    root = fetch_xml(year)
    for room in root.findall(exp):
        if not contains_videos(room.findall('./event/links/link')):
            continue

        room_name = room.attrib['name']
        track = room.find('./event/track').text
        text = '[B]{track}[/B] - {room_name}'.format(track=track, room_name=room_name)
        url = plugin.url_for(show_room, year=year, day=day, room=room_name)
        addDirectoryItem(plugin.handle, url,
                         ListItem(text), True)
    addSortMethod(handle=plugin.handle, sortMethod=SORT_METHOD_LABEL)
    endOfDirectory(plugin.handle)


@plugin.route('/room/<year>/<day>/<room>')
def show_room(day, year, room):
    exp = './day[@index="{}"]/room[@name="{}"]/event'.format(day, room)
    root = fetch_xml(year)
    for event in root.findall(exp):
        event_id = event.attrib['id']
        title = event.find('title').text
        duration = event.find('duration').text or '00:00'

        if contains_videos(event.findall('./links/link')):
            url = plugin.url_for(show_event,
                                 year=year,
                                 event_id=event_id)
            playable = 'true'
            stream = 'true'
            # duration is formatted as 01:30
            hour, minute = duration.split(':')
            seconds = timedelta(hours=int(hour), minutes=int(minute)).total_seconds()

        else:
            url = plugin.url_for(noop)
            title = '[COLOR=gray]{title}[/COLOR]'.format(title=title)
            playable = 'false'
            stream = 'false'
            seconds = 0

        item = ListItem(title)
        item.setProperty('IsPlayable', playable)
        item.setProperty('IsInternetStream', stream)
        item.setInfo('video', get_metadata(event))

        if seconds:
            item.addStreamInfo('video', {
                'duration': seconds
            })

        addDirectoryItem(plugin.handle, url, item, False)
        setContent(plugin.handle, 'videos')

    addSortMethod(handle=plugin.handle, sortMethod=SORT_METHOD_UNSORTED)
    addSortMethod(handle=plugin.handle, sortMethod=SORT_METHOD_LABEL)
    endOfDirectory(plugin.handle)


@plugin.route('/event/<year>/<event_id>')
def show_event(year, event_id):
    root = fetch_xml(year)
    event = root.find('.//event[@id="{}"]'.format(event_id))

    videos = [link.attrib['href'] for link in event.findall('./links/link') if 'video.fosdem.org' in link.attrib['href']]
    if not videos:
        Dialog().ok('Error playing video', 'FOSDEM event {id} in {year} has no videos.'.format(id=event_id, year=year))
        endOfDirectory(plugin.handle)
        return

    video_format = get_format()
    urls = [video for video in videos if video.endswith(video_format)]
    if urls:
        url = urls[0]
    else:
        # Select a random video
        url = videos[0]
    title = event.find('title').text
    item = ListItem(title, path=url)
    item.setInfo('video', get_metadata(event))
    setResolvedUrl(plugin.handle, True, item)


def run(argv):
    """Addon entry point from wrapper"""
    plugin.run(argv)
