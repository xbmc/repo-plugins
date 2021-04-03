# -*- coding: utf-8 -*-
# Copyright: (c) 2017, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
import base64
import json
import re
import string
import xml.etree.ElementTree as ET

from codequick import Listitem, Resolver, Route, utils
import htmlement
import urlquick

from resources.lib import download
from resources.lib.menu_utils import item_post_treatment

# TO DO
# Add Premium Account (purchase an account to test)
# Add last videos
# Fix Info add Premium Content

URL_ROOT = 'http://www.ina.fr'

URL_STREAM = 'https://player.ina.fr/notices/%s'
# VideoId


@Route.register
def website_root(plugin, **kwargs):
    """Build root listing"""
    categories = [
        ('Thèmes', list_subcategories, 'themes', ''),
        ('Toutes les Personnalités', list_alpha, '184', 'classic'),
        ('Toutes les Émissions', list_alpha, '196', 'classic'),
        ('Toutes les Séries', list_alpha, '196', 'series'),
        ('Dossiers', list_subcategories, 'dossiers', '')
    ]

    for category in categories:
        item = Listitem()
        item.label = category[0]
        item.set_callback(category[1], category[2], category[3])
        item_post_treatment(item)
        yield item

    # Search videos
    item = Listitem.search(list_types, URL_ROOT)
    item_post_treatment(item)
    yield item


@Route.register
def list_subcategories(plugin, subcategory, **kwargs):
    """Build subcateory listing"""
    ina_html = urlquick.get(URL_ROOT).text.encode('utf-8')
    ina = htmlement.fromstring(ina_html)
    if subcategory == 'themes':
        ina = ina.find('.//div[@class="menusThemes"]')
        for sub in ina.iterfind('.//a'):
            url = sub.get('href')
            label = sub.text.encode('utf-8')
            if url[-1] != '/' or label == 'Voir tout':
                continue
            item = Listitem()
            item.label = label
            item.set_callback(list_subsubcategories, url=URL_ROOT + url)
            yield item
    elif subcategory == 'dossiers':
        ina = ina.find('.//div[@class="secondary-nav__dossiers"]')
        for sub in ina.iterfind('.//a'):
            url = sub.get('href')
            label = sub.text.encode('utf-8')
            if url.count('/') != 3 or url[-1] != '/' or label == 'Voir tout':
                continue
            item = Listitem()
            item.label = label
            item.set_callback(list_types, url=URL_ROOT + url)
            yield item


@Route.register
def list_alpha(plugin, js_file, mode, **kwargs):
    """Build alpha listing choice (A, B, C, ..."""
    range_l = [
        ('Toutes', 'Toutes'),
        ('#', '')
    ]
    for letter in list(string.ascii_uppercase):
        range_l.append((letter, letter))

    for range_elt in range_l:
        item = Listitem()
        item.label = range_elt[0]
        item.set_callback(
            list_alpha2,
            js_file=js_file,
            mode=mode,
            range_elt=range_elt[1])
        yield item


@Route.register
def list_alpha2(plugin, js_file, mode, range_elt, page=1, **kwargs):
    """Build categories listing after range choice"""
    params_l = [
        'order=asc',
        'page=' + str(page),
        'nbResults=48',
        'mode=' + mode,
        'range=' + range_elt
    ]

    url = URL_ROOT + '/blocs/rubrique_sommaire/' + js_file \
        + '?' + '&'.join(params_l)

    list_categories_text = urlquick.get(url).text.encode('utf-8')
    list_categories_json = json.loads(list_categories_text)
    categories = htmlement.fromstring(list_categories_json["html"])
    cnt = 0
    for categroy in categories.iterfind(".//div[@class='media']"):
        cnt = cnt + 1
        item = Listitem()
        item.label = categroy.find('.//img').get('alt')
        item.art['thumb'] = item.art['landscape'] = URL_ROOT + \
            categroy.find('.//img').get('src')
        url = URL_ROOT + categroy.find('.//a').get('href')

        item.set_callback(list_types,
                          url=url)
        item_post_treatment(item)
        yield item

    if cnt == 48:
        # More categories...
        yield Listitem.next_page(
            js_file=js_file,
            mode=mode,
            range_elt=range_elt,
            page=page + 1)
    elif cnt == 0:
        plugin.notify(plugin.localize(30718), '')
        yield False


@Route.register
def list_subsubcategories(plugin, url, **kwargs):
    """Build subsubcategories listing"""
    sub_html = urlquick.get(url).text.encode('utf-8')
    sub = htmlement.fromstring(sub_html)
    sub = sub.find('.//section[@id="stackSousThemes"]')
    for fig in sub.iterfind('.//figure'):
        item = Listitem()
        img = fig.find('.//img')
        item.label = img.get('alt')
        item.art['thumb'] = item.art['landscape'] = URL_ROOT + img.get('src')
        url = fig.find('.//a').get('href')
        item.set_callback(list_types, url=URL_ROOT + url)
        yield item


@Route.register
def list_types(plugin, url, search_query='', **kwargs):
    """Build listing to choose contents type"""
    # type=
    content_types = [
        ('Vidéos', 'video'),
        ('Audios', 'audio'),
        ('Pubs', 'pub')
        # ('Dossiers', 'dossier')
        # ('Créations Web', 'creationWeb')
    ]
    for content_type in content_types:
        item = Listitem()
        item.label = content_type[0]
        item.set_callback(
            list_sort,
            url=url,
            content_type=content_type[1],
            search_query=search_query)
        item_post_treatment(item)
        yield item


@Route.register
def list_sort(plugin, url, content_type, search_query, **kwargs):
    """Build listing to choose sort method"""
    # s=
    # sa=
    sort_methods = [
        ('Trier par : Pertinence', 'pertinence', 'desc'),
        ('Trier par : Nombre de vues croissant', 'compteur_vue', 'asc'),
        ('Trier par : Nombre de vues décroissant', 'compteur_vue', 'desc'),
        ('Trier par : Date croissante', 'date_diffusion', 'asc'),
        ('Trier par : Date décroissante', 'date_diffusion', 'desc'),
        ('Trier par : Durée croissante', 'duree_totale', 'asc'),
        ('Trier par : Durée décroissante', 'duree_totale', 'desc')
    ]
    for sort_method in sort_methods:
        item = Listitem()
        item.label = sort_method[0]
        item.set_callback(
            list_videos,
            url=url,
            content_type=content_type,
            sort_method=sort_method[1],
            sort_method_order=sort_method[2],
            search_query=search_query)
        item_post_treatment(item)
        yield item


@Route.register
def list_videos(plugin, url, content_type, sort_method,
                sort_method_order, search_query, start=0, **kwargs):
    """Build videos listing"""
    videos_html = urlquick.get(url).text
    query = ''
    must = ''
    madelen_page = False
    if search_query == '':
        if 'executeQuery' in videos_html:
            query = re.compile(r'OGP\.Search\.executeQuery(.*?);').findall(videos_html)[0]
            if 'must' in query:
                must = re.compile(r'must=(.*?)&').findall(query)[0]
        else:
            madelen_page = True

    if madelen_page:
        plugin.notify(plugin.localize(30712), '')
        yield False
    else:
        query_l = [
            'b=' + str(start),
            'type=' + content_type,
            'q=' + search_query,
            's=' + sort_method,
            'sa=' + sort_method_order,
            'hf=48',
            'must=' + must,
            'block=true',
            'target=www',
            'resetParams=false'
        ]

        query_s = '%'.join(query_l)

        videos_url = URL_ROOT + '/layout/set/ajax/recherche/result?' + base64.b64encode(query_s)
        videos_html = urlquick.get(videos_url).text.encode('utf-8')
        videos_html = videos_html.decode('unicode_escape')
        videos_html = videos_html.replace('\\/', '/')
        videos = htmlement.fromstring(videos_html)
        cnt = 0
        for episode in videos.iterfind(
                ".//div[@class='media zoomarticle afficheNotices']"):
            cnt = cnt + 1
            item = Listitem()
            item.label = 'No title'
            if episode.find(".//div[@class='media-inapremium-slide']") is not None:
                item.label = '[Ina Premium] ' + episode.find('.//img').get('alt')
            else:
                item.label = episode.find('.//img').get('alt')
            try:
                video_id = episode.find('.//a').get('href').split('/')[2]
            except Exception:
                continue
            item.art['thumb'] = item.art['landscape'] = URL_ROOT + episode.find('.//img').get('src')
            try:
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
            except Exception:
                pass

            if episode.find(".//span[@class='broadcast']") is not None:
                video_date = episode.find(".//span[@class='broadcast']").text
                item.info.date(video_date, '%d/%m/%Y')

            item.set_callback(get_video_url,
                              video_id=video_id)
            item_post_treatment(item, is_playable=True, is_downloadable=True)
            yield item

        if cnt == 48:
            # More videos...
            yield Listitem.next_page(
                url=url,
                content_type=content_type,
                sort_method=sort_method,
                sort_method_order=sort_method_order,
                start=start + 48)
        elif cnt == 0:
            plugin.notify(plugin.localize(30718), '')
            yield False


@Resolver.register
def get_video_url(plugin,
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
