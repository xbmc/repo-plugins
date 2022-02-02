# -*- coding: utf-8 -*-
""" Search API """

from __future__ import absolute_import, division, unicode_literals

import json
import logging

import requests

from resources.lib import kodiutils
from resources.lib.viervijfzes.content import CACHE_ONLY, ContentApi, Program

_LOGGER = logging.getLogger(__name__)


class SearchApi:
    """ GoPlay Search API """
    API_ENDPOINT = 'https://api.goplay.be/search'

    def __init__(self):
        """ Initialise object """
        self._api = ContentApi(None, cache_path=kodiutils.get_cache_path())
        self._session = requests.session()

    def search(self, query):
        """ Get the stream URL to use for this video.
        :type query: str
        :rtype list[Program]
        """
        if not query:
            return []

        response = self._session.post(
            self.API_ENDPOINT,
            json={
                "query": query,
                "page": 0,
                "mode": "programs"
            }
        )
        _LOGGER.debug(response.content)
        response.raise_for_status()

        data = json.loads(response.text)

        results = []
        for hit in data['hits']['hits']:
            if hit['_source']['bundle'] == 'program':
                path = hit['_source']['url'].split('/')[-1]
                program = self._api.get_program(path, cache=CACHE_ONLY)
                if program:
                    results.append(program)
                else:
                    results.append(Program(
                        path=path,
                        title=hit['_source']['title'],
                        description=hit['_source']['intro'],
                        poster=hit['_source']['img'],
                    ))

        return results
