# -*- coding: utf-8 -*-
# Copyright: (c) 2026
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals

import base64
import html
import json
import re
import requests
import urlquick
from codequick import Listitem, Resolver
from datetime import datetime, timedelta, timezone
from kodi_six import xbmcgui
from urllib.parse import urlencode

from resources.lib.kodi_utils import (INPUTSTREAM_PROP, get_selected_item_art,
                                      get_selected_item_info,
                                      get_selected_item_label)

from resources.lib import web_utils

URL_ROOT = 'https://www.rte.ie'
WEB_CONFIG_JSON = URL_ROOT + "/wordpress/wp-content/uploads/standard/web/config.json"
URL_API_ANONYMOUS_LOGIN = URL_ROOT + '/servicelayer/api/anonymouslogin'
URL_LICENSE = "https://widevine.entitlement.eu.theplatform.com/wv/web/ModularDrm"
URL_ALL_LIVE_SCHEDULES = "https://feed.entertainment.tv.theplatform.eu/f/1uC-gC/rte-prd-prd-all-schedules"
LICENSE_HEADERS = "Content-Type=application/json"

GENERIC_HEADERS = {'User-Agent': web_utils.get_random_windows_ua()}


def get_account():
    json_response = requests.get("%s" % WEB_CONFIG_JSON, headers=GENERIC_HEADERS).json()
    return json_response["mpx_config"]["account_id"]


def get_token():
    return requests.get(URL_API_ANONYMOUS_LOGIN, headers=GENERIC_HEADERS).json()["mpx_token"]


def get_manifest_and_pid(plugin, media_url, account, token):
    headers = {
        'authorization': 'Basic ' + base64.b64encode((account + ':' + token).encode()).decode(),
    }

    params = {
        'format': 'SMIL',
        'embedded': 'true',
        'tracking': 'true',
        'formats': 'mpeg-dash',
        'appVers': 'P_Web_3 3.164.2',
        'policy': '123034966',
        'iu': '/3014/RTE_Player_Live/Desktop_Web/NotRegistered',
    }

    response = requests.get(media_url, params=params, headers=headers)
    media_html = response.text

    if "GeoLocationBlocked" in media_html:
        plugin.notify("ERROR", plugin.localize(30713))
        return None, None

    manifest_match = re.search(r'src="(https?://[^/"]+[^"]*?\.mpd\?[^"]+)"', media_html)
    pid_match = re.search(r'(?<=\bpid=)[^|"]+', media_html)

    if manifest_match and pid_match:
        manifest = html.unescape(manifest_match.group(1))
        pid = pid_match.group(0)
        return manifest, pid
    return None, None


def build_rte_list_item(plugin, media_url) -> Listitem:
    account = get_account()
    token = get_token()

    manifest, pid = get_manifest_and_pid(plugin, media_url, account, token)

    if manifest is None or pid is None:
        return None

    return get_the_platform_list_item(manifest, pid, account, token)


def get_the_platform_list_item(manifest, pid, account, token) -> Listitem:
    params = {
        "token": token,
        "account": account,
        "form": "json",
        "schema": "1.0",
    }

    license_url = f"{URL_LICENSE}?{urlencode(params)}"

    payload = json.dumps({
        "getWidevineLicense": {
            "releasePid": pid,
            "widevineChallenge": "b{SSM}"
        }
    })

    item = Listitem()
    item.path = manifest
    item.property[INPUTSTREAM_PROP] = 'inputstream.adaptive'
    item.property['inputstream.adaptive.manifest_type'] = 'mpd'
    item.property['inputstream.adaptive.license_type'] = 'com.widevine.alpha'
    item.property['inputstream.adaptive.license_key'] = '%s|%s|%s|JBlicense' % (license_url, LICENSE_HEADERS, payload)
    return item


def get_live_media_url(guid):
    start_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
    end_ms = start_ms + int(timedelta(days=1).total_seconds() * 1000)

    params = {
        "byListingTime": f"{start_ms}~{end_ms}"
    }

    schedules_json = requests.get(URL_ALL_LIVE_SCHEDULES, headers=GENERIC_HEADERS, params=params).json()
    entry = next(
        (r for r in schedules_json.get('entries', []) if r.get('guid') == guid),
        None
    )
    media_pid = entry['plchannelschedule$listings'][0]['rtelisting$mediaPid']
    media_url = 'https://link.eu.theplatform.com/s/1uC-gC/media/' + media_pid
    return media_url


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):
    media_url = get_live_media_url(item_id)

    item = build_rte_list_item(plugin, media_url)
    if item:
        item.label = get_selected_item_label()
        item.art.update(get_selected_item_art())
        item.info.update(get_selected_item_info())
        return item
    return None
