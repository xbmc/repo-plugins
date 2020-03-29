# SPDX-License-Identifier: CC-BY-NC-SA-4.0
import base64
import hashlib

from resources.lib.backtothefuture import PY3, unichr


class EncodingHelper(object):
    """Class that is intended to help with the encoding and decoding
    of text.

    """

    def __init__(self):
        """Initialises the class with a text-encoder and -decoder.

        Python explanation of text encoding and decoding:

        s.decode(encoding)
            * <type 'str'> to <type 'unicode'>
        u.encode(encoding)
            * <type 'unicode'> to <type 'str'> (or Binary data)

        """

        # What to do with Encoding errors?
        #codecs.register_error('keep', EncodingHelper.__keep_handler)
        #self.decoder = decoder
        #self.encoder = encoder
        return

    @staticmethod
    def decode_base64(data):
        """Decodes a Base64 encoded string into a normal string.

        @param data:  string - Base64 encode string withdata to decode.
        @return: Normal string representing the Base64 encoded string.

        """

        return base64.b64decode(data)

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

    @staticmethod
    def __keep_handler(exc):
        """Sometimes the unicode decoding fails due to strange UTF-8 chars in
        string that should not be there. This method just converts the chars
        in the string to Unicode chars and then returns the as their unicode
        chars.

        Arguments:
        exc : UnicodeDecodeError - Exception thrown by Decode.


        Returns the same as the input but then Unicode:
        'Barnen p\xe5 Luna p\xe5 Svt.se' returns u'Barnen p\xe5 Luna p\xe5 Svt.se'

        """

        try:
            return_value = u''
            for c in exc.object[exc.start:exc.end]:
                # just convert each character as if it was Unicode to it's Unicode equivalent.
                return_value = u'%s%s' % (return_value, unichr(ord(c)))
        except:
            return_value = exc.object[exc.start:exc.end].decode(exc.encoding, 'replace')
        return return_value, exc.end
