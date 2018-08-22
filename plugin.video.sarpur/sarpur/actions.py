#!/usr/bin/env python
# encoding: UTF-8

import json
import sarpur
import requests
from sarpur import scraper, logger  # noqa
import util.player as player
from util.gui import GUI
from datetime import datetime, timedelta

INTERFACE = GUI(sarpur.ADDON_HANDLE, sarpur.BASE_URL)


def index():
    """
    The front page (i.e. the first one the user sees when opening the plugin)
    """

    INTERFACE.add_dir(u'Beinar útsendingar', 'view_live_index', '')
    INTERFACE.add_dir(u'RÚV', 'view_category', '1')
    INTERFACE.add_dir(u'RÚV Íþróttir', 'view_category', '10')
    INTERFACE.add_dir(u'RÁS 1', 'view_category', '2')
    INTERFACE.add_dir(u'RÁS 2', 'view_category', '3')
    INTERFACE.add_dir(u'Rondó', 'view_category', 'rondo')
    INTERFACE.add_dir(u'Krakkasarpurinn', 'view_category', 'born')
    INTERFACE.add_dir(u'Hlaðvarp', 'view_podcast_index', '')
    # INTERFACE.add_dir(u'Leita', 'search', '')


def live_index():
    """
    List of available live streams
    """
    INTERFACE.add_item(u'RÚV', 'play_live', '1')
    INTERFACE.add_item(u'RÚV Íþróttir', 'play_live', '10')
    INTERFACE.add_item(u'RÁS 1', 'play_live', '2')
    INTERFACE.add_item(u'RÁS 2', 'play_live', '3')
    INTERFACE.add_item(u'Rondó', 'play_live', 'rondo')


def play_url(url, name):
    """
    Play media on page (scrapes it to find it)

    :param url: The page url
    :param name: Text to display in media player
    """
    video_url = scraper.get_media_url(url)
    if video_url == -1:
        GUI.info_box(u"Vesen", u"Fann ekki upptöku")
    else:
        player.play(video_url, name)


def play_video(serie_episode, name):
    """
    Play video give only the filename

    :param serie_episode: Colon seperated string containing
        '{serie_id}:{episode_number}:{file}'
    :param name: Text to display in media player
    :return:
    """
    serie_id, episode_number, filename = serie_episode.split(':')
    episode_number = int(episode_number)
    url = 'https://api.ruv.is/api/programs/program/{0}/all'.format(serie_id)
    r = requests.get(url)
    episodes = [
        episode for episode in r.json()['episodes']
        if episode['number'] == episode_number
    ]
    if not episodes:
        # Sometimes we get episodes that have incorrect (?) episode numbers.
        # We can try to guess using the filename.
        episodes = [
            episode for episode in r.json()['episodes']
            if filename in episode['file']
        ]

    if len(episodes) == 1:
        player.play(episodes[0]['file'], name)
    else:
        url = u"http://smooth.ruv.cache.is/opid/{0}".format(filename)
        r = requests.head(url)
        if r.status_code != 200:
            url = u"http://smooth.ruv.cache.is/lokad/{0}".format(filename)
        logger.log('Using legacy play for %s' % (serie_episode, ))
        player.play(url, name)


def play_podcast(url, name):
    """
    Plays podcast (or any media really

    :param url: Direct url to the media
    :param name: Text to display in media player
    """

    player.play(url, name)


def play_live_stream(category_id, name):
    """
    Play one of the live streams.

    :param category_id: The channel/radio station id (see index())
    :param name: Text to display in media player
    """
    channel_slugs = {
        "1": "ruv",
        "10": "ruv2",
        "2": "ras1",
        "3": "ras2",
        "rondo": "ras3"
    }
    url = scraper.get_live_url(channel_slugs[category_id])
    if url == -1:
        GUI.info_box(u"Vesen", u"Fann ekki straum")
    else:
        player.play(url, name)


def view_category(category_id, date_string):
    """
    Display the available media in category

    :param category_id: The channel/radio station id (see index())
    :param date_string: Display media at this date. Format is %Y%m%d
    """

    if date_string.startswith('<<'):
        format = "<< %d.%m.%Y"
    elif date_string.endswith('>>'):
        format = "%d.%m.%Y >>"
    else:
        format = None
        date = datetime.today()

    if format:
        date = scraper.strptime(date_string, format)

    url = "http://www.ruv.is/sarpur/app/json/{0}/{1}".format(
        category_id,
        date.strftime("%Y%m%d")
    )
    shows = json.loads(requests.get(url).content)

    day_before = date + timedelta(days=-1)
    next_day = date + timedelta(days=1)
    INTERFACE.add_dir(u"<< {0}".format(day_before.strftime("%d.%m.%Y")),
                      'view_category',
                      category_id)
    INTERFACE.add_dir("{0} >>".format((next_day.strftime("%d.%m.%Y"))),
                      'view_category',
                      category_id)

    for show in shows['events']:
        ev = show['event']
        showtime = datetime.fromtimestamp(float(ev['start_time']))
        end_time = datetime.fromtimestamp(float(ev['end_time']))
        in_progress = showtime <= datetime.now() < end_time
        duration = (end_time - showtime).seconds
        display_show_time = (
            in_progress and u"[COLOR blue]Í GANGI[/COLOR]" or
            showtime.strftime("%H:%M")
        )

        title = u"{1} - {0}".format(
            ev['title'],
            display_show_time,
        )
        original_title = ev.get('orginal_title')
        description = ev.get('description', '').strip()
        if original_title and description:
            plot = u"{0} - {1}".format(original_title, description)
        elif description:
            plot = description
        elif original_title:
            plot = original_title
        else:
            plot = u""

        meta = {
            'TVShowTitle': title,
            'Episode': ev['episode_number'],
            'Premiered': showtime.strftime("%d.%m.%Y"),
            'TotalEpisodes': ev['number_of_episodes'],
            'Plot': plot,
            'Duration': duration,
            'fanart_image': ev.get('picture')
        }

        if in_progress:
            INTERFACE.add_item(title,
                               'play_live',
                               category_id,
                               image=ev.get('picture'),
                               extra_info=meta)

        elif ev.get('serie_id') and ev.get('episode_number'):
            serie_episode = '{0}:{1}:{2}'.format(
                ev['serie_id'],
                ev['episode_number'],
                ev['media'],
            )
            INTERFACE.add_item(title,
                               'play_file',
                               serie_episode,
                               image=ev.get('picture'),
                               extra_info=meta)
        else:
            INTERFACE.add_item(title,
                               'play_url',
                               ev.get('url'),
                               image=ev.get('picture'),
                               extra_info=meta)


def podcast_index():
    """
    List all the podcasts.
    """
    for show in scraper.get_podcast_shows(sarpur.PODCAST_URL):
        INTERFACE.add_dir(show['name'],
                          'view_podcast_show',
                          show['url'],
                          image=show['img'])


def podcast_show(url, name):
    """
    List all the recordings in a podcast.

    :param url: The podcast url (xml/rss file)
    :param name: The name of the show
    """
    for recording in scraper.get_podcast_episodes(url):
        INTERFACE.add_item(recording['title'],
                           'play_podcast',
                           recording['url'],
                           extra_info=recording)


def search():
    query = INTERFACE.keyboard(u"Leita að efni")
    if not query:
        index()
    else:
        for show in scraper.search(query):
            INTERFACE.add_item(show['name'],
                               'play_url',
                               show['url'],
                               image=show['img'],
                               extra_info=show)
