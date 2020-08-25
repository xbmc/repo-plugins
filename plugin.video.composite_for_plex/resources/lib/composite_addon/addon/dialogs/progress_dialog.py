# -*- coding: utf-8 -*-
"""

    Copyright (C) 2020 Composite (plugin.video.composite_for_plex)

    This file is part of Composite (plugin.video.composite_for_plex)

    SPDX-License-Identifier: GPL-2.0-or-later
    See LICENSES/GPL-2.0-or-later.txt for more information.
"""

import time

from kodi_six import xbmcgui  # pylint: disable=import-error


class ProgressDialog:
    dialog = None

    def __init__(self, heading, line1='', line2='', line3='',
                 background=False, active=True, delay=0):

        self._active = active
        self._background = background

        self._heading = heading
        self._message = self._create_message(line1, line2, line3)

        self._delay = delay
        self._start_timestamp = time.time()

        self.__percent = 0

        if self._active and self._delay < 1:
            self.dialog = self._create_dialog()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.dialog is not None:
            self.dialog.close()

    @property
    def percent(self):
        return self.__percent

    def _create_message(self, line1='', line2='', line3=''):
        _message_joint = ' ' if self._background else '[CR]'

        return _message_joint.join([line1, line2, line3])

    def _create_dialog(self):
        dialog = xbmcgui.DialogProgressBG() if self._background else xbmcgui.DialogProgress()
        dialog.create(self._heading, self._message)

        self.__percent = 0

        return dialog

    def is_canceled(self):
        if self.dialog is not None and not self._background:
            return self.dialog.iscanceled()

        return False

    def update(self, percent, line1, line2='', line3=''):
        if self.dialog is None and 0 < self._delay <= (time.time() - self._start_timestamp):
            self.dialog = self._create_dialog()

        if self.dialog is not None:
            message = self._create_message(line1, line2, line3)
            percent = self._limiter(percent, upper_limit=100)

            if self._background:
                self.dialog.update(percent, self._heading, message)
            else:
                self.dialog.update(percent, message)

            self.__percent = percent

    @staticmethod
    def _limiter(value, upper_limit, lower_limit=0):
        return upper_limit if value > upper_limit else lower_limit if value < lower_limit else value
