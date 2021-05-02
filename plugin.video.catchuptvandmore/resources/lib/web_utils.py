# -*- coding: utf-8 -*-
"""
    Catch-up TV & More
    Original work (C) JUL1EN094, SPM, SylvainCecchetto
    Copyright (C) 2016  SylvainCecchetto

    This file is part of Catch-up TV & More.

    Catch-up TV & More is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

    Catch-up TV & More is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License along
    with Catch-up TV & More; if not, write to the Free Software Foundation,
    Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
"""
from codequick import Script
from random import randint

import json
import urlquick

user_agents = [
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
    '(KHTML, like Gecko) Chrome/69.0.3497.100 Safari/537.36',
    'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.1',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.75.14'
    ' (KHTML, like Gecko) Version/7.0.3 Safari/7046A194A',
    'Opera/9.80 (X11; Linux i686; Ubuntu/14.10) Presto/2.12.388 Version/12.16',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_1) AppleWebKit/602.2.14'
    ' (KHTML, like Gecko) Version/10.0.1 Safari/602.2.14',
    'Mozilla/5.0 (Windows NT 6.1; WOW64) '
    'AppleWebKit/537.36 (KHTML, like Gecko) '
    'Chrome/55.0.2883.87 Safari/537.36'
]


def get_ua():
    """Get first user agent in the 'user_agents' list

    Returns:
        str: User agent
    """
    return user_agents[0]


def get_random_ua():
    """Get a random user agent in the 'user_agents' list

    Returns:
        str: Random user agent
    """
    return user_agents[randint(0, len(user_agents) - 1)]


# code adapted from weather.weatherbit.io - Thanks Ronie
def geoip():
    """Get country code based on IP address

    Returns:
        str: Country code (e.g. FR)
    """
    # better service - https://geoftv-a.akamaihd.net/ws/edgescape.json
    try:
        resp = urlquick.get('https://geoftv-a.akamaihd.net/ws/edgescape.json', max_age=-1)
        data = json.loads(resp.text)
        if 'reponse' in data:
            return data['reponse']['geo_info']['country_code']
    except Exception:
        pass
    Script.notify(Script.get_info('name'), Script.localize(30724), icon=Script.NOTIFY_WARNING)
    Script.log('Failed to get country code based on IP address', lvl=Script.WARNING)
    return None
