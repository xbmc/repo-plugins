#!/usr/bin/env python
# encoding: UTF-8


import sarpur
import sarpur.scraper as scraper
import util.player as player
from sarpur.cached import Categories
from util.gui import GUI


INTERFACE = GUI(sarpur.ADDON_HANDLE, sarpur.BASE_URL)
CATS = Categories()

def index():
    """
    The front page (i.e. the first one the user sees when opening the plugin)
    """

    for tab in CATS.tabs:
        title = tab[0].encode('utf-8')
        url = tab[1].encode('utf-8')
        INTERFACE.addDir(title, 'view_tab', url)

    for i, channel in enumerate(CATS.showtree):
        title = '{0} Þættir'.format(channel['name'].encode('utf-8'))
        INTERFACE.addDir(title, 'view_channel_index', i)

    INTERFACE.addDir('Hlaðvarp', 'view_podcast_index', '')
    INTERFACE.addItem('Bein úttsending: RÚV', 'play_live', 'ruv')
    INTERFACE.addItem('Bein úttsending: RÁS 1', 'play_live', 'ras1')
    INTERFACE.addItem('Bein úttsending: RÁS 2', 'play_live', 'ras2')
    INTERFACE.addItem('Bein úttsending: RONDÓ', 'play_live', 'rondo')

def channel_index(channel):
    for i, category in enumerate(CATS.showtree[channel].get('categories')):
        INTERFACE.addDir(category['name'].encode('utf-8'),
                   'view_channel_category',
                   "{0};{1}".format(channel, i))

def channel_category(channel, category):
    for show in CATS.showtree[channel]['categories'][category]['shows']:
        name, url = show
        if url[0] == '/':
            url = 'http://dagskra.ruv.is%s' % url
        INTERFACE.addDir(name.encode('utf-8'),
                         'view_channel_category_show',
                         url.encode('utf-8'))

def channel_category_show(url, show_name):
    episodes = scraper.get_episodes(url)
    if not episodes:
        INTERFACE.infobox("Engar upptökur", "Engin upptaka fannst")
    else:
        for episode in episodes:
            episode_name, url = episode
            name = "{0} - {1}".format(show_name, episode_name.encode('utf-8'))
            INTERFACE.addItem(name, 'play', url)

def play_video(url, name):
    (playpath, rtmp_url, swfplayer) = scraper.get_stream_info(url)
    player.play_stream(playpath, swfplayer, rtmp_url, url, name)

def play_podcast(url):
    player.play(url)

def play_live_stream(name):
    #url = scraper.get_live_url(name)
    url = sarpur.LIVE_URLS.get(name)
    player.play(url)

def tab_index(url):
    pageurl = 'http://www.ruv.is{0}'.format(url)

    episodes = scraper.get_tab_items(pageurl)
    if not episodes:
        INTERFACE.infobox("Engar upptökur", "Engin upptaka fannst")
    else:
        for episode in episodes:
            episode_name, url = episode
            INTERFACE.addItem(episode_name.encode('utf-8'),
                              'play',
                              url.encode('utf-8'))

def podcast_index():
    for show in scraper.get_podcast_shows():
        name, url = show
        INTERFACE.addDir(name.encode('utf-8'), 'view_podcast_show', url)

def podcast_show(url, name):
    for recording in scraper.get_podcast_episodes(url):
        date, url = recording
        title = "{0} - {1}".format(name, date.encode('utf-8'))
        INTERFACE.addItem(title, 'play_podcast', url.encode('utf-8'))
