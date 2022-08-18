# -*- coding: utf-8 -*-
"""

    Copyright (C) 2019-2020 Composite (plugin.video.composite_for_plex)

    This file is part of Composite (plugin.video.composite_for_plex)

    SPDX-License-Identifier: GPL-2.0-or-later
    See LICENSES/GPL-2.0-or-later.txt for more information.
"""

import string
import xml.etree.ElementTree as ETree

from kodi_six import xbmc  # pylint: disable=import-error
from kodi_six import xbmcplugin  # pylint: disable=import-error
from six import PY3
from six.moves.urllib_parse import unquote

from ..addon.common import get_handle
from ..addon.common import get_plugin_url
from ..addon.constants import MODES
from ..addon.logger import Logger
from ..addon.processing.episodes import process_episodes
from ..addon.processing.seasons import process_seasons
from ..addon.strings import decode_utf8
from ..addon.utils import jsonrpc_play
from ..addon.utils import wait_for_busy_dialog
from ..plex import plex

LOG = Logger()


def run(context):
    context.plex_network = plex.Plex(context.settings, load=True)

    params = context.params
    for param in ['video_type', 'title', 'year']:  # check for expected common parameters
        if param not in params:
            return

    # possible params ['video_type', 'title', 'year', 'trakt_id', 'episode_id', 'season_id',
    # 'season', 'episode', 'ep_title', 'imdb_id', 'tmdb_id', 'tvdb_id']

    search_results = search(context)
    log_results = list(map(lambda x: decode_utf8(ETree.tostring(x[1])), search_results))
    LOG.debug('Found search results: %s' % '\n\n'.join(log_results))

    server_uuid, media_id = get_server_uuid_and_media_id(context.params, search_results)
    if server_uuid and media_id:
        LOG.debug('Found a server with the requested content @ server_uuid=%s w/ media_id=%s' %
                  (server_uuid, media_id))

        if context.params.get('video_type') in ['show', 'season']:
            if context.params.get('video_type') == 'show':
                process_seasons(context, server_uuid, rating_key=media_id)
                return

            if context.params.get('video_type') == 'season':
                process_episodes(context, server_uuid, rating_key=media_id)
                return

        if context.params.get('video_type') in ['movie', 'episode']:
            xbmcplugin.endOfDirectory(get_handle(), False, cacheToDisc=False)
            if xbmc.Player().isPlaying():
                xbmc.Player().stop()

            play = wait_for_busy_dialog()
            if play:
                jsonrpc_play(get_plugin_url({
                    'mode': MODES.PLAYLIBRARY,
                    'server_uuid': server_uuid,
                    'media_id': media_id
                }))
                return

        LOG.debug('Failed to execute TraktToKodi action')
    else:
        LOG.debug('Content not found on any server')


def _is_not_none(item):
    if item is not None and item.get('size', '0') == '0':
        item = None
    return item is not None


def _get_show(params, response):
    for show in response:
        title = _compare_titles(show.get('title'), params.get('title'))
        year = show.get('year') == params.get('year')
        if title and year:
            return show
    return None


def _get_season(params, server, show_id):
    seasons = server.get_children(show_id)
    if _is_not_none(seasons):
        for season in seasons:
            if season.get('index') == params.get('season'):
                return season
    return None


def _get_episode(params, server, season_id=None, processed=None):
    if not season_id and not processed:
        return None

    episodes = processed
    if season_id and not episodes:
        episodes = server.get_children(season_id)

    if _is_not_none(episodes):
        for episode in episodes:
            if (episode.get('parentIndex') == params.get('season') and
                    episode.get('index') == params.get('episode')):
                return episode
    return None


def _get_content_type(video_type):
    content_type = None
    if video_type == 'movie':
        content_type = 'movie'
    elif video_type == 'show':
        content_type = 'show'
    elif video_type == 'season':
        content_type = 'show'
    elif video_type == 'episode':
        content_type = 'show'
    return content_type


def _get_search_type(video_type):
    search_type = None
    if video_type == 'movie':
        search_type = '1'
    elif video_type == 'show':
        search_type = '2'
    elif video_type == 'season':
        search_type = '2'
    elif video_type == 'episode':
        search_type = '4'
    return search_type


def _get_search_results(context, server, processed):
    server_uuid = server.get_uuid()

    results = []
    append_result = results.append

    if context.params.get('video_type') == 'episode':
        episode = _get_episode(context.params, server, processed=processed)

        if episode is not None:
            append_result((server_uuid, episode))
            return results

    if context.params.get('video_type') in ['episode', 'season']:
        show = _get_show(context.params, processed)
        if show is not None:

            season = _get_season(context.params, server, show.get('ratingKey'))
            if season is not None:
                if context.params.get('video_type') == 'season':
                    append_result((server_uuid, season))
                    return results

                if context.params.get('video_type') == 'episode':
                    episode = _get_episode(context.params, server, season.get('ratingKey'))
                    if episode is not None:
                        append_result((server_uuid, episode))
                        return results
    else:
        results = list(map(lambda x: (server_uuid, x), processed))

    return results


def search(context):
    results = []

    content_type = _get_content_type(context.params.get('video_type'))
    search_type = _get_search_type(context.params.get('video_type'))
    if not content_type or not search_type:
        return []

    server_list = context.plex_network.get_server_list()
    params = context.params

    for server in server_list:
        processed_xml = server.processed_xml

        sections = server.get_sections()
        for section in sections:

            if section.get_type() == content_type:
                title = params.get('ep_title') if search_type == '4' \
                    else params.get('title')
                url = '%s/search?type=%s&query=%s' % (section.get_path(), search_type, title)
                processed = processed_xml(url)

                if not _is_not_none(processed) and params.get('video_type') == 'episode':
                    url = '%s/search?type=%s&query=%s' % \
                          (section.get_path(), '2', params.get('title'))
                    processed = processed_xml(url)

                if _is_not_none(processed):
                    results += _get_search_results(context, server, processed)

    return results


def _compare_titles(plex_title, trakt_title):
    def _translate(_string):
        _string = _string.lower()
        _string = _string.replace('  ', ' ')
        _string = _string.strip()
        if PY3:
            _string = _string.translate(str.maketrans('', '', string.punctuation))
        else:
            _string = _string.translate(None, string.punctuation)
        return _string

    plex_title = _translate(plex_title)
    trakt_title = _translate(unquote(trakt_title))

    LOG.debug('Comparing titles: %s -> %s' % (plex_title, trakt_title))
    return plex_title == trakt_title


def get_server_uuid_and_media_id(params, search_results):
    for result in search_results:
        if params.get('video_type') == 'movie':
            title = _compare_titles(result[1].get('title'), params.get('title'))
            year = result[1].get('year') == params.get('year')
            if title and year:
                return result[0], result[1].get('ratingKey')

        elif params.get('video_type') == 'show':
            title = _compare_titles(result[1].get('title'), params.get('title'))
            year = result[1].get('year') == params.get('year')
            if title and year:
                return result[0], result[1].get('ratingKey')

        elif params.get('video_type') == 'season':
            title = _compare_titles(result[1].get('parentTitle'), params.get('title'))
            season = result[1].get('index') == params.get('season')
            if title and season:
                return result[0], result[1].get('ratingKey')

        elif params.get('video_type') == 'episode':
            title = _compare_titles(result[1].get('grandparentTitle'), params.get('title'))
            season = result[1].get('parentIndex') == params.get('season')
            episode = result[1].get('index') == params.get('episode')
            if title and season and episode:
                return result[0], result[1].get('ratingKey')

    return None, None
