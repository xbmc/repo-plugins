# SPDX-License-Identifier: GPL-3.0-or-later

from resources.lib.urihandler import UriHandler
from resources.lib.logger import Logger
from resources.lib.regexer import Regexer


class F4m(object):
    def __init__(self):
        pass

    @staticmethod
    def get_streams_from_f4m(url, headers=None):
        """ Parsers standard F4m lists and returns a list of tuples with streams and bitrates that can be used by
        other methods

        :param str url:                 The url to download.
        :param dict[str,str] headers:   Possible HTTP Headers.

        Can be used like this:

            for s, b in F4m.get_streams_from_f4m(url):
                item.complete = True
                # s = self.get_verifiable_video_url(s)
                item.add_stream(s, b)

        """

        streams = []

        data = UriHandler.open(url, additional_headers=headers)
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
