# -*- coding: utf-8 -*-
# Copyright: (c) 2018, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
import json
import re

from codequick import Listitem, Resolver, Route, Script, utils
import urlquick

from resources.lib import download, web_utils
from resources.lib.menu_utils import item_post_treatment

# TO DO
# Add Region
# Check different cases of getting videos
# Passer sur l'API V2 ?

URL_API = 'https://api.radio-canada.ca/validationMedia/v1/Validation.html'

URL_API_2 = 'https://services.radio-canada.ca/media'

URL_CLIENT_VALUE = URL_API_2 + '/player/client/radiocanadaca_unit'

URL_LIVE = URL_API_2 + '/validation/v2/?connectionType=hd&output=json&multibitrate=true&deviceType=ipad&appCode=medianetlive&idMedia=%s'

URL_ROOT = 'https://ici.radio-canada.ca'

URL_EMISSION = URL_ROOT + '/tele/emissions'

URL_EMISSION_VIDEOS = URL_ROOT + '/v35/Component/EpisodeSummaries/Content?seasonId=%s&pageIndex=%s'
# ProgramId, Page

URL_STREAM_REPLAY = URL_API + '?connectionType=broadband&output=json&multibitrate=true&deviceType=ipad&appCode=medianet&idMedia=%s'
# VideoId

LIVE_ICI_TELE_REGIONS = {
    "Vancouver": "cbuft",
    "Regina": "cbkft",
    "Toronto": "cblft",
    "Edmonton": "cbxft",
    "Rimouski": "cjbr",
    "Québec": "cbvt",
    "Winnipeg": "cbwft",
    "Moncton": "cbaft",
    "Ottawa": "cboft",
    "Sherbrooke": "cksh",
    "Trois-Rivières": "cktm",
    "Montréal": "cbft"
}


@Route.register
def list_programs(plugin, item_id, **kwargs):

    resp = urlquick.get(URL_EMISSION)
    json_value = re.compile(r'/\*bns\*/ (.*?) /\*bne\*/').findall(resp.text)[0]
    json_parser = json.loads(json_value)

    # Regional programms
    for programs_datas in json_parser["pagesV2"]["pages"]["/tele/emissions"][
            "data"]["programmesForRegion"]:

        if '/tele/' in programs_datas["url"]:
            program_title = programs_datas["title"]
            program_image = programs_datas["picture"]["url"]
            program_url = programs_datas["url"] + '/site/episodes'

            item = Listitem()
            item.label = program_title
            item.art['thumb'] = item.art['landscape'] = program_image
            item.set_callback(list_videos,
                              item_id=item_id,
                              program_url=program_url,
                              page='1')
            item_post_treatment(item)
            yield item
    # All programs
    for programs_datas in json_parser["pagesV2"]["pages"]["/tele/emissions"][
            "data"]["programmes"]:

        if '/tele/' in programs_datas["url"]:
            program_title = programs_datas["title"]
            program_image = programs_datas["picture"]["url"]
            program_url = URL_ROOT + programs_datas["url"] + '/site/episodes'

            item = Listitem()
            item.label = program_title
            item.art['thumb'] = item.art['landscape'] = program_image
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
        item.art['thumb'] = item.art['landscape'] = video_image

        item.set_callback(get_video_url,
                          item_id=item_id,
                          video_url=video_url)
        item_post_treatment(item, is_playable=True, is_downloadable=True)
        yield item

    yield Listitem.next_page(item_id=item_id, program_url=program_url, page=str(int(page) + 1))


@Resolver.register
def get_video_url(plugin,
                  item_id,
                  video_url,
                  download_mode=False,
                  **kwargs):

    resp = urlquick.get(video_url)
    video_id = re.compile(r'idMedia\"\:\"(.*?)\"').findall(
        resp.text)[0]
    resp2 = urlquick.get(URL_STREAM_REPLAY % video_id)
    json_parser = json.loads(resp2.text)
    final_video_url = json_parser["url"]

    if download_mode:
        return download.download_video(final_video_url)
    return final_video_url


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):

    resp2 = urlquick.get(
        URL_CLIENT_VALUE,
        headers={
            'User-Agent': web_utils.get_random_ua()
        })
    client_id_value = re.compile(
        r'clientKey\:\"(.*?)\"').findall(resp2.text)[0]

    final_region = kwargs.get('language', Script.setting['icitele.language'])
    region = utils.ensure_unicode(final_region)

    resp = urlquick.get(
        URL_LIVE % LIVE_ICI_TELE_REGIONS[region],
        headers={
            'User-Agent': web_utils.get_random_ua(),
            'Authorization': 'Client-Key %s' % client_id_value
        })
    json_parser = json.loads(resp.text)
    return json_parser["url"]
