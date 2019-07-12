#===============================================================================
# LICENSE Retrospect-Framework - CC BY-NC-ND
#===============================================================================
# This work is licenced under the Creative Commons
# Attribution-Non-Commercial-No Derivative Works 3.0 Unported License. To view a
# copy of this licence, visit http://creativecommons.org/licenses/by-nc-nd/3.0/
# or send a letter to Creative Commons, 171 Second Street, Suite 300,
# San Francisco, California 94105, USA.
#===============================================================================

from backtothefuture import PY2
if PY2:
    # noinspection PyPep8Naming,PyUnresolvedReferences
    import cPickle as pickle
else:
    import pickle

import base64
from functools import reduce

from logger import Logger


class Pickler:
    # hack for Base64 chars that are URL encoded. We only need 3 (or 6 to make it case-insenstive)
    # and then we don't need to use urlencode which is slow in Python.
    __Base64CharsDecode = {
        "-": "\n",
        "%3d": "=",
        "%3D": "=",
        "%2f": "/",
        "%2F": "/",
        "%2b": "+",
        "%2B": "+"
    }
    __Base64CharsEncode = {
        "\n": "-",
        "=": "%3d",
        "/": "%2f",
        "+": "%2b",
    }

    def __init__(self):
        # store some vars for speed optimization
        self.__pickleContainer = dict()  # : storage for pickled items to prevent duplicate pickling

    def de_pickle_media_item(self, hex_string):
        """ De-serializes a serialized mediaitem.

        Warning: Pickling from Python2 to Python3 will not work.

        :param str|unicode hex_string: Base64 encoded string that should be decoded.

        :return: The object that was Pickled and Base64 encoded.

        """

        hex_string = hex_string.rstrip(' ')
        hex_string = reduce(lambda x, y: x.replace(y, Pickler.__Base64CharsDecode[y]),
                            Pickler.__Base64CharsDecode.keys(),
                            hex_string)

        Logger.trace("DePickle: HexString: %s (might be truncated)", hex_string[0:256])

        pickle_string = base64.b64decode(hex_string)  # type: bytes
        pickle_item = pickle.loads(pickle_string)  # type: object
        return pickle_item

    def pickle_media_item(self, item):
        """ Serialises a mediaitem using Pickle

        :param Any item: The item that should be serialized
        :return: A pickled and Base64 encoded serialization of the `item`.
        :rtype: str

        """

        if item.guid in self.__pickleContainer:
            Logger.trace("Pickle Container cache hit: %s", item.guid)
            return self.__pickleContainer[item.guid]

        pickle_string = pickle.dumps(item, protocol=pickle.HIGHEST_PROTOCOL)  # type: bytes
        hex_bytes = base64.b64encode(pickle_string)  # type: bytes
        hex_string = hex_bytes.decode()  # type: str

        # if not unquoted, we must replace the \n's for the URL
        hex_string = reduce(lambda x, y: x.replace(y, Pickler.__Base64CharsEncode[y]),
                            Pickler.__Base64CharsEncode.keys(),
                            hex_string)

        self.__pickleContainer[item.guid] = hex_string
        return hex_string

    def validate(self, test, raise_on_missing=False, logger=None):
        """ Validates if in instance has all properties after depickling. The __class__ of
        the 'test' should implement a self.__dir__(self) that returns the required attributes.

        :param any test:                Item to test
        :param bool raise_on_missing:   If True an error will be raised on failure
        :param Logger|None logger:      Pass a loger in

        :return: None if no error, or an error message if an error occurred.
        :rtype: str|None

        """

        if logger is not None:
            Logger.trace("Testing: %s", test.__dir__())

        # the default dir() does not work for Android at the moment.
        for attribute in test.__dir__():
            if logger is not None:
                logger.trace("Testing: %s", attribute)

            # manage private attributes
            if attribute.startswith("__"):
                attribute = "_%s%s" % (test.__class__.__name__, attribute)

            if not hasattr(test, attribute):
                error = "Attribute Missing: %s" % attribute

                if logger is not None:
                    logger.warning(error)
                if raise_on_missing:
                    raise Exception(error)
                return error

        # We are good
        return None
