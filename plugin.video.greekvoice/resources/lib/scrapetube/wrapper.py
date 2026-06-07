# Scrapetube wrapper for Kodi
# SPDX-License-Identifier: GPL-3.0
# See LICENSES/GPL-3.0 for more information.

from .scrapetube import get_videos, get_channel, get_playlist, get_search


YT_ADDON_ID = 'plugin.video.youtube'
YT_ADDON = 'plugin://{0}'.format(YT_ADDON_ID)
YT_PREFIX = ''.join([YT_ADDON, '/play/?video_id={0}'])


def duration_converter(duration):

    """
    Converts duration in string (minutes:seconds) to integer in seconds
    """

    result = duration.split(':')

    result = int(result[0]) * 60 + int(result[1])

    return result


def list_channel_videos(
    channel_id=None, channel_url=None, limit=None, sleep=1, sort_by="newest",
    add_prefix=True, thumb_quality=-1
):

    items_list = list(get_channel(channel_id, channel_url, limit, sleep, sort_by=sort_by))

    items_list = [
        dict(
            title=i['title']['runs'][0]['text'], url=YT_PREFIX.format(i['videoId']) if add_prefix else i['videoId'],
            image=i['thumbnail']['thumbnails'][thumb_quality]['url'],
            duration=duration_converter(i['thumbnailOverlays'][0]['thumbnailOverlayTimeStatusRenderer']['text']['simpleText'])
            ) for i in items_list
        ]
    
    return items_list
    

def list_playlists(
    url, api='https://www.youtube.com/youtubei/v1/browse', renderer='gridPlaylistRenderer', limit=None, sleep=1
):

    items_list = list(get_videos(url, api, renderer, limit, sleep))

    items_list = [
        dict(
            title=i['title']['runs'][0]['text'], url=i['playlistId'],
            image=i['thumbnail']['thumbnails'][0]['url']
            ) for i in items_list
    ]


def list_playlist_videos(url, limit=None, sleep=1, add_prefix=True, thumb_quality=-1):

    items_list = list(get_playlist(url, limit, sleep))

    items_list = [
        dict(
            title=i['title']['runs'][0]['text'], url=YT_PREFIX.format(i['videoId']) if add_prefix else i['videoId'],
            image=i['thumbnail']['thumbnails'][thumb_quality]['url'],
            duration=duration_converter(i['thumbnailOverlays'][0]['thumbnailOverlayTimeStatusRenderer']['text']['simpleText'])
            ) for i in items_list
        ]

    return items_list


def list_search(
    query, limit=None, sleep=1, sort_by="relevance", results_type="video", add_prefix=True, thumb_quality=-1
):

    items_list = list(get_search(query, limit, sleep, sort_by, results_type))

    if results_type == 'video':

        items_list = [
        dict(
            title=i['title']['runs'][0]['text'], url=YT_PREFIX.format(i['videoId']) if add_prefix else i['videoId'],
            image=i['thumbnail']['thumbnails'][thumb_quality]['url'],
            duration=duration_converter(i['thumbnailOverlays'][0]['thumbnailOverlayTimeStatusRenderer']['text']['simpleText'])
            ) for i in items_list
        ]

        return items_list

    elif results_type == 'playlist':

        items_list = [
        dict(
            title=i['title']['runs'][0]['text'], url=i['playlistId'],
            image=i['thumbnail']['thumbnails'][0]['url']
            ) for i in items_list
    ]

        return items_list

    else:

        return
