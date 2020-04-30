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


def html_to_kodilabel(text):
    """Convert VRT HTML content into Kodit formatted text"""
    for key, val in HTML_MAPPING:
        text = key.sub(val, text)
    return unescape(text).strip()


def reformat_url(url, url_type, domain='www.vrt.be'):
    """Convert a url"""
    # Clean URLs with a hash in it
    pos = url.find('#')
    if pos >= 0:
        url = url[:pos]
    # long url
    if url_type == 'long':
        if url.startswith('/vrtnu/a-z'):
            return 'https://' + domain + url
        if url.startswith('//'):  # This could be //www.vrt.be, or //images.vrt.be
            return 'https:' + url
        return url
    # medium url
    if url_type == 'medium':
        if url.startswith('https:'):
            return url.replace('https:', '')
        if url.startswith('/vrtnu/a-z'):
            return '//' + domain + url
        return url
    # short url
    if url_type == 'short':
        if url.startswith('https://' + domain):
            return url.replace('https://' + domain, '')
        if url.startswith('//' + domain):
            return url.replace('//' + domain, '')
    return url


def program_to_url(program, url_type):
    """Convert a program url component (e.g. de-campus-cup) to:
        - a short programUrl (e.g. /vrtnu/a-z/de-campus-cup/)
        - a medium programUrl (e.g. //www.vrt.be/vrtnu/a-z/de-campus-cup/)
        - a long programUrl (e.g. https://www.vrt.be/vrtnu/a-z/de-campus-cup/)
   """
    url = None
    if program:
        # short programUrl
        if url_type == 'short':
            url = '/vrtnu/a-z/' + program + '/'
        # medium programUrl
        elif url_type == 'medium':
            url = '//www.vrt.be/vrtnu/a-z/' + program + '/'
        # long programUrl
        elif url_type == 'long':
            url = 'https://www.vrt.be/vrtnu/a-z/' + program + '/'
    return url


def url_to_program(url):
    """Convert
          - a targetUrl (e.g. //www.vrt.be/vrtnu/a-z/de-campus-cup.relevant/),
          - a short programUrl (e.g. /vrtnu/a-z/de-campus-cup/) or
          - a medium programUrl (e.g. //www.vrt.be/vrtnu/a-z/de-campus-cup/)
          - a long programUrl (e.g. https://www.vrt.be/vrtnu/a-z/de-campus-cup/)
        to a program url component (e.g. de-campus-cup).
        Any season or episode information is removed as well.
    """
    program = ''
    if url.startswith('https://www.vrt.be/vrtnu/a-z/'):
        # long programUrl or targetUrl
        program = url.split('/')[5]
    elif url.startswith('//www.vrt.be/vrtnu/a-z/'):
        # medium programUrl or targetUrl
        program = url.split('/')[5]
    elif url.startswith('/vrtnu/a-z/'):
        # short programUrl
        program = url.split('/')[3]
    if program.endswith('.relevant'):
        # targetUrl
        program = program.replace('.relevant', '')
    return program


def url_to_episode(url):
    """Convert a targetUrl (e.g. //www.vrt.be/vrtnu/a-z/buck/1/buck-s1a32/) to
        a short episode url (/vrtnu/a-z/buck/1/buck-s1a32/)
   """
    if url.startswith('https://www.vrt.be/vrtnu/a-z/'):
        # long episode url
        return url.replace('https://www.vrt.be/vrtnu/a-z/', '/vrtnu/a-z/')
    if url.startswith('//www.vrt.be/vrtnu/a-z/'):
        # medium episode url
        return url.replace('//www.vrt.be/vrtnu/a-z/', '/vrtnu/a-z/')
    if url.startswith('/vrtnu/a-z/'):
        # short episode url
        return url
    return None


def video_to_api_url(url):
    """Convert a full VRT NU url (e.g. https://www.vrt.be/vrtnu/a-z/de-ideale-wereld/2019-nj/de-ideale-wereld-d20191010/)
        to a VRT Search API url (e.g. //www.vrt.be/vrtnu/a-z/de-ideale-wereld/2019-nj/de-ideale-wereld-d20191010/)
   """
    if url.startswith('https:'):
        url = url.replace('https:', '')
        # NOTE: add a trailing slash again because routing plugin removes it and VRT NU Search API needs it
        if not url.endswith('/'):
            url += '/'
    return url


def program_to_id(program):
    """Convert a program url component (e.g. de-campus-cup)
        to a favorite program_id (e.g. vrtnuazdecampuscup), used for lookups in favorites dict"""
    return 'vrtnuaz' + program.replace('-', '')


def assetpath_to_id(assetpath):
    """Convert an assetpath (e.g. /content/dam/vrt/2019/08/14/woodstock-depot_WP00157456)
        to a resumepoint asset_id (e.g. contentdamvrt20190814woodstockdepotwp00157456)"""
    # The video has no assetPath, so we return None instead
    if assetpath is None:
        return None
    return assetpath.translate({ord(char): None for char in '/-_'}).lower()


def play_url_to_id(url):
    """Convert a plugin:// url (e.g. plugin://plugin.video.vrt.nu/play/id/vid-5b12c0f6-b8fe-426f-a600-557f501f3be9/pbs-pub-7e2764cf-a8c0-4e78-9cbc-46d39381c237)
        to an id dictionary (e.g. {'video_id': 'vid-5b12c0f6-b8fe-426f-a600-557f501f3be9'}
   """
    play_id = dict()
    if 'play/id/' in url:
        play_id['video_id'] = url.split('play/id/')[1].split('/')[0]
    elif 'play/upnext/' in url:
        play_id['video_id'] = url.split('play/upnext/')[1]
    elif '/play/url/' in url:
        play_id['video_url'] = video_to_api_url(url.split('play/url/')[1])
    return play_id


def shorten_link(url):
    """Create a link that is as short as possible"""
    if url is None:
        return None
    if url.startswith('https://www.vrt.be/vrtnu/'):
        # As used in episode search result 'permalink'
        return url.replace('https://www.vrt.be/vrtnu/', 'vrtnu.be/')
    if url.startswith('//www.vrt.be/vrtnu/'):
        # As used in program a-z listing 'targetUrl'
        return url.replace('//www.vrt.be/vrtnu/', 'vrtnu.be/')
    return url


def add_https_proto(url):
    """Add HTTPS protocol to URL that lacks it"""
    if url.startswith('//'):
        return 'https:' + url
    if url.startswith('/'):
        return 'https://www.vrt.be' + url
    return url


def realpage(page):
    """Convert a URL parameter page value into an integer"""
    try:
        page = int(page)
    except ValueError:
        return 1
    if page < 1:
        return 1
    return page


def find_entry(dlist, key, value, default=None):
    """Find (the first) dictionary in a list where key matches value"""
    return next((entry for entry in dlist if entry.get(key) == value), default)


def youtube_to_plugin_url(url):
    """Convert a YouTube URL to a Kodi plugin URL"""
    url = url.replace('https://www.youtube.com/', 'plugin://plugin.video.youtube/')
    if not url.endswith('/'):
        url += '/'
    return url
