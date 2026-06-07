# -*- coding: utf-8 -*-
# Copyright: (c) 2017, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
from builtins import str
import json
import re

from codequick import Listitem, Resolver, Route
import urlquick

from kodi_six import xbmcgui
from resources.lib import resolver_proxy, web_utils
from resources.lib.menu_utils import item_post_treatment

# TO DO
# Info Videos (date, plot, etc ...)

URL_ROOT = 'https://www.tv5unis.ca'
# Channel Name

URL_COLLECTIONS = URL_ROOT + '/collections/%s'

URL_VIDEOS_SEASON = URL_ROOT + '/%s/saisons/%s'
# slug_program, number_season
URL_VIDEOS = URL_ROOT + '/%s'
# slug_program

# https://www.tv5unis.ca/videos/canot-cocasse/saisons/4/episodes/8
URL_STREAM_SEASON_EPISODE = URL_ROOT + '/videos/%s/saisons/%s/episodes/%s'
# slug_video, number_season, episode_number
URL_STREAM = URL_ROOT + '/videos/%s'
# slug_video

URL_API = 'https://api.tv5unis.ca/graphql'
GENERIC_HEADERS = {"User-Agent": web_utils.get_random_ua()}


@Route.register
def list_categories(plugin, item_id, **kwargs):
    """
    Build categories listing
    - Tous les programmes
    - Séries
    - Informations
    - ...
    """
    resp = urlquick.get(URL_ROOT, headers=GENERIC_HEADERS)
    json_datas = re.compile(
        r'\/json\"\>\{(.*?)\}\<\/script\>').findall(resp.text)[0]
    json_parser = json.loads('{' + json_datas + '}')

    json_entry = json_parser["props"]["apolloState"]
    for json_key in list(json_entry.keys()):
        if "__typename" in json_entry[json_key]:
            if "ProductSet" in json_entry[json_key]["__typename"]:
                if "slug" in json_entry[json_key]:
                    category_title = json_entry[json_key]["title"]
                    category_slug = json_entry[json_key]["slug"]

                    item = Listitem()
                    item.label = category_title
                    item.set_callback(list_programs, item_id=item_id, category_slug=category_slug)
                    item_post_treatment(item)
                    yield item


@Route.register
def list_programs(plugin, item_id, category_slug, **kwargs):
    resp = urlquick.get(URL_COLLECTIONS % category_slug, headers=GENERIC_HEADERS)

    json_datas = re.compile(
        r'\/json\"\>\{(.*?)\}\<\/script\>').findall(resp.text)[0]
    json_parser = json.loads('{' + json_datas + '}')

    json_entry = json_parser["props"]["apolloState"]
    already_listed = []
    for json_key in list(json_entry.keys()):
        if json_key not in already_listed and "Product:" in json_key and 'slug' in json_entry[json_key] and json_entry[json_key]['slug'] is not None:
            if "__typename" in json_entry[json_key] and json_entry[json_key]['__typename'] == 'Product':
                program_title = json_entry[json_key]["title"]
                product_type = None
                for info in list(json_entry.keys()):
                    cond = 'collection' in json_entry[info] and json_entry[info]['collection'] is not None and '__ref' in json_entry[info]['collection']
                    cond = cond and json_entry[info]['collection']['__ref'] == json_key and 'slug' in json_entry[info] and json_entry[info]['slug'] is None
                    if ('shortSummary' in json_entry[info]) and (info == json_key or cond):
                        description = json_entry[info]['shortSummary']
                        image_thumb = json.loads(re.compile(r'Image\:(.*?)$').findall(json_entry[info]["mainPortraitImage"]['__ref'])[0])['url']
                        image_landscape = json.loads(re.compile(r'Image\:(.*?)$').findall(json_entry[info]["mainLandscapeImage"]['__ref'])[0])['url']
                        present = [description, image_thumb, image_landscape]
                        if 'productType' in json_entry[info]:
                            product_type = json_entry[info]['productType']

                already_listed.append(json_key)

                item = Listitem()
                item.info['plot'] = description
                item.art['thumb'] = image_thumb
                item.art['landscape'] = image_landscape
                item.label = program_title
                if product_type == 'MOVIE':
                    item.set_callback(get_video_url, is_episode=False, video=json_entry[json_key]["slug"])
                else:
                    item.set_callback(list_seasons, video=json_entry[json_key]["slug"], present=present)
                item_post_treatment(item)
                yield item


@Route.register
def list_seasons(plugin, video, present, **kwargs):
    resp = urlquick.get(URL_VIDEOS % video, headers=GENERIC_HEADERS)
    root = resp.parse()
    for subject in root.iterfind(".//select[@class='gtm-season-dropdown']"):
        for option in subject.iterfind(".//option"):
            season_text = option.text
            season_number = option.get('value')
            item = Listitem()
            item.info['plot'] = present[0]
            item.art['thumb'] = present[1]
            item.art['landscape'] = present[2]
            item.label = season_text
            item.set_callback(list_episodes, video=video, season=season_number)
            item_post_treatment(item)
            yield item


@Route.register
def list_episodes(plugin, video, season, **kwargs):
    resp = urlquick.get(URL_VIDEOS_SEASON % (video, season), headers=GENERIC_HEADERS)
    json_datas = re.compile(
        r'\/json\"\>\{(.*?)\}\<\/script\>').findall(resp.text)[0]
    json_parser = json.loads('{' + json_datas + '}')

    json_entry = json_parser["props"]["apolloState"]
    for json_key in list(json_entry.keys()):
        if "Product:" in json_key:
            product = json_entry[json_key]
            if ('episodeNumber' in product) and (product['episodeNumber'] is not None):
                program_title = json_entry[json_key]["title"]
                description = json_entry[json_key]['shortSummary']
                image_landscape = json.loads(re.compile(r'Image\:(.*?)$').findall(json_entry[json_key]["mainLandscapeImage"]['__ref'])[0])['url']
                item = Listitem()
                item.info['plot'] = description
                item.art['thumb'] = item.art['landscape'] = image_landscape
                item.label = program_title
                item.set_callback(get_video_url, is_episode=True, video=video, season=season, episode=str(product['episodeNumber']))
                item_post_treatment(item)
                yield item

    return False


@Resolver.register
def get_video_url(plugin, is_episode, video, season=None, episode=None, download_mode=False, **kwargs):
    if is_episode:
        resp = urlquick.get(URL_STREAM_SEASON_EPISODE % (video, season, episode), headers=GENERIC_HEADERS)
    else:
        resp = urlquick.get(URL_STREAM % video, headers=GENERIC_HEADERS)

    json_datas = {
        'operationName': 'VideoPlayerPage',
        'variables': {},
        'query': 'query VideoPlayerPage($collectionSlug: String!, $seasonNumber: Int, $episodeNumber: Int) {\n  videoPlayerPage(\n    rootProductSlug: $collectionSlug\n    seasonNumber: $seasonNumber\n    episodeNumber: $episodeNumber\n  ) {\n    blocks {\n      id\n      blockType\n      ...PageMetaDataFragment\n      ... on ArtisanBlocksVideoPlayer {\n        blockConfiguration {\n          pauseAdsConfiguration\n          product {\n            ...ProductWithVideo\n            __typename\n          }\n          __typename\n        }\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n}\n\nfragment PageMetaDataFragment on ArtisanBlocksPageMetaData {\n  id\n  blockConfiguration {\n    pageMetaDataConfiguration {\n      title\n      description\n      keywords\n      language\n      canonicalUrl\n      jsonLd\n      robots\n      productMetaData {\n        title\n        seasonName\n        seasonNumber\n        episodeName\n        episodeNumber\n        category\n        channel\n        keywords\n        kind\n        fmcApplicationId\n        productionCompany\n        productionCountry\n        francolabObjective\n        francolabTargetAudience\n        francolabDifficulties\n        francolabThemes\n        __typename\n      }\n      ogTags {\n        property\n        content\n        __typename\n      }\n      adContext {\n        slug\n        channel\n        category\n        genre\n        keywords\n        productionCountry\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment ProductWithVideo on Product {\n  id\n  externalKey\n  title\n  slug\n  episodeNumber\n  seasonNumber\n  seasonName\n  productionCompany\n  productionCountry\n  productType\n  shortSummary\n  duration\n  tags\n  category {\n    id\n    label\n    __typename\n  }\n  collection {\n    id\n    title\n    slug\n    __typename\n  }\n  keywords {\n    label\n    __typename\n  }\n  kind {\n    label\n    __typename\n  }\n  mainLandscapeImage {\n    url\n    __typename\n  }\n  channel {\n    id\n    name\n    identity\n    __typename\n  }\n  nextViewableProduct {\n    id\n    slug\n    episodeNumber\n    seasonNumber\n    seasonName\n    productType\n    collection {\n      id\n      slug\n      __typename\n    }\n    __typename\n  }\n  rating {\n    id\n    type\n    __typename\n  }\n  season {\n    id\n    title\n    productionCompany\n    productionCountry\n    rating {\n      id\n      type\n      __typename\n    }\n    collection {\n      title\n      __typename\n    }\n    category {\n      label\n      __typename\n    }\n    keywords {\n      label\n      __typename\n    }\n    kind {\n      label\n      __typename\n    }\n    channel {\n      identity\n      __typename\n    }\n    __typename\n  }\n  trailerParent {\n    id\n    seasonNumber\n    episodeNumber\n    productionCompany\n    productionCountry\n    productType\n    slug\n    collection {\n      id\n      title\n      slug\n      __typename\n    }\n    category {\n      label\n      __typename\n    }\n    keywords {\n      label\n      __typename\n    }\n    kind {\n      label\n      __typename\n    }\n    channel {\n      identity\n      __typename\n    }\n    __typename\n  }\n  videoElement {\n    ... on Video {\n      id\n      duration\n      mediaId\n      creditsTimestamp\n      ads {\n        format\n        url\n        __typename\n      }\n      encodings {\n        dash {\n          url\n          __typename\n        }\n        hls {\n          url\n          __typename\n        }\n        progressive {\n          url\n          __typename\n        }\n        smooth {\n          url\n          __typename\n        }\n        __typename\n      }\n      subtitles {\n        language\n        url\n        __typename\n      }\n      __typename\n    }\n    ... on RestrictedVideo {\n      mediaId\n      code\n      reason\n      __typename\n    }\n    __typename\n  }\n  upcomingBroadcasts {\n    id\n    startsAt\n    __typename\n  }\n  activeNonLinearProgram {\n    id\n    startsAt\n    __typename\n  }\n  viewedProgress {\n    id\n    timestamp\n    __typename\n  }\n  __typename\n}',
    }

    dic_variables = {}
    variables = json.loads(re.compile(r'\"query\"\:(.*?)\}').findall(resp.text)[0] + '}')
    if 'episodeNumber' in variables.keys():
        dic_variables['episodeNumber'] = int(variables['episodeNumber'])
    if 'seasonNumber' in variables.keys():
        dic_variables['seasonNumber'] = int(variables['seasonNumber'])
    if 'collectionSlug' in variables.keys():
        dic_variables['collectionSlug'] = variables['collectionSlug']
    json_datas['variables'] = dic_variables

    resp = urlquick.post(URL_API, headers=GENERIC_HEADERS, json=json_datas, max_age=-1)
    data = json.loads(resp.text)
    if data['data']['videoPlayerPage']['blocks'][1]['blockConfiguration']['product']['videoElement']['__typename'] == 'RestrictedVideo':
        xbmcgui.Dialog().ok(
            'Info',
            'The video content is not available in your country due to a restriction by territories')
        return False
    video_url = data['data']['videoPlayerPage']['blocks'][1]['blockConfiguration']['product']['videoElement']['encodings']['hls']['url']

    return resolver_proxy.get_stream_with_quality(plugin, video_url)
