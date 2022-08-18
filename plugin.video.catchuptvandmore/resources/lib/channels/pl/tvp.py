# -*- coding: utf-8 -*-
# Copyright: (c) 2018, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
import re

from codequick import Resolver, Script, utils
import urlquick

from resources.lib import web_utils


# TO DO
# Add Replay

# Live
URL_LIVE = 'http://tvpstream.vod.tvp.pl/'

URL_STREAM = 'http://www.tvp.pl/sess/tvplayer.php?object_id=%s'
# videoId

LIVE_TVP3_REGIONS = {
    "Białystok": "tvp3-bialystok",
    "Bydgoszcz": "tvp3-bydgoszcz",
    "Gdańsk": "tvp3-gdansk",
    "Gorzów Wielkopolski": "tvp3-gorzow-wielkopolski",
    "Katowice": "tvp3-katowice",
    "Kielce": "tvp3-kielce",
    "Kraków": "tvp3-krakow",
    "Lublin": "tvp3-lublin",
    "Łódź": "tvp3-lodz",
    "Olsztyn": "tvp3-olsztyn",
    "Opole": "tvp3-opole",
    "Poznań": "tvp3-poznan",
    "Rzeszów": "tvp3-rzeszow",
    "Szczecin": "tvp3-szczecin",
    "Warszawa": "tvp3-warszawa",
    "Wrocław": "tvp3-wroclaw"
}


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):
    final_language = kwargs.get('language', Script.setting['tvp3.language'])

    resp = urlquick.get(URL_LIVE,
                        headers={'User-Agent': web_utils.get_random_ua()},
                        max_age=-1)
    root = resp.parse()

    live_id = None
    for live_datas in root.findall(".//div"):
        if live_datas.get('data-stationname') is not None:
            if item_id == 'tvpinfo':
                if 'info' in live_datas.find('.//img').get('alt'):
                    live_id = live_datas.get('data-video-id')
                    break
            elif item_id == 'tvppolonia':
                if (
                    'Polonia' in live_datas.get('data-title')
                    or '1773' in live_datas.get('data-channel-id')
                ):
                    live_id = live_datas.get('data-video-id')
                    break
            elif item_id == 'tvpworld':
                if 'News and entertainment' in live_datas.get('data-title'):
                    live_id = live_datas.get('data-video-id')
                    break
            elif item_id == 'tvp3':
                if LIVE_TVP3_REGIONS[utils.ensure_unicode(
                        final_language)] in live_datas.find('.//img').get(
                            'alt'):
                    live_id = live_datas.get('data-video-id')
                    break
            elif item_id == 'tvpwilno':
                if 'wilno' in live_datas.find('.//img').get('alt'):
                    live_id = live_datas.get('data-video-id')
                    break

    if live_id is None:
        # Stream is not available - channel not found on scrapped page
        plugin.notify('INFO', plugin.localize(30716))
        return False

    lives_html = urlquick.get(URL_STREAM % live_id,
                              headers={'User-Agent': web_utils.get_random_ua()},
                              max_age=-1)

    final_video_url = re.compile(r'src:\'(.+\.m3u8)\'').search(lives_html.text)
    if final_video_url is not None:
        return final_video_url.group(1)

    # Stream is not available - M3U8 playlist not found on scrapped page
    plugin.notify('INFO', plugin.localize(30716))
    return False
