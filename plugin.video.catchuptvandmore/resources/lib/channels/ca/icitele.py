# -*- coding: utf-8 -*-
"""
    Catch-up TV & More
    Copyright (C) 2018  SylvainCecchetto

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

# The unicode_literals import only has
# an effect on Python 2.
# It makes string literals as unicode like in Python 3
from __future__ import unicode_literals

from codequick import Route, Resolver, Listitem, utils, Script

from resources.lib.labels import LABELS
from resources.lib import web_utils
from resources.lib import download
from resources.lib.listitem_utils import item_post_treatment, item2dict

import json
import re
import urlquick

# TO DO
# Add Region
# Check different cases of getting videos
# Passer sur l'API V2 ?

URL_API = 'https://api.radio-canada.ca/validationMedia/v1/Validation.html'

URL_LIVE = URL_API + '?connectionType=broadband&output=json&multibitrate=true&deviceType=ipad&appCode=medianetlive&idMedia=cbuft'

URL_ROOT = 'https://ici.radio-canada.ca'

URL_EMISSION = URL_ROOT + '/tele/emissions'

URL_EMISSION_VIDEOS = URL_ROOT + '/v35/Component/EpisodeSummaries/Content?seasonId=%s&pageIndex=%s'
# ProgramId, Page

URL_STREAM_REPLAY = URL_API + '?connectionType=broadband&output=json&multibitrate=true&deviceType=ipad&appCode=medianet&idMedia=%s'
# VideoId


def replay_entry(plugin, item_id, **kwargs):
    """
    First executed function after replay_bridge
    """
    return list_programs(plugin, item_id)


@Route.register
def list_programs(plugin, item_id, **kwargs):

    resp = urlquick.get(URL_EMISSION)
    json_value = re.compile(r'/\*bns\*/ (.*?) /\*bne\*/').findall(resp.text)[0]
    json_parser = json.loads(json_value)

    # All programs
    for programs_datas in json_parser["pages"]["teleShowsList"]["pageModel"][
            "data"]["programmes"]:

        if '/tele/' in programs_datas["url"]:
            program_title = programs_datas["title"]
            program_url = ''
            if 'telejournal-22h' in programs_datas["url"] or \
                    'telejournal-18h' in programs_datas["url"]:
                program_url = URL_ROOT + programs_datas[
                    "url"] + '/2016-2017/episodes'
            else:
                program_url = URL_ROOT + programs_datas[
                    "url"] + '/site/episodes'

            item = Listitem()
            item.label = program_title
            item.set_callback(list_videos,
                              item_id=item_id,
                              program_url=program_url,
                              page='1')
            item_post_treatment(item)
            yield item


@Route.register
def list_videos(plugin, item_id, program_url, page, **kwargs):

    resp = urlquick.get(program_url)
    program_id = re.compile(r'data-seasonid\=\"(.*?)\"').findall(
        resp.text)[0]
    resp2 = urlquick.get(URL_EMISSION_VIDEOS % (program_id, page))
    root = resp2.parse()

    for video_datas in root.iterfind(".//a[@class='medianet-content']"):

        video_title = video_datas.get('title')
        video_image = URL_ROOT + video_datas.find(".//img").get('src')
        video_url = URL_ROOT + video_datas.get('href')

        item = Listitem()
        item.label = video_title
        item.art['thumb'] = video_image

        item.set_callback(get_video_url,
                          item_id=item_id,
                          video_label=LABELS[item_id] + ' - ' + item.label,
                          video_url=video_url)
        item_post_treatment(item, is_playable=True, is_downloadable=True)
        yield item

    yield Listitem.next_page(item_id=item_id, program_url=program_url, page=str(int(page) + 1))


@Resolver.register
def get_video_url(plugin,
                  item_id,
                  video_url,
                  download_mode=False,
                  video_label=None,
                  **kwargs):

    resp = urlquick.get(video_url)
    video_id = re.compile(r'idMedia\"\:\"(.*?)\"').findall(
        resp.text)[0]
    resp2 = urlquick.get(URL_STREAM_REPLAY % video_id)
    json_parser = json.loads(resp2.text)
    final_video_url = json_parser["url"]

    if download_mode:
        return download.download_video(final_video_url, video_label)
    return final_video_url


def live_entry(plugin, item_id, item_dict, **kwargs):
    return get_live_url(plugin, item_id, item_id.upper(), item_dict)


@Resolver.register
def get_live_url(plugin, item_id, video_id, item_dict, **kwargs):

    resp = urlquick.get(URL_LIVE)
    json_parser = json.loads(resp.text)
    return json_parser["url"]
