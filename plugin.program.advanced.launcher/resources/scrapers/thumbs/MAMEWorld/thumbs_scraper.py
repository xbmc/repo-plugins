# -*- coding: UTF-8 -*-

import os
import re
import urllib

# Thumbnails list scrapper
def _get_thumbnails_list(system,search,region,imgsize):
    covers = []
    results = []
    try:
        f = urllib.urlopen('http://maws.mameworld.info/maws/romset/'+search)
        page = f.read().replace('\r\n', '').replace('\n', '')
        results = re.findall('document.snapshot.src=\'(.*?)\';return false;', page)
        for index, line in enumerate(results):
            covers.append(['http://maws.mameworld.info/maws/'+line,'http://maws.mameworld.info/maws/'+line,'Image '+str(index+1)])
        return covers
    except:
        return covers

# Get Thumbnail scrapper
def _get_thumbnail(image_url):
    return image_url

