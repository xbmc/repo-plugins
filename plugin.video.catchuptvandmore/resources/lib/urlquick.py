#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# The MIT License (MIT)
#
# Copyright (c) 2017 William Forde
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
# the Software, and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
# FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
# COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
# IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

"""
Urlquick
--------
A light-weight http client with requests like interface. Featuring persistent connections and caching support.
This project was originally created for use by Kodi add-ons, but has grown into something more.
I found, that while requests has a very nice interface, there was a noticeable lag when importing the library.
The other option available is to use urllib2, but then you loose the benefit of persistent connections that requests
have. Hence the reason for this project.

All GET, HEAD and POST requests are cached locally for a period of 4 hours. When the cache expires,
conditional headers are added to a new request e.g. "Etag" and "Last-modified". Then if the server
returns a 304 Not-Modified response, the cache is reused, saving having to re-download the content body.

Inspired by: urlfetch & requests
urlfetch: https://github.com/ifduyue/urlfetch
requests: http://docs.python-requests.org/en/master/

Github: https://github.com/willforde/urlquick
Documentation: http://urlquick.readthedocs.io/en/stable/?badge=stable
Testing: https://travis-ci.org/willforde/urlquick
Code Coverage: https://coveralls.io/github/willforde/urlquick?branch=master
Code Quality: https://app.codacy.com/app/willforde/urlquick/dashboard
"""

__all__ = ["request", "get", "head", "post", "put", "patch", "delete", "cache_cleanup", "Session"]
__version__ = "0.9.4"

# Standard library imports
from codecs import open as _open, getencoder
from base64 import b64encode, b64decode
from collections import defaultdict
from datetime import datetime
import json as _json
import logging
import hashlib
import socket
import time
import zlib
import ssl
import sys
import re
import os

# Check python version to set the object that can detect non unicode strings
py3 = sys.version_info >= (3, 0)
if py3:
    # noinspection PyUnresolvedReferences, PyCompatibility
    from http.client import HTTPConnection, HTTPSConnection, HTTPException
    # noinspection PyUnresolvedReferences, PyCompatibility
    from urllib.parse import urlsplit, urlunsplit, urljoin, SplitResult, urlencode, parse_qsl, quote, unquote
    # noinspection PyUnresolvedReferences, PyCompatibility
    from http.cookies import SimpleCookie
    # noinspection PyUnresolvedReferences, PyCompatibility
    from collections.abc import MutableMapping

    # Under kodi this constant is set to the addon data directory
    # code for whitch is at the bottom of this file
    CACHE_LOCATION = os.getcwd()

    # noinspection PyShadowingBuiltins
    unicode = str
else:
    # noinspection PyUnresolvedReferences, PyCompatibility
    from httplib import HTTPConnection, HTTPSConnection, HTTPException
    # noinspection PyUnresolvedReferences, PyCompatibility
    from urlparse import urlsplit, urlunsplit, urljoin, SplitResult, parse_qsl as _parse_qsl
    # noinspection PyUnresolvedReferences, PyCompatibility
    from urllib import urlencode as _urlencode, quote as _quote, unquote as _unquote
    # noinspection PyUnresolvedReferences, PyCompatibility
    from Cookie import SimpleCookie
    # noinspection PyUnresolvedReferences, PyCompatibility
    from collections import MutableMapping

    # Under kodi this constant is set to the addon data directory
    # code for whitch is at the bottom of this file
    CACHE_LOCATION = os.getcwdu()


    def quote(data, safe=b"/", encoding="utf8", errors="strict"):
        data = data.encode(encoding, errors)
        return _quote(data, safe).decode("ascii")


    def unquote(data, encoding="utf-8", errors="replace"):
        data = data.encode("ascii", errors)
        return _unquote(data).decode(encoding, errors)


    def parse_qsl(qs, encoding="utf8", errors="replace", **kwargs):
        qs = qs.encode(encoding, errors)
        qsl = _parse_qsl(qs, **kwargs)
        return [(k.decode(encoding, errors), v.decode(encoding, errors)) for k, v in qsl]  # pragma: no branch


    def urlencode(query, doseq=False, encoding="utf8", errors=""):
        # Fetch items as a tuple of (key, value)
        items = query.items() if hasattr(query, "items") else query
        new_query = []

        # Process the items and encode unicode strings
        for key, value in items:
            key = key.encode(encoding, errors)
            if isinstance(value, (list, tuple)):
                value = [_value.encode(encoding, errors) for _value in value]  # pragma: no branch
            else:
                value = value.encode(encoding, errors)
            new_query.append((key, value))

        # Decode the output of urlencode back into unicode and return
        return _urlencode(new_query, doseq).decode("ascii")

# Cacheable request types
CACHEABLE_METHODS = (u"GET", u"HEAD", u"POST")
CACHEABLE_CODES = (200, 203, 204, 300, 301, 302, 303, 307, 308, 410, 414)
REDIRECT_CODES = (301, 302, 303, 307, 308)

#: The default max age of the cache in seconds is used when no max age is given in request.
MAX_AGE = 14400  # 4 Hours

# Unique logger for this module
logger = logging.getLogger("urlquick")


class UrlError(IOError):
    """Base exception. All exceptions and errors will subclass from this."""


class Timeout(UrlError):
    """Request timed out."""


class MaxRedirects(UrlError):
    """Too many redirects."""


class ContentError(UrlError):
    """Failed to decode content."""


class ConnError(UrlError):
    """A Connection error occurred."""


class SSLError(ConnError):
    """An SSL error occurred."""


class HTTPError(UrlError):
    """Raised when HTTP error occurs."""

    def __init__(self, url, code, msg, hdrs):
        self.code = code
        self.msg = msg
        self.hdrs = hdrs
        self.filename = url

    def __str__(self):
        error_type = "Client" if self.code < 500 else "Server"
        return "HTTP {} Error {}: {}".format(error_type, self.code, self.msg)


class MissingDependency(ImportError):
    """Missing optional Dependency 'HTMLement'"""


class CaseInsensitiveDict(MutableMapping):
    """
    A case-insensitive `dict` like object.

    Credit goes to requests for this code
    http://docs.python-requests.org/en/master/
    """

    def __init__(self, *args):
        self._store = {}
        for _dict in args:
            if _dict:
                self.update(_dict)

    def __repr__(self):
        return str(dict(self.items()))

    def __setitem__(self, key, value):
        if value is not None:
            key = make_unicode(key, "ascii")
            value = make_unicode(value, "iso-8859-1")
            self._store[key.lower()] = (key, value)

    def __getitem__(self, key):
        return self._store[key.lower()][1]

    def __delitem__(self, key):
        del self._store[key.lower()]

    def __iter__(self):
        return (casedkey for casedkey, _ in self._store.values())

    def __len__(self):
        return len(self._store)

    def copy(self):
        """Return a shallow copy of the case-insensitive dictionary."""
        return CaseInsensitiveDict(self._store.values())


class CachedProperty(object):
    """
    Cached property.

    A property that is only computed once per instance and then replaces
    itself with an ordinary attribute. Deleting the attribute resets the
    property.
    """

    def __init__(self, fget=None):
        self.__get = fget
        self.__doc__ = fget.__doc__
        self.__name__ = fget.__name__
        self.__module__ = fget.__module__
        self.allow_setter = False

    def __get__(self, instance, owner):
        try:
            return instance.__dict__[self.__name__]
        except KeyError:
            value = instance.__dict__[self.__name__] = self.__get(instance)
            return value

    def __set__(self, instance, value):
        if self.allow_setter:
            instance.__dict__[self.__name__] = value
        else:
            raise AttributeError("Can't set attribute")

    def __delete__(self, instance):
        instance.__dict__.pop(self.__name__, None)


class CacheHandler(object):
    def __init__(self, uid, max_age=MAX_AGE):
        self.max_age = max_age
        self.response = None

        # Filepath to cache file
        cache_dir = self.cache_dir()
        self.cache_file = cache_file = os.path.join(cache_dir, uid)
        if os.path.exists(cache_file):
            self.response = self._load()
            if self.response is None:
                self.delete(cache_file)

    @classmethod
    def cache_dir(cls):
        """Returns the cache directory."""
        cache_dir = cls.safe_path(os.path.join(CACHE_LOCATION, u".cache"))
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
        return cache_dir

    @staticmethod
    def delete(cache_path):
        """Delete cache from disk."""
        try:
            os.remove(cache_path)
        except EnvironmentError:
            logger.error("Faild to remove cache: %s", cache_path)
        else:
            logger.debug("Removed cache: %s", cache_path)

    @staticmethod
    def isfilefresh(cache_path, max_age):
        return (time.time() - os.stat(cache_path).st_mtime) < max_age

    def isfresh(self):
        """Return True if cache is fresh else False."""
        # Check that the response is of status 301 or that the cache is not older than the max age
        if self.response.status in (301, 308, 414) or self.max_age == -1:
            return True
        elif self.max_age == 0:
            return False
        else:
            return self.isfilefresh(self.cache_file, self.max_age)

    def reset_timestamp(self):
        """Reset the last modified timestamp to current time."""
        os.utime(self.cache_file, None)

    def add_conditional_headers(self, headers):
        """Return a dict of conditional headers from cache."""
        # Fetch cached headers
        cached_headers = self.response.headers

        # Check for conditional headers
        if u"Etag" in cached_headers:
            logger.debug("Found conditional header: ETag = %s", cached_headers[u"ETag"])
            headers[u"If-none-match"] = cached_headers[u"ETag"]

        if u"Last-modified" in cached_headers:
            logger.debug("Found conditional header: Last-Modified = %s", cached_headers[u"Last-modified"])
            headers[u"If-modified-since"] = cached_headers[u"Last-Modified"]

    def update(self, headers, body, status, reason, version=11, strict=True):
        # Convert headers into a Case Insensitive Dict
        headers = CaseInsensitiveDict(headers)

        # Remove Transfer-Encoding from header if exists
        if u"Transfer-Encoding" in headers:
            del headers[u"Transfer-Encoding"]

        # Ensure that reason is unicode
        # noinspection PyArgumentList
        reason = unicode(reason)

        # Create response data structure
        self.response = CacheResponse(headers, body, status, reason, version, strict)

        # Save response to disk
        self._save(headers=dict(headers), body=body, status=status, reason=reason, version=version, strict=strict)

    def _load(self):
        """Load the cache response that is stored on disk."""
        try:
            # Atempt to read the raw cache data
            with _open(self.cache_file, "rb", encoding="utf8") as stream:
                json_data = _json.load(stream)

        except (IOError, OSError):
            logger.exception("Cache Error: Failed to read cached response.")
            return None

        except TypeError:
            logger.exception("Cache Error: Failed to deserialize cached response.")
            return None

        # Decode body content using base64
        json_data[u"body"] = b64decode(json_data[u"body"].encode("ascii"))
        json_data[u"headers"] = CaseInsensitiveDict(json_data[u"headers"])
        return CacheResponse(**json_data)

    def _save(self, **response):
        # Base64 encode the body to make it json serializable
        response[u"body"] = b64encode(response["body"]).decode("ascii")

        try:
            # Save the response to disk using json Serialization
            with _open(self.cache_file, "wb", encoding="utf8") as stream:
                _json.dump(response, stream, indent=4, separators=(",", ":"))

        except (IOError, OSError):
            logger.exception("Cache Error: Failed to write response to cache.")
            self.delete(self.cache_file)

        except TypeError:
            logger.exception("Cache Error: Failed to serialize response.")
            self.delete(self.cache_file)

    @staticmethod
    def safe_path(path):
        """
        Convert path into a encoding that best suits the platform os.
        Unicode when on windows and utf8 when on linux/bsd.

        :type path: str
        :param path: The path to convert.
        :return: Returns the path as unicode or utf8 encoded str.
        """
        # Notting needs to be down if on windows as windows works well with unicode already
        # We only want to convert to bytes when we are on linux.
        if not sys.platform.startswith("win"):
            path = path.encode("utf8")
        return path

    @classmethod
    def hash_url(cls, url, data=None):
        """Return url as a sha1 encoded hash."""
        # Make sure that url is of type bites
        if isinstance(url, unicode):
            url = url.encode("utf8")

        if data:
            # Make sure that data is of type bites
            if isinstance(data, unicode):
                data = data.encode("utf8")
            url += data

        # Convert hashed url to unicode
        urlhash = hashlib.sha1(url).hexdigest()
        if isinstance(urlhash, bytes):
            urlhash = unicode(urlhash)

        # Append urlhash to the filename
        return cls.safe_path(u"cache-{}".format(urlhash))

    @classmethod
    def from_url(cls, url, data=None, max_age=MAX_AGE):
        """Initialize CacheHandler with url instead of uid."""
        uid = cls.hash_url(url, data)
        return cls(uid, max_age)

    def __bool__(self):
        return self.response is not None

    def __nonzero__(self):
        return self.response is not None


class CacheAdapter(object):
    def __init__(self):
        self.__cache = None

    def cache_check(self, method, url, data, headers, max_age=None):
        # Fetch max age from request header
        max_age = max_age if max_age is not None else int(headers.pop(u"x-max-age", MAX_AGE))
        if method == u"OPTIONS":
            return None

        # Check if cache exists first
        self.__cache = cache = CacheHandler.from_url(url, data, max_age)
        if cache:
            if method in ("PUT", "DELETE"):
                logger.debug("Cache purged, %s request invalidates cache", method)
                cache.delete(cache.cache_file)

            elif cache.isfresh():
                logger.debug("Cache is fresh, returning cached response")
                return cache.response

            else:
                logger.debug("Cache is stale, checking for conditional headers")
                cache.add_conditional_headers(headers)

    def handle_response(self, method, status, callback):
        if status == 304:
            logger.debug("Server return 304 Not Modified response, using cached response")
            callback()
            self.__cache.reset_timestamp()
            return self.__cache.response

        # Cache any cachable response
        elif status in CACHEABLE_CODES and method.upper() in CACHEABLE_METHODS:
            response = callback()
            logger.debug("Caching %s %s response", status, response[3])

            # Save response to cache and return the cached response
            self.__cache.update(*response)
            return self.__cache.response


class CacheResponse(object):
    """A mock HTTPResponse class"""

    def __init__(self, headers, body, status, reason, version=11, strict=True):
        self.headers = headers
        self.status = status
        self.reason = reason
        self.version = version
        self.strict = strict
        self.body = body

    def getheaders(self):
        """Return the response headers"""
        return self.headers

    def read(self):
        """Return the body of the response"""
        return self.body

    def close(self):
        pass


class ConnectionManager(CacheAdapter):
    def __init__(self):
        self.request_handler = {"http": {}, "https": {}}
        super(ConnectionManager, self).__init__()

    def make_request(self, req, timeout, verify, max_age):
        # Only check cache if max_age set to a valid value
        if max_age >= 0:
            cached_resp = self.cache_check(req.method, req.url, req.data, req.headers, max_age=max_age)
            if cached_resp:
                return cached_resp

            def callback():
                return resp.getheaders(), resp.read(), resp.status, resp.reason

            # Request resource and cache it if possible
            resp = self.connect(req, timeout, verify)
            cached_resp = self.handle_response(req.method, resp.status, callback)
            if cached_resp:
                return cached_resp
            else:
                return resp

        # Default to un-cached response
        return self.connect(req, timeout, verify)

    def connect(self, req, timeout, verify):
        # Fetch connection from pool and attempt to reuse if available
        pool = self.request_handler[req.type]
        if req.host in pool:
            try:
                # noinspection PyTypeChecker
                return self.send_request(pool[req.host], req)
            except Exception as e:
                # Remove the connection from the pool as it's unusable
                pool[req.host].close()
                del pool[req.host]

                # Raise the exception if it's not a subclass of UrlError
                if not isinstance(e, UrlError):
                    raise

        # Create a new connection
        if req.type == "https":
            # noinspection PyProtectedMember
            context = ssl._create_unverified_context() if verify is False else None
            conn = HTTPSConnection(req.host, timeout=timeout, context=context)
        else:
            conn = HTTPConnection(req.host, timeout=timeout)

        # Make first connection to server
        response = self.send_request(conn, req)

        # Add connection to the pool if the response is not set to close
        if not response.will_close:
            pool[req.host] = conn
        return response

    @staticmethod
    def send_request(conn, req):
        try:
            # Setup request
            conn.putrequest(str(req.method), str(req.selector), skip_host=1, skip_accept_encoding=1)

            # Add all headers to request
            for hdr, value in req.header_items():
                conn.putheader(hdr, value)

            # Send the body of the request witch will initiate the connection
            conn.endheaders(req.data)
            return conn.getresponse()

        except socket.timeout as e:
            raise Timeout(e)

        except ssl.SSLError as e:
            raise SSLError(e)

        except (socket.error, HTTPException) as e:
            raise ConnError(e)

    def close(self):
        """Close all persistent connections and remove."""
        for pool in self.request_handler.values():
            for key in list(pool.keys()):
                conn = pool.pop(key)
                conn.close()


class Request(object):
    """A Request Object"""

    def __init__(self, method, url, headers, data=None, json=None, params=None, referer=None):
        #: Tuple of (username, password) for basic authentication.
        self.auth = None

        # Convert url into a fully ascii unicode string using urlencoding
        self._referer_url = referer
        self._urlparts = urlparts = self._parse_url(url, params)

        # Ensure that method is always unicode
        if isinstance(method, bytes):
            method = method.decode("ascii")

        #: The URI scheme.
        self.type = urlparts.scheme
        #: The HTTP request method to use.
        self.method = method.upper()
        #: Dictionary of HTTP headers.
        self.headers = headers = headers.copy()
        #: Urlencoded url of the remote resource.
        self.url = urlunsplit((urlparts.scheme, urlparts.netloc, urlparts.path, urlparts.query, urlparts.fragment))
        #: The URI authority, typically a host, but may also contain a port separated by a colon.
        self.host = urlparts.netloc.lower()

        # Add Referer header if not the original request
        if referer:
            self.headers[u"Referer"] = referer

        # Add host header to be compliant with HTTP/1.1
        if u"Host" not in headers:
            self.headers[u"Host"] = self._urlparts.hostname

        # Construct post data from a json object
        if json:
            self.headers[u"Content-Type"] = u"application/json"
            data = _json.dumps(json)

        if data:
            # Convert data into a urlencode string if data is a dict
            if isinstance(data, dict):
                self.headers[u"Content-Type"] = u"application/x-www-form-urlencoded"
                data = urlencode(data, True).encode("utf8")
            elif isinstance(data, unicode):
                data = data.encode("utf8")

            if u"Content-Length" not in headers:
                # noinspection PyArgumentList
                self.headers[u"Content-Length"] = unicode(len(data))

        #: Request body, to send to the server.
        self.data = data

    def _parse_url(self, url, params=None, scheme=u"http"):
        """
        Parse a URL into it's individual components.

        :param str url: Url to parse
        :param dict params: params to add to url as query
        :return: A 5-tuple of URL components
        :rtype: urllib.parse.SplitResult
        """
        # Make sure we have unicode
        if isinstance(url, bytes):
            url = url.decode("utf8")

        # Check for valid url structure
        if not url[:4] == u"http":
            if self._referer_url:
                url = urljoin(self._referer_url, url, allow_fragments=False)

            elif url[:3] == u"://":
                url = url[1:]

        # Parse the url into each element
        scheme, netloc, path, query, _ = urlsplit(url.replace(u" ", u"%20"), scheme=scheme)
        if scheme not in ("http", "https"):
            raise ValueError("Unsupported scheme: {}".format(scheme))

        # Insure that all element of the url can be encoded into ascii
        self.auth, netloc = self._ascii_netloc(netloc)
        path = self._ascii_path(path) if path else u"/"
        query = self._ascii_query(query, params)

        # noinspection PyArgumentList
        return SplitResult(scheme, netloc, path, query, u"")

    @staticmethod
    def _ascii_netloc(netloc):
        """Make sure that host is ascii compatible."""
        auth = None
        if u"@" in netloc:
            # Extract auth
            auth, netloc = netloc.rsplit(u"@", 1)
            if u":" in auth:
                auth = tuple(auth.split(u":", 1))
            else:
                auth = (auth, u"")

        return auth, netloc.encode("idna").decode("ascii")

    @staticmethod
    def _ascii_path(path):
        """Make sure that path is url encoded and ascii compatible."""
        try:
            # If this statement passes then path must contain only ascii characters
            return path.encode("ascii").decode("ascii")
        except UnicodeEncodeError:
            # Path must contain non ascii characters
            return quote(path)

    @staticmethod
    def _ascii_query(query, params):
        """Make sure that query is urlencoded and ascii compatible."""
        if query:
            # Ensure that query contains only valid characters
            qsl = parse_qsl(query, keep_blank_values=True)
            query = urlencode(qsl)

        if query and params:
            extra_query = urlencode(params, doseq=True)
            return u"{}&{}".format(query, extra_query)
        elif params:
            return urlencode(params, doseq=True)
        elif query:
            return query
        else:
            return u""

    @property
    def selector(self):
        """Resource selector, with the url path and query parts."""
        if self._urlparts.query:
            return u"{}?{}".format(self._urlparts.path, self._urlparts.query)
        else:
            return self._urlparts.path

    def header_items(self):
        """Return list of tuples (header_name, header_value) of the Request headers, as native type of :class:`str`."""
        if py3:
            return self.headers.items()
        else:
            return self._py2_header_items()

    def _py2_header_items(self):
        """Return request headers with no unicode value to be compatible with python2"""
        # noinspection PyCompatibility
        for key, value in self.headers.iteritems():
            key = key.encode("ascii")
            value = value.encode("iso-8859-1")
            yield key, value


class UnicodeDict(dict):
    def __init__(self, *mappings):
        super(UnicodeDict, self).__init__()
        for mapping in mappings:
            if mapping:
                # noinspection PyUnresolvedReferences
                for key, value in mapping.items():
                    if value is not None:
                        key = make_unicode(key)
                        value = make_unicode(value)
                        self[key] = value


def make_unicode(data, encoding="utf8", errors=""):
    """Ensure that data is a unicode string"""
    if isinstance(data, bytes):
        return data.decode(encoding, errors)
    else:
        # noinspection PyArgumentList
        return unicode(data)


# ########################## Public API ##########################


class Session(ConnectionManager):
    """
    Provides cookie persistence and connection-pooling plus configuration.

    :param kwargs: Default configuration for session variables.

    :ivar int max_repeats: Max number of repeat redirects. Defaults to `4`
    :ivar int max_redirects: Max number of redirects. Defaults to `10`
    :ivar bool allow_redirects: Enable/disable redirection. Defaults to ``True``
    :ivar bool raise_for_status: Raise HTTPError if status code is > 400. Defaults to ``False``
    :ivar int max_age: Max age the cache can be, before it’s considered stale. -1 will disable caching.
                       Defaults to :data:`MAX_AGE <urlquick.MAX_AGE>`
    """
    # This is here so the kodi related code can change
    # this value to True for a better kodi expereance.
    default_raise_for_status = False

    def __init__(self, **kwargs):
        super(Session, self).__init__()
        self._headers = CaseInsensitiveDict()

        # Set Default headers
        self._headers[u"Accept"] = u"*/*"
        self._headers[u"Accept-Encoding"] = u"gzip, deflate"
        self._headers[u"Accept-language"] = u"en-gb,en-us,en"
        self._headers[u"Connection"] = u"keep-alive"

        # Session Controls
        self._cm = ConnectionManager()
        self._cookies = dict()
        self._params = dict()
        self._auth = None

        # Set session configuration settings
        self.max_age = kwargs.get("max_age", MAX_AGE)
        self.max_repeats = kwargs.get("max_repeats", 4)
        self.max_redirects = kwargs.get("max_redirects", 10)
        self.allow_redirects = kwargs.get("allow_redirects", True)
        self.raise_for_status = kwargs.get("raise_for_status", self.default_raise_for_status)

    @property
    def auth(self):
        """
        Default Authentication tuple to attach to Request.

        :return: Default authentication tuple.
        :rtype: tuple
        """
        return self._auth

    @auth.setter
    def auth(self, value):
        """Set Default Authentication tuple."""
        if isinstance(value, (tuple, list)):
            self._auth = value
        else:
            raise ValueError("Invalid type: {}, dict required".format(type(value)))

    @property
    def cookies(self):
        """
        Dictionary of cookies to attach to each request.

        :return: Session cookies
        :rtype: dict
        """
        return self._cookies

    @cookies.setter
    def cookies(self, _dict):
        """Replace session cookies with new cookies dict"""
        if isinstance(_dict, dict):
            self._cookies = _dict
        else:
            raise ValueError("Invalid type: {}, dict required".format(type(_dict)))

    @property
    def headers(self):
        """
        Dictionary of headers to attach to each request.

        :return: Session headers
        :rtype: dict
        """
        return self._headers

    @property
    def params(self):
        """
        Dictionary of querystrings to attach to each Request. The dictionary values
        may be lists for representing multivalued query parameters.

        :return: Session params
        :rtype: dict
        """
        return self._params

    @params.setter
    def params(self, _dict):
        """Replace session params with new params dict"""
        if isinstance(_dict, dict):
            self._params = _dict
        else:
            raise ValueError("Invalid type: {}, dict required".format(type(_dict)))

    def get(self, url, params=None, **kwargs):
        """
        Sends a GET request.

        Requests data from a specified resource.

        :param str url: Url of the remote resource.
        :param dict params: [opt] Dictionary of url query key/value pairs.
        :param kwargs: Optional arguments that :func:`request <urlquick.request>` takes.

        :return: A requests like Response object.
        :rtype: urlquick.Response
        """
        kwargs["params"] = params
        return self.request(u"GET", url, **kwargs)

    def head(self, url, **kwargs):
        """
        Sends a HEAD request.

        Same as GET but returns only HTTP headers and no document body.

        :param str url: Url of the remote resource.
        :param kwargs: Optional arguments that :func:`request <urlquick.request>` takes.

        :return: A requests like Response object.
        :rtype: urlquick.Response
        """
        return self.request(u"HEAD", url, **kwargs)

    def post(self, url, data=None, json=None, **kwargs):
        """
        Sends a POST request.

        Submits data to be processed to a specified resource.

        :param str url: Url of the remote resource.
        :param data: [opt] Dictionary (will be form-encoded) or bytes sent in the body of the Request.
        :param json: [opt] Json data sent in the body of the Request.
        :param kwargs: Optional arguments that :func:`request <urlquick.request>` takes.

        :return: A requests like Response object.
        :rtype: urlquick.Response
        """
        return self.request(u"POST", url, data=data, json=json, **kwargs)

    def put(self, url, data=None, **kwargs):
        """
        Sends a PUT request.

        Uploads a representation of the specified URI.

        :param str url: Url of the remote resource.
        :param data: [opt] Dictionary (will be form-encoded) or bytes sent in the body of the Request.
        :param kwargs: Optional arguments that :func:`request <urlquick.request>` takes.

        :return: A requests like Response object.
        :rtype: urlquick.Response
        """
        return self.request(u"PUT", url, data=data, **kwargs)

    def patch(self, url, data=None, **kwargs):
        """
        Sends a PATCH request.

        :param str url: Url of the remote resource.
        :param data: [opt] Dictionary (will be form-encoded) or bytes sent in the body of the Request.
        :param kwargs: Optional arguments that :func:`request <urlquick.request>` takes.

        :return: A requests like Response object.
        :rtype: urlquick.Response
        """
        return self.request(u"PATCH", url, data=data, **kwargs)

    def delete(self, url, **kwargs):
        """
        Sends a DELETE request.

        :param str url: Url of the remote resource.
        :param kwargs: Optional arguments that :func:`request <urlquick.request>` takes.

        :return: A requests like Response object.
        :rtype: urlquick.Response
        """
        return self.request(u"DELETE", url, **kwargs)

    def request(self, method, url, params=None, data=None, headers=None, cookies=None, auth=None,
                timeout=10, allow_redirects=None, verify=True, json=None, raise_for_status=None, max_age=None):
        """
        Make request for remote resource.

        :param str method: HTTP request method, GET, HEAD, POST.
        :param str url: Url of the remote resource.
        :param dict params: [opt] Dictionary of url query key/value pairs.
        :param data: [opt] Dictionary (will be form-encoded) or bytes sent in the body of the Request.
        :param dict headers: [opt] HTTP request headers.
        :param dict cookies: [opt] Dictionary of cookies to send with the request.
        :param tuple auth: [opt] (username, password) for basic authentication.
        :param int timeout: [opt] Connection timeout in seconds.
        :param bool allow_redirects: [opt] Enable/disable redirection. Defaults to ``True``.
        :param bool verify: [opt] Controls whether to verify the server's TLS certificate. Defaults to ``True``
        :param json: [opt] Json data sent in the body of the Request.
        :param bool raise_for_status: [opt] Raise's HTTPError if status code is > 400. Defaults to ``False``.
        :param int max_age: [opt] Age the 'cache' can be, before it’s considered stale. -1 will disable caching.
                            Defaults to :data:`MAX_AGE <urlquick.MAX_AGE>`

        :return: A requests like Response object.
        :rtype: urlquick.Response

        :raises MaxRedirects: If too many redirects was detected.
        :raises ConnError: If connection to server failed.
        :raises HTTPError: If response status is greater or equal to 400 and raise_for_status is ``True``.
        :raises SSLError: If an SSL error occurs while sending the request.
        :raises Timeout: If the connection to server timed out.
        """
        # Fetch settings from local or session
        allow_redirects = self.allow_redirects if allow_redirects is None else allow_redirects
        raise_for_status = self.raise_for_status if raise_for_status is None else raise_for_status

        # Ensure that all mappings of unicode data
        req_headers = CaseInsensitiveDict(self._headers, headers)
        req_cookies = UnicodeDict(self._cookies, cookies)
        req_params = UnicodeDict(self._params, params)

        # Add cookies to headers
        if req_cookies and u"Cookie" not in req_headers:
            header = u"; ".join([u"{}={}".format(key, value) for key, value in req_cookies.items()])
            req_headers[u"Cookie"] = header

        # Fetch max age of cache
        max_age = (-1 if self.max_age is None else self.max_age) if max_age is None else max_age

        # Parse url into it's individual components including params if given
        req = Request(method, url, req_headers, data, json, req_params)
        logger.debug("Requesting resource: %s", req.url)
        logger.debug("Request headers: %s", req.headers)
        if data:
            logger.debug("Request data: %s", req.data)

        # Add Authorization header if needed
        auth = auth or req.auth or self._auth
        if auth:
            auth = self._auth_header(*auth)
            req.headers[u"Authorization"] = auth

        # Request monitors
        history = []
        visited = defaultdict(int)
        start_time = datetime.utcnow()

        while True:
            # Send a request for resource
            raw_resp = self.make_request(req, timeout, verify, max_age)
            resp = Response(raw_resp, req, start_time, history[:])

            visited[req.url] += 1
            # Process the response
            if allow_redirects and resp.is_redirect:
                history.append(resp)
                if len(history) >= self.max_redirects:
                    raise MaxRedirects("max_redirects exceeded")
                if visited[req.url] >= self.max_repeats:
                    raise MaxRedirects("max_repeat_redirects exceeded")

                # Create new request for redirect
                location = resp.headers.get(u"location")
                if resp.status_code == 307:
                    req = Request(req.method, location, req_headers, req.data, referer=req.url)
                else:
                    req = Request(u"GET", location, req_headers, referer=req.url)
                logger.debug("Redirecting to = %s", unquote(req.url))

            # And Authorization Credentials if needed
            elif auth and resp.status_code == 401 and u"Authorization" not in req.headers:
                req.headers[u"Authorization"] = auth

            # According to RFC 2616, "2xx" code indicates that the client's
            # request was successfully received, understood, and accepted.
            # Therefore all other codes will be considered as errors.
            elif raise_for_status:
                resp.raise_for_status()
                return resp
            else:
                return resp

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    @staticmethod
    def _auth_header(username, password):
        # Ensure that username & password is of type bytes
        if isinstance(username, unicode):
            username = username.encode("utf8")
        if isinstance(password, unicode):
            password = password.encode("utf8")

        # Create basic authentication header
        auth = username + b":" + password
        auth = b64encode(auth).decode("ascii")
        return u"Basic {}".format(auth)


class Response(object):
    """A Response object containing all data returned from the server."""

    # noinspection PyArgumentList
    def __init__(self, response, org_request, start_time, history):
        #: The default encoding, used when no encoding is given.
        self.apparent_encoding = "utf8"

        #: File-like object representation of response (for advanced usage).
        self.raw = response

        #: Final URL location of Response.
        self.url = org_request.url

        #: The :class:`Request <urlquick.Request>` object to which this is a response.
        self.request = org_request

        #: A list of Response objects from the history of the Request.
        #: Any redirect responses will end up here.
        self.history = history

        #: The amount of time elapsed, between sending the request and
        #: the arrival of the response (as a timedelta).
        self.elapsed = datetime.utcnow() - start_time

        #: Integer Code of responded HTTP Status e.g. 404 or 200.
        self.status_code = response.status

        #: Textual reason of response HTTP Status e.g. “Not Found” or “OK”.
        self.reason = unicode(response.reason)

        # Fetch content body
        self._body = response.read()
        response.close()

        # Fetch response headers and convert to CaseInsensitiveDict if needed
        headers = response.getheaders()
        if isinstance(headers, CaseInsensitiveDict):
            self._headers = headers
        else:
            self._headers = CaseInsensitiveDict(headers)

    @CachedProperty
    def encoding(self):
        """Encoding, to decode with, when accessing :meth:`resp.text <urlquick.Response.text>`."""
        if u"Content-Type" in self._headers:
            header = self._headers[u"Content-Type"]
            for sec in header.split(u";"):
                sec = sec.strip()
                if sec.startswith(u"charset"):
                    _, value = sec.split(u"=", 1)
                    return value.strip()

    # Allow encoding property to be set by the user
    encoding.allow_setter = True

    @CachedProperty
    def content(self):
        """
        Content of the response in bytes.

        :raises ContentError: If content failes to decompress.
        """
        # Check if Response need to be decoded, else return raw response
        content_encoding = self._headers.get(u"content-encoding", u"").lower()
        if u"gzip" in content_encoding:
            decoder = zlib.decompressobj(16 + zlib.MAX_WBITS)
        elif u"deflate" in content_encoding:
            decoder = zlib.decompressobj()
        elif content_encoding:
            raise ContentError("Unknown encoding: {}".format(content_encoding))
        else:
            return self._body

        try:
            return decoder.decompress(self._body)
        except (IOError, zlib.error) as e:
            raise ContentError("Failed to decompress content body: {}".format(e))

    @CachedProperty
    def text(self):
        """
        Content of the response in unicode.

        The response content will be decoded using the best available encoding based on the response headers.
        Will fallback to :data:`apparent_encoding <urlquick.Response.apparent_encoding>`
        if no encoding was given within headers.
        """
        if self.encoding:
            try:
                return self.content.decode(self.encoding)
            except UnicodeDecodeError:
                logger.debug("Failed to decode content with given encoding: '%s'", self.encoding)

        apparent_encoding = self.apparent_encoding
        if apparent_encoding and not (self.encoding and getencoder(self.encoding) == getencoder(apparent_encoding)):
            logger.debug("Attempting to decode with default encoding: '%s'", self.apparent_encoding)
            try:
                return self.content.decode(apparent_encoding)
            except UnicodeDecodeError:
                logger.debug("Failed to decode content with default encoding: %s, "
                             "switching to fallback encoding: 'iso-8859-1'", apparent_encoding)
        else:
            logger.debug("Attempting to decode with fallback encoding: 'iso-8859-1'")

        return self.content.decode("iso-8859-1")

    @CachedProperty
    def cookies(self):
        """A dictionary of Cookies the server sent back."""
        if u"Set-Cookie" in self._headers:
            cookies = self._headers[u"Set-Cookie"]
            if py3:
                cookiejar = SimpleCookie(cookies)
            else:
                cookiejar = SimpleCookie(cookies.encode("iso-8859-1"))

            return {cookie.key: cookie.value for cookie in cookiejar.values()}
        else:
            return {}

    @CachedProperty
    def links(self):
        """Dictionary of 'parsed header links' of the response, if any."""
        if u"link" in self._headers:
            links = {}

            replace_chars = u" '\""
            for val in re.split(u", *<", self._headers[u"link"]):
                try:
                    url, params = val.split(";", 1)
                except ValueError:
                    url, params = val, u""

                link = {u"url": url.strip("<> '\"")}

                for param in params.split(";"):
                    try:
                        key, value = param.split("=")
                    except ValueError:
                        break

                    link[key.strip(replace_chars).lower()] = value.strip(replace_chars)

                key = link.get(u"rel") or link.get(u"url")
                links[key] = link

            return links
        else:
            return {}

    @property
    def headers(self):
        """Case-insensitive Dictionary of Response Headers."""
        return self._headers

    @property
    def is_redirect(self):
        """``True``, if this Response is a well-formed HTTP redirect, that could have been processed automatically."""
        headers = self._headers
        return u"location" in headers and self.status_code in REDIRECT_CODES

    @property
    def is_permanent_redirect(self):
        """``True``, if this Response is one of the permanent versions of redirect."""
        headers = self._headers
        return u"location" in headers and self.status_code in (301, 308)

    @property
    def ok(self):
        """
        ``True``, if status_code is less than 400.

        This attribute checks if the status code of the response is between 400 and 600. To
        see if there was a client error or a server error. If the status code is between
        200 and 400, this will return True. This is not a check to see if the response code is 200 "OK".
        """
        return self.status_code < 400

    def json(self, **kwargs):
        """
        Returns the json-encoded content of a response.

        :param kwargs: [opt] Arguments that :func:`json.loads` takes.
        :raises ValueError: If the response body does not contain valid json.
        """
        return _json.loads(self.text, **kwargs)

    def xml(self):
        """
        Parse's "XML" document into a element tree.

        :return: The root element of the element tree.
        :rtype: xml.etree.ElementTree.Element
        """
        from xml.etree import ElementTree
        return ElementTree.fromstring(self.content)

    def parse(self, tag=u"", attrs=None):
        """
        Parse's "HTML" document into a element tree using HTMLement.

        .. seealso:: The htmlement documentation can be found at.\n
                     http://python-htmlement.readthedocs.io/en/stable/?badge=stable

        :param str tag: [opt] Name of 'element' which is used to filter tree to required section.

        :type attrs: dict
        :param attrs: [opt] Attributes of 'element', used when searching for required section.
                            Attrs should be a dict of unicode key/value pairs.

        :return: The root element of the element tree.
        :rtype: xml.etree.ElementTree.Element

        :raise MissingDependency: If the optional 'HTMLement' dependency is missing.
        """
        try:
            # noinspection PyUnresolvedReferences
            from htmlement import HTMLement
        except ImportError:
            raise MissingDependency("Missing optional dependency named 'HTMLement'")
        else:
            parser = HTMLement(unicode(tag), attrs)
            parser.feed(self.text)
            return parser.close()

    def iter_content(self, chunk_size=512, decode_unicode=False):
        """
        Iterates over the response data. The chunk size are the number of bytes it should read into memory.
        This is not necessarily the length of each item returned, as decoding can take place.

        :param int chunk_size: [opt] The chunk size to use for each chunk.
                               (default=512)
        :param bool decode_unicode: [opt] ``True`` to return unicode, else ``False`` to return bytes.
                                    (default=``False``)
        """
        content = self.text if decode_unicode else self.content
        prevnl = 0
        while True:
            chucknl = prevnl + chunk_size
            data = content[prevnl:chucknl]
            if not data:
                break
            yield data
            prevnl = chucknl

    # noinspection PyUnusedLocal
    def iter_lines(self, chunk_size=None, decode_unicode=False, delimiter=b"\n"):
        """
        Iterates over the response data, one line at a time.

        :param int chunk_size: [opt] Unused, here for compatibility with requests.
        :param bool decode_unicode: [opt] ``True`` to return unicode, else ``False`` to return bytes.
                                    (default=``False``)
        :param bytes delimiter: [opt] Delimiter used as the end of line marker.
                                (default=b'\\\\n')
        """
        if decode_unicode:
            content = self.text
            # noinspection PyArgumentList
            delimiter = unicode(delimiter)
        else:
            content = self.content

        prevnl = 0
        sepsize = len(delimiter)
        while True:
            nextnl = content.find(delimiter, prevnl)
            if nextnl < 0:
                yield content[prevnl:]
                break
            yield content[prevnl:nextnl]
            prevnl = nextnl + sepsize

    def raise_for_status(self):
        """
        Raises stored error, if one occurred.

        :raises HTTPError: If response status code is greater or equal to 400
        """
        # According to RFC 2616, "2xx" code indicates that the client's
        # request was successfully received, understood, and accepted.
        # Therefore all other codes will be considered as errors.
        if self.status_code >= 400:
            raise HTTPError(self.url, self.status_code, self.reason, self.headers)

    def close(self):
        pass

    def __iter__(self):
        """Allows to use a response as an iterator."""
        return self.iter_content()

    def __bool__(self):
        """Returns True if status_code is less than 400."""
        return self.ok

    def __nonzero__(self):
        """Returns True if status_code is less than 400."""
        return self.ok

    def __repr__(self):
        return "<Response [{}]>".format(self.status_code)


def request(method, url, params=None, data=None, headers=None, cookies=None, auth=None,
            timeout=10, allow_redirects=None, verify=True, json=None, raise_for_status=None, max_age=None):
    """
    Make request for remote resource.

    :param str method: HTTP request method, GET, HEAD, POST.
    :param str url: Url of the remote resource.
    :param dict params: [opt] Dictionary of url query key/value pairs.
    :param data: [opt] Dictionary (will be form-encoded) or bytes sent in the body of the Request.
    :param dict headers: [opt] HTTP request headers.
    :param dict cookies: [opt] Dictionary of cookies to send with the request.
    :param tuple auth: [opt] (username, password) for basic authentication.
    :param int timeout: [opt] Connection timeout in seconds.
    :param bool allow_redirects: [opt] Enable/disable redirection. Defaults to ``True``.
    :param bool verify: [opt] Controls whether to verify the server's TLS certificate. Defaults to ``True``
    :param json: [opt] Json data sent in the body of the Request.
    :param bool raise_for_status: [opt] Raise's HTTPError if status code is > 400. Defaults to ``False``.
    :param int max_age: [opt] Age the 'cache' can be, before it’s considered stale. -1 will disable caching.
                        Defaults to :data:`MAX_AGE <urlquick.MAX_AGE>`

    :return: A requests like Response object.
    :rtype: urlquick.Response

    :raises MaxRedirects: If too many redirects was detected.
    :raises ConnError: If connection to server failed.
    :raises HTTPError: If response status is greater or equal to 400 and raise_for_status is ``True``.
    :raises SSLError: If an SSL error occurs while sending the request.
    :raises Timeout: If the connection to server timed out.
    """
    with Session() as session:
        return session.request(method, url, params, data, headers, cookies, auth, timeout,
                               allow_redirects, verify, json, raise_for_status, max_age)


def get(url, params=None, **kwargs):
    """
    Sends a GET request.

    Requests data from a specified resource.

    :param str url: Url of the remote resource.
    :param dict params: [opt] Dictionary of url query key/value pairs.
    :param kwargs: Optional arguments that :func:`request <urlquick.request>` takes.

    :return: A requests like Response object.
    :rtype: urlquick.Response
    """
    with Session() as session:
        return session.request(u"GET", url, params=params, **kwargs)


def head(url, **kwargs):
    """
    Sends a HEAD request.

    Same as GET but returns only HTTP headers and no document body.

    :param str url: Url of the remote resource.
    :param kwargs: Optional arguments that :func:`request <urlquick.request>` takes.

    :return: A requests like Response object.
    :rtype: urlquick.Response
    """
    with Session() as session:
        return session.request(u"HEAD", url, **kwargs)


def post(url, data=None, json=None, **kwargs):
    """
    Sends a POST request.

    Submits data to be processed to a specified resource.

    :param str url: Url of the remote resource.
    :param data: [opt] Dictionary (will be form-encoded) or bytes sent in the body of the Request.
    :param json: [opt] Json data sent in the body of the Request.
    :param kwargs: Optional arguments that :func:`request <urlquick.request>` takes.

    :return: A requests like Response object.
    :rtype: urlquick.Response
    """
    with Session() as session:
        return session.request(u"POST", url, data=data, json=json, **kwargs)


def put(url, data=None, **kwargs):
    """
    Sends a PUT request.

    Uploads a representation of the specified URI.

    :param str url: Url of the remote resource.
    :param data: [opt] Dictionary (will be form-encoded) or bytes sent in the body of the Request.
    :param kwargs: Optional arguments that :func:`request <urlquick.request>` takes.

    :return: A requests like Response object.
    :rtype: urlquick.Response
    """
    with Session() as session:
        return session.request(u"PUT", url, data=data, **kwargs)


def patch(url, data=None, **kwargs):
    """
    Sends a PATCH request.

    :param str url: Url of the remote resource.
    :param data: [opt] Dictionary (will be form-encoded) or bytes sent in the body of the Request.
    :param kwargs: Optional arguments that :func:`request <urlquick.request>` takes.

    :return: A requests like Response object.
    :rtype: urlquick.Response
    """
    with Session() as session:
        return session.request(u"PATCH", url, data=data, **kwargs)


def delete(url, **kwargs):
    """
    Sends a DELETE request.

    :param str url: Url of the remote resource.
    :param kwargs: Optional arguments that :func:`request <urlquick.request>` takes.

    :return: A requests like Response object.
    :rtype: urlquick.Response
    """
    with Session() as session:
        return session.request(u"DELETE", url, **kwargs)


def cache_cleanup(max_age=None):
    """
    Remove all stale cache files.

    :param int max_age: [opt] The max age the cache can be before removal.
                        defaults => :data:`MAX_AGE <urlquick.MAX_AGE>`
    """
    logger.info("Initiating cache cleanup")

    handler = CacheHandler
    max_age = MAX_AGE if max_age is None else max_age
    cache_dir = handler.cache_dir()

    # Loop over all cache files and remove stale files
    filestart = handler.safe_path(u"cache-")
    for cachefile in os.listdir(cache_dir):
        # Check that we actually have a cache file
        if cachefile.startswith(filestart):
            cache_path = os.path.join(cache_dir, cachefile)
            # Check if the cache is not fresh and delete if so
            if not handler.isfilefresh(cache_path, max_age):
                handler.delete(cache_path)


def auto_cache_cleanup(max_age=60 * 60 * 24 * 14):
    """
    Check if the cache needs cleanup. Uses a empty file to keep track.

    :param int max_age: [opt] The max age the cache can be before removal.
                        defaults => 1209600 (14 days)

    :returns: True if cache was cleaned else false if no cache cleanup was started.
    :rtype: bool
    """
    check_file = os.path.join(CACHE_LOCATION, "cache_check")
    last_check = os.stat(check_file).st_mtime if os.path.exists(check_file) else 0
    current_time = time.time()

    # Check if it's time to initiate a cache cleanup
    if current_time - last_check > max_age * 2:
        cache_cleanup(max_age)
        try:
            os.utime(check_file, None)
        except OSError:
            open(check_file, "a").close()
        return True
    return False


#############
# Kodi Only #
#############

# Set the location of the cache file to the addon data directory
_addon_data = __import__("xbmcaddon").Addon()
_CACHE_LOCATION = __import__("xbmc").translatePath(_addon_data.getAddonInfo("profile"))
CACHE_LOCATION = _CACHE_LOCATION.decode("utf8") if isinstance(_CACHE_LOCATION, bytes) else _CACHE_LOCATION
logger.debug("Cache location: %s", CACHE_LOCATION)
Session.default_raise_for_status = True

# Check if cache cleanup is required
auto_cache_cleanup()
