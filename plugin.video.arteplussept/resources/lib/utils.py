import datetime
import dateutil.parser
import xbmc
import html
import urllib.parse


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
    date = None
    try:
        date = dateutil.parser.parse(datestr)
    except dateutil.parser.ParserError as e:
        logmsg = "[{addon_id}] Problem with parsing date: {error}".format(addon_id="plugin.video.arteplussept", error=e)
        xbmc.log(msg=logmsg, level=xbmc.LOGWARNING)
    return date


def past_week():
    today = datetime.date.today()
    one_day = datetime.timedelta(days=1)

    for i in range(0, 8):  # TODO: find better interval
        yield today - (one_day * i)
