# -*- coding: utf-8 -*-
# Copyright: (c) 2017, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
import json
import re
try:  # Python 3
    from urllib.parse import urlencode
except ImportError:  # Python 2
    from urllib import urlencode

import inputstreamhelper
from codequick import Route, Resolver, Listitem
import htmlement
from kodi_six import xbmcgui
import urlquick

from resources.lib import download, resolver_proxy
from resources.lib.kodi_utils import get_kodi_version, get_selected_item_art, get_selected_item_label, get_selected_item_info, INPUTSTREAM_PROP
from resources.lib.menu_utils import item_post_treatment


# TODO
# Add geoblock (info in JSON)
# Add Quality Mode

URL_EMISSIONS_AUVIO = 'https://www.rtbf.be/auvio/emissions'

URL_JSON_EMISSION_BY_ID2 = 'https://www.rtbf.be/api/media/video?' \
                           'method=getVideoListByEmissionOrdered&args[]=%s'

# I made the choice to select video only because it seems that some audio and video program have the same id but are different
URL_JSON_EMISSION_BY_ID = 'https://www.rtbf.be/api/partner/generic/media/'\
                          'objectlist?v=8&program_id=%s&content_type=complete'\
                          '&type=video&target_site=mediaz&limit=100&partner_key=%s'

# emission_id

URL_CATEGORIES2 = 'https://www.rtbf.be/news/api/menu?site=media'
URL_CATEGORIES = 'https://www.rtbf.be/api/partner/generic/embed/'\
                 'category?method=getTree&v=1&partnerID=%s'

# Doesn't contains all the TV Show
URL_PROGRAMS2 = 'https://www.rtbf.be/api/partner/generic/embed/program?v=1&partnerID=%s'

URL_LIST_TV_CHANNELS = 'https://www.rtbf.be/api/partner/generic/epg/channellist?v=7&type=tv&partner_key=%s'
URL_PROGRAMS = 'https://www.rtbf.be/api/partner/generic/program/getprograms?channel=%s&partner_key=%s'

URL_LIST_SEARCH = 'https://www.rtbf.be/api/partner/generic/search/query?index=media&q=%s&type=media&target_site=mediaz&v=8&partner_key=%s'
URL_LIST_SEARCH_PROG = 'https://www.rtbf.be/api/partner/generic/search/query?index=program&is_paid=0&q=%s&target_site=mediaz&v=8&partner_key=%s'

URL_SUB_CATEGORIES = 'https://www.rtbf.be/news/api/block?data[0][uuid]=%s&data[0][type]=widget&data[0][settings][id]=%s'
# data-uuid and part of data-uuid

URL_VIDEOS_BY_CAT_ID = 'https://www.rtbf.be/api/partner/generic/media/objectlist?'\
                       'v=8&category_id=%s&target_site=mediaz&limit=100&content_type=complete&partner_key=%s'

URL_VIDEO_BY_ID = 'https://www.rtbf.be/auvio/embed/media?id=%s&autoplay=1'
# Video Id

URL_ROOT_IMAGE_RTBF = 'https://ds1.static.rtbf.be'

URL_JSON_LIVE = 'https://www.rtbf.be/api/partner/generic/live/' \
                'planninglist?target_site=media&origin_site=media&category_id=0&' \
                'start_date=&offset=0&limit=15&partner_key=%s&v=8'

URL_JSON_LIVE_CHANNEL = 'http://www.rtbf.be/api/partner/generic/live/' \
                        'planningcurrent?v=8&channel=%s&target_site=mediaz&partner_key=%s'

URL_LICENCE_KEY = 'https://wv-keyos.licensekeyserver.com/|%s|R{SSM}|'

URL_TOKEN = 'https://www.rtbf.be/api/partner/generic/drm/encauthxml?%s=%s&partner_key=%s'


URL_ROOT_LIVE = 'https://www.rtbf.be/auvio/direct#/'


def get_partener_key():
    # Get partener key
    resp = urlquick.get(URL_ROOT_LIVE, max_age=-1)
    list_js_files = re.compile(
        r'<script type="text\/javascript" src="(.*?)">').findall(resp.text)

    # Brute force :)
    partener_key_value = ''
    for js_file in list_js_files:
        resp2 = urlquick.get(js_file)
        partener_key_datas = re.compile('partner_key: \'(.+?)\'').findall(
            resp2.text)
        if len(partener_key_datas) > 0:
            partener_key_value = partener_key_datas[0]
            break
    # print 'partener_key_value : ' + partener_key_value
    return partener_key_value


# partener_key
PARTNER_KEY = get_partener_key()


def format_hours(date, **kwargs):
    """Format hours"""
    date_list = date.split('T')
    date_hour = date_list[1][:5]
    return date_hour


def format_day(date, **kwargs):
    """Format day"""
    date_list = date.split('T')
    date_dmy = date_list[0].replace('-', '/')
    return date_dmy


@Route.register
def list_categories(plugin, item_id, **kwargs):

    item = Listitem.search(list_videos_search, item_id=item_id, page='0')
    item_post_treatment(item)
    yield item

    item = Listitem.search(list_videos_search_prog, item_id=item_id, page='0')
    item.label = plugin.localize(30715)
    item_post_treatment(item)
    yield item

    item = Listitem()
    item.label = plugin.localize(30717)
    item.set_callback(list_programs, item_id=item_id)
    item_post_treatment(item)
    yield item

    resp = urlquick.get(URL_CATEGORIES % PARTNER_KEY)
    json_parser = json.loads(resp.text)

    for category_datas in json_parser["data"]:
        category_title = category_datas["name"]
        category_id = category_datas["id"]
        item = Listitem()
        item.label = category_title
        if "subCategory" in category_datas:
            item.set_callback(list_sub_categories,
                              item_id=item_id,
                              category_datas=category_datas,
                              category_id=category_id)
        else:
            item.set_callback(list_videos_category,
                              item_id=item_id,
                              cat_id=category_id)
        item_post_treatment(item)
        yield item


@Route.register
def list_videos_search(plugin, search_query, item_id, page, **kwargs):
    resp = urlquick.get(URL_LIST_SEARCH % (search_query, PARTNER_KEY))
    json_parser = json.loads(resp.text)
    for results_datas in json_parser["results"]:
        video_datas = results_datas["data"]
        if "subtitle" in video_datas:
            video_title = video_datas["title"] + ' - ' + video_datas["subtitle"]
        else:
            video_title = video_datas["title"]
        video_image = video_datas["images"]["illustration"]["16x9"]["1248x702"]
        video_plot = ''
        if "description" in video_datas:
            video_plot = video_datas["description"]
        video_duration = video_datas["duration"]
        date_value = format_day(video_datas["date_publish_from"])
        video_url = ""
        if "url_streaming" in video_datas:
            is_drm = video_datas["drm"]
            if is_drm:
                if "url_hls" in video_datas["url_streaming"]:
                    video_url = video_datas["url_streaming"]["url_hls"]
                    if "master.m3u8" in video_url:
                        video_url = video_url.replace('/master.m3u8', '-aes/master.m3u8')
                    is_drm = False
                elif "url_dash" in video_datas["url_streaming"]:
                    video_url = video_datas["url_streaming"]["url_dash"]
                    is_drm = video_datas["drm"]
                else:
                    video_url = video_datas["url_streaming"]["url"]
                    is_drm = False
            else:
                if "url_hls" in video_datas["url_streaming"]:
                    video_url = video_datas["url_streaming"]["url_hls"]
                else:
                    video_url = video_datas["url_streaming"]["url"]
        else:
            video_url = video_datas["url_embed"]
            is_drm = False

        video_id = video_datas["id"]
        item = Listitem()
        item.label = video_title
        item.art['thumb'] = item.art['landscape'] = video_image
        item.info['plot'] = video_plot
        item.info['duration'] = video_duration
        item.info.date(date_value, '%Y/%m/%d')
        item.set_callback(get_video_url,
                          item_id=item_id,
                          video_url=video_url,
                          video_id=video_id,
                          is_drm=is_drm)
        item_post_treatment(item, is_playable=True, is_downloadable=True)
        yield item


@Route.register
def list_videos_search_prog(plugin, search_query, item_id, page, **kwargs):
    resp = urlquick.get(URL_LIST_SEARCH_PROG % (search_query, PARTNER_KEY))
    json_parser = json.loads(resp.text)

    for search_datas in json_parser["results"]:
        search_title = search_datas["data"]["label"]
        search_id = search_datas["id"]
        search_image = search_datas["data"]["images"]["illustration"]["16x9"]["1248x702"]
        item = Listitem()
        item.label = search_title
        item.art['thumb'] = item.art['landscape'] = search_image
        item.set_callback(list_videos_program,
                          item_id=item_id,
                          program_id=search_id)
        item_post_treatment(item)
        yield item


# Not used at the moment but could be used if we want to display all the programs per channel via API
# (doesn't work at the moment because display folders that are empties)
@Route.register
def list_channels(plugin, item_id, **kwargs):
    resp = urlquick.get(URL_LIST_TV_CHANNELS % PARTNER_KEY)
    json_parser = json.loads(resp.text)

    for channel_datas in json_parser:
        channel_title = channel_datas["name"]
        channel_image = channel_datas["images"]["illustration"]["16x9"]["1248x702"]
        channel_key = channel_datas["key"]
        item = Listitem()
        item.label = channel_title
        item.art['thumb'] = item.art['landscape'] = channel_image
        item.set_callback(list_programs,
                          item_id=item_id,
                          channel_key=channel_key)
        item_post_treatment(item)
        yield item


@Route.register
def list_programs(plugin, item_id, **kwargs):

    resp = urlquick.get(URL_EMISSIONS_AUVIO)
    root = resp.parse()

    for program_datas in root.iterfind(
            ".//article[@class='rtbf-media-item rtbf-media-item--program-wide col-xxs-12 col-xs-6 col-md-4 col-lg-3 ']"
    ):
        program_title = program_datas.find('.//a').get('title')
        program_image = ''
        list_program_image_datas = program_datas.find('.//img').get(
            'data-srcset').split(' ')
        for program_image_data in list_program_image_datas:
            if 'jpg' in program_image_data:
                if ',' in program_image_data:
                    program_image = program_image_data.split(',')[1]
                else:
                    program_image = program_image_data
        program_id = program_datas.get('data-id')

        item = Listitem()
        item.label = program_title

        item.art['thumb'] = item.art['landscape'] = program_image
        item.set_callback(list_videos_program,
                          item_id=item_id,
                          program_id=program_id)
        item_post_treatment(item)
        yield item


@Route.register
def list_videos_program(plugin, item_id, program_id, **kwargs):

    resp = urlquick.get(URL_JSON_EMISSION_BY_ID % (program_id, PARTNER_KEY))
    json_parser = json.loads(resp.text)

    for video_datas in json_parser:

        if "subtitle" in video_datas:
            video_title = video_datas["title"] + ' - ' + video_datas["subtitle"]
        else:
            video_title = video_datas["title"]
        video_image = video_datas["images"]["illustration"]["16x9"]["1248x702"]
        video_plot = ''
        if "description" in video_datas:
            video_plot = video_datas["description"]
        video_duration = video_datas["duration"]
        date_value = format_day(video_datas["date_publish_from"])
        video_url = ""
        if "url_streaming" in video_datas:
            is_drm = video_datas["drm"]
            if is_drm:
                if "url_hls" in video_datas["url_streaming"]:
                    video_url = video_datas["url_streaming"]["url_hls"]
                    if "master.m3u8" in video_url:
                        video_url = video_url.replace('/master.m3u8', '-aes/master.m3u8')
                    is_drm = False
                elif "url_dash" in video_datas["url_streaming"]:
                    video_url = video_datas["url_streaming"]["url_dash"]
                    is_drm = video_datas["drm"]
                else:
                    video_url = video_datas["url_streaming"]["url"]
                    is_drm = False
            else:
                if "url_hls" in video_datas["url_streaming"]:
                    video_url = video_datas["url_streaming"]["url_hls"]
                else:
                    video_url = video_datas["url_streaming"]["url"]
        else:
            video_url = video_datas["url_embed"]
            is_drm = False

        video_id = video_datas["id"]
        item = Listitem()
        item.label = video_title
        item.art['thumb'] = item.art['landscape'] = video_image
        item.info['plot'] = video_plot
        item.info['duration'] = video_duration
        item.info.date(date_value, '%Y/%m/%d')
        item.set_callback(get_video_url,
                          item_id=item_id,
                          video_url=video_url,
                          video_id=video_id,
                          is_drm=is_drm)
        item_post_treatment(item, is_playable=True, is_downloadable=True)
        yield item


@Route.register
def list_sub_categories(plugin, item_id, category_datas, category_id, **kwargs):
    for sub_category_datas in category_datas["subCategory"]:
        sub_category_title = sub_category_datas["name"]
        sub_category_id = sub_category_datas["id"]

        item = Listitem()
        item.label = sub_category_title
        item.set_callback(list_videos_category,
                          item_id=item_id,
                          cat_id=sub_category_id)
        item_post_treatment(item)
        yield item

    category_url = 'https://www.rtbf.be/auvio/categorie?id=' + str(category_id)
    resp = urlquick.get(category_url)

    list_data_uuid = re.compile(r'data-uuid\=\"(.*?)\"').findall(resp.text)
    for sub_category_data_uuid in list_data_uuid:
        resp2 = urlquick.get(
            URL_SUB_CATEGORIES %
            (sub_category_data_uuid, sub_category_data_uuid.split('-')[1]))
        json_parser = json.loads(resp2.text)
        if sub_category_data_uuid in json_parser["blocks"]:

            parser = htmlement.HTMLement()
            parser.feed(json_parser["blocks"][sub_category_data_uuid])
            root_2 = parser.close()

            for sub_category_dl_data in root_2.iterfind(
                    ".//section[@class='js-item-container']"):

                if sub_category_dl_data.find('.//h2').text is not None:
                    sub_category_dl_title = sub_category_dl_data.find(
                        './/h2').text.strip()
                else:
                    sub_category_dl_title = sub_category_dl_data.find(
                        './/h2/a').text.strip()
                sub_category_dl_id = sub_category_dl_data.get('id')

                item = Listitem()
                item.label = sub_category_dl_title + ' download'
                item.set_callback(
                    list_videos_sub_category_dl,
                    item_id=item_id,
                    sub_category_data_uuid=sub_category_data_uuid,
                    sub_category_id=sub_category_dl_id)
                item_post_treatment(item)
                yield item


@Route.register
def list_videos_category(plugin, item_id, cat_id, **kwargs):

    resp = urlquick.get(URL_VIDEOS_BY_CAT_ID % (cat_id, PARTNER_KEY))
    json_parser = json.loads(resp.text)

    for video_datas in json_parser:
        if "subtitle" in video_datas:
            video_title = video_datas["title"] + ' - ' + video_datas["subtitle"]
        else:
            video_title = video_datas["title"]
        video_image = video_datas["images"]["illustration"]["16x9"]["1248x702"]
        video_plot = ''
        if "description" in video_datas:
            video_plot = video_datas["description"]
        video_duration = video_datas["duration"]
        date_value = format_day(video_datas["date_publish_from"])
        video_url = ""
        if "url_streaming" in video_datas:
            is_drm = video_datas["drm"]
            if is_drm:
                if "url_hls" in video_datas["url_streaming"]:
                    video_url = video_datas["url_streaming"]["url_hls"]
                    if "master.m3u8" in video_url:
                        video_url = video_url.replace('/master.m3u8', '-aes/master.m3u8')
                    is_drm = False
                elif "url_dash" in video_datas["url_streaming"]:
                    video_url = video_datas["url_streaming"]["url_dash"]
                    is_drm = video_datas["drm"]
                else:
                    video_url = video_datas["url_streaming"]["url"]
                    is_drm = False
            else:
                if "url_hls" in video_datas["url_streaming"]:
                    video_url = video_datas["url_streaming"]["url_hls"]
                else:
                    video_url = video_datas["url_streaming"]["url"]
        else:
            video_url = video_datas["url_embed"]
            is_drm = False
        video_id = video_datas["id"]
        # is_downloadable = False
        # if video_datas["url_download"]:
        # is_downloadable = True
        # video_url = video_datas["url_download"]

        item = Listitem()
        item.label = video_title
        item.art['thumb'] = item.art['landscape'] = video_image
        item.info['plot'] = video_plot
        item.info['duration'] = video_duration
        item.info.date(date_value, '%Y/%m/%d')

        item.set_callback(get_video_url,
                          item_id=item_id,
                          video_url=video_url,
                          video_id=video_id,
                          is_drm=is_drm)
        item_post_treatment(item,
                            is_playable=True,
                            is_downloadable=True)
        yield item


@Route.register
def list_videos_sub_category_dl(plugin, item_id, sub_category_data_uuid,
                                sub_category_id, **kwargs):

    resp = urlquick.get(
        URL_SUB_CATEGORIES %
        (sub_category_data_uuid, sub_category_data_uuid.split('-')[1]))
    json_parser = json.loads(resp.text)

    parser = htmlement.HTMLement()
    parser.feed(json_parser["blocks"][sub_category_data_uuid])
    root = parser.close()

    for sub_category_dl_datas in root.iterfind(".//section[@class='js-item-container']"):
        if sub_category_dl_datas.get('id') != sub_category_id:
            continue

        list_videos_datas = sub_category_dl_datas.findall('.//article')

        for video_datas in list_videos_datas:
            if video_datas.get('data-card') is None:
                continue

            data_card = video_datas.get('data-card')
            if not data_card:
                continue

            json_parser = json.loads(data_card)
            if not json_parser["isVideo"]:
                continue

            if "mediaId" not in json_parser:
                continue

            video_title = json_parser["title"] + ' - ' + json_parser["subtitle"]
            video_image = json_parser["illustration"]["format1248"]
            video_id = json_parser["mediaId"]

            item = Listitem()
            item.label = video_title
            item.art['thumb'] = item.art['landscape'] = video_image

            item.set_callback(get_video_url2,
                              item_id=item_id,
                              video_id=video_id)
            item_post_treatment(item, is_playable=True, is_downloadable=True)
            yield item


@Resolver.register
def get_video_url(plugin,
                  item_id,
                  video_url,
                  video_id,
                  is_drm,
                  download_mode=False,
                  **kwargs):
    if 'youtube.com' in video_url:
        video_id = video_url.rsplit('/', 1)[1]
        return resolver_proxy.get_stream_youtube(plugin, video_id,
                                                 download_mode)

    if 'arte.tv' in video_url:
        video_id = re.compile("(?<=fr%2F)(.*)(?=&autostart)").findall(video_url)[0]
        return resolver_proxy.get_arte_video_stream(plugin,
                                                    'fr',
                                                    video_id,
                                                    download_mode)

    if is_drm:
        if get_kodi_version() < 18:
            xbmcgui.Dialog().ok('Info', plugin.localize(30602))
            return False

        is_helper = inputstreamhelper.Helper('mpd', drm='widevine')
        if not is_helper.check_inputstream():
            return False

        token_url = URL_TOKEN % ('media_id', video_id, PARTNER_KEY)
        token_value = urlquick.get(token_url, max_age=-1)
        json_parser_token = json.loads(token_value.text)

        item = Listitem()
        item.path = video_url
        item.property[INPUTSTREAM_PROP] = 'inputstream.adaptive'
        item.property['inputstream.adaptive.manifest_type'] = 'mpd'
        item.property['inputstream.adaptive.license_type'] = 'com.widevine.alpha'
        headers2 = {
            'customdata':
            json_parser_token["auth_encoded_xml"],
        }
        item.property['inputstream.adaptive.license_key'] = URL_LICENCE_KEY % urlencode(headers2)
        item.property['inputstream.adaptive.manifest_update_parameter'] = 'full'
        item.label = get_selected_item_label()
        item.art.update(get_selected_item_art())
        item.info.update(get_selected_item_info())
        return item

    return video_url


@Resolver.register
def get_video_url2(plugin,
                   item_id,
                   video_id,
                   download_mode=False,
                   **kwargs):

    resp = urlquick.get(URL_VIDEO_BY_ID % video_id, max_age=-1)
    json_parser = json.loads(
        re.compile('data-media=\"(.*?)\"').findall(resp.text)[0].replace(
            '&quot;', '"'))

    if json_parser["urlHls"] is None:
        if 'youtube.com' in json_parser["url"]:
            video_id = json_parser["url"].rsplit('/', 1)[1]
            return resolver_proxy.get_stream_youtube(plugin, video_id,
                                                     download_mode)
        return json_parser["url"]

    stream_url = json_parser["urlHls"]
    if 'drm' in stream_url:
        stream_url = json_parser["urlHlsAes128"]

    if download_mode:
        return download.download_video(stream_url)
    return stream_url


@Resolver.register
def set_live_url(plugin, item_id, **kwargs):

    resp = urlquick.get(URL_JSON_LIVE_CHANNEL % (item_id, PARTNER_KEY), max_age=-1)
    json_parser = json.loads(resp.text)

    if "url_streaming" in json_parser:
        is_drm = json_parser["drm"]
        if is_drm:
            if 'url_hls' in json_parser["url_streaming"]:
                live_url = json_parser["url_streaming"]["url_hls"]
                if "_drm.m3u8" in live_url:
                    live_url = live_url.replace('_drm.m3u8', '_aes.m3u8')
                live_id = json_parser["id"]
                is_drm = False
            elif 'url_dash' in json_parser["url_streaming"]:
                live_url = json_parser["url_streaming"]["url_dash"]
                live_id = json_parser["id"]
            else:
                live_url = json_parser["url_streaming"]["url_hls"]
                live_id = json_parser["id"]
                is_drm = False
        else:
            live_url = json_parser["url_streaming"]["url_hls"]
            live_id = json_parser["id"]
    live_channel_title = json_parser["channel"]["label"]
    # start_time_value = format_hours(json_parser["start_date"])
    # end_time_value = format_hours(json_parser["end_date"])
    # date_value = format_day(json_parser["start_date"])
    live_title = live_channel_title + " - " + json_parser["title"]
    if json_parser['subtitle']:
        live_title += " - " + json_parser['subtitle']
    live_plot = json_parser["description"]
    live_image = json_parser["images"]["illustration"]["16x9"]["1248x702"]

    item = Listitem()
    item.label = live_title
    item.art['thumb'] = item.art['landscape'] = live_image
    item.info['plot'] = live_plot
    item.set_callback(get_live_url, item_id=item_id, live_url=live_url, is_drm=is_drm, live_id=live_id)
    item_post_treatment(item, is_playable=True)
    yield item


@Route.register
def list_lives(plugin, item_id, **kwargs):

    resp = urlquick.get(URL_JSON_LIVE % (PARTNER_KEY), max_age=-1)
    json_parser = json.loads(resp.text)

    for live_datas in json_parser:

        if "url_streaming" in live_datas:
            is_drm = live_datas["drm"]
            if is_drm:
                # check if we can add prochainnement if stream is not present
                if 'url_hls' in live_datas["url_streaming"]:
                    live_url = live_datas["url_streaming"]["url_hls"]
                    if "_drm.m3u8" in live_url:
                        live_url = live_url.replace('_drm.m3u8', '_aes.m3u8')
                    live_id = live_datas["id"]
                    is_drm = False
                elif 'url_dash' in live_datas["url_streaming"]:
                    live_url = live_datas["url_streaming"]["url_dash"]
                    live_id = live_datas["id"]
                else:
                    live_url = live_datas["url_streaming"]["url_hls"]
                    live_id = live_datas["id"]
                    is_drm = False
            else:
                live_url = live_datas["url_streaming"]["url_hls"]
                live_id = live_datas["id"]
        if type(live_datas["channel"]) is dict:
            live_channel_title = live_datas["channel"]["label"]
        else:
            live_channel_title = 'Exclu Auvio'
        if live_channel_title in ['La Une', 'Tipik', 'La Trois']:
            continue
        start_time_value = format_hours(live_datas["start_date"])
        end_time_value = format_hours(live_datas["end_date"])
        date_value = format_day(live_datas["start_date"])
        live_title = live_channel_title + " - " + live_datas["title"]
        if live_datas['subtitle']:
            live_title += " - " + live_datas['subtitle']
        live_plot = 'Début le %s à %s (CET)' % (date_value, start_time_value) + \
            '\n\r' + 'Fin le %s à %s (CET)' % (date_value, end_time_value) + '\n\r' + \
            'Accessibilité: ' + live_datas["geolock"]["title"] + '\n\r' + \
            live_datas["description"]
        live_image = live_datas["images"]["illustration"]["16x9"]["1248x702"]

        item = Listitem()
        item.label = live_title
        item.art['thumb'] = item.art['landscape'] = live_image
        item.info['plot'] = live_plot
        # commented this line because othrewie sorting is made by date and then by title
        # and doesn't help to find the direct
        # item.info.date(date_time_value, '%Y/%m/%d')
        item.set_callback(get_live_url, item_id=item_id, live_url=live_url, is_drm=is_drm, live_id=live_id)
        item_post_treatment(item, is_playable=True)
        yield item


@Resolver.register
def get_live_url(plugin, item_id, live_url, is_drm, live_id, **kwargs):

    if is_drm:
        if get_kodi_version() < 18:
            xbmcgui.Dialog().ok('Info', plugin.localize(30602))
            return False

        is_helper = inputstreamhelper.Helper('mpd', drm='widevine')
        if not is_helper.check_inputstream():
            return False

        token_url = URL_TOKEN % ('planning_id', live_id, PARTNER_KEY)
        token_value = urlquick.get(token_url, max_age=-1)
        json_parser_token = json.loads(token_value.text)

        item = Listitem()
        item.path = live_url
        item.property[INPUTSTREAM_PROP] = 'inputstream.adaptive'
        item.property['inputstream.adaptive.manifest_type'] = 'mpd'
        item.property['inputstream.adaptive.license_type'] = 'com.widevine.alpha'
        headers2 = {
            'customdata':
            json_parser_token["auth_encoded_xml"],
        }
        item.property['inputstream.adaptive.license_key'] = URL_LICENCE_KEY % urlencode(headers2)
        item.property['inputstream.adaptive.manifest_update_parameter'] = 'full'
        item.label = get_selected_item_label()
        item.art.update(get_selected_item_art())
        item.info.update(get_selected_item_info())
        return item

    return live_url
