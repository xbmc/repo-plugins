# -*- coding: utf-8 -*-
"""

    Copyright (C) 2011-2018 PleXBMC (plugin.video.plexbmc) by hippojay (Dave Hawes-Johnson)
    Copyright (C) 2018-2020 Composite (plugin.video.composite_for_plex)

    This file is part of Composite (plugin.video.composite_for_plex)

    SPDX-License-Identifier: GPL-2.0-or-later
    See LICENSES/GPL-2.0-or-later.txt for more information.
"""

from kodi_six import xbmcplugin  # pylint: disable=import-error
from six import PY3

from ..addon.common import get_handle
from ..addon.constants import MODES
from ..addon.containers import GUIItem
from ..addon.items.common import get_fanart_image
from ..addon.items.common import get_link_url
from ..addon.items.common import get_thumb_image
from ..addon.items.gui import create_gui_item
from ..addon.strings import i18n
from ..addon.utils import get_xml
from ..plex import plex


def run(context, url):
    context.plex_network = plex.Plex(context.settings, load=True)
    server = context.plex_network.get_server_from_url(url)

    tree = get_xml(context, url)
    if tree is None:
        return

    items = []
    append_item = items.append
    if PY3:
        directories = tree.iter('Directory')
    else:
        directories = tree.getiterator('Directory')

    for channels in directories:

        if channels.get('local', '') == '0' or channels.get('size', '0') == '0':
            continue

        extra_data = {
            'fanart_image': get_fanart_image(context, server, channels),
            'thumb': get_thumb_image(context, server, channels)
        }

        details = {
            'title': channels.get('title', i18n('Unknown'))
        }

        suffix = channels.get('key').split('/')[1]

        if channels.get('unique', '') == '0':
            details['title'] = '%s (%s)' % (details['title'], suffix)

        # Alter data sent into get_link_url, as channels use path rather than key
        path_data = {
            'key': channels.get('key'),
            'identifier': channels.get('key')
        }
        p_url = get_link_url(server, url, path_data)

        extra_data['mode'] = MODES.GETCONTENT
        if suffix == 'photos':
            extra_data['mode'] = MODES.PHOTOS
        elif suffix == 'video':
            extra_data['mode'] = MODES.PLEXPLUGINS
        elif suffix == 'music':
            extra_data['mode'] = MODES.MUSIC

        gui_item = GUIItem(p_url, details, extra_data)
        append_item(create_gui_item(context, gui_item))

    if items:
        xbmcplugin.addDirectoryItems(get_handle(), items, len(items))

    xbmcplugin.endOfDirectory(get_handle(), cacheToDisc=context.settings.cache_directory())
