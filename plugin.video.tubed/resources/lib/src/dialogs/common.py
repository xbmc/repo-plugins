# -*- coding: utf-8 -*-
"""
    Copyright (C) 2020 Tubed (plugin.video.tubed)

    This file is part of plugin.video.tubed

    SPDX-License-Identifier: GPL-2.0-only
    See LICENSES/GPL-2.0-only.txt for more information.
"""

import os

import pyxbmct.addonwindow as pyxbmct  # pylint: disable=import-error
import xbmcgui  # pylint: disable=import-error

from ..constants import ADDON_ID
from . import DialogActiveException

PROPERTY_ACTIVE = '-'.join([ADDON_ID, 'dialog_active'])


class AddonFullWindow(pyxbmct.AddonFullWindow):

    def __enter__(self):
        if self.window.getProperty(PROPERTY_ACTIVE) == 'true':
            raise DialogActiveException

        self.window.setProperty(PROPERTY_ACTIVE, 'true')
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.window.clearProperty(PROPERTY_ACTIVE)


class RadioButton(pyxbmct.CompareMixin, xbmcgui.ControlRadioButton):

    def __new__(cls, *args, **kwargs):
        kwargs.update({
            'focusOnTexture': os.path.join(pyxbmct.skin.images,
                                           'RadioButton', 'MenuItemFO.png'),
            'noFocusOnTexture': os.path.join(pyxbmct.skin.images,
                                             'RadioButton', 'radiobutton-focus.png'),
            'focusOffTexture': os.path.join(pyxbmct.skin.images,
                                            'RadioButton', 'radiobutton-focus.png'),
            'noFocusOffTexture': os.path.join(pyxbmct.skin.images,
                                              'RadioButton', 'radiobutton-nofocus.png')
        })
        return super(RadioButton, cls).__new__(cls, -10, -10, 1, 1, *args, **kwargs)


# currently required until pyxbmct is updated to remove deprecated textures
pyxbmct.RadioButton = RadioButton


def open_dialog(context, dialog_class, **kwargs):
    try:
        with dialog_class(context=context, window=xbmcgui.Window(10000), **kwargs) as dialog:
            payload = dialog.start()

    except DialogActiveException:
        payload = None

    except AttributeError:
        payload = None

    return payload
