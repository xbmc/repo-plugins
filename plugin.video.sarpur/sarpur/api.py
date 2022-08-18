#!/usr/bin/env python
# encoding: UTF-8

from __future__ import absolute_import
from urllib.parse import quote

import requests
from sarpur import logger  # noqa

API_PATH = 'https://api.ruv.is/api'


def api_url(path):
    return '{0}{1}'.format(API_PATH, path)


def search(query):
    """
    Search for media

    :param query: Query string
    :return: A list of dicts (or empty list)
    """
    search_url = api_url(
        '/programs/search/tv/{0}'.format(
            quote(query, safe='')
        )
    )

    return requests.get(search_url).json()['programs']


def program_details(program_id):
    program_url = api_url('/programs/program/{0}/all'.format(program_id))

    return requests.get(program_url).json()


def featured_panels():
    url = api_url('/programs/featured/tv/')
    return requests.get(url).json()['panels']


def panel_programs(slug):
    url = api_url('/programs/featured/tv/{0}'.format(slug))
    return requests.get(url).json()['programs']


def categories():
    url = api_url('/programs/categories/tv')
    return requests.get(url).json()['categories']


def category_programs(slug):
    url = api_url('/programs/category/tv/{0}'.format(slug))
    return requests.get(url).json()['programs']
