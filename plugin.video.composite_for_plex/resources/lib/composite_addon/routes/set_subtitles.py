# -*- coding: utf-8 -*-
"""

    Copyright (C) 2011-2018 PleXBMC (plugin.video.plexbmc) by hippojay (Dave Hawes-Johnson)
    Copyright (C) 2018-2020 Composite (plugin.video.composite_for_plex)

    This file is part of Composite (plugin.video.composite_for_plex)

    SPDX-License-Identifier: GPL-2.0-or-later
    See LICENSES/GPL-2.0-or-later.txt for more information.
"""

from kodi_six import xbmcgui  # pylint: disable=import-error
from six import PY3

from ..addon.common import get_argv
from ..addon.logger import Logger
from ..addon.strings import encode_utf8
from ..addon.strings import i18n
from ..plex import plex

LOG = Logger()


def run(context):
    """
        Display a list of available Subtitle streams and allow a user to select one.
        The currently selected stream will be annotated with a *
    """

    context.plex_network = plex.Plex(context.settings, load=True)

    server_uuid = get_argv()[2]
    metadata_id = get_argv()[3]

    server = context.plex_network.get_server_from_uuid(server_uuid)
    tree = server.get_metadata(metadata_id)

    sub_list = ['']
    append_subtitle = sub_list.append
    display_list = ['None']
    append_label = display_list.append
    fl_select = False
    part_id = ''

    if PY3:
        subtitle_parts = tree.iter('Part')
    else:
        subtitle_parts = tree.getiterator('Part')

    for parts in subtitle_parts:

        part_id = parts.get('id')

        for streams in parts:

            if streams.get('streamType', '') == '3':

                stream_id = streams.get('id')
                lang = encode_utf8(streams.get('languageCode', i18n('Unknown')))
                LOG.debug('Detected Subtitle stream [%s] [%s]' % (stream_id, lang))

                if streams.get('format', streams.get('codec')) == 'idx':
                    LOG.debug('Stream: %s - Ignoring idx file for now' % stream_id)
                    continue

                append_subtitle(stream_id)

                if streams.get('selected') == '1':
                    fl_select = True
                    language = streams.get('language', i18n('Unknown')) + '*'
                else:
                    language = streams.get('language', i18n('Unknown'))

                append_label(language)
        break

    if not fl_select:
        display_list[0] = display_list[0] + '*'

    result = xbmcgui.Dialog().select(i18n('Select subtitle'), display_list)
    if result == -1:
        return

    LOG.debug('User has selected stream %s' % sub_list[result])
    server.set_subtitle_stream(part_id, sub_list[result])
