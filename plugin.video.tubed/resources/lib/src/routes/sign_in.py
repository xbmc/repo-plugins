# -*- coding: utf-8 -*-
"""
    Copyright (C) 2020 Tubed (plugin.video.tubed)

    This file is part of plugin.video.tubed

    SPDX-License-Identifier: GPL-2.0-only
    See LICENSES/GPL-2.0-only.txt for more information.
"""

import xbmc  # pylint: disable=import-error

from ..dialogs.common import open_dialog
from ..dialogs.sign_in import SignInDialog


def invoke(context):
    signed_in = open_dialog(context, SignInDialog)

    if signed_in:
        xbmc.executebuiltin('Container.Refresh')
