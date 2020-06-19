# -*- coding: utf-8 -*-
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""Implements static functions used elsewhere in the add-on"""

from __future__ import absolute_import, division, unicode_literals
import re

try:  # Python 3
    from html import unescape
except ImportError:  # Python 2
    from HTMLParser import HTMLParser

    def unescape(string):
        """Expose HTMLParser's unescape"""
        return HTMLParser().unescape(string)

HTML_MAPPING = [
    (re.compile(r'<(/?)i(|\s[^>]+)>', re.I), '[\\1I]'),
    (re.compile(r'<(/?)b(|\s[^>]+)>', re.I), '[\\1B]'),
    (re.compile(r'<em(|\s[^>]+)>', re.I), '[B][COLOR={highlighted}]'),
    (re.compile(r'</em>', re.I), '[/COLOR][/B]'),
    (re.compile(r'<li>', re.I), '- '),
    (re.compile(r'</?(li|ul)(|\s[^>]+)>', re.I), '\n'),
    (re.compile(r'</?(div|p|span)(|\s[^>]+)>', re.I), ''),
    (re.compile('<br>\n{0,1}', re.I), ' '),  # This appears to be specific formatting for VRT NU, but unwanted by us
    (re.compile('(&nbsp;\n){2,}', re.I), '\n'),  # Remove repeating non-blocking spaced newlines
]


def to_unicode(text, encoding='utf-8', errors='strict'):
    """Force text to unicode"""
    if isinstance(text, bytes):
        return text.decode(encoding, errors=errors)
    return text


def from_unicode(text, encoding='utf-8', errors='strict'):
    """Force unicode to text"""
    import sys
    if sys.version_info.major == 2 and isinstance(text, unicode):  # noqa: F821; pylint: disable=undefined-variable
        return text.encode(encoding, errors)
    return text


def capitalize(string):
    """Ensure the first character is uppercase"""
    string = string.strip()
    return string[0].upper() + string[1:]


def strip_newlines(text):
    """Strip newlines and trailing whitespaces"""
    return text.replace('\n', '').strip()


def html_to_kodi(text):
    """Convert VRT HTML content into Kodit formatted text"""
    for key, val in HTML_MAPPING:
        text = key.sub(val, text)
    return unescape(text).strip()


def add_https_proto(url):
    """Add HTTPS protocol to URL that lacks it"""
    if url.startswith('//'):
        return 'https:' + url
    if url.startswith('/'):
        return 'https://www.vrt.be' + url
    return url


def find_entry(dlist, key, value, default=None):
    """Find (the first) dictionary in a list where key matches value"""
    return next((entry for entry in dlist if entry.get(key) == value), default)


def youtube_to_plugin_url(url):
    """Convert a YouTube URL to a Kodi plugin URL"""
    url = url.replace('https://www.youtube.com/', 'plugin://plugin.video.youtube/')
    if not url.endswith('/'):
        url += '/'
    return url
