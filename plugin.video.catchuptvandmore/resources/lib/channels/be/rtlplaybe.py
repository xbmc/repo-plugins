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


from resources.lib import web_utils
from resources.lib import download
from resources.lib.kodi_utils import get_kodi_version, get_selected_item_art, get_selected_item_label, get_selected_item_info
from resources.lib.menu_utils import item_post_treatment

import inputstreamhelper
import json
import re
import urlquick
from kodi_six import xbmc
from kodi_six import xbmcgui

# TO DO
# Playlists (cas les blagues de TOTO)

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
               'm6group_web/services/rtlbe_rtl_play/folders/%s/programs' \
               '?limit=999&offset=0&csa=6&with=parentcontext'

# Url to get program's subfolders
# e.g. Saison 5, Les meilleurs moments, les recettes pas à pas, ...
# We get an id by subfolder
URL_SUBCATEGORY = 'http://pc.middleware.6play.fr/6play/v2/platforms/' \
                  'm6group_web/services/rtlbe_rtl_play/programs/%s' \
                  '?with=links,subcats,rights'

# Url to get shows list
# e.g. Episode 1, Episode 2, ...
URL_VIDEOS = 'http://pc.middleware.6play.fr/6play/v2/platforms/' \
             'm6group_web/services/rtlbe_rtl_play/programs/%s/videos?' \
             'csa=6&with=clips,freemiumpacks&type=vi,vc,playlist&limit=999'\
             '&offset=0&subcat=%s&sort=subcat'

URL_VIDEOS2 = 'https://pc.middleware.6play.fr/6play/v2/platforms/' \
              'm6group_web/services/rtlbe_rtl_play/programs/%s/videos?' \
              'csa=6&with=clips,freemiumpacks&type=vi&limit=999&offset=0'


URL_JSON_VIDEO = 'https://pc.middleware.6play.fr/6play/v2/platforms/' \
                 'm6group_web/services/rtlbe_rtl_play/videos/%s'\
                 '?csa=6&with=clips,freemiumpacks'

URL_IMG = 'https://images.6play.fr/v1/images/%s/raw'

URL_COMPTE_LOGIN = 'https://accounts.eu1.gigya.com/accounts.login'
# https://login.6play.fr/accounts.login?loginID=*****&password=*******&targetEnv=mobile&format=jsonp&apiKey=3_hH5KBv25qZTd_sURpixbQW6a4OsiIzIEF2Ei_2H7TXTGLJb_1Hr4THKZianCQhWK&callback=jsonp_3bbusffr388pem4
# TODO get value Callback
# callback: jsonp_3bbusffr388pem4

URL_GET_JS_ID_API_KEY = 'https://www.rtlplay.be/connexion'

URL_API_KEY = 'https://www.rtlplay.be/client-%s.bundle.js'
# Id

URL_TOKEN_DRM = 'https://6play-users.6play.fr/v2/platforms/m6group_web/services/rtlbe_rtl_play/users/%s/videos/%s/upfront-token'

# URL_LICENCE_KEY = 'https://lic.drmtoday.com/license-proxy-widevine/cenc/|Content-Type=&User-Agent=Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3041.0 Safari/537.36&Host=lic.drmtoday.com&Origin=https://www.6play.fr&Referer=%s&x-dt-auth-token=%s|R{SSM}|JBlicense'
URL_LICENCE_KEY = 'https://lic.drmtoday.com/license-proxy-widevine/cenc/|Content-Type=&User-Agent=Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3041.0 Safari/537.36&Host=lic.drmtoday.com&x-dt-auth-token=%s&x-customer-name=rtlbe|R{SSM}|JBlicense'
# Referer, Token

URL_LIVE_JSON = 'https://pc.middleware.6play.fr/6play/v2/platforms/m6group_web/services/rtlbe_rtl_play/live?channel=%s&with=service_display_images,nextdiffusion,extra_data'
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
    resp = urlquick.get(URL_ROOT % ('rtlbe_' + item_id),
                        headers={
                            'User-Agent': web_utils.get_random_ua(),
                            'x-customer-name': 'rtlbe'})
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
    resp = urlquick.get(URL_CATEGORY % category_id,
                        headers={
                            'User-Agent': web_utils.get_random_ua(),
                            'x-customer-name': 'rtlbe'
                        })
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
        item.art['thumb'] = item.art['landscape'] = program_img
        item.art['fanart'] = program_fanart
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
    resp = urlquick.get(URL_SUBCATEGORY % program_id,
                        headers={
                            'User-Agent': web_utils.get_random_ua(),
                            'x-customer-name': 'rtlbe'
                        })
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
    yield item


@Route.register
def list_videos(plugin, item_id, program_id, sub_category_id, **kwargs):

    url = ''
    if sub_category_id is None:
        url = URL_VIDEOS2 % program_id
    else:
        url = URL_VIDEOS % (program_id, sub_category_id)
    resp = urlquick.get(url,
                        headers={
                            'User-Agent': web_utils.get_random_ua(),
                            'x-customer-name': 'rtlbe'
                        })
    json_parser = json.loads(resp.text)

    # TO DO Playlist More one 'clips'
    at_least_one_item = False
    for video in json_parser:
        video_id = str(video['id'])

        title = video['title']
        duration = video['clips'][0]['duration']
        description = ''
        if 'description' in video:
            description = video['description']
        try:
            aired = video['clips'][0]['product']['last_diffusion']
            aired = aired
            aired = aired[:10]
            # year = aired[:4]
            # date : string (%d.%m.%Y / 01.01.2009)
            # aired : string (2008-12-07)
            # day = aired.split('-')[2]
            # mounth = aired.split('-')[1]
            # year = aired.split('-')[0]
            # date = '.'.join((day, mounth, year))

        except Exception:
            aired = ''
            # year = ''
            # date = ''
        img = ''

        program_imgs = video['clips'][0]['images']
        program_img = ''
        for img in program_imgs:
            if img['role'] == 'vignette':
                external_key = img['external_key']
                program_img = URL_IMG % (external_key)

        item = Listitem()
        at_least_one_item = True
        item.label = title
        item.info['plot'] = description
        item.info['duration'] = duration
        item.art['thumb'] = item.art['landscape'] = program_img
        item.art['fanart'] = program_img
        try:
            item.info.date(aired, '%Y-%m-%d')
        except Exception:
            pass

        is_downloadable = False
        if get_kodi_version() < 18:
            is_downloadable = True

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
                    plugin.localize(30709),
                    all_datas_videos_quality)
                if seleted_item == -1:
                    return False
                final_video_url = all_datas_videos_path[seleted_item]
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
            return None

        resp_js_id = urlquick.get(URL_GET_JS_ID_API_KEY)
        js_id = re.compile(r'client\-(.*?)\.bundle\.js').findall(
            resp_js_id.text)[0]
        resp = urlquick.get(URL_API_KEY % js_id)

        api_key = re.compile(
            r'login.rtl.be\"\,key\:\"(.*?)\"').findall(
                resp.text)[0]

        if plugin.setting.get_string('rtlplaybe.login') == '' or\
                plugin.setting.get_string('rtlplaybe.password') == '':
            xbmcgui.Dialog().ok(
                'Info',
                plugin.localize(30604) %
                ('RTLPlay (BE)', 'https://www.rtlplay.be'))
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
        json_parser = json.loads(
            resp2.text.replace('gigya.callback(', '').replace(');', ''))
        if "UID" not in json_parser:
            plugin.notify('ERROR', 'RTLPlay (BE) : ' + plugin.localize(30711))
            return None
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


def live_entry(plugin, item_id, **kwargs):
    return get_live_url(plugin, item_id, item_id.upper())


@Resolver.register
def get_live_url(plugin, item_id, video_id, **kwargs):

    if get_kodi_version() < 18:
        xbmcgui.Dialog().ok('Info', plugin.localize(30602))
        return False

    resp_js_id = urlquick.get(URL_GET_JS_ID_API_KEY)
    js_id = re.compile(r'client\-(.*?)\.bundle\.js').findall(
        resp_js_id.text)[0]
    resp = urlquick.get(URL_API_KEY % js_id)

    api_key = re.compile(
        r'login.rtl.be\"\,key\:\"(.*?)\"').findall(
            resp.text)[0]

    if plugin.setting.get_string('rtlplaybe.login') == '' or\
            plugin.setting.get_string('rtlplaybe.password') == '':
        xbmcgui.Dialog().ok(
            'Info',
            plugin.localize(30604) %
            ('RTLPlay (BE)', 'https://www.rtlplay.be'))
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
    token_json = urlquick.get(URL_TOKEN_DRM % (account_id, 'dashcenc_%s' %
                                               (channel)),
                              headers=payload_headers,
                              max_age=-1)
    token_jsonparser = json.loads(token_json.text)
    token = token_jsonparser["token"]

    video_json = urlquick.get(URL_LIVE_JSON % (channel),
                              headers={
                                  'User-Agent': web_utils.get_random_ua(),
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
