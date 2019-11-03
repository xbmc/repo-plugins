# SPDX-License-Identifier: CC-BY-NC-SA-4.0

from resources.lib.regexer import Regexer
from resources.lib.logger import Logger
from resources.lib.urihandler import UriHandler


class Mms(object):
    """Class that could help with parsing of simple MMS Stream files"""
    def __init__(self):
        """Creates a class object. Should not be used. There are only static
        methods available.

        """

        raise NotImplementedError

    @staticmethod
    def get_mms_from_html(url, proxy=None, index=0):
        """Opens a URL with a MMS playlist and returns the first found stream
        in the MMS file. Searches for http://url and returns mms://url.

        Arguments:
        url : string - the URL to a MMS playlist.

        Keyword Arguments:
        proxy : Proxy - Proxy info
        index : int   - The index of the item to retrieve

        Returns:
        The first found stream in a MMS playlist. If the <url> ends with .mms
        it is assumed to already be a single stream. In that case the URL
        is returned.

        Example:
        Ref1=http://url.here/stream1
        Ref2=http://url.here/stream2

        Will return: mms://url.here.stream1

        """

        if url.find(".mms") > 0:
            Logger.info("MMS found in url: %s", url)
            return url

        Logger.debug("Parsing %s to find MMS", url)
        data = UriHandler.open(url, proxy=proxy)
        urls = Regexer.do_regex(r"[Rr]ef\d=http://([^\r\n]+)", data)

        if len(urls) > index:
            return "mms://%s" % (urls[index],)
        elif len(urls) > 0:
            return "mms://%s" % (urls[0],)
        else:
            return url

    @staticmethod
    def get_mms_from_asx(url, proxy):
        """Opens a URL with an ASX playlist and returns the first found stream
        in the ASX file. Only searches for mms://url.

        Arguments:
        url : string - the URL to an ASX playlist.

        Returns:
        The first found stream in an ASX playlist. If the <url> ends with .mms
        it is assumed to already be a single stream. In that case the URL
        is returned.

        Example:
        <asx version="3.0">
          <title>Example.com Live Stream</title>

          <entry>
            <title>Short Announcement to Play Before Main Stream</title>
            <ref href="http://example.com/announcement.wma" />
            <param name="aParameterName" value="aParameterValue" />
          </entry>

          <entry>
            <title>Example radio</title>
            <ref href="mms://example.com:8080" />
            <author>Example.com</author>
            <copyright>2005 Example.com</copyright>
          </entry>
        </asx>

        Will return: mms://example.com:8080 because it is the first MMS stream

        """

        if url.find(".mms") > 0:
            Logger.info("MMS found in url: %s", url)
            return url

        Logger.debug("Parsing %s to find MMS", url)
        data = UriHandler.open(url, proxy=proxy)
        urls = Regexer.do_regex(r'[Rr]ef href\W*=\W*"mms://([^"]+)"', data)

        if len(urls) > 0:
            return "mms://%s" % (urls[0],)
        else:
            return url
