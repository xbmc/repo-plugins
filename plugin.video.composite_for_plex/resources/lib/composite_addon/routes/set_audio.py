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
        Display a list of available audio streams and allow a user to select one.
        The currently selected stream will be annotated with a *
    """

    context.plex_network = plex.Plex(context.settings, load=True)

    server_uuid = get_argv()[2]
    metadata_id = get_argv()[3]

    server = context.plex_network.get_server_from_uuid(server_uuid)
    tree = server.get_metadata(metadata_id)

    audio_list = []
    append_audio = audio_list.append
    display_list = []
    append_label = display_list.append
    part_id = ''

    if PY3:
        audio_parts = tree.iter('Part')
    else:
        audio_parts = tree.getiterator('Part')

    for parts in audio_parts:

        part_id = parts.get('id')

        for streams in parts:

            if streams.get('streamType', '') == '2':

                stream_id = streams.get('id')
                append_audio(stream_id)

                LOG.debug('Detected Audio stream [%s] [%s] ' %
                          (stream_id, streams.get('languageCode', 'Unknown')))

                language = '%s (%s %s)' % (encode_utf8(streams.get('language', i18n('Unknown'))),
                                           audio_codec(streams), audio_channels(streams))

                if streams.get('selected') == '1':
                    language = language + '*'

                append_label(language)
        break

    result = xbmcgui.Dialog().select(i18n('Select audio'), display_list)
    if result == -1:
        return

    LOG.debug('User has selected stream %s' % audio_list[result])
    server.set_audio_stream(part_id, audio_list[result])


def audio_channels(streams):
    if streams.get('channels', i18n('Unknown')) == '6':
        return '5.1'
    if streams.get('channels', i18n('Unknown')) == '7':
        return '6.1'
    if streams.get('channels', i18n('Unknown')) == '2':
        return 'Stereo'

    return streams.get('channels', i18n('Unknown'))


def audio_codec(streams):
    if streams.get('codec', i18n('Unknown')) == 'ac3':
        return 'AC3'

    if streams.get('codec', i18n('Unknown')) == 'dca':
        return 'DTS'

    return streams.get('codec', i18n('Unknown'))
