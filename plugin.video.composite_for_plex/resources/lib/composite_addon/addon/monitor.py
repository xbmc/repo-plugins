# -*- coding: utf-8 -*-
"""

    Copyright (C) 2019 Composite (plugin.video.composite_for_plex)

    This file is part of Composite (plugin.video.composite_for_plex)

    SPDX-License-Identifier: GPL-2.0-or-later
    See LICENSES/GPL-2.0-or-later.txt for more information.
"""

from kodi_six import xbmc  # pylint: disable=import-error

from .constants import CONFIG
from .logger import Logger


class Monitor(xbmc.Monitor):
    LOG = Logger('Monitor')

    def __init__(self, settings):
        self.settings = settings

    def __str__(self):
        """ pylint: too-few-public-methods """

    def onNotification(self, sender, method, data):  # pylint: disable=invalid-name
        """
        Handle any notifications directed to this add-on
        """
        if CONFIG['id'] not in method:
            return

        self.LOG.debug('Notification from %s: %s -> %s' % (sender, method, data))
