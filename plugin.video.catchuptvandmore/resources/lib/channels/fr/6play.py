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

# The unicode_literals import only has
# an effect on Python 2.
# It makes string literals as unicode like in Python 3
from __future__ import unicode_literals

from builtins import str
from codequick import Route, Resolver, Listitem, utils, Script

from resources.lib.labels import LABELS
from resources.lib import web_utils
from resources.lib import download
from resources.lib.menu_utils import item_post_treatment
from resources.lib.kodi_utils import get_kodi_version, get_selected_item_art, get_selected_item_label, get_selected_item_info


import inputstreamhelper
import json
import re
import urlquick
from kodi_six import xbmc
from kodi_six import xbmcgui

# TO DO
# Playlists (cas les blagues de TOTO)
# Some DRM (m3u8) not working old videos (Kamelot)

# Thank you (https://github.com/peak3d/plugin.video.simple)

# Url to get channel's categories
# e.g. Info, Divertissement, Séries, ...
# We get an id by category
URL_ROOT = 'http://pc.middleware.6play.fr/6play/v2/platforms/' \
           'm6group_web/services/%s/folders?limit=999&offset=0'

# Url to get catgory's programs
# e.g. Le meilleur patissier, La france à un incroyable talent, ...
# We get an id by program
URL_CATEGORY = 'http://pc.middleware.6play.fr/6play/v2/platforms/' \
               'm6group_web/services/6play/folders/%s/programs' \
               '?limit=999&offset=0&csa=6&with=parentcontext'

# Url to get program's subfolders
# e.g. Saison 5, Les meilleurs moments, les recettes pas à pas, ...
# We get an id by subfolder
URL_SUBCATEGORY = 'http://pc.middleware.6play.fr/6play/v2/platforms/' \
                  'm6group_web/services/6play/programs/%s' \
                  '?with=links,subcats,rights'

# Url to get shows list
# e.g. Episode 1, Episode 2, ...
URL_VIDEOS = 'http://pc.middleware.6play.fr/6play/v2/platforms/' \
             'm6group_web/services/6play/programs/%s/videos?' \
             'csa=6&with=clips,freemiumpacks&type=vi,vc,playlist&limit=999'\
             '&offset=0&subcat=%s&sort=subcat'

URL_VIDEOS2 = 'https://pc.middleware.6play.fr/6play/v2/platforms/' \
              'm6group_web/services/6play/programs/%s/videos?' \
              'csa=6&with=clips,freemiumpacks&type=vi&limit=999&offset=0'


URL_JSON_VIDEO = 'https://pc.middleware.6play.fr/6play/v2/platforms/' \
                 'm6group_web/services/6play/videos/%s'\
                 '?csa=6&with=clips,freemiumpacks'

URL_IMG = 'https://images.6play.fr/v1/images/%s/raw'

URL_COMPTE_LOGIN = 'https://login.6play.fr/accounts.login'
# https://login.6play.fr/accounts.login?loginID=*****&password=*******&targetEnv=mobile&format=jsonp&apiKey=3_hH5KBv25qZTd_sURpixbQW6a4OsiIzIEF2Ei_2H7TXTGLJb_1Hr4THKZianCQhWK&callback=jsonp_3bbusffr388pem4
# TODO get value Callback
# callback: jsonp_3bbusffr388pem4

URL_GET_JS_ID_API_KEY = 'https://www.6play.fr/connexion'

URL_API_KEY = 'https://www.6play.fr/client-%s.bundle.js'
# Id

URL_TOKEN_DRM = 'https://6play-users.6play.fr/v2/platforms/m6group_web/services/6play/users/%s/videos/%s/upfront-token'

# URL_LICENCE_KEY = 'https://lic.drmtoday.com/license-proxy-widevine/cenc/|Content-Type=&User-Agent=Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3041.0 Safari/537.36&Host=lic.drmtoday.com&Origin=https://www.6play.fr&Referer=%s&x-dt-auth-token=%s|R{SSM}|JBlicense'
URL_LICENCE_KEY = 'https://lic.drmtoday.com/license-proxy-widevine/cenc/|Content-Type=&User-Agent=Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3041.0 Safari/537.36&Host=lic.drmtoday.com&x-dt-auth-token=%s|R{SSM}|JBlicense'
# Referer, Token

URL_LIVE_JSON = 'https://pc.middleware.6play.fr/6play/v2/platforms/m6group_web/services/6play/live?channel=%s&with=service_display_images,nextdiffusion,extra_data'
# Chaine

DESIRED_QUALITY = Script.setting['quality']


def replay_entry(plugin, item_id, **kwargs):
    """
    First executed function after replay_bridge
    """
    return list_categories(plugin, item_id)


@Route.register
def list_categories(plugin, item_id, **kwargs):
    """
    Build categories listing
    - Tous les programmes
    - Séries
    - Informations
    - ...
    """
    if item_id == 'rtl2' or \
            item_id == 'fun_radio' or \
            item_id == 'courses':
        resp = urlquick.get(URL_ROOT % item_id)
    else:
        resp = urlquick.get(URL_ROOT % (item_id + 'replay'))
    json_parser = json.loads(resp.text)

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
    resp = urlquick.get(URL_CATEGORY % category_id)
    json_parser = json.loads(resp.text)

    for array in json_parser:
        item = Listitem()
        program_title = array['title']
        program_id = str(array['id'])
        program_desc = array['description']
        program_imgs = array['images']
        program_img = ''
        program_fanart = ''
        for img in program_imgs:
            if img['role'] == 'vignette':
                external_key = img['external_key']
                program_img = URL_IMG % (external_key)
            elif img['role'] == 'carousel':
                external_key = img['external_key']
                program_fanart = URL_IMG % (external_key)

        item.label = program_title
        item.art["thumb"] = program_img
        item.art["fanart"] = program_fanart
        item.info['plot'] = program_desc
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
    resp = urlquick.get(URL_SUBCATEGORY % program_id)
    json_parser = json.loads(resp.text)

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

    item.info['duration'] = clip_dict.get('duration', None)
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
        if img['role'] == 'vignette':
            external_key = img['external_key']
            program_img = URL_IMG % (external_key)
            item.art["thumb"] = program_img
            item.art["fanart"] = program_img
            break


@Route.register
def list_videos(plugin, item_id, program_id, sub_category_id, **kwargs):

    url = ''
    if sub_category_id is None:
        url = URL_VIDEOS2 % program_id
    else:
        url = URL_VIDEOS % (program_id, sub_category_id)
    resp = urlquick.get(url)
    json_parser = json.loads(resp.text)

    if not json_parser:
        plugin.notify(plugin.localize(LABELS['No videos found']), '')
        yield False

    for video in json_parser:

        video_id = str(video['id'])

        item = Listitem()
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
                                      'x-customer-name': 'm6web'
                                  },
                                  max_age=-1)
        json_parser = json.loads(video_json.text)

        video_assets = json_parser['clips'][0]['assets']

        if video_assets is None:
            plugin.notify('ERROR', plugin.localize(30721))
            return False

        final_video_url = ''
        all_datas_videos_quality = []
        all_datas_videos_path = []
        for asset in video_assets:
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

        if len(all_datas_videos_quality) == 0:
            xbmcgui.Dialog().ok('Info', plugin.localize(30602))
            return False
        elif len(all_datas_videos_quality) == 1:
            final_video_url = all_datas_videos_path[0]
        else:
            if DESIRED_QUALITY == "DIALOG":
                seleted_item = xbmcgui.Dialog().select(
                    plugin.localize(LABELS['choose_video_quality']),
                    all_datas_videos_quality)
                if seleted_item == -1:
                    return False
                return all_datas_videos_path[seleted_item]
            elif DESIRED_QUALITY == "BEST":
                url_best = ''
                i = 0
                for data_video in all_datas_videos_quality:
                    if 'lq' not in data_video:
                        url_best = all_datas_videos_path[i]
                    i = i + 1
                final_video_url = url_best
            else:
                final_video_url = all_datas_videos_path[0]

        if download_mode:
            return download.download_video(final_video_url)
        return final_video_url

    else:

        resp_js_id = urlquick.get(URL_GET_JS_ID_API_KEY)
        js_id = re.compile(r'client\-(.*?)\.bundle\.js').findall(
            resp_js_id.text)[0]
        resp = urlquick.get(URL_API_KEY % js_id)

        api_key = re.compile(r'\"eu1.gigya.com\"\,key\:\"(.*?)\"').findall(
            resp.text)[0]

        if plugin.setting.get_string('6play.login') == '' or\
                plugin.setting.get_string('6play.password') == '':
            xbmcgui.Dialog().ok(
                'Info',
                plugin.localize(30604) % ('6play', 'https://www.6play.fr'))
            return False

        # Build PAYLOAD
        payload = {
            "loginID": plugin.setting.get_string('6play.login'),
            "password": plugin.setting.get_string('6play.password'),
            "apiKey": api_key,
            "format": "jsonp",
            "callback": "jsonp_3bbusffr388pem4"
        }
        # LOGIN
        resp2 = urlquick.post(URL_COMPTE_LOGIN,
                              data=payload,
                              headers={
                                  'User-Agent': web_utils.get_random_ua(),
                                  'referer': 'https://www.6play.fr/connexion'
                              })
        json_parser = json.loads(
            resp2.text.replace('jsonp_3bbusffr388pem4(', '').replace(');', ''))

        if "UID" not in json_parser:
            plugin.notify('ERROR', '6play : ' + plugin.localize(30711))
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
            'x-customer-name': 'm6web'
        }

        token_json = urlquick.get(URL_TOKEN_DRM % (account_id, video_id),
                                  headers=payload_headers,
                                  max_age=-1)

        token_jsonparser = json.loads(token_json.text)
        token = token_jsonparser["token"]

        video_json = urlquick.get(URL_JSON_VIDEO % video_id,
                                  headers={
                                      'User-Agent': web_utils.get_random_ua(),
                                      'x-customer-name': 'm6web'
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
                item.path = asset['full_physical_path']
                if 'http' in subtitle_url:
                    item.subtitles.append(subtitle_url)
                item.label = get_selected_item_label()
                item.art.update(get_selected_item_art())
                item.info.update(get_selected_item_info())
                item.property['inputstreamaddon'] = 'inputstream.adaptive'
                item.property['inputstream.adaptive.manifest_type'] = 'mpd'
                item.property[
                    'inputstream.adaptive.license_type'] = 'com.widevine.alpha'
                item.property[
                    'inputstream.adaptive.license_key'] = URL_LICENCE_KEY % token
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


@Resolver.register
def get_playlist_urls(plugin,
                      item_id,
                      video_id,
                      url,
                      **kwargs):
    resp = urlquick.get(url)
    json_parser = json.loads(resp.text)

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


def live_entry(plugin, item_id, **kwargs):
    return get_live_url(plugin, item_id, item_id.upper())


@Resolver.register
def get_live_url(plugin, item_id, video_id, **kwargs):

    if item_id == 'fun_radio' or \
            item_id == 'rtl2' or \
            item_id == 'mb':
        if item_id == 'mb':
            video_json = urlquick.get(
                URL_LIVE_JSON % (item_id.upper()),
                headers={'User-Agent': web_utils.get_random_ua()},
                max_age=-1)
            json_parser = json.loads(video_json.text)
            video_assets = json_parser[item_id.upper()][0]['live']['assets']
        else:
            video_json = urlquick.get(
                URL_LIVE_JSON % (item_id),
                headers={'User-Agent': web_utils.get_random_ua()},
                max_age=-1)
            json_parser = json.loads(video_json.text)
            video_assets = json_parser[item_id][0]['live']['assets']

        if not video_assets:
            plugin.notify('INFO', plugin.localize(30716))
            return False

        subtitle_url = ''
        if plugin.setting.get_boolean('active_subtitle'):
            for asset in video_assets:
                if 'subtitle_vtt' in asset["type"]:
                    subtitle_url = asset['full_physical_path']

        for asset in video_assets:
            if 'delta_hls_h264' in asset["type"]:
                item = Listitem()
                item.path = asset['full_physical_path']
                if 'http' in subtitle_url:
                    item.subtitles.append(subtitle_url)

                item.label = get_selected_item_label()
                item.art.update(get_selected_item_art())
                item.info.update(get_selected_item_info())
                return item
        return False

    else:

        if get_kodi_version() < 18:
            xbmcgui.Dialog().ok('Info', plugin.localize(30602))
            return False

        resp_js_id = urlquick.get(URL_GET_JS_ID_API_KEY)
        js_id = re.compile(r'client\-(.*?)\.bundle\.js').findall(
            resp_js_id.text)[0]
        resp = urlquick.get(URL_API_KEY % js_id)

        api_key = re.compile(r'\"eu1.gigya.com\"\,key\:\"(.*?)\"').findall(
            resp.text)[0]

        if plugin.setting.get_string('6play.login') == '' or\
                plugin.setting.get_string('6play.password') == '':
            xbmcgui.Dialog().ok(
                'Info',
                plugin.localize(30604) % ('6play', 'https://www.6play.fr'))
            return False

        # Build PAYLOAD
        payload = {
            "loginID": plugin.setting.get_string('6play.login'),
            "password": plugin.setting.get_string('6play.password'),
            "apiKey": api_key,
            "format": "jsonp",
            "callback": "jsonp_3bbusffr388pem4"
        }
        # LOGIN
        resp2 = urlquick.post(URL_COMPTE_LOGIN,
                              data=payload,
                              headers={
                                  'User-Agent': web_utils.get_random_ua(),
                                  'referer': 'https://www.6play.fr/connexion'
                              })
        json_parser = json.loads(
            resp2.text.replace('jsonp_3bbusffr388pem4(', '').replace(');', ''))

        if "UID" not in json_parser:
            plugin.notify('ERROR', '6play : ' + plugin.localize(30711))
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
            'x-customer-name': 'm6web'
        }

        if item_id == '6ter':
            token_json = urlquick.get(URL_TOKEN_DRM %
                                      (account_id, 'dashcenc_%s' % '6T'),
                                      headers=payload_headers,
                                      max_age=-1)
        else:
            token_json = urlquick.get(
                URL_TOKEN_DRM % (account_id, 'dashcenc_%s' % item_id.upper()),
                headers=payload_headers,
                max_age=-1)
        token_jsonparser = json.loads(token_json.text)
        token = token_jsonparser["token"]

        if item_id == '6ter':
            video_json = urlquick.get(
                URL_LIVE_JSON % '6T',
                headers={'User-Agent': web_utils.get_random_ua()},
                max_age=-1)
            json_parser = json.loads(video_json.text)
            video_assets = json_parser['6T'][0]['live']['assets']
        else:
            video_json = urlquick.get(
                URL_LIVE_JSON % (item_id.upper()),
                headers={'User-Agent': web_utils.get_random_ua()},
                max_age=-1)
            json_parser = json.loads(video_json.text)
            video_assets = json_parser[item_id.upper()][0]['live']['assets']

        if not video_assets:
            plugin.notify('INFO', plugin.localize(30716))
            return False

        subtitle_url = ''
        if plugin.setting.get_boolean('active_subtitle'):
            for asset in video_assets:
                if 'subtitle_vtt' in asset["type"]:
                    subtitle_url = asset['full_physical_path']

        for asset in video_assets:
            if 'delta_dashcenc_h264' in asset["type"]:
                item = Listitem()
                item.path = asset['full_physical_path']
                if 'http' in subtitle_url:
                    item.subtitles.append(subtitle_url)
                item.property['inputstreamaddon'] = 'inputstream.adaptive'
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
