# -*- coding: utf-8 -*-
# Copyright: (c) 2022, darodi
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

class MediaStream:
    """Class that represents a Mediastream with <url> and a specific <bitrate> and a specific <resolution>"""

    def __init__(self, url, bitrate=0, resolution="0x0", *args):
        """Initialises a new MediaStream

        :param str url:                 The URL of the stream.
        :param int|str bitrate:         The bitrate of the stream (defaults to 0).
        :param str resolution:          The resolution of the stream (defaults to 0x0).
        :param tuple[str,str] args:     (name, value) for any stream property.

        """

        self.resolution = resolution
        self.url = url
        self.bitrate = int(bitrate)

    def __eq__(self, other):
        """ Checks 2 items for Equality

        Equality takes into consideration:

        * The url of the MediaStream

        :param MediaStream other:   The stream to check for equality.

        :return: True if the items are equal.
        :rtype: bool

        """

        # also check for URL
        if other is None:
            return False

        return self.url == other.url

    def __str__(self):
        """ String representation

        :return: The String representation
        :rtype: str

        """
        text = "MediaStream: %s [bitrate=%s, resolution=%s]" % (self.url, self.bitrate, self.resolution)
        return text
