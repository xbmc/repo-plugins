# -*- coding: utf-8 -*-

# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, unicode_literals
import re


HTML_MAPPING = [
    (re.compile(r'<i\s[^>]+>'), '[I]'),
    (re.compile('<i>'), '[I]'),
    (re.compile('</i>'), '[/I]'),
    (re.compile(r'<b\s[^>]+>'), '[B]'),
    (re.compile('<b>'), '[B]'),
    (re.compile('</b>'), '[/B]'),
    (re.compile(r'<p\s[^>]+>'), ''),
    (re.compile('<p>'), '',),
    (re.compile('</p>'), ''),
    (re.compile(r'<div\s[^>]+>'), ''),
    (re.compile('<div>'), ''),
    (re.compile('</div>'), ''),
    (re.compile(r'<span\s[^>]+>'), ''),
    (re.compile('<span>'), ''),
    (re.compile('</span>'), ''),
    (re.compile('<br>\n'), ' '),  # This appears to be specific formatting for VRT.NU, but unwanted for us
    (re.compile('<br>'), ' '),  # This appears to be specific formatting for VRT.NU, but unwanted for us
]

# pylint: disable=unused-import
try:
    from html import unescape
except ImportError:
    from HTMLParser import HTMLParser

    def unescape(s):
        return HTMLParser().unescape(s)


def convert_html_to_kodilabel(text):
    for (k, v) in HTML_MAPPING:
        text = k.sub(v, text)
    return unescape(text).strip()


def shorten_link(url):
    if url is None:
        return None
    # As used in episode search result 'permalink'
    url = url.replace('https://www.vrt.be/vrtnu/', 'vrtnu.be/')
    # As used in program a-z listing 'targetUrl'
    url = url.replace('//www.vrt.be/vrtnu/', 'vrtnu.be/')
    return url


def strip_newlines(text):
    return text.replace('\n', '').strip()


def add_https_method(url):
    if url.startswith('//'):
        return 'https:' + url
    if url.startswith('/'):
        return 'https://vrt.be' + url
    return url


def distinct(sequence):
    seen = set()
    for s in sequence:
        if s not in seen:
            seen.add(s)
            yield s
