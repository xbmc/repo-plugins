"""Utility methods for:
- strings encoding/decoding for URL usage
- age restrictions/MPAA mapping qnd warnings
"""
import urllib.parse


def encode_string(string):
    """Return escaped string to be used as URL. More details in
    https://docs.python.org/3/library/urllib.parse.html#urllib.parse.quote_plus"""
    return urllib.parse.quote_plus(string, encoding='utf-8', errors='replace')


def decode_string(string):
    """Return unescaped string to be human readable. More details in
    https://docs.python.org/3/library/urllib.parse.html#urllib.parse.unquote_plus"""
    return urllib.parse.unquote_plus(string, encoding='utf-8', errors='replace')


def mpaa_from_age(age):
    """Map an integer age restriction to an MPAA rating string.

    Returns 'Unknown' when mapping cannot be determined.
    """
    mpaa = 'Unknown'
    if isinstance(age, int):
        if age == 0:
            mpaa = 'G'
        elif 0 < age < 12:
            mpaa = 'PG'
        elif 12 <= age < 16:
            mpaa = 'PG-13'
        elif 16 <= age < 18:
            mpaa = 'R'
        elif 18 <= age:
            mpaa = 'NC-17'
    return mpaa


def warn_if_age_restricted(plugin, mpaa):
    """Return True if the MPAA rating requires a warning
    i.e. when MPAA is in ('PG-13', 'R', 'NC-17')
    and notify with a warning translated message.

    Parameters:
    - plugin: the xbmcswift2 Plugin instance used to translate and display the
      notification. If falsy, only the boolean result is returned.
    - mpaa: MPAA rating string to evaluate.
    """
    restricted = bool(mpaa) and mpaa in ('PG-13', 'R', 'NC-17')
    if restricted and plugin:
        msg = plugin.addon.getLocalizedString(30055).format(label=mpaa)
        plugin.notify(msg=msg, image='warning')
    return restricted
