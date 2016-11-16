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

import base64
import json
import zlib
import hashlib


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
