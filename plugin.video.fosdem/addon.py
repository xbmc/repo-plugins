# -*- coding: utf-8 -*-
from datetime import timedelta

import requests

import routing
from xbmcgui import ListItem
from xbmcplugin import addDirectoryItem, endOfDirectory, setResolvedUrl, getSetting

# FIXME: BS4?
import xml.etree.ElementTree as ET

URL = 'https://fosdem.org/2018/schedule/xml'
FORMATS = ['mp4', 'webm']

plugin = routing.Plugin()
root = None


def fetch_root():
    r = requests.get(URL)
    return ET.fromstring(r.text.encode('utf-8'))

def contains_videos(links):
    videos = list(filter(lambda x: 'video.fosdem.org' in x,
                  map(lambda x: x.attrib['href'], links)))
    return videos != []


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
        url = plugin.url_for(show_dir, subdir='2018')
        addDirectoryItem(plugin.handle, url, ListItem('2018'), True)
    else:
        for day in root.findall('day'):
            number = day.attrib['index']
            text = 'Day {}'.format(number)
            url = plugin.url_for(show_day, day=number)
            addDirectoryItem(plugin.handle, url,
                             ListItem(text), True)
    endOfDirectory(plugin.handle)


@plugin.route('/day/<day>')
def show_day(day):
    exp = './day[@index="{}"]/room'.format(day)
    for room in root.findall(exp):
        if not contains_videos(room.findall('./event/links/link')):
            continue

        name = room.attrib['name']
        url = plugin.url_for(show_room, day=day, room=name)
        addDirectoryItem(plugin.handle, url,
                         ListItem(name), True)
    endOfDirectory(plugin.handle)


@plugin.route('/room/<day>/<room>')
def show_room(day, room):
    exp = './day[@index="{}"]/room[@name="{}"]/event'.format(day, room)
    for event in root.findall(exp):
        if not contains_videos(event.findall('./links/link')):
            continue

        event_id = event.attrib['id']
        title = event.find('title').text
        track = event.find('track').text
        subtitle = event.find('subtitle').text
        persons = [p.text for p in event.find('./persons/person')]
        abstract = event.find('abstract').text
        duration = event.find('duration').text
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
                             event_id=event_id)
        addDirectoryItem(plugin.handle, url, item, False)

    endOfDirectory(plugin.handle)


@plugin.route('/event/<event_id>')
def show_event(event_id):
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
    root = fetch_root()
    plugin.run()
