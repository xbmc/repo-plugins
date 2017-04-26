# -*- coding: utf-8 -*-
"""
     
    Copyright (C) 2016 Twitch-on-Kodi
    
    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.
    
    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
    GNU General Public License for more details.
    
    You should have received a copy of the GNU General Public License
    along with this program. If not, see <http://www.gnu.org/licenses/>.
"""

import sys
import traceback
from addon import utils, api, menu_items, cache
from addon.common import kodi, log_utils
from addon.common.url_dispatcher import URL_Dispatcher
from addon.converter import JsonListItemConverter
from addon.constants import MODES, LINE_LENGTH, LIVE_PREVIEW_TEMPLATE, Keys, REQUEST_LIMIT, CURSOR_LIMIT, MAX_REQUESTS
from addon.googl_shorten import googl_url
from addon.error_handling import error_handler
from addon.twitch_exceptions import SubRequired, NotFound, PlaybackFailed, TwitchException
from twitch.api.parameters import Boolean, Period, ClipPeriod, Direction, SortBy, VideoSort, Language, StreamType, Platform

i18n = utils.i18n
dispatcher = URL_Dispatcher()
converter = JsonListItemConverter(LINE_LENGTH)
blacklist_filter = utils.BlacklistFilter()
twitch = None


@dispatcher.register(MODES.MAIN)
@error_handler
def main():
    has_token = True if twitch.access_token else False
    kodi.set_content('files')
    show_menu = utils.show_menu

    if show_menu('featured'):
        context_menu = list()
        context_menu.extend(menu_items.clear_previews())
        kodi.create_item({'label': i18n('featured_streams'), 'path': {'mode': MODES.FEATUREDSTREAMS}, 'context_menu': context_menu,
                          'info': {'plot': i18n('featured_streams')}})
    if has_token:
        if show_menu('live', 'following'):
            context_menu = list()
            context_menu.extend(menu_items.clear_previews())
            kodi.create_item(
                {'label': '%s %s' % (i18n('following'), i18n('live_channels')), 'path': {'mode': MODES.FOLLOWED, 'content': StreamType.LIVE}, 'context_menu': context_menu,
                 'info': {'plot': '%s - %s' % (i18n('following'), i18n('live_channels'))}})
        if show_menu('playlists', 'following'):
            kodi.create_item({'label': '%s %s' % (i18n('following'), i18n('playlists')), 'path': {'mode': MODES.FOLLOWED, 'content': StreamType.PLAYLIST},
                              'info': {'plot': '%s - %s' % (i18n('following'), i18n('playlists'))}})
        if show_menu('channels', 'following'):
            context_menu = list()
            context_menu.extend(menu_items.change_sort_by('followed_channels'))
            context_menu.extend(menu_items.change_direction('followed_channels'))
            kodi.create_item({'label': '%s %s' % (i18n('following'), i18n('channels')), 'path': {'mode': MODES.FOLLOWED, 'content': 'channels'}, 'context_menu': context_menu,
                              'info': {'plot': '%s - %s' % (i18n('following'), i18n('channels'))}})
        if show_menu('games', 'following'):
            kodi.create_item({'label': '%s %s' % (i18n('following'), i18n('games')), 'path': {'mode': MODES.FOLLOWED, 'content': 'games'},
                              'info': {'plot': '%s - %s' % (i18n('following'), i18n('games'))}})
        if show_menu('clips', 'following'):
            context_menu = list()
            context_menu.extend(menu_items.change_sort_by('clips'))
            kodi.create_item({'label': '%s %s' % (i18n('following'), i18n('clips')), 'path': {'mode': MODES.FOLLOWED, 'content': 'clips'}, 'context_menu': context_menu,
                              'info': {'plot': '%s - %s' % (i18n('following'), i18n('clips'))}})
        if show_menu('following'):
            kodi.create_item({'label': i18n('following'), 'path': {'mode': MODES.FOLLOWING}, 'info': {'plot': i18n('following')}})
    if show_menu('live', 'browse'):
        context_menu = list()
        context_menu.extend(menu_items.clear_previews())
        kodi.create_item({'label': '%s %s' % (i18n('browse'), i18n('live_channels')), 'path': {'mode': MODES.STREAMLIST, 'stream_type': StreamType.LIVE},
                          'context_menu': context_menu, 'info': {'plot': '%s - %s' % (i18n('browse'), i18n('live_channels'))}})
    if show_menu('playlists', 'browse'):
        kodi.create_item({'label': '%s %s' % (i18n('browse'), i18n('playlists')), 'path': {'mode': MODES.STREAMLIST, 'stream_type': StreamType.PLAYLIST},
                          'info': {'plot': '%s - %s' % (i18n('browse'), i18n('playlists'))}})
    if show_menu('xbox_one', 'browse'):
        context_menu = list()
        context_menu.extend(menu_items.clear_previews())
        kodi.create_item({'label': '%s %s' % (i18n('browse'), i18n('xbox_one')), 'path': {'mode': MODES.STREAMLIST, 'platform': Platform.XBOX_ONE},
                          'context_menu': context_menu, 'info': {'plot': '%s - %s' % (i18n('browse'), i18n('xbox_one'))}})
    if show_menu('ps4', 'browse'):
        context_menu = list()
        context_menu.extend(menu_items.clear_previews())
        kodi.create_item({'label': '%s %s' % (i18n('browse'), i18n('ps4')), 'path': {'mode': MODES.STREAMLIST, 'platform': Platform.PS4}, 'context_menu': context_menu,
                          'info': {'plot': '%s - %s' % (i18n('browse'), i18n('ps4'))}})
    if show_menu('videos', 'browse'):
        kodi.create_item({'label': '%s %s' % (i18n('browse'), i18n('videos')), 'path': {'mode': MODES.CHANNELVIDEOS, 'channel_id': 'all'},
                          'info': {'plot': '%s - %s' % (i18n('browse'), i18n('videos'))}})
    if show_menu('clips', 'browse'):
        context_menu = list()
        context_menu.extend(menu_items.change_sort_by('clips'))
        context_menu.extend(menu_items.change_period('clips'))
        kodi.create_item({'label': '%s %s' % (i18n('browse'), i18n('clips')), 'path': {'mode': MODES.CLIPSLIST}, 'context_menu': context_menu,
                          'info': {'plot': '%s - %s' % (i18n('browse'), i18n('clips'))}})
    if show_menu('communities', 'browse'):
        kodi.create_item({'label': '%s %s' % (i18n('browse'), i18n('communities')), 'path': {'mode': MODES.COMMUNITIES},
                          'info': {'plot': '%s - %s' % (i18n('browse'), i18n('communities'))}})
    if show_menu('games', 'browse'):
        kodi.create_item({'label': '%s %s' % (i18n('browse'), i18n('games')), 'path': {'mode': MODES.GAMES},
                          'info': {'plot': '%s - %s' % (i18n('browse'), i18n('games'))}})
    if show_menu('browse'):
        kodi.create_item({'label': i18n('browse'), 'path': {'mode': MODES.BROWSE}, 'info': {'plot': i18n('browse')}})
    if show_menu('streams', 'search'):
        context_menu = list()
        context_menu.extend(menu_items.clear_previews())
        kodi.create_item({'label': '%s %s' % (i18n('search'), i18n('streams')), 'path': {'mode': MODES.NEWSEARCH, 'content': 'streams'}, 'context_menu': context_menu,
                          'info': {'plot': '%s - %s' % (i18n('search'), i18n('streams'))}})
    if show_menu('channels', 'search'):
        kodi.create_item({'label': '%s %s' % (i18n('search'), i18n('channels')), 'path': {'mode': MODES.NEWSEARCH, 'content': 'channels'},
                          'info': {'plot': '%s - %s' % (i18n('search'), i18n('channels'))}})
    if show_menu('games', 'search'):
        kodi.create_item({'label': '%s %s' % (i18n('search'), i18n('games')), 'path': {'mode': MODES.NEWSEARCH, 'content': 'games'},
                          'info': {'plot': '%s - %s' % (i18n('search'), i18n('games'))}})
    if show_menu('url', 'search'):
        kodi.create_item({'label': '%s %s' % (i18n('search'), i18n('video_id_url')), 'path': {'mode': MODES.NEWSEARCH, 'content': 'id_url'},
                          'info': {'plot': '%s - %s[CR]%s' % (i18n('search'), i18n('video_id_url'), i18n('search_id_url_description'))}})
    if show_menu('search'):
        kodi.create_item({'label': i18n('search'), 'path': {'mode': MODES.SEARCH}, 'info': {'plot': i18n('search')}})
    if show_menu('settings'):
        kodi.create_item({'label': i18n('settings'), 'path': {'mode': MODES.SETTINGS}, 'info': {'plot': i18n('settings')}})
    kodi.end_of_directory()


@dispatcher.register(MODES.BROWSE)
@error_handler
def browse():
    kodi.set_content('files')
    context_menu = list()
    context_menu.extend(menu_items.clear_previews())
    kodi.create_item({'label': i18n('live_channels'), 'path': {'mode': MODES.STREAMLIST, 'stream_type': StreamType.LIVE},
                      'context_menu': context_menu, 'info': {'plot': '%s - %s' % (i18n('browse'), i18n('live_channels'))}})
    kodi.create_item({'label': i18n('playlists'), 'path': {'mode': MODES.STREAMLIST, 'stream_type': StreamType.PLAYLIST},
                      'info': {'plot': '%s - %s' % (i18n('browse'), i18n('playlists'))}})
    kodi.create_item({'label': i18n('xbox_one'), 'path': {'mode': MODES.STREAMLIST, 'platform': Platform.XBOX_ONE},
                      'context_menu': context_menu, 'info': {'plot': '%s - %s' % (i18n('browse'), i18n('xbox_one'))}})
    kodi.create_item({'label': i18n('ps4'), 'path': {'mode': MODES.STREAMLIST, 'platform': Platform.PS4}, 'context_menu': context_menu,
                      'info': {'plot': '%s - %s' % (i18n('browse'), i18n('ps4'))}})
    kodi.create_item({'label': i18n('videos'), 'path': {'mode': MODES.CHANNELVIDEOS, 'channel_id': 'all'},
                      'info': {'plot': '%s - %s' % (i18n('browse'), i18n('videos'))}})
    context_menu = list()
    context_menu.extend(menu_items.change_sort_by('clips'))
    context_menu.extend(menu_items.change_period('clips'))
    kodi.create_item({'label': i18n('clips'), 'path': {'mode': MODES.CLIPSLIST}, 'context_menu': context_menu,
                      'info': {'plot': '%s - %s' % (i18n('browse'), i18n('clips'))}})
    kodi.create_item({'label': i18n('communities'), 'path': {'mode': MODES.COMMUNITIES},
                      'info': {'plot': '%s - %s' % (i18n('browse'), i18n('communities'))}})
    kodi.create_item({'label': i18n('games'), 'path': {'mode': MODES.GAMES},
                      'info': {'plot': '%s - %s' % (i18n('browse'), i18n('games'))}})
    kodi.end_of_directory()


@dispatcher.register(MODES.SEARCH)
@error_handler
def search():
    kodi.set_content('files')
    context_menu = list()
    context_menu.extend(menu_items.clear_previews())
    kodi.create_item({'label': i18n('streams'), 'path': {'mode': MODES.NEWSEARCH, 'content': 'streams'}, 'context_menu': context_menu,
                      'info': {'plot': '%s - %s' % (i18n('search'), i18n('streams'))}})
    kodi.create_item({'label': i18n('channels'), 'path': {'mode': MODES.NEWSEARCH, 'content': 'channels'},
                      'info': {'plot': '%s - %s' % (i18n('search'), i18n('channels'))}})
    kodi.create_item({'label': i18n('games'), 'path': {'mode': MODES.NEWSEARCH, 'content': 'games'},
                      'info': {'plot': '%s - %s' % (i18n('search'), i18n('games'))}})
    kodi.create_item({'label': i18n('video_id_url'), 'path': {'mode': MODES.NEWSEARCH, 'content': 'id_url'},
                      'info': {'plot': '%s - %s[CR]%s' % (i18n('search'), i18n('video_id_url'), i18n('search_id_url_description'))}})
    kodi.end_of_directory()


@dispatcher.register(MODES.NEWSEARCH, args=['content'])
@error_handler
def new_search(content):
    kodi.set_content('files')
    user_input = kodi.get_keyboard(i18n('search'))
    if user_input:
        kodi.end_of_directory()
        kodi.update_container(kodi.get_plugin_url({'mode': MODES.SEARCHRESULTS, 'content': content, 'query': user_input, 'index': 0}))
    else:
        return


@dispatcher.register(MODES.SEARCHRESULTS, args=['content', 'query'], kwargs=['index'])
@error_handler
def search_results(content, query, index=0):
    if content == 'streams':
        utils.refresh_previews()
        kodi.set_content('videos')
        index, offset, limit = utils.calculate_pagination_values(index)
        results = twitch.get_stream_search(search_query=query, offset=offset, limit=limit)
        if (results[Keys.TOTAL] > 0) and (Keys.STREAMS in results):
            for stream in results[Keys.STREAMS]:
                kodi.create_item(converter.stream_to_listitem(stream))
            if results[Keys.TOTAL] > (offset + limit):
                kodi.create_item(utils.link_to_next_page({'mode': MODES.SEARCHRESULTS, 'content': content, 'query': query, 'index': index}))
            kodi.end_of_directory()
        else:
            kodi.update_container(kodi.get_plugin_url({'mode': MODES.SEARCH}))
    elif content == 'channels':
        kodi.set_content('files')
        index, offset, limit = utils.calculate_pagination_values(index)
        results = twitch.get_channel_search(search_query=query, offset=offset, limit=limit)
        if (results[Keys.TOTAL] > 0) and (Keys.CHANNELS in results):
            for channel in results[Keys.CHANNELS]:
                kodi.create_item(converter.channel_to_listitem(channel))
            if results[Keys.TOTAL] > (offset + limit):
                kodi.create_item(utils.link_to_next_page({'mode': MODES.SEARCHRESULTS, 'content': content, 'query': query, 'index': index}))
            kodi.end_of_directory()
        else:
            kodi.update_container(kodi.get_plugin_url({'mode': MODES.SEARCH}))
    elif content == 'games':
        kodi.set_content('files')
        results = twitch.get_game_search(search_query=query)
        if (Keys.GAMES in results) and (results[Keys.GAMES]):
            for game in results[Keys.GAMES]:
                kodi.create_item(converter.game_to_listitem(game))
            kodi.end_of_directory()
        else:
            kodi.update_container(kodi.get_plugin_url({'mode': MODES.SEARCH}))
    elif content == 'id_url':
        kodi.set_content('videos')
        video_id, seek_time = utils.extract_video(query)
        results = twitch.get_video_by_id(video_id)
        if video_id.startswith('a') or video_id.startswith('c') or video_id.startswith('v'):
            window = kodi.Window(10000)
            if seek_time > 0:
                window.setProperty(kodi.get_id() + '-_seek', '%s,%d' % (video_id, seek_time))
            else:
                window.clearProperty(kodi.get_id() + '-_seek')
            kodi.create_item(converter.video_list_to_listitem(results))
            kodi.end_of_directory()
        else:
            kodi.update_container(kodi.get_plugin_url({'mode': MODES.SEARCH}))
    else:
        kodi.update_container(kodi.get_plugin_url({'mode': MODES.SEARCH}))


@dispatcher.register(MODES.FOLLOWING)
@error_handler
def following():
    kodi.set_content('files')
    context_menu = list()
    context_menu.extend(menu_items.clear_previews())
    kodi.create_item({'label': i18n('live_channels'), 'path': {'mode': MODES.FOLLOWED, 'content': StreamType.LIVE}, 'context_menu': context_menu,
                      'info': {'plot': '%s - %s' % (i18n('following'), i18n('live_channels'))}})
    kodi.create_item({'label': i18n('playlists'), 'path': {'mode': MODES.FOLLOWED, 'content': StreamType.PLAYLIST},
                      'info': {'plot': '%s - %s' % (i18n('following'), i18n('playlists'))}})
    context_menu = list()
    context_menu.extend(menu_items.change_sort_by('followed_channels'))
    context_menu.extend(menu_items.change_direction('followed_channels'))
    kodi.create_item({'label': i18n('channels'), 'path': {'mode': MODES.FOLLOWED, 'content': 'channels'}, 'context_menu': context_menu,
                      'info': {'plot': '%s - %s' % (i18n('following'), i18n('channels'))}})
    kodi.create_item({'label': i18n('games'), 'path': {'mode': MODES.FOLLOWED, 'content': 'games'},
                      'info': {'plot': '%s - %s' % (i18n('following'), i18n('games'))}})
    context_menu = list()
    context_menu.extend(menu_items.change_sort_by('clips'))
    kodi.create_item({'label': i18n('clips'), 'path': {'mode': MODES.FOLLOWED, 'content': 'clips'}, 'context_menu': context_menu,
                      'info': {'plot': '%s - %s' % (i18n('following'), i18n('clips'))}})
    kodi.end_of_directory()


@dispatcher.register(MODES.FEATUREDSTREAMS)
@error_handler
def list_featured_streams():
    utils.refresh_previews()
    kodi.set_content('videos')
    streams = twitch.get_featured_streams(offset=0, limit=100)
    if Keys.FEATURED in streams:
        filtered = \
            blacklist_filter.by_type(streams, Keys.FEATURED, parent_keys=[Keys.STREAM, Keys.CHANNEL], id_key=Keys._ID, list_type='user')
        filtered = \
            blacklist_filter.by_type(filtered, Keys.FEATURED, parent_keys=[Keys.STREAM], game_key=Keys.GAME, list_type='game')
        if filtered[Keys.FEATURED]:
            for result in filtered[Keys.FEATURED]:
                kodi.create_item(converter.stream_to_listitem(result[Keys.STREAM]))
            kodi.end_of_directory()
            return
    raise NotFound('streams')


@dispatcher.register(MODES.GAMES, kwargs=['offset'])
@error_handler
def list_all_games(offset=0):
    kodi.set_content('files')
    per_page = utils.get_items_per_page()
    games = None
    all_items = list()
    requests = 0
    while (per_page >= (len(all_items) + 1)) and (requests < MAX_REQUESTS):
        requests += 1
        games = twitch.get_top_games(offset, limit=REQUEST_LIMIT)
        if (games[Keys.TOTAL] > 0) and (Keys.TOP in games):
            filtered = \
                blacklist_filter.by_type(games, Keys.TOP, parent_keys=[Keys.GAME], game_key=Keys.NAME, list_type='game')
            last = None
            for game in filtered[Keys.TOP]:
                last = game[Keys.GAME]
                if per_page >= (len(all_items) + 1):
                    add_item = last if last not in all_items else None
                    if add_item:
                        all_items.append(add_item)
                else:
                    break
            offset = utils.get_offset(offset, last, games[Keys.TOP], key=Keys.GAME)
            if (offset is None) or (games[Keys.TOTAL] <= offset) or (games[Keys.TOTAL] <= REQUEST_LIMIT):
                break
        else:
            break
    has_items = False
    if len(all_items) > 0:
        has_items = True
        for game in all_items:
            kodi.create_item(converter.game_to_listitem(game))
    if games[Keys.TOTAL] > (offset + 1):
        has_items = True
        kodi.create_item(utils.link_to_next_page({'mode': MODES.GAMES, 'offset': offset}))
    if has_items:
        kodi.end_of_directory()
        return
    raise NotFound('games')


@dispatcher.register(MODES.COMMUNITIES, kwargs=['cursor'])
@error_handler
def list_all_communities(cursor='MA=='):
    kodi.set_content('files')
    all_items = list()
    requests = 0
    while (CURSOR_LIMIT >= (len(all_items) + 1)) and cursor and (requests < MAX_REQUESTS):
        requests += 1
        communities = twitch.get_top_communities(cursor, limit=CURSOR_LIMIT)
        cursor = communities[Keys.CURSOR]
        if (communities[Keys.TOTAL] > 0) and (Keys.COMMUNITIES in communities):
            filtered = \
                blacklist_filter.by_type(communities, Keys.COMMUNITIES, id_key=Keys._ID, list_type='community')
            for community in filtered[Keys.COMMUNITIES]:
                add_item = community if community not in all_items else None
                if add_item:
                    all_items.append(add_item)
        else:
            break
    has_items = False
    if len(all_items) > 0:
        has_items = True
        for community in all_items:
            kodi.create_item(converter.community_to_listitem(community))
    if cursor:
        has_items = True
        kodi.create_item(utils.link_to_next_page({'mode': MODES.COMMUNITIES, 'cursor': cursor}))
    if has_items:
        kodi.end_of_directory()
        return
    raise NotFound('communities')


@dispatcher.register(MODES.STREAMLIST, kwargs=['stream_type', 'offset', 'platform'])
@error_handler
def list_streams(stream_type=StreamType.LIVE, offset=0, platform=Platform.ALL):
    utils.refresh_previews()
    kodi.set_content('videos')
    per_page = utils.get_items_per_page()
    streams = None
    all_items = list()
    requests = 0
    while (per_page >= (len(all_items) + 1)) and (requests < MAX_REQUESTS):
        requests += 1
        languages = ','.join(utils.get_languages())
        streams = twitch.get_all_streams(stream_type=stream_type, platform=platform, offset=offset, limit=REQUEST_LIMIT, language=languages)
        if (streams[Keys.TOTAL] > 0) and (Keys.STREAMS in streams):
            filtered = \
                blacklist_filter.by_type(streams, Keys.STREAMS, parent_keys=[Keys.CHANNEL], id_key=Keys._ID, list_type='user')
            filtered = \
                blacklist_filter.by_type(filtered, Keys.STREAMS, game_key=Keys.GAME, list_type='game')
            last = None
            for stream in filtered[Keys.STREAMS]:
                last = stream
                if per_page >= (len(all_items) + 1):
                    add_item = last if last not in all_items else None
                    if add_item:
                        all_items.append(add_item)
                else:
                    break
            offset = utils.get_offset(offset, last, streams[Keys.STREAMS])
            if (offset is None) or (streams[Keys.TOTAL] <= offset) or (streams[Keys.TOTAL] <= REQUEST_LIMIT):
                break
        else:
            break
    has_items = False
    if len(all_items) > 0:
        has_items = True
        for stream in all_items:
            kodi.create_item(converter.stream_to_listitem(stream))
    if streams[Keys.TOTAL] > (offset + 1):
        has_items = True
        kodi.create_item(utils.link_to_next_page({'mode': MODES.STREAMLIST, 'stream_type': stream_type, 'platform': platform, 'offset': offset}))
    if has_items:
        kodi.end_of_directory()
        return
    raise NotFound(i18n('streams'))


@dispatcher.register(MODES.FOLLOWED, args=['content'], kwargs=['offset', 'cursor'])
@error_handler
def list_followed(content, offset=0, cursor='MA=='):
    user_id = twitch.get_user_id()
    username = twitch.get_username()
    per_page = utils.get_items_per_page()
    if content == StreamType.LIVE or content == StreamType.PLAYLIST:
        if content == StreamType.LIVE:
            utils.refresh_previews()
        kodi.set_content('videos')
        streams = None
        all_items = list()
        requests = 0
        while (per_page >= (len(all_items) + 1)) and (requests < MAX_REQUESTS):
            requests += 1
            streams = twitch.get_followed_streams(stream_type=content, offset=offset, limit=REQUEST_LIMIT)
            if (streams[Keys.TOTAL] > 0) and (Keys.STREAMS in streams):
                filtered = \
                    blacklist_filter.by_type(streams, Keys.STREAMS, parent_keys=[Keys.CHANNEL], id_key=Keys._ID, list_type='user')
                filtered = \
                    blacklist_filter.by_type(filtered, Keys.STREAMS, game_key=Keys.GAME, list_type='game')
                last = None
                for stream in filtered[Keys.STREAMS]:
                    last = stream
                    if per_page >= (len(all_items) + 1):
                        add_item = last if last not in all_items else None
                        if add_item:
                            all_items.append(add_item)
                    else:
                        break
                offset = utils.get_offset(offset, last, streams[Keys.STREAMS])
                if (offset is None) or (streams[Keys.TOTAL] <= offset) or (streams[Keys.TOTAL] <= REQUEST_LIMIT):
                    break
            else:
                break
        has_items = False
        if len(all_items) > 0:
            has_items = True
            for stream in all_items:
                kodi.create_item(converter.stream_to_listitem(stream))
        if streams[Keys.TOTAL] > (offset + 1):
            has_items = True
            kodi.create_item(utils.link_to_next_page({'mode': MODES.FOLLOWED, 'content': content, 'offset': offset}))
        if has_items:
            kodi.end_of_directory()
            return
        if content == StreamType.LIVE:
            raise NotFound(i18n('streams'))
        else:
            raise NotFound(i18n('playlists'))
    elif content == 'channels':
        kodi.set_content('files')
        sorting = utils.get_sort('followed_channels')
        channels = None
        all_items = list()
        requests = 0
        while (per_page >= (len(all_items) + 1)) and (requests < MAX_REQUESTS):
            requests += 1
            channels = twitch.get_followed_channels(user_id=user_id, offset=offset, limit=REQUEST_LIMIT, direction=sorting['direction'], sort_by=sorting['by'])
            if (channels[Keys.TOTAL] > 0) and (Keys.FOLLOWS in channels):
                filtered = \
                    blacklist_filter.by_type(channels, Keys.FOLLOWS, parent_keys=[Keys.CHANNEL], id_key=Keys._ID, list_type='user')
                last = None
                for follow in filtered[Keys.FOLLOWS]:
                    channel = follow[Keys.CHANNEL]
                    last = channel
                    if per_page >= (len(all_items) + 1):
                        add_item = last if last not in all_items else None
                        if add_item:
                            all_items.append(add_item)
                    else:
                        break
                offset = utils.get_offset(offset, last, channels[Keys.FOLLOWS], key=Keys.CHANNEL)
                if (offset is None) or (channels[Keys.TOTAL] <= offset) or (channels[Keys.TOTAL] <= REQUEST_LIMIT):
                    break
            else:
                break
        has_items = False
        if len(all_items) > 0:
            has_items = True
            for channel in all_items:
                kodi.create_item(converter.channel_to_listitem(channel))
        if channels[Keys.TOTAL] > (offset + 1):
            has_items = True
            kodi.create_item(utils.link_to_next_page({'mode': MODES.FOLLOWED, 'content': content, 'offset': offset}))
        if has_items:
            kodi.end_of_directory()
            return
        raise NotFound(i18n('channels'))
    elif content == 'games':
        kodi.set_content('files')
        all_items = list()
        games = twitch.get_followed_games(username)
        if (games[Keys.TOTAL] > 0) and (Keys.FOLLOWS in games):
            filtered = \
                blacklist_filter.by_type(games, Keys.FOLLOWS, game_key=Keys._ID, list_type='game')
            for game in filtered[Keys.FOLLOWS]:
                add_item = game if game not in all_items else None
                if add_item:
                    all_items.append(add_item)
        if len(all_items) > 0:
            for game in all_items:
                kodi.create_item(converter.game_to_listitem(game))
            kodi.end_of_directory()
            return
        raise NotFound(i18n('games'))
    elif content == 'clips':
        kodi.set_content('videos')
        sort_by = utils.get_sort('clips', 'by')
        all_items = list()
        requests = 0
        languages = ','.join(utils.get_languages())
        while (CURSOR_LIMIT >= (len(all_items) + 1)) and cursor and (requests < MAX_REQUESTS):
            requests += 1
            clips = twitch.get_followed_clips(cursor=cursor, limit=CURSOR_LIMIT, trending=sort_by, language=languages)
            cursor = clips[Keys.CURSOR]
            if Keys.CLIPS in clips and len(clips[Keys.CLIPS]) > 0:
                filtered = \
                    blacklist_filter.by_type(clips, Keys.CLIPS, parent_keys=[Keys.BROADCASTER], id_key=Keys.ID, list_type='user')
                filtered = \
                    blacklist_filter.by_type(filtered, Keys.CLIPS, game_key=Keys.GAME, list_type='game')
                for clip in filtered[Keys.CLIPS]:
                    add_item = clip if clip not in all_items else None
                    if add_item:
                        all_items.append(add_item)
            else:
                break
        has_items = False
        if len(all_items) > 0:
            has_items = True
            for clip in all_items:
                kodi.create_item(converter.clip_to_listitem(clip))
        if cursor:
            has_items = True
            kodi.create_item(utils.link_to_next_page({'mode': MODES.FOLLOWED, 'content': content, 'cursor': cursor}))
        if has_items:
            kodi.end_of_directory()
            return
        raise NotFound(i18n('clips'))


@dispatcher.register(MODES.CHANNELVIDEOS, kwargs=['channel_id', 'channel_name', 'display_name', 'game'])
@error_handler
def list_channel_video_types(channel_id=None, channel_name=None, display_name=None, game=None):
    if (channel_id is None) and (game is None): return
    kodi.set_content('files')
    context_menu = list()
    if channel_id == 'all' or game is not None:
        context_menu.extend(menu_items.change_period('top_videos'))
        menu_tag = display_name if display_name else game
        menu_tag = menu_tag if menu_tag else i18n('videos')
    else:
        context_menu.extend(menu_items.change_sort_by('channel_videos'))
        menu_tag = display_name if display_name else channel_name
        menu_tag = menu_tag if menu_tag else i18n('channels')
    kodi.create_item({'label': i18n('past_broadcasts'), 'path': {'mode': MODES.CHANNELVIDEOLIST, 'channel_id': channel_id, 'broadcast_type': 'archive', 'game': game},
                      'context_menu': context_menu, 'info': {'plot': '%s - %s' % (menu_tag, i18n('past_broadcasts'))}})
    kodi.create_item({'label': i18n('uploads'), 'path': {'mode': MODES.CHANNELVIDEOLIST, 'channel_id': channel_id, 'broadcast_type': 'upload', 'game': game},
                      'context_menu': context_menu, 'info': {'plot': '%s - %s' % (menu_tag, i18n('uploads'))}})
    kodi.create_item({'label': i18n('video_highlights'), 'path': {'mode': MODES.CHANNELVIDEOLIST, 'channel_id': channel_id, 'broadcast_type': 'highlight', 'game': game},
                      'context_menu': context_menu, 'info': {'plot': '%s - %s' % (menu_tag, i18n('video_highlights'))}})
    if channel_id != 'all':
        if channel_name or game:
            context_menu = list()
            context_menu.extend(menu_items.change_sort_by('clips'))
            context_menu.extend(menu_items.change_period('clips'))
            kodi.create_item({'label': i18n('clips'), 'path': {'mode': MODES.CLIPSLIST, 'channel_name': channel_name, 'game': game},
                              'context_menu': context_menu, 'info': {'plot': '%s - %s' % (menu_tag, i18n('clips'))}})
        if channel_id:
            kodi.create_item({'label': i18n('collections'), 'path': {'mode': MODES.COLLECTIONS, 'channel_id': channel_id},
                              'info': {'plot': '%s - %s' % (menu_tag, i18n('collections'))}})
    kodi.end_of_directory()


@dispatcher.register(MODES.COLLECTIONS, args=['channel_id'], kwargs=['cursor'])
@error_handler
def list_collections(channel_id, cursor='MA=='):
    kodi.set_content('files')
    all_items = list()
    requests = 0
    while (CURSOR_LIMIT >= (len(all_items) + 1)) and cursor and (requests < MAX_REQUESTS):
        requests += 1
        collections = twitch.get_collections(channel_id, cursor, limit=CURSOR_LIMIT)
        cursor = collections[Keys.CURSOR]
        if (Keys.COLLECTIONS in collections) and (len(collections[Keys.COLLECTIONS]) > 0):
            filtered = \
                blacklist_filter.by_type(collections, Keys.COLLECTIONS, parent_keys=[Keys.OWNER], id_key=Keys._ID, list_type='user')
            for collection in filtered[Keys.COLLECTIONS]:
                if collection[Keys.ITEMS_COUNT] > 0:
                    add_item = collection if collection not in all_items else None
                    if add_item:
                        all_items.append(add_item)
        else:
            break
    has_items = False
    if len(all_items) > 0:
        has_items = True
        for collection in all_items:
            kodi.create_item(converter.collection_to_listitem(collection))
    if cursor:
        has_items = True
        kodi.create_item(utils.link_to_next_page({'mode': MODES.COLLECTIONS, 'channel_id': channel_id, 'cursor': cursor}))
    if has_items:
        kodi.end_of_directory()
        return
    raise NotFound(i18n('collections'))


@dispatcher.register(MODES.COLLECTIONVIDEOLIST, args=['collection_id'])
@error_handler
def list_collection_videos(collection_id):
    kodi.set_content('videos')
    videos = twitch.get_collection_videos(collection_id)
    all_items = list()
    if (Keys.ITEMS in videos) and (len(videos[Keys.ITEMS]) > 0):
        filtered = \
            blacklist_filter.by_type(videos, Keys.ITEMS, parent_keys=[Keys.OWNER], id_key=Keys._ID, list_type='user')
        filtered = \
            blacklist_filter.by_type(filtered, Keys.ITEMS, game_key=Keys.GAME, list_type='game')
        for video in filtered[Keys.ITEMS]:
            add_item = video if video not in all_items else None
            if add_item:
                all_items.append(add_item)
        if len(all_items) > 0:
            for video in all_items:
                kodi.create_item(converter.collection_video_to_listitem(video))
            kodi.end_of_directory()
            return
    raise NotFound(i18n('videos'))


@dispatcher.register(MODES.CLIPSLIST, kwargs=['cursor', 'channel_name', 'game'])
@error_handler
def list_clips(cursor='MA==', channel_name=None, game=None):
    kodi.set_content('videos')
    sorting = utils.get_sort('clips')
    all_items = list()
    requests = 0
    languages = ','.join(utils.get_languages())
    while (CURSOR_LIMIT >= (len(all_items) + 1)) and cursor and (requests < MAX_REQUESTS):
        requests += 1
        clips = twitch.get_top_clips(cursor, limit=CURSOR_LIMIT, channel=channel_name, game=game, period=sorting['period'], trending=sorting['by'], language=languages)
        cursor = clips[Keys.CURSOR]
        if Keys.CLIPS in clips and len(clips[Keys.CLIPS]) > 0:
            filtered = \
                blacklist_filter.by_type(clips, Keys.CLIPS, parent_keys=[Keys.BROADCASTER], id_key=Keys.ID, list_type='user')
            filtered = \
                blacklist_filter.by_type(filtered, Keys.CLIPS, game_key=Keys.GAME, list_type='game')
            for clip in filtered[Keys.CLIPS]:
                add_item = clip if clip not in all_items else None
                if add_item:
                    all_items.append(add_item)
        else:
            break
    has_items = False
    if len(all_items) > 0:
        has_items = True
        for clip in all_items:
            kodi.create_item(converter.clip_to_listitem(clip))
    if cursor:
        has_items = True
        item_dict = {'mode': MODES.CLIPSLIST, 'cursor': cursor}
        if channel_name:
            item_dict['channel_name'] = channel_name
        kodi.create_item(utils.link_to_next_page(item_dict))
    if has_items:
        kodi.end_of_directory()
        return
    raise NotFound(i18n('clips'))


@dispatcher.register(MODES.CHANNELVIDEOLIST, args=['broadcast_type'], kwargs=['offset', 'channel_id', 'game'])
@error_handler
def list_channel_videos(broadcast_type, channel_id=None, game=None, offset=0):
    if (channel_id is None) and (game is None): return
    kodi.set_content('videos')
    per_page = utils.get_items_per_page()
    videos = None
    all_items = list()
    requests = 0
    while (per_page >= (len(all_items) + 1)) and (requests < MAX_REQUESTS):
        requests += 1
        if game is not None:
            period = utils.get_sort('top_videos', 'period')
            videos = twitch.get_top_videos(offset, limit=REQUEST_LIMIT, game=game, broadcast_type=broadcast_type, period=period)
        else:
            if channel_id == 'all':
                period = utils.get_sort('top_videos', 'period')
                videos = twitch.get_top_videos(offset, limit=REQUEST_LIMIT, broadcast_type=broadcast_type, period=period)
            else:
                sort_by = utils.get_sort('channel_videos', 'by')
                languages = ','.join(utils.get_languages())
                videos = twitch.get_channel_videos(channel_id, offset, limit=REQUEST_LIMIT, broadcast_type=broadcast_type, sort_by=sort_by, language=languages)
        if Keys.VODS in videos or ((videos[Keys.TOTAL] > 0) and (Keys.VIDEOS in videos)):
            key = Keys.VODS if Keys.VODS in videos else Keys.VIDEOS
            filtered = \
                blacklist_filter.by_type(videos, key, parent_keys=[Keys.CHANNEL], id_key=Keys._ID, list_type='user')
            filtered = \
                blacklist_filter.by_type(filtered, key, game_key=Keys.GAME, list_type='game')
            last = None
            for video in filtered[key]:
                last = video
                if per_page >= (len(all_items) + 1):
                    add_item = last if last not in all_items else None
                    if add_item:
                        all_items.append(add_item)
                else:
                    break
            offset = utils.get_offset(offset, last, videos[key])
            if (offset is None) or ((key == Keys.VIDEOS) and ((videos[Keys.TOTAL] <= offset) or (videos[Keys.TOTAL] <= REQUEST_LIMIT))):
                break
        else:
            break
    has_items = False
    if len(all_items) > 0 and videos is not None:
        has_items = True
        for video in all_items:
            kodi.create_item(converter.video_list_to_listitem(video))
    if Keys.VODS in videos or videos[Keys.TOTAL] > (offset + 1):
        has_items = True
        kodi.create_item(utils.link_to_next_page({'mode': MODES.CHANNELVIDEOLIST, 'channel_id': channel_id, 'broadcast_type': broadcast_type, 'offset': offset}))
    if has_items:
        kodi.end_of_directory()
        return
    raise NotFound(i18n('videos'))


@dispatcher.register(MODES.GAMELISTS, args=['game'])
@error_handler
def game_lists(game):
    kodi.set_content('files')
    context_menu = list()
    context_menu.extend(menu_items.clear_previews())
    kodi.create_item({'label': i18n('live_channels'), 'path': {'mode': MODES.GAMESTREAMS, 'game': game}, 'context_menu': context_menu,
                      'info': {'plot': '%s - %s' % (game, i18n('live_channels'))}})
    kodi.create_item({'label': i18n('videos'), 'path': {'mode': MODES.CHANNELVIDEOS, 'game': game},
                      'info': {'plot': '%s - %s' % (game, i18n('videos'))}})
    kodi.end_of_directory()


@dispatcher.register(MODES.GAMESTREAMS, args=['game'], kwargs=['offset'])
@error_handler
def list_game_streams(game, offset=0):
    utils.refresh_previews()
    kodi.set_content('videos')
    per_page = utils.get_items_per_page()
    streams = None
    all_items = list()
    requests = 0
    while (per_page >= (len(all_items) + 1)) and (requests < MAX_REQUESTS):
        requests += 1
        languages = ','.join(utils.get_languages())
        streams = twitch.get_game_streams(game=game, offset=offset, limit=REQUEST_LIMIT, language=languages)
        if (streams[Keys.TOTAL] > 0) and (Keys.STREAMS in streams):
            filtered = \
                blacklist_filter.by_type(streams, Keys.STREAMS, parent_keys=[Keys.CHANNEL], id_key=Keys._ID, list_type='user')
            last = None
            for stream in filtered[Keys.STREAMS]:
                last = stream
                if per_page >= (len(all_items) + 1):
                    add_item = last if last not in all_items else None
                    if add_item:
                        all_items.append(add_item)
                else:
                    break
            offset = utils.get_offset(offset, last, streams[Keys.STREAMS])
            if (offset is None) or (streams[Keys.TOTAL] <= offset) or (streams[Keys.TOTAL] <= REQUEST_LIMIT):
                break
        else:
            break
    has_items = False
    if len(all_items) > 0:
        has_items = True
        for stream in all_items:
            kodi.create_item(converter.stream_to_listitem(stream))
    if streams[Keys.TOTAL] > (offset + 1):
        has_items = True
        kodi.create_item(utils.link_to_next_page({'mode': MODES.GAMESTREAMS, 'game': game, 'offset': offset}))
    if has_items:
        kodi.end_of_directory()
        return
    raise NotFound(i18n('streams'))


@dispatcher.register(MODES.COMMUNITYSTREAMS, args=['community_id'], kwargs=['offset'])
@error_handler
def list_community_streams(community_id, offset=0):
    utils.refresh_previews()
    kodi.set_content('videos')
    per_page = utils.get_items_per_page()
    streams = None
    all_items = list()
    requests = 0
    while (per_page >= (len(all_items) + 1)) and (requests < MAX_REQUESTS):
        requests += 1
        languages = ','.join(utils.get_languages())
        streams = twitch.get_community_streams(community_id=community_id, offset=offset, limit=REQUEST_LIMIT, language=languages)
        if (streams[Keys.TOTAL] > 0) and (Keys.STREAMS in streams):
            filtered = \
                blacklist_filter.by_type(streams, Keys.STREAMS, parent_keys=[Keys.CHANNEL], id_key=Keys._ID, list_type='user')
            # filtering by game causes excessive calls (game-centric communities)
            # filtered, _filtered_total, __discarded = \
            #     blacklist_filter.by_type(filtered, Keys.STREAMS, game_key=Keys.GAME, list_type='game')
            last = None
            for stream in filtered[Keys.STREAMS]:
                last = stream
                if per_page >= (len(all_items) + 1):
                    add_item = last if last not in all_items else None
                    if add_item:
                        all_items.append(add_item)
                else:
                    break
            offset = utils.get_offset(offset, last, streams[Keys.STREAMS])
            if (offset is None) or (streams[Keys.TOTAL] <= offset) or (streams[Keys.TOTAL] <= REQUEST_LIMIT):
                break
        else:
            break
    has_items = False
    if len(all_items) > 0:
        has_items = True
        for stream in all_items:
            kodi.create_item(converter.stream_to_listitem(stream))
        if streams[Keys.TOTAL] > (offset + 1):
            has_items = True
            kodi.create_item(utils.link_to_next_page({'mode': MODES.COMMUNITYSTREAMS, 'community_id': community_id, 'offset': offset}))
    if has_items:
        kodi.end_of_directory()
        return
    raise NotFound(i18n('streams'))


@dispatcher.register(MODES.PLAY, kwargs=['name', 'channel_id', 'video_id', 'slug', 'ask', 'use_player'])
@error_handler
def play(name=None, channel_id=None, video_id=None, slug=None, ask=False, use_player=False):
    window = kodi.Window(10000)

    def _reset():
        window.clearProperty(kodi.get_id() + '-_seek')
        window.clearProperty(kodi.get_id() + '-seek_time')
        window.clearProperty(kodi.get_id() + '-twitch_playing')

    def _reset_live():
        window.clearProperty(kodi.get_id() + '-livestream')

    def _get_seek():
        result = window.getProperty(kodi.get_id() + '-_seek')
        if result:
            return result.split(',')
        return None, None

    def _set_playing():
        window.setProperty(kodi.get_id() + '-twitch_playing', str(True))

    def _set_live(_id, _name, _display_name):
        window.setProperty(kodi.get_id() + '-livestream', '%s,%s,%s' % (_id, _name, _display_name))

    def _set_seek_time(value):
        window.setProperty(kodi.get_id() + '-seek_time', str(value))

    try:
        _reset_live()
        videos = item_dict = quality = None
        seek_time = 0
        if video_id:
            seek_id, _seek_time = _get_seek()
            if seek_id == video_id:
                seek_time = int(_seek_time)
            restricted = False
            unrestricted = None
            result = twitch.get_video_by_id(video_id)
            video_id = result[Keys._ID]
            channel_id = result[Keys.CHANNEL][Keys._ID]
            channel_name = result[Keys.CHANNEL][Keys.DISPLAY_NAME] if result[Keys.CHANNEL][Keys.DISPLAY_NAME] else result[Keys.CHANNEL][Keys.NAME]
            extra_info = twitch._get_video_by_id(video_id)
            if twitch.access_token:
                try:
                    subscribed = twitch.check_subscribed(channel_id)
                except TwitchException as e:
                    if ('status' in e.message) and (e.message['status'] == 422):
                        subscribed = True  # no subscription program
                    else:
                        raise
            else:
                subscribed = False
            if not subscribed:
                if ('restrictions' in extra_info) and ('chunks' in extra_info):
                    unrestricted = extra_info['chunks']
                    for key in list(extra_info['chunks']):
                        if key in extra_info['restrictions']:
                            if extra_info['restrictions'][key] == 'chansub':
                                del unrestricted[key]
                    if unrestricted == {}:
                        restricted = True
            if not restricted:
                _videos = twitch.get_vod(video_id)
                if unrestricted:
                    videos = list()
                    for _video in _videos:
                        if _video['id'] in list(unrestricted):
                            videos.append(_video)
                else:
                    videos = _videos
                item_dict = converter.video_to_playitem(result)
                quality = utils.get_default_quality('video', channel_id)
                if quality:
                    quality = quality[channel_id]['quality']
            else:
                raise SubRequired(channel_name)
        elif name and channel_id:
            quality = utils.get_default_quality('stream', channel_id)
            if quality:
                quality = quality[channel_id]['quality']
            videos = twitch.get_live(name)
            result = twitch.get_channel_stream(channel_id)[Keys.STREAM]
            item_dict = converter.stream_to_playitem(result)
            channel_name = result[Keys.CHANNEL][Keys.DISPLAY_NAME] \
                if result[Keys.CHANNEL][Keys.DISPLAY_NAME] else result[Keys.CHANNEL][Keys.NAME]
            _set_live(channel_id, name, channel_name)
        elif slug and channel_id:
            quality = utils.get_default_quality('clip', channel_id)
            if quality:
                quality = quality[channel_id]['quality']
            videos = twitch.get_clip(slug)
            result = twitch.get_clip_by_slug(slug)
            item_dict = converter.clip_to_playitem(result)
        _reset()
        if item_dict and videos:
            clip = False if slug is None else True
            result = converter.get_video_for_quality(videos, ask=ask, quality=quality, clip=clip)
            if result:
                play_url = result['url']
                quality_label = result['name']
                log_utils.log('Attempting playback using quality |%s| @ |%s|' % (quality_label, play_url), log_utils.LOGDEBUG)
                item_dict['path'] = play_url
                playback_item = kodi.create_item(item_dict, add=False)
                if seek_time > 0:
                    _set_seek_time(seek_time)
                _set_playing()
                if use_player:
                    kodi.Player().play(item_dict['path'], playback_item)
                else:
                    kodi.set_resolved_url(playback_item)
                if utils.irc_enabled() and twitch.access_token:
                    username = twitch.get_username()
                    if username:
                        utils.exec_irc_script(username, name)
                return
            else:
                return
        raise PlaybackFailed()
    except:
        _reset()
        _reset_live()
        raise


@dispatcher.register(MODES.EDITFOLLOW, kwargs=['channel_id', 'channel_name', 'game'])
@error_handler
def edit_user_follows(channel_id=None, channel_name=None, game=None):
    if (channel_id is None or channel_name is None) and game is None:
        return

    if not game:
        is_following = twitch.check_follow(channel_id)
    else:
        is_following = twitch.check_follow_game(game)

    if not game:
        display_name = channel_name
    else:
        display_name = game

    if is_following:
        confirmed = kodi.Dialog().yesno(i18n('toggle_follow'), i18n('unfollow_confirm') % display_name)
        if confirmed:
            if not game:
                result = twitch.unfollow(channel_id)
            else:
                result = twitch.unfollow_game(game)
            kodi.notify(msg=i18n('unfollowed') % display_name, sound=False)
    else:
        confirmed = kodi.Dialog().yesno(i18n('toggle_follow'), i18n('follow_confirm') % display_name)
        if confirmed:
            if not game:
                result = twitch.follow(channel_id)
            else:
                result = twitch.follow_game(game)
            kodi.notify(msg=i18n('now_following') % display_name, sound=False)


"""
# unused, requires scopes [scopes.user_blocks_edit, scopes.user_blocks_read]
@dispatcher.register(MODES.EDITBLOCK, args=['target_id', 'name'])
@error_handler
def edit_user_blocks(target_id, name):
    block_list = twitch.get_user_blocks()
    is_blocked = any(target_id == blocked_id for blocked_id, blocked_name in block_list)

    if is_blocked:
        confirmed = kodi.Dialog().yesno(i18n('toggle_block'), i18n('unblock_confirm') % name)
        if confirmed:
            result = twitch.unblock_user(target_id)
            kodi.notify(msg=i18n('unblocked') % name, sound=False)
    else:
        confirmed = kodi.Dialog().yesno(i18n('toggle_block'), i18n('block_confirm') % name)
        if confirmed:
            result = twitch.block_user(target_id)
            kodi.notify(msg=i18n('blocked') % name, sound=False)
"""


@dispatcher.register(MODES.EDITBLACKLIST, kwargs=['list_type', 'target_id', 'name', 'remove'])
@error_handler
def edit_blacklist(list_type='user', target_id=None, name=None, remove=False):
    if not remove:
        if not target_id or not name: return
        if kodi.get_setting('blacklist_confirm_toggle') == 'true':
            confirmed = kodi.Dialog().yesno(i18n('blacklist'), i18n('confirm_blacklist') % name)
            if confirmed:
                result = utils.add_blacklist(target_id, name, list_type)
                if result:
                    kodi.notify(msg=i18n('blacklisted') % name, sound=False)
        else:
            result = utils.add_blacklist(target_id, name, list_type)
    else:
        result = utils.remove_blacklist(list_type)
        if result:
            kodi.notify(msg=i18n('removed_from_blacklist') % result[1], sound=False)


@dispatcher.register(MODES.EDITQUALITIES, args=['content_type'], kwargs=['video_id', 'target_id', 'name', 'remove', 'clip_id'])
@error_handler
def edit_qualities(content_type, target_id=None, name=None, video_id=None, remove=False, clip_id=None):
    if not remove:
        videos = None
        if not target_id or not name: return
        if content_type == 'video' and video_id:
            videos = twitch.get_vod(video_id)
        elif content_type == 'clip' and clip_id:
            videos = twitch.get_clip(clip_id)
        elif content_type == 'stream':
            videos = twitch.get_live(name)
        if videos:
            result = converter.select_video_for_quality(videos)
            if result:
                quality = result['name']
                result = utils.add_default_quality(content_type, target_id, name, quality)
                if result:
                    kodi.notify(msg=i18n('default_quality_set') % (content_type, quality, name), sound=False)
    else:
        result = utils.remove_default_quality(content_type)
        if result:
            kodi.notify(msg=i18n('removed_default_quality') % (content_type, result[result.keys()[0]]['name']), sound=False)


@dispatcher.register(MODES.EDITSORTING, args=['list_type', 'sort_type'])
@error_handler
def edit_sorting(list_type, sort_type):
    if sort_type == 'by':
        choices = list()
        if list_type == 'followed_channels':
            choices = [(valid.replace('_', ' ').capitalize(), valid) for valid in SortBy.valid()]
        elif list_type == 'channel_videos':
            choices = [(valid.capitalize().replace('_', ' '), valid) for valid in VideoSort.valid()]
        elif list_type == 'clips':
            choices = [(i18n('popular'), Boolean.TRUE), (i18n('views'), Boolean.FALSE)]
        if choices:
            result = kodi.Dialog().select(i18n('change_sort_by'), [label for label, value in choices])
            if result > -1:
                sorting = utils.get_sort(list_type)
                utils.set_sort(list_type, sort_by=choices[result][1], period=sorting['period'], direction=sorting['direction'])

    elif sort_type == 'period':
        choices = list()
        if list_type == 'top_videos':
            choices = [(valid.replace('_', ' ').capitalize(), valid) for valid in Period.valid()]
        elif list_type == 'clips':
            choices = [(valid.replace('_', ' ').capitalize(), valid) for valid in ClipPeriod.valid()]
        if choices:
            result = kodi.Dialog().select(i18n('change_period'), [label for label, value in choices])
            if result > -1:
                sorting = utils.get_sort(list_type)
                utils.set_sort(list_type, sort_by=sorting['by'], period=choices[result][1], direction=sorting['direction'])

    elif sort_type == 'direction':
        choices = list()
        if list_type == 'followed_channels':
            choices = [(valid.replace('_', ' ').capitalize(), valid) for valid in Direction.valid()]
        if choices:
            result = kodi.Dialog().select(i18n('change_direction'), [label for label, value in choices])
            if result > -1:
                sorting = utils.get_sort(list_type)
                utils.set_sort(list_type, sort_by=sorting['by'], period=sorting['period'], direction=choices[result][1])


@dispatcher.register(MODES.EDITLANGUAGES, args=['action'])
@error_handler
def edit_languages(action):
    if action == 'add':
        current_languages = utils.get_languages()
        valid_languages = Language.valid()
        missing_languages = [language for language in valid_languages if language not in current_languages]
        result = kodi.Dialog().select(i18n('add_language'), missing_languages)
        if result > -1:
            utils.add_language(missing_languages[result])
    elif action == 'remove':
        current_languages = utils.get_languages()
        result = kodi.Dialog().select(i18n('remove_language'), current_languages)
        if result > -1:
            utils.remove_language(current_languages[result])


@dispatcher.register(MODES.CLEARLIST, args=['list_type', 'list_name'])
@error_handler
def clear_list(list_type, list_name):
    confirmed = kodi.Dialog().yesno(i18n('clear_list'), i18n('confirm_clear') % (list_type, list_name))
    if confirmed:
        result = utils.clear_list(list_type, list_name)
        if result:
            kodi.notify(msg=i18n('cleared_list') % (list_type, list_name), sound=False)


@dispatcher.register(MODES.SETTINGS, kwargs=['refresh'])
@error_handler
def settings(refresh=True):
    kodi.show_settings()
    if refresh:
        kodi.refresh_container()


@dispatcher.register(MODES.RESETCACHE)
@error_handler
def reset_cache():
    confirmed = kodi.Dialog().yesno(i18n('confirm'), i18n('cache_reset_confirm'))
    if confirmed:
        result = cache.reset_cache()
        if result:
            kodi.notify(msg=i18n('cache_reset_succeeded'), sound=False)
        else:
            kodi.notify(msg=i18n('cache_reset_failed'), sound=False)


@dispatcher.register(MODES.CLEARLIVEPREVIEWS, kwargs=['notify'])
@error_handler
def clear_live_previews(notify=True):
    utils.TextureCacheCleaner().remove_like(LIVE_PREVIEW_TEMPLATE, notify)


@dispatcher.register(MODES.INSTALLIRCCHAT)
@error_handler
def install_ircchat():
    if kodi.get_kodi_version().major > 16:
        kodi.execute_builtin('InstallAddon(script.ircchat)')
    else:
        kodi.execute_builtin('RunPlugin(plugin://script.ircchat/)')


@dispatcher.register(MODES.TOKENURL)
@error_handler
def get_token_url():
    redirect_uri = utils.get_redirect_uri()
    request_url = twitch.client.prepare_request_uri(redirect_uri=redirect_uri, scope=twitch.required_scopes)
    try:
        short_url = googl_url(request_url)
    except:
        short_url = None
    prompt_url = short_url if short_url else request_url
    result = kodi.Dialog().ok(heading=i18n('authorize_heading'), line1=i18n('authorize_message'),
                              line2=' %s' % prompt_url)
    kodi.show_settings()


def run(argv=None):
    if sys.argv:
        argv = sys.argv
    queries = kodi.parse_query(sys.argv[2])
    log_utils.log('Version: |%s| Kodi Version: %s' % (kodi.get_version(), kodi.get_kodi_version()), log_utils.LOGDEBUG)
    log_utils.log('Queries: |%s| Args: |%s|' % (queries, argv), log_utils.LOGDEBUG)

    # don't process params that don't match our url exactly
    plugin_url = 'plugin://%s/' % kodi.get_id()
    if argv[0] != plugin_url:
        return
    try:
        global twitch
        twitch = api.Twitch()
    except:
        kodi.notify(utils.i18n('connection_failed'), utils.i18n('failed_connect_api'))
        log_utils.log(traceback.print_exc(), log_utils.LOGERROR)
        return

    mode = queries.get('mode', None)
    dispatcher.dispatch(mode, queries)


if __name__ == '__main__':
    sys.exit(run())
