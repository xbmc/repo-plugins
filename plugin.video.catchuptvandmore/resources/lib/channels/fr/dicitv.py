# -*- coding: utf-8 -*-
# Copyright: (c) 2019, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
import re
import urlquick

from codequick import Listitem, Resolver, Route
from resources.lib import resolver_proxy, web_utils
from resources.lib.menu_utils import item_post_treatment

URL_ROOT = "https://www.dici.fr"

URL_LIVE = URL_ROOT + "/player?tab=tv"
URL_CATCHUP = URL_ROOT + "/replays/all"

URL_STREAM = 'https://player.infomaniak.com/playerConfig.php?channel=%s'
# channel


@Route.register
def list_videos(plugin, page=0, **kwargs):
    if page == 0:
        url = URL_CATCHUP
    else:
        url = URL_ROOT + page

    resp = urlquick.get(url, headers={"User-Agent": web_utils.get_random_ua()}).text
    dataList = re.compile(r'thumbnail.+?src="([^"]+).+?field-content">([^<]+).+?<a href="([^"]+)', re.DOTALL).findall(resp)

    for program_datas in dataList:
        program_image = program_datas[0]
        program_title = program_datas[1].replace('&#039;', "'")
        program_url = URL_ROOT + program_datas[2]

        item = Listitem()
        item.label = program_title
        item.art['thumb'] = item.art['landscape'] = program_image
        item.set_callback(get_video_url, program_url=program_url)
        item_post_treatment(item)
        yield item

    next_ = re.search(r'<li class="next"><a href="([^"]+)">', resp).group(1)
    yield Listitem.next_page(page=next_)


@Resolver.register
def get_video_url(plugin, program_url, **kwargs):
    resp = urlquick.get(program_url,
                        headers={'User-Agent': web_utils.get_random_ua()},
                        max_age=-1)
    root = resp.parse()
    live_id = root.find(".//iframe").get('src').split('/')[4]
    return resolver_proxy.get_stream_vimeo(plugin, live_id)


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):
    resp = urlquick.get(URL_LIVE,
                        headers={'User-Agent': web_utils.get_random_ua()},
                        max_age=-1)
    stream_url = re.compile(r'mp3: "(.+?)"').findall(resp.text)[0]
    return stream_url
