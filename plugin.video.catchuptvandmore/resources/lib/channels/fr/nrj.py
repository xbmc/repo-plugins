# -*- coding: utf-8 -*-
# Copyright: (c) 2017, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
import json
import requests

from codequick import Listitem, Resolver, Route
import htmlement
import urlquick

from resources.lib import resolver_proxy, download
from resources.lib.addon_utils import get_item_media_path
from resources.lib.menu_utils import item_post_treatment


# TO DO
# Fix Live TV

URL_ROOT = 'https://www.nrj-play.fr'

URL_REPLAY = URL_ROOT + '/%s/replay'
# channel_name (nrj12, ...)

URL_COMPTE_LOGIN = 'https://user-api2.nrj.fr/api/5/login'
# TO DO add account for using Live Direct

URL_LIVE_WITH_TOKEN = URL_ROOT + '/compte/live?channel=%s'
# channel (nrj12, ...) -
# call this url after get session (url live with token inside this page)


@Route.register
def nrjplay_root(plugin, **kwargs):

    # (item_id, label, thumb, fanart)
    channels = [
        ('nrj12', 'NRJ 12', 'nrj12.png', 'nrj12_fanart.jpg'),
        ('cherie25', 'Chérie 25', 'cherie25.png', 'cherie25_fanart.jpg')
    ]

    for channel_infos in channels:
        item = Listitem()
        item.label = channel_infos[1]
        item.art["thumb"] = get_item_media_path('channels/fr/' + channel_infos[2])
        item.art["fanart"] = get_item_media_path('channels/fr/' + channel_infos[3])
        item.set_callback(list_categories, channel_infos[0])
        item_post_treatment(item)
        yield item


@Route.register
def list_categories(plugin, item_id, **kwargs):
    """
    Build categories listing
    - Tous les programmes
    - Séries
    - Informations
    - ...
    """
    resp = urlquick.get(URL_REPLAY % item_id)
    root = resp.parse("ul", attrs={"class": "subNav-menu hidden-xs"})

    for category_datas in root.iterfind(".//a"):
        category_title = category_datas.text.strip()
        category_url = URL_ROOT + category_datas.get('href')

        item = Listitem()
        item.label = category_title
        item.set_callback(list_programs,
                          item_id=item_id,
                          category_url=category_url)
        item_post_treatment(item)
        yield item


@Route.register
def list_programs(plugin, item_id, category_url, **kwargs):
    """
    Build programs listing
    - Les feux de l'amour
    - ...
    """
    resp = urlquick.get(category_url)
    root = resp.parse()

    for program_datas in root.iterfind(".//div[@class='linkProgram-visual']"):

        program_title = program_datas.find('.//img').get('alt')
        program_url = URL_ROOT + program_datas.find('.//a').get('href')
        program_image = ''
        if program_datas.find('.//source').get('data-srcset') is not None:
            program_image = program_datas.find('.//source').get('data-srcset')
        else:
            program_image = program_datas.find('.//source').get('srcset')

        item = Listitem()
        item.label = program_title
        item.art['thumb'] = item.art['landscape'] = program_image
        item.set_callback(list_videos,
                          item_id=item_id,
                          program_title=program_title,
                          program_url=program_url)
        item_post_treatment(item)
        yield item


@Route.register
def list_videos(plugin, item_id, program_title, program_url, **kwargs):

    resp = urlquick.get(program_url)
    root = resp.parse()

    if len(root.findall(".//figure[@class='thumbnailReplay-visual']")) > 0:
        for video_datas in root.findall(
                ".//figure[@class='thumbnailReplay-visual']"):
            video_title = program_title + ' - ' + video_datas.find(
                './/img').get('alt')
            video_url = URL_ROOT + video_datas.find('.//a').get('href')
            video_image = ''
            if video_datas.find('.//source').get('data-srcset') is not None:
                video_image = video_datas.find('.//source').get('data-srcset')
            else:
                video_image = video_datas.find('.//source').get('srcset')

            item = Listitem()
            item.label = video_title
            item.art['thumb'] = item.art['landscape'] = video_image

            item.set_callback(get_video_url,
                              item_id=item_id,
                              video_url=video_url)
            item_post_treatment(item, is_playable=True, is_downloadable=True)
            yield item
    else:
        video_title = root.find(".//div[@class='nrjVideo-player']").find(
            './/meta').get('alt')
        video_url = program_url
        video_image = root.find(".//div[@class='nrjVideo-player']").find(
            './/meta').get('content')

        item = Listitem()
        item.label = video_title
        item.art['thumb'] = item.art['landscape'] = video_image

        item.set_callback(get_video_url,
                          item_id=item_id,
                          video_url=video_url)
        item_post_treatment(item, is_playable=True, is_downloadable=True)
        yield item


@Resolver.register
def get_video_url(plugin,
                  item_id,
                  video_url,
                  download_mode=False,
                  **kwargs):
    # Just One format of each video (no need of QUALITY)
    resp = urlquick.get(video_url)
    root = resp.parse("div", attrs={"class": "nrjVideo-player"})

    stream_url = ''
    for stream in root.iterfind(".//meta"):
        if 'mp4' in stream.get('content'):
            stream_url = stream.get('content')

    if download_mode:
        return download.download_video(stream_url)
    return stream_url


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):

    # Live TV Not working / find a way to dump html received

    # Create session
    # KO - session_urlquick = urlquick.Session()
    session_requests = requests.session()

    # Build PAYLOAD
    payload = {
        "email": plugin.setting.get_string('nrj.login'),
        "password": plugin.setting.get_string('nrj.password')
    }
    headers = {
        'accept': 'application/json, text/javascript, */*; q=0.01',
        'origin': 'https://www.nrj-play.fr',
        'referer': 'https://www.nrj-play.fr/'
    }

    # LOGIN
    # KO - resp2 = session_urlquick.post(
    #     URL_COMPTE_LOGIN, data=payload,
    #     headers={'User-Agent': web_utils.get_ua, 'referer': URL_COMPTE_LOGIN})
    resp2 = session_requests.post(URL_COMPTE_LOGIN,
                                  data=payload,
                                  headers=headers)
    if 'error alert alert-danger' in repr(resp2.text):
        plugin.notify('ERROR', 'NRJ : ' + plugin.localize(30711))
        return False

    # GET page with url_live with the session logged
    # KO - resp3 = session_urlquick.get(
    #     URL_LIVE_WITH_TOKEN % item_id,
    #     headers={'User-Agent': web_utils.get_ua, 'referer': URL_LIVE_WITH_TOKEN % item_id})
    resp3 = session_requests.get(URL_LIVE_WITH_TOKEN % (item_id),
                                 headers=dict(referer=URL_LIVE_WITH_TOKEN %
                                              (item_id)))

    parser = htmlement.HTMLement()
    parser.feed(resp3.text)
    root = parser.close()
    live_data = root.find(".//div[@class='player']")

    url_live_json = live_data.get('data-options')
    url_live_json_jsonparser = json.loads(url_live_json)
    return resolver_proxy.get_stream_with_quality(plugin, url_live_json_jsonparser["file"], manifest_type="hls")
