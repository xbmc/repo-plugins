#!/usr/bin/env python
# -*- coding: utf-8; -*-

import urllib

import httplib2
from multipart import encode_multipart, BOUNDARY

class Http(httplib2.Http):
    """
    Subclass of Http that supports multipart style file uploading via POST as
    and cookies.
    """
    def request_with_files(self, url, method, body=None, body_files=None,
                           headers=None, *args, **kwargs):
        """
        Note: Unlike the standard request method, the body & body_files params
        to this method should *not* be urlencoded strings. They should instead
        be urlencodable objects (e.g. a dict), and will be urlencoded
        automatically by this method after the body files are processed.
        """
        if body_files:
            body = encode_multipart(body, body_files)
            headers["Content-type"] = \
                    "multipart/form-data; boundary=%s" % BOUNDARY
            headers["Content-length"] = str(len(body))
        else:
            body = urllib.urlencode(body)
            headers.setdefault("Content-type",
                               "application/x-www-form-urlencoded")

        return super(Http, self).request(url, method, body,
                                         headers, *args, **kwargs)
