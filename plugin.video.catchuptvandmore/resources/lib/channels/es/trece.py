# -*- coding: utf-8 -*-
"""
    Copyright (C) 2016-2020 Team Catch-up TV & More
    This file is part of Catch-up TV & More.
    SPDX-License-Identifier: GPL-2.0-or-later
"""

# The unicode_literals import only has
# an effect on Python 2.
# It makes string literals as unicode like in Python 3
from __future__ import unicode_literals

from builtins import range
from codequick import Route, Resolver, Listitem, utils, Script

from resources.lib import web_utils
from resources.lib.menu_utils import item_post_treatment

import json
import urlquick

# TO DO

URL_ROOT = 'https://www.cope.es'

URL_LIVE_JSON = URL_ROOT + '/api/es/appbeta/streaming/trece'
# Live Id


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):

    resp = urlquick.get(URL_LIVE_JSON)
    json_parser = json.loads(resp.text)

    return json_parser["medias"][0]["url"]
