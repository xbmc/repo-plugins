# -*- coding: utf-8 -*-
# Copyright: (c) 2018, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
import re
import json

from codequick import Listitem, Resolver, Route
import urlquick

from resources.lib import download
from resources.lib.menu_utils import item_post_treatment
from resources.lib import resolver_proxy, web_utils


# TODO Add replays

URL_ROOT = 'https://viaoccitanie.tv'

URL_LIVE = URL_ROOT + '/direct-tv/'

ULTRAMEDIA_API = 'https://www.ultimedia.com/api/widget/smart?'

GENERIC_HEADERS = {'User-Agent': web_utils.get_random_ua()}


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):

    resp = urlquick.get(URL_LIVE, headers=GENERIC_HEADERS, max_age=-1)
    root = resp.text
    mdtk = re.compile(r'mdtk\/(.*?)\/').findall(root)[0]
    zone = re.compile(r'zone\/(.*?)\/').findall(root)[0]

    params = {
        'mdtk': mdtk,
        'zone': zone
    }
    url_frame = urlquick.get(ULTRAMEDIA_API, headers=GENERIC_HEADERS, params=params, max_age=-1)
    url_player = re.compile(r'iframe src\=\\\"(.*?)\&width').findall(url_frame.text)[0]

    player = urlquick.get(url_player, headers=GENERIC_HEADERS, max_age=-1)
    data_json = json.loads(re.compile(r'DtkPlayer.init\((.*?)\, \{\"topic').findall(player.text)[0])

    video_url = data_json['video']['media_sources']['hls']['hls_auto']

    return resolver_proxy.get_stream_with_quality(plugin, video_url)
