'''
    VimCasts KODI Addon
    -------------------

    Watch screencasts from http://vimcasts.org in KODI.

    :copyright: (c) 2012 by Jonathan Beluch
    :license: GPLv3, see LICENSE.txt for more details.
'''
import re
import sys
try:
    import json
except ImportError:
    import simplejson as json
from xbmcswift2 import Plugin

PY3 = sys.version_info.major >= 3

if PY3:
    from html.parser import HTMLParser
    from urllib.request import urlopen
else:
    from HTMLParser import HTMLParser
    from urllib2 import urlopen

PLUGIN_NAME = 'VimCasts'
PLUGIN_ID = 'plugin.video.vimcasts'
plugin = Plugin(PLUGIN_NAME, PLUGIN_ID, __file__)


def get_json_feed():
    '''Loads the JSON feed for vimcasts.org.'''
    json_url = 'http://vimcasts.org/episodes.json?referrer=xbmc'
    conn = urlopen(json_url)
    _json = json.load(conn)
    conn.close()
    return _json


def strip_tags(inp):
    '''Naively strips instances of <tag> from the given inp'''
    return re.sub('(<.+?>)', '', inp)


_parser = HTMLParser()
def unescape_html(inp):
    '''Replaces named instances of html entities with the corresponding
    unescaped character.

    >>> unescape_html('apples &amp; oranges')
    apples & oranges
    '''
    return _parser.unescape(inp)


def clean(inp):
    '''Strips HTML tags and unescapes named HTML entities for the given input.

    >>> clean('<strong>apples &amp; oranges</strong>')
    apples & oranges
    '''
    return unescape_html(strip_tags(inp))


@plugin.route('/')
def index():
    '''The main menu and only view for this plugin. Lists available episodes'''
    items = [{
        'label': '#%s %s' % (epi['episode_number'], epi['title']),
        'path': epi['quicktime']['url'],
        'thumbnail': epi['poster'],
        'fanart': plugin.fanart,
        'info': {
            'plot': clean(epi['abstract']),
            'duration': int(epi['quicktime']['seconds'])
        },
        'is_playable': True,
    } for epi in get_json_feed()['episodes'] if epi['quicktime']['url']]

    finish_kwargs = {
        'sort_methods': [
            ('UNSORTED', '%X'),
            ('TITLE', '%X'),
            'DURATION',
        ],
    }

    return plugin.finish(items, **finish_kwargs)


def run():
    plugin.run()
