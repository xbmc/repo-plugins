# -*- coding: utf-8 -*-

'''
    Odeon Add-on
    Copyright (C) 2016 Empresa Argentina de Soluciones Satelitales SA - ARSAT

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

import json as jsonr
import urllib2
import zlib

class response():

    def __init__(self, resp=None, err=None):
        self.r = resp
        self.e = err
        self.status_code = 0
        self.content = None
        self.headers = {}

        if self.r:
            info = self.r.info()
            self.headers = info.dict.copy()
            self.status_code = self.r.code

            try:
                self.content = self.r.read()
                if info.get('Content-Encoding') == 'gzip':
                    self.content = zlib.decompress(self.content, zlib.MAX_WBITS + 16)
            except:
                pass

        elif self.e:
            self.status_code = self.e.code
            self.content = self.e.read()


def get(url, headers=None, timeout=10, compress=False):
    req = urllib2.Request(url)
    for k, v in headers.iteritems():
        req.add_header(k, v)
    if compress: req.add_header('Accept-Encoding', 'gzip')

    try:
        r = urllib2.urlopen(req, timeout=timeout)
        return response(resp=r)
    except urllib2.HTTPError as e:
        return response(err=e)
    except urllib2.URLError as e:
        raise Exception("Error de conexion:{0} args:{1}".format(e, e.args))


def post(url, json, headers=None, timeout=10):
    data = jsonr.dumps(json, ensure_ascii=False)
    req = urllib2.Request(url, data)
    for k, v in headers.iteritems():
        req.add_header(k, v)

    try:
        r = urllib2.urlopen(req, timeout=timeout)
        return response(resp=r)
    except urllib2.HTTPError as e:
        return response(err=e)
    except urllib2.URLError as e:
        raise Exception("Error de conexion:{0} args:{1}".format(e, e.args))


