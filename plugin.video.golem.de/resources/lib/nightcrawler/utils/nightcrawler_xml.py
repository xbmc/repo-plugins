__author__ = 'bromix'

import HTMLParser
import re


def decode(xml_text):
    parser = HTMLParser.HTMLParser()
    return re.sub(r'(&.+?;)', lambda m: parser.unescape(m.group()), xml_text)