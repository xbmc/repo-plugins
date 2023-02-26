# -*- coding: utf-8 -*-
"""
    Copyright (C) 2020 Tubed (plugin.video.tubed)

    This file is part of plugin.video.tubed

    SPDX-License-Identifier: GPL-2.0-only
    See LICENSES/GPL-2.0-only.txt for more information.
"""

import xbmc  # pylint: disable=import-error
import xbmcgui  # pylint: disable=import-error

from ..constants.media import LOGO_SMALL
from ..lib.txt_fmt import bold
from ..lib.url_utils import unquote


def invoke(context, setting_id, menu_title):
    if '%' in menu_title:
        menu_title = unquote(menu_title)

    context.settings.show_main_menu_item(setting_id, False)

    xbmcgui.Dialog().notification(
        menu_title,
        context.i18n('%s was hidden from the main menu') % bold(menu_title),
        LOGO_SMALL,
        sound=False
    )

    xbmc.executebuiltin('Container.Refresh')
