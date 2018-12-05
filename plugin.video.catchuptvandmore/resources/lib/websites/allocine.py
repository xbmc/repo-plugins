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

import json
import re
import requests

from codequick import Route, Resolver, Listitem, Script
import urlquick
import xbmcgui
from bs4 import BeautifulSoup as bs

from resources.lib import resolver_proxy
from resources.lib import download
from resources.lib.labels import LABELS

# TO DO
# Get Last_Page (for Programs, Videos) / Fix Last_page
# Get Partner Id ?
# Todo get Aired, Year, Date of the Video
# News Videos - Need work

URL_ROOT = 'http://www.allocine.fr'

URL_API_MEDIA = 'http://api.allocine.fr/rest/v3/' \
                'media?code=%s&partner=%s&format=json'
# videoId, PARTENER
PARTNER = 'YW5kcm9pZC12Mg'

URL_SEARCH_VIDEOS = URL_ROOT + '/recherche/18/?p=%s&q=%s'
# Page, Query


def website_entry(plugin, item_id):
    """
    First executed function after website_bridge
    """
    return root(plugin, item_id)


CATEGORIES = {
    'Les émissions': URL_ROOT + '/video/',
    'Videos Films (Bandes-Annonces, Extraits, ...)':
        URL_ROOT + '/video/films/',
    'Videos Séries TV  (Bandes-Annonces, Extraits, ...)':
        URL_ROOT + '/series/video/',
    'News Vidéos': URL_ROOT + '/news/videos/'
}

CATEGORIES_LANGUAGE = {
    'VF': 'version-0/',
    'VO': 'version-1/'
}


def root(plugin, item_id):
    """Add modes in the listing"""
    for category_name, category_url in CATEGORIES.iteritems():

        if 'series' in category_url or 'films' in category_url:
            next_value = 'list_shows_films_series_1'
        elif 'news' in category_url:
            next_value = 'list_videos_news_videos'
        else:
            next_value = 'list_shows_emissions_1'

        if 'news' in category_url:
            item = Listitem()
            item.label = category_name
            item.set_callback(
                eval(next_value),
                item_id=item_id,
                category_url=category_url,
                page=1)
            yield item
        else:
            item = Listitem()
            item.label = category_name
            item.set_callback(
                eval(next_value),
                item_id=item_id,
                category_url=category_url)
            yield item

    # Search videos
    item = Listitem.search(
        list_videos_search,
        item_id=item_id,
        page=1)
    yield item


@Route.register
def list_shows_emissions_1(plugin, item_id, category_url):
    # Build Categories Emissions
    replay_categories_programs_html = urlquick.get(
        category_url).text
    replay_categories_programs_soup = bs(
        replay_categories_programs_html, 'html.parser')
    root_categories_programs = replay_categories_programs_soup.find(
        'li', class_='item_4 is_active ')
    replay_categories_programs = root_categories_programs.find_all('a')

    for category_programs in replay_categories_programs:
        item = Listitem()
        categorie_programs_title = category_programs.get_text()
        item.label = categorie_programs_title.strip()

        categorie_programs_url = URL_ROOT + category_programs.get('href')

        item.set_callback(
            list_shows_emissions_2,
            item_id=item_id,
            categorie_programs_url=categorie_programs_url)
        yield item


@Route.register
def list_shows_emissions_2(plugin, item_id, categorie_programs_url):
    # Build sub categories if exists / add 'Les Programmes', 'Les Vidéos'
    replay_subcategories_programs_html = urlquick.get(
        categorie_programs_url).text
    replay_subcategories_programs_soup = bs(
        replay_subcategories_programs_html, 'html.parser')

    # Les vidéos
    item = Listitem()
    item.label = '# Les videos'
    show_url = categorie_programs_url

    item.set_callback(
        list_videos_emissions_1,
        item_id=item_id,
        page=1,
        last_page=100,
        show_url=show_url)

    yield item

    # Les programmes
    item = Listitem()
    item.label = '# Les programmes'
    programs_url = categorie_programs_url.replace(
        '/cat-', '/prgcat-')

    item.set_callback(
        list_shows_emissions_4,
        item_id=item_id,
        programs_url=programs_url,
        page=1)

    yield item

    # Subcategories
    subcategories = replay_subcategories_programs_soup.find(
        'div', class_='nav-button-filter').find_all('a')

    for subcategory in subcategories:
        item = Listitem()
        item.label = subcategory.find(
            'span', class_='label').get_text()
        subcategorie_programs_url = URL_ROOT + subcategory.get('href')

        item.set_callback(
            list_shows_emissions_3,
            item_id=item_id,
            subcategorie_programs_url=subcategorie_programs_url)
        yield item


@Route.register
def list_shows_emissions_3(plugin, item_id, subcategorie_programs_url):
    # Les vidéos
    item = Listitem()
    item.label = '# Les videos'
    item.set_callback(
        list_videos_emissions_1,
        item_id=item_id,
        page=1,
        last_page=100,
        show_url=subcategorie_programs_url)
    yield item

    # Les programmes
    item = Listitem()
    item.label = '# Les programmes'
    programs_url = subcategorie_programs_url.replace(
        '/cat-', '/prgcat-')

    item.set_callback(
        list_shows_emissions_4,
        item_id=item_id,
        page=1,
        programs_url=programs_url)
    yield item


@Route.register
def list_shows_emissions_4(plugin, item_id, page, programs_url):
    replay_programs_html = urlquick.get(
        programs_url + '?page=%s' % page).text
    replay_programs_soup = bs(replay_programs_html, 'html.parser')
    replay_programs = replay_programs_soup.find_all(
        'figure', class_='media-meta-fig')

    for program in replay_programs:
        item = Listitem()
        item.label = program.find(
            'h2', class_='title '
        ).find('span').find('a').get_text().strip()
        if program.find('img').get('data-attr'):
            image_json_parser = json.loads(program.find('img').get('data-attr'))
            item.art['thumb'] = image_json_parser['src']
        else:
            item.art['thumb'] = program.find('img').get('src')
        program_url = URL_ROOT + program.find(
            'h2', class_='title '
        ).find('span').find('a').get('href')

        item.set_callback(
            list_shows_emissions_5,
            item_id=item_id,
            program_url=program_url)
        yield item

    if replay_programs_soup.find('div', class_='pager pager margin_40t') \
            is not None:
        # More programs...
        yield Listitem.next_page(
            item_id=item_id,
            programs_url=programs_url,
            page=page + 1)


@Route.register
def list_shows_emissions_5(plugin, item_id, program_url):
    replay_seasons_html = urlquick.get(
        program_url + 'saisons/').text
    replay_seasons_soup = bs(replay_seasons_html, 'html.parser')
    replay_seasons = replay_seasons_soup.find_all(
        'h2', class_='fs18 d_inline_block margin_10r')

    if len(replay_seasons) > 0:

        for season in replay_seasons:
            item = Listitem()
            item.label = season.find('a').find('span').get_text().strip()
            show_season_url = URL_ROOT + season.find(
                'a', class_='no_underline').get('href')

            # Get Last Page
            last_page = '0'
            info_show_season = urlquick.get(show_season_url).text
            info_show_season_pages = re.compile(
                '<a href="(.*?)"').findall(info_show_season)
            for info_show_season_page in info_show_season_pages:
                if '?page=' in info_show_season_page:
                    last_page = info_show_season_page.split('=')[1]

            item.set_callback(
                list_videos_emissions_1,
                item_id=item_id,
                page=1,
                last_page=last_page,
                show_url=show_season_url)
            yield item

    else:
        item = Listitem()
        try:
            item.label = replay_seasons_soup.find(
                'div', class_='margin_20t margin_40b'
            ).find('a').get_text().strip()
            show_season_url = URL_ROOT + replay_seasons_soup.find(
                'div', class_='margin_20t margin_40b'
            ).find('a').get('href')
        except Exception:
            item.label = replay_seasons_soup.find(
                'h3', class_='title'
            ).find('a').get_text().strip()
            show_season_url = URL_ROOT + replay_seasons_soup.find(
                'h3', class_='title'
            ).find('a').get('href')

        # Get Last Page
        last_page = '0'
        info_show_season = urlquick.get(show_season_url).text
        info_show_season_pages = re.compile(
            '<a href="(.*?)"').findall(info_show_season)
        for info_show_season_page in info_show_season_pages:
            if '?page=' in info_show_season_page:
                last_page = info_show_season_page.split('=')[1]

        item.set_callback(
            list_videos_emissions_1,
            item_id=item_id,
            page=1,
            last_page=last_page,
            show_url=show_season_url)
        yield item


@Route.register
def list_shows_films_series_1(plugin, item_id, category_url):
    # Build All Types
    replay_types_films_series_html = urlquick.get(
        category_url).text
    replay_types_films_series_soup = bs(
        replay_types_films_series_html, 'html.parser')
    replay_types_films_series = replay_types_films_series_soup.find_all(
        'div', class_='left_col_menu_item')[0]

    item = Listitem()
    item.label = '# Toutes les videos'
    item.set_callback(
        list_videos_films_series_1,
        item_id=item_id,
        page=1,
        show_url=category_url)
    yield item

    for all_types in replay_types_films_series.find_all('a'):
        item = Listitem()

        item.label = all_types.get_text()
        show_url = URL_ROOT + all_types.get('href')

        item.set_callback(
            list_shows_films_series_2,
            item_id=item_id,
            show_url=show_url)
        yield item


@Route.register
def list_shows_films_series_2(plugin, item_id, show_url):
    # Build All Languages
    item = Listitem()
    item.label = '# Toutes les videos'
    item.set_callback(
        list_videos_films_series_1,
        item_id=item_id,
        show_url=show_url,
        page=1)
    yield item

    for language, language_url in CATEGORIES_LANGUAGE.iteritems():
        item = Listitem()
        item.label = language
        item.set_callback(
            list_videos_films_series_1,
            item_id=item_id,
            page=1,
            show_url=show_url + language_url)
        yield item


@Route.register
def list_videos_films_series_1(plugin, item_id, page, show_url):
    replay_episodes_html = urlquick.get(
        show_url + '?page=%s' % page).text
    replay_episodes_soup = bs(replay_episodes_html, 'html.parser')
    episodes = replay_episodes_soup.find_all(
        'article', class_="media-meta sidecontent small")

    for episode in episodes:
        item = Listitem()
        item.label = episode.find('h2').find(
            'span').find('a').get_text().strip()
        try:
            video_id = re.compile(
                'cmedia=(.*?)&').findall(episode.find('a').get('href'))[0]
        except IndexError:
            continue
        item.art['thumb'] = episode.find('img').get('src')

        item.context.script(
            get_video_url,
            plugin.localize(LABELS['Download']),
            video_id=video_id,
            item_id=item_id,
            video_label=LABELS[item_id] + ' - ' + item.label,
            download_mode=True)

        item.set_callback(
            get_video_url,
            item_id=item_id,
            video_id=video_id)

        yield item

    # More videos...
    yield Listitem.next_page(
        item_id=item_id,
        page=page + 1,
        show_url=show_url)


@Route.register
def list_videos_emissions_1(plugin, item_id, page, show_url, last_page):
    replay_episodes_html = urlquick.get(
        show_url + '?page=%s' % page).text
    replay_episodes_soup = bs(replay_episodes_html, 'html.parser')

    if replay_episodes_soup.find(
            'section', class_='media-meta-list by2 j_w') is not None:
        root_episodes_soup = replay_episodes_soup.find(
            'section', class_='media-meta-list by2 j_w')
        episodes = root_episodes_soup.find_all(
            'figure', class_='media-meta-fig')
    else:
        episodes = replay_episodes_soup.find_all(
            'figure', class_='media-meta-fig')

    for episode in episodes:
        item = Listitem()
        if episode.find('h3') is not None:
            item.label = episode.find(
                'h3').find('span').find('a').get_text().strip()
        else:
            item.label = episode.find(
                'h2').find('span').find('a').get_text().strip()
        if '?cmedia=' in episode.find('a').get('href'):
            video_id = episode.find('a').get('href').split('?cmedia=')[1]
        elif 'cfilm=' in episode.find('a').get('href') or \
                'cserie=' in episode.find('a').get('href'):
            video_id = episode.find(
                'h2').find('span').find(
                    'a').get('href').split('_cmedia=')[1].split('&')[0]
        else:
            video_id = episode.find(
                'a').get('href').split('-')[1].replace('/', '')

        for plot_value in episode.find(
                'div', class_='media-meta-figcaption-inner').find_all('p'):
            item.info['plot'] = plot_value.get_text().strip()
        if episode.find('meta') is not None:
            item.art['thumb'] = episode.find('meta').get('content')
        else:
            if episode.find('img').get('data-attr'):
                image_json_parser = json.loads(episode.find('img').get('data-attr'))
                item.art['thumb'] = image_json_parser['src']
            else:
                item.art['thumb'] = episode.find('img').get('src')

        item.context.script(
            get_video_url,
            plugin.localize(LABELS['Download']),
            video_id=video_id,
            item_id=item_id,
            video_label=LABELS[item_id] + ' - ' + item.label,
            download_mode=True)

        item.set_callback(
            get_video_url,
            item_id=item_id,
            video_id=video_id)
        yield item

    # More videos...
    yield Listitem.next_page(
        item_id=item_id,
        page=page + 1,
        last_page=last_page,
        show_url=show_url)


@Route.register
def list_videos_search(plugin, item_id, page, search_query):
    replay_episodes_html = urlquick.get(
        URL_SEARCH_VIDEOS % (page, search_query)).text
    replay_episodes_soup = bs(replay_episodes_html, 'html.parser')

    episodes = replay_episodes_soup.find(
        'table', class_='totalwidth noborder purehtml').find_all(
            'tr')

    for episode in episodes:
        if episode.find('img'):
            item = Listitem()
            item.label = episode.find('img').get('alt')
            video_id = ''
            if '_cmedia=' in episode.find('a').get('href'):
                video_id = re.compile(
                    r'cmedia=(.*?)\&').findall(
                        episode.find('a').get('href'))[0]
            elif '?cmedia=' in episode.find('a').get('href'):
                video_id = episode.find('a').get('href').split('?cmedia=')[1]
            elif 'video-' in episode.find('a').get('href'):
                video_id = episode.find(
                    'a').get('href').split('-')[1].replace('/', '')
            item.art['thumb'] = episode.find('img').get('src')

            item.context.script(
                get_video_url,
                plugin.localize(LABELS['Download']),
                video_id=video_id,
                item_id=item_id,
                video_label=LABELS[item_id] + ' - ' + item.label,
                download_mode=True)

            item.set_callback(
                get_video_url,
                item_id=item_id,
                video_id=video_id)
            yield item

    # More videos...
    yield Listitem.next_page(
        item_id=item_id,
        page=page + 1,
        search_query=search_query)


@Resolver.register
def get_video_url(
        plugin, item_id, video_id, download_mode=False, video_label=None):
    """Get video URL and start video player"""

    video_json = urlquick.get(
        URL_API_MEDIA % (video_id, PARTNER)).text
    video_json_parser = json.loads(video_json)
    # print(repr(video_json_parser))
    desired_quality = Script.setting.get_string('quality')

    if 'media' not in video_json_parser:
        return False

    final_url = ''
    if 'rendition' in video_json_parser["media"]:
        # (Video Hosted By Allocine)
        if desired_quality == "DIALOG":
            all_datas_videos_quality = []
            all_datas_videos_path = []
            for media in video_json_parser["media"]["rendition"]:
                all_datas_videos_quality.append(
                    media["bandwidth"]["$"])
                all_datas_videos_path.append(media["href"])
            seleted_item = xbmcgui.Dialog().select(
                plugin.localize(LABELS['choose_video_quality']),
                all_datas_videos_quality)
            if seleted_item == -1:
                return False
            final_url = all_datas_videos_path[seleted_item]
        elif desired_quality == "BEST":
            for media in video_json_parser["media"]["rendition"]:
                final_url = media["href"]
        else:
            for media in video_json_parser["media"]["rendition"][0]:
                final_url = media["href"]
        if requests.get(final_url, stream=True).status_code == 404:
            label = plugin.localize(LABELS['Video stream no longer exists'])
            Script.notify(label, label)
            return False
        if download_mode:
            return download.download_video(final_url, video_label)

        return final_url
    else:
        # (Video Not Hosted By Allocine)
        url_video_embeded = re.compile(
            'src=\'(.*?)\''
        ).findall(video_json_parser["media"]["trailerEmbed"])[0]
        if 'allocine' in url_video_embeded:
            url_video_embeded_html = urlquick.get(url_video_embeded).text
            url_video_resolver = re.compile(
                'data-model="(.*?)"'
            ).findall(url_video_embeded_html)[0]
            url_video_resolver = url_video_resolver.replace('&quot;', '"')
            url_video_resolver = url_video_resolver.replace('\\', '')
            url_video_resolver = url_video_resolver.replace('&amp;', '&')
            url_video_resolver = url_video_resolver.replace('%2F', '/')
            # Case Youtube
            if 'youtube' in url_video_resolver:
                video_id = re.compile(
                    r'www.youtube.com/embed/(.*?)[\?\"\&]').findall(
                    url_video_resolver)[0]
                return resolver_proxy.get_stream_youtube(
                    plugin, video_id, download_mode, video_label)

            # Case DailyMotion
            elif 'dailymotion' in url_video_resolver:
                video_id = re.compile(
                    r'embed/video/(.*?)[\"\?]').findall(
                    url_video_resolver)[0]
                return resolver_proxy.get_stream_dailymotion(
                    plugin, video_id, download_mode, video_label)

            # Case Facebook
            elif 'facebook' in url_video_resolver:
                video_id = re.compile(
                    'www.facebook.com/allocine/videos/(.*?)/').findall(
                    url_video_resolver)[0]
                return resolver_proxy.get_stream_facebook(
                    plugin, video_id, download_mode, video_label)

            # Case Vimeo
            elif 'vimeo' in url_video_resolver:
                video_id = re.compile('player.vimeo.com/video/(.*?)[\?\"]').findall(
                    url_video_resolver)[0]
                return resolver_proxy.get_stream_vimeo(
                    plugin, video_id, download_mode, video_label)

            # TO DO ? (return an error)
            else:
                return False
        else:
            # Case Youtube
            if 'youtube' in url_video_embeded:
                video_id = re.compile(
                    'www.youtube.com/embed/(.*?)[\?\"\&]').findall(
                    url_video_embeded)[0]
                return resolver_proxy.get_stream_youtube(
                    plugin, video_id, download_mode, video_label)

            # TO DO ? (return an error)
            else:
                return False


@Route.register
def list_videos_news_videos(plugin, item_id, category_url, page):

    replay_episodes_html = urlquick.get(
        category_url + '?page=%s' % page).text
    replay_episodes_soup = bs(replay_episodes_html, 'html.parser')
    episodes = replay_episodes_soup.find_all(
        'div', class_=re.compile('card card-news'))

    for episode in episodes:
        if episode.find('a', class_='meta-title-link'):
            item = Listitem()
            item.label = episode.find('a', class_='meta-title-link').text
            if episode.find('img').get('data-src'):
                item.art['thumb'] = episode.find('img').get('data-src')
            else:
                item.art['thumb'] = episode.find('img').get('src')
            video_url = URL_ROOT + episode.find('a', class_='meta-title-link').get('href')
            if episode.find('div', class_='meta-body'):
                item.info['plot'] = episode.find('div', class_='meta-body').text
            item.context.script(
                get_video_url_news_videos,
                plugin.localize(LABELS['Download']),
                video_url=video_url,
                item_id=item_id,
                video_label=LABELS[item_id] + ' - ' + item.label,
                download_mode=True)

            item.set_callback(
                get_video_url_news_videos,
                item_id=item_id,
                video_url=video_url)
            yield item

    # More videos...
    yield Listitem.next_page(
        item_id=item_id,
        page=page + 1,
        category_url=category_url)


@Resolver.register
def get_video_url_news_videos(
        plugin, item_id, video_url, download_mode=False, video_label=None):

    resp = urlquick.get(video_url)
    root_soup = bs(resp.text, 'html.parser')
    url_video_resolver = root_soup.find(
        'iframe', class_='js-frame-lazed').get('data-url')

    # print 'url_video_resolver value : ' + url_video_resolver

    # Case Youtube
    if 'youtube' in url_video_resolver:
        video_id = re.compile(
            r'www.youtube.com/embed/(.*?)$').findall(
            url_video_resolver)[0]
        return resolver_proxy.get_stream_youtube(
            plugin, video_id, download_mode, video_label)

    # Case DailyMotion
    elif 'dailymotion' in url_video_resolver:
        video_id = re.compile(
            r'embed/video/(.*?)$').findall(
            url_video_resolver)[0]
        return resolver_proxy.get_stream_dailymotion(
            plugin, video_id, download_mode, video_label)

    # Case Facebook
    elif 'facebook' in url_video_resolver:
        video_id = re.compile(
            'www.facebook.com/allocine/videos/(.*?)/').findall(
            url_video_resolver)[0]
        # print 'video_id facebook ' + video_id
        return resolver_proxy.get_stream_facebook(
            plugin, video_id, download_mode, video_label)

    # Case Vimeo
    elif 'vimeo' in url_video_resolver:
        video_id = re.compile(r'player.vimeo.com/video/(.*?)$').findall(
            url_video_resolver)[0]
        return resolver_proxy.get_stream_vimeo(
            plugin, video_id, download_mode, video_label)
    # TO DO ? (return an error)
    else:
        return False
