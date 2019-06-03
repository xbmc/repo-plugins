# -*- coding: utf-8 -*-

# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, unicode_literals
import re

try:
    from html import unescape
except ImportError:
    from HTMLParser import HTMLParser

    def unescape(s):
        ''' Expose HTMLParser's unescape '''
        return HTMLParser().unescape(s)

HTML_MAPPING = [
    (re.compile(r'<(/?)i(|\s[^>]+)>', re.I), '[\\1I]'),
    (re.compile(r'<(/?)b(|\s[^>]+)>', re.I), '[\\1B]'),
    (re.compile(r'<em(|\s[^>]+)>', re.I), '[B][COLOR yellow]'),
    (re.compile(r'</em>', re.I), '[/COLOR][/B]'),
    (re.compile(r'<li>', re.I), '- '),
    (re.compile(r'</?(div|li|p|span|ul)(|\s[^>]+)>', re.I), ''),
    (re.compile('<br>\n{0,1}', re.I), ' '),  # This appears to be specific formatting for VRT NU, but unwanted by us
]


def convert_html_to_kodilabel(text):
    ''' Convert VRT HTML content into Kodit formatted text '''
    for (k, v) in HTML_MAPPING:
        text = k.sub(v, text)
    return unescape(text).strip()


def unique_path(path):
    ''' Create a unique path to be used in VRT favorites '''
    if path.startswith('//www.vrt.be/vrtnu'):
        return path.replace('//www.vrt.be/vrtnu/', '/vrtnu/').replace('.relevant/', '/')
    return path


def shorten_link(url):
    ''' Create a link that is as short as possible '''
    if url is None:
        return None
    if url.startswith('https://www.vrt.be/vrtnu/'):
        # As used in episode search result 'permalink'
        return url.replace('https://www.vrt.be/vrtnu/', 'vrtnu.be/')
    if url.startswith('//www.vrt.be/vrtnu/'):
        # As used in program a-z listing 'targetUrl'
        return url.replace('//www.vrt.be/vrtnu/', 'vrtnu.be/')
    return url


def strip_newlines(text):
    ''' Strip newlines and whitespaces '''
    return text.replace('\n', '').strip()


def add_https_method(url):
    ''' Add HTTPS protocol to URL that lacks it '''
    if url.startswith('//'):
        return 'https:' + url
    if url.startswith('/'):
        return 'https://vrt.be' + url
    return url


def distinct(sequence):
    ''' Create a unique list that has no duplicates '''
    seen = set()
    for s in sequence:
        if s not in seen:
            seen.add(s)
            yield s


def boolean(value):
    ''' Verify if a URL parameter values is a boolean '''
    if value is True:
        return True
    if value in ('True', 'true'):
        return True
    return False


def realpage(page):
    ''' Convert a URL parameter page value into an integer '''
    try:
        page = int(page)
    except TypeError:
        return 1
    if page < 1:
        return 1
    return page
