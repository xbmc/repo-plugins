# -*- coding: utf-8 -*-

import routing
import logging
import xbmcaddon
from resources.lib import kodiutils
from resources.lib import kodilogging
from xbmcgui import ListItem
from xbmcplugin import addDirectoryItem, endOfDirectory


ADDON = xbmcaddon.Addon()
logger = logging.getLogger(ADDON.getAddonInfo('id'))
kodilogging.config()
plugin = routing.Plugin()

AUDIO_STREAMS = (
    {
        'title': 'AD6 Live',
        'logo': 'ad6_small.jpg',
        'fanart': 'fanart.jpg',
        'url_id': ('http://stream.mediagroep-eva.nl:8001/alpe'),
    }, {
        'title': 'Radio d\'HuZes',
        'logo': 'radiodhuzes.jpg',
        'fanart': 'radiodhuzes_fanart.jpg',
        'url_id': ('http://stream001.digiplay.nl:9040'),
    },
)

VIDEO_STREAMS = (
    {
        'title': 'AD6 Live',
        'logo': 'ad6_small.jpg',
        'fanart': 'fanart.jpg',
        'url_id': ('https://d3slqp9xhts6qb.cloudfront.net/omroepbrabantTvExtra1/index.m3u8'),
    },
)

YOUTUBE_CHANNELS = (
    {
        'title': '(YouTube) Live webcam',
        'logo': 'ad6_small.jpg',
        'fanart': 'fanart.jpg',
        'url_id': 'UCQ4jrGcpg9JmnLJ8Ma-iMDQ',
        'user': 'kwfkankerbestrijding',
    }, {
        'title': '(YouTube) Alpe d\'HuZes',
        'logo': 'ad6_small.jpg',
        'fanart': 'fanart.jpg',
        'url_id': 'UCmYG5APUGAmumx67gi4Iu6Q',
        'user': 'alpedhuzes',
    }, {
        'title': '(YouTube) KWF Kankerbestrijding',
        'logo': 'kwf.png',
        'fanart': 'fanart.jpg',
        'url_id': 'UCtuMYGgKhtA5Kfnh2iDDjGw',
        'user': 'kwfkankerbestrijding',
    }, {
        'title': '(YouTube) Radio d\'HuZes',
        'logo': 'radiodhuzes.jpg',
        'fanart': 'radiodhuzes_fanart.jpg',
        'url_id': 'UCYS7HDNW7wiSEe6UF6OLQmQ',
        'user': 'radiodhuzes',
    },

)

YOUTUBE_URL = 'plugin://plugin.video.youtube/channel/%s/?page=1'

FLICKR_URL = 'plugin://plugin.image.flickr'


@plugin.route('/')
def index():
    content_type = plugin.args['content_type'][0]

    if content_type == 'video':
        build_dir(VIDEO_STREAMS)
        build_dir(YOUTUBE_CHANNELS, YOUTUBE_URL)
        endOfDirectory(plugin.handle)
    if content_type == 'audio':
        build_dir(AUDIO_STREAMS)
        endOfDirectory(plugin.handle)


def build_dir(streams, prefix=None):
    for stream in streams:
        if prefix is None:
            url = stream['url_id']
            folder = False
        else:
            url = prefix % stream['url_id']
            folder = True
        li = ListItem(label=stream['title'])
        li.setArt({'thumb': get_logo(stream['logo']), 'icon': get_logo(stream['logo']), 'fanart': get_logo(stream['fanart'])})
        addDirectoryItem(
            plugin.handle,
            url,
            li,
            folder
        )


def get_logo(logo):
    addon_id = ADDON.getAddonInfo('id')
    return 'special://home/addons/%s/resources/media/%s' % (addon_id, logo)


def run():
    plugin.run()
