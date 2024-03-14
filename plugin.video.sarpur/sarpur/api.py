#!/usr/bin/env python
# encoding: UTF-8

from __future__ import absolute_import

from urllib.parse import quote

import requests
from sarpur import logger  # noqa

API_PATH = "https://api.ruv.is/api"
GRAPHQL_URL = "https://spilari.nyr.ruv.is/gql/"


def api_url(path):
    return "{0}{1}".format(API_PATH, path)


def search(query, type="tv"):
    """
    Search for media

    :param query: Query string
    :return: A list of dicts (or empty list)
    """
    gql = {
        "operationName": "getSearch",
        "variables": f'{{"type":"{type}","text":"{query}"}}',
        "extensions": '{"persistedQuery":{"version":1,"sha256Hash":"99be6d8b3c99b265086df4b6d87e72d005bdbf1cf0d50173610632bc0ecf7ff5"}}',
    }
    req = requests.get(GRAPHQL_URL, headers={"Content-Type": "text/plain"}, params=gql)
    return req.json()["data"]["Search"]

    return requests.get(search_url).json()["programs"]


def program_details(program_id):
    program_url = api_url("/programs/program/{0}/all".format(program_id))

    return requests.get(program_url).json()


def featured_panels():
    url = api_url("/programs/featured/tv")
    return requests.get(url).json()["panels"]


def panel_programs(slug):
    url = api_url("/programs/featured/tv/{0}".format(slug))
    return requests.get(url).json()["programs"]


def categories():
    url = api_url("/programs/categories/tv")
    return requests.get(url).json()["categories"]


def category_programs(slug):
    url = api_url("/programs/category/tv/{0}".format(slug))
    return requests.get(url).json()["programs"]


def podcasts():
    url = "https://muninn.nyr.ruv.is/files/podcasts"
    return requests.get(url).json()["programs"]


def podcast_show(id):
    # For future use?
    gql = {
        "operationName": "getEpisode",
        "variables": f'{{"programID":{id}}}',
        "extensions": '{"persistedQuery":{"version":1,"sha256Hash":"f3f957a3a577be001eccf93a76cf2ae1b6d10c95e67305c56e4273279115bb93"}}',
    }
    req = requests.get(GRAPHQL_URL, headers={"Content-Type": "text/plain"}, params=gql)
    return req.json()["data"]["Program"]
