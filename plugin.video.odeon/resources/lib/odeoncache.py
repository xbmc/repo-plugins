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

import time
import base64
import json
import zlib
import hashlib

try:
    import StorageServer
except:
    import storageserverdummy as StorageServer


def comp(js):
    data = json.dumps(js, ensure_ascii=True, encoding='utf-8')
    deflated = zlib.compress(data)
    return base64.b64encode(deflated)


def decomp(b64):
    try:
        deflated = base64.b64decode(b64)
        data = zlib.decompress(deflated)
        return json.loads(data, encoding='utf-8')
    except:
        return None


def digest(data):
    digest = hashlib.md5(data).digest()
    return base64.b64encode(digest)


class OdeonCache():

    def __init__(self, plugin_name):
        self.cache = StorageServer.StorageServer(plugin_name, 6) # cache time in hours
        self.cache.dbg = True
        self.plugin_name = plugin_name


    def put(self, url, data, etag, ttl):
        url = url.encode("utf-8")
        data = {
            "data": data,
            "venc": str(time.time() + ttl)
            }
        if etag:
            data.update({"etag": etag})

        self.cache.table_name = self.plugin_name
        self.cache.set(url, comp(data))
        return


    def get(self, url):
        url = url.encode("utf-8")
        self.cache.table_name = self.plugin_name
        b64 = self.cache.get(url)
        if b64:
            return decomp(b64)
        else:
            return None


    def time_valid(self, data):
        if data:
            venc = data.get("venc", 0)
            return time.time() < float(venc)
        else:
            return False


    def refresh_ttl(self, url, data, ttl):
        self.put(url, data["data"], data.get("etag"), ttl)
