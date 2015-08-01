__author__ = 'bromix'

import re


def strip_tags(html):
    return re.sub('<[^<]+?>', '', html)
