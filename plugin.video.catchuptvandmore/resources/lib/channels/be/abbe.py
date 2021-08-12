# -*- coding: utf-8 -*-
# Copyright: (c) 2017, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
import re
import json
import random
import urlquick
from hashlib import sha256
from codecs import encode as codec_encode
from codecs import decode as codec_decode

from codequick import Resolver
from kodi_six import xbmcgui
from resources.lib import web_utils
try:
    from urllib.parse import urlencode
except ImportError:
    from urllib import urlencode

# TO DO
# Add Paid contents ?

URL_ROOT = 'https://live-replay.%s.be'

URL_ROOT_LOGIN = 'https://app.auth.digital.abweb.com'

URL_CONNECT_AUTHORIZE = URL_ROOT_LOGIN + '/connect/authorize'

URL_ACCOUNT_LOGIN = URL_ROOT_LOGIN + '/Account/Login'

URL_CONNECT_TOKEN = URL_ROOT_LOGIN + '/connect/token'

URL_AUTH_CALLBACK = URL_ROOT + '/auth-callback'

URL_API = 'https://subscription.digital.api.abweb.com/api/subscription/has-live-rights/%s/%s'


def genparams(item_id):
    state = ''.join(random.choice('0123456789abcdef') for n in range(32))
    while True:
        code_verifier = ''.join(random.choice('0123456789abcdef') for n in range(96)).encode('utf-8')
        hashed = sha256(code_verifier).hexdigest()
        code_challenge = codec_encode(codec_decode(hashed, 'hex'), 'base64').decode("utf-8").strip().replace('=', '')
        # make sure that the hashed string doesn't contain + / =
        if not any(c in '+/=' for c in code_challenge):
            result = json.dumps(
                {
                    'code_verifier': code_verifier.decode("utf-8"),
                    "params": {
                        'client_id': item_id,
                        'redirect_uri': URL_AUTH_CALLBACK % item_id,
                        'response_type': 'code',
                        'scope': 'openid profile email',
                        'state': state,
                        'code_challenge': code_challenge,
                        'code_challenge_method': 'S256',
                        'response_mode': 'query',
                        'action': 'undefined'
                    }
                }
            )
            return result


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):

    # Using script (https://github.com/Catch-up-TV-and-More/plugin.video.catchuptvandmore/issues/484)

    # Create session
    session_urlquick = urlquick.Session()
    json_parser = json.loads(genparams(item_id))
    params = json_parser['params']
    paramsencoded = urlencode(params)

    # Get Token
    # KO - resp = session_urlquick.get(URL_COMPTE_LOGIN)
    resp = session_urlquick.get(URL_CONNECT_AUTHORIZE, params=params, max_age=-1)
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
        "button":
        'login'
    }
    paramslogin = {
        'ReturnUrl': '/connect/authorize/callback?%s' % paramsencoded
    }
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    resp2 = session_urlquick.post(URL_ACCOUNT_LOGIN,
                                  params=paramslogin,
                                  data=payload,
                                  headers=headers,
                                  verify=False)
    next_url = resp2.history[1].headers['location']
    code_value = re.compile(r'code\=(.*?)\&').findall(next_url)[0]
    code_verifier = json_parser['code_verifier']

    paramtoken = {
        'client_id': item_id,
        'code': code_value,
        'redirect_uri': URL_AUTH_CALLBACK % item_id,
        'code_verifier': code_verifier,
        'grant_type': 'authorization_code'
    }
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Referer': URL_ROOT % item_id,
        'User-Agent': web_utils.get_random_ua()
    }
    resp3 = session_urlquick.post(URL_CONNECT_TOKEN, headers=headers, data=paramtoken, max_age=-1)
    json_parser3 = json.loads(resp3.text)
    token = json_parser3['id_token']

    headers = {
        'Accept': 'application/json, text/plain, */*',
        'Authorization': 'Bearer %s' % token,
        'User-Agent': web_utils.get_random_ua(),
        'Referer': URL_AUTH_CALLBACK % item_id
    }
    resp4 = session_urlquick.get(URL_API % (item_id, item_id), headers=headers, max_age=-1)
    json_parser4 = json.loads(resp4.text)
    return json_parser4['hlsUrl']
