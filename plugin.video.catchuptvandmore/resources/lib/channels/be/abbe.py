# -*- coding: utf-8 -*-
# Copyright: (c) 2017, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
import re
import requests

from codequick import Resolver
from kodi_six import xbmcgui

# TO DO
# Add Paid contents ?

URL_ROOT = 'https://www.%s.be'

URL_COMPTE_LOGIN = URL_ROOT + '/Account/Login'

URL_LIVES = URL_ROOT + '/Live-Replay/'
# channel (lucky jack, ...)


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):

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

    if len(re.compile(r'file\: \"(.*?)\"').findall(resp3.text)) == 0:
        plugin.notify('ERROR', plugin.localize(30891))
        return False

    return re.compile(r'file\: \"(.*?)\"').findall(resp3.text)[0]
