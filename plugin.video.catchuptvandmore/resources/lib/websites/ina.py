# -*- coding: utf-8 -*-
'''
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
'''
# The unicode_literals import only has
# an effect on Python 2.
# It makes string literals as unicode like in Python 3
from __future__ import unicode_literals

from resources.lib.codequick import Route, Resolver, Listitem, utils

from resources.lib import download
from resources.lib.labels import LABELS
from resources.lib.menu_utils import item_post_treatment

import htmlement
import json
import re
from resources.lib import urlquick
import xml.etree.ElementTree as ET

# TO DO
# Add Premium Account (purchase an account to test)
# Add last videos
# Fix Info add Premium Content

URL_ROOT = 'http://www.ina.fr'

URL_PROGRAMS = URL_ROOT + '/blocs/rubrique_sommaire/196?order=asc&page=%s&nbResults=48&mode=%s&range=Toutes'
# Page, Mode

URL_VIDEOS = URL_ROOT + '/layout/set/ajax/recherche/result?q=%s&autopromote=0&typeBlock=ina_resultat_exalead&s=date_diffusion&sa=0&b=%s&type=Video&r=&hf=48&c=ina_emission'
# Name Program, Nb Video (+ 48)

URL_VIDEOS_SEARCH = URL_ROOT + '/layout/set/ajax/recherche/result?q=%s&autopromote=&b=%s&type=Video&r=&hf=48'
# Query, Nb Video (+ 48)

URL_STREAM = 'https://player.ina.fr/notices/%s'
# VideoId


def website_entry(plugin, item_id, **kwargs):
    """
    First executed function after website_bridge
    """
    return root(plugin, item_id)


CATEGORIES = {'Toutes les Emissions': 'classic', 'Toutes les séries': 'serie'}


def root(plugin, item_id, **kwargs):
    """Add modes in the listing"""
    for category_name, category_mode in list(CATEGORIES.items()):
        item = Listitem()

        item.label = category_name
        item.set_callback(list_shows,
                          item_id=item_id,
                          category_mode=category_mode,
                          page=1)
        item_post_treatment(item)
        yield item

    # Search videos
    item = Listitem.search(list_videos_search, item_id=item_id, nb_videos=0)
    item_post_treatment(item)
    yield item


@Route.register
def list_shows(plugin, item_id, category_mode, page, **kwargs):
    """Build categories listing"""
    list_programs_json = urlquick.get(URL_PROGRAMS % (page, category_mode))
    list_programs_jsonparser = json.loads(list_programs_json.text)
    parser = htmlement.HTMLement()
    parser.feed(list_programs_jsonparser["html"])
    root = parser.close()

    for program_datas in root.iterfind(".//div[@class='media']"):
        item = Listitem()
        item.label = program_datas.find('.//img').get('alt')
        item.art['thumb'] = item.art['landscape'] = URL_ROOT + program_datas.find('.//img').get('src')
        program_url = URL_ROOT + program_datas.find('.//a').get('href')

        item.set_callback(list_videos,
                          item_id=item_id,
                          program_url=program_url,
                          nb_videos=0)
        item_post_treatment(item)
        yield item

    # More programs...
    yield Listitem.next_page(item_id=item_id,
                             category_mode=category_mode,
                             page=page + 1)


@Route.register
def list_videos(plugin, item_id, program_url, nb_videos, **kwargs):
    """Build videos listing"""
    replay_episodes_html = urlquick.get(program_url).text
    program_title = re.compile(r'&q=(.*?)&auto').findall(
        replay_episodes_html)[0]
    replay_episodes_json = urlquick.get(URL_VIDEOS %
                                        (program_title, nb_videos)).text
    list_episodes_jsonparser = json.loads(replay_episodes_json)
    parser = htmlement.HTMLement()
    parser.feed(list_episodes_jsonparser["content"])
    root = parser.close()
    at_least_one_item = False
    for episode in root.iterfind(
            ".//div[@class='media zoomarticle afficheNotices']"):
        at_least_one_item = True
        item = Listitem()
        item.label = 'No title'
        if episode.find(".//div[@class='media-inapremium-slide']") is not None:
            item.label = '[Ina Premium] ' + episode.find('.//img').get('alt')
        else:
            item.label = episode.find('.//img').get('alt')
        video_id = episode.find('.//a').get('href').split('/')[2]
        item.art['thumb'] = item.art['landscape'] = URL_ROOT + episode.find('.//img').get('src')
        video_duration_text_datas = episode.find(
            ".//span[@class='duration']").text.split(' ')
        video_duration = 0
        for video_duration_datas in video_duration_text_datas:
            if 's' in video_duration_datas:
                video_duration_datas = video_duration_datas.replace('s', '')
                video_duration = video_duration + int(video_duration_datas)
            elif 'm' in video_duration_datas:
                video_duration_datas = video_duration_datas.replace('m', '')
                video_duration = video_duration + (int(video_duration_datas) *
                                                   60)
            elif 'h' in video_duration_datas:
                video_duration_datas = video_duration_datas.replace('h', '')
                video_duration = video_duration + (int(video_duration_datas) *
                                                   3600)
        item.info['duration'] = video_duration

        if episode.find(".//span[@class='broadcast']") is not None:
            video_date = episode.find(".//span[@class='broadcast']").text
            item.info.date(video_date, '%d/%m/%Y')

        item.set_callback(get_video_url,
                          item_id=item_id,
                          video_id=video_id)
        item_post_treatment(item, is_playable=True, is_downloadable=True)
        yield item

    if at_least_one_item:
        # More videos...
        yield Listitem.next_page(item_id=item_id,
                                 program_url=program_url,
                                 nb_videos=nb_videos + 48)
    else:
        plugin.notify(plugin.localize(LABELS['No videos found']), '')
        yield False


@Route.register
def list_videos_search(plugin, item_id, nb_videos, search_query, **kwargs):
    replay_episodes_json = urlquick.get(URL_VIDEOS_SEARCH %
                                        (search_query, nb_videos)).text
    list_episodes_jsonparser = json.loads(replay_episodes_json)
    parser = htmlement.HTMLement()
    parser.feed(list_episodes_jsonparser["content"])
    root = parser.close()

    for episode in root.iterfind(".//div[@class='media zoomarticle']"):
        item = Listitem()
        item.label = 'No title'
        if episode.find(
                ".//div[@class='media-inapremium-search']") is not None:
            item.label = '[Ina Premium] ' + episode.find('.//img').get('alt')
        else:
            item.label = episode.find('.//img').get('alt')
        video_id = episode.find('.//a').get('href').split('/')[2]
        item.art['thumb'] = item.art['landscape'] = URL_ROOT + episode.find('.//img').get('src')
        video_duration_text_datas = episode.find(
            ".//span[@class='duration']").text.split(' ')
        video_duration = 0
        for video_duration_datas in video_duration_text_datas:
            if 's' in video_duration_datas:
                video_duration_datas = video_duration_datas.replace('s', '')
                video_duration = video_duration + int(video_duration_datas)
            elif 'm' in video_duration_datas:
                video_duration_datas = video_duration_datas.replace('m', '')
                video_duration = video_duration + (int(video_duration_datas) *
                                                   60)
            elif 'h' in video_duration_datas:
                video_duration_datas = video_duration_datas.replace('h', '')
                video_duration = video_duration + (int(video_duration_datas) *
                                                   3600)
        item.info['duration'] = video_duration

        if episode.find(".//span[@class='broadcast']") is not None:
            video_date = episode.find(".//span[@class='broadcast']").text
            item.info.date(video_date, '%d/%m/%Y')

        item.set_callback(get_video_url,
                          item_id=item_id,
                          video_id=video_id)
        item_post_treatment(item, is_playable=True, is_downloadable=True)
        yield item

    # More videos...
    yield Listitem.next_page(item_id=item_id,
                             nb_videos=nb_videos + 48,
                             search_query=search_query)


@Resolver.register
def get_video_url(plugin,
                  item_id,
                  video_id,
                  download_mode=False,
                  **kwargs):
    """Get video URL and start video player"""
    stream_xml = urlquick.get(URL_STREAM % video_id).text
    stream_xml = utils.ensure_native_str(stream_xml)
    stream_url = ''
    xml_elements = ET.XML(stream_xml)
    for item in xml_elements.findall('./channel/item'):
        for child in item:
            if child.tag == '{http://search.yahoo.com/mrss/}content':
                stream_url = child.attrib['url']

    if download_mode:
        return download.download_video(stream_url)

    return stream_url
