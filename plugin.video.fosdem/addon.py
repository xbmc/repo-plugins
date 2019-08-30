# -*- coding: utf-8 -*-
import sys
from datetime import datetime, timedelta

import routing
from xbmcgui import ListItem
from xbmcplugin import addDirectoryItem, endOfDirectory, setResolvedUrl, getSetting, setContent

from resources.lib.fosdem import fetch_xml, contains_videos

FORMAT_URL = 'https://fosdem.org/{}/schedule/xml'
FORMATS = ['mp4', 'webm']
YEARS_SHOWN = 5

plugin = routing.Plugin()


def years():
    now = datetime.now()
    year = now.year

    # Determine if FOSDEM happened this year already
    if now.month < 2 and now.day < 3:
        year -= 1

    # Range does not include the end.
    year += 1
    return range(year - YEARS_SHOWN, year)


def get_setting_int(name):
    val = getSetting(plugin.handle, name)
    if not val:
        val = '0'
    return int(val)


def get_format():
    return FORMATS[get_setting_int('format')]


@plugin.route('/')
@plugin.route('/dir/<path:subdir>')
def show_dir(subdir=''):
    if subdir == '':
        for year in years():
            year = str(year)
            url = plugin.url_for(show_dir, subdir=year)
            addDirectoryItem(plugin.handle, url, ListItem(year), True)
    else:
        root = fetch_xml(subdir)
        for day in root.findall('day'):
            number = day.attrib['index']
            date = day.attrib['date']
            text = 'Day {} ({})'.format(number, date)
            url = plugin.url_for(show_day, year=subdir, day=number)
            addDirectoryItem(plugin.handle, url,
                             ListItem(text), True)
    endOfDirectory(plugin.handle)


@plugin.route('/day/<year>/<day>')
def show_day(year, day):
    exp = './day[@index="{}"]/room'.format(day)
    root = fetch_xml(year)
    for room in root.findall(exp):
        if not contains_videos(room.findall('./event/links/link')):
            continue

        name = room.attrib['name']
        genre = room.find('./event/track').text
        text = '{} - {}'.format(name, genre)
        url = plugin.url_for(show_room, year=year, day=day, room=name)
        addDirectoryItem(plugin.handle, url,
                         ListItem(text), True)
    endOfDirectory(plugin.handle)


@plugin.route('/room/<year>/<day>/<room>')
def show_room(day, year, room):
    exp = './day[@index="{}"]/room[@name="{}"]/event'.format(day, room)
    root = fetch_xml(year)
    for event in root.findall(exp):
        if not contains_videos(event.findall('./links/link')):
            continue

        event_id = event.attrib['id']
        title = event.find('title').text
        track = event.find('track').text
        subtitle = event.find('subtitle').text
        person_items = event.find('./persons/person')
        persons = [p.text for p in person_items] if person_items is not None else []
        abstract = event.find('abstract').text
        duration = event.find('duration').text or '0:0'
        if abstract:
            abstract = abstract.replace('<p>', '').replace('</p>', '')

        item = ListItem(title)
        item.setProperty('IsPlayable', 'true')
        item.setInfo('video', {
            'cast': persons,
            'genre': track,
            'plot': abstract,
            'tagline': subtitle,
            'title': title,
        })

        # duration is formatted as 01:30
        hour, minute = duration.split(':')
        seconds = timedelta(hours=int(hour), minutes=int(minute)).total_seconds()

        item.addStreamInfo('video', {
            'duration': seconds
        })
        url = plugin.url_for(show_event,
                             year=year,
                             event_id=event_id)
        addDirectoryItem(plugin.handle, url, item, False)
        setContent(plugin.handle, 'videos')

    endOfDirectory(plugin.handle)


@plugin.route('/event/<year>/<event_id>')
def show_event(year, event_id):
    root = fetch_xml(year)
    event = root.find('.//event[@id="{}"]'.format(event_id))
    videos = [link.attrib['href'] for link in event.findall('./links/link') if 'video.fosdem.org' in link.attrib['href']]
    if not videos:
        setResolvedUrl(plugin.handle, False, ListItem(path=event_id))
        return

    video_format = get_format()
    urls = [video for video in videos if video.endswith(video_format)]
    if urls:
        url = urls[0]
    else:
        # Select a random video
        url = videos[0]
    setResolvedUrl(plugin.handle, True, ListItem(path=url))


if __name__ == '__main__':
    plugin.run(sys.argv)
