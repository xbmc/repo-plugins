# -*- coding: utf-8 -*-
"""
    Copyright (C) 2020 Tubed (plugin.video.tubed)

    This file is part of plugin.video.tubed

    SPDX-License-Identifier: GPL-2.0-only
    See LICENSES/GPL-2.0-only.txt for more information.
"""

from copy import deepcopy
from html import unescape
from urllib.parse import quote

import arrow
from infotagger.listitem import ListItemInfoTag  # pylint: disable=import-error

from ..constants import ADDON_ID
from ..constants import MODES
from ..constants import SCRIPT_MODES
from ..items.action import Action
from ..items.video import Video
from ..lib.time import iso8601_duration_to_seconds
from ..lib.txt_fmt import bold
from ..lib.url_utils import create_addon_path
from ..storage.users import UserStorage
from .data_cache import get_cached
from .data_cache import get_fanart
from .utils import get_chapters
from .utils import get_thumbnail


def video_generator(context, items, mine=False):
    event_type = ''

    if context.mode == str(MODES.LIVE):
        event_type = context.query.get('event_type', '')

    cached_videos = get_cached_videos(context, items, event_type)

    fanart = get_fanart(
        context,
        context.api.channels,
        [item.get('snippet', {}).get('channelId')
         for _, item in cached_videos.items()
         if item.get('snippet', {}).get('channelId')],
        cache_ttl=context.settings.data_cache_ttl
    )

    has_channel_mine = False
    if context.api.logged_in:
        has_channel_mine = context.api.channel_by_username('mine') != {}

    users = UserStorage()

    for item in items:
        video_id = get_id(item)

        if not video_id:
            continue

        video = cached_videos.get(video_id, {})

        snippet = video.get('snippet', {})
        if not snippet:
            continue

        info_labels = get_info_labels(video, snippet)

        channel_id = info_labels.pop('channel_id', '')
        scheduled_start = info_labels.pop('scheduled_start', '')
        chapters = info_labels.pop('chapters', [])

        if event_type == 'upcoming':
            payload = Action(
                label=info_labels.get('originaltitle', ''),
                label2=','.join(info_labels.get('studio', [''])),
                path=create_addon_path({
                    'mode': str(MODES.UPCOMING_NOTIFICATION),
                    'title': quote(info_labels.get('originaltitle', '')),
                    'timestamp': scheduled_start
                })
            )
        else:
            payload = Video(
                label=info_labels.get('originaltitle', ''),
                label2=','.join(info_labels.get('studio', [''])),
                path=create_addon_path({
                    'mode': str(MODES.PLAY),
                    'video_id': video_id,
                    'uuid': users.uuid
                })
            )

        info_tag = ListItemInfoTag(payload.ListItem, 'video')
        info_tag.set_info(info_labels)

        thumbnail = get_thumbnail(snippet)

        payload.ListItem.setArt({
            'icon': thumbnail,
            'thumb': thumbnail,
            'fanart': fanart.get(channel_id, ''),
        })

        context_menus = get_context_menu(context, users, item, video_id,
                                         info_labels.get('originaltitle', ''),
                                         channel_id, info_labels.get('studio', [''])[0],
                                         event_type, mine, has_channel_mine, chapters)

        payload.ListItem.addContextMenuItems(context_menus)

        payload.ListItem.setProperty('video_id', video_id)

        yield tuple(payload)


def get_id(item):
    kind = item.get('kind', '')
    if kind == 'youtube#video':
        return item.get('id', '')

    if kind == 'youtube#playlistItem':
        return item.get('snippet', {}).get('resourceId', {}).get('videoId', '')

    if kind == 'youtube#searchResult':
        if isinstance(item.get('id', {}), dict):
            return item.get('id', {}).get('videoId', '')

    return ''


def get_info_labels(video, snippet):
    content_details = video.get('contentDetails', {})
    statistics = video.get('statistics', {})

    duration = iso8601_duration_to_seconds(content_details.get('duration', ''))

    channel_id = snippet.get('channelId', '')
    channel_name = unescape(snippet.get('channelTitle', ''))

    video_title = unescape(snippet.get('title', ''))

    published_arrow = None
    scheduled_start = None
    live_details = video.get('liveStreamingDetails')

    if live_details:
        actual_start = live_details.get('actualStartTime')
        actual_end = live_details.get('actualEndTime')
        scheduled_start = live_details.get('scheduledStartTime')

        published = actual_end or actual_start or scheduled_start
        if published:
            published_arrow = arrow.get(published).to('local')

    if not published_arrow:
        published_arrow = arrow.get(snippet['publishedAt']).to('local')

    votes = int(statistics.get('likeCount', '0')) + int(statistics.get('dislikeCount', '0'))
    try:
        rating = '%0.1f' % ((int(statistics.get('likeCount', '0')) / votes) * 10)
    except ZeroDivisionError:
        rating = '0.0'

    description = unescape(snippet.get('description', ''))

    info_labels = {
        'mediatype': 'video',
        'plot': description,
        'plotoutline': description,
        'originaltitle': video_title,
        'sorttitle': video_title,
        'studio': [channel_name],
        'year': published_arrow.year,
        'premiered': published_arrow.format('YYYY-MM-DD'),
        'dateadded': published_arrow.format('YYYY-MM-DD HH:mm:ss'),
        'tag': snippet.get('tags', []),
        'rating': rating,
        'votes': votes,
        'channel_id': channel_id,
        'scheduled_start': scheduled_start,
        'chapters': get_chapters(description)
    }

    if duration:
        info_labels['duration'] = duration

    if snippet.get('liveBroadcastContent', 'none') != 'none':
        info_labels['playcount'] = '0'

    return info_labels


def get_cached_videos(context, items, event_type):
    if event_type == 'upcoming':
        # don't add upcoming video items to long term cache since
        # they will change when in progress or completed
        cached_videos = {}

        videos = context.api.videos(
            [get_id(item) for item in items if get_id(item)],
            live_details=True
        )

        for video in videos.get('items', []):
            cached_videos[get_id(video)] = video

    else:
        parameters = None
        if event_type in ['live', 'completed']:
            parameters = {
                'live_details': True,
            }

        cached_videos = get_cached(
            context,
            context.api.videos,
            [get_id(item) for item in items if get_id(item)],
            parameters,
            cache_ttl=context.settings.data_cache_ttl
        )

    return cached_videos


def get_context_menu(context, users, item, video_id, video_title, channel_id,  # pylint: disable=too-many-arguments
                     channel_name, event_type, mine, has_channel_mine, chapters):
    logged_in = context.api.logged_in

    context_menus = []
    kind = item.get('kind', '')
    snippet = item.get('snippet', {})
    playlist_id = snippet.get('playlistId', '')

    if kind == 'youtube#searchResult' or event_type:
        query = deepcopy(context.query)
        query['order'] = 'prompt'
        context_menus += [
            (context.i18n('Sort order'),
             'Container.Update(%s)' % create_addon_path(query))
        ]

    if logged_in:
        watch_later_playlist = users.watchlater_playlist
        if (((watch_later_playlist and watch_later_playlist != playlist_id) or
             not watch_later_playlist) and has_channel_mine):

            watch_later_playlist = watch_later_playlist or 'watch_later_prompt'
            context_menus += [
                (context.i18n('Add to watch later'),
                 'RunScript(%s,mode=%s&action=add&video_id=%s&playlist_id=%s&playlist_title=%s)' %
                 (ADDON_ID, str(SCRIPT_MODES.PLAYLIST), video_id,
                  watch_later_playlist, quote(context.i18n('Watch Later')))),
            ]

        context_menus += [
            (context.i18n('Subscribe'),
             'RunScript(%s,mode=%s&action=add&channel_id=%s&channel_name=%s)' %
             (ADDON_ID, str(SCRIPT_MODES.SUBSCRIPTIONS), channel_id, quote(channel_name))),
        ]

    if event_type != 'upcoming':
        if logged_in:
            context_menus += [
                (context.i18n('Rate'),
                 'RunScript(%s,mode=%s&video_id=%s)' %
                 (ADDON_ID, str(SCRIPT_MODES.RATE), video_id)),
            ]

            if has_channel_mine:
                context_menus += [
                    (context.i18n('Add to playlist'),
                     'RunScript(%s,mode=%s&action=add&video_id=%s)' %
                     (ADDON_ID, str(SCRIPT_MODES.PLAYLIST), video_id)),
                ]

            if mine and snippet and playlist_id:
                context_menus += [
                    (context.i18n('Remove from playlist'),
                     'RunScript(%s,mode=%s&action=remove&playlistitem_id=%s&video_title=%s)' %
                     (ADDON_ID, str(SCRIPT_MODES.PLAYLIST), item['id'], quote(video_title)))
                ]

    if context.settings.favorite_channel_maximum > 0:
        context_menus += [
            (context.i18n('Add %s to favorite channels') % bold(channel_name),
             'RunScript(%s,mode=%s&action=add&channel_id=%s&channel_name=%s)' %
             (ADDON_ID, str(SCRIPT_MODES.FAVORITE_CHANNELS), channel_id, quote(channel_name))),
        ]

    if playlist_id:
        if context.settings.favorite_playlist_maximum > 0:
            context_menus += [
                (context.i18n('Add to favorite playlists'),
                 'RunScript(%s,mode=%s&action=add&playlist_id=%s)' %
                 (ADDON_ID, str(SCRIPT_MODES.FAVORITE_PLAYLISTS), playlist_id)),
            ]

    context_menus += [
        (context.i18n('Related videos'),
         'Container.Update(plugin://%s/?mode=%s&video_id=%s)' %
         (ADDON_ID, str(MODES.RELATED_VIDEOS), video_id)),

        (context.i18n('Links in the description'),
         'Container.Update(plugin://%s/?mode=%s&video_id=%s)' %
         (ADDON_ID, str(MODES.LINKS_IN_DESCRIPTION), video_id)),

        (context.i18n('Go to %s') % bold(channel_name),
         'Container.Update(plugin://%s/?mode=%s&channel_id=%s)' %
         (ADDON_ID, str(MODES.CHANNEL), channel_id)),

        (context.i18n('Comments'),
         'Container.Update(plugin://%s/?mode=%s&video_id=%s)' %
         (ADDON_ID, str(MODES.COMMENTS_THREADS), video_id)),
    ]

    context_menus += [
        (context.i18n('Refresh'), 'RunScript(%s,mode=%s)' % (ADDON_ID, str(SCRIPT_MODES.REFRESH))),
    ]

    if chapters:
        context_menus += [
            (context.i18n('Chapters'),
             'PlayMedia(plugin://%s/?mode=%s&video_id=%s)' %
             (ADDON_ID, str(MODES.CHAPTERS), video_id)),
        ]

    if event_type != 'upcoming':
        context_menus += [
            (context.i18n('Play (Prompt for subtitles)'),
             'PlayMedia(plugin://%s/?mode=%s&video_id=%s&prompt_subtitles=true&uuid=%s)' %
             (ADDON_ID, str(MODES.PLAY), video_id, users.uuid)),
        ]

    if playlist_id:
        context_menus += [
            (context.i18n('Play from %s') % bold(video_title),
             'RunScript(%s,mode=%s&playlist_id=%s&video_id=%s)' %
             (ADDON_ID, str(SCRIPT_MODES.PLAY), playlist_id, video_id)),
        ]

    return context_menus
