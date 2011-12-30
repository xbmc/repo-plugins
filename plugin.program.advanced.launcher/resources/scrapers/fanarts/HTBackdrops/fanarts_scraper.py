# -*- coding: UTF-8 -*-

import xbmc
import os
import time
import urllib,re

CACHE_PATH = xbmc.translatePath('special://profile/addon_data/plugin.program.advanced.launcher/cache/')
if not os.path.exists(CACHE_PATH): os.makedirs(CACHE_PATH)
for each in os.listdir(CACHE_PATH):
    os.remove(os.path.join(CACHE_PATH.decode('utf-8','ignore'),each.decode('utf-8','ignore')))

# Fanarts list scrapper
def _get_fanarts_list(system,search,imgsize):
    full_fanarts = []
    api_key = "3a9f018734ef0eaf1e44c5557e4a0d13"
    f = urllib.urlopen("http://htbackdrops.com/api/"+api_key+"/searchXML?keywords="+search+"&default_operator=and")
    page = f.read().replace('\n', '')
    fanarts = re.findall('<id>(.*?)</id>', page)
    for index, fanart in enumerate(fanarts):
		thumbnail = os.path.join(CACHE_PATH,str(index) + str(time.time()) + '.jpg')
		h = urllib.urlretrieve("http://htbackdrops.com/api/"+api_key+"/download/"+fanarts[index]+"/thumbnail",thumbnail)
		full_fanarts.append(("http://htbackdrops.com/api/"+api_key+"/download/"+fanarts[index]+"/fullsize",thumbnail,"Fanart "+str(index+1)))
    return full_fanarts

# Get Fanart scrapper
def _get_fanart(image_url):
    return image_url

