# -*- coding: utf-8 -*-

'''
    Montreal Greek TV Add-on
    Author: greektimes

        License summary below, for more details please read license.txt file

        This program is free software: you can redistribute it and/or modify
        it under the terms of the GNU General Public License as published by
        the Free Software Foundation, either version 2 of the License, or
        (at your option) any later version.
        This program is distributed in the hope that it will be useful,
        but WITHOUT ANY WARRANTY; without even the implied warranty of
        MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
        GNU General Public License for more details.
        You should have received a copy of the GNU General Public License
        along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''
from __future__ import absolute_import, division, unicode_literals

import sys

is_py2 = (sys.version_info[0] == 2)
is_py3 = (sys.version_info[0] == 3)


if is_py2:

    _str = str
    str = unicode
    range = xrange
    from itertools import izip
    unicode = unicode
    basestring = basestring

    def bytes(b, encoding="ascii"):
        return _str(b)

    def iteritems(d, **kw):

        return d.iteritems(**kw)

elif is_py3:

    bytes = bytes
    str = unicode = basestring = str
    range = range
    izip = zip

    def iteritems(d, **kw):

        return iter(d.items(**kw))

try:
    from sqlite3 import dbapi2 as database
except ImportError:
    from pysqlite2 import dbapi2 as database

# Python 2
try:
    from urlparse import urlparse, urlunparse, urljoin, parse_qsl, urlsplit, urlunsplit, parse_qs
    from urllib import quote, unquote, urlencode, URLopener, quote_plus, unquote_plus
    import Queue as queue
    import cookielib
    import urllib2
    from HTMLParser import HTMLParser
    unescape = HTMLParser().unescape
# Python 3:
except ImportError:
    from http import cookiejar as cookielib
    from html import unescape
    import urllib.request as urllib2
    URLopener = urllib2.URLopener
    from urllib.parse import (
        urlparse, urlunparse, urljoin, quote, unquote, parse_qsl, urlencode, urlsplit, urlunsplit, unquote_plus,
        quote_plus
    )
    import queue
finally:
    urlopen = urllib2.urlopen
    Request = urllib2.Request


__all__ = [
    "is_py2", "is_py3", "str", "bytes", "urlparse", "urlunparse", "urljoin", "parse_qsl", "quote", "unquote", "queue",
    "range", "urlencode", "izip", "urlsplit", "urlunsplit", "cookielib", "URLopener", "quote_plus", "unescape",
    "parse_qs", "unquote_plus", "urllib2", "unicode", "database", "basestring", "urlopen", "Request", "OrderedDict"
]
