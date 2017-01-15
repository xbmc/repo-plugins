#!/usr/bin/env python
'''
Test for connection status of each channel

This is a bit messy, should redo parser
TODO Need to test Sonica and Radio3

'''

import sys
import os.path
import urllib2

CUR_DIR = os.path.dirname(__file__)
RESOURCES_DIR = os.path.abspath(os.path.join(CUR_DIR, os.path.pardir, 'resources', 'lib'))
sys.path.append(RESOURCES_DIR)

import CBCJsonParser

'''
Checks that it is possible to connect to the stream specified by region and channel
TODO Fix unicode situation

Args:
    region: The region served by channel
    channel: radio1 or radio2
    qual: 0 for High, 1 for Low
'''
def checkRegionConnection(region, channel, qual=0):
    if qual is 0:
        quality = "HQ"
    else:
        quality = "SQ"
    if channel == "radio1":
        try:
            url = CBCJsonParser.parse_pls(CBCJsonParser.get_R1_streams(region)[qual])
        except (UnicodeError, UnicodeWarning, TypeError):
            print("Unicode error for region " + region)
            return

    elif channel == "radio2":
        url = CBCJsonParser.parse_pls(CBCJsonParser.get_R2_streams(region))

    r = urllib2.urlopen(url)
    if r.getcode() < 400:
        print("Success: Connection to {} {} stream for: {}".format(quality, channel, region))
    else:
        print("Cannot access stream for: " + region)

if __name__ == "__main__":
    # Radio 1 High quality check
    for region in CBCJsonParser.get_regions('radio1'):
        checkRegionConnection(region, 'radio1', 0)

    # Radio 1 Low quality check
    for region in CBCJsonParser.get_regions('radio1'):
        checkRegionConnection(region, 'radio1', 1)

    # Radio 2 check
    for region in CBCJsonParser.get_regions('radio2'):
        checkRegionConnection(region, 'radio2')
