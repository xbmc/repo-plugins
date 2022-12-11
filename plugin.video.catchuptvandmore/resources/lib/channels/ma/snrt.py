# -*- coding: utf-8 -*-
# Copyright: (c) 2017, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
import re
import urlquick

# noinspection PyUnresolvedReferences
from codequick import Resolver

from resources.lib import resolver_proxy, web_utils

URL_LIVES = 'https://cdnamd-hls-globecast.akamaized.net/live/ramdisk/%s/hls_snrt/%s.m3u8'


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):

    if item_id == "alAoula":
        id = "al_aoula_inter"
    if item_id == "alMaghribia":
        id = "al_maghribia_snrt"
    if item_id == "laayoune":
        id = "al_aoula_laayoune"
    if item_id == "tamazight":
        id = "tamazight_tv8_snrt"
    if item_id == "assadissa":
        id = "assadissa"
    if item_id == "athaqafia":
        id = "arrabiaa"
    if item_id == "arryadia":
        id = "arriadia"
    video_url = URL_LIVES % (id, id)

    return resolver_proxy.get_stream_with_quality(plugin, video_url, manifest_type="hls")
