# -*- coding: utf-8 -*-
# Copyright: (c) 2017, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
import json
import re

import inputstreamhelper
from codequick import Listitem, Resolver, Route
import urlquick

from resources.lib import web_utils
from resources.lib.kodi_utils import get_selected_item_art, get_selected_item_label, get_selected_item_info, INPUTSTREAM_PROP
from resources.lib.menu_utils import item_post_treatment


URL_REPLAY_SERVICE = 'https://platform-api.tver.jp/v2/api/platform_users/browser/create'

URL_REPLAY_PROGRAM = 'https://platform-api.tver.jp/service/api/v1/callSearch?platform_uid={}&platform_token={}'

URL_VIDEOS_REPLAY = 'https://statics.tver.jp/content/{}/{}.json?v=v2.0.0'

URL_VIDEO_PICTURE = 'https://statics.tver.jp/images/content/thumbnail/{}/small/{}.jpg'

URL_BRIGHTCOVE_POLICY_KEY = 'http://players.brightcove.net/%s/%s_default/index.min.js'
# AccountId, PlayerId

URL_BRIGHTCOVE_VIDEO_JSON = 'https://edge.api.brightcove.com/playback/v1/accounts/%s/videos/%s%s'
# AccountId, VideoId

BROADCASTER = {
    'abc': ['ABCテレビ'],
    'cx': ['フジテレビ', 'テレビ愛媛', 'テレビ宮崎', 'さんいん中央テレビ', 'BSフジ', '北海道文化放送', '仙台放送', '福井テレビ', 'テレビ西日本', '東海テレビ', 'STSサガテレビ', '沖縄テレビ', 'テレビ熊本', 'OHK 岡山放送', 'テレビ静岡'],
    'ex': ['テレビ朝日', 'KBCテレビ', 'BS朝日', 'KAB熊本朝日放送', '静岡朝日テレビ'],
    'ktv': ['カンテレ'],
    'mbs': ['MBS毎日放送'],
    'nhk': ['NHK', 'NHK総合・東京', 'NHK Eテレ・東京'],
    'ntv': ['日テレ', '山梨放送', 'BS日テレ', 'KKTくまもと県民テレビ', '日本海テレビ', 'TeNY', 'tvk', 'Daiichi-TV', '中京テレビ', 'FBS福岡放送', 'テレ玉', 'テレビ信州', '高知放送', '長崎国際テレビ', 'STV札幌テレビ放送', '福島中央テレビ', 'TOKYO MX', 'チバテレ', '広島テレビオンデマンド', 'RAB青森放送', '鹿児島読売テレビ', 'BS11', '南海放送', '福井放送'],
    'tbs': ['TBS', 'TUYテレビユー山形', 'CBCテレビ', 'RKK熊本放送', 'HBC北海道放送', 'BS-TBS', 'MRO', 'RCCテレビ', 'BSN', 'TUFテレビユー福島', 'SBC信越放送', 'RKB毎日放送'],
    'tver': ['TVER'],
    'tvo': ['テレビ大阪'],
    'tx': ['テレビ東京', 'TVh', 'ＢＳテレ東', 'ＢＳテレ東 ほか', 'TVQ九州放送'],
    'ytv': ['読売テレ']
}


@Route.register
def list_categories(plugin, item_id, **kwargs):

    resp = urlquick.post(URL_REPLAY_SERVICE, data={'device_type': 'pc'})
    data = resp.json()
    uid = data['result']['platform_uid']
    token = data['result']['platform_token']
    resp = urlquick.get(URL_REPLAY_PROGRAM.format(uid, token), headers={'x-tver-platform-type': 'web'})
    programs = resp.json()

    list_program = []
    for program in programs['result']['contents']:
        if program['content']['broadcasterName'] in BROADCASTER[item_id]:
            program_title = program['content']['seriesTitle']
            if program_title not in list_program:
                list_program.append(program_title)
                item = Listitem()
                item.label = program_title
                item.set_callback(list_episodes, item_id, program_title, programs)
                item_post_treatment(item)
                yield item


@Route.register
def list_episodes(plugin, item_id, program_title, programs, **kwargs):
    for program in programs['result']['contents']:
        if program_title == program['content']['seriesTitle'] and program['content']['broadcasterName'] in BROADCASTER[item_id]:
            item = Listitem()
            item.label = '{} ({})'.format(program['content']['title'], program['content']['broadcastDateLabel'])
            video_id = program['content']['id']
            video_type = program['type']
            item.art['thumb'] = item.art['landscape'] = URL_VIDEO_PICTURE.format(video_type, video_id)
            resp = urlquick.get(URL_VIDEOS_REPLAY.format(video_type, video_id),
                                headers={'User-Agent': web_utils.get_random_ua()},
                                max_age=-1)
            data = resp.json()
            item.info['plot'] = data['description']
            item.set_callback(get_video_url, data)
            item_post_treatment(item)
            yield item


@Resolver.register
def get_video_url(plugin, data, **kwargs):

    is_helper = inputstreamhelper.Helper('mpd', drm='widevine')
    if not is_helper.check_inputstream():
        return False

    if 'videoID' in data['video']:
        data_video = data['video']['videoID']
        ref = ''
    else:
        data_video = data['video']['videoRefID']
        ref = 'ref:'
    data_account = data['video']['accountID']
    data_player = data['video']['playerID']

    # Method to get JSON from 'edge.api.brightcove.com'
    file_js = urlquick.get(URL_BRIGHTCOVE_POLICY_KEY % (data_account, data_player))
    policy = re.compile('policyKey:"(.+?)"').findall(file_js.text)[0]
    headers = {
        'User-Agent': web_utils.get_random_ua(),
        'Accept': 'application/json;pk=%s' % policy
    }
    URL_JSON_VIDEO = URL_BRIGHTCOVE_VIDEO_JSON % (data_account, ref, data_video)
    json_parser = urlquick.get(URL_JSON_VIDEO, headers=headers).json()

    video_url = ''
    if 'sources' in json_parser:
        for url in json_parser["sources"]:
            if 'src' in url:
                if 'manifest.mpd' in url["src"]:
                    video_url = url["src"]
    else:
        if json_parser[0]['error_code'] == "ACCESS_DENIED":
            plugin.notify('ERROR', plugin.localize(30713))
            return False

    if video_url == '':
        return False

    item = Listitem()
    item.path = video_url
    item.label = get_selected_item_label()
    item.art.update(get_selected_item_art())
    item.info.update(get_selected_item_info())
    item.property[INPUTSTREAM_PROP] = 'inputstream.adaptive'
    item.property['inputstream.adaptive.manifest_type'] = 'mpd'
    return item
