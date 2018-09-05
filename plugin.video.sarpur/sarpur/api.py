#!/usr/bin/env python
# encoding: UTF-8

from urllib import quote

import requests
from sarpur import logger  # noqa

API_PATH = 'https://api.ruv.is/api'


def api_url(path):
    return u'{0}{1}'.format(API_PATH, path)


def search(query):
    """
    Search for media

    :param query: Query string
    :return: A list of dicts (or empty list)
    """
    search_url = api_url(
        u'/programs/search/tv/{0}'.format(
            quote(query, safe='')
        )
    )

    return requests.get(search_url).json()['programs']


def program_details(program_id):
    program_url = api_url('/programs/program/{0}/all'.format(program_id))

    return requests.get(program_url).json()
