'''
    Khan Academy XBMC Addon
    ~~~~~~~~~~~~~~~~~~~~~~~

    Watch videos from http://www.khanacademy.org in XBMC.

    :copyright: (c) 2013 by Jonathan Beluch
    :license: GPLv3, see LICENSE.txt for more details.
'''
import xbmcswift2
from resources.lib import khan


ONE_HOUR_IN_MINUTES = 60
YOUTUBE_URL = 'plugin://plugin.video.youtube/?action=play_video&videoid=%s'
plugin = xbmcswift2.Plugin()


@plugin.cached(TTL=ONE_HOUR_IN_MINUTES)
def get_khan_data():
    '''A wrapper method that exists to cache the results of the remote API
    calls.
    '''
    return khan.load_topic_tree()


def get_playable_url(video):
    '''Returns a the direct mp4 url if present otherwise returns a URL for the
    youtube addon.
    '''
    return video['mp4_url'] or YOUTUBE_URL % video['youtube_id']


def to_listitem(item):
    '''Converts a khan academy dict to an xbmcswift2 item dict.'''
    if 'mp4_url' in item.keys():
        return {
            'label': item['title'],
            'path': get_playable_url(item),
            'is_playable': True,
            'thumbnail': item['thumbnail'],
            'info': {
                'plot': item['description'],
            },
        }
    else:
        return {
            'label': item['title'],
            'path': plugin.url_for('show_topic', topic=item['id']),
        }


@plugin.route('/')
@plugin.route('/<topic>/', name='show_topic')
def main_menu(topic='root'):
    '''The one and only view which displays topics hierarchically.'''
    return [to_listitem(item) for item in get_khan_data()[topic]]


if __name__ == '__main__':
    plugin.run()
