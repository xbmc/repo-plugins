# -*- coding: utf-8 -*-
# Module: default
# Author: jurialmunkey
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
from resources.lib.container import Container
from resources.lib.requestapi import _cache


if __name__ == '__main__':
    if _cache:
        Container().router()
