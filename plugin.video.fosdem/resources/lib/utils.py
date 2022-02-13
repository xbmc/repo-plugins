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
    (re.compile(r'<em(|\s[^>]+)>', re.I), '[B][COLOR=yellow]'),
    (re.compile(r'</em>', re.I), '[/COLOR][/B]'),
    (re.compile(r'<(strong|h\d)>', re.I), '[B]'),
    (re.compile(r'</(strong|h\d)>', re.I), '[/B]'),
    (re.compile(r'<li>', re.I), '- '),
    (re.compile(r'</?(li|ul|ol)(|\s[^>]+)>', re.I), '\n'),
    (re.compile(r'</?(code|div|p|pre|span)(|\s[^>]+)>', re.I), ''),
    (re.compile('<br>\n{0,1}', re.I), ' '),  # This appears to be specific formatting for VRT NU, but unwanted by us
    (re.compile('(&nbsp;\n){2,}', re.I), '\n'),  # Remove repeating non-blocking spaced newlines
]


def html_to_kodi(text):
    """Convert VRT HTML content into Kodit formatted text"""
    for key, val in HTML_MAPPING:
        text = key.sub(val, text)
    return unescape(text).strip()
