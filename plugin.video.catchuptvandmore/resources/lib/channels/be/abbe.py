# -*- coding: utf-8 -*-
"""
    Catch-up TV & More
    Copyright (C) 2017  SylvainCecchetto

    This file is part of Catch-up TV & More.

    Catch-up TV & More is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

    Catch-up TV & More is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License along
    with Catch-up TV & More; if not, write to the Free Software Foundation,
    Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
"""

# The unicode_literals import only has
# an effect on Python 2.
# It makes string literals as unicode like in Python 3
from __future__ import unicode_literals

from codequick import Route, Resolver, Listitem, utils, Script


from resources.lib import web_utils
from resources.lib import download
from resources.lib.menu_utils import item_post_treatment

import json
import re
import requests
import urlquick
from kodi_six import xbmcgui

# TO DO
# Add Paid contents ?

URL_ROOT = 'https://www.%s.be'

URL_COMPTE_LOGIN = URL_ROOT + '/Account/Login'

URL_LIVES = URL_ROOT + '/Live-Replay/'
# channel (lucky jack, ...)


def live_entry(plugin, item_id, **kwargs):
    return get_live_url(plugin, item_id, item_id.upper())


@Resolver.register
def get_live_url(plugin, item_id, video_id, **kwargs):

    # Live TV Not working / find a way to dump html received

    # Create session
    # KO - session_urlquick = urlquick.Session()
    session_requests = requests.session()

    # Get Token
    # KO - resp = session_urlquick.get(URL_COMPTE_LOGIN)
    resp = session_requests.get(URL_COMPTE_LOGIN % item_id)
    value_token = re.compile(
        r'__RequestVerificationToken\" type\=\"hidden\" value\=\"(.*?)\"').findall(resp.text)[0]

    if plugin.setting.get_string('abweb.login') == '' or \
            plugin.setting.get_string('abweb.password') == '':
        xbmcgui.Dialog().ok(
            'Info',
            plugin.localize(30604) %
            ('ABWeb', 'http://www.abweb.com/BIS-TV-Online/abonnement.aspx'))
        return False

    # Build PAYLOAD
    payload = {
        "__RequestVerificationToken":
        value_token,
        "Email":
        plugin.setting.get_string('abweb.login'),
        "Password":
        plugin.setting.get_string('abweb.password'),
        "login-submit":
        'Se connecter'
    }

    # LOGIN
    # KO - resp2 = session_urlquick.post(
    #     URL_COMPTE_LOGIN, data=payload,
    #     headers={'User-Agent': web_utils.get_ua, 'referer': URL_COMPTE_LOGIN})
    resp2 = session_requests.post(URL_COMPTE_LOGIN % item_id,
                                  data=payload,
                                  headers=dict(referer=URL_COMPTE_LOGIN),
                                  verify=False)
    if 'tentative' in repr(resp2.text):
        plugin.notify('ERROR', 'ABWeb : ' + plugin.localize(30711))
        return False

    resp3 = session_requests.get(URL_LIVES % item_id)

    if len(re.compile(r'file\: \"(.*?)\"').findall(resp3.text)) > 0:
        return re.compile(r'file\: \"(.*?)\"').findall(resp3.text)[0]
    else:
        plugin.notify('ERROR', plugin.localize(30891))
        return False
