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
    logged_in = context.api.logged_in
    tv_logged_in = context.api.tv_logged_in

    signed_in = False
    tv_signed_in = False

    if not logged_in:
        signed_in = open_dialog(context, SignInDialog)

    if not tv_logged_in:
        tv_signed_in = open_dialog(context, SignInDialog, tv_client=True)

    if signed_in or tv_signed_in:
        xbmc.executebuiltin('Container.Refresh')
