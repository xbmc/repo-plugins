# -*- coding: utf-8 -*-
"""

    Copyright (C) 2012-2018 Twitch-on-Kodi

    This file is part of Twitch-on-Kodi (plugin.video.twitch)

    SPDX-License-Identifier: GPL-3.0-only
    See LICENSES/GPL-3.0-only for more information.
"""
from ..addon import utils
from ..addon.common import kodi
from ..addon.googl_shorten import googl_url
from ..addon.utils import i18n


def route(api):
    redirect_uri = utils.get_redirect_uri()
    request_url = api.client.prepare_request_uri(redirect_uri=redirect_uri, scope=api.required_scopes)
    try:
        short_url = googl_url(request_url)
    except:
        short_url = None
    prompt_url = short_url if short_url else i18n('authorize_url_fail')
    result = kodi.Dialog().ok(heading=i18n('authorize_heading'), line1=i18n('authorize_message'),
                              line2=' %s' % prompt_url)
    kodi.show_settings()
