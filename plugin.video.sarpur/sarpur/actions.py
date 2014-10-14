#!/usr/bin/env python
# encoding: UTF-8


import sarpur
import sarpur.scraper as scraper
import util.player as player
from util.gui import GUI


INTERFACE = GUI(sarpur.ADDON_HANDLE, sarpur.BASE_URL)

def index():
    """
    .. py:function:: index()

    The front page (i.e. the first one the user sees when opening the plugin)
    """

    INTERFACE.addItem('Bein útsending RÚV', 'play_live', 'ruv')
    INTERFACE.addItem('Bein útsending RÁS 1', 'play_live', 'ras1')
    INTERFACE.addItem('Bein útsending RÁS 2', 'play_live', 'ras2')
    INTERFACE.addItem('Bein útsending Rondó', 'play_live', 'rondo')
    INTERFACE.addDir('Nýtt', 'view_group', '/')
    INTERFACE.addDir('Fréttir', 'view_group', '/flokkar/frettir')
    INTERFACE.addDir('Íþróttir', 'view_group', '/flokkar/ithrottir')
    INTERFACE.addDir('Barnaefni', 'view_group', '/flokkar/born')
    INTERFACE.addDir('Rás 1', 'view_group', '/ras1')
    INTERFACE.addDir('Rás 2', 'view_group', '/ras2')
    INTERFACE.addDir('Sjónvarpsefni', 'view_group', '/flokkar/1')
    INTERFACE.addDir('Íþróttarás', 'view_group', '/flokkar/10')
    INTERFACE.addDir('Hlaðvarp', 'view_podcast_index', '')

def play_video(url, name):
    """
    .. py:function:: play_video(url, name)

    Plays videos (and audio) other than live streams and podcasts.

    :param url: The page url
    :param name: The name of the item to play
    """
    (playpath, rtmp_url, swfplayer) = scraper.get_stream_info(url)
    player.play_stream(playpath, swfplayer, rtmp_url, url, name)

def play_podcast(url):
    """
    .. py:function:: play_podcast(url)

    Plays podcast

    :param url: The file url (this can be any file that xbmc can play)
    """

    player.play(url)

def play_live_stream(name):
    """
    .. py:function:: play_live_stream(name)

    Play one of the live streams.

    :param name: The name of the stream (defined in LIVE_URLS in __init__.py)
    """
    url = sarpur.LIVE_URLS.get(name)
    player.play(url)

def view_group(rel_url):
    """
    .. py:function:: view_group(rel_url)

    List items on one of the groups (flokkur tab) on sarpurinn.

    :param rel_url: Relative url to the flokkur

    """
    full_url =  'http://www.ruv.is/sarpurinn{0}'.format(rel_url)
    for video in scraper.get_videos(full_url):
        name, url = video
        INTERFACE.addItem(name.encode('utf-8'), 'play', url.encode('utf-8'))

def podcast_index():
    """
    .. py:function:: podcast_index()

    List all the podcasts.
    """
    for show in scraper.get_podcast_shows(sarpur.PODCAST_URL):
        name, url = show
        INTERFACE.addDir(name.encode('utf-8'), 'view_podcast_show', url)

def podcast_show(url, name):
    """
    .. py:function:: podcast_show(url, name)

    List all the recordings for a podcast show.

    :param url: The podcast url (xml file)
    :param name: The name of the show
    """
    for recording in scraper.get_podcast_episodes(url):
        date, url = recording
        title = "{0} - {1}".format(name, date.encode('utf-8'))
        INTERFACE.addItem(title, 'play_podcast', url.encode('utf-8'))
