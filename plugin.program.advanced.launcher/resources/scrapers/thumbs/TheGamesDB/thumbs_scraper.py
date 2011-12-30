# -*- coding: UTF-8 -*-

import os
import re
import urllib
from xbmcaddon import Addon

# Get Game page
def _get_game_page_url(system,search):
    platform = _system_conversion(system)
    params = urllib.urlencode({"name": search, "platform": platform})
    results = []
    try:
        f = urllib.urlopen("http://thegamesdb.net/api/GetGamesList.php", params)
        page = f.read().replace("\n", "")
        if (platform == "Sega Genesis" ) :
           params = urllib.urlencode({"name": search, "platform": "Sega Mega Drive"})
           f2 = urllib.urlopen("http://thegamesdb.net/api/GetGamesList.php", params)
           page = page + f2.read().replace("\n", "")
        games = re.findall("<Game><id>(.*?)</id><GameTitle>(.*?)</GameTitle>(.*?)<Platform>(.*?)</Platform></Game>", page)
        for item in games:
            game = {}
            game["id"] = item[0]
            game["title"] = item[1]
            game["order"] = 1
            if ( game["title"].lower() == search.lower() ):
                game["order"] += 1
            if ( game["title"].lower().find(search.lower()) != -1 ):
                game["order"] += 1
            results.append(game)
        results.sort(key=lambda result: result["order"], reverse=True)
        if results:
           return 'http://thegamesdb.net/api/GetGame.php?id='+results[0]["id"]
    except:
        return ""

# Thumbnails list scrapper
def _get_thumbnails_list(system,search,region,imgsize):
    covers = []
    game_id_url = _get_game_page_url(system,search)
    try:
        f = urllib.urlopen(game_id_url)
        page = f.read().replace('\n', '')
        boxarts = re.findall('<boxart side="front" (.*?)">(.*?)</boxart>', page)
        for indexa, boxart in enumerate(boxarts):
            covers.append(("http://thegamesdb.net/banners/"+boxarts[indexa][1],"http://thegamesdb.net/banners/_cache/"+boxarts[indexa][1],"Cover "+str(indexa+1)))
        banners = re.findall('<banner (.*?)">(.*?)</banner>', page)
        for indexb, banner in enumerate(banners):
            covers.append(("http://thegamesdb.net/banners/"+banners[indexb][1],"http://thegamesdb.net/banners/_cache/"+banners[indexb][1],"Banner "+str(indexb+1)))
        return covers
    except:
        return covers
        
# Get Thumbnail scrapper
def _get_thumbnail(image_url):
    return image_url

# Game systems DB identification
def _system_conversion(system_id):
    try:
        rootDir = Addon( id="plugin.program.advanced.launcher" ).getAddonInfo('path')
        if rootDir[-1] == ';':rootDir = rootDir[0:-1]
        resDir = os.path.join(rootDir, 'resources')
        scrapDir = os.path.join(resDir, 'scrapers')
        csvfile = open( os.path.join(scrapDir, 'gamesys'), "rb")
        conversion = []
        for line in csvfile.readlines():
            result = line.replace('\n', '').replace('"', '').split(',')
            if result[0].lower() == system_id.lower():
                if result[4]:
                    platform = result[4]
                    return platform
    except:
        return ''

