# -*- coding: utf-8 -*-
# Copyright: (c) JUL1EN094, SPM, SylvainCecchetto
# Copyright: (c) 2016, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
import json
import re
import time

from codequick import Listitem, Route, Resolver, Script, utils
from kodi_six import xbmcplugin
import urlquick

from resources.lib import resolver_proxy, web_utils
from resources.lib.addon_utils import get_item_media_path
from resources.lib.menu_utils import item_post_treatment


TAG_RE = re.compile(r'<[^>]+>')

try:
    from itertools import zip_longest
except ImportError:
    from itertools import izip_longest as zip_longest

try:
    from html import unescape
except ImportError:
    from six.moves.html_parser import HTMLParser
    HTML_PARSER = HTMLParser()
    unescape = HTML_PARSER.unescape


# Channels:
#     * france.tv (https://www.france.tv/)

URL_API_MOBILE = utils.urljoin_partial("https://api-mobile.yatta.francetv.fr/")
URL_API_FRONT = utils.urljoin_partial("http://api-front.yatta.francetv.fr")
URL_LIVE = 'https://www.france.tv/%s/direct.html'


@Route.register
def francetv_root(plugin, **kwargs):
    # Channels
    item = Listitem()
    item.label = Script.localize(30006)
    item.set_callback(channels)
    item_post_treatment(item)
    yield item

    # Categories
    item = Listitem()
    item.label = Script.localize(30725)
    item.set_callback(categories)
    item_post_treatment(item)
    yield item

    # Search feature
    item = Listitem.search(search)
    item_post_treatment(item)
    yield item


@Route.register
def channels(plugin, **kwargs):
    """
    List all france.tv channels
    """
    # (item_id, label, thumb, fanart)
    channels = [
        ('channels/france-2', 'France 2', 'france2.png', 'france2_fanart.jpg'),
        ('channels/france-3', 'France 3', 'france3.png', 'france3_fanart.jpg'),
        ('channels/france-4', 'France 4', 'france4.png', 'france4_fanart.jpg'),
        ('channels/france-5', 'France 5', 'france5.png', 'france5_fanart.jpg'),
        ('channels/france-o', 'France Ô', 'franceo.png', 'franceo_fanart.jpg'),
        ('regions/outre-mer', 'Outre-mer la 1ère', 'la1ere.png', 'la1ere_fanart.jpg'),
        ('channels/franceinfo', 'franceinfo:', 'franceinfo.png', 'franceinfo_fanart.jpg'),
        ('channels/slash', 'France tv Slash', 'slash.png', 'slash_fanart.jpg'),
        ('categories/enfants', 'Okoo', 'okoo.png', 'okoo_fanart.jpg'),
        ('channels/spectacles-et-culture', 'Culturebox', 'culturebox.png', 'culturebox_fanart.jpg')
    ]

    for channel_infos in channels:
        item = Listitem()
        item.label = channel_infos[1]
        item.art["thumb"] = get_item_media_path('channels/fr/' + channel_infos[2])
        item.art["fanart"] = get_item_media_path('channels/fr/' + channel_infos[3])
        item.set_callback(channel_homepage, channel_infos[0])
        item_post_treatment(item)
        yield item


@Route.register
def channel_homepage(plugin, item_id, **kwargs):
    """
    List channel homepage elements
    (e.g. https://www.france.tv/france-2/)
    """
    r = urlquick.get(URL_API_MOBILE('/apps/%s' % item_id),
                     params={'platform': 'apps'})
    j = json.loads(r.text)
    j = j['collections'] if 'collections' in j else j['items']

    for collection in j:
        item = Listitem()
        if set_item_callback_based_on_type(item, collection['type'], collection):
            yield item

    menu_items = [
        (Script.localize(30701), '/generic/taxonomy/%s/contents'),  # All videos
        (Script.localize(30717), '/apps/regions/%s/programs')  # All programs
    ]
    for menu_item in menu_items:
        item = Listitem()
        item.label = menu_item[0]
        item.set_callback(grab_json_collections, URL_API_MOBILE(menu_item[1] % item_id.split('/')[1]), page=0, collection_position=0)
        item_post_treatment(item)
        yield item


def set_item_callback_based_on_type(item, type_, j, next_page_item=None):
    # First try to populate label
    if 'label' in j:
        item.label = j['label'].capitalize()
    elif 'title' in j:
        item.label = j['title'].capitalize()
    else:
        item.label = 'No title'

    if 'description' in j:
        item.info['plot'] = j['description']

    # Second, try to populate images
    if 'images' in j:
        populate_images(item, j['images'])

    # Then, based on type, try to guess the correct callback

    # This is a new path
    if type_ == 'program':
        item.set_callback(grab_json_collections, URL_API_MOBILE('/apps/program/%s' % j['program_path']))
        item_post_treatment(item)
        return True

    if type_ == 'sous_categorie':
        item.set_callback(grab_json_collections, URL_API_MOBILE('/apps/sub-categories/%s' % j['url_complete']))
        item_post_treatment(item)
        return True

    if type_ == 'region':
        item.set_callback(outre_mer_root, j['region_path'])
        item_post_treatment(item)
        return True

    if type_ == 'categories':
        item.label = 'Les sous-catégories'
        item.set_callback(list_generic_items, j['items'], next_page_item)
        item_post_treatment(item)
        return True

    # This is a video
    if type_ == 'integrale' or type_ == 'extrait' or type_ == 'unitaire':
        si_id = populate_video_item(item, j)
        item.set_callback(get_video_url,
                          broadcast_id=si_id)
        item_post_treatment(item, is_playable=True, is_downloadable=True)
        return True

    if 'items' in j:
        item.set_callback(list_generic_items, j['items'], next_page_item)
        item_post_treatment(item)
        return True

    return False


def populate_images(item, images):
    all_images = {}
    for image in images:
        if 'type' in image:
            type_ = image['type']
            if type_ == 'carre':
                all_images['carre'] = image['urls']['w:400']
            elif type_ == 'vignette_16x9':
                all_images['vignette_16x9'] = image['urls']['w:1024']
            elif type_ == 'background_16x9':
                all_images['background_16x9'] = image['urls']['w:2500']
            elif type_ == 'vignette_3x4':
                all_images['vignette_3x4'] = image['urls']['w:1024']

    if 'vignette_3x4' in all_images:
        item.art['thumb'] = item.art['landscape'] = all_images['vignette_3x4']
    elif 'carre' in all_images:
        item.art['thumb'] = item.art['landscape'] = all_images['carre']

    if 'background_16x9' in all_images:
        item.art['fanart'] = all_images['background_16x9']
    elif 'vignette_16x9' in all_images:
        item.art['fanart'] = all_images['vignette_16x9']


def populate_video_item(item, video):
    if 'episode_title' in video:
        item.label = video['episode_title']
    else:
        item.label = video['title']
    description = video['description']
    if description:
        item.info['plot'] = TAG_RE.sub('', unescape(description))
    begin_date = time.strftime('%Y-%m-%d', time.localtime(video['begin_date']))
    item.info.date(begin_date, "%Y-%m-%d")

    if 'program' in video and video['program'] is not None and 'label' in video['program']:
        item.label = video['program']['label'] + ' - ' + item.label

    type_ = video['type']
    if type_ == 'extrait':
        item.label = '[extrait] ' + item.label

    # It's too bad item.info['title'] overrules item.label everywhere
    # so there's no difference between what is shown in the video list
    # and what is shown in the video details
    # item.info['title'] = video['title']
    item.info['title'] = item.label

    # id_ = video['id']

    rating = video['rating_csa_code']
    if rating.isdigit():
        rating = "-" + rating

    item.info['mpaa'] = rating

    if "text" in video and video['text']:
        item.info['plot'] = video['text']

    if "director" in video and video['director']:
        item.info['director'] = video['director']

    if "saison" in video and video['saison']:
        item.info['season'] = video['saison']

    if "episode" in video and video['episode']:
        # Now we know for sure we are dealing with an episode
        item.info['mediatype'] = "episode"
        item.info['episode'] = video['episode']

    actors = []
    if "casting" in video and video['casting']:
        actors = [actor.strip() for actor in video['casting'].split(",")]
    elif "presenter" in video and video['presenter']:
        actors.append(video['presenter'])

    item.info['cast'] = actors

    if "characters" in video and video['characters']:
        characters = [role.strip() for role in video['characters'].split(",")]
        if len(actors) > 0 and len(characters) > 0:
            item.info['castandrole'] = list(zip_longest(actors, characters))

    si_id = video['si_id']
    return si_id


@Route.register
def search(plugin, search_query, **kwargs):
    r = urlquick.get(URL_API_MOBILE('/apps/search'),
                     params={'platform': 'apps',
                             'filters': 'with-collections',
                             'term': search_query})
    j = json.loads(r.text)
    for collection in j['collections']:
        item = Listitem()
        if set_item_callback_based_on_type(item, collection['type'], collection):
            yield item


@Route.register
def categories(plugin, **kwargs):
    """
    List all ctagories
    (e.g. séries & fictions, documentaires, ...)
    This folder will also list videos that are not associated with any channel
    """
    categories = {
        'Séries & fictions': 'series-et-fictions',
        'Documentaires': 'documentaires',
        'Cinéma': 'films',
        'Info & société': 'actualites-et-societe',
        'Culture': 'spectacles-et-culture',
        'Sports': 'sport',
        'Jeux & divertissements': 'jeux-et-divertissements',
        'Art de vivre': 'vie-quotidienne',
        'Enfants': 'enfants'
    }

    for category_label, category_path in categories.items():
        item = Listitem()
        item.label = category_label
        item.set_callback(grab_json_collections, URL_API_MOBILE('/apps/categories/%s' % category_path))
        item_post_treatment(item)
        yield item


@Route.register
def outre_mer_root(plugin, region_path, **kwargs):
    menu_items = [
        (Script.localize(30704), '/generic/taxonomy/%s/contents'),  # Last videos
        (Script.localize(30717), '/apps/regions/%s/programs')  # All programs
    ]
    for menu_item in menu_items:
        item = Listitem()
        item.label = menu_item[0]
        item.set_callback(grab_json_collections, URL_API_MOBILE(menu_item[1] % region_path), page=0, collection_position=0)
        item_post_treatment(item)
        yield item


@Route.register
def list_generic_items(plugin, generic_items, next_page_item, **kwargs):
    """
    List items of a generic type
    """
    plugin.add_sort_methods(xbmcplugin.SORT_METHOD_UNSORTED)
    items = []
    for collection_item in generic_items:
        item = Listitem()
        if set_item_callback_based_on_type(item, collection_item['type'], collection_item):
            items.append(item)
    if next_page_item:
        items.append(next_page_item)
    return items


@Route.register
def grab_json_collections(plugin, json_url, page=0, collection_position=None, **kwargs):
    plugin.add_sort_methods(xbmcplugin.SORT_METHOD_UNSORTED)
    r = urlquick.get(json_url,
                     params={'platform': 'apps',
                             'page': str(page)})
    j = json.loads(r.text)
    cnt = -1
    items = []
    if 'collections' in j:
        collections = j['collections']
    else:
        collections = [j]
    for collection in collections:
        cnt = cnt + 1
        next_page_item = None
        if 'cursor' in collection:
            if 'next' in collection['cursor']:
                next_ = collection['cursor']['next']
                if next_:
                    next_page_item = Listitem.next_page(json_url,
                                                        page=next_,
                                                        collection_position=cnt)

        # If we are not in page 0, directly print items
        if collection_position is not None and cnt == collection_position:
            return list_generic_items(plugin, collection['items'], next_page_item)

        item = Listitem()
        if set_item_callback_based_on_type(item, collection['type'], collection, next_page_item):
            items.append(item)

    if 'item' in j:
        if 'program_path' in j['item'] or 'url_complete' in j['item']:
            if 'program_path' in j['item']:
                path = j['item']['program_path']
            elif 'url_complete' in j['item']:
                path = j['item']['url_complete']
            menu_items = [
                (Script.localize(30701), '/generic/taxonomy/%s/contents'),  # All videos
                (Script.localize(30717), '/apps/regions/%s/programs')  # All programs
            ]
            for menu_item in menu_items:
                item = Listitem()
                item.label = menu_item[0]
                item.set_callback(grab_json_collections, URL_API_MOBILE(menu_item[1] % path), page=0, collection_position=0)
                item_post_treatment(item)
                items.append(item)

    return items


@Resolver.register
def get_video_url(plugin,
                  broadcast_id=None,
                  id_yatta=None,
                  download_mode=False,
                  **kwargs):
    if id_yatta is not None:
        url_yatta_video = "standard/publish/contents/%s" % id_yatta
        resp = urlquick.get(URL_API_FRONT(url_yatta_video), max_age=-1)
        json_parser = json.loads(resp.text)
        for medium in json_parser['content_has_medias']:
            if "si_id" in medium['media']:
                broadcast_id = medium['media']['si_id']
                break

    return resolver_proxy.get_francetv_video_stream(plugin, broadcast_id, download_mode)


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):

    if item_id in ('spectacles-et-culture', 'france-2', 'france-3', 'france-4', 'france-5', 'franceinfo'):
        resp = urlquick.get(URL_LIVE % item_id, headers={'User-Agent': web_utils.get_random_ua()}, max_age=-1)
        broadcast_id = re.compile(r'videoId\"\:\"(.*?)\"', re.DOTALL).findall(resp.text)[0]
        return resolver_proxy.get_francetv_live_stream(plugin, broadcast_id)

    broadcast_id = 'SIM_France%s'
    return resolver_proxy.get_francetv_live_stream(plugin, broadcast_id % item_id.split('-')[1])
