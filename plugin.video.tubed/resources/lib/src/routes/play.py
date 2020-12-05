# -*- coding: utf-8 -*-
"""
    Copyright (C) 2020 Tubed (plugin.video.tubed)

    This file is part of plugin.video.tubed

    SPDX-License-Identifier: GPL-2.0-only
    See LICENSES/GPL-2.0-only.txt for more information.
"""

from copy import deepcopy
from html import unescape

import arrow
import xbmc  # pylint: disable=import-error
import xbmcplugin  # pylint: disable=import-error

from ..api.utils import choose_subtitles
from ..generators.data_cache import get_cached
from ..generators.utils import get_thumbnail
from ..generators.video import video_generator
from ..items.stream import Stream
from ..lib.pickle import write_pickled
from ..lib.time import iso8601_duration_to_seconds


def invoke(context, video_id='', playlist_id='', prompt_subtitles=False, start_offset=None):
    if video_id and not playlist_id:
        play_single(context, video_id, prompt_subtitles, start_offset)
        return

    if playlist_id:
        play_playlist(context, playlist_id, video_id)
        return


def play_playlist(context, playlist_id, video_id):
    successful = create_playlist(context, playlist_id, video_id)
    if successful:

        playlist, start_position, start_item = successful
        if context.handle != -1:
            xbmcplugin.setResolvedUrl(context.handle, True, start_item)

        else:  # called from script use Player().play()
            xbmc.Player().play(item=playlist, startpos=start_position)


def create_playlist(context, playlist_id, video_id):
    playlist_items = []

    page_token = True
    while page_token:
        if page_token is True:
            page_token = ''

        payload = context.api.playlist_items(
            playlist_id,
            page_token=page_token,
            fields='items(kind,id,snippet(playlistId,resourceId/videoId))'
        )

        playlist_items.extend(payload.get('items', []))

        page_token = payload.get('nextPageToken')
        if not page_token:
            break

    if not playlist_items:
        return None

    list_items = []

    # make lists of 50 for api requests that follow
    groups = [playlist_items[index:index + 50] for index in range(0, len(playlist_items), 50)]
    for group in groups:
        list_items += list(video_generator(context, group))

    if not list_items:
        return None

    start_position = 0
    start_item = None

    playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
    playlist.clear()

    for index, (path, list_item, _) in enumerate(list_items):
        if list_item.getProperty('video_id') == video_id:
            start_position = index
            start_item = list_item

        playlist.add(path, list_item)

    return playlist, start_position, start_item


def play_single(context, video_id, prompt_subtitles=False, start_offset=None):
    quality = context.api.quality(
        context.settings.video_quality,
        limit_30fps=context.settings.limit_to_30fps,
        hdr=context.settings.hdr
    )

    payload = context.api.resolve(video_id=video_id, quality=quality)

    try:
        cached_payload = get_cached(context, context.api.videos, [video_id])
    except:  # pylint: disable=bare-except
        cached_payload = {}

    license_data = payload.get('license', {})

    resolved_metadata = payload.get('metadata', {})
    resolved_channel = resolved_metadata.get('channel', {})
    resolved_video = resolved_metadata.get('video', {})
    resolved_images = resolved_metadata.get('images', {})

    thumbnail = resolved_images.get('standard', resolved_images.get('high', ''))
    if not thumbnail:
        thumbnail = resolved_images.get('medium', resolved_images.get('default', ''))

    cached_video = cached_payload.get(video_id, {})
    snippet = cached_video.get('snippet', {})
    content_details = cached_video.get('contentDetails', {})

    if not snippet:
        video_title = resolved_video.get('title', '')
        channel_name = resolved_channel.get('author', '')

    else:
        video_title = unescape(snippet.get('title', ''))
        channel_name = unescape(snippet.get('channelTitle', ''))

    stream = Stream(
        label=video_title,
        label2=channel_name,
        path=payload.get('url', ''),
        headers=payload.get('headers', ''),
        license_key=license_data.get('proxy', '')
    )

    subtitles = choose_subtitles(
        context,
        subtitles=resolved_metadata.get('subtitles', []),
        prompt_override=prompt_subtitles
    )
    stream.ListItem.setSubtitles(subtitles)

    duration = iso8601_duration_to_seconds(content_details.get('duration', ''))

    if snippet:
        published_arrow = arrow.get(snippet['publishedAt']).to('local')
        info_labels = {
            'mediatype': 'video',
            'plot': unescape(snippet.get('description', '')),
            'plotoutline': unescape(snippet.get('description', '')),
            'originaltitle': video_title,
            'sorttitle': video_title,
            'studio': channel_name,
            'year': published_arrow.year,
            'premiered': published_arrow.format('YYYY-MM-DD'),
            'dateadded': published_arrow.format('YYYY-MM-DD HH:mm:ss'),
        }

        if duration:
            info_labels['duration'] = duration

        if snippet.get('liveBroadcastContent', 'none') != 'none':
            info_labels['playcount'] = '0'

        if start_offset is not None and duration:
            # start `preload_time:5` seconds earlier than offset, otherwise a start offset of
            # 60 may actually start at 61~64 seconds
            preload_time = 5.0
            start_offset = float(start_offset)
            if start_offset >= preload_time:
                start_offset = start_offset - preload_time

            info_labels['playcount'] = '0'
            stream.ListItem.setProperty('ResumeTime', '%.1f' % start_offset)
            stream.ListItem.setProperty('TotalTime', '%.1f' % duration)

        thumbnail = get_thumbnail(snippet)

    else:
        info_labels = {
            'mediatype': 'video',
            'originaltitle': video_title,
            'sorttitle': video_title,
            'studio': channel_name,
        }

    stream.ListItem.setInfo('video', info_labels)

    stream.ListItem.setArt({
        'icon': thumbnail,
        'thumb': thumbnail,
    })

    metadata = deepcopy(info_labels)
    metadata.update({
        'art': {
            'icon': thumbnail,
            'thumb': thumbnail,
        }
    })

    write_pickled('playback.pickle', {
        'video_id': video_id,
        'playing_file': stream.ListItem.getPath(),
        'metadata': metadata,
        'live': snippet.get('liveBroadcastContent', 'none') != 'none',
    })

    if context.handle != -1:
        xbmcplugin.setResolvedUrl(context.handle, True, stream.ListItem)

    else:  # called from script use Player().play()
        xbmc.Player().play(item=stream.ListItem.getPath(), listitem=stream.ListItem)
