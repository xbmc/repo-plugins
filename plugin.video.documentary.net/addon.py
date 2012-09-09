'''
    Documentary.net
    ~~~~~~~~~~~~~~~

    An XBMC addon for watching documentaries found on
    http://documentary.net/.

    :copyright: (c) 2012 by Jonathan Beluch
    :license: GPLv3, see LICENSE.txt for more details.
'''
from operator import itemgetter
from xbmcswift2 import Plugin, SortMethod
from resources.lib.api import  get_categories, get_category_posts


PLUGIN_NAME = 'Documentary.net'
PLUGIN_ID = 'plugin.video.documentary.net'
plugin = Plugin(PLUGIN_NAME, PLUGIN_ID, __file__)


def video_url(host, video_id):
    '''This addon uses the youtube and vimeo addons for playback of certain
    items. This functions returns the playable URL given a host and a video_id.
    '''
    ptns = {
        'youtube': 'plugin://plugin.video.youtube/?action=play_video&videoid=%s',
        'vimeo': 'plugin://plugin.video.vimeo/?action=play_video&videoid=%s',
    }
    if host in ptns.keys():
        return ptns[host] % video_id
    return None


@plugin.route('/')
def index():
    '''The main view, lists available categories.'''
    items = [{
        'path': plugin.url_for('show_category', url=item['url']),
        'label': item['title'],
    } for item in get_categories()]

    return items


@plugin.route('/categories/<url>/')
def show_category(url):
    '''Lists playable videos for a given category url.'''
    items = [{
        'path': item.get('video_url') or video_url(item['video_host'],
                                                   item['video_id']),
        'label': item['title'],
        'thumbnail': item.get('thumbnail'),
        'is_playable': True,
        'info': {
            'plot': item['content'],
            'plotoutline': item['excerpt'],
            'aired': item['date'].split()[0],
        },
    } for item in get_category_posts(url)]

    # Filter out items that we can't play, currently just ooyala videos
    items = [item for item in items if item['path'] is not None]

    return plugin.finish(items,sort_methods=[SortMethod.LABEL,
                                             SortMethod.DATE])


if __name__ == '__main__':
    plugin.run()
