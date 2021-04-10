# -*- coding: utf-8 -*-
# Copyright: (c) 2017, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
import re
import urlquick

from codequick import Resolver

URL_LIVES = 'http://www.medi1tv.com/ar/live.aspx'


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):

    resp = urlquick.get(URL_LIVES)
    pattern = r"Medi1TV\ %s[\S\s]*file\:\ \'(.*\.m3u8.*)\'[\S\s]*Medi1V_%s.jpg" % (item_id, item_id.lower())
    manifesturl = re.compile(pattern).findall(resp.text)[0]
    finalurl = ''
    if manifesturl.startswith('https'):
        finalurl = manifesturl
    else:
        finalurl = 'https:' + manifesturl
    return finalurl
