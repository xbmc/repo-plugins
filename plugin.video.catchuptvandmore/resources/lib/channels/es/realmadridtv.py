# -*- coding: utf-8 -*-
# Copyright: (c) 2018, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
import re

from codequick import Resolver, Script
import urlquick

from resources.lib import web_utils


# TODO
# Replay add emissions

URL_ROOT = 'https://www.realmadrid.com'

URL_LIVE = URL_ROOT + '/real-madrid-tv'


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):

    url_live = ''
    final_language = kwargs.get('language', Script.setting['realmadridtv.language'])

    resp = urlquick.get(URL_LIVE,
                        headers={'User-Agent': web_utils.get_random_ua()},
                        max_age=-1)
    url_lives = re.compile(r'data-stream-hsl-url=\'(.*?)\'').findall(resp.text)

    for urls in url_lives:
        if final_language.lower() in urls:
            url_live = urls
    return url_live
