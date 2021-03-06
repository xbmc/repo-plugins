import time
import datetime
import html
import urllib.parse

import hof


def colorize(text, color):
    """
    color: a hex color string (RRGGBB or #RRGGBB) or None
    """
    if not color:
        return text
    if color.startswith('#'):
        color = color[1:]
    return '[COLOR ff' + color + ']' + text + '[/COLOR]'


def format_title_and_subtitle(title, subtitle=None):
    label = u'[B]{title}[/B]'.format(title=html.unescape(title))
    # suffixes
    if subtitle:
        label += u' - {subtitle}'.format(subtitle=html.unescape(subtitle))
    return label


def encode_string(str):
    return urllib.parse.quote_plus(str, encoding='utf-8', errors='replace')


def decode_string(str):
    return urllib.parse.unquote_plus(str, encoding='utf-8', errors='replace')


def parse_date(datestr):
    # remove weekday & timezone
    datestr = str.join(' ', datestr.split(None)[1:5])

    date = None
    # workaround for datetime.strptime not working (NoneType ???)
    try:
        date = datetime.datetime.strptime(datestr, '%d %b %Y %H:%M:%S')
    except TypeError:
        date = datetime.datetime.fromtimestamp(time.mktime(
            time.strptime(datestr, '%d %b %Y %H:%M:%S')))
    return date


def past_week():
    today = datetime.date.today()
    one_day = datetime.timedelta(days=1)

    for i in range(0, 8):  # TODO: find better interval
        yield today - (one_day * i)
