# -*- coding: utf-8 -*-
# Copyright: (c) 2019, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
import re

from codequick import Resolver
import urlquick


# TO DO
# Add Replay

URL_ROOT = 'https://www.ln24.be'

URL_LIVE = URL_ROOT + '/direct'


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):

    resp = urlquick.get(URL_LIVE, max_age=-1)
    return re.compile(r'source src\=\"(.*?)\"').findall(resp.text)[0]
