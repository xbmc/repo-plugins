# -*- coding: utf-8 -*-
from __future__ import absolute_import

# Standard Library Imports
import sys
import re

# Kodi imports
import xbmc

try:
    import urllib.parse as urlparse
except ImportError:
    # noinspection PyUnresolvedReferences
    import urlparse

PY3 = sys.version_info[0] >= 3

# Unicode Type object, unicode on python2 or str on python3
unicode_type = type(u"")

string_map = {}
"""
Dict of localized string references used in conjunction with 
:class:`Script.localize<codequick.script.Script.localize>`.
Allowing you to use the string as the localized string reference.

.. note:: It is best if you set the string references at the top of your add-on python file.

:example:
    >>> Script.localize(30001)
    "Toutes les vidéos"
    >>> 
    >>> # Add reference id for "All Videos" so you can use the string name instead.
    >>> utils.string_map["All Videos": 30001]
    >>> Script.localize("All Videos")
    "Toutes les vidéos"
"""


def keyboard(heading, default="", hidden=False):
    """
    Show a keyboard dialog.

    :param str heading: Keyboard heading.
    :param str default: [opt] Default text.
    :param bool hidden: [opt] ``True`` for hidden text entry.

    :return: Returns the user input as unicode.
    :rtype: str
    """
    # Convert inputs to strings if required
    heading = ensure_native_str(heading)
    default = ensure_native_str(default)

    # Show the onscreen keyboard
    kb = xbmc.Keyboard(default, heading, hidden)
    kb.doModal()

    # Return user input only if 'OK' was pressed (confirmed)
    if kb.isConfirmed():
        text = kb.getText()
        return text.decode("utf8") if isinstance(text, bytes) else text
    else:
        return u""  # pragma: no cover


def parse_qs(qs, keep_blank_values=False, strict_parsing=False):
    """
    Parse a "urlencoded" query string, and return the data as a dictionary.

    Parse a query string given as a string or unicode argument (data of type application/x-www-form- urlencoded).
    Data is returned as a dictionary. The dictionary keys are the "Unique" query variable names and
    the values are "Unicode" values for each name.

    The optional argument ``keep_blank_values``, is a flag indicating whether blank values in percent-encoded queries
    should be treated as a blank string.  A ``True`` value indicates that blanks should be retained as a blank string.
    The default ``False`` value indicates that blank values are to be ignored and treated as if they were not included.

    The optional argument ``strict_parsing``, is a flag indicating what to do with parsing errors. If ``False``
    (the default), errors are silently ignored. If ``True``, errors raise a "ValueError" exception.

    :param str qs: Percent-encoded "query string" to be parsed, or a URL with a "query string".
    :param bool keep_blank_values: ``True`` to keep blank values, else discard.
    :param bool strict_parsing: ``True`` to raise "ValueError" if there are parsing errors, else silently ignore.

    :return: Returns a dictionary of key/value pairs, with all keys and values as "Unicode".
    :rtype: dict

    :raises ValueError: If duplicate query field names exists or if there is a parsing error.

    :example:
        >>> parse_qs("http://example.com/path?q=search&safe=no")
        {u"q": u"search", u"safe": u"no"}
        >>> parse_qs(u"q=search&safe=no")
        {u"q": u"search", u"safe": u"no"}
    """
    params = {}
    qs = ensure_native_str(qs)
    parsed = urlparse.parse_qsl(qs.split("?", 1)[-1], keep_blank_values, strict_parsing)
    if PY3:
        for key, value in parsed:
            if key not in params:
                params[key] = value
            else:
                # Only add keys that are not already added, multiple values are not supported
                raise ValueError("encountered duplicate param field name: '%s'" % key)
    else:
        for bkey, value in parsed:
            ukey = bkey.decode("utf8")
            if ukey not in params:
                params[ukey] = value.decode("utf8")
            else:
                # Only add keys that are not already added, multiple values are not supported
                raise ValueError("encountered duplicate param field name: '%s'" % bkey)

    # Return the params with all keys and values as unicode
    return params


def urljoin_partial(base_url):
    """
    Construct a full (absolute) URL by combining a base URL with another URL.

    This is useful when parsing HTML, as the majority of links would be relative links.

    Informally, this uses components of the base URL, in particular the addressing scheme,
    the network location and (part of) the path, to provide missing components in the relative URL.

    Returns a new "partial" object which when called, will pass ``base_url`` to :func:`urlparse.urljoin` along with the
    supplied relative URL.

    :param str base_url: The absolute URL to use as the base.
    :returns: A partial function that accepts a relative URL and returns a full absolute URL.
    
    :example:
        >>> url_constructor = urljoin_partial("https://google.ie/")
        >>> url_constructor("/path/to/something")
        "https://google.ie/path/to/something"
        >>> url_constructor("/gmail")
        "https://google.ie/gmail"
    """
    base_url = ensure_unicode(base_url)

    def wrapper(url):
        """
        Construct a full (absolute) using saved base url.

        :param str url: The relative URL to combine with base.
        :return: Absolute url.
        :rtype: str
        """
        return urlparse.urljoin(base_url, ensure_unicode(url))

    return wrapper


def strip_tags(html):
    """
    Strips out HTML tags and return plain text.

    :param str html: HTML with text to extract.
    :returns: Html with tags striped out
    :rtype: str

    :example:
        >>> strip_tags('<a href="http://example.com/">I linked to <i>example.com</i></a>')
        "I linked to example.com"
    """
    # This will fail under python3 when html is of type bytes
    # This is ok sence you will have much bigger problems if you are still using bytes on python3
    return re.sub("<[^<]+?>", "", html)


def ensure_native_str(data, encoding="utf8"):
    """
    Ensures that the given string is returned as a native str type, ``bytes`` on Python 2, ``unicode`` on Python 3.

    :param data: String to convert if needed.
    :param str encoding: [opt] The encoding to use if needed..
    :returns: The given string as a native ``str`` type.
    :rtype: str
    """
    # This is the fastest way
    # that I can find to do this
    if isinstance(data, str):
        return data
    elif isinstance(data, unicode_type):
        # Only executes on python 2
        return data.encode(encoding)
    elif isinstance(data, bytes):
        # Only executes on python 3
        return data.decode(encoding)
    else:
        return str(data)


def ensure_unicode(data, encoding="utf8"):
    """
    Ensures that the given string is return as type ``unicode``.

    :type data: str or bytes
    :param data: String to convert if needed.
    :param str encoding: [opt] The encoding to use if needed..

    :returns: The given string as type ``unicode``.
    :rtype: str
    """
    return data.decode(encoding) if isinstance(data, bytes) else unicode_type(data)


def bold(text):
    """
    Return Bolded text.

    :param str text: Text to bold.
    :returns: Bolded text.
    :rtype: str
    """
    return "[B]%s[/B]" % text


def italic(text):
    """
    Return Italic text.

    :param str text: Text to italic.
    :returns: Italic text.
    :rtype: str
    """
    return "[I]%s[/I]" % text


def color(text, color_code):
    """
    Return Colorized text of givin color.

    :param str text: Text to italic.
    :param str color_code: Color to change text to.
    :returns: Colorized text.
    :rtype: str
    """
    return "[COLOR %s]%s[/COLOR]" % (color_code, text)
