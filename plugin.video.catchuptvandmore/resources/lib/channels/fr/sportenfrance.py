# -*- coding: utf-8 -*-
# Copyright: (c) 2019, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
import re

from codequick import Resolver
import urlquick

from resources.lib import web_utils


# TODO
# Add Replay

URL_ROOT = "https://www.sportenfrance.com"


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):

    resp = urlquick.get(
        URL_ROOT, headers={"User-Agent": web_utils.get_random_ua()}, max_age=-1)
    root = resp.parse()
    live_datas = root.find('.//iframe')
    resp2 = urlquick.get(
        live_datas.get('src'), headers={"User-Agent": web_utils.get_random_ua()}, max_age=-1)
    stream_url = ''
    for url in re.compile(r'videoxurl \= \'(.*?)\'').findall(resp2.text):
        stream_url = url
    return stream_url
