# -*- coding: utf-8 -*-
# Copyright: (c) 2020, Dag Wieers (@dagwieers) <dag@wieers.com>
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""Implements VRT Radio schedules"""

from __future__ import absolute_import, division, unicode_literals

try:  # Python 3
    from urllib.request import build_opener, install_opener, ProxyHandler
except ImportError:  # Python 2
    from urllib2 import build_opener, install_opener, ProxyHandler

from data import CHANNELS
from kodiutils import get_proxies, get_url_json, log
from utils import find_entry, html_to_kodi


class Schedule:
    """This implements VRT Radio schedules"""

    WEEK_SCHEDULE = 'http://services.vrt.be/epg/schedules/thisweek?channel_type=radio&type=week'

    def __init__(self):
        """Initializes TV-guide object"""
        install_opener(build_opener(ProxyHandler(get_proxies())))

    def get_epg_data(self):
        """Return EPG data"""
        epg_data = dict()
        epg_url = self.WEEK_SCHEDULE
        schedule = get_url_json(url=epg_url, headers=dict(accept='application/vnd.epg.vrt.be.schedule_3.1+json'), fail={})
        for event in schedule.get('events', []):
            channel_id = event.get('channel', dict(code=None)).get('code')
            if channel_id is None:
                log(2, 'No channel code found in EPG event: {event}', event=event)
                continue
            channel = find_entry(CHANNELS, 'id', channel_id)
            if channel is None:
                log(2, 'No channel found using code: {code}', code=channel_id)
                continue
            epg_id = channel.get('epg_id')
            if epg_id not in epg_data:
                epg_data[epg_id] = []
            if event.get('images'):
                image = event.get('images')[0].get('url')
            else:
                image = None
            epg_data[epg_id].append(dict(
                start=event.get('startTime'),
                stop=event.get('endTime'),
                image=image,
                title=event.get('title'),
                description=html_to_kodi(event.get('description', '')),
            ))
        return epg_data
