# -*- coding: utf-8 -*-
#
# Copyright (C) 2014 Thomas Amland
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import re
import sys
import xbmc
import xbmcaddon
from urlparse import parse_qs, urlsplit
from urllib import urlencode


_addon = xbmcaddon.Addon()
_addon_id = _addon.getAddonInfo('id')

_log_tag = "[%s][routing] " % _addon_id
log = lambda msg: xbmc.log(_log_tag + msg, level=xbmc.LOGDEBUG)


class Plugin(object):

    def __init__(self):
        self._routes = []
        self._addon = _addon
        self.handle = int(sys.argv[1])
        self.addon_id = _addon_id
        self.path = self._addon.getAddonInfo('path')
        self.args = None

    def route_for(self, path):
        uri_self = 'plugin://%s' % self.addon_id
        if path.startswith(uri_self):
            path = path.split(uri_self, 1)[1]
        for rule in self._routes:
            view_func, items = rule.match(path)
            if view_func:
                return view_func
        raise Exception('route_for: no route for path <%s>' % path)

    def url_for(self, func, *args, **kwargs):
        for rule in self._routes:
            if rule._view_func is func:
                path = rule.make_path(*args, **kwargs)
                return self.url_for_path(path)
        return None

    def url_for_path(self, path):
        if not path.startswith('/'):
            path = '/' + path
        return 'plugin://%s%s' % (self.addon_id, path)

    def route(self, url_rule):
        def decorator(f):
            rule = UrlRule(url_rule, f)
            self._routes.append(rule)
            return f
        return decorator

    def run(self):
        self.args = parse_qs(sys.argv[2].lstrip('?'))
        path = sys.argv[0].split('plugin://%s' % self.addon_id)[1] or '/'
        self._dispatch(path)

    def redirect(self, path):
        self._dispatch(path)

    def _dispatch(self, path):
        for rule in self._routes:
            view_func, kwargs = rule.match(path)
            if view_func:
                log("dispatching to <%s>, args: %s" % (view_func.__name__, kwargs))
                view_func(**kwargs)
                return
        raise Exception('no route for path "%s"' % path)


class UrlRule(object):

    def __init__(self, url_rule, view_func):
        self._view_func = view_func

        kw_pattern = r'<(?:[^:]+:)?([A-z]+)>'
        self._url_format = re.sub(kw_pattern, '{\\1}', url_rule)
        self._keywords = re.findall(kw_pattern, url_rule)

        p = re.sub('<([A-z]+)>', '<string:\\1>', url_rule)
        p = re.sub('<string:([A-z]+)>', '(?P<\\1>[^/]+?)', p)
        p = re.sub('<path:([A-z]+)>', '(?P<\\1>.*)', p)
        self._pattern = p
        self._regex = re.compile('^' + p + '$')

    def match(self, path):
        path = urlsplit(path).path
        m = self._regex.search(path)
        if not m:
            return False, None
        return self._view_func, m.groupdict()

    def make_path(self, *args, **kwargs):
        if args and kwargs:
            raise ValueError("can't use both args and kwargs")
        if args:
            return re.sub(r'{[A-z]+}', r'%s', self._url_format) % args

        url_args = dict(((k, v) for k, v in kwargs.items() if k in self._keywords))
        qs_args = dict(((k, v) for k, v in kwargs.items() if k not in self._keywords))
        return self._url_format.format(**url_args) + '?' + urlencode(qs_args)
