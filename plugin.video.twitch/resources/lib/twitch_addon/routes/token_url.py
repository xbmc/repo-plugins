# -*- coding: utf-8 -*-
"""

    Copyright (C) 2012-2019 Twitch-on-Kodi

    This file is part of Twitch-on-Kodi (plugin.video.twitch)

    SPDX-License-Identifier: GPL-3.0-only
    See LICENSES/GPL-3.0-only for more information.
"""

from ..addon import utils
from ..addon.common import kodi
from ..addon.google_firebase import dynamic_links_short_url
from ..addon.utils import i18n


def route(api):
    redirect_uri = utils.get_redirect_uri()
    request_url = api.client.prepare_request_uri(redirect_uri=redirect_uri, scope=api.required_scopes)
    try:
        short_url = dynamic_links_short_url(request_url)
    except:
        short_url = None
    prompt_url = short_url if short_url else i18n('authorize_url_fail')

    _ = kodi.Dialog().ok(i18n('authorize_heading'), i18n('authorize_message') + '[CR]%s' % prompt_url)
    kodi.show_settings()
