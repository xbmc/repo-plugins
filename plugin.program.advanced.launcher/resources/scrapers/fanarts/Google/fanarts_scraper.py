# -*- coding: UTF-8 -*-

import xbmc
import os
import time
import urllib,re
import simplejson

CACHE_PATH = xbmc.translatePath('special://profile/addon_data/plugin.program.advanced.launcher/cache/')
if not os.path.exists(CACHE_PATH): os.makedirs(CACHE_PATH)
for each in os.listdir(CACHE_PATH):
    os.remove(os.path.join(CACHE_PATH.decode('utf-8','ignore'),each.decode('utf-8','ignore')))

# Thumbnails list scrapper
def _get_fanarts_list(system,search,imgsize):
    qdict = {'q':search,'imgsz':imgsize}
    query = urllib.urlencode(qdict)
    base_url = ('http://ajax.googleapis.com/ajax/services/search/images?v=1.0&start=%s&rsz=8&%s')
    covers = []
    results = []
    try:
        for start in (0,8,16,24):
            url = base_url % (start,query)
            search_results = urllib.urlopen(url)
            json = simplejson.loads(search_results.read())
            search_results.close()
            results += json['responseData']['results']
        for index, images in enumerate(results):
            thumbnail = os.path.join(CACHE_PATH,str(index) + str(time.time()) + '.jpg')
            h = urllib.urlretrieve(images['tbUrl'],thumbnail)
            covers.append((images['url'],thumbnail,"Image "+str(index+1)))
        return covers
    except:
        return covers

# Get Thumbnail scrapper
def _get_fanart(image_url):
     return image_url

