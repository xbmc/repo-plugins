# -*- coding: utf-8 -*-
# Copyright: (c) 2017, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
import re
import urlquick

from codequick import Resolver

URL_LIVES = 'http://libs.easybroadcast.io/snrt/%s/EB%s_ads.js'


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):

    if item_id == "alAoula":
        first_id = "aoula"
    elif item_id == "alMaghribia":
        first_id = "maghribia"
    else:
        first_id = item_id

    resp = urlquick.get(URL_LIVES % (first_id, item_id))
    return re.compile(r'autolaunch\:\!0\,autoplay\:\!0\,src\:\"(.*)\"\,playerID').findall(resp.text)[0]
