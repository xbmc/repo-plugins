# -*- coding: utf-8 -*-
"""
     
    Copyright (C) 2012-2018 Twitch-on-Kodi

    This file is part of Twitch-on-Kodi (plugin.video.twitch)

    SPDX-License-Identifier: GPL-3.0-only
    See LICENSES/GPL-3.0-only for more information.
"""

import traceback

from .addon import api
from .addon.common import kodi, log_utils
from .addon.common.url_dispatcher import URL_Dispatcher
from .addon.constants import MODES
from .addon.error_handling import error_handler
from .addon.utils import i18n

from twitch.api.parameters import StreamType, Platform

dispatcher = URL_Dispatcher()
twitch_api = None


@dispatcher.register(MODES.MAIN)
@error_handler
def _main():
    from .routes import main
    main.route(twitch_api)


@dispatcher.register(MODES.BROWSE)
@error_handler
def _browse():
    from .routes import browse
    browse.route()


@dispatcher.register(MODES.SEARCH)
@error_handler
def _search():
    from .routes import search
    search.route()


@dispatcher.register(MODES.LISTSEARCH, args=['content'])
@error_handler
def _search_history(content):
    from .routes import search_history
    search_history.route(content)


@dispatcher.register(MODES.NEWSEARCH, args=['content'])
@error_handler
def _new_search(content):
    from .routes import new_search
    new_search.route(content)


@dispatcher.register(MODES.SEARCHRESULTS, args=['content', 'query'], kwargs=['after'])
@error_handler(route_type=1)
def _search_results(content, query, after='MA=='):
    from .routes import search_results
    search_results.route(twitch_api, content, query, after)


@dispatcher.register(MODES.FOLLOWING)
@error_handler
def _following():
    from .routes import following
    following.route()


@dispatcher.register(MODES.FEATUREDSTREAMS)
@error_handler(route_type=1)
def _list_featured_streams():
    from .routes import popular_streams
    popular_streams.route(twitch_api)


@dispatcher.register(MODES.GAMES, kwargs=['after'])
@error_handler(route_type=1)
def _list_all_games(after='MA=='):
    from .routes import games
    games.route(twitch_api, after)


@dispatcher.register(MODES.STREAMLIST, kwargs=['after'])
@error_handler(route_type=1)
def _list_streams(after='MA=='):
    from .routes import streams
    streams.route(twitch_api, after)


@dispatcher.register(MODES.FOLLOWED, args=['content'], kwargs=['after'])
@error_handler(route_type=1)
def _list_followed(content, after='MA=='):
    from .routes import followed
    followed.route(twitch_api, content, after)


@dispatcher.register(MODES.CHANNELVIDEOS, kwargs=['channel_id', 'channel_name', 'display_name', 'game', 'game_name'])
@error_handler
def _list_channel_video_categories(channel_id=None, channel_name=None, display_name=None, game=None, game_name=None):
    from .routes import channel_video_categories
    channel_video_categories.route(channel_id, channel_name, display_name, game, game_name)


@dispatcher.register(MODES.COLLECTIONS, args=['channel_id'], kwargs=['cursor'])
@error_handler(route_type=1)
def _list_collections(channel_id, cursor='MA=='):
    from .routes import collections
    collections.route(twitch_api, channel_id, cursor)


@dispatcher.register(MODES.COLLECTIONVIDEOLIST, args=['collection_id'])
@error_handler(route_type=1)
def _list_collection_videos(collection_id):
    from .routes import collection_videos
    collection_videos.route(twitch_api, collection_id)


@dispatcher.register(MODES.CLIPSLIST, kwargs=['after', 'channel_id', 'game_id'])
@error_handler(route_type=1)
def _list_clips(after='MA==', channel_id='', game_id=''):
    from .routes import clips
    clips.route(twitch_api, after, channel_id, game_id)


@dispatcher.register(MODES.CHANNELVIDEOLIST, args=['broadcast_type'], kwargs=['after', 'channel_id', 'game'])
@error_handler(route_type=1)
def _list_channel_videos(broadcast_type, channel_id=None, game=None, after='MA=='):
    from .routes import channel_videos
    channel_videos.route(twitch_api, broadcast_type, channel_id, game, after)


@dispatcher.register(MODES.GAMELISTS, args=['game_id', 'game_name'])
@error_handler
def _game_lists(game_id, game_name):
    from .routes import game_categories
    game_categories.route(game_id, game_name)


@dispatcher.register(MODES.GAMESTREAMS, args=['game'], kwargs=['after'])
@error_handler(route_type=1)
def _list_game_streams(game, after='MA=='):
    from .routes import game_streams
    game_streams.route(twitch_api, game, after)


@dispatcher.register(MODES.PLAY, kwargs=['seek_time', 'channel_id', 'video_id', 'slug', 'ask', 'use_player', 'quality', 'channel_name'])
@error_handler
def _play(seek_time=0, channel_id=None, video_id=None, slug=None, ask=False, use_player=False, quality=None, channel_name=None):
    from .routes import play
    play.route(twitch_api, seek_time, channel_id, video_id, slug, ask, use_player, quality, channel_name)


@dispatcher.register(MODES.EDITFOLLOW, kwargs=['channel_id', 'channel_name', 'game_id', 'game_name', 'follow'])
@error_handler
def _edit_user_follows(channel_id=None, channel_name=None, game_id=None, game_name=None, follow=True):
    from .routes import edit_user_follows
    edit_user_follows.route(twitch_api, channel_id, channel_name, game_id, game_name, follow)


@dispatcher.register(MODES.EDITBLACKLIST, kwargs=['list_type', 'target_id', 'name', 'remove', 'refresh'])
@error_handler
def _edit_blacklist(list_type='user', target_id=None, name=None, remove=False, refresh=False):
    from .routes import edit_blacklist
    edit_blacklist.route(list_type, target_id, name, remove, refresh)


@dispatcher.register(MODES.EDITQUALITIES, args=['content_type'], kwargs=['video_id', 'target_id', 'name', 'remove', 'clip_id'])
@error_handler
def _edit_qualities(content_type, target_id=None, name=None, video_id=None, remove=False, clip_id=None):
    from .routes import edit_qualities
    edit_qualities.route(twitch_api, content_type, target_id, name, video_id, remove, clip_id)


@dispatcher.register(MODES.EDITSORTING, args=['list_type', 'sort_type'])
@error_handler
def _edit_sorting(list_type, sort_type):
    from .routes import edit_sorting
    edit_sorting.route(list_type, sort_type)


@dispatcher.register(MODES.EDITLANGUAGES, args=['action'])
@error_handler
def _edit_languages(action):
    from .routes import edit_languages
    edit_languages.route(action)


@dispatcher.register(MODES.CLEARLIST, args=['list_type', 'list_name'])
@error_handler
def _clear_list(list_type, list_name):
    from .routes import clear_list
    clear_list.route(list_type, list_name)


@dispatcher.register(MODES.REMOVESEARCHHISTORY, args=['search_type', 'query'], kwargs=['refresh'])
@error_handler
def _remove_search_history(search_type, query, refresh=True):
    from .routes import remove_search_history
    remove_search_history.route(search_type, query, refresh)


@dispatcher.register(MODES.CLEARSEARCHHISTORY, args=['search_type'], kwargs=['refresh'])
@error_handler
def _clear_search_history(search_type, refresh=False):
    from .routes import clear_search_history
    clear_search_history.route(search_type, refresh)


@dispatcher.register(MODES.REFRESH)
@error_handler
def _do_refresh():
    from .routes import refresh
    refresh.route()


@dispatcher.register(MODES.SETTINGS, kwargs=['refresh'])
@error_handler
def _settings(refresh=True):
    from .routes import settings
    settings.route(refresh)


@dispatcher.register(MODES.RESETCACHE)
@error_handler
def _reset_cache():
    from .routes import reset_cache
    reset_cache.route()


@dispatcher.register(MODES.INSTALLIRCCHAT)
@error_handler
def _install_ircchat():
    from .routes import install_ircchat
    install_ircchat.route()


@dispatcher.register(MODES.CONFIGUREIA)
@error_handler
def _configure_ia():
    from .routes import configure_inputstream_adaptive
    configure_inputstream_adaptive.route()


@dispatcher.register(MODES.TOKENURL)
@error_handler
def _get_token_url():
    from .routes import token_url
    token_url.route(twitch_api)


@dispatcher.register(MODES.REVOKETOKEN)
@error_handler
def _revoke_token():
    from .routes import revoke_token
    revoke_token.route(twitch_api)


@dispatcher.register(MODES.UPDATETOKEN, args=['oauth_token'])
@error_handler
def _update_token(oauth_token):
    from .routes import update_token
    update_token.route(oauth_token)


@dispatcher.register(MODES.MAINTAIN, args=['sub_mode', 'file_type'])
@error_handler
def _maintain(sub_mode, file_type):
    from .routes import maintain
    maintain.route(sub_mode, file_type)


def run(argv):
    queries = kodi.parse_query(argv[2])
    log_utils.log('Version: |%s| Application Version: %s' % (kodi.get_version(), kodi.get_kodi_version()), log_utils.LOGDEBUG)
    log_utils.log('Queries: |%s| Args: |%s|' % (queries, argv), log_utils.LOGDEBUG)

    # don't process params that don't match our url exactly
    plugin_url = 'plugin://%s/' % kodi.get_id()
    if argv[0] != plugin_url:
        return
    try:
        global twitch_api
        twitch_api = api.Twitch()
    except:
        kodi.notify(i18n('connection_failed'), i18n('failed_connect_api'))
        log_utils.log(traceback.print_exc(), log_utils.LOGERROR)
        return

    mode = queries.get('mode', None)
    dispatcher.dispatch(mode, queries)
