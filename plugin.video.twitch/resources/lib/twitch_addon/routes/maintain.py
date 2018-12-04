# -*- coding: utf-8 -*-
"""

    Copyright (C) 2012-2018 Twitch-on-Kodi

    This file is part of Twitch-on-Kodi (plugin.video.twitch)

    SPDX-License-Identifier: GPL-3.0-only
    See LICENSES/GPL-3.0-only for more information.
"""
from ..addon.common import kodi
from ..addon.utils import i18n


def route(sub_mode, file_type):
    shortname = None
    filename = None
    if sub_mode == 'delete':
        if file_type.endswith('_search'):
            if file_type in ['streams_search', 'channels_search', 'games_search', 'id_url_search']:
                path = 'special://profile/addon_data/plugin.video.twitch/search/'
                shortname = file_type + '.sqlite'
                filename = kodi.translate_path(path + shortname)
        elif file_type.endswith('_json'):
            if file_type == 'storage_json':
                path = 'special://profile/addon_data/plugin.video.twitch/'
                shortname = 'storage.json'
                filename = kodi.translate_path(path + shortname)

    if filename and shortname:
        shortname = '\'[B]' + shortname + '[/B]\''
        confirmed = kodi.Dialog().yesno(i18n('confirm'), i18n('confirm_file_delete_') % shortname)
        if confirmed:
            result = kodi.delete_file(filename)
            if result:
                kodi.notify(msg=i18n('delete_succeeded_') % shortname, sound=False)
            else:
                kodi.notify(msg=i18n('delete_failed_') % shortname, sound=False)
