# SPDX-License-Identifier: CC-BY-NC-SA-4.0
import re

from resources.lib.backtothefuture import PY2, PY3, unichr

if PY2:
    import urllib
    # noinspection PyUnresolvedReferences
    import htmlentitydefs as htmldefs
else:
    # noinspection PyUnresolvedReferences
    import urllib.parse
    import html.entities as htmldefs

from resources.lib.logger import Logger


class HtmlEntityHelper(object):
    """Used for HTML converting"""

    def __init__(self):
        """Initialises the class"""

        raise NotImplementedError("Just statics")

    @staticmethod
    def strip_amp(data):
        """Replaces the "&amp;" with "&"


        :param str data:     Data to search and replace in.

        :return: The data with replaced values.
        :rtype: str

        """

        return data.replace("&amp;", "&")

    @staticmethod
    def convert_html_entities(html):
        """Convert the HTML entities into their real characters

        :param str|None html: The HTML to convert.

        :return: The HTML with converted characters.
        :rtype: str

        """

        try:
            return HtmlEntityHelper.__convert_html_entities(html)
        except:
            Logger.error("Error converting: %s", html, exc_info=True)
            return html

    @staticmethod
    def url_encode(url):
        """Converts an URL in url encode characters

        :param str url: The data to URL encode.

        :return: Encoded URL like this. Example: '/~connolly/' yields '/%7econnolly/'.
        :rtype: str

        """

        if PY3:
            # noinspection PyUnresolvedReferences
            return urllib.parse.quote(url)

        # noinspection PyUnresolvedReferences
        if isinstance(url, unicode):
            Logger.trace("Unicode url: %s", url)
            # noinspection PyUnresolvedReferences
            return urllib.quote(url.encode())
        else:
            # this is the main time waster
            # noinspection PyUnresolvedReferences
            return urllib.quote(url)

    @staticmethod
    def url_decode(url):
        """Converts an URL encoded text in plain text

        :param str url:     The URL encoded text to decode to decode.

        :return: Decoded URL like this. Example: '/%7econnolly/' yields '/~connolly/'.
        :rtype: str

        """

        if PY2:
            # noinspection PyUnresolvedReferences
            return urllib.unquote(url)

        # noinspection PyUnresolvedReferences
        return urllib.parse.unquote(url)

    @staticmethod
    def __convert_html_entities(html):
        """Convert the entities in HTML using the HTMLEntityConverter into
        their real characters.

        :param str html: The HTML to convert

        :return: The HTML with converted characters
        :rtype: str

        """

        return re.sub(r"&(#?x?)(\w+?);", HtmlEntityHelper.__html_entity_converter, html)

    @staticmethod
    def __html_entity_converter(entity):
        """Substitutes an HTML entity with the correct character

        :param re.MatchObject entity: Value of the HTML entity without the '&'

        :rtype: str
        :return: Replaces &#xx where 'x' is single digit, or &...; where '.' is a
        character into the real character. That character is returned.

        """

        # Logger.Debug("1:%s, 2:%s", entity.group(1), entity.group(2))
        try:
            if entity.group(1) == "#":
                # Logger.Trace("%s: %s", entity.group(2), chr(int(entity.group(2))))
                return unichr(int(entity.group(2), 10))

            elif entity.group(1) == "#x":
                # check for hex values
                return unichr(int(entity.group(2), 16))

            elif entity.group(2) == 'apos':
                # this one is not covert in name2codepoint
                return "'"

            else:
                # Logger.Trace("%s: %s", entity.group(2), htmldefs.name2codepoint[entity.group(2)])
                return unichr(htmldefs.name2codepoint[entity.group(2)])
        except:
            Logger.error("Error converting HTMLEntities: &%s%s", entity.group(1), entity.group(2), exc_info=True)
            return '&%s%s;' % (entity.group(1), entity.group(2))
