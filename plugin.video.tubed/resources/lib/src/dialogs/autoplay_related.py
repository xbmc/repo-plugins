# -*- coding: utf-8 -*-
"""
    Copyright (C) 2020 Tubed (plugin.video.tubed)

    This file is part of plugin.video.tubed

    SPDX-License-Identifier: GPL-2.0-only
    See LICENSES/GPL-2.0-only.txt for more information.
"""

import os
import threading

import pyxbmct.addonwindow as pyxbmct  # pylint: disable=import-error
import xbmc  # pylint: disable=import-error

from ..constants import MEDIA_PATH
from ..constants.demo import VIDEO_ITEM
from .common import AddonFullWindow
from .utils import add_related_video_to_playlist
from .utils import int_to_shortform_string

ACTION_STOP = 13


class AutoplayRelated(AddonFullWindow):

    def __init__(self, context, window, **kwargs):
        self._context = context
        self.window = window

        self.demo = kwargs.get('mode') == 'demo'

        if self.demo:
            self.video_id = VIDEO_ITEM['id']

        else:
            self.video_id = kwargs.get('video_id')
            if not self.video_id:
                return

        self.title = context.i18n('Up Next')

        super().__init__(self.title)

        self.l_video_title = None
        self.l_channel_name = None
        self.l_premiered = None
        self.l_video_description = None
        self.l_video_thumbnail = None
        self.l_video_statistics = None

        self.spinner_image = pyxbmct.Image(os.path.join(MEDIA_PATH, 'spinner.gif'))

        self.select_button = pyxbmct.Button('')

        self.metadata = {}

        self.thread = None
        self._selected = False

    @property
    def context(self):
        return self._context

    @context.setter
    def context(self, value):
        self._context = value

    def start(self):
        self.metadata = add_related_video_to_playlist(self.context, self.video_id, self.demo)
        if not self.metadata:
            return False

        xbmc.executebuiltin('Dialog.Close(all,true)')

        self.setGeometry(800, 320, 64, 160)

        self.set_controls()

        self.set_navigation()

        self.connect(pyxbmct.ACTION_NAV_BACK, self.close)
        self.connect(ACTION_STOP, self.close)

        self.thread = DialogThread(self.context, self.selected, self.close, self.demo)

        self.doModal()

        self.thread.stop()
        self.thread.join()

        if self._selected:
            return True

        return False

    def set_controls(self):

        self.placeControl(self.select_button, 12, 3, rowspan=50, columnspan=67)
        self.connect(self.select_button, self.selected)

        self.l_video_thumbnail = pyxbmct.Image(self.metadata.get('thumbnail', ''))
        self.placeControl(self.l_video_thumbnail, 12, 3, rowspan=50, columnspan=67)

        self.placeControl(self.spinner_image, 49, 57, rowspan=10, columnspan=10)

        self.l_video_title = pyxbmct.FadeLabel(
            font='font30_title',
        )
        self.placeControl(self.l_video_title, 3, 3, columnspan=190)
        self.l_video_title.addLabel(self.metadata.get('title'))

        self.l_channel_name = pyxbmct.FadeLabel(
            font='font25_title',
        )
        self.placeControl(self.l_channel_name, 12, 73, columnspan=95)
        self.l_channel_name.addLabel(self.metadata.get('channel_name'))

        self.l_premiered = pyxbmct.Label(
            self.metadata.get('premiered'),
            font='font20_title',
            alignment=3,
        )
        self.placeControl(self.l_premiered, 12, 157, columnspan=27)

        self.l_video_statistics = pyxbmct.Label(
            '%s %s / %s %s / %s %s' %
            (int_to_shortform_string(self.metadata.get('like_count')),
             self.context.i18n('likes'),
             int_to_shortform_string(self.metadata.get('dislike_count')),
             self.context.i18n('dislikes'),
             int_to_shortform_string(self.metadata.get('view_count')),
             self.context.i18n('views')),
            font='font20_title',
            alignment=2,
        )
        self.placeControl(self.l_video_statistics, 19, 73, columnspan=122)

        self.l_video_description = pyxbmct.TextBox(
            font='font10'
        )
        self.l_video_description.setText(self.metadata.get('description'))
        self.placeControl(self.l_video_description, 26, 73, rowspan=35, columnspan=122)
        self.l_video_description.autoScroll(1000, 5500, 500)

    def set_navigation(self):
        self.select_button.setNavigation(self.select_button, self.select_button,
                                         self.select_button, self.select_button)
        self.setFocus(self.select_button)

    def selected(self):
        self._selected = True
        self.close()


class DialogThread(threading.Thread):
    def __init__(self, context, success_event, fail_event, demo=False):
        super().__init__()

        self._stopped = threading.Event()
        self._ended = threading.Event()

        self.context = context
        self.success_event = success_event
        self.fail_event = fail_event

        self.demo = demo

        self.monitor = xbmc.Monitor()

        self.daemon = True
        self.start()

    def abort_now(self):
        return self.monitor.abortRequested() or self.stopped()

    def run(self):
        if self.demo:
            while True:
                if self.abort_now():
                    break

                xbmc.sleep(1000)

        else:
            for _ in range(7):
                # self.update_progress(int(float((100.0 // steps)) * index))

                if self.abort_now():
                    break

                xbmc.sleep(1000)

        if not self.abort_now():
            self.success_event()
        else:
            self.fail_event()

        self.end()

    def stop(self):
        self._stopped.set()

    def stopped(self):
        return self._stopped.is_set()

    def end(self):
        if not self._stopped.is_set():
            self._stopped.set()

        self._ended.set()

    def ended(self):
        return self._ended.is_set()
