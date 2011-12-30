# -*- coding: UTF-8 -*-

import os
import re
import urllib
from xbmcaddon import Addon

# Get Game page
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

# Thumbnails list scrapper
def _get_thumbnails_list(system,search,region,imgsize):
    covers = []
    results = []
    game_id_url = _get_game_page_url(system,search)
    try:
        f = urllib.urlopen(game_id_url+'cover-art')
        page = f.read().replace('\r\n', '').replace('\n', '')
        countries = re.findall('Countr(.*?)</td><td>&nbsp;:&nbsp;</td><td><span style="white-space: nowrap">(.*?) <img alt="(.*?)href="(.*?)"><img alt="(.*?)" border="0" src="(.*?)"', page)
        found = 0
        for index, country in enumerate(countries):
            if region == 'US':
                if (country[1] == 'Canada') | (country[1] == 'United States'):
                    found = found+1
                    covers.append([country[5].replace('/small/','/large/'),country[5],'Cover '+str(found)])
            if region == 'JP':
                if (country[1] == 'Japan'):
                    found = found+1
                    covers.append([country[5].replace('/small/','/large/'),country[5],'Cover '+str(found)])
            if region == 'EU':
                if (country[1] == 'Finland') | (country[1] == 'France') | (country[1] == 'Germany') | (country[1] == 'Italy') | (country[1] == 'The Netherlands') | (country[1] == 'Spain') | (country[1] == 'Sweden') | (country[1] == 'United Kingdom'):
                    found = found+1
                    covers.append([country[5].replace('/small/','/large/'),country[5],'Cover '+str(found)])
            if region == 'All':
                found = found+1
                covers.append([country[5].replace('/small/','/large/'),country[5],'Cover '+str(found)])
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
                if result[3]:
                    platform = result[3]
                    return platform
    except:
        return ''

