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
    if action == 'change':
        current_language = utils.get_language()
        valid_languages = Language.valid()
        missing_languages = [language for language in valid_languages if language != current_language]
        result = kodi.Dialog().select(i18n('change_languages'), missing_languages)
        if result > -1:
            utils.change_language(missing_languages[result])
