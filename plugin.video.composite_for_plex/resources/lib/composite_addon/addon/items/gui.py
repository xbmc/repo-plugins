# -*- coding: utf-8 -*-
"""

    Copyright (C) 2011-2018 PleXBMC (plugin.video.plexbmc) by hippojay (Dave Hawes-Johnson)
    Copyright (C) 2018-2020 Composite (plugin.video.composite_for_plex)

    This file is part of Composite (plugin.video.composite_for_plex)

    SPDX-License-Identifier: GPL-2.0-or-later
    See LICENSES/GPL-2.0-or-later.txt for more information.
"""

import copy
import json

from six.moves.urllib_parse import quote
from six.moves.urllib_parse import urlparse

from ..common import get_argv
from ..constants import CONFIG
from ..logger import Logger
from ..strings import i18n
from ..strings import item_translate

LOG = Logger()


def create_gui_item(context, item):
    LOG.debug('Adding %s\n'
              'Info Labels: %s\n'
              'Extra: %s' %
              (item.info_labels.get('title', i18n('Unknown')),
               json.dumps(item.info_labels, indent=4),
               json.dumps(item.extra, indent=4)))

    url = _get_url(item)
    LOG.debug('URL to use for listing: %s' % url)

    title = item_translate(item.info_labels.get('title', i18n('Unknown')),
                           item.extra.get('source'), item.is_folder)

    if CONFIG['kodi_version'] >= 18:
        list_item = item.CONSTRUCTOR(title, offscreen=True)
    else:
        list_item = item.CONSTRUCTOR(title)

    # Set the properties of the item, such as summary, name, season, etc
    info_type, info_labels = _get_info(item)
    list_item.setInfo(type=info_type, infoLabels=info_labels)

    if (not context.settings.skip_flags() and
            not item.is_folder and
            item.extra.get('type', 'video').lower() == 'video'):
        stream_info = item.extra.get('stream_info', {})
        list_item.addStreamInfo('video', stream_info.get('video', {}))
        list_item.addStreamInfo('audio', stream_info.get('audio', {}))

    list_item.setArt(_get_art(item))

    if item.context_menu is not None:
        if not item.is_folder and item.extra.get('type', 'video').lower() == 'video':
            # Play Transcoded
            item.context_menu.insert(0, (i18n('Play Transcoded'),
                                         'PlayMedia(%s&transcode=1)' % url))
            LOG.debug('Setting transcode options to [%s&transcode=1]' % url)
        LOG.debug('Building Context Menus')
        list_item.addContextMenuItems(item.context_menu)

    item_properties = _get_properties(context, item)
    if CONFIG['kodi_version'] >= 18:
        list_item.setProperties(item_properties)
    else:
        set_property = list_item.setProperty
        _item_properties = item_properties.items()
        for key, value in _item_properties:
            set_property(key, value)

    if item.url.startswith('cmd:'):
        item.is_folder = False

    return url, list_item, item.is_folder


def _get_url(item):
    path_mode = item.extra.get('path_mode')
    plugin_url = get_argv()[0]
    url_parts = urlparse(plugin_url)
    plugin_url = 'plugin://%s/' % url_parts.netloc
    if path_mode and '/' in path_mode:
        plugin_url += path_mode.rstrip('/') + '/'

    # Create the URL to pass to the item
    if not item.is_folder and item.extra['type'] == 'image':
        url = item.url
    elif item.url.startswith('http') or item.url.startswith('file'):
        url = '%s?url=%s&mode=%s' % (plugin_url, quote(item.url), item.extra.get('mode', 0))
    else:
        url = '%s?url=%s&mode=%s' % (plugin_url, item.url, item.extra.get('mode', 0))

    if item.extra.get('parameters'):
        parameters = item.extra.get('parameters').items()
        for argument, value in parameters:
            url = '%s&%s=%s' % (url, argument, quote(value))

    return url


def _get_info(item):
    info_type = item.extra.get('type', 'Video')
    info_labels = copy.deepcopy(item.info_labels)

    if info_type.lower() == 'folder' or info_type.lower() == 'file':
        info_type = 'Video'
    elif info_type.lower() == 'image':
        info_type = 'Picture'

    if info_type == 'Video':
        if not info_labels.get('plot'):
            info_labels['plot'] = u'\u2008'
        if not info_labels.get('plotoutline'):
            info_labels['plotoutline'] = u'\u2008'

    return info_type, info_labels


def _get_art(item):
    fanart = item.extra.get('fanart_image', '')
    thumb = item.extra.get('thumb', CONFIG['icon'])
    banner = item.extra.get('banner', '')

    poster = item.extra.get('season_thumb', '')
    if not poster:
        if not item.is_folder:
            poster = item.extra.get('thumb', 'DefaultPoster.png')
        else:
            poster = thumb

    return {
        'fanart': fanart,
        'poster': poster,
        'banner': banner,
        'thumb': thumb,
        'icon': thumb
    }


def _get_properties(context, item):
    item_properties = {}

    # Music related tags
    if item.extra.get('type', '').lower() == 'music':
        item_properties['Artist_Genre'] = item.info_labels.get('genre', '')
        item_properties['Artist_Description'] = item.extra.get('plot', '')
        item_properties['Album_Description'] = item.extra.get('plot', '')

    # For all end items
    if not item.is_folder:
        item_properties['IsPlayable'] = 'true'

        if item.extra.get('type', 'video').lower() == 'video':
            item_properties['TotalTime'] = str(item.extra.get('duration'))
            item_properties['ResumeTime'] = str(item.extra.get('resume'))

            if not context.settings.skip_flags():
                LOG.debug('Setting VrR as : %s' % item.extra.get('VideoResolution', ''))
                item_properties['VideoResolution'] = item.extra.get('VideoResolution', '')
                item_properties['VideoCodec'] = item.extra.get('VideoCodec', '')
                item_properties['AudioCodec'] = item.extra.get('AudioCodec', '')
                item_properties['AudioChannels'] = item.extra.get('AudioChannels', '')
                item_properties['VideoAspect'] = item.extra.get('VideoAspect', '')

    if item.extra.get('source') == 'tvshows' or item.extra.get('source') == 'tvseasons':
        # Then set the number of watched and unwatched, which will be displayed per season
        item_properties['TotalEpisodes'] = str(item.extra['TotalEpisodes'])
        item_properties['WatchedEpisodes'] = str(item.extra['WatchedEpisodes'])
        item_properties['UnWatchedEpisodes'] = str(item.extra['UnWatchedEpisodes'])

        # Hack to show partial flag for TV shows and seasons
        if item.extra.get('partialTV') == 1:
            item_properties['TotalTime'] = '100'
            item_properties['ResumeTime'] = '50'

    if item.extra.get('season_thumb', ''):
        item_properties['seasonThumb'] = item.extra.get('season_thumb', '')

    if item.url.startswith('cmd:'):
        item_properties['IsPlayable'] = 'false'

    mediatype = item.info_labels.get('mediatype')
    if mediatype:
        item_properties['content_type'] = mediatype + 's'

    if item.extra.get('hash'):
        item_properties['hash'] = item.extra['hash']

    return item_properties
