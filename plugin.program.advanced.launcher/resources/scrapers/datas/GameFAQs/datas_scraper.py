# -*- coding: UTF-8 -*-

import re
import os
import urllib
from xbmcaddon import Addon

# Return Game search list
def _get_games_list(search):
    display=[]
    results=[]
    try:
        f = urllib.urlopen('http://www.gamefaqs.com/search/index.html?platform=0&game='+search.replace(' ','+')+'')
        gets = {}
        gets = re.findall('                                <a href="(.*?)"                                >(.*?)</a></td>', f.read().replace('\r\n', ''))
        for get in gets:
            game = {}
            gamesystem = get[0].split('/')
            game["id"] = 'http://www.gamefaqs.com'+get[0]
            game["title"] = unescape(get[1])
            game["gamesys"] = gamesystem[1].capitalize()
            results.append(game)
            display.append(game["title"]+" / "+game["gamesys"])
        return results,display
    except:
        return results,display

# Return 1st Game search
def _get_first_game(search,gamesys):
    platform = _system_conversion(gamesys)
    results = []
    try:
        f = urllib.urlopen('http://www.gamefaqs.com/search/index.html?platform='+platform+'&game='+search.replace(' ','+')+'')
        gets = {}
        gets = re.findall('                                <a href="(.*?)"                                >(.*?)</a></td>', f.read().replace('\r\n', ''))
        for get in gets:
            game = {}
            game["id"] = 'http://www.gamefaqs.com'+get[0]
            game["title"] = unescape(get[1])
            game["gamesys"] = gamesys
            results.append(game)
        return results
    except:
        return results

# Return Game data
def _get_game_data(game_url):
    print game_url
    gamedata = {}
    gamedata["genre"] = ""
    gamedata["release"] = ""
    gamedata["studio"] = ""
    gamedata["plot"] = ""
    try:
        f = urllib.urlopen(game_url)
        page = f.read().replace('\r\n', '')
        game_genre = re.findall('</a> &raquo; <a href="(.*?)">(.*?)</a> &raquo; <a href="/', page)
        if game_genre:
            gamedata["genre"] = game_genre[0][1]
        game_release = re.findall('Release: <a href="(.*?)">(.*?) &raquo;</a>', page)
        if game_release:
            gamedata["release"] = game_release[0][1][-4:]
        game_studio = re.findall('<ul><li><a href="/features/company/(.*?)">(.*?)</a></li>', page)
        if game_studio:
            p = re.compile(r'<.*?>')
            gamedata["studio"] = p.sub('', game_studio[0][1])
        game_plot = re.findall('Description</h2></div><div class="body"><div class="details">(.*?)</div></div>', page)
        if game_plot:
            gamedata["plot"] = unescape(game_plot[0])
        return gamedata
    except:
        return gamedata  

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
                if result[2]:
                    platform = result[2]
                    return platform
    except:
        return ''
        
def unescape(s):
    s = s.replace('<br />',' ')
    s = s.replace("&lt;", "<")
    s = s.replace("&gt;", ">")
    s = s.replace("&amp;", "&")
    s = s.replace("&#039;","'")
    s = s.replace('<br />',' ')
    s = s.replace(",","‚")
    s = s.replace('&quot;','"')
    s = s.replace('&nbsp;',' ')
    s = s.replace('&#x26;','&')
    s = s.replace('&#x27;',"'")
    s = s.replace('&#xB0;',"°")
    return s

