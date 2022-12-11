# -*- coding: utf-8 -*-
# Copyright: (c) JUL1EN094, SPM, SylvainCecchetto
# Copyright: (c) 2016, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals

import json
import re
from builtins import str

import inputstreamhelper
import urlquick
from codequick import Listitem, Resolver, Route, Script
from kodi_six import xbmcgui

from resources.lib import download, web_utils
from resources.lib.addon_utils import get_item_media_path, Quality
from resources.lib.kodi_utils import (INPUTSTREAM_PROP, get_kodi_version,
                                      get_selected_item_art,
                                      get_selected_item_info,
                                      get_selected_item_label)
from resources.lib.menu_utils import item_post_treatment

# TO DO
# Playlists (cas les blagues de TOTO)

# Thank you (https://github.com/peak3d/plugin.video.simple)

# Url to get channel's categories
# e.g. Info, Divertissement, Séries, ...
# We get an id by category
URL_ROOT = 'http://android.middleware.6play.fr/6play/v2/platforms/' \
           'm6group_androidmob/services/%s/folders?limit=999&offset=0'

URL_ALL_PROGRAMS = 'http://android.middleware.6play.fr/6play/v2/platforms/' \
                   'm6group_androidmob/services/rtlbe_rtl_play/programs' \
                   '?limit=999&offset=0&csa=6&firstLetter=%s&with=rights'

# Url to get catgory's programs
# e.g. Le meilleur patissier, La france à un incroyable talent, ...
# We get an id by program
URL_CATEGORY = 'http://android.middleware.6play.fr/6play/v2/platforms/' \
               'm6group_androidmob/services/rtlbe_rtl_play/folders/%s/programs' \
               '?limit=999&offset=0&csa=6&with=parentcontext'

# Url to get program's subfolders
# e.g. Saison 5, Les meilleurs moments, les recettes pas à pas, ...
# We get an id by subfolder
URL_SUBCATEGORY = 'http://android.middleware.6play.fr/6play/v2/platforms/' \
                  'm6group_androidmob/services/rtlbe_rtl_play/programs/%s' \
                  '?with=links,subcats,rights'

# Url to get shows list
# e.g. Episode 1, Episode 2, ...
URL_VIDEOS = 'http://chromecast.middleware.6play.fr/6play/v2/platforms/' \
             'chromecast/services/rtlbe_rtl_play/programs/%s/videos?' \
             'csa=6&with=clips,freemiumpacks&type=vi,vc,playlist&limit=999'\
             '&offset=0&subcat=%s&sort=subcat'

URL_VIDEOS2 = 'https://chromecast.middleware.6play.fr/6play/v2/platforms/' \
              'chromecast/services/rtlbe_rtl_play/programs/%s/videos?' \
              'csa=6&with=clips,freemiumpacks&type=vi&limit=999&offset=0'

URL_SEARCH = 'https://nhacvivxxk-dsn.algolia.net/1/indexes/*/queries?x-algolia-agent=Algolia%20for%20JavaScript%20(' \
             '4.10.5)%3B%20Browser'

URL_JSON_VIDEO = 'https://chromecast.middleware.6play.fr/6play/v2/platforms/' \
                 'chromecast/services/rtlbe_rtl_play/videos/%s'\
                 '?csa=6&with=clips,freemiumpacks'

URL_IMG = 'https://images.6play.fr/v1/images/%s/raw'

URL_COMPTE_LOGIN = 'https://accounts.eu1.gigya.com/accounts.login'
# https://login.6play.fr/accounts.login?loginID=*****&password=*******&targetEnv=mobile&format=jsonp&apiKey=3_hH5KBv25qZTd_sURpixbQW6a4OsiIzIEF2Ei_2H7TXTGLJb_1Hr4THKZianCQhWK&callback=jsonp_3bbusffr388pem4
# TODO get value Callback
# callback: jsonp_3bbusffr388pem4

URL_GET_JS_ID_API_KEY = 'https://www.rtlplay.be/connexion'

URL_API_KEY = 'https://www.rtlplay.be/client-%s.bundle.js'
# Id

URL_TOKEN_DRM = 'https://6play-users.6play.fr/v2/platforms/chromecast/services/rtlbe_rtl_play/users/%s/videos/%s/upfront-token'

# URL_LICENCE_KEY = 'https://lic.drmtoday.com/license-proxy-widevine/cenc/|Content-Type=&User-Agent=Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3041.0 Safari/537.36&Host=lic.drmtoday.com&Origin=https://www.6play.fr&Referer=%s&x-dt-auth-token=%s|R{SSM}|JBlicense'
URL_LICENCE_KEY = 'https://lic.drmtoday.com/license-proxy-widevine/cenc/|Content-Type=&User-Agent=Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3041.0 Safari/537.36&Host=lic.drmtoday.com&x-dt-auth-token=%s&x-customer-name=rtlbe|R{SSM}|JBlicense'
# Referer, Token

URL_LIVE_JSON = 'https://chromecast.middleware.6play.fr/6play/v2/platforms/chromecast/services/rtlbe_rtl_play/live?channel=%s&with=service_display_images,nextdiffusion,extra_data'
# Chaine


@Route.register
def rtlplay_root(plugin, **kwargs):
    # (item_id, label, thumb, fanart)
    channels = [
        ('rtl_tvi', 'RTL TVI', 'rtltvi.png', 'rtltvi_fanart.jpg'),
        ('club_rtl', 'CLUB RTL', 'clubrtl.png', 'clubrtl_fanart.jpg'),
        ('plug_rtl', 'PLUG RTL', 'plugrtl.png', 'plugrtl_fanart.jpg'),
        ('rtl_info', 'RTL INFO', 'rtlinfo.png', 'rtlinfo_fanart.jpg'),
        ('rtl_sport', 'RTL Sport', 'rtlsport.png', 'rtlsport_fanart.jpg'),
        ('bel_rtl', 'BEL RTL', 'belrtl.png', 'belrtl_fanart.jpg'),
        ('contact', 'Contact', 'contact.png', 'contact_fanart.jpg'),
        ('rtl_play', 'RTL Play', 'rtlplay.png', 'rtlplay_fanart.jpg')
    ]

    for channel_infos in channels:
        item = Listitem()
        item.label = channel_infos[1]
        item.art["thumb"] = get_item_media_path('channels/be/' + channel_infos[2])
        item.art["fanart"] = get_item_media_path('channels/be/' + channel_infos[3])
        item.set_callback(list_categories, channel_infos[0])
        item_post_treatment(item)
        yield item

    # all programs
    item = Listitem()
    item.label = plugin.localize(30717)
    item.art["thumb"] = get_item_media_path('channels/be/rtlplay.png')
    item.art["fanart"] = get_item_media_path('channels/be/rtlplay_fanart.jpg')
    item.set_callback(list_all_programs, 'rtl_play')
    item_post_treatment(item)
    yield item

    item = Listitem.search(list_videos_search, item_id='rtl_play', page='0')
    item.label = plugin.localize(30715)
    item_post_treatment(item)
    yield item


@Route.register
def list_videos_search(plugin, search_query, item_id, page, **kwargs):

    if search_query is None or len(search_query) == 0:
        return False

    json_body_template = """
    {
        "requests": [
            {
              "indexName": "rtlmutu_prod_bedrock_layout_items_v1_rtlbe_main",
              "query": "search_term",
              "params": "hitsPerPage=50&facetFilters=%5B%22metadata.item_type%3Afunctionality%22%5D"
            },
            {
              "indexName": "rtlmutu_prod_bedrock_layout_items_v1_rtlbe_main",
              "query": "search_term",
              "params": "hitsPerPage=50&facetFilters=%5B%22metadata.item_type%3Aplaylist%22%5D"
            },
            {
              "indexName": "rtlmutu_prod_bedrock_layout_items_v1_rtlbe_main",
              "query": "search_term",
              "params": "hitsPerPage=50&facetFilters=%5B%22metadata.item_type%3Aprogram%22%5D"
            },
            {
              "indexName": "rtlmutu_prod_bedrock_layout_items_v1_rtlbe_main",
              "query": "search_term",
              "params": "hitsPerPage=50&facetFilters=%5B%22metadata.item_type%3Avc%22%5D"
            },
            {
              "indexName": "rtlmutu_prod_bedrock_layout_items_v1_rtlbe_main",
              "query": "search_term",
              "params": "hitsPerPage=50&facetFilters=%5B%22metadata.item_type%3Avi%22%5D"
            }
          ]
    }

    """

    json_body = json.loads(json_body_template)
    for request in json_body['requests']:
        request['query'] = search_query

    headers = {
        'User-Agent': web_utils.get_random_ua(),
        'Accept': '*/*',
        'Accept-Language': 'fr,fr-FR;q=0.8,en-US;q=0.5,en;q=0.3',
        'Accept-Encoding': 'gzip, deflate, br',
        'Content-Type': 'application/x-www-form-urlencoded',
        'x-algolia-api-key': '5fce02cb376fb2cda773be8a8404598a',
        'x-algolia-application-id': 'NHACVIVXXK',
        'Origin': 'https://www.rtlplay.be',
        'DNT': '1',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'cross-site',
        'Referer': 'https://www.rtlplay.be/',
        'Connection': 'keep-alive'
    }

    resp = urlquick.post(URL_SEARCH, None, json_body, headers=headers)
    json_parser = resp.json()

    for result in json_parser["results"]:
        if result["nbHits"] > 0:
            for hit in result["hits"]:
                search_title = hit["item"]["itemContent"]["title"]
                search_id = hit["item"]["itemContent"]["action"]["target"]["value_layout"]["id"]
                search_type = hit["item"]["itemContent"]["action"]["target"]["value_layout"]["type"]
                # search_image = result["data"]["images"]["illustration"]["16x9"]["1248x702"]
                if search_type == "program":
                    item = Listitem()
                    item.label = search_title
                    # item.art['thumb'] = item.art['landscape'] = search_image
                    item.set_callback(list_program_categories,
                                      item_id=item_id,
                                      program_id=search_id)
                    item_post_treatment(item)
                    yield
                    yield item
                else:
                    is_downloadable = False
                    if get_kodi_version() < 18:
                        is_downloadable = True

                    if search_type != 'playlist':
                        item = Listitem()
                        item.label = search_title
                        # populate_item(item, video['clips'][0])
                        item.set_callback(get_video_url,
                                          item_id=item_id,
                                          video_id=search_id)
                    # TODO playlist
                    # else:
                    #     item = Listitem()
                    #     item.label = search_title
                    #     # populate_item(item, video)
                    #     item.set_callback(get_playlist_urls,
                    #                       item_id=item_id,
                    #                       video_id=search_id,
                    #                       url=url)

                        item_post_treatment(item,
                                            is_playable=True,
                                            is_downloadable=is_downloadable)
                        yield
                        yield item


@Route.register
def list_all_programs(plugin, item_id, **kwargs):
    letters = ['@', 'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't',
               'u', 'v', 'w', 'y', 'z']

    for letter in letters:
        item = Listitem()
        item.label = plugin.localize(30717) + ' : ' + letter
        item.art["thumb"] = get_item_media_path('channels/be/rtlplay.png')
        item.art["fanart"] = get_item_media_path('channels/be/rtlplay_fanart.jpg')
        item.set_callback(list_all_programs_by_letter, item_id, letter)
        item_post_treatment(item)
        yield item


@Route.register
def list_all_programs_by_letter(plugin, item_id, letter, **kwargs):
    resp = urlquick.get(URL_ALL_PROGRAMS % letter,
                        headers={
                            'User-Agent': web_utils.get_random_ua(),
                            'x-customer-name': 'rtlbe'})
    json_parser = resp.json()

    at_least_one_item = False
    for array in json_parser:
        at_least_one_item = True
        item = Listitem()
        program_id = str(array['id'])
        item.label = array['title']
        populate_item(item, array)
        item.set_callback(list_program_categories,
                          item_id=item_id,
                          program_id=program_id)
        item_post_treatment(item)
        yield item

    if not at_least_one_item:
        plugin.notify(plugin.localize(30718), '')
        yield False


@Route.register
def list_categories(plugin, item_id, **kwargs):
    """
    Build categories listing
    - Tous les programmes
    - Séries
    - Informations
    - ...
    """
    resp = urlquick.get(URL_ROOT % ('rtlbe_' + item_id),
                        headers={
                            'User-Agent': web_utils.get_random_ua(),
                            'x-customer-name': 'rtlbe'})
    json_parser = resp.json()

    for array in json_parser:
        category_id = str(array['id'])
        category_name = array['name']

        item = Listitem()
        item.label = category_name
        item.set_callback(list_programs,
                          item_id=item_id,
                          category_id=category_id)
        item_post_treatment(item)
        yield item


@Route.register
def list_programs(plugin, item_id, category_id, **kwargs):
    """
    Build programs listing
    - Les feux de l'amour
    - ...
    """
    resp = urlquick.get(URL_CATEGORY % category_id,
                        headers={
                            'User-Agent': web_utils.get_random_ua(),
                            'x-customer-name': 'rtlbe'
                        })
    json_parser = resp.json()

    for array in json_parser:
        item = Listitem()
        program_id = str(array['id'])
        item.label = array['title']
        populate_item(item, array)
        item.set_callback(list_program_categories,
                          item_id=item_id,
                          program_id=program_id)
        item_post_treatment(item)
        yield item


@Route.register
def list_program_categories(plugin, item_id, program_id, **kwargs):
    """
    Build program categories
    - Toutes les vidéos
    - Tous les replay
    - Saison 1
    - ...
    """
    resp = urlquick.get(URL_SUBCATEGORY % program_id,
                        headers={
                            'User-Agent': web_utils.get_random_ua(),
                            'x-customer-name': 'rtlbe'
                        })
    json_parser = resp.json()

    for sub_category in json_parser['program_subcats']:
        item = Listitem()
        sub_category_id = str(sub_category['id'])
        sub_category_title = sub_category['title']

        item.label = sub_category_title
        item.set_callback(list_videos,
                          item_id=item_id,
                          program_id=program_id,
                          sub_category_id=sub_category_id)
        item_post_treatment(item)
        yield item

    item = Listitem()
    item.label = plugin.localize(30701)
    item.set_callback(list_videos,
                      item_id=item_id,
                      program_id=program_id,
                      sub_category_id=None)
    item_post_treatment(item)
    yield item


def populate_item(item, clip_dict):
    duration = clip_dict.get('duration', None)
    if duration is not None:
        item.info['duration'] = duration
    item.info['plot'] = clip_dict.get('description', None)

    try:
        aired = clip_dict['product']['last_diffusion']
        aired = aired
        aired = aired[:10]
        item.info.date(aired, '%Y-%m-%d')
    except Exception:
        pass

    program_imgs = clip_dict['images']
    for img in program_imgs:
        if img['role'] == 'vignette' or img['role'] == 'carousel':
            external_key = img['external_key']
            program_img = URL_IMG % external_key
            item.art['thumb'] = item.art['landscape'] = program_img
            item.art['fanart'] = program_img
            break


@Route.register
def list_videos(plugin, item_id, program_id, sub_category_id, **kwargs):
    if sub_category_id is None:
        url = URL_VIDEOS2 % program_id
    else:
        url = URL_VIDEOS % (program_id, sub_category_id)
    resp = urlquick.get(url,
                        headers={
                            'User-Agent': web_utils.get_random_ua(),
                            'x-customer-name': 'rtlbe'
                        })
    json_parser = resp.json()

    if not json_parser:
        plugin.notify(plugin.localize(30718), '')
        yield False

    at_least_one_item = False
    for video in json_parser:
        video_id = str(video['id'])

        item = Listitem()
        at_least_one_item = True
        item.label = video['title']

        is_downloadable = False
        if get_kodi_version() < 18:
            is_downloadable = True

        if 'type' in video and video['type'] == 'playlist':
            populate_item(item, video)
            item.set_callback(get_playlist_urls,
                              item_id=item_id,
                              video_id=video_id,
                              url=url)
        else:
            populate_item(item, video['clips'][0])
            item.set_callback(get_video_url,
                              item_id=item_id,
                              video_id=video_id)
        item_post_treatment(item,
                            is_playable=True,
                            is_downloadable=is_downloadable)
        yield item

    if not at_least_one_item:
        plugin.notify(plugin.localize(30718), '')
        yield False


@Resolver.register
def get_video_url(plugin,
                  item_id,
                  video_id,
                  download_mode=False,
                  **kwargs):

    if get_kodi_version() < 18:
        video_json = urlquick.get(URL_JSON_VIDEO % video_id,
                                  headers={
                                      'User-Agent': web_utils.get_random_ua(),
                                      'x-customer-name': 'rtlbe'
                                  },
                                  max_age=-1)
        json_parser = json.loads(video_json.text)

        video_assets = json_parser['clips'][0]['assets']

        final_video_url = get_final_video_url(plugin, video_assets)
        if final_video_url is None:
            return False

        if download_mode:
            return download.download_video(final_video_url)

        return final_video_url

    resp_js_id = urlquick.get(URL_GET_JS_ID_API_KEY)
    js_id = re.compile(r'client\-(.*?)\.bundle\.js').findall(resp_js_id.text)[0]
    resp = urlquick.get(URL_API_KEY % js_id)

    # Hack to force encoding of the response
    resp.encoding = 'utf-8'
    api_key = re.compile(r'login.rtl.be\"\,key\:\"(.*?)\"').findall(resp.text)[0]

    if plugin.setting.get_string('rtlplaybe.login') == '' or\
            plugin.setting.get_string('rtlplaybe.password') == '':
        xbmcgui.Dialog().ok(
            'Info',
            plugin.localize(30604) % ('RTLPlay (BE)', 'https://www.rtlplay.be'))
        return False

    # Build PAYLOAD
    payload = {
        "loginID": plugin.setting.get_string('rtlplaybe.login'),
        "password": plugin.setting.get_string('rtlplaybe.password'),
        "apiKey": api_key,
        "format": "jsonp",
        "callback": "gigya.callback"
    }
    # LOGIN
    resp2 = urlquick.post(URL_COMPTE_LOGIN,
                          data=payload,
                          headers={
                              'User-Agent': web_utils.get_random_ua(),
                              'referer': 'https://www.rtlplay.be/connexion'
                          })
    json_parser = json.loads(resp2.text.replace('gigya.callback(', '').replace(');', ''))

    if "UID" not in json_parser:
        plugin.notify('ERROR', 'RTLPlay (BE) : ' + plugin.localize(30711))
        return False
    account_id = json_parser["UID"]
    account_timestamp = json_parser["signatureTimestamp"]
    account_signature = json_parser["UIDSignature"]

    is_helper = inputstreamhelper.Helper('mpd', drm='widevine')
    if not is_helper.check_inputstream():
        return False

    # Build PAYLOAD headers
    payload_headers = {
        'x-auth-gigya-signature': account_signature,
        'x-auth-gigya-signature-timestamp': account_timestamp,
        'x-auth-gigya-uid': account_id,
        'User-Agent': web_utils.get_random_ua(),
        'x-customer-name': 'rtlbe'
    }

    token_json = urlquick.get(URL_TOKEN_DRM % (account_id, video_id),
                              headers=payload_headers,
                              max_age=-1)

    token_jsonparser = json.loads(token_json.text)
    token = token_jsonparser["token"]

    video_json = urlquick.get(URL_JSON_VIDEO % video_id,
                              headers={
                                  'User-Agent': web_utils.get_random_ua(),
                                  'x-customer-name': 'rtlbe'
                              },
                              max_age=-1)
    json_parser = json.loads(video_json.text)

    video_assets = json_parser['clips'][0]['assets']

    if video_assets is None:
        plugin.notify('ERROR', plugin.localize(30721))
        return False

    subtitle_url = ''
    if plugin.setting.get_boolean('active_subtitle'):
        for asset in video_assets:
            if 'subtitle_vtt' in asset["type"]:
                subtitle_url = asset['full_physical_path']

    for asset in video_assets:
        if 'usp_dashcenc_h264' in asset["type"]:
            item = Listitem()
            dummy_req = urlquick.get(asset['full_physical_path'],
                                     headers={'User-Agent': web_utils.get_random_ua()},
                                     allow_redirects=False)
            if 'location' in dummy_req.headers:
                item.path = dummy_req.headers['location']
            else:
                item.path = asset['full_physical_path']
            if 'http' in subtitle_url:
                item.subtitles.append(subtitle_url)
            item.label = get_selected_item_label()
            item.art.update(get_selected_item_art())
            item.info.update(get_selected_item_info())
            item.property[INPUTSTREAM_PROP] = 'inputstream.adaptive'
            item.property['inputstream.adaptive.manifest_type'] = 'mpd'
            item.property['inputstream.adaptive.license_type'] = 'com.widevine.alpha'
            item.property['inputstream.adaptive.license_key'] = URL_LICENCE_KEY % token
            return item
    for asset in video_assets:
        if 'http_h264' in asset["type"]:
            if "hd" in asset["video_quality"]:
                item = Listitem()
                item.path = asset['full_physical_path']
                if 'http' in subtitle_url:
                    item.subtitles.append(subtitle_url)
                item.label = get_selected_item_label()
                item.art.update(get_selected_item_art())
                item.info.update(get_selected_item_info())
                return item
    return False


def get_final_video_url(plugin, video_assets, asset_type=None):
    if video_assets is None:
        plugin.notify('ERROR', plugin.localize(30721))
        return None

    all_datas_videos_quality = []
    all_datas_videos_path = []
    for asset in video_assets:
        if asset_type is None:
            if 'http_h264' in asset["type"]:
                all_datas_videos_quality.append(asset["video_quality"])
                all_datas_videos_path.append(asset['full_physical_path'])
            elif 'h264' in asset["type"]:
                manifest = urlquick.get(
                    asset['full_physical_path'],
                    headers={'User-Agent': web_utils.get_random_ua()},
                    max_age=-1)
                if 'drm' not in manifest.text:
                    all_datas_videos_quality.append(asset["video_quality"])
                    all_datas_videos_path.append(asset['full_physical_path'])
        elif asset_type in asset["type"]:
            all_datas_videos_quality.append(asset["video_quality"])
            all_datas_videos_path.append(asset['full_physical_path'])

    if len(all_datas_videos_quality) == 0:
        xbmcgui.Dialog().ok('Info', plugin.localize(30602))
        return None

    final_video_url = all_datas_videos_path[0]

    desired_quality = Script.setting.get_string('quality')
    if desired_quality == Quality['DIALOG']:
        selected_item = xbmcgui.Dialog().select(
            plugin.localize(30709),
            all_datas_videos_quality)
        if selected_item == -1:
            return None
        final_video_url = all_datas_videos_path[selected_item]

    elif desired_quality == Quality['BEST']:
        url_best = ''
        i = 0
        for data_video in all_datas_videos_quality:
            if 'lq' not in data_video:
                url_best = all_datas_videos_path[i]
            i = i + 1
        final_video_url = url_best

    elif desired_quality == Quality['WORST']:
        final_video_url = all_datas_videos_path[0]
        i = 0
        for data_video in all_datas_videos_quality:
            if 'lq' in data_video:
                final_video_url = all_datas_videos_path[i]
                return final_video_url

    return final_video_url


@Resolver.register
def get_playlist_urls(plugin,
                      item_id,
                      video_id,
                      url,
                      **kwargs):
    resp = urlquick.get(url)
    json_parser = resp.json()

    for video in json_parser:
        current_video_id = str(video['id'])

        if current_video_id != video_id:
            continue

        playlist_videos = []

        for clip in video['clips']:
            clip_id = str(clip['video_id'])

            item = Listitem()
            item.label = clip['title']

            populate_item(item, clip)

            video = get_video_url(
                plugin,
                item_id=item_id,
                video_id=clip_id)

            playlist_videos.append(video)

        return playlist_videos


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):

    if get_kodi_version() < 18:
        xbmcgui.Dialog().ok('Info', plugin.localize(30602))
        return False

    resp_js_id = urlquick.get(URL_GET_JS_ID_API_KEY)
    js_id = re.compile(r'client\-(.*?)\.bundle\.js').findall(
        resp_js_id.text)[0]
    resp = urlquick.get(URL_API_KEY % js_id)

    # Hack to force encoding of the response
    resp.encoding = 'utf-8'
    api_key = re.compile(r'login.rtl.be\"\,key\:\"(.*?)\"').findall(
        resp.text)[0]

    if plugin.setting.get_string('rtlplaybe.login') == '' or\
            plugin.setting.get_string('rtlplaybe.password') == '':
        xbmcgui.Dialog().ok(
            plugin.localize(30600),
            plugin.localize(30604) % ('RTLPlay (BE)', 'https://www.rtlplay.be'))
        return False

    # Build PAYLOAD
    payload = {
        "loginID": plugin.setting.get_string('rtlplaybe.login'),
        "password": plugin.setting.get_string('rtlplaybe.password'),
        "apiKey": api_key,
        "format": "jsonp",
        "callback": "gigya.callback"
    }
    # LOGIN
    resp2 = urlquick.post(
        URL_COMPTE_LOGIN,
        data=payload,
        headers={
            'User-Agent': web_utils.get_random_ua(),
            'referer': 'https://www.rtlplay.be/connexion'})
    json_parser = json.loads(
        resp2.text.replace('gigya.callback(', '').replace(');', ''))

    if "UID" not in json_parser:
        plugin.notify('ERROR', 'RTLPlay (BE) : ' + plugin.localize(30711))
        return False
    account_id = json_parser["UID"]
    account_timestamp = json_parser["signatureTimestamp"]
    account_signature = json_parser["UIDSignature"]

    is_helper = inputstreamhelper.Helper('mpd', drm='widevine')
    if not is_helper.check_inputstream():
        return False

    # Build PAYLOAD headers
    payload_headers = {
        'x-auth-gigya-signature': account_signature,
        'x-auth-gigya-signature-timestamp': account_timestamp,
        'x-auth-gigya-uid': account_id,
        'User-Agent': web_utils.get_random_ua(),
        'x-customer-name': 'rtlbe'
    }
    channel = 'rtlbe_' + item_id
    token_json = urlquick.get(
        URL_TOKEN_DRM % (account_id, 'dashcenc_%s' % channel),
        headers=payload_headers,
        max_age=-1)
    token_jsonparser = json.loads(token_json.text)
    token = token_jsonparser["token"]

    video_json = urlquick.get(
        URL_LIVE_JSON % channel,
        headers={'User-Agent': web_utils.get_random_ua(),
                 'x-customer-name': 'rtlbe'},
        max_age=-1)
    json_parser = json.loads(video_json.text)
    if not json_parser[channel]:
        plugin.notify('ERROR', plugin.localize(30712))
        return False

    video_assets = json_parser[channel][0]['live']['assets']

    if not video_assets:
        plugin.notify('INFO', plugin.localize(30716))
        return False

    subtitle_url = ''
    if plugin.setting.get_boolean('active_subtitle'):
        for asset in video_assets:
            if 'subtitle_vtt' in asset["type"]:
                subtitle_url = asset['full_physical_path']

    final_video_url = get_final_video_url(plugin, video_assets, 'delta_dashcenc_h264')
    if final_video_url is None:
        return False

    for asset in video_assets:
        if 'delta_dashcenc_h264' in asset["type"]:
            item = Listitem()
            item.path = final_video_url
            if 'http' in subtitle_url:
                item.subtitles.append(subtitle_url)
            item.property[INPUTSTREAM_PROP] = 'inputstream.adaptive'
            item.property['inputstream.adaptive.manifest_type'] = 'mpd'
            item.property[
                'inputstream.adaptive.license_type'] = 'com.widevine.alpha'
            item.property[
                'inputstream.adaptive.license_key'] = URL_LICENCE_KEY % token

            item.label = get_selected_item_label()
            item.art.update(get_selected_item_art())
            item.info.update(get_selected_item_info())
            return item
    return False
