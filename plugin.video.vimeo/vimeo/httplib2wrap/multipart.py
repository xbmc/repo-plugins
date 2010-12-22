#!/usr/bin/env python
# -*- coding: utf-8; -*-
from uuid import uuid4
from os.path import basename
from mimetypes import guess_type

BOUNDARY = uuid4().hex

def encode_multipart(data, files_data, boundary=BOUNDARY):
    lines = []

    for key, value in data.items():
        lines.extend(['--' + boundary,
                     'Content-Disposition: form-data; name="%s"' % str(key),
                      '',
                      str(value)])
    for key, value in files_data.items():
        lines.extend(encode_file(key, value, boundary))

    lines.extend(['--' + boundary + '--', '',])
    return '\r\n'.join(lines)

def guess_mime(path):
    mime, _ = guess_type(path)
    return mime or 'application/octet-stream'

def encode_file(key, file_data, boundary=BOUNDARY):
    try:
        file_name = file_data.name
    except AttributeError:
        file_name = "fileobject"
    return [
        '--' + boundary,
        'Content-Disposition: form-data; name="%s"; filename="%s"' \
            % (str(key), str(basename(file_name))),
        'Content-Type: %s' % guess_mime(file_name),
        '',
        str(file_data.read())
    ]
