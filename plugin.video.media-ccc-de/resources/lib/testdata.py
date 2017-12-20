# -*- coding: utf-8 -*-

from __future__ import print_function

import json
import os.path


DATAPATH = os.path.join(os.path.dirname(__file__), "../data")


def getfile(filename):
    with open(os.path.join(DATAPATH, filename), "r") as f:
        return json.load(f)
