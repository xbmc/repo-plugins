'''
    New York Times XBMC Addon
    ~~~~~~~~~~~~~~~~~~~~~~~~~

    Watch video from The New York Times.
    http://video.on.nytimes.com/

   :copyright: (c) 2012 by Jonathan Beluch
   :modified on 2014 by idleloop
   :license: GPLv3, see LICENSE.txt for more details.
'''
from xbmcswift2 import Plugin
from resources.lib import api

###
#
# bigger videos settings
import xbmcaddon
settings = xbmcaddon.Addon(id='plugin.video.newyorktimes')
#
###

plugin = Plugin()


@plugin.route('/')
def show_topics():
    '''The main menu, shows available video topics'''
    items = [{
        'label': name.replace('&amp;', "&"),
        'path': plugin.url_for('show_topic', url=url),
    } for name, url in api.get_topics()]
    return items


@plugin.route('/topics/<url>')
def show_topic(url):
    '''For a given topic page, shows available sub-topics (if present) as well
    as videos.
    '''
    videos = api.get_videos(url)
    XXL4HIRES = settings.getSetting("xxl4hires")
    items = [item_from_video(v, XXL4HIRES) for v in videos]

    subtopics = [{
        'label': name,
        'path': plugin.url_for('show_topic', url=url),
    } for name, url in api.get_sub_topics(url)]

    return subtopics + items


def update_url_for_rtmp(url, XXL4HIRES):
    '''Appends playpath option for an RTMP url. Other url types are
    returned unchanged.

    For brightcove urls, the playpath is after the '&'.

    '''
    if XXL4HIRES == 'true': url=url.replace('_xl_','_xxl_')
    ###print "XXL4HIRES = " + XXL4HIRES + " url = " + url
    if url.startswith('rtmp'):
        return '%s playpath=%s' % (url, url.split('&', 1)[1])
    return url


def item_from_video(video, XXL4HIRES):
    '''Returns a dict suitable for passing to plugin.add_items from a
    brightcove api Video.

    '''
    item = {
        'label': video.name,
        'path': update_url_for_rtmp(video.FLVURL, XXL4HIRES),
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
