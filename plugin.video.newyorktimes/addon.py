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


def update_url_for_rtmp(url):
    '''Appends playpath option for an RTMP url. Other url types are
    returned unchanged.

    For brightcove urls, the playpath is after the '&'.

    '''
    if url.startswith('rtmp'):
        return '%s playpath=%s' % (url, url.split('&', 1)[1])
    return url


def item_from_video(video, XXL4HIRES):
    '''Returns a dict suitable for passing to plugin.add_items from a
    brightcove api Video.

    '''
    # extract the best possible resolution from renditions[] given the XXL4HIRES option:
    url=url_best=''
    signal=signal_best=0
    for p in video.renditions: 
        url=''
        signal=0
        for q in p: 
            if q[0] == 'url':
                url=q[1]
                if XXL4HIRES == 'false' and signal == 1: break
            if q[0] == 'frameHeight':
                if XXL4HIRES == 'false':
                    if q[1]>400 and q[1]<500:
                        signal=1
                        if url != '': break
                else:
                    if q[1]>signal:
                        signal=q[1]
        if XXL4HIRES == 'false' and signal == 1: 
            url_best=url
            break
        if XXL4HIRES == 'true' and signal > signal_best:
            signal_best=signal
            url_best=url

    item = {
        'label': video.name,
        'path': update_url_for_rtmp(url_best),
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
