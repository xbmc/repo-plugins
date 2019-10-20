# -*- coding: utf-8 -*-
import datetime

def sortedDictKeys(adict):
    keys = list(adict.keys())
    keys.sort()
    return keys

def daterange(start_date, end_date):
    for n in range((end_date - start_date).days + 1):
        yield end_date - datetime.timedelta(n)
