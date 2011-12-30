# -*- coding: UTF-8 -*-

import os
import re
import urllib
from xbmcaddon import Addon

# Get Game first page
def _get_game_page_url(system,search):
    platform = _system_conversion(system)
    params = urllib.urlencode({'q': search.replace(' ','+'), 'p': platform, 'sFilter': '1', 'sG': 'on'})
    games = []
    try:
        search_page = urllib.urlopen('http://www.mobygames.com/search/quick', params)
        for line in search_page.readlines():
            if 'searchNumber' in line:
               games.append(re.findall('Game: <a href="(.*?)"', line))
        if games:
            return 'http://www.mobygames.com'+games[0][0]+'/'
    except:
        return ""

# Fanarts list scrapper
def _get_fanarts_list(system,search,imgsize):
    full_fanarts = []
    results = []
    game_id_url = _get_game_page_url(system,search)
    try:
        game_page = urllib.urlopen(game_id_url+'screenshots')
        for line in game_page.readlines():
            if 'gameShotId' in line:
                results.append(re.findall('href="(.*?)"><img alt="(.*?)" border="0" src="(.*?)"', line))
        for index, line in enumerate(results):
    	    full_fanarts.append(['http://www.mobygames.com'+line[0][2].replace('/s/','/l/'),'http://www.mobygames.com'+line[0][2],'Image '+str(index+1)])
        return full_fanarts
    except:
        return full_fanarts

# Get Fanart scrapper
def _get_fanart(image_url):
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
                if result[3]:
                    platform = result[3]
                    return platform
    except:
        return ''

