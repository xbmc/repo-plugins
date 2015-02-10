#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# Copyright 2011 Jonathan Beluch.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
from xbmcswift import Plugin, download_page, xbmc, xbmcgui
from xbmcswift.ext.playlist import playlist
from BeautifulSoup import BeautifulSoup as BS
from urllib import urlencode
from urlparse import urljoin
import re
try:
    import json
except ImportError:
    import simplejson as json


PLUGIN_NAME = 'AlJazeera'
PLUGIN_ID = 'plugin.video.aljazeera'


plugin = Plugin(PLUGIN_NAME, PLUGIN_ID, __file__)
plugin.register_module(playlist, url_prefix='/_playlist')


BASE_URL = 'http://english.aljazeera.net'
def full_url(path):
    return urljoin(BASE_URL, path)


YOUTUBE_PTN = 'plugin://plugin.video.youtube/?action=play_video&videoid=%s'
def youtube_url(videoid):
    return YOUTUBE_PTN % (videoid)


def parse_queryvideo_args(s):
    '''Parses a QueryVideos javascript call (string) and returns a 4 tuple.

    parse_queryvideo_args("QueryVideos(13,'africanews',1,1)")
    >> ('13, 'africanews', '1', '1')
    '''
    p = re.compile('QueryVideos\((.+?)\)')
    m = p.search(s)
    if not m:
        return None
    count, list_id, start_index, method = m.group(1).split(',')
    return count, list_id.strip("'"), start_index, method


def parse_video(video):
    '''Returns a dict of information for a given json video object.'''
    info = {
        'title': video['title']['$t'],
        'summary': video['media$group']['media$description']['$t'],
        'videoid': video['media$group']['yt$videoid']['$t'],
    }

    # There are multiple images returned, default to high quality
    images = video['media$group']['media$thumbnail']
    for image in images:
        if image['yt$name'] == u'hqdefault':
            info['thumbnail'] = image['url']

    # Make a datetime
    #info['published'] = video['published']['$t']
    return info


def get_videos(count, list_id, start_index):
    '''Returns a tuple of (videos, total_videos) where videos is a list of
    dicts containing video information and total_videos is the toal number
    of videos available for the given list_id. The number of videos returned
    is specified by the given count.

    This function queris the gdata youtube API. The AlJazeera website uses the
    same API on the client side via javascript.'''
    params = {
        'v': '2',
        'author': 'AlJazeeraEnglish',
        'alt': 'json',
        'max-results': count,
        'start-index': start_index,
        'prettyprint': 'true',
        'orderby': 'updated',
    }
    url_ptn = 'http://gdata.youtube.com/feeds/api/videos/-/%s?%s'
    url = url_ptn % (list_id, urlencode(params))
    src = download_page(url)
    resp = json.loads(src)
    videos  = resp['feed']['entry']
    video_infos = map(parse_video, videos)
    total_results = resp['feed']['openSearch$totalResults']['$t']
    return video_infos, total_results


@plugin.route('/', default=True)
def show_homepage():
    items = [
        # Watch Live
        {'label': plugin.get_string(30100),
         'url': plugin.url_for('watch_live')},
        # News Clips
        {'label': plugin.get_string(30101),
         'url': plugin.url_for('show_clip_categories')},
        # Programs
        {'label': plugin.get_string(30102),
         'url': plugin.url_for('show_program_categories')},
    ]
    return plugin.add_items(items)


@plugin.route('/live/')
def watch_live():
    rtmpurl = 'rtmp://aljazeeraflashlivefs.fplive.net:443/aljazeeraflashlive-live?videoId=883816736001&lineUpId=&pubId=665003303001&playerId=751182905001&affiliateId=/aljazeera_eng_med?videoId=883816736001&lineUpId=&pubId=665003303001&playerId=751182905001&affiliateId= live=true'
    li = xbmcgui.ListItem('AlJazeera Live')
    xbmc.Player(xbmc.PLAYER_CORE_DVDPLAYER).play(rtmpurl, li)
    # Return an empty list so we can test with plugin.crawl() and
    # plugin.interactive()
    return []


def only_clip_categories(s):
    return s.find("SelectProgInfo('Selected');") > -1


def only_program_categories(s):
    return not only_clip_categories(s)


@plugin.route('/categories/clips/', onclick_func=only_clip_categories,
              name='show_clip_categories', clips=True)
@plugin.route('/categories/programs/', name='show_program_categories',
              onclick_func=only_program_categories)
def show_categories3(onclick_func, clips=False):
    '''Shows categories available for either Clips or Programs on the aljazeera
    video page.
    '''
    url = full_url('video')
    src = download_page(url)
    # Fix shitty HTML so BeautifulSoup doesn't break
    src = src.replace('id"adSpacer"', 'id="adSpacer"')
    html = BS(src)

    tds = html.findAll('td', {
        'id': re.compile('^mItem_'),
        'onclick': onclick_func,
    })

    items = []

    # The first link for the 'Clips' section links directly to a video so we
    # must handle it differently.
    if clips:
        videos, total_results = get_videos('1', 'vod', '1')
        video = videos[0]
        items.append({
            'label': video['title'],
            'thumbnail': video['thumbnail'],
            'info': {'plot': video['summary'], },
            'url': youtube_url(video['videoid']),
            'is_folder': False,
            'is_playable': True,
        })
        tds = tds[1:]

    for td in tds:
        count, list_id, start_index, method = parse_queryvideo_args(td['onclick'])
        items.append({
            'label': td.string,
            'url': plugin.url_for('show_videos', count=count, list_id=list_id,
                                  start_index=start_index),
        })

    return plugin.add_items(items)


@plugin.route('/videos/<list_id>/<start_index>/<count>/')
def show_videos(list_id, start_index, count):
    '''List videos available for a given category. Only 13 videos are displayed
    at a time. If there are older or newwer videos, appropriate list items will
    be placed at the top of the list.
    '''
    videos, total_results = get_videos(count, list_id, start_index)
    items = [{
        'label': video['title'],
        'thumbnail': video['thumbnail'],
        'info': {'plot': video['summary'], },
        'url': youtube_url(video['videoid']),
        'is_folder': False,
        'is_playable': True,
        'context_menu': [(
            #'Add to Now Playing'
            plugin.get_string(30300),
            'XBMC.RunPlugin(%s)' % plugin.url_for(
                'playlist.add_to_playlist',
                url=youtube_url(video['videoid']),
                label=video['title']
            )
        )],
    } for video in videos]

    # Add '> Older' and '< Newer' list items if the list spans more than 1 page
    # (e.g. > 13 videos)
    if int(start_index) + int(count) < int(total_results):
        items.insert(0, {
            # Older videos
            'label': u'%s »' % plugin.get_string(30200),
            'url': plugin.url_for('show_videos', count=count, list_id=list_id,
                                  start_index=str(int(start_index) + int(count))),
        })
    if int(start_index) > 1:
        items.insert(0, {
            # Newer videos
            'label': u'« %s' % plugin.get_string(30201),
            'url': plugin.url_for('show_videos', count=count, list_id=list_id,
                                  start_index=str(int(start_index) - int(count))),
        })

    return plugin.add_items(items)


if __name__ == '__main__':
    plugin.run()
