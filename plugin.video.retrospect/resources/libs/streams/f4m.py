#===============================================================================
# LICENSE Retrospect-Framework - CC BY-NC-ND
#===============================================================================
# This work is licenced under the Creative Commons
# Attribution-Non-Commercial-No Derivative Works 3.0 Unported License. To view a
# copy of this licence, visit http://creativecommons.org/licenses/by-nc-nd/3.0/
# or send a letter to Creative Commons, 171 Second Street, Suite 300,
# San Francisco, California 94105, USA.
#===============================================================================

from urihandler import UriHandler
from proxyinfo import ProxyInfo
from logger import Logger
from regexer import Regexer


class F4m(object):
    def __init__(self):
        pass

    @staticmethod
    def get_streams_from_f4m(url, proxy=None, headers=None):
        """ Parsers standard F4m lists and returns a list of tuples with streams and bitrates that can be used by
        other methods

        :param ProxyInfo proxy:         The proxy to use for opening.
        :param str url:                 The url to download.
        :param dict[str,str] headers:   Possible HTTP Headers.

        Can be used like this:

            part = item.create_new_empty_media_part()
            for s, b in F4m.get_streams_from_f4m(url, self.proxy):
                item.complete = True
                # s = self.get_verifiable_video_url(s)
                part.append_media_stream(s, b)

        """

        streams = []

        data = UriHandler.open(url, proxy, additional_headers=headers)
        Logger.trace(data)
        Logger.debug("Processing F4M Streams: %s", url)
        needle = '<media href="([^"]+)"[^>]*bitrate="([^"]+)"'
        needles = Regexer.do_regex(needle, data)

        base_url_logged = False
        base_url = url[:url.rindex("/")]
        for n in needles:
            # see if we need to append a server path
            Logger.trace(n)
            if "://" not in n[0]:
                if not base_url_logged:
                    Logger.trace("Using base_url %s for F4M", base_url)
                    base_url_logged = True
                stream = "%s/%s" % (base_url, n[0])
            else:
                if not base_url_logged:
                    Logger.trace("Full url found in F4M")
                    base_url_logged = True
                stream = n[0]
            bitrate = int(n[1])
            streams.append((stream, bitrate))

        Logger.debug("Found %s substreams in F4M", len(streams))
        return streams
