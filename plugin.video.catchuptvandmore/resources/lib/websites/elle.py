# -*- coding: utf-8 -*-
# Copyright: (c) 2017, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
import json
import re

from codequick import Listitem, Resolver, Route
import urlquick

from resources.lib import download
from resources.lib.menu_utils import item_post_treatment

URL_ROOT = 'http://www.elle.fr'

URL_CATEGORIES = URL_ROOT + '/Videos/'

URL_JS_CATEGORIES = 'https://cdn-elle.ladmedia.fr/js/compiled/showcase_bottom.min.js?version=%s'
# IdJsCategories

URL_VIDEOS_JSON = 'https://content.jwplatform.com/v2/playlists/%s'
# CategoryId


@Route.register
def website_root(plugin, item_id, **kwargs):
    """Add modes in the listing"""
    categories_html = urlquick.get(URL_CATEGORIES).text
    categories_js_id = re.compile(
        r'compiled\/showcase_bottom.min\.js\?version=(.*?)\"').findall(
            categories_html)[0]
    categories_js_html = urlquick.get(URL_JS_CATEGORIES %
                                      categories_js_id).text
    list_categories = re.compile(r'\!0\,playlistId\:\"(.*?)\"').findall(
        categories_js_html)

    for category_id in list_categories:

        data_categories_json = urlquick.get(URL_VIDEOS_JSON % category_id).text
        data_categories_jsonparser = json.loads(data_categories_json)
        category_name = data_categories_jsonparser["title"]

        item = Listitem()
        item.label = category_name

        item.set_callback(list_videos,
                          item_id=item_id,
                          category_id=category_id)
        item_post_treatment(item)
        yield item


@Route.register
def list_videos(plugin, item_id, category_id, **kwargs):
    """Build videos listing"""
    replay_episodes_json = urlquick.get(URL_VIDEOS_JSON % category_id).text
    replay_episodes_jsonparser = json.loads(replay_episodes_json)

    for episode in replay_episodes_jsonparser["playlist"]:
        item = Listitem()

        item.label = episode["title"]
        video_url = episode["sources"][0]["file"]
        item.art['thumb'] = item.art['landscape'] = episode["image"]
        item.info['info'] = episode["description"]

        item.set_callback(get_video_url,
                          item_id=item_id,
                          video_url=video_url)
        item_post_treatment(item, is_playable=True, is_downloadable=True)
        yield item


@Resolver.register
def get_video_url(plugin,
                  item_id,
                  video_url,
                  download_mode=False,
                  **kwargs):
    """Get video URL and start video player"""
    if download_mode:
        return download.download_video(video_url)

    return video_url
