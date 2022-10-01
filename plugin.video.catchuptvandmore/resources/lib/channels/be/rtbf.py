# -*- coding: utf-8 -*-
# Copyright: (c) 2017, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals

import base64
import json
import re

import inputstreamhelper
# noinspection PyUnresolvedReferences
from codequick import Route, Resolver, Listitem
import htmlement
# noinspection PyUnresolvedReferences
from kodi_six import xbmcgui
import urlquick

from resources.lib import download, resolver_proxy
from resources.lib.kodi_utils import (get_kodi_version, get_selected_item_art, get_selected_item_label,
                                      get_selected_item_info, INPUTSTREAM_PROP)
from resources.lib.menu_utils import item_post_treatment
from resources.lib.web_utils import urlencode

# TODO
# Add geoblock (info in JSON)
# Add Quality Mode

URL_EMISSIONS_AUVIO = 'https://www.rtbf.be/auvio/emissions'

URL_JSON_EMISSION_BY_ID2 = 'https://www.rtbf.be/api/media/video?' \
                           'method=getVideoListByEmissionOrdered&args[]=%s'

# I made the choice to select video only because it seems that some audio and video program have the same id but are
# different
URL_JSON_EMISSION_BY_ID = 'https://www.rtbf.be/api/partner/generic/media/' \
                          'objectlist?v=8&program_id=%s&content_type=complete' \
                          '&type=video&target_site=mediaz&limit=100&partner_key=%s'

# emission_id

URL_CATEGORIES2 = 'https://www.rtbf.be/news/api/menu?site=media'
URL_CATEGORIES = 'https://www.rtbf.be/api/partner/generic/embed/' \
                 'category?method=getTree&v=1&partnerID=%s'

# Doesn't contain all the TV Show
URL_PROGRAMS2 = 'https://www.rtbf.be/api/partner/generic/embed/program?v=1&partnerID=%s'

URL_LIST_TV_CHANNELS = 'https://www.rtbf.be/api/partner/generic/epg/channellist?v=7&type=tv&partner_key=%s'
URL_PROGRAMS = 'https://www.rtbf.be/api/partner/generic/program/getprograms?channel=%s&partner_key=%s'

URL_LIST_SEARCH = 'https://www.rtbf.be/api/partner/generic/search/query?index=media&q=%s&type=media&target_site' \
                  '=mediaz&v=8&partner_key=%s '
URL_LIST_SEARCH_PROG = 'https://www.rtbf.be/api/partner/generic/search/query?index=program&is_paid=0&q=%s&target_site' \
                       '=mediaz&v=8&partner_key=%s '

URL_SUB_CATEGORIES = 'https://www.rtbf.be/news/api/block?data[0][uuid]=%s&data[0][type]=widget&data[0][settings][id]=%s'
# data-uuid and part of data-uuid

URL_VIDEOS_BY_CAT_ID = 'https://www.rtbf.be/api/partner/generic/media/objectlist?' \
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
URL_LIVE_LAUNE = 'https://rtbf-live.fl.freecaster.net/live/rtbf/geo/drm/laune_aes.m3u8'
URL_LIVE_LADEUX = 'https://rtbf-live.fl.freecaster.net/live/rtbf/geo/drm/ladeux_aes.m3u8'
URL_LIVE_LATROIS = 'https://rtbf-live.fl.freecaster.net/live/rtbf/geo/drm/latrois_aes.m3u8'

URL_ROOT_LIVE = 'https://www.rtbf.be/auvio/direct#/'

# redbee variables
GIGYA_API_KEY = '3_kWKuPgcdAybqnqxq_MvHVk0-6PN8Zk8pIIkJM_yXOu-qLPDDsGOtIDFfpGivtbeO'
REDBEE_BASE_URL = 'https://exposure.api.redbee.live/v2/customer/RTBF/businessunit/Auvio'
RTBF_LOGIN_URL = 'https://login.rtbf.be/accounts.login'
RTBF_GETJWT_URL = 'https://login.rtbf.be/accounts.getJWT'


def get_partner_key():
    # Get partner key
    resp = urlquick.get(URL_ROOT_LIVE, max_age=-1)
    list_js_files = re.compile(
        r'<script type="text/javascript" src="(.*?)">').findall(resp.text)

    # Brute force :)
    partner_key_value = ''
    for js_file in list_js_files:
        resp2 = urlquick.get(js_file)
        partner_key_datas = re.compile('partner_key: \'(.+?)\'').findall(
            resp2.text)
        if len(partner_key_datas) > 0:
            partner_key_value = partner_key_datas[0]
            break
    # print 'partner_key_value : ' + partner_key_value
    return partner_key_value


# partner_key
PARTNER_KEY = get_partner_key()


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
    json_parser = resp.json()

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
    json_parser = resp.json()
    for results_datas in json_parser["results"]:
        is_redbee = False
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
        elif "url_embed" in video_datas:
            video_url = video_datas["url_embed"]
            is_drm = False
        else:
            video_url = video_datas["url"]
            is_drm = False
            if "tarmac" in video_url:
                is_redbee = True
                is_drm = video_datas["drm"]

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
                          is_drm=is_drm,
                          is_redbee=is_redbee)
        item_post_treatment(item, is_playable=True, is_downloadable=True)
        yield item


@Route.register
def list_videos_search_prog(plugin, search_query, item_id, page, **kwargs):
    resp = urlquick.get(URL_LIST_SEARCH_PROG % (search_query, PARTNER_KEY))
    json_parser = resp.json()

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
    json_parser = resp.json()

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
    json_parser = resp.json()

    for video_datas in json_parser:
        is_redbee = False
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
        elif "url_embed" in video_datas:
            video_url = video_datas["url_embed"]
            is_drm = False
        else:
            video_url = video_datas["url"]
            is_drm = False
            if "tarmac" in video_url:
                is_redbee = True
                is_drm = video_datas["drm"]

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
                          is_drm=is_drm,
                          is_redbee=is_redbee)
        item_post_treatment(item, is_playable=True, is_downloadable=not is_drm)
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

    list_data_uuid = re.compile(r'data-uuid=\"(.*?)\"').findall(resp.text)
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
def list_videos_category(plugin, item_id, cat_id, offset=0, **kwargs):
    url = URL_VIDEOS_BY_CAT_ID % (cat_id, PARTNER_KEY)
    if offset > 0:
        url += ('&offset=%s' % offset)
    resp = urlquick.get(url)
    json_parser = resp.json()

    for video_datas in json_parser:
        is_redbee = False
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
        elif "url_embed" in video_datas:
            video_url = video_datas["url_embed"]
            is_drm = False
        else:
            video_url = video_datas["url"]
            is_drm = False
            if "tarmac" in video_url:
                is_redbee = True
                is_drm = video_datas["drm"]

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
                          is_drm=is_drm,
                          is_redbee=is_redbee)
        item_post_treatment(item,
                            is_playable=True,
                            is_downloadable=True)
        yield item

    if len(json_parser) == 100:
        yield Listitem.next_page(item_id=item_id, cat_id=cat_id, offset=(offset + 100), callback=list_videos_category)


@Route.register
def list_videos_sub_category_dl(plugin, item_id, sub_category_data_uuid,
                                sub_category_id, **kwargs):
    resp = urlquick.get(
        URL_SUB_CATEGORIES %
        (sub_category_data_uuid, sub_category_data_uuid.split('-')[1]))
    json_parser = resp.json()

    parser = htmlement.HTMLement()
    parser.feed(json_parser["blocks"][sub_category_data_uuid])
    root = parser.close()

    item_found = False

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
            item_found = True
            yield item

    if not item_found:
        yield False
        return


def get_video_redbee(plugin, video_id, is_drm):
    login = plugin.setting.get_string('rtbf.login')
    password = plugin.setting.get_string('rtbf.password')
    if login == '' or password == '':
        xbmcgui.Dialog().ok(
            plugin.localize(30600),
            plugin.localize(30604) % ('RTBF (BE)', 'https://www.rtbf.be/auvio/'))
        return False

    rtbf_login_data = rtbf_login(plugin, login, password)
    if rtbf_login_data is None:
        return False

    rtbf_jwt = get_rtbf_jwt(plugin, rtbf_login_data['sessionInfo']['cookieValue'])
    if rtbf_jwt is None:
        return False

    redbee_jwt = get_redbee_jwt(plugin, rtbf_jwt['id_token'])

    video_format = get_redbee_format(plugin, video_id, redbee_jwt['sessionToken'], is_drm)
    if video_format is None:
        return False

    video_url = video_format['mediaLocator']

    if not is_drm:
        if video_url.endswith('m3u8'):
            return resolver_proxy.get_stream_with_quality(plugin, video_url=video_url, manifest_type="hls")
        return video_url

    if get_kodi_version() < 18:
        xbmcgui.Dialog().ok(plugin.localize(30600), plugin.localize(30602))
        return False

    is_helper = inputstreamhelper.Helper('mpd', drm='widevine')
    if not is_helper.check_inputstream():
        return False

    license_server_url = video_format['drm']['com.widevine.alpha']['licenseServerUrl']
    certificate_url = video_format['drm']['com.widevine.alpha']['certificateUrl']

    resp_cert = urlquick.get(certificate_url, max_age=-1).text
    certificate_data = base64.b64encode(resp_cert.encode("utf-8")).decode("utf-8")

    # TODO
    # subtitles = video_format['sprites'][0]['vtt']

    item = Listitem()
    item.path = video_url
    item.property[INPUTSTREAM_PROP] = 'inputstream.adaptive'
    item.property['inputstream.adaptive.manifest_type'] = 'mpd'
    item.property['inputstream.adaptive.license_type'] = 'com.widevine.alpha'
    item.property['inputstream.adaptive.license_key'] = license_server_url + '||R{SSM}|'
    item.property['inputstream.adaptive.server_certificate'] = certificate_data
    # item.property['inputstream.adaptive.manifest_update_parameter'] = 'full'
    stream_bitrate_limit = plugin.setting.get_int('stream_bitrate_limit')
    if stream_bitrate_limit > 0:
        item.property["inputstream.adaptive.max_bandwidth"] = str(stream_bitrate_limit * 1000)
    item.label = get_selected_item_label()
    item.art.update(get_selected_item_art())
    item.info.update(get_selected_item_info())
    return item


@Resolver.register
def get_video_url(plugin,
                  item_id,
                  video_url,
                  video_id,
                  is_drm,
                  download_mode=False,
                  is_redbee=False,
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
    if is_redbee:
        return get_video_redbee(plugin, video_id, is_drm)

    if is_drm:
        if get_kodi_version() < 18:
            xbmcgui.Dialog().ok(plugin.localize(30600), plugin.localize(30602))
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
            'customdata': json_parser_token["auth_encoded_xml"],
        }
        item.property['inputstream.adaptive.license_key'] = URL_LICENCE_KEY % urlencode(headers2)
        item.property['inputstream.adaptive.manifest_update_parameter'] = 'full'
        stream_bitrate_limit = plugin.setting.get_int('stream_bitrate_limit')
        if stream_bitrate_limit > 0:
            item.property["inputstream.adaptive.max_bandwidth"] = str(stream_bitrate_limit * 1000)
        item.label = get_selected_item_label()
        item.art.update(get_selected_item_art())
        item.info.update(get_selected_item_info())
        return item

    if video_url.endswith('m3u8'):
        return resolver_proxy.get_stream_with_quality(plugin, video_url=video_url, manifest_type="hls")

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

    if stream_url.endswith('m3u8'):
        return resolver_proxy.get_stream_with_quality(plugin, video_url=stream_url, manifest_type="hls")

    return stream_url


@Resolver.register
def set_live_url(plugin, item_id, **kwargs):
    resp = urlquick.get(URL_JSON_LIVE_CHANNEL % (item_id, PARTNER_KEY), max_age=-1)
    json_parser = resp.json()

    if "url_streaming" not in json_parser:
        plugin.notify(plugin.localize(30600), plugin.localize(30716))
        yield False
        return

    is_drm = json_parser["drm"]
    is_redbee = False
    if is_drm:
        if 'url_hls' in json_parser["url_streaming"]:
            live_url = json_parser["url_streaming"]["url_hls"]
            if "_drm.m3u8" in live_url:
                live_url = live_url.replace('_drm.m3u8', '_aes.m3u8')
            if "/.m3u8?" in live_url:
                live_url = live_url.replace('_drm.m3u8', '_aes.m3u8')
                if json_parser.get("external_id") is not None:
                    is_redbee = True
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
    item.set_callback(get_live_url,
                      item_id=item_id,
                      live_url=live_url,
                      is_drm=is_drm,
                      live_id=live_id,
                      is_redbee=is_redbee,
                      external_id=json_parser.get("external_id"))
    item_post_treatment(item, is_playable=True)
    yield item


@Route.register
def list_lives(plugin, item_id, **kwargs):
    resp = urlquick.get(URL_JSON_LIVE % PARTNER_KEY, max_age=-1)
    json_parser = resp.json()

    for live_datas in json_parser:

        if not live_datas["is_live"]:
            continue

        if "url_streaming" not in live_datas:
            plugin.notify(plugin.localize(30600), plugin.localize(30716))
            yield False
            return

        is_drm = live_datas["drm"]
        is_redbee = False
        if is_drm:
            if 'url_hls' in live_datas["url_streaming"]:
                live_url = live_datas["url_streaming"]["url_hls"]
                if "_drm.m3u8" in live_url:
                    live_url = live_url.replace('_drm.m3u8', '_aes.m3u8')
                if "/.m3u8?" in live_url:
                    if live_datas.get("external_id") is not None:
                        is_redbee = True
                live_id = live_datas["id"]
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
        start_time_value = format_hours(live_datas["start_date"])
        end_time_value = format_hours(live_datas["end_date"])
        date_value = format_day(live_datas["start_date"])
        live_title = live_channel_title + " - " + live_datas["title"]
        if live_datas['subtitle']:
            live_title += " - " + live_datas['subtitle']
        live_plot = 'Début le %s à %s (CET)' % (date_value, start_time_value) + '\n\r' + \
                    'Fin le %s à %s (CET)' % (date_value, end_time_value) + '\n\r' + \
                    'Accessibilité: ' + live_datas["geolock"]["title"] + '\n\r' + \
                    live_datas["description"]
        live_image = live_datas["images"]["illustration"]["16x9"]["1248x702"]

        item = Listitem()
        item.label = live_title
        item.art['thumb'] = item.art['landscape'] = live_image
        item.info['plot'] = live_plot
        # commented this line because otherwise sorting is made by date and then by title
        # and doesn't help to find the direct
        # item.info.date(date_time_value, '%Y/%m/%d')
        item.set_callback(get_live_url,
                          item_id=item_id,
                          live_url=live_url,
                          is_drm=is_drm,
                          live_id=live_id,
                          is_redbee=is_redbee,
                          external_id=live_datas.get("external_id"))
        item_post_treatment(item, is_playable=True)
        yield item


@Resolver.register
def get_live_url(plugin, item_id, live_url, is_drm, live_id, is_redbee=False, external_id=None, **kwargs):
    if is_drm:
        if get_kodi_version() < 18:
            xbmcgui.Dialog().ok(plugin.localize(30600), plugin.localize(30602))
            return False

        if is_redbee:
            return get_video_redbee(plugin, external_id, is_drm)

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
            'customdata': json_parser_token["auth_encoded_xml"],
        }
        item.property['inputstream.adaptive.license_key'] = URL_LICENCE_KEY % urlencode(headers2)
        item.property['inputstream.adaptive.manifest_update_parameter'] = 'full'
        stream_bitrate_limit = plugin.setting.get_int('stream_bitrate_limit')
        if stream_bitrate_limit > 0:
            item.property["inputstream.adaptive.max_bandwidth"] = str(stream_bitrate_limit * 1000)
        item.label = get_selected_item_label()
        item.art.update(get_selected_item_art())
        item.info.update(get_selected_item_info())
        return item

    return live_url


# redbee functions
def rtbf_login(plugin, user_login, user_pwd):
    url_params = {
        'loginID': user_login,
        'password': user_pwd,
        'apiKey': GIGYA_API_KEY,
        'format': 'json',
        'lang': 'fr'
    }

    resp = urlquick.get(RTBF_LOGIN_URL, params=url_params, max_age=-1)

    if not resp:
        plugin.notify(plugin.localize(30600), 'rtbf_login response: empty')
        return None

    json_parser = resp.json()

    if 'errorMessage' in json_parser:
        plugin.notify(plugin.localize(30600), 'rtbf_login errorMessage: %s' % (json_parser['errorMessage']))
        return None

    if json_parser['errorCode'] != 0:
        plugin.notify(plugin.localize(30600), "rtbf_login errorCode: #%s" % (json_parser['errorCode']))
        return None

    if json_parser['statusCode'] != 200:
        plugin.notify(plugin.localize(30600), "rtbf_login statusCode: #%s" % (json_parser['statusCode']))
        return None

    return json_parser


def get_rtbf_jwt(plugin, login_token):
    url_params = {
        'apiKey': GIGYA_API_KEY,
        'login_token': login_token,
        'format': 'json'
    }

    resp = urlquick.get(RTBF_GETJWT_URL, params=url_params, max_age=-1)

    if not resp:
        plugin.notify(plugin.localize(30600), 'get_rtbf_jwt response: empty')
        return None

    json_parser = resp.json()

    if 'errorMessage' in json_parser:
        plugin.notify(plugin.localize(30600), 'rtbf_getJWT errorMessage: %s' % (json_parser['errorMessage']))

    if json_parser['errorCode'] != 0:
        plugin.notify(plugin.localize(30600), "rtbf_getJWT errorCode: #%s" % (json_parser['errorCode']))
        return None

    if json_parser['statusCode'] != 200:
        plugin.notify(plugin.localize(30600), "rtbf_getJWT statusCode: #%s" % (json_parser['statusCode']))
        return None

    return json_parser


def get_redbee_jwt(plugin, rtbf_jwt):
    url = REDBEE_BASE_URL + '/auth/gigyaLogin'

    data_string = '{"jwt":"' + rtbf_jwt + '","device":{"deviceId":"123","name":"","type":"WEB"}}'
    data = data_string.encode("utf-8")

    headers = {
        'Content-Type': 'application/json'
    }

    return urlquick.post(url, headers=headers, data=data, max_age=-1).json()


def get_redbee_format(plugin, media_id, session_token, is_drm):
    url = REDBEE_BASE_URL + '/entitlement/{}/play'.format(media_id)

    headers = {
        'Authorization': 'Bearer {}'.format(session_token)
    }

    for fmt in urlquick.get(url, headers=headers, max_age=-1).json()['formats']:
        if fmt['format'] == 'HLS' and not is_drm:
            return fmt
        if fmt['format'] == 'DASH' and is_drm:
            return fmt

    return None
