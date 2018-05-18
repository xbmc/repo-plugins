#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# encoding=utf8
import sys
reload(sys)
sys.setdefaultencoding('utf8')
# solution from: http://stackoverflow.com/1/753052/strip-html-from-strings-in-python
from HTMLParser import HTMLParser


class MLStripper(HTMLParser):
    def __init__(self):
        self.reset()
        self.fed = []

    def handle_data(self, d):
        self.fed.append(d)

    def handle_entityref(self, name):
        self.fed.append('&%s;' % name)

    def get_data(self):
        return ''.join(self.fed)


def html_to_text(html_str):
    data = ""
    if html_str is not None:
        s = MLStripper()
        s.feed(html_str)
        data = s.get_data()
    return data
