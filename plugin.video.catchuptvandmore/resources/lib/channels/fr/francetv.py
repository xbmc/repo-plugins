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

URL_ROOT = 'https://www.france.tv'
URL_API_MOBILE = utils.urljoin_partial("https://api-mobile.yatta.francetv.fr/")
URL_API_FRONT = utils.urljoin_partial("http://api-front.yatta.francetv.fr")


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
        ('channels/spectacles-et-culture', 'Culturebox', 'culturebox.png', 'culturebox_fanart.jpg'),
        ('categories/arte', 'Arte', '../wo/arte.png', '../wo/arte_fanart.jpg'),
        ('categories/lcp', 'LCP Assemblée Nationale', 'lcp.png', 'lcp_fanart.jpg'),
        ('categories/public-senat', 'Public Sénat', 'publicsenat.png', 'publicsenat_fanart.jpg'),
        ('categories/tv5-monde', 'TV5 Monde', '../wo/tv5monde.png', '../wo/tv5monde_fanart.jpg'),
        ('categories/france-24', 'France 24', 'france24.png', 'france24_fanart.jpg'),
        ('categories/ina', 'ina', '../../websites/ina.png', '../../websites/ina_fanart.jpg'),
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
    # type_id = [(#type_, #category, #path),]
    type_id = [
        ('program', 'program', 'program_path'),
        ('collection', 'collections', 'collection_path'),
        ('categorie', 'sub-categories', 'url_complete'),
        ('sous_categorie', 'sub-categories', 'url_complete'),
        ('event', 'events', 'url_complete'),
    ]

    # This is a new path
    for array in type_id:
        if type_ == array[0]:
            item.set_callback(grab_json_collections, URL_API_MOBILE('/apps/%s/%s' % (array[1], j[array[2]])))
            item_post_treatment(item)
            return True

    if type_ == 'region':
        marker = j.get('marker', None)
        zone = None
        if marker is not None:
            page = marker.get('page', None)
            if page is not None:
                zone = page.split('::')[0]
        if zone is None:
            item.set_callback(outre_mer_root, j['region_path'])
        else:
            if zone == 'region':
                path = j['region_path'] + '/metropole'
            else:
                path = j['region_path'] + '/outre-mer'
            item.set_callback(grab_json_collections, URL_API_MOBILE('/apps/regions/%s' % path))
        item_post_treatment(item)
        return True

    if type_ == 'categories':
        item.label = 'Les sous-catégories'
        item.set_callback(list_generic_items, j['items'], next_page_item)
        item_post_treatment(item)
        return True

    # This is a video
    if type_ == 'integrale' or type_ == 'extrait' or type_ == 'unitaire' or type_ == 'resume':
        si_id = populate_video_item(item, j)
        item.set_callback(get_video_url,
                          broadcast_id=si_id)
        item_post_treatment(item, is_playable=True, is_downloadable=True)
        return True

    # This is an article
    if type_ == 'article':
        array = []
        array.append(j)
        item.set_callback(list_generic_items, array, next_page_item)
        item_post_treatment(item)
        return True

    if type_ == 'dict' or type_ == 'live':
        return False

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
    item.info['duration'] = video.get('duration', '')

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
    r = urlquick.get(URL_API_MOBILE('/generic/homepage'),
                     params={'platform': 'apps_tv'})
    j = json.loads(r.text)
    j = j['collections']
    for array in j:
        if 'playlist_categories' == array['type']:
            for categorie in array['items']:
                item = Listitem()
                if 'images' in categorie:
                    populate_images(item, categorie['images'])
                item.label = categorie.get('label')
                item.set_callback(grab_json_collections, URL_API_MOBILE('/apps/categories/%s' % categorie.get('url_complete')))
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
    fallback_id = {
        "france-2": "006194ea-117d-4bcf-94a9-153d999c59ae",
        "france-3": "29bdf749-7082-4426-a4f3-595cc436aa0d",
        "france-4": "9a6a7670-dde9-4264-adbc-55b89558594b",
        "france-5": "45007886-f3ff-4b3e-9706-1ef1014c5a60",
        "franceinfo": "35be22fb-1569-43ff-857c-99bf81defa2e",
    }
    params = {'platform': 'apps'}
    resp = urlquick.get(URL_API_MOBILE('/apps/channels/%s' % item_id), params=params, max_age=-1)
    json_parser = json.loads(resp.text)

    for collection in json_parser['collections']:
        if 'live' == collection['type']:
            if "channel_path" in collection:
                channel_path = collection["items"][0]["channel"]["channel_path"]
                broadcast_id = collection["items"][0]["channel"]["si_id"]
            else:
                if item_id in fallback_id:
                    channel_path = item_id
                    broadcast_id = fallback_id[item_id]
                else:
                    plugin.notify('ERROR', plugin.localize(30716))
                    return False
            if channel_path == item_id:
                return resolver_proxy.get_francetv_live_stream(plugin, broadcast_id)


@Route.register
def get_multi_live_url(plugin, item_id, **kwargs):
    params = {'platform': 'apps'}
    resp = urlquick.get(URL_API_MOBILE('/generic/directs'), params=params, max_age=-1)
    json_parser = json.loads(resp.text)

    at_least_one_item = False
    for items in json_parser['items']:
        channel_program = channel_episode_title = ''
        item = Listitem()
        if items.get('channel'):
            if 'images' in items:
                populate_images(item, items['images'])
            channel_episode_title = items.get('episode_title', '')
            if items.get('program'):
                channel_program = items['program'].get('label', '')
                populate_images(item, items['program']['images'])
            channel_label = items['channel'].get("label")
            if channel_program and channel_episode_title:
                channel_label = channel_label + ' - ' + channel_program + ' - ' + channel_episode_title
            elif channel_program:
                channel_label = channel_label + ' - ' + channel_program
            elif channel_episode_title:
                channel_label = channel_label + ' - ' + channel_episode_title
            channel_id = items['channel'].get("si_id")

            at_least_one_item = True
            item.label = channel_label
            item.set_callback(get_multi_video_url, channel_id)
            item_post_treatment(item)
            yield item
        elif items.get('partner'):
            if 'images' in items:
                populate_images(item, items['images'])
            channel_episode_title = items.get('episode_title', '')
            if items.get('program'):
                channel_program = items['program'].get('label', '')
                populate_images(item, items['program']['images'])
            channel_label = items['partner'].get("label")
            if channel_program and channel_episode_title:
                channel_label = channel_label + ' - ' + channel_program + ' - ' + channel_episode_title
            elif channel_program:
                channel_label = channel_label + ' - ' + channel_program
            elif channel_episode_title:
                channel_label = channel_label + ' - ' + channel_episode_title
            channel_id = items['partner'].get("si_id")

            at_least_one_item = True
            item.label = channel_label
            item.set_callback(get_multi_video_url, channel_id)
            item_post_treatment(item)
            yield item

    if not at_least_one_item:
        item = Listitem()
        item.label = Script.localize(30896)
        yield item


@Resolver.register
def get_multi_video_url(plugin, channel_id, **kwargs):
    return resolver_proxy.get_francetv_live_stream(plugin, channel_id)
