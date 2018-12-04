# -*- coding: utf-8 -*-
"""

    Copyright (C) 2012-2018 Twitch-on-Kodi

    This file is part of Twitch-on-Kodi (plugin.video.twitch)

    SPDX-License-Identifier: GPL-3.0-only
    See LICENSES/GPL-3.0-only for more information.
"""
from ..addon import utils
from ..addon.common import kodi
from ..addon.utils import i18n

from twitch.api.parameters import Language


def route(action):
    if action == 'add':
        current_languages = utils.get_languages()
        valid_languages = Language.valid()
        missing_languages = [language for language in valid_languages if language not in current_languages]
        result = kodi.Dialog().select(i18n('add_language'), missing_languages)
        if result > -1:
            utils.add_language(missing_languages[result])
    elif action == 'remove':
        current_languages = utils.get_languages()
        result = kodi.Dialog().select(i18n('remove_language'), current_languages)
        if result > -1:
            utils.remove_language(current_languages[result])
