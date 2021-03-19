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

URL_ROOT = 'http://www.abweb.com'

URL_COMPTE_LOGIN = URL_ROOT + '/BIS-TV-Online/identification.aspx'

URL_LIVES = URL_ROOT + '/BIS-TV-Online/bistvo-tele-universal.aspx'
# channel (lucky jack, ...)


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):

    # Live TV Not working / find a way to dump html received

    # Create session
    # KO - session_urlquick = urlquick.Session()
    session_requests = requests.session()

    # Get Token
    # KO - resp = session_urlquick.get(URL_COMPTE_LOGIN)
    resp = session_requests.get(URL_COMPTE_LOGIN)
    view_state_value = re.compile(
        r'id\=\"\_\_VIEWSTATE\" value\=\"(.*?)\"').findall(resp.text)[0]
    view_state_generator_value = re.compile(
        r'id\=\"\_\_VIEWSTATEGENERATOR\" value\=\"(.*?)\"').findall(
            resp.text)[0]
    event_validation_value = re.compile(
        r'id\=\"\_\_EVENTVALIDATION\" value\=\"(.*?)\"').findall(resp.text)[0]

    if plugin.setting.get_string('abweb.login') == '' or \
            plugin.setting.get_string('abweb.password') == '':
        xbmcgui.Dialog().ok(
            'Info',
            plugin.localize(30604) %
            ('ABWeb', 'http://www.abweb.com/BIS-TV-Online/abonnement.aspx'))
        return False

    # Build PAYLOAD
    payload = {
        "ctl00$ContentPlaceHolder1$Login1$UserName":
        plugin.setting.get_string('abweb.login'),
        "ctl00$ContentPlaceHolder1$Login1$Password":
        plugin.setting.get_string('abweb.password'),
        "__EVENTTARGET":
        '',
        "__EVENTARGUMENT":
        '',
        "__VIEWSTATE":
        view_state_value,
        "__VIEWSTATEGENERATOR":
        view_state_generator_value,
        "__EVENTVALIDATION":
        event_validation_value,
        "ctl00$Login1$UserName":
        '',
        "ctl00$Login1$Password":
        '',
        "ctl00$ContentPlaceHolder1$Login1$LoginButton.x":
        '15',
        "ctl00$ContentPlaceHolder1$Login1$LoginButton.y":
        '12',
        "ctl00$ContentPlaceHolder1$Login1$RememberMe":
        'on'
    }

    # LOGIN
    # KO - resp2 = session_urlquick.post(
    #     URL_COMPTE_LOGIN, data=payload,
    #     headers={'User-Agent': web_utils.get_ua, 'referer': URL_COMPTE_LOGIN})
    resp2 = session_requests.post(URL_COMPTE_LOGIN,
                                  data=payload,
                                  headers=dict(referer=URL_COMPTE_LOGIN),
                                  verify=False)
    if 'tentative' in repr(resp2.text):
        plugin.notify('ERROR', 'ABWeb : ' + plugin.localize(30711))
        return False

    resp3 = session_requests.get(URL_LIVES)

    if item_id == 'luckyjack':
        chnid_value = re.compile(r'luckyjack\'\,\'(.*?)\'').findall(
            resp3.text)[0]

        payload = {'chn': 'luckyjack', 'chnid': chnid_value}
        resp4 = session_requests.post(
            URL_LIVES,
            params=payload,
            headers=dict(
                referer='http://www.abweb.com/BIS-TV-Online/bistvo-tele-universal.aspx'
            ))
        stream_datas_url = 'http:' + re.compile(
            r'id\=\"ifr_stream\" src\=\"(.*?)\"').findall(resp4.text)[0]
        resp5 = session_requests.get(stream_datas_url)
        return re.compile(r'\"file\"\: \"(.*?)\"').findall(resp5.text)[0]

    return False
