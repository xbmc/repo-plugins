# -*- coding: utf-8 -*-
"""

    Copyright (C) 2011-2018 PleXBMC (plugin.video.plexbmc) by hippojay (Dave Hawes-Johnson)
    Copyright (C) 2018-2020 Composite (plugin.video.composite_for_plex)

    This file is part of Composite (plugin.video.composite_for_plex)

    SPDX-License-Identifier: GPL-2.0-or-later
    See LICENSES/GPL-2.0-or-later.txt for more information.
"""

import json

from ..constants import COMBINED_SECTIONS
from ..constants import MODES
from ..containers import GUIItem
from ..logger import Logger
from ..strings import encode_utf8
from ..strings import i18n
from .common import get_banner_image
from .common import get_fanart_image
from .common import get_media_data
from .common import get_metadata
from .common import get_thumb_image
from .context_menu import ContextMenu
from .gui import create_gui_item

LOG = Logger()


def create_episode_item(context, item, library=False):
    metadata = get_metadata(context, item.data)
    LOG.debug('Media attributes are %s' % json.dumps(metadata['attributes'], indent=4))

    # Required listItem entries for Kodi
    info_labels = {
        'plot': encode_utf8(item.data.get('summary', '')),
        'title': encode_utf8(item.data.get('title', i18n('Unknown'))),
        'sorttitle': encode_utf8(item.data.get('titleSort',
                                               item.data.get('title', i18n('Unknown')))),
        'rating': float(item.data.get('rating', 0)),
        'studio': encode_utf8(item.data.get('studio', item.tree.get('studio', ''))),
        'mpaa': item.data.get('contentRating', item.tree.get('grandparentContentRating', '')),
        'year': int(item.data.get('year', 0)),
        'tagline': encode_utf8(item.data.get('tagline', '')),
        'episode': int(item.data.get('index', 0)),
        'aired': item.data.get('originallyAvailableAt', ''),
        'tvshowtitle': encode_utf8(item.data.get('grandparentTitle',
                                                 item.tree.get('grandparentTitle', ''))),
        'season': int(item.data.get('parentIndex', item.tree.get('parentIndex', 0))),
        'mediatype': 'episode',
        'playcount': int(int(item.data.get('viewCount', 0)) > 0),
        'cast': metadata['cast'],
        'director': ' / '.join(metadata['director']),
        'genre': ' / '.join(metadata['genre']),
        'writer': ' / '.join(metadata['writer']),
    }

    if item.data.get('sorttitle'):
        info_labels['sorttitle'] = encode_utf8(item.data.get('sorttitle'))

    prefix_sxee = (item.tree.get('mixedParents') == '1' or
                   context.settings.episode_sort_method() == 'plex')
    prefix_tvshow = (item.tree.get('parentIndex') != '1' and
                     context.params.get('mode') == '0')

    prefix_server = (context.params.get('mode') in COMBINED_SECTIONS and
                     context.settings.prefix_server_in_combined())

    if not library:
        if prefix_sxee:
            info_labels['title'] = '%sx%s %s' % \
                                   (info_labels['season'],
                                    str(info_labels['episode']).zfill(2), info_labels['title'])
            if prefix_tvshow:
                info_labels['title'] = '%s - %s' % \
                                       (info_labels['tvshowtitle'], info_labels['title'])

        if prefix_server:
            info_labels['title'] = '%s: %s' % (item.server.get_name(), info_labels['title'])

    # Gather some data
    view_offset = item.data.get('viewOffset', 0)
    duration = int(metadata['attributes'].get('duration', item.data.get('duration', 0))) / 1000

    art = _get_art(context, item)

    # Extra data required to manage other properties
    extra_data = {
        'type': 'Video',
        'source': 'tvepisodes',
        'thumb': art.get('thumb', ''),
        'fanart_image': art.get('fanart', ''),
        'banner': art.get('banner', ''),
        'season_thumb': art.get('season_thumb', ''),
        'key': item.data.get('key', ''),
        'ratingKey': str(item.data.get('ratingKey', 0)),
        'parentRatingKey': str(item.data.get('parentRatingKey', 0)),
        'grandparentRatingKey': str(item.data.get('grandparentRatingKey', 0)),
        'duration': duration,
        'resume': int(int(view_offset) / 1000),
        'season': info_labels.get('season'),
        'tvshowtitle': info_labels.get('tvshowtitle'),
        'additional_context_menus': {
            'go_to': item.url.endswith(('onDeck', 'recentlyAdded', 'recentlyViewed', 'newest'))
        },
    }

    if item.up_next is False:
        extra_data['parameters'] = {
            'up_next': str(item.up_next).lower()
        }

    if item.tree.tag == 'MediaContainer':
        extra_data.update({
            'library_section_uuid': item.tree.get('librarySectionUUID')
        })

    # Add extra media flag data
    if not context.settings.skip_flags():
        extra_data.update(get_media_data(metadata['attributes']))

    # Build any specific context menu entries
    context_menu = None
    if not context.settings.skip_context_menus():
        context_menu = ContextMenu(context, item.server, item.url, extra_data).menu

    extra_data['mode'] = MODES.PLAYLIBRARY
    if library:
        extra_data['path_mode'] = MODES.TXT_TVSHOWS_LIBRARY

    item_url = item.server.join_url(item.server.get_url_location(), extra_data['key'])

    gui_item = GUIItem(item_url, info_labels, extra_data, context_menu)
    gui_item.is_folder = False
    return create_gui_item(context, gui_item)


def _get_art(context, item):
    art = {
        'banner': '',
        'fanart': '',
        'season_thumb': '',
        'section_art': '',
        'thumb': '',
    }

    if not context.settings.skip_images():
        art.update({
            'banner': get_banner_image(context, item.server, item.tree),
            'fanart': get_fanart_image(context, item.server, item.data),
            'season_thumb': '',
            'section_art': get_fanart_image(context, item.server, item.tree),
            'thumb': get_thumb_image(context, item.server, item.data),
        })

        if '/:/resources/show-fanart.jpg' in art['section_art']:
            art['section_art'] = art.get('fanart', '')

        if art['fanart'] == '' or '-1' in art['fanart']:
            art['fanart'] = art.get('section_art', '')

        if (art.get('season_thumb', '') and
                '/:/resources/show.png' not in art.get('season_thumb', '')):
            art['season_thumb'] = get_thumb_image(context, item.server, {
                'thumb': art.get('season_thumb')
            })

        # get ALL SEASONS or TVSHOW thumb
        if (not art.get('season_thumb', '') and item.data.get('parentThumb', '') and
                '/:/resources/show.png' not in item.data.get('parentThumb', '')):
            art['season_thumb'] = \
                get_thumb_image(context, item.server, {
                    'thumb': item.data.get('parentThumb', '')
                })

        elif (not art.get('season_thumb', '') and item.data.get('grandparentThumb', '') and
              '/:/resources/show.png' not in item.data.get('grandparentThumb', '')):
            art['season_thumb'] = \
                get_thumb_image(context, item.server, {
                    'thumb': item.data.get('grandparentThumb', '')
                })

    return art
