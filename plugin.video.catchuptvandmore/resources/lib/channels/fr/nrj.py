# -*- coding: utf-8 -*-
"""
    Catch-up TV & More
    Copyright (C) 2017  SylvainCecchetto

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

from bs4 import BeautifulSoup as bs

import json
import re
import requests
import urlquick


# TO DO
# Fix Live TV


URL_ROOT = 'http://www.nrj-play.fr'

URL_REPLAY = URL_ROOT + '/%s/replay'
# channel_name (nrj12, ...)

URL_COMPTE_LOGIN = URL_ROOT + '/compte/login'
# TO DO add account for using Live Direct

URL_LIVE_WITH_TOKEN = URL_ROOT + '/compte/live?channel=%s'
# channel (nrj12, ...) -
# call this url after get session (url live with token inside this page)


def replay_entry(plugin, item_id):
    """
    First executed function after replay_bridge
    """
    return list_categories(plugin, item_id)


@Route.register
def list_categories(plugin, item_id):
    """
    Build categories listing
    - Tous les programmes
    - Séries
    - Informations
    - ...
    """
    resp = urlquick.get(URL_REPLAY % item_id)
    root_soup = bs(resp.text, 'html.parser')
    list_categories_datas = root_soup.find(
        'ul', class_='subNav-menu hidden-xs').find_all('a')
    for category_datas in list_categories_datas:
        category_title = category_datas.get_text().strip()
        category_url = URL_ROOT + category_datas.get('href')

        item = Listitem()
        item.label = category_title
        item.set_callback(
            list_programs,
            item_id=item_id,
            category_url=category_url)
        yield item


@Route.register
def list_programs(plugin, item_id, category_url):
    """
    Build programs listing
    - Les feux de l'amour
    - ...
    """
    resp = urlquick.get(category_url)
    root_soup = bs(resp.text, 'html.parser')
    list_programs_datas = root_soup.find_all(
        'div', class_='linkProgram-visual')
    for program_datas in list_programs_datas:

        program_title = program_datas.find(
            'img').get('alt')
        program_url = URL_ROOT + program_datas.find(
            'a').get('href')
        program_image = ''
        if program_datas.find('source').get('data-srcset'):
            program_image = program_datas.find('source').get('data-srcset')
        else:
            program_image = program_datas.find('source').get('srcset')

        item = Listitem()
        item.label = program_title
        item.art['thumb'] = program_image
        item.set_callback(
            list_videos,
            item_id=item_id,
            program_title=program_title,
            program_url=program_url)
        yield item


@Route.register
def list_videos(plugin, item_id, program_title, program_url):

    resp = urlquick.get(program_url)
    root_soup = bs(resp.text, 'html.parser')
    list_videos_datas = root_soup.find_all(
        'figure', class_='thumbnailReplay-visual')

    if len(list_videos_datas) > 0:
        for video_datas in list_videos_datas:
            video_title = program_title + ' - ' + video_datas.find(
                'img').get('alt')
            video_url = URL_ROOT + video_datas.find('a').get('href')
            video_image = ''
            if video_datas.find('source').get('data-srcset'):
                video_image = video_datas.find('source').get('data-srcset')
            else:
                video_image = video_datas.find('source').get('srcset')

            item = Listitem()
            item.label = video_title
            item.art['thumb'] = video_image

            item.context.script(
                get_video_url,
                plugin.localize(LABELS['Download']),
                item_id=item_id,
                video_url=video_url,
                video_label=LABELS[item_id] + ' - ' + item.label,
                download_mode=True)

            item.set_callback(
                get_video_url,
                item_id=item_id,
                video_url=video_url)
            yield item
    else:
        video_title = root_soup.find(
            'div', class_='nrjVideo-player').find('meta').get('alt')
        video_url = program_url
        video_image = root_soup.find(
            'div', class_='nrjVideo-player').find('meta').get('content')

        item = Listitem()
        item.label = video_title
        item.art['thumb'] = video_image

        item.context.script(
            get_video_url,
            plugin.localize(LABELS['Download']),
            item_id=item_id,
            video_url=video_url,
            video_label=LABELS[item_id] + ' - ' + item.label,
            download_mode=True)

        item.set_callback(
            get_video_url,
            item_id=item_id,
            video_url=video_url)
        yield item


@Resolver.register
def get_video_url(
        plugin, item_id, video_url, download_mode=False, video_label=None):
    # Just One format of each video (no need of QUALITY)
    resp = urlquick.get(video_url)
    root_soup = bs(resp.text, 'html.parser')
    stream_datas = root_soup.find(
        'div', class_='nrjVideo-player').find_all('meta')
    stream_url = ''
    for stream in stream_datas:
        if 'mp4' in stream.get('content'):
            stream_url = stream.get('content')

    if download_mode:
        return download.download_video(stream_url, video_label)
    return stream_url


def live_entry(plugin, item_id, item_dict):
    return get_live_url(plugin, item_id, item_id.upper(), item_dict)


@Resolver.register
def get_live_url(plugin, item_id, video_id, item_dict):

    # Live TV Not working / find a way to dump html received

    # Create session
    # KO - session_urlquick = urlquick.Session()
    session_requests = requests.session()

    # Get Token
    # KO - resp = session_urlquick.get(URL_COMPTE_LOGIN)
    resp = session_requests.get(URL_COMPTE_LOGIN)
    token_form_login = re.compile(
        r'name=\"login_form\[_token\]\" value=\"(.*?)\"'
        ).findall(resp.text)[0]

    # Build PAYLOAD
    payload = {
        "login_form[email]": plugin.setting.get_string(
            'nrj.login'),
        "login_form[password]": plugin.setting.get_string(
            'nrj.password'),
        "login_form[_token]": token_form_login
    }

    # LOGIN
    # KO - resp2 = session_urlquick.post(
    #     URL_COMPTE_LOGIN, data=payload,
    #     headers={'User-Agent': web_utils.get_ua, 'referer': URL_COMPTE_LOGIN})
    resp2 = session_requests.post(
        URL_COMPTE_LOGIN, data=payload, headers=dict(referer=URL_COMPTE_LOGIN))
    if 'Une erreur est survenue' in repr(resp2.text):
        plugin.notify('ERROR', 'NRJ : ' + plugin.localize(30711))
        return False

    # GET page with url_live with the session logged
    # KO - resp3 = session_urlquick.get(
    #     URL_LIVE_WITH_TOKEN % item_id,
    #     headers={'User-Agent': web_utils.get_ua, 'referer': URL_LIVE_WITH_TOKEN % item_id})
    resp3 = session_requests.get(
        URL_LIVE_WITH_TOKEN % (item_id),
        headers=dict(
            referer=URL_LIVE_WITH_TOKEN % (item_id)))

    root_soup = bs(resp3.text, 'html.parser')
    live_data = root_soup.find('div', class_="player")

    url_live_json = live_data.get('data-options')
    url_live_json_jsonparser = json.loads(url_live_json)
    return url_live_json_jsonparser["file"]
