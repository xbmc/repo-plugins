# -*- coding: utf-8 -*-
"""

    Copyright (C) 2011-2018 PleXBMC (plugin.video.plexbmc) by hippojay (Dave Hawes-Johnson)
    Copyright (C) 2018-2020 Composite (plugin.video.composite_for_plex)

    This file is part of Composite (plugin.video.composite_for_plex)

    SPDX-License-Identifier: GPL-2.0-or-later
    See LICENSES/GPL-2.0-or-later.txt for more information.
"""

from kodi_six import xbmc  # pylint: disable=import-error
from kodi_six import xbmcplugin  # pylint: disable=import-error
from six.moves.urllib_parse import quote
from six.moves.urllib_parse import unquote

from ..addon.common import get_handle
from ..addon.constants import MODES
from ..addon.logger import Logger
from ..addon.processing.albums import process_albums
from ..addon.processing.artists import process_artists
from ..addon.processing.directories import process_directories
from ..addon.processing.episodes import process_episodes
from ..addon.processing.movies import process_movies
from ..addon.processing.photos import process_photos
from ..addon.processing.shows import process_shows
from ..addon.processing.tracks import process_tracks
from ..addon.processing.xml import process_xml
from ..addon.strings import i18n
from ..addon.utils import get_xml
from ..plex import plex

LOG = Logger()


def run(context, url=None, server_uuid=None, mode=None):
    """
        This function takes teh URL, gets the XML and determines what the content is
        This XML is then redirected to the best processing function.
        If a search term is detected, then show keyboard and run search query
        @input: URL of XML page
        @return: nothing, redirects to another function
    """
    context.plex_network = plex.Plex(context.settings, load=True)

    if server_uuid and mode:
        server = context.plex_network.get_server_from_uuid(server_uuid)
        url = _get_url(server, mode, url)
    else:
        if not url:
            return

    last_bit = url.split('/')[-1]
    LOG.debug('URL suffix: %s' % last_bit)

    # Catch search requests, as we need to process input before getting results.
    if last_bit.startswith('search'):
        LOG.debug('This is a search URL.  Bringing up keyboard')
        search_url = search(url)
        if not search_url:
            return
        url = search_url

    try:
        tree = get_xml(context, url)
        process(context, url, tree, last_bit)

    except:  # pylint: disable=bare-except
        if mode not in [MODES.TXT_TVSHOWS, MODES.TXT_MOVIES, MODES.TXT_MOVIES_ON_DECK,
                        MODES.TXT_TVSHOWS_ON_DECK, MODES.TXT_MOVIES_RECENT_ADDED,
                        MODES.TXT_TVSHOWS_RECENT_ADDED, MODES.TXT_MOVIES_RECENT_RELEASE,
                        MODES.TXT_TVSHOWS_RECENT_AIRED]:
            raise

        # this was a widget, don't raise error, return empty directory
        xbmcplugin.endOfDirectory(get_handle(), cacheToDisc=False)


def _get_url(server, mode, url):
    sections = server.get_sections()

    for section in sections:
        is_video = section.is_movie() or section.is_show()
        if is_video:
            if mode in [MODES.TXT_TVSHOWS, MODES.TXT_MOVIES]:
                url = server.join_url(server.get_url_location(), section.get_path(), 'all')
                break
            if mode in [MODES.TXT_MOVIES_ON_DECK, MODES.TXT_TVSHOWS_ON_DECK]:
                url = server.join_url(server.get_url_location(), unquote(url), 'onDeck')
                break
            if mode in [MODES.TXT_MOVIES_RECENT_ADDED, MODES.TXT_TVSHOWS_RECENT_ADDED]:
                url = server.join_url(server.get_url_location(), unquote(url), 'recentlyAdded')
                break
            if mode in [MODES.TXT_MOVIES_RECENT_RELEASE, MODES.TXT_TVSHOWS_RECENT_AIRED]:
                url = server.join_url(server.get_url_location(), unquote(url), 'newest')
                break
    return url


def search(url):
    keyboard = xbmc.Keyboard('', i18n('Search...'))
    keyboard.setHeading(i18n('Enter search term'))
    keyboard.doModal()
    if keyboard.isConfirmed():
        text = keyboard.getText()
        LOG.debug('Search term input: %s' % text)
        return url + '&query=' + quote(text)

    return None


def process(context, url, tree, last_bit):
    view_group = None
    if tree is not None:
        view_group = tree.get('viewGroup')

    if last_bit in ['folder', 'playlists']:
        process_xml(context, url, tree)
    elif view_group == 'movie':
        LOG.debug('This is movie XML, passing to Movies')
        process_movies(context, url, tree)
    elif view_group == 'show':
        LOG.debug('This is tv show XML')
        process_shows(context, url, tree)
    elif view_group == 'episode':
        LOG.debug('This is TV episode XML')
        process_episodes(context, url, tree)
    elif view_group == 'artist':
        LOG.debug('This is music XML')
        process_artists(context, url, tree)
    elif view_group in ['album', 'albums']:
        process_albums(context, url, tree)
    elif view_group == 'track':
        LOG.debug('This is track XML')
        process_tracks(context, url, tree)  # sorting is handled here
    elif view_group == 'photo':
        LOG.debug('This is a photo XML')
        process_photos(context, url, tree)
    else:
        process_directories(context, url, tree)
