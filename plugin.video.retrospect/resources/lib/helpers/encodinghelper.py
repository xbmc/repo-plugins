# SPDX-License-Identifier: GPL-3.0-or-later
import base64
import hashlib

from resources.lib.backtothefuture import PY3


class EncodingHelper(object):
    """Class that is intended to help with the encoding and decoding
    of text.

    """

    @staticmethod
    def decode_base64(data):
        """Decodes a Base64 encoded string into a normal string.

        @param data:  string - Base64 encode string withdata to decode.
        @return: Normal string representing the Base64 encoded string.

        """

        return base64.b64decode(data)

    @staticmethod
    def encode_base64(data):
        """ Encodes the given string into base64 bytes.

        :param str data:
        :return: bytes
        """

        if PY3 and isinstance(data, str):
            data = data.encode()

        return base64.b64encode(data)

    @staticmethod
    def encode_md5(data, to_upper=True):
        """Encodes the selected string into an MD5 hashTool.

        @param data:        string        - Data for which the MD5 should be calculated.
        @param to_upper:    [opt] boolean - Result should be upper-case. (default: True)

        @return: an MD5 encoded representation of the input, ether upper-case (default)
                 or lower-case.

        """

        hash_tool = hashlib.md5()
        if PY3 and isinstance(data, str):
            data = data.encode()

        hash_tool.update(data)
        if to_upper:
            return hash_tool.hexdigest().upper()
        else:
            return hash_tool.hexdigest()
