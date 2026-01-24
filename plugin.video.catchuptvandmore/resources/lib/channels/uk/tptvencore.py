# -*- coding: utf-8 -*-
# Copyright: (c) 2025
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals

import json
import re
import requests
import urlquick
import uuid
from builtins import str
from codequick import Listitem, Script, Resolver, Route
from urllib.parse import quote

from resources.lib import resolver_proxy
from resources.lib.menu_utils import item_post_treatment

URL_ROOT = 'https://tptvencore.co.uk'
API_CLIENT = 'https://prod.suggestedtv.com/api/client'
TENANT = 'encore'
ANONYMOUS_TOKEN_URL = API_CLIENT + '/v1/session'
PREDICTIVE_SEARCH_URL = API_CLIENT + '/v2/search/{search_query}'
VIDEO_URL = API_CLIENT + '/v1/product/{product_id}/media/feature'
PRODUCTS_URL = API_CLIENT + '/v1/product'


def get_token():
    headers = {
        'api-key': 'zq5pyPd0RTbNg3Fyj52PrkKL9c2Af38HHh4itgZTKDaCzjAyhd',
        'content-type': 'application/json',
        'tenant': TENANT
    }

    token_response = requests.post(ANONYMOUS_TOKEN_URL, headers=headers, json={})

    if token_response.status_code == 200:
        return token_response.json()

    return None


HEADERS = {'session': get_token().get('id'), 'tenant': TENANT}


def get_products(product_ids):
    params = {
        'ids': ','.join(product_ids),
        'extend': 'label'
    }

    product_json = json.loads(urlquick.get(PRODUCTS_URL, headers=HEADERS, params=params, max_age=-1).text)
    return product_json


@Route.register(content_type='videos')
def do_search(plugin, search_query):
    search_json = json.loads(
        urlquick.get(PREDICTIVE_SEARCH_URL.format(search_query=quote(search_query)), headers=HEADERS, max_age=-1).text)
    if search_json:
        if 'data' in search_json:
            data = search_json.get('data', [])

            product_ = 'product_'
            product_ids = [item.replace(product_, '') for item in data if item.startswith(product_)]
            if product_ids:
                product_json = get_products(product_ids).get('data', [])
                if product_json:
                    for product in product_json:
                        if product:
                            listitem = Listitem()
                            listitem.label = product.get('name')
                            listitem.info['plot'] = product.get('description')
                            listitem.info['genre'] = product.get('categories')

                            image_template = product.get('links', {}).get('image')
                            image_rendition_id = product.get('image', {}).get('master', [])
                            image_url = get_image_url(image_template, image_rendition_id)
                            listitem.art['thumb'] = listitem.art['landscape'] = image_url

                            id = product.get('feature')
                            listitem.set_callback(get_video, product_id=id)
                            item_post_treatment(listitem)
                            yield listitem


def get_image_url(image_template, image_rendition_id):
    mode = 'fill'
    format = 'webp'
    width = 720
    height = 480
    image_url = image_template.format(imageRenditionId=image_rendition_id, mode=mode, format=format, width=width,
                                      height=height)
    return image_url


@Route.register
def main_menu(plugin, **kwargs):
    yield Listitem.search(do_search)


@Resolver.register
def get_video(plugin, product_id, **kwargs):
    playout_json = json.loads(urlquick.get(VIDEO_URL.format(product_id=product_id), headers=HEADERS, max_age=-1).text)

    brightcove = playout_json.get('brightcove', {})
    policy_key = brightcove.get('policyId')
    url = brightcove.get('url')
    match = re.search(r"accounts/(\d+)/videos/(\d+)", url)
    data_account = match.group(1)
    data_video_id = match.group(2)

    return resolver_proxy.get_brightcove_video_json(plugin, data_account, None, data_video_id, policy_key,
                                                    None, None)
