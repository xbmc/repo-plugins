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

import gzip
import StringIO
import base64
import json
import hashlib


def comp(data):
    out = StringIO.StringIO()
    f = gzip.GzipFile(fileobj=out, mode='w', compresslevel=5)
    js = json.dumps(data, ensure_ascii=True, encoding='utf-8')
    f.write(js)
    f.close()
    return base64.b64encode(out.getvalue())


def decomp(b64):
    gzipData = base64.b64decode(b64)
    stream = StringIO.StringIO(gzipData)
    f = gzip.GzipFile(fileobj=stream, mode='r')
    txt = f.read()
    f.close()
    return json.loads(txt, encoding='utf-8')


def digest(data):
    digest = hashlib.md5(data).digest()
    return base64.b64encode(digest)


def unzip(zipped):
    stream = StringIO.StringIO(zipped)
    f = gzip.GzipFile(fileobj=stream, mode='r')
    return f.read()
