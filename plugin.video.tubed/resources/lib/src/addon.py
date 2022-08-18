# -*- coding: utf-8 -*-
"""
    Copyright (C) 2020 Tubed (plugin.video.tubed)

    This file is part of plugin.video.tubed

    SPDX-License-Identifier: GPL-2.0-only
    See LICENSES/GPL-2.0-only.txt for more information.
"""

import sys

from .api import API
from .constants import MODES
from .lib.context import Context
from .lib.logger import Log
from .lib.privacy_policy import show_privacy_policy
from .lib.routing import Router
from .lib.url_utils import parse_query

# pylint: disable=import-outside-toplevel

CONTEXT = None
LOG = Log('entrypoint', __file__)

router = Router()


@router.route(MODES.MAIN)
def _main_menu():
    from .routes import main_menu
    main_menu.invoke(CONTEXT)


@router.route(MODES.SIGN_IN)
def _sign_in():
    from .routes import sign_in
    sign_in.invoke(CONTEXT)


@router.route(MODES.SIGN_OUT)
def _sign_out():
    from .routes import sign_out
    sign_out.invoke(CONTEXT)


@router.route(MODES.MANAGE_USERS)
def _manage_users():
    from .routes import manage_users
    manage_users.invoke(CONTEXT)


@router.route(MODES.MOST_POPULAR, kwargs=['page_token', 'region_code'])
def _most_popular(page_token='', region_code=''):
    from .routes import most_popular
    most_popular.invoke(CONTEXT, page_token=page_token, region_code=region_code)


@router.route(MODES.MOST_POPULAR_REGIONALLY)
def _most_popular_regionally():
    from .routes import most_popular_regionally
    most_popular_regionally.invoke(CONTEXT)


@router.route(MODES.CHAPTERS, args=['video_id'])
def _chapters(video_id):
    from .routes import chapters
    chapters.invoke(CONTEXT, video_id)


@router.route(MODES.LIKED_VIDEOS, kwargs=['page_token'])
def _liked_videos(page_token=''):
    from .routes import liked_videos
    liked_videos.invoke(CONTEXT, page_token=page_token)


@router.route(MODES.DISLIKED_VIDEOS, kwargs=['page_token'])
def _disliked_videos(page_token=''):
    from .routes import disliked_videos
    disliked_videos.invoke(CONTEXT, page_token=page_token)


@router.route(MODES.LIVE, kwargs=['page_token', 'event_type', 'order'])
def _live(page_token='', event_type='live', order='relevance'):
    from .routes import live
    live.invoke(CONTEXT, page_token=page_token, event_type=event_type, order=order)


@router.route(MODES.UPCOMING_NOTIFICATION, args=['title', 'timestamp'])
def _upcoming_notification(title, timestamp):
    from .routes import upcoming_notification
    upcoming_notification.invoke(CONTEXT, title=title, timestamp=timestamp)


@router.route(MODES.SUBSCRIPTIONS, kwargs=['page_token', 'order'])
def _subscriptions(page_token='', order='alphabetical'):
    from .routes import subscriptions
    subscriptions.invoke(CONTEXT, page_token=page_token, order=order)


@router.route(MODES.RELATED_VIDEOS, args=['video_id'], kwargs=['page_token'])
def _related_videos(video_id, page_token=''):
    from .routes import related_videos
    related_videos.invoke(CONTEXT, video_id, page_token=page_token)


@router.route(MODES.CHANNEL, args=['channel_id'], kwargs=['page_token'])
def _channel(channel_id, page_token=''):
    # alias of MODES.PLAYLISTS
    from .routes import playlists
    playlists.invoke(CONTEXT, channel_id, page_token=page_token)


@router.route(MODES.PLAYLISTS, args=['channel_id'], kwargs=['page_token'])
def _playlists(channel_id, page_token=''):
    from .routes import playlists
    playlists.invoke(CONTEXT, channel_id, page_token=page_token)


@router.route(MODES.PLAYLIST, args=['playlist_id'], kwargs=['page_token', 'mine'])
def _playlist(playlist_id, page_token='', mine=False):
    from .routes import playlist
    playlist.invoke(CONTEXT, playlist_id, page_token, mine)


@router.route(MODES.PLAY, kwargs=['video_id', 'playlist_id', 'prompt_subtitles', 'start_offset'])
def _play(video_id='', playlist_id='', prompt_subtitles=False, start_offset=None):
    from .routes import play
    play.invoke(CONTEXT, video_id, playlist_id, prompt_subtitles, start_offset)


@router.route(MODES.FAVORITE_CHANNELS, kwargs=['page'])
def _favorite_channels(page=1):
    from .routes import favorite_channels
    favorite_channels.invoke(CONTEXT, page)


@router.route(MODES.FAVORITE_PLAYLISTS, kwargs=['page'])
def _favorite_playlists(page=1):
    from .routes import favorite_playlists
    favorite_playlists.invoke(CONTEXT, page)


@router.route(MODES.SEARCH)
def _search():
    from .routes import search
    search.invoke(CONTEXT)


@router.route(MODES.SEARCH_QUERY, kwargs=['page_token', 'query', 'search_type',
                                          'order', 'channel_id'])
def _search_query(query='', page_token='', search_type='video', order='relevance', channel_id=None):
    from .routes import search_query
    search_query.invoke(CONTEXT, query, page_token, search_type, order, channel_id)


@router.route(MODES.MY_CHANNEL, kwargs=['page_token'])
def _my_channel(page_token=''):
    from .routes import my_channel
    my_channel.invoke(CONTEXT, page_token)


@router.route(MODES.CATEGORIES, kwargs=['page_token'])
def _categories(page_token=''):
    from .routes import categories
    categories.invoke(CONTEXT, page_token)


@router.route(MODES.READ_COMMENT, kwargs=['thread_id', 'comment_id'])
def _read_comment(thread_id='', comment_id=''):
    from .routes import read_comment
    read_comment.invoke(CONTEXT, thread_id, comment_id)


@router.route(MODES.COMMENTS, args=['thread_id'], kwargs=['page_token'])
def _comments(thread_id, page_token=''):
    from .routes import comments
    comments.invoke(CONTEXT, thread_id, page_token)


@router.route(MODES.COMMENTS_THREADS, args=['video_id'], kwargs=['page_token', 'order'])
def _comment_threads(video_id, page_token='', order='relevance'):
    from .routes import comment_threads
    comment_threads.invoke(CONTEXT, video_id, page_token, order)


@router.route(MODES.LINKS_IN_DESCRIPTION, args=['video_id'])
def _links_in_description(video_id):
    from .routes import links_in_description
    links_in_description.invoke(CONTEXT, video_id)


@router.route(MODES.CATEGORY, args=['category_id'], kwargs=['page_token'])
def _category(category_id, page_token=''):
    from .routes import category
    category.invoke(CONTEXT, category_id, page_token)


@router.route(MODES.SETTINGS)
def _settings():
    from .routes import settings
    settings.invoke(CONTEXT)


def invoke(argv):
    global CONTEXT  # pylint: disable=global-statement

    CONTEXT = Context()

    CONTEXT.argv = argv
    CONTEXT.handle = argv[1]

    CONTEXT.query = parse_query(argv[2])
    CONTEXT.mode = CONTEXT.query.get('mode', str(MODES.MAIN))

    LOG.debug(
        'Invoker:\n  Handle: %s\n  Mode: %s\n  Parameters: %s\n' %
        (str(CONTEXT.handle), CONTEXT.mode, CONTEXT.query)
    )

    privacy_policy_accepted = show_privacy_policy(CONTEXT)

    if not privacy_policy_accepted:
        sys.exit(1)

    CONTEXT.api = API(
        language=CONTEXT.settings.language,
        region=CONTEXT.settings.region
    )

    router.invoke(CONTEXT.query)
