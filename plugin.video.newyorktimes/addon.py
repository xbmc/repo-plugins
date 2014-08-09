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

import re

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
    # 201408: new renditions (video resolutions) have been added... and FLVURL is anchored to 3g resolution (?)
    #         maybe in the future renditions[] should be parsed and resolution selected by "encodingRate".
    url = re.sub(r'^(.+_wg_16x9)_.+_.+_.+\.mp4$', r'\1_xl_bb_mm.mp4', url)
    if XXL4HIRES == 'true': 
        url=url.replace('_xl_bb_mm.mp4','_xxxl_hb_mm.mp4') 
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
