# -*- coding: utf-8 -*-
"""

    Copyright (C) 2011-2018 PleXBMC (plugin.video.plexbmc) by hippojay (Dave Hawes-Johnson)
    Copyright (C) 2018-2019 Composite (plugin.video.composite_for_plex)

    This file is part of Composite (plugin.video.composite_for_plex)

    SPDX-License-Identifier: GPL-2.0-or-later
    See LICENSES/GPL-2.0-or-later.txt for more information.
"""

from kodi_six import xbmcgui  # pylint: disable=import-error

from ..addon.logger import Logger
from ..addon.strings import i18n
from ..plex import plex
from ..plex import plexsignin

LOG = Logger()


def run(context):
    _dialog = xbmcgui.Dialog()
    context.plex_network = plex.Plex(context.settings, load=False)

    has_access = True
    if not context.plex_network.is_myplex_signedin():
        has_access = False
        result = _dialog.yesno(i18n('Manage myPlex'),
                               i18n('You are not currently logged into myPlex. '
                                    'Continue to sign in, or cancel to return'))
        if result:
            has_access = plexsignin.sign_in_to_plex(context, refresh=False)
            context.plex_network = plex.Plex(context.settings, load=False)

    elif not context.plex_network.is_admin():
        has_access = False
        _ = _dialog.ok(i18n('Manage myPlex'),
                       i18n('To access these screens you must be logged in as '
                            'an admin user. Switch user and try again'))

    if has_access:
        plexsignin.manage_plex(context)
