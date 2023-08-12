"""Utility methods mainly to format strings and manipulate date"""
import datetime
import html
import urllib.parse
# pylint: disable=import-error
import dateutil.parser
# pylint: disable=import-error
from xbmcswift2 import xbmc


def format_live_title_and_subtitle(title, subtitle=None):
    """Orange prefix LIVE for live stream"""
    return f"[COLOR ffffa500]LIVE[/COLOR] - {format_title_and_subtitle(title, subtitle)}"

def colorize(text, color):
    """
    Wrap text to be display with color
    :param str text: text to colorize
    :param str color: a hex color string (RRGGBB or #RRGGBB) or None
    """
    if not color:
        return text
    if color.startswith('#'):
        color = color[1:]
    return f"[COLOR ff{color}]{text}[/COLOR]"


def format_title_and_subtitle(title, subtitle=None):
    """Build string for menu entry thanks to title and optionally subtitle"""
    label = f"[B]{html.unescape(title)}[/B]"
    # suffixes
    if subtitle:
        label += f" - {html.unescape(subtitle)}"
    return label


def encode_string(string):
    """Return escaped string to be used as URL. More details in
    https://docs.python.org/3/library/urllib.parse.html#urllib.parse.quote_plus"""
    return urllib.parse.quote_plus(string, encoding='utf-8', errors='replace')


def decode_string(string):
    """Return unescaped string to be human readable. More details in
    https://docs.python.org/3/library/urllib.parse.html#urllib.parse.unquote_plus"""
    return urllib.parse.unquote_plus(string, encoding='utf-8', errors='replace')


def parse_date_hbbtv(datestr):
    """Try to parse ``datestr`` into a ``datetime`` object. Return ``None`` if parsing fails.
    Similar to parse_date_artetv."""
    date = None
    try:
        date = dateutil.parser.parse(datestr)
    except dateutil.parser.ParserError as error:
        xbmc.log(f"[plugin.video.arteplussept] Problem with parsing date: {error}",
                 level=xbmc.LOGWARNING)
    return date


def parse_date_artetv(datestr):
    """Try to parse ``datestr`` into a ``datetime`` object like 2022-07-01T03:00:00Z for instance.
     Return ``None`` if parsing fails.
     Similar to ``parse_date_hbbtv``"""
    date = None
    try:
        date = datetime.datetime.strptime(datestr, '%Y-%m-%dT%H:%M:%S%z')
    except TypeError:
        date = None
    return date


def is_playlist(program_id):
    """Return True if program_id is a str starting with PL- or RC-."""
    is_playlist_var = False
    if isinstance(program_id, str):
        is_playlist_var = program_id.startswith('RC-') or program_id.startswith('PL-')
    return is_playlist_var


def get_progress(item):
    """
    Return item progress or 0 as float.
    Never None, even if lastviewed or item is None.
    """
    # pylint raises that it is not snake_case. it's in uppercase, because it's a constant
    # pylint: disable=invalid-name
    DEFAULT_PROGRESS = 0.0
    if not item:
        return DEFAULT_PROGRESS
    if not item.get('lastviewed'):
        return DEFAULT_PROGRESS
    if not item.get('lastviewed').get('progress'):
        return DEFAULT_PROGRESS
    return float(item.get('lastviewed') and item.get('lastviewed').get('progress'))
