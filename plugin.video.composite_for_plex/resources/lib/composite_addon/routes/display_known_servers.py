# -*- coding: utf-8 -*-
"""

    Copyright (C) 2011-2018 PleXBMC (plugin.video.plexbmc) by hippojay (Dave Hawes-Johnson)
    Copyright (C) 2018-2020 Composite (plugin.video.composite_for_plex)

    This file is part of Composite (plugin.video.composite_for_plex)

    SPDX-License-Identifier: GPL-2.0-or-later
    See LICENSES/GPL-2.0-or-later.txt for more information.
"""

from kodi_six import xbmc  # pylint: disable=import-error
from kodi_six import xbmcgui  # pylint: disable=import-error

from ..addon.logger import Logger
from ..addon.strings import i18n
from ..plex import plex

LOG = Logger()


def run(context):
    context.plex_network = plex.Plex(context.settings, load=True)
    servers = context.plex_network.get_server_list()

    display_list = []
    append_server = display_list.append
    for server in servers:
        name = server.get_name()
        log_status = server.get_status()
        status_label = i18n(log_status)

        if server.is_secure():
            log_secure = 'SSL'
            secure_label = i18n(log_secure)
        else:
            log_secure = 'Not Secure'
            secure_label = i18n(log_secure)

        LOG.debug('Device: %s [%s] [%s]' % (name, log_status, log_secure))
        LOG.debugplus('Full device dump [%s]' % server.__dict__)

        append_server('%s [%s] [%s]' % (name, status_label, secure_label))

    xbmcgui.Dialog().select(i18n('Known server list'), display_list)

    xbmc.executebuiltin('Container.Refresh')
