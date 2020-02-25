# -*- coding: utf-8 -*-
"""

    Copyright (C) 2011-2018 PleXBMC (plugin.video.plexbmc) by hippojay (Dave Hawes-Johnson)
    Copyright (C) 2018-2019 Composite (plugin.video.composite_for_plex)

    This file is part of Composite (plugin.video.composite_for_plex)

    SPDX-License-Identifier: GPL-2.0-or-later
    See LICENSES/GPL-2.0-or-later.txt for more information.
"""

from kodi_six import xbmc  # pylint: disable=import-error
from kodi_six import xbmcgui  # pylint: disable=import-error

from ..addon.common import get_argv
from ..addon.logger import Logger
from ..addon.strings import i18n
from ..plex import plex

LOG = Logger()


def run(context):
    context.plex_network = plex.Plex(context.settings, load=True)

    server_uuid = get_argv()[2]
    metadata_id = get_argv()[3]

    LOG.debug('Deleting media at: %s' % metadata_id)

    result = xbmcgui.Dialog().yesno(i18n('Confirm file delete?'),
                                    i18n('Delete this item? This action will delete media '
                                         'and associated data files.'))

    if result:
        LOG.debug('Deleting....')
        server = context.plex_network.get_server_from_uuid(server_uuid)
        server.delete_metadata(metadata_id)
        xbmc.executebuiltin('Container.Refresh')
