# -*- coding: UTF-8 -*-

import os
import re
import urllib
import simplejson
from xbmcaddon import Addon

# Get Comics pages
def _get_game_page_url(system,search):
    search = urllib.quote(search.lower().replace('vol.',''))
    try:
        url = urllib.urlopen('http://www.comicvine.com/search/autocomplete/?json=%7B%22models%22%3A%5B%22comics.issue%22%2C%22comics.volume%22%5D%2C%22q%22%3A%22'+search+'%22%2C%22search_matches%22%3A8%2C%22alias_matches%22%3A2%7D')
        json = simplejson.loads(url.read())
        comics_results = json['results']
        return comics_results
    except:
        return comics_results
	
# Thumbnails list scrapper
def _get_thumbnails_list(system,search,region,imgsize):
    covers = []
    game_id_url = _get_game_page_url(system,search)
    try:
        for comic in game_id_url:
            cover_number = 1
            game_page = urllib.urlopen('http://www.comicvine.com'+str(comic["url"].encode('utf-8','ignore')))
            if game_page:
                for line in game_page.readlines():
                    if '[/img][/url]' in line:
                        result = ''.join(re.findall('\[img\](.*?)\[/img\]', line))
                        covers.append((result,result.replace('_large','_thumb'),comic["name"]+" ("+comic["publish_date"][-4:]+") Cover "+str(cover_number)))
                        cover_number = cover_number + 1
        return covers
    except:
        return covers

# Get Thumbnail scrapper
def _get_thumbnail(image_url):
    return image_url
