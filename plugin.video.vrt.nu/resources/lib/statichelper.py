# -*- coding: utf-8 -*-
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
''' Implements static functions used elsewhere in the add-on '''

from __future__ import absolute_import, division, unicode_literals
import re

try:  # Python 3
    from html import unescape
except ImportError:  # Python 2
    from HTMLParser import HTMLParser

    def unescape(string):
        ''' Expose HTMLParser's unescape '''
        return HTMLParser().unescape(string)

HTML_MAPPING = [
    (re.compile(r'<(/?)i(|\s[^>]+)>', re.I), '[\\1I]'),
    (re.compile(r'<(/?)b(|\s[^>]+)>', re.I), '[\\1B]'),
    (re.compile(r'<em(|\s[^>]+)>', re.I), '[B][COLOR yellow]'),
    (re.compile(r'</em>', re.I), '[/COLOR][/B]'),
    (re.compile(r'<li>', re.I), '- '),
    (re.compile(r'</?(div|li|p|span|ul)(|\s[^>]+)>', re.I), ''),
    (re.compile('<br>\n{0,1}', re.I), ' '),  # This appears to be specific formatting for VRT NU, but unwanted by us
    (re.compile('(&nbsp;\n){2,}', re.I), '\n'),  # Remove repeating non-blocking spaced newlines
]


def convert_html_to_kodilabel(text):
    ''' Convert VRT HTML content into Kodit formatted text '''
    for key, val in HTML_MAPPING:
        text = key.sub(val, text)
    return unescape(text).strip()


def program_to_url(program, url_type):
    ''' Convert a program url component (e.g. de-campus-cup) to a short programUrl (e.g. /vrtnu/a-z/de-campus-cup/)
        or to a long programUrl (e.g. //www.vrt.be/vrtnu/a-z/de-campus-cup/)
    '''
    url = None
    if program:
        # short programUrl
        if url_type == 'short':
            url = '/vrtnu/a-z/' + program + '/'
        # long programUrl
        elif url_type == 'long':
            url = '//www.vrt.be/vrtnu/a-z/' + program + '/'
    return url


def url_to_program(url):
    ''' Convert
          - a targetUrl (e.g. //www.vrt.be/vrtnu/a-z/de-campus-cup.relevant/),
          - a short programUrl (e.g. /vrtnu/a-z/de-campus-cup/) or
          - a long programUrl (e.g. //www.vrt.be/vrtnu/a-z/de-campus-cup/)
        to a program url component (e.g. de-campus-cup).
        Any season or episode information is removed as well.
    '''
    program = None
    if url.startswith('//www.vrt.be/vrtnu/a-z/'):
        # long programUrl or targetUrl
        program = url.split('/')[5]
        if program.endswith('.relevant'):
            # targetUrl
            program = program.replace('.relevant', '')
    elif url.startswith('/vrtnu/a-z/'):
        # short programUrl
        program = url.split('/')[3]
    return program


def to_unicode(text, encoding='utf-8'):
    ''' Force text to unicode '''
    return text.decode(encoding) if isinstance(text, bytes) else text


def from_unicode(text, encoding='utf-8'):
    ''' Force unicode to text '''
    import sys
    if sys.version_info.major == 2 and isinstance(text, unicode):  # noqa: F821; pylint: disable=undefined-variable
        return text.encode(encoding)
    return text


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


def realpage(page):
    ''' Convert a URL parameter page value into an integer '''
    try:
        page = int(page)
    except ValueError:
        return 1
    if page < 1:
        return 1
    return page


def find_entry(dlist, key, value, default=None):
    ''' Find (the first) dictionary in a list where key matches value '''
    return next((entry for entry in dlist if entry.get(key) == value), default)
