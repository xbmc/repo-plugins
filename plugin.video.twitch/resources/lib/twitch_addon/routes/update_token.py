# -*- coding: utf-8 -*-
from ..addon.common import kodi
from ..addon.utils import i18n


def route(oauth_token):
    kodi.set_setting('oauth_token', oauth_token)
    kodi.notify(msg=i18n('token_updated'))
