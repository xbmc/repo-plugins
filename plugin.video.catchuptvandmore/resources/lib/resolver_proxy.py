# -*- coding: utf-8 -*-
# Copyright: (c) 2017, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals

import json
import re
from random import randint
# noinspection PyUnresolvedReferences
import inputstreamhelper
import urlquick
# noinspection PyUnresolvedReferences
from codequick import Listitem, Route, Script
# noinspection PyUnresolvedReferences
from kodi_six import xbmcgui
from resources.lib import download, web_utils
from resources.lib.addon_utils import get_quality_YTDL, Quality
from resources.lib.kodi_utils import (INPUTSTREAM_PROP, get_selected_item_art,
                                      get_selected_item_info,
                                      get_selected_item_label, get_kodi_version)
from resources.lib.streams.m3u8 import M3u8

try:
    from urllib.parse import quote_plus
    from urllib.parse import urlencode
except ImportError:
    from urllib import quote_plus
    from urllib import urlencode

# TO DO
# Quality VIMEO
# Download Mode with Facebook (the video has no audio)

URL_DAILYMOTION_EMBED = 'http://www.dailymotion.com/embed/video/%s'
# Video_id

URL_VIMEO_BY_ID = 'https://player.vimeo.com/video/%s?byline=0&portrait=0&autoplay=1'
# Video_id

URL_FACEBOOK_BY_ID = 'https://www.facebook.com/allocine/videos/%s'
# Video_id

URL_YOUTUBE = 'https://www.youtube.com/embed/%s?&autoplay=0'
# Video_id

URL_BRIGHTCOVE_POLICY_KEY = 'http://players.brightcove.net/%s/%s_default/index.min.js'
# AccountId, PlayerId

URL_BRIGHTCOVE_VIDEO_JSON = 'https://edge.api.brightcove.com/' \
                            'playback/v1/accounts/%s/videos/%s'
# AccountId, VideoId

URL_MTVNSERVICES_STREAM = 'https://media-utils.mtvnservices.com/services/' \
                          'MediaGenerator/%s?&format=json&acceptMethods=hls'
# videoURI

URL_MTVNSERVICES_STREAM_ACCOUNT = 'https://media-utils.mtvnservices.com/services/' \
                                  'MediaGenerator/%s?&format=json&acceptMethods=hls' \
                                  '&accountOverride=%s'
# videoURI, accountOverride

URL_MTVNSERVICES_STREAM_ACCOUNT_EP = 'https://media-utils.mtvnservices.com/services/' \
                                     'MediaGenerator/%s?&format=json&acceptMethods=hls' \
                                     '&accountOverride=%s&ep=%s'
# videoURI, accountOverride, ep

URL_FRANCETV_PROGRAM_INFO = 'https://player.webservices.francetelevisions.fr/v1/videos/%s'
# VideoId

URL_FRANCETV_HDFAUTH_URL = 'https://hdfauthftv-a.akamaihd.net/esi/TA?format=json&url=%s'
# Url

URL_LICENSE_FRANCETV = 'https://simulcast-b.ftven.fr/keys/hls.key'
# URL license

URL_DAILYMOTION_EMBED_2 = 'https://www.dailymotion.com/player/metadata/video/%s'

URL_TWITCH = 'https://player.twitch.tv/?channel=%s'

# desired_language, videoid
URL_REPLAY_ARTE = 'https://api.arte.tv/api/player/v2/config/%s/%s'

GENERIC_HEADERS = {'User-Agent': web_utils.get_random_ua()}


def __get_non_ia_stream_with_quality(plugin, url, manifest_type="hls", headers=None, map_audio=False,
                                     append_query_string=False, verify=True, subtitles=None):
    item = Listitem()
    if manifest_type == 'hls':
        stream_bitrate_limit = plugin.setting.get_int('stream_bitrate_limit')
        m3u8 = M3u8(url, headers=headers, map_audio=map_audio, append_query_string=append_query_string, verify=verify)
        if stream_bitrate_limit > 0:
            item.path = m3u8.get_matching_stream(stream_bitrate_limit)
        else:
            url_quality, bitrate = m3u8.get_url_and_bitrate_for_quality()
            if url_quality is None and bitrate is None:
                return False
            item.path = url_quality
        # disabled doesn't work yet
        # item.context.related(add_context_qualities, media_streams=m3u8.media_streams)

    # TODO other manifest types?
    else:
        if headers is not None:
            return url + "|" + urlencode(headers)
        else:
            return url

    item.label = get_selected_item_label()
    item.art.update(get_selected_item_art())
    item.info.update(get_selected_item_info())

    if subtitles is not None:
        item.subtitles.append(subtitles)

    return item


def __set_ia_quality(plugin, video_url, bypass, headers, item, manifest_type, input_stream_properties):
    """
    @param plugin: plugin
    @param video_url: video url
    @param bypass: use IA to read stream with only one resolution
    @param headers: the headers
    @param item: the item on which the quality should be set
    @param manifest_type: manifest type
    @param input_stream_properties: input_stream_properties

    @return: boolean: false when quality is not chosen in dialog box
    """
    if get_kodi_version() < 20:
        stream_bitrate_limit = plugin.setting.get_int('stream_bitrate_limit')
        if stream_bitrate_limit > 0:
            item.property["inputstream.adaptive.max_bandwidth"] = str(stream_bitrate_limit * 1000)
        elif manifest_type == "hls" and Quality['BEST'] != plugin.setting.get_string('quality') and bypass is False:
            url, bitrate = M3u8(video_url, headers).get_url_and_bitrate_for_quality()
            if url is None and bitrate is None:
                return False
            if bitrate != 0:
                item.property["inputstream.adaptive.max_bandwidth"] = str(bitrate * 1000)
    else:
        # see https://github.com/xbmc/inputstream.adaptive/wiki/ \
        # Stream-selection-types-properties#inputstreamadaptivechooser_bandwidth_max
        stream_bitrate_limit = plugin.setting.get_int('stream_bitrate_limit')
        if stream_bitrate_limit > 0:
            item.property['inputstream.adaptive.stream_selection_type'] = 'adaptive'
            item.property['inputstream.adaptive.chooser_bandwidth_max'] = str(stream_bitrate_limit * 1000)
        elif Quality['DIALOG'] == plugin.setting.get_string('quality'):
            item.property['inputstream.adaptive.stream_selection_type'] = 'ask-quality'
        elif Quality['WORST'] == plugin.setting.get_string('quality'):
            item.property['inputstream.adaptive.stream_selection_type'] = 'fixed-res'
            item.property['inputstream.adaptive.chooser_resolution_max'] = '480p'
            item.property['inputstream.adaptive.chooser_resolution_secure_max'] = '480p'

        if input_stream_properties is not None and "chooser_resolution_secure_max" in input_stream_properties:
            item.property['inputstream.adaptive.chooser_resolution_secure_max'] = input_stream_properties[
                "chooser_resolution_secure_max"]

    return True


@Route.register
def add_context_qualities(plugin, media_streams):
    if len(media_streams) > 0:
        streams = media_streams.sort(key=lambda s: s.bitrate)
        for stream in streams:
            item = Listitem()
            item.path = stream.url
            item.label = get_selected_item_label() + " - " + str(stream)
            item.art.update(get_selected_item_art())
            item.info.update(get_selected_item_info())
            yield item


def get_stream_with_quality(plugin,
                            video_url,
                            manifest_type="hls",
                            headers=None,
                            license_url=None,
                            map_audio=False,
                            append_query_string=False,
                            verify=True,
                            subtitles=None,
                            bypass=False,
                            workaround=None,
                            input_stream_properties=None):

    """ Returns the stream for the bitrate or the requested quality.

    :param plugin:                      plugin
    :param str video_url:               The url to download
    :param str manifest_type:           Manifest type
    :param dict headers:                the headers
    :param str license_url:        licence url
    :param bool append_query_string:    Should the existing query string be appended?
    :param bool map_audio:              Map audio streams
    :param bool verify:                 verify ssl?
    :param str subtitles:               subtitles url
    :param bool bypass:                 use IA to read stream with only one resolution
    :param str workaround:     workaround an inpustream adaptive bug for live split in chapters (see IA issue #1066)
    :param dict input_stream_properties:            inputstream properties

    :return: An item for the stream
    :rtype: Listitem

    """
    if (license_url is not None or input_stream_properties is not None) and (get_kodi_version() < 18):
        xbmcgui.Dialog().ok(plugin.localize(30600), plugin.localize(30602))
        return False

    if ((license_url is None and input_stream_properties is None)
            and ((not plugin.setting.get_boolean('use_ia_hls_stream') and manifest_type == "hls")
                 or (get_kodi_version() < 18)
                 or (not inputstreamhelper.Helper(manifest_type).check_inputstream()))):

        if plugin.setting.get_boolean('use_ytdl_stream'):
            return get_stream_default(plugin, video_url, False)

        return __get_non_ia_stream_with_quality(plugin, video_url,
                                                manifest_type=manifest_type,
                                                headers=headers,
                                                map_audio=map_audio,
                                                append_query_string=append_query_string,
                                                verify=verify, subtitles=subtitles)

    is_helper = inputstreamhelper.Helper(manifest_type, drm='widevine')
    if not is_helper.check_inputstream():
        return False

    if headers is None:
        headers = GENERIC_HEADERS
    else:
        headers.update(GENERIC_HEADERS)

    item = Listitem()
    stream_headers = urlencode(headers)
    item.property['inputstream.adaptive.stream_headers'] = stream_headers
    if get_kodi_version() == 20:
        item.property['inputstream.adaptive.manifest_headers'] = stream_headers
    item.path = video_url
    item.property[INPUTSTREAM_PROP] = "inputstream.adaptive"

    if input_stream_properties is not None and "license_type" in input_stream_properties:
        if input_stream_properties["license_type"] is not None:
            item.property['inputstream.adaptive.license_type'] = input_stream_properties["license_type"]
        else:
            pass
    else:
        item.property['inputstream.adaptive.license_type'] = 'com.widevine.alpha'
    if get_kodi_version() < 21:
        # mandatory until Kodi 20, deprecated on Kodi 21
        item.property["inputstream.adaptive.manifest_type"] = manifest_type
    if workaround is not None:
        item.property['ResumeTime'] = '43200'  # 12 hours buffer, can be changed if not enough
        item.property['TotalTime'] = workaround

    is_ok = __set_ia_quality(plugin, video_url, bypass, headers, item, manifest_type, input_stream_properties)
    if not is_ok:
        return False

    if license_url is not None:

        if '|' not in license_url:  # add headers only if they are not already in the url
            license_url = '%s|%s|R{SSM}|' % (license_url, stream_headers)
        item.property['inputstream.adaptive.license_key'] = license_url

    if input_stream_properties is not None:
        if "manifest_update_parameter" in input_stream_properties and get_kodi_version() < 21:
            item.property['inputstream.adaptive.manifest_update_parameter'] = input_stream_properties[
                "manifest_update_parameter"]

        if "server_certificate" in input_stream_properties:
            item.property['inputstream.adaptive.server_certificate'] = input_stream_properties[
                "server_certificate"]

    if subtitles is not None:
        item.subtitles.append(subtitles)

    item.label = get_selected_item_label()
    item.art.update(get_selected_item_art())
    item.info.update(get_selected_item_info())
    return item


def get_stream_default(plugin,
                       video_url,
                       download_mode=False):
    """
    get a stream using youtube-dl
    """
    if download_mode:
        return download.download_video(video_url)

    quality = get_quality_YTDL(download_mode=download_mode)
    return plugin.extract_source(video_url, quality)


# Kaltura Part
def get_stream_kaltura(plugin,
                       video_url,
                       download_mode=False):
    return get_stream_default(plugin, video_url, download_mode)


# DailyMotion Part
def get_stream_dailymotion(plugin,
                           video_id,
                           download_mode=False,
                           embeder=None):

    if download_mode:
        url_dailymotion = URL_DAILYMOTION_EMBED % video_id
        return get_stream_default(plugin, url_dailymotion, download_mode)
    else:
        if embeder is None:
            embeder = ''
        params = {'embedder': embeder}
        url_dmotion = URL_DAILYMOTION_EMBED_2 % video_id
        resp = urlquick.get(url_dmotion, headers=GENERIC_HEADERS, params=params, max_age=-1)
        json_parser = json.loads(resp.text)

        if "qualities" not in json_parser:
            plugin.notify('ERROR', plugin.localize(30716))

        url = json_parser["qualities"]["auto"][0]["url"]
        return get_stream_with_quality(plugin, url)


# Vimeo Part
def get_stream_vimeo(plugin,
                     video_id,
                     download_mode=False,
                     referer=None):
    url_vimeo = URL_VIMEO_BY_ID % video_id

    if referer is not None:
        html_vimeo = urlquick.get(url_vimeo,
                                  headers={
                                      'User-Agent': web_utils.get_random_ua(),
                                      'Referer': referer
                                  },
                                  max_age=-1)
    else:
        html_vimeo = urlquick.get(
            url_vimeo,
            headers={'User-Agent': web_utils.get_random_ua()},
            max_age=-1)
    json_vimeo = json.loads(
        '{' +
        re.compile('var config = \{(.*?)};').findall(html_vimeo.text)[0] +
        '}')
    hls_json = json_vimeo["request"]["files"]["hls"]
    default_cdn = hls_json["default_cdn"]
    final_video_url = hls_json["cdns"][default_cdn]["url"]

    if download_mode:
        return download.download_video(final_video_url)
    return get_stream_with_quality(plugin, video_url=final_video_url)


# Facebook Part
def get_stream_facebook(plugin,
                        video_id,
                        download_mode=False):
    url_facebook = URL_FACEBOOK_BY_ID % video_id
    return get_stream_default(plugin, url_facebook, download_mode)


# YouTube Part
def get_stream_youtube(plugin, video_id, download_mode=False):
    url_youtube = URL_YOUTUBE % video_id
    return get_stream_default(plugin, url_youtube, download_mode)


# BRIGHTCOVE Part
def get_brightcove_policy_key(data_account, data_player):
    """Get policy key"""
    file_js = urlquick.get(URL_BRIGHTCOVE_POLICY_KEY %
                           (data_account, data_player))
    return re.compile(r'policyKey:\"(.*?)\"').findall(file_js.text)[0]


def get_brightcove_video_json(plugin,
                              data_account,
                              data_player,
                              data_video_id,
                              policy_key=None,
                              download_mode=False,
                              subtitles=None):
    if policy_key is None:
        # Method to get JSON from 'edge.api.brightcove.com'
        key = get_brightcove_policy_key(data_account, data_player)
    else:
        key = policy_key

    headers = {
        'User-Agent': web_utils.get_random_ua(),
        'Accept': 'application/json;pk=%s' % key,
        'X-Forwarded-For': plugin.setting.get_string('header_x-forwarded-for')
    }
    resp = urlquick.get(URL_BRIGHTCOVE_VIDEO_JSON % (data_account, data_video_id), headers=headers)

    json_parser = json.loads(resp.text)
    video_url = ''
    license_url = None
    is_drm = False

    manifest = 'hls'
    if 'sources' in json_parser:
        for url in json_parser["sources"]:
            # Workaroud Inputstream adative can not some types of AES crypted streams
            if 'src' in url:
                if ('m3u8' in url["src"] or 'container' in url) and (is_drm is False):
                    manifest = 'hls'
                    video_url = url["src"]
                if 'manifest.mpd' in url["src"]:
                    manifest = 'mpd'
                    video_url = url["src"]
                    is_drm = True
                    if 'key_systems' in url:
                        license_url = url['key_systems']['com.widevine.alpha']['license_url']
    else:
        if json_parser[0]['error_code'] == "ACCESS_DENIED":
            plugin.notify('ERROR', plugin.localize(30713))
            return False

    if video_url == '':
        return False

    if download_mode:
        return download.download_video(video_url)
    return get_stream_with_quality(plugin, video_url=video_url, manifest_type=manifest, headers=headers,
                                   license_url=license_url, subtitles=subtitles)


# MTVN Services Part
def get_mtvnservices_stream(plugin,
                            video_uri,
                            download_mode=False,
                            account_override=None,
                            ep=None):
    if account_override is not None and ep is not None:
        json_video_stream = urlquick.get(URL_MTVNSERVICES_STREAM_ACCOUNT_EP %
                                         (video_uri, account_override, ep),
                                         max_age=-1)
    elif account_override is not None:
        json_video_stream = urlquick.get(URL_MTVNSERVICES_STREAM_ACCOUNT %
                                         (video_uri, account_override),
                                         max_age=-1)
    else:
        json_video_stream = urlquick.get(URL_MTVNSERVICES_STREAM % video_uri,
                                         max_age=-1)

    json_video_stream_parser = json.loads(json_video_stream.text)
    if 'rendition' not in json_video_stream_parser["package"]["video"]["item"][0]:
        plugin.notify('ERROR', plugin.localize(30716))
        return False

    video_url = json_video_stream_parser["package"]["video"]["item"][0][
        "rendition"][0]["src"]
    if download_mode:
        return download.download_video(video_url)
    return video_url


def __get_francetv_program_info(video_id):
    # Move Live TV on the new API
    geoip_value = web_utils.geoip()
    if not geoip_value:
        geoip_value = 'FR'
    params = {
        'country_code': geoip_value,
        'browser': 'firefox',
        'device_type': 'mobile'
    }
    resp = urlquick.get(URL_FRANCETV_PROGRAM_INFO % video_id, params=params, headers=GENERIC_HEADERS, max_age=-1)
    json_parser_live_id = json.loads(resp.text)
    return json_parser_live_id


# FranceTV Part
# FranceTV, FranceTV Sport, France Info, ...
def get_francetv_video_stream(plugin,
                              id_diffusion,
                              download_mode=False):

    json_parser = __get_francetv_program_info(id_diffusion)

    if 'video' not in json_parser:
        plugin.notify('ERROR', plugin.localize(30716))
        return False

    all_video_datas = []
    video_datas = json_parser['video']
    # Implementer Caption (found case)
    # Implement DRM (found case)
    if video_datas['drm'] is not None:
        all_video_datas.append((video_datas['format'], video_datas['drm'], video_datas['token']))
    else:
        all_video_datas.append((video_datas['format'], None, video_datas['token']))

    url_selected = all_video_datas[0][2]
    if 'hls' in all_video_datas[0][0]:
        json_parser2 = json.loads(
            urlquick.get(url_selected, max_age=-1).text)
        final_video_url = json_parser2['url']
        if download_mode:
            return download.download_video(final_video_url)
        return final_video_url + '|X-Forwarded-For=' + '2.' + str(randint(0, 15)) + '.' + str(
            randint(0, 255)) + '.' + str(randint(0, 255)) + '&User-Agent=' + web_utils.get_random_ua()

    if 'dash' in all_video_datas[0][0]:

        is_helper = inputstreamhelper.Helper('mpd')
        if not is_helper.check_inputstream():
            return False

        item = Listitem()
        item.property[INPUTSTREAM_PROP] = 'inputstream.adaptive'
        item.property['inputstream.adaptive.manifest_type'] = 'mpd'
        item.label = get_selected_item_label()
        item.art.update(get_selected_item_art())
        item.info.update(get_selected_item_info())

        if all_video_datas[0][1]:
            if download_mode:
                xbmcgui.Dialog().ok(plugin.localize(14116), plugin.localize(30603))
                return False
            item.path = video_datas['url']
            token_request = json.loads('{"id": "%s", "drm_type": "%s", "license_type": "%s"}'
                                       % (id_diffusion, video_datas['drm_type'], video_datas['license_type']))
            token = urlquick.post(video_datas['token'], json=token_request).json()['token']
            license_request = '{"token": "%s", "drm_info": [D{SSM}]}' % token
            license_key = 'https://widevine-proxy.drm.technology/proxy|Content-Type=application%%2Fjson|%s|' \
                          % quote_plus(license_request)
            item.property['inputstream.adaptive.license_type'] = 'com.widevine.alpha'
            item.property['inputstream.adaptive.license_key'] = license_key
        else:
            headers = {
                'User-Agent': web_utils.get_random_ua(),
                # 2.0.0.0 -> 2.16.0.255 are french IP addresses, see https://lite.ip2location.com/france-ip-address-ranges
                # 'X-Forwarded-For': '2.' + str(randint(0, 15)) + '.' + str(randint(0, 255)) + '.' + str(randint(0, 255)),
            }
            stream_headers = urlencode(headers)
            json_parser2 = json.loads(urlquick.get(url_selected, headers=headers, max_age=-1).text)
            resp3 = urlquick.get(json_parser2['url'], headers=headers, max_age=-1, allow_redirects=False)
            if 400 > resp3.status_code >= 300:
                location_url = resp3.headers['location']
            else:
                location_url = resp3.url
            item.path = location_url
            if get_kodi_version() == 20:
                item.property['inputstream.adaptive.manifest_headers'] = stream_headers
            else:
                item.property['inputstream.adaptive.stream_headers'] = stream_headers
            if download_mode:
                return download.download_video(item.path)
        return item

    # Return info the format is not known
    return False


def get_francetv_live_stream(plugin, broadcast_id):

    json_parser_live_id = __get_francetv_program_info(broadcast_id)
    final_url = json_parser_live_id['video']['token']

    resp = urlquick.get(final_url, max_age=-1)
    video_url = json.loads(resp.text)['url']
    return get_stream_with_quality(plugin, video_url, license_url=URL_LICENSE_FRANCETV)


# Arte Part
def get_arte_video_stream(plugin,
                          desired_language,
                          video_id,
                          download_mode=False):
    url = URL_REPLAY_ARTE % (desired_language, video_id)
    j = urlquick.get(url).json()

    language = []
    for stream in j['data']['attributes']['streams']:
        language.append(stream['versions'][0]['label'])
    choose_language = xbmcgui.Dialog().select(Script.localize(30181), language)

    video_url = j['data']['attributes']['streams'][choose_language]['url']

    if download_mode:
        return download.download_video(video_url)

    return get_stream_with_quality(plugin, video_url)


# Twitch Part
def get_stream_twitch(plugin, video_id, download_mode=False):
    url_twitch = URL_TWITCH % video_id
    return get_stream_default(plugin, url_twitch, download_mode)
