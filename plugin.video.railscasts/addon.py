'''
    Railscasts XBMC Addon
    -------------------

    Watch screencasts from http://railscasts.com in XBMC.

    :copyright: (c) 2012 by Jonathan Beluch
    :license: GPLv3, see LICENSE.txt for more details.
'''

import re
from urllib2 import urlopen
from xml.dom import minidom
from xbmcswift2 import Plugin

PLUGIN_NAME = 'Railscasts'
PLUGIN_ID = 'plugin.video.railscasts'
plugin = Plugin(PLUGIN_NAME, PLUGIN_ID, __file__)

def get_rss():
    '''Gets RSS feed for the episodes'''
    rss = urlopen('http://feeds.feedburner.com/railscasts')
    return rss

def get_episodes():
    '''Scrapes the episode data from XML'''
    rss = get_rss()

    tree = minidom.parse(rss)
    nodes = tree.childNodes

    episodes = []

    _titles = nodes[0].getElementsByTagName('title')
    _titles.pop(0)
    _descriptions = nodes[0].getElementsByTagName('description')
    _descriptions.pop(0)
    _durations = nodes[0].getElementsByTagName('itunes:duration')
    _urls = nodes[0].getElementsByTagName('enclosure')

    for i in range(0, _titles.length):
        url = _urls[i].getAttribute('url')

        episodes.append({
            'title': _titles[i].childNodes[0].toxml() + ' (' + _durations[i].childNodes[0].toxml() + ')',
            'thumbnail': "http://railscasts.com/static/episodes/stills/%s.png" % (re.search('((?<=/)[a-z0-9-]+)\.mp4', url).group(1)),
            'description': _descriptions[i].childNodes[0].toxml(),
            'url': url
        })

    return episodes

@plugin.route('/')
def index():
    '''The main menu for add-on'''
    items = [{
        'label': episode['title'],
        'path': episode['url'],
        'thumbnail': episode['thumbnail'],
        'info': {
            'plot': episode['description']
        },
        'is_playable': True,
    } for episode in get_episodes()]

    return items

if __name__ == '__main__':
    plugin.run()