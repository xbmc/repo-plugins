# -*- coding: utf-8 -*-
# Copyright: (c) 2017, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
import base64
import json

# noinspection PyUnresolvedReferences
from codequick import Listitem, Resolver, Route
import urlquick

from resources.lib import download
from resources.lib.menu_utils import item_post_treatment

# TODO
# Get sub-playlist

URL_ROOT = 'https://www.nytimes.com'

URL_VIDEOS = URL_ROOT + '/video'

URL_PLAYLIST = URL_ROOT + '/svc/video/api/v2/playlist/%s'
# playlistId

URL_REQUESTS = 'https://samizdat-graphql.nytimes.com/graphql/v2'

URL_STREAM = URL_ROOT + '/svc/video/api/v3/video/%s'
# videoId

HEADERS = {'Content-Type': 'application/json',
           'nyt-app-type': 'project-vi',
           'nyt-app-version': '0.0.5',
           'nyt-token': ('MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAs+/oU'
                         'CTBmD/cLdmcecrnBMHiU/pxQCn2DDyaPKUOXxi4p0uUSZQzsu'
                         'q1pJ1m5z1i0YGPd1U1OeGHAChWtqoxC7bFMCXcwnE1oyui9G1'
                         'uobgpm1GdhtwkR7ta7akVTcsF8zxiXx7DNXIPd2nIJFH83rmk'
                         'ZueKrC4JVaNzjvD+Z03piLn5bHWU6+w+rA+kyJtGgZNTXKyPh'
                         '6EC6o5N+rknNMG5+CdTq35p8f99WjFawSvYgP9V64kgckbTbt'
                         'dJ6YhVP58TnuYgr12urtwnIqWP9KSJ1e5vmgf3tunMqWNm6+A'
                         'nsqNj8mCLdCuc5cEB74CwUeQcP2HQQmbCddBy2y0mEwIDAQAB')}


def video_query(videoid='', playlistid='', genericid='', cursor=""):
    _json = {"operationName": "VideoWatchQuery",
             "variables": {"id": videoid,
                           "playlistId": playlistid,
                           "genericId": genericid,
                           "magazineId": "",
                           "opinionId": "",
                           "cursor": cursor},
             "extensions": {"persistedQuery": {
                 "version": 1,
                 "sha256Hash": "7d32782d33329093e28a10b3238ecd0408f008127e957241a3f23ad4774904d7"}}}
    return urlquick.request('POST', URL_REQUESTS, data=json.dumps(_json), headers=HEADERS, max_age=-1)


def additional_playlists_query(playlistids=None):
    if playlistids is None:
        playlistids = []
    _json = {"operationName": "AdditionalPlaylistsQuery",
             "variables": {"playlistIds": playlistids},
             "extensions": {"persistedQuery": {
                 "version": 1,
                 "sha256Hash": "99be195e9692ba8b9a28713feb3a54699b4b65565294c037eb331ced2e662f24"}}}
    return urlquick.request('POST', URL_REQUESTS, data=json.dumps(_json), headers=HEADERS, max_age=-1)


def format_day(date, **kwargs):
    """Format day"""
    date_list = date.split('T')
    date_dmy = date_list[0].replace('-', '/')
    return date_dmy


@Route.register
def website_root(plugin, item_id, **kwargs):
    """Add modes in the listing"""

    # import web_pdb; web_pdb.set_trace()
    query = video_query(genericid="/video/embedded/admin/100000006681488/main-video-navigation.html")
    json_parser = query.json()

    if "PersistedQueryNotFound" in query.text:
        plugin.notify(plugin.localize(30600), plugin.localize(30716))
        return False

    categories = json_parser['data']['genericVideoPlaylists']['summary'].split(',')

    playlist = []
    for category in categories:
        playlist.append('/video/{}'.format(category.strip()))

    playlists_query = additional_playlists_query(playlistids=playlist)

    if "PersistedQueryNotFound" in playlists_query.text:
        plugin.notify(plugin.localize(30600), plugin.localize(30716))
        return False

    json_parser2 = playlists_query.json()
    for anywork in json_parser2['data']['anyWorks']:
        item = Listitem()
        item.label = anywork['promotionalHeadline']
        item.set_callback(list_videos,
                          item_id=item_id,
                          playlistid='/video/{}'.format(anywork['slug']))
        item_post_treatment(item)
        yield item

    for channel in json_parser['data']['videoNavigationChannels']:
        if channel['publishUrl'] not in playlist:
            item = Listitem()
            item.label = channel['displayName']
            item.set_callback(list_videos,
                              item_id=item_id,
                              playlistid=channel['publishUrl'])
            item_post_treatment(item)
            yield item


@Route.register
def list_videos(plugin, item_id, playlistid, cursor="", **kwargs):
    """Build videos listing"""

    query = video_query(playlistid=playlistid, cursor=cursor)

    if "PersistedQueryNotFound" in query.text:
        plugin.notify(plugin.localize(30600), plugin.localize(30716))
        return False

    videos_jsonparser = query.json()

    try:
        for video_data in videos_jsonparser['data']['playlist']['relatedVideos']['edges']:
            item = Listitem()
            video_id = video_data['node']['url']
            item.label = video_data['node']['headline']['default']
            item.info['duration'] = video_data['node']['duration']
            item.info['plot'] = video_data['node']['summary']
            video_img = video_data['node']['promotionalMedia']['crops'][0]['renditions'][0]['url']
            item.art['thumb'] = item.art['landscape'] = video_img
            date_value = format_day(video_data['node']['firstPublished'])
            item.info.date(date_value, '%Y/%m/%d')

            item.set_callback(get_video_url,
                              item_id=item_id,
                              video_id=video_id)
            item_post_treatment(item, is_playable=True, is_downloadable=True)
            yield item

        endcursor = videos_jsonparser['data']['playlist']['relatedVideos']['pageInfo']['endCursor']
        nb_videos = int(base64.b64decode(endcursor).decode('utf-8').split(':')[1]) + 1
        if nb_videos % 12 == 0:
            yield Listitem.next_page(
                item_id=item_id,
                playlistid=playlistid,
                cursor=endcursor)

    except IndexError:
        yield None


@Resolver.register
def get_video_url(plugin,
                  item_id,
                  video_id,
                  download_mode=False,
                  **kwargs):
    """Get video URL and start video player"""
    query = video_query(videoid=video_id)

    if "PersistedQueryNotFound" in query.text:
        plugin.notify(plugin.localize(30600), plugin.localize(30716))
        return False

    video_jsonparser = query.json()

    video_url = ''
    for video in video_jsonparser['data']['video']['renditions']:
        if video["type"] == 'hls':
            video_url = video["url"]

    if download_mode:
        return download.download_video(video_url)

    return video_url
