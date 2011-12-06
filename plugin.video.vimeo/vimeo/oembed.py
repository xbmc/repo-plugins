#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Module to interface with the oEmbed portion of the Vimeo API.
"""
from urllib import urlencode
from httplib2 import Http

from . import XMLProcessor, JSONProcessor, FormatProcessor, DEFAULT_HEADERS


OEMBED_BASE_URL = "http://vimeo.com/api/oembed"

class VimeoOEmbedClient(object):
    """
    This class specifically interacts with the oEmbed API provided by Vimeo.

    To query the API for the oEmbed code, call the get_oembed method. For a
    list of available arguments, check the API documentation (currently at
    http://vimeo.com/api/docs/oembed).

    When instantiating, the available arguments are:

        format (default: "xml"):
            Specifies the default response format. Currently, the available
            choices are XML and JSON, but check the API documentation for other
            potential options. Can be overridden on an individual API call
            basis.
    """
    _processors = {"xml" : XMLProcessor(),
                   "json" : JSONProcessor()}

    def __init__(self, format="xml"):
        self.default_response_format = format

    def _get_default_response_format(self):
        return self._default_response_format.lower()

    def _set_default_response_format(self, value):
        self._default_response_format = value.lower()

    default_response_format = property(_get_default_response_format, _set_default_response_format)

    def get_oembed(self, **params):
        format = params.pop("format", self.default_response_format).lower()
        processor = self._processors.get(format, FormatProcessor())
        uri = "{0}.{1}?{2}".format(OEMBED_BASE_URL, format, urlencode(params))

        return processor(*Http().request(uri))
