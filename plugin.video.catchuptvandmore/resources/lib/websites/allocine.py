# -*- coding: utf-8 -*-
# Copyright: (c) 2017, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals

import base64
import json
import re
import xbmcgui
import urlquick

from codequick import Listitem, Resolver, Route
from resources.lib import resolver_proxy
from resources.lib.menu_utils import item_post_treatment
from resources.lib.kodi_utils import PY3

# TO DO
# Get Partner Id ?

URL_ROOT = 'http://www.allocine.fr'

URL_API_MEDIA = 'http://api.allocine.fr/rest/v3/' \
                'media?code=%s&partner=%s&format=json'
# videoId, PARTENER
PARTNER = 'YW5kcm9pZC12Mg'

URL_SEARCH_VIDEOS = URL_ROOT + '/rechercher/%s?q=%s'
# Page, Query


CATEGORIES = {
    'Les émissions': URL_ROOT + '/video/',
    'Videos Films (Bandes-Annonces, Extraits, ...)':
    URL_ROOT + '/video/films/',
    'Videos Séries TV  (Bandes-Annonces, Extraits, ...)':
    URL_ROOT + '/series/video/',
    'News Vidéos': URL_ROOT + '/news/videos/'
}

CATEGORIES_LANGUAGE = {'VF': 'version-0/', 'VO': 'version-1/'}

SPLIT_CODE = "ACr"


def convertMonth(string):
    m = {
        'janvier': 1,
        'février': 2,
        'mars': 3,
        'avril': 4,
        'mai': 5,
        'juin': 6,
        'juillet': 7,
        'août': 8,
        'septembre': 9,
        'octobre': 10,
        'novembre': 11,
        'décembre': 12,
    }
    return m[string]


def html_decode(s):
    """
    Returns the ASCII decoded version of the given HTML string. This does
    NOT remove normal HTML tags like <p>.
    """

    htmlCodes = (("'", '&#39;'), ('"', '&quot;'), ('>', '&gt;'), ('<',
                 '&lt;'), ('&', '&amp;'))
    for code in htmlCodes:
        s = s.replace(code[1], code[0])
    return s


def unobfuscated(obfuscated):
    b64_url = obfuscated.split()[0]
    base64Decode = base64.standard_b64decode(b64_url.replace(SPLIT_CODE, ""))
    if PY3:
        return base64Decode.decode()
    return base64Decode


@Route.register
def website_root(plugin, item_id, **kwargs):
    """Add modes in the listing"""
    for category_name, category_url in list(CATEGORIES.items()):

        if 'series' in category_url or 'films' in category_url:
            next_value = 'list_shows_films_series_1'
        elif 'news' in category_url:
            next_value = 'list_videos_news_videos'
        else:
            next_value = 'list_shows_emissions_1'

        if 'news' in category_url:
            item = Listitem()
            item.label = category_name
            item.set_callback(eval(next_value),
                              item_id=item_id,
                              category_url=category_url,
                              page=1)
            item_post_treatment(item)
            yield item
        else:
            item = Listitem()
            item.label = category_name
            item.set_callback(eval(next_value),
                              item_id=item_id,
                              category_url=category_url)
            item_post_treatment(item)
            yield item

    # Search videos
    item = Listitem.search(list_search_categories, item_id=item_id)
    item_post_treatment(item)
    yield item


@Route.register
def list_shows_emissions_1(plugin, item_id, category_url, **kwargs):
    # Build Categories Emissions
    resp = urlquick.get(category_url)
    root = resp.parse("li", attrs={"class": "item_4 is_active "})

    for category_programs in root.iterfind(".//a"):
        item = Listitem()
        categorie_programs_title = category_programs.text
        item.label = categorie_programs_title.strip()

        categorie_programs_url = URL_ROOT + category_programs.get('href')

        item.set_callback(list_shows_emissions_2,
                          item_id=item_id,
                          categorie_programs_url=categorie_programs_url)
        item_post_treatment(item)
        yield item


@Route.register
def list_shows_emissions_2(plugin, item_id, categorie_programs_url, **kwargs):
    # Build sub categories if exists / add 'Les Programmes', 'Les Vidéos'

    # Les vidéos
    item = Listitem()
    item.label = '# Les videos'
    show_url = categorie_programs_url

    item.set_callback(list_videos_emissions_2,
                      item_id=item_id,
                      page=1,
                      last_page=100,
                      show_url=show_url)
    item_post_treatment(item)

    yield item

    # Les programmes
    item = Listitem()
    item.label = '# Les programmes'
    programs_url = categorie_programs_url.replace('/cat-', '/prgcat-')

    item.set_callback(list_shows_emissions_4,
                      item_id=item_id,
                      programs_url=programs_url,
                      page=1)
    item_post_treatment(item)

    yield item

    resp = urlquick.get(categorie_programs_url)
    root = resp.parse("div", attrs={"class": "nav-button-filter"})

    for subcategory in root.iterfind(".//a"):
        item = Listitem()
        item.label = subcategory.find(".//span[@class='label']").text
        subcategorie_programs_url = URL_ROOT + subcategory.get('href')

        item.set_callback(list_shows_emissions_3,
                          item_id=item_id,
                          subcategorie_programs_url=subcategorie_programs_url)
        item_post_treatment(item)
        yield item


@Route.register
def list_shows_emissions_3(plugin, item_id, subcategorie_programs_url,
                           **kwargs):
    # Les vidéos
    item = Listitem()
    item.label = '# Les videos'
    item.set_callback(list_videos_emissions_2,
                      item_id=item_id,
                      page=1,
                      last_page=100,
                      show_url=subcategorie_programs_url)
    item_post_treatment(item)
    yield item

    # Les programmes
    item = Listitem()
    item.label = '# Les programmes'
    programs_url = subcategorie_programs_url.replace('/cat-', '/prgcat-')

    item.set_callback(list_shows_emissions_4,
                      item_id=item_id,
                      page=1,
                      programs_url=programs_url)
    item_post_treatment(item)
    yield item


@Route.register
def list_shows_emissions_4(plugin, item_id, page, programs_url, **kwargs):
    resp = urlquick.get(programs_url + '?page=%s' % page)
    root = resp.parse()

    for program in root.iterfind(".//figure[@class='media-meta-fig']"):
        item = Listitem()
        item.label = program.find(".//h2[@class='title ']").find(
            './/span').find('.//a').text.strip()
        if program.find('.//img').get('data-attr') is not None:
            image_json_parser = json.loads(
                program.find('.//img').get('data-attr'))
            item.art['thumb'] = item.art['landscape'] = image_json_parser['src']
        else:
            item.art['thumb'] = item.art['landscape'] = program.find('.//img').get('src')
        program_url = URL_ROOT + program.find(".//h2[@class='title ']").find(
            './/span').find('.//a').get('href')

        item.set_callback(list_shows_emissions_5,
                          item_id=item_id,
                          program_url=program_url)
        item_post_treatment(item)
        yield item

    if 'button btn-primary btn-large fr btn-disabled' not in resp.text \
       and "pager pager margin_40t" in resp.text:
        # More programs...
        yield Listitem.next_page(item_id=item_id,
                                 programs_url=programs_url,
                                 page=page + 1)


@Route.register
def list_shows_emissions_5(plugin, item_id, program_url, **kwargs):

    resp = urlquick.get(program_url)
    root = resp.parse()
    if root.find(".//div[@class='cf']") is not None:
        root_ok = resp.parse("div", attrs={"class": "cf"})

        replay_seasons = root_ok.findall(
            ".//a[@class='end-section-link ']")

        if len(replay_seasons) > 0:
            for season in replay_seasons:

                item = Listitem()
                item.label = season.get('title')
                show_season_url = URL_ROOT + season.get('href')
                item.set_callback(list_videos_emissions_1,
                                  item_id=item_id,
                                  show_url=show_season_url)
                item_post_treatment(item)
                yield item


@Route.register
def list_shows_films_series_1(plugin, item_id, category_url, **kwargs):
    # Build All Types
    resp = urlquick.get(category_url)
    root = resp.parse()

    replay_types_films_series = root.findall(
        ".//ul[@class='filter-entity-word']")[0]

    item = Listitem()
    item.label = '# Toutes les videos'
    item.set_callback(list_videos_films_series_1,
                      item_id=item_id,
                      page=1,
                      show_url=category_url)
    item_post_treatment(item)
    yield item

    for all_types in replay_types_films_series.findall('.//a'):
        item = Listitem()

        item.label = all_types.text
        show_url = URL_ROOT + all_types.get('href')

        item.set_callback(list_shows_films_series_2,
                          item_id=item_id,
                          show_url=show_url)
        item_post_treatment(item)
        yield item


@Route.register
def list_shows_films_series_2(plugin, item_id, show_url, **kwargs):
    # Build All Languages
    item = Listitem()
    item.label = '# Toutes les videos'
    item.set_callback(list_videos_films_series_1,
                      item_id=item_id,
                      show_url=show_url,
                      page=1)
    item_post_treatment(item)
    yield item

    for language, language_url in list(CATEGORIES_LANGUAGE.items()):
        item = Listitem()
        item.label = language
        item.set_callback(list_videos_films_series_1,
                          item_id=item_id,
                          page=1,
                          show_url=show_url + language_url)
        item_post_treatment(item)
        yield item


@Route.register
def list_videos_films_series_1(plugin, item_id, page, show_url, **kwargs):
    resp = urlquick.get(show_url + '?page=%s' % page)
    root = resp.parse()

    for episode in root.iterfind(
            ".//div[@class='card video-card video-card-row mdl-fixed']"):
        item = Listitem()
        item.label = episode.find('.//img').get('alt')
        try:
            video_url = URL_ROOT + episode.find(".//a[@class='meta-title-link']").get('href')
        except IndexError:
            continue
        if episode.find('.//img').get('data-src') is not None:
            item.art['thumb'] = item.art['landscape'] = episode.find('.//img').get('data-src')
        else:
            item.art['thumb'] = item.art['landscape'] = episode.find('.//img').get('src')

        item.set_callback(get_video_url,
                          item_id=item_id,
                          video_url=video_url)
        item_post_treatment(item, is_playable=True, is_downloadable=True)
        yield item

    # More videos...
    yield Listitem.next_page(item_id=item_id, page=page + 1, show_url=show_url)


@Route.register
def list_videos_emissions_1(plugin, item_id, show_url,
                            **kwargs):
    resp = urlquick.get(show_url)
    root = resp.parse("div", attrs={"class": "gd gd-gap-15 gd-xs-1 gd-s-2"})

    for episode in root.iterfind(".//div[@class='card video-card video-card-col mdl-fixed']"):
        item = Listitem()
        item.label = episode.find(".//img").get('alt')

        if episode.find('.//img').get('data-attr') is not None:
            image_json_parser = json.loads(
                episode.find('.//img').get('data-attr'))
            item.art['thumb'] = item.art['landscape'] = image_json_parser['src']
        elif episode.find('.//img').get('data-src') is not None:
            item.art['thumb'] = item.art['landscape'] = episode.find('.//img').get('data-src')
        else:
            item.art['thumb'] = item.art['landscape'] = episode.find('.//img').get('src')

        try:
            video_url = URL_ROOT + episode.find(".//a[@class='meta-title-link']").get('href')
        except IndexError:
            continue

        item.set_callback(get_video_url,
                          item_id=item_id,
                          video_url=video_url)
        item_post_treatment(item, is_playable=True, is_downloadable=True)
        yield item


@Route.register
def list_videos_emissions_2(plugin, item_id, page, show_url, last_page,
                            **kwargs):
    resp = urlquick.get(show_url + '?page=%s' % page)
    root = resp.parse()

    if root.find(".//section[@class='media-meta-list by2 j_w']") is not None:
        root_episodes = root.find(
            ".//section[@class='media-meta-list by2 j_w']")
        episodes = root_episodes.findall(".//figure[@class='media-meta-fig']")
    else:
        episodes = root.findall(".//figure[@class='media-meta-fig']")

    for episode in episodes:
        item = Listitem()
        if episode.find('.//h3') is not None:
            video_title = episode.find('.//h3').find('.//span').find(
                './/a').find('.//strong').text.strip() + ' - ' + episode.find(
                    './/h3').find('.//span').find('.//a').find(
                        './/strong').tail.strip()
        else:
            if episode.find('.//h2/span/a/strong') is not None:
                video_title = episode.find('.//h2/span/a/strong').text.strip() \
                    + ' - ' + episode.find('.//h2/span/a/strong').tail.strip()
            elif episode.find('.//h2/span/span') is not None:
                video_title = episode.find('.//h2/span/span').text.strip()
            elif episode.find('.//h2/span/a') is not None:
                video_title = episode.find('.//h2/span/a').text.strip()
            else:
                video_title = ''
        item.label = video_title

        if episode.find(".//a") is not None:
            video_urls_datas = episode.findall(".//a")
            video_url = ''
            for video_url_datas in video_urls_datas:
                if 'program' not in video_url_datas.get('href'):
                    video_url = URL_ROOT + video_url_datas.get('href')
        else:
            # TODO: ↪ Root menu (1) ➡ Websites (3) ➡ Allociné (1) ➡ Les émissions (1) ➡
            # Stars (6) ➡ Clips musicaux (3) ➡ # Les videos (1) ➡ [B]Next page 2[/B]
            continue

        for plot_value in episode.find(
                ".//div[@class='media-meta-figcaption-inner']").findall(
                    './/p'):
            item.info['plot'] = plot_value.text.strip()
        if episode.find('.//meta') is not None:
            item.art['thumb'] = item.art['landscape'] = episode.find('.//meta').get('content')
        else:
            if episode.find('.//img').get('data-attr') is not None:
                image_json_parser = json.loads(
                    episode.find('.//img').get('data-attr'))
                item.art['thumb'] = item.art['landscape'] = image_json_parser['src']
            else:
                item.art['thumb'] = item.art['landscape'] = episode.find('.//img').get('src')

        item.set_callback(get_video_url,
                          item_id=item_id,
                          video_url=video_url)
        item_post_treatment(item, is_playable=True, is_downloadable=True)
        yield item

    # More videos...
    yield Listitem.next_page(item_id=item_id,
                             page=page + 1,
                             last_page=last_page,
                             show_url=show_url)


@Route.register
def list_search_categories(plugin, item_id, search_query=None, full_url=None, **kwargs):

    if search_query is not None:
        resp = urlquick.get(URL_SEARCH_VIDEOS % ("", search_query))
    else:
        resp = urlquick.get(full_url)

    try:
        root = resp.parse("nav", attrs={"class": "third-nav third-nav-tab js-third-nav "})
    except RuntimeError:
        try:
            root = resp.parse("nav", attrs={"class": "third-nav third-nav-tab js-third-nav"})
        except RuntimeError:
            yield None
            return

    # only show categories that may contain videos
    menu_items_1 = ('Stars', 'Sociétés')
    menu_items_2 = ('Top', 'VOD', 'News', 'Vidéo', 'Films', 'Séries',
                    'Production', 'Exportation', 'Chaîne', 'Effets')

    if root.find(".//a[@title]") is not None:
        for menu_item in root.iterfind(".//a[@title]"):
            label = menu_item.get('title')
            menu_url = URL_ROOT + menu_item.get('href')

            item = Listitem()
            item.label = label.strip(' \n')
            if item.label.startswith(menu_items_1):
                item.set_callback(list_search_subcategories,
                                  item_id=item_id,
                                  category_url=menu_url,
                                  page=1)
                item_post_treatment(item)
                yield item
            elif item.label.startswith(menu_items_2):
                item.set_callback(list_search_videos,
                                  item_id=item_id,
                                  search_url=menu_url,
                                  page=1)
                item_post_treatment(item)
                yield item

    else:
        for menu_item in root.iterfind(".//span"):
            if SPLIT_CODE in menu_item.get('class'):
                if menu_item.find(".//span") is not None:
                    label = menu_item.find(".//span").text
                else:
                    label = menu_item.text
                if not label:
                    continue
                menu_url = URL_ROOT + unobfuscated(menu_item.get('class'))

                item = Listitem()
                item.label = label.strip(' \n')
                if item.label.startswith(menu_items_1):
                    item.set_callback(list_search_subcategories,
                                      item_id=item_id,
                                      category_url=menu_url,
                                      page=1)
                    item_post_treatment(item)
                    yield item
                elif item.label.startswith(menu_items_2):
                    item.set_callback(list_search_videos,
                                      item_id=item_id,
                                      search_url=menu_url,
                                      page=1)
                    item_post_treatment(item)
                    yield item


@Route.register
def list_search_subcategories(plugin, item_id, category_url, page, **kwargs):

    if '?q' in category_url:
        resp = urlquick.get(category_url + "&page=%s" % page)
    else:
        resp = urlquick.get(category_url + "?page=%s" % page)
    root = resp.parse()

    card_classes = ('card person-card entity-card-list entity-card mdl-fixed',
                    'card entity-card company-card',
                    'card entity-card company-card ')
    video_data_list = None
    for card_class in card_classes:
        if root.find(".//div[@class='%s']" % card_class) is not None:
            video_data_list = root.iterfind(".//div[@class='%s']" % card_class)
            break
    if not video_data_list:
        yield None
        return

    for category in video_data_list:
        if category.find('.//img') is not None:
            item = Listitem()
            item.label = category.find('.//img').get('alt')
            item.art['thumb'] = item.art['landscape'] = category.find('.//img').get('data-src')

            try:
                video_url = URL_ROOT + category.find(
                    './/*[@class="meta-title"]/a').get('href')
                item.set_callback(get_video_url,
                                  item_id=item_id,
                                  video_url=video_url)
                item_post_treatment(item, is_playable=True, is_downloadable=True)
                yield item
            except AttributeError:
                subcategory_url = URL_ROOT + unobfuscated(category.find(
                    './/*[@class="meta-title"]/span').get('class'))
                item.set_callback(list_search_categories,
                                  item_id=item_id,
                                  full_url=subcategory_url)
                item_post_treatment(item)
                yield item

    # More subcategories...
    try:
        root2 = resp.parse("nav", attrs={"class": "pagination cf"})
        if 'button-disabled' not in root2.find('span[2]').get('class'):
            yield Listitem.next_page(item_id=item_id,
                                     category_url=category_url,
                                     page=page + 1)
    except (RuntimeError, AttributeError):
        pass


@Route.register
def list_search_videos(plugin, item_id, search_url, page, **kwargs):

    if '?q' in search_url:
        resp = urlquick.get(search_url + "&page=%s" % page)
    else:
        resp = urlquick.get(search_url + "?page=%s" % page)
    root = resp.parse()

    card_classes = ('card entity-card entity-card-list cf',
                    'card entity-card entity-card-list entity-card-person cf',
                    'card video-card video-card-col mdl-fixed',
                    'card news-card news-card-row cf',
                    'card news-card news-card-col mdl cf')
    video_data_list = None
    for card_class in card_classes:
        if root.find(".//div[@class='%s']" % card_class) is not None:
            video_data_list = root.iterfind(".//div[@class='%s']" % card_class)
            break
    if not video_data_list:
        yield None
        return

    for video_data in video_data_list:
        item = Listitem()

        image_src = video_data.find('.//img').get('data-src')
        if not image_src:
            image_src = video_data.find('.//img').get('src')

        try:
            video_url = URL_ROOT + unobfuscated(video_data.find(
                './/*[@class="meta-title"]/span').get('class'))
        except AttributeError:
            video_url = URL_ROOT + video_data.find(
                './/*[@class="meta-title"]/a').get('href')

        # if not '/empty/' in image_src:
        item.label = video_data.find('.//img').get('alt')
        item.art['thumb'] = item.art['landscape'] = image_src

        try:
            date = video_data.find('.//*[@class="date"]').text
            month = date.split(" ")[1]
            month_number = convertMonth(month)
            item.info.date(date.replace(month, str(month_number)), '%d %m %Y')
        except AttributeError:
            pass

        try:
            item.info['plot'] = video_data.find('.//*[@class="content-txt "]').text
        except AttributeError:
            pass

        try:
            item.info['duration'] = video_data.find('.//*[@class="thumbnail-count"]').text
        except AttributeError:
            pass

        item.set_callback(get_video_url,
                          item_id=item_id,
                          video_url=video_url)
        item_post_treatment(item, is_playable=True, is_downloadable=True)
        yield item

    # More videos...
    try:
        root2 = resp.parse("nav", attrs={"class": "pagination cf"})
        if 'button-disabled' not in root2.find('span[2]').get('class'):
            yield Listitem.next_page(item_id=item_id,
                                     search_url=search_url,
                                     page=page + 1)
    except (RuntimeError, AttributeError):
        pass


@Route.register
def list_videos_news_videos(plugin, item_id, category_url, page, **kwargs):

    resp = urlquick.get(category_url + '?page=%s' % page)
    root = resp.parse("div", attrs={"class": "gd-col-left"})

    for episode in root.iterfind(".//div"):
        if episode.get('class') is not None:
            if 'card news-card' in episode.get('class'):
                if episode.find(".//a[@class='meta-title-link']") is not None:
                    item = Listitem()
                    item.label = episode.find(
                        ".//a[@class='meta-title-link']").text
                    if episode.find('.//img').get('data-src') is not None:
                        item.art['thumb'] = item.art['landscape'] = episode.find('.//img').get(
                            'data-src')
                    else:
                        item.art['thumb'] = item.art['landscape'] = episode.find('.//img').get('src')
                    video_url = URL_ROOT + episode.find(
                        ".//a[@class='meta-title-link']").get('href')
                    if episode.find(".//div[@class='meta-body']") is not None:
                        item.info['plot'] = episode.find(
                            ".//div[@class='meta-body']").text
                    item.context.script(get_video_url,
                                        plugin.localize(30503),
                                        video_url=video_url,
                                        item_id=item_id,
                                        download_mode=True)

                    item.set_callback(get_video_url,
                                      item_id=item_id,
                                      video_url=video_url)
                    yield item

    # More videos...
    yield Listitem.next_page(item_id=item_id,
                             page=page + 1,
                             category_url=category_url)


@Resolver.register
def get_video_url(plugin,
                  item_id,
                  video_url,
                  download_mode=False,
                  loop=1,
                  **kwargs):

    """Get video URL and start video player"""
    resp = urlquick.get(video_url, max_age=-1).text

    if "fichefilm" in video_url:
        video_url = URL_ROOT + re.compile(r'class="trailer item" href="(.+?)"').findall(resp)[0].replace("&amp;", "&")

        resp = urlquick.get(video_url, max_age=-1).text
        video_list = re.compile(r'meta ".+?span class="(.+?) .+?">(.+?)<', re.DOTALL).findall(resp)

        list_url = []
        list_q = []

        for a in video_list:
            list_url.append(a[0])
            list_q.append(a[1])

        if len(video_list) == 0:
            plugin.notify(plugin.localize(30718), '')
            return False

        ret = xbmcgui.Dialog().select("Choissiez le contenu", list_q)
        if ret > -1:
            video_url = URL_ROOT + unobfuscated(list_url[ret])

        resp = urlquick.get(video_url, max_age=-1).text

    if 'iframe src="about:blank"' in resp:
        url_video_resolver = re.compile(r'iframe.+?data-src="(.+?)"').findall(resp)[0]
        if 'youtube' in url_video_resolver:
            video_id = re.compile(
                r'www.youtube.com/embed/([^/]+)').findall(url_video_resolver)[0]
            return resolver_proxy.get_stream_youtube(
                plugin, video_id, download_mode)

        # Case DailyMotion
        if 'dailymotion' in url_video_resolver:
            video_id = re.compile(r'embed/video/(.*?)[\"\?]').findall(
                url_video_resolver)[0]
            return resolver_proxy.get_stream_dailymotion(
                plugin, video_id, download_mode)

        # Case Facebook
        if 'facebook' in url_video_resolver:
            video_id = re.compile(
                r'www.facebook.com/allocine/videos/(.*?)/').findall(url_video_resolver)[0]
            return resolver_proxy.get_stream_facebook(
                plugin, video_id, download_mode)

        # Case Vimeo
        if 'vimeo' in url_video_resolver:
            video_id = re.compile(
                r'player.vimeo.com/video/(.*?)[\?\"]').findall(url_video_resolver)[0]
            return resolver_proxy.get_stream_vimeo(
                plugin, video_id, download_mode)
    else:
        url_video_resolver = re.compile(r'data-model="(.+?)"').findall(resp)[0]

        video_id = json.loads(html_decode(url_video_resolver))["videos"][0]["idDailymotion"]
        return resolver_proxy.get_stream_dailymotion(
            plugin, video_id, download_mode)
