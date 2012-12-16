'''
    New York Times XBMC Addon
    ~~~~~~~~~~~~~~~~~~~~~~~~~

    Watch video from The New York Times.
    http://video.on.nytimes.com/

   :copyright: (c) 2012 by Jonathan Beluch
   :license: GPLv3, see LICENSE.txt for more details.
'''
from xbmcswift2 import Plugin
from resources.lib import api


plugin = Plugin()


@plugin.route('/')
def show_topics():
    '''The main menu, shows available video topics'''
    items = [{
        'label': name,
        'path': plugin.url_for('show_topic', url=url),
    } for name, url in api.get_topics()]
    return items


@plugin.route('/topics/<url>')
def show_topic(url):
    '''For a given topic page, shows available sub-topics (if present) as well
    as videos.
    '''
    videos = api.get_videos(url)
    items = [item_from_video(v) for v in videos]

    subtopics = [{
        'label': name,
        'path': plugin.url_for('show_topic', url=url),
    } for name, url in api.get_sub_topics(url)]

    return subtopics + items


def update_url_for_rtmp(url):
    '''Appends playpath option for an RTMP url. Other url types are
    returned unchanged.

    For brightcove urls, the playpath is after the '&'.

    '''
    if url.startswith('rtmp'):
        return '%s playpath=%s' % (url, url.split('&', 1)[1])
    return url


def item_from_video(video):
    '''Returns a dict suitable for passing to plugin.add_items from a
    brightcove api Video.

    '''
    item = {
        'label': video.name,
        'path': update_url_for_rtmp(video.FLVURL),
        'info': info_from_video(video),
        'is_playable': True,
    }

    if video.videoStillURL or video.thumbnailURL:
        item.update({'thumbnail': video.videoStillURL or video.thumbnailURL})

    return item


def info_from_video(video):
    '''Returns an info dict for a video item from a brightcove api
    Video.

    '''
    return {
        'year': video.publishedDate.year,
        'plot': video.longDescription,
        'plotoutline': video.shortDescription,
        'title': video.name,
        'premiered': video.publishedDate.strftime('%Y-%m-%d'),
    }


if __name__ == '__main__':
    plugin.run()
