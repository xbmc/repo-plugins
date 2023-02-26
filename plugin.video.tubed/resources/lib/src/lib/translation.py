# -*- coding: utf-8 -*-
"""
    Copyright (C) 2020 Tubed (plugin.video.tubed)

    This file is part of plugin.video.tubed

    SPDX-License-Identifier: GPL-2.0-only
    See LICENSES/GPL-2.0-only.txt for more information.
"""

import xbmc  # pylint: disable=import-error
import xbmcaddon  # pylint: disable=import-error

from ..constants import STRINGS
from .logger import Log

LOG = Log('lib', __file__)


class Translator:

    def __init__(self, addon=None):
        self._addon = addon

    def i18n(self, string_id):
        string_msgctxt = STRINGS.get(string_id)

        try:
            if int(string_msgctxt) < 30000:
                return xbmc.getLocalizedString(string_msgctxt)

        except (ValueError, TypeError):
            LOG.error('String is not properly localized: %s' % string_id)
            return string_id

        localized = self.addon.getLocalizedString(string_msgctxt)
        if not localized:
            LOG.error('String is not properly localized: %s' % string_id)
            return string_id

        return localized

    @property
    def addon(self):
        if not self._addon:
            self._addon = xbmcaddon.Addon()
        return self._addon
