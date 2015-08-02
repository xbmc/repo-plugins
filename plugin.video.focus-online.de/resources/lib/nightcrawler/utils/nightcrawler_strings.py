__author__ = 'bromix'

import urllib
import re
import datetime


def to_utf8(text):
    result = text
    if isinstance(text, unicode):
        result = text.encode('utf-8')
        pass

    return result


def to_unicode(text):
    result = text
    if isinstance(text, str):
        result = text.decode('utf-8')
        pass

    return result