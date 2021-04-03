#!/usr/bin/env python
# encoding: UTF-8

from __future__ import absolute_import
from datetime import datetime, timedelta
import json

import requests

import sarpur
from sarpur import scraper, api, logger  # noqa
import util.player as player
from util.gui import GUI
from util import strptime

INTERFACE = GUI(sarpur.ADDON_HANDLE, sarpur.BASE_URL)
EVENT_DATE_FORMAT = '%Y-%m-%dT%H:%M:%S'


def index():
    """
    The front page (i.e. the first one the user sees when opening the plugin)
    """

    INTERFACE.add_dir(sarpur.getLocalizedString(30900), 'view_live_index', '')
    INTERFACE.add_dir(sarpur.getLocalizedString(30901), 'view_featured', '')
    INTERFACE.add_dir(sarpur.getLocalizedString(30902), 'view_categories', '')
    INTERFACE.add_dir('RÚV', 'view_schedule', 'ruv')
    INTERFACE.add_dir('RÚV 2', 'view_schedule', 'ruv2')
    INTERFACE.add_dir(sarpur.getLocalizedString(30903), 'view_radio', '')
    INTERFACE.add_dir(sarpur.getLocalizedString(30904), 'search', '')


def view_featured(action_value, name):
    for panel in api.featured_panels():
        INTERFACE.add_dir(panel['title'], 'view_panel', panel['slug'])


def view_panel(panel_slug, name):
    for program in api.panel_programs(panel_slug):
        if program['episodes']:
            INTERFACE.add_program_episode(program, program['episodes'][0])


def view_categories(action_value, name):
    for category in api.categories():
        INTERFACE.add_dir(category['title'], 'view_category', category['slug'])


def view_category(category_slug, name):
    for program in api.category_programs(category_slug):
        if program['episodes']:
            INTERFACE.add_program_episode(program, program['episodes'][0])


def view_live_index(action_value, name):
    """
    List of available live streams
    """
    INTERFACE.add_item('RÚV', 'play_live_stream', 'ruv')
    INTERFACE.add_item('RÚV 2', 'play_live_stream', 'ruv2')
    INTERFACE.add_item('RÁS 1', 'play_live_stream', 'ras1')
    INTERFACE.add_item('RÁS 2', 'play_live_stream', 'ras2')
    INTERFACE.add_item('Rondó', 'play_live_stream', 'rondo')


def view_radio(action_value, name):
    INTERFACE.add_dir('RÁS 1', 'view_schedule', 'ras1')
    INTERFACE.add_dir('RÁS 2', 'view_schedule', 'ras2')
    INTERFACE.add_dir('Rondó', 'view_schedule', 'rondo')
    INTERFACE.add_dir(
        sarpur.getLocalizedString(30905),
        'view_podcast_index',
        ''
    )


def play_video(file, name):
    """
    Play video given only the filename

    :param file: playable file
    :param name: Text to display in media player
    :return:
    """
    player.play(file, name)


def play_live_stream(channel, name):
    """
    Play one of the live streams.

    :param channel: The channel/radio station
    :param name: Text to display in media player
    """
    url = scraper.get_live_url(channel)
    if url == -1:
        GUI.info_box(
            sarpur.getLocalizedString(30906),
            sarpur.getLocalizedString(30907),
        )
    else:
        player.play(url, name, live=True)


def view_schedule(channel, date_string):
    """
    Display the available media in category

    :param channel: The channel/radio station
    :param date_string: Display media at this date. Format is %Y%m%d

    TODO: Simplify/extract
    """

    if date_string.startswith('<<'):
        format = "<< %d.%m.%Y"
    elif date_string.endswith('>>'):
        format = "%d.%m.%Y >>"
    else:
        format = None
        date = datetime.today()

    if format:
        date = strptime(date_string, format)

    url = 'https://api.ruv.is/api/schedule/{0}/{1}/'.format(
        channel,
        date.strftime('%Y-%m-%d'),
    )
    shows = requests.get(url).json()

    if 'error' in shows:
        if 'message' in shows:
            GUI.info_box(
                sarpur.getLocalizedString(30906),
                shows['error']['message'],
            )
        else:
            GUI.info_box(
                sarpur.getLocalizedString(30906),
                json.dumps(shows['error']),
            )
        return

    day_before = date + timedelta(days=-1)
    next_day = date + timedelta(days=1)
    INTERFACE.add_dir("<< {0}".format(day_before.strftime("%d.%m.%Y")),
                      'view_schedule',
                      channel)
    INTERFACE.add_dir("{0} >>".format((next_day.strftime("%d.%m.%Y"))),
                      'view_schedule',
                      channel)
    for ev in shows['events']:
        if 'start_time' not in ev:
            continue
        showtime = strptime(ev['start_time'], EVENT_DATE_FORMAT)
        end_time = strptime(ev['end_time'], EVENT_DATE_FORMAT)
        in_progress = showtime <= datetime.now() < end_time
        duration = (end_time - showtime).seconds
        in_progress_str = "[COLOR blue]%s[/COLOR]" % (
            sarpur.getLocalizedString(30908),
        )
        display_show_time = (
            in_progress and in_progress_str or
            showtime.strftime("%H:%M")
        )

        title = "{1} - {0}".format(
            ev['title'],
            display_show_time,
        )
        original_title = ev.get('orginal_title')
        description = '\n'.join(ev.get('description', []))
        if original_title and description:
            plot = "{0} - {1}".format(original_title, description)
        elif description:
            plot = description
        elif original_title:
            plot = original_title
        else:
            plot = ""

        image = ev.get('image', ev.get('default_image'))
        meta = {
            'TVShowTitle': title,
            'Premiered': showtime.strftime("%d.%m.%Y"),
            'Plot': plot,
            'Duration': duration,
            'fanart_image': image,
        }
        if 'episode_number' in ev:
            meta['Episode'] = ev['episode_number']
        if 'number_of_episodes' in ev:
            meta['TotalEpisodes'] = ev['number_of_episodes']

        has_passed = ev['program'] and ev['program']['episodes']
        is_available = ev['web_accessible'] and ev['program'] is not None
        is_playable = has_passed and is_available

        if in_progress:
            INTERFACE.add_item(title,
                               'play_live_stream',
                               channel,
                               image=image,
                               extra_info=meta,
                               )

        elif is_playable:
            episode = ev['program']['episodes'][0]
            subtitles = [episode.get('subtitles_url')]
            INTERFACE.add_item(title,
                               'play_video',
                               episode['file'],
                               image=image,
                               extra_info=meta,
                               subtitles=subtitles,
                               )
        else:
            INTERFACE.add_unselectable_item(
                title,
                image=image,
                extra_info=meta
            )


def view_podcast_index(action_value, name):
    """
    List all the podcasts.
    """
    for show in scraper.get_podcast_shows(sarpur.PODCAST_URL):
        INTERFACE.add_dir(show['name'],
                          'view_podcast_show',
                          show['url'],
                          image=show['img'])


def view_podcast_show(url, name):
    """
    List all the recordings in a podcast.

    :param url: The podcast url (xml/rss file)
    :param name: The name of the show
    """
    for recording in scraper.get_podcast_episodes(url):
        INTERFACE.add_item(recording['title'],
                           'play_video',
                           recording['url'],
                           extra_info=recording)


def search(action_value, name):
    query = INTERFACE.keyboard(sarpur.getLocalizedString(30909))
    if not query:
        index()
    else:
        for program in api.search(query):
            INTERFACE.add_program_dir(program)


def list_program_episodes(program_id, name):
    program = api.program_details(program_id)
    for episode in program['episodes']:
        INTERFACE.add_program_episode(program, episode)
