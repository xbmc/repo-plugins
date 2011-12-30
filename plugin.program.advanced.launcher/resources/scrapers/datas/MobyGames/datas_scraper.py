# -*- coding: UTF-8 -*-

import re
import os
import urllib
from xbmcaddon import Addon

# Return Game search list
def _get_games_list(search):
    results = []
    display = []
    try:
        f = urllib.urlopen('http://www.mobygames.com/search/quick?q='+search.replace(' ','+')+'&sFilter=1&sG=on')
        for line in f.readlines():
            if 'searchNumber' in line:
                split_games = re.findall('Game: (.*?)</span></div>', line)
        for games in split_games:
            game_title = re.findall('<a href="(.*?)">(.*?)</a>', games)
            split_versions = re.findall('nowrap"><a href="(.*?)">(.*?)</a> ', games)
            if split_versions:
                for version in split_versions:
                    game = {}
                    game["title"] = unescape(game_title[0][1])
                    game["id"] = 'http://www.mobygames.com'+version[0]
                    game["gamesys"] = version[1]
                    results.append(game)
                    display.append(game["title"]+" / "+game["gamesys"])
            else:
                game = {}
                game["title"] = unescape(game_title[0][1].replace('&#x26;','&').replace('&#x27;',"'"))
                one_version = re.findall('nowrap">(.*?) \(', games)
                game["id"] = 'http://www.mobygames.com'+game_title[0][0]
                game["gamesys"] = one_version[0]
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
        f = urllib.urlopen('http://www.mobygames.com/search/quick?q='+search.replace(' ','+')+'&p='+platform+'&sFilter=1&sG=on')
        for line in f.readlines():
            if 'searchNumber' in line:
                split_games = re.findall('Game: (.*?)</span></div>', line)
        for games in split_games:
            game_title = re.findall('<a href="(.*?)">(.*?)</a>', games)
            split_versions = re.findall('nowrap"><a href="(.*?)">(.*?)</a> ', games)
            if split_versions:
                for version in split_versions:
                    game = {}
                    game["title"] = unescape(game_title[0][1])
                    game["id"] = 'http://www.mobygames.com'+version[0]
                    game["gamesys"] = gamesys
                    results.append(game)
            else:
                game = {}
                game["title"] = unescape(game_title[0][1])
                one_version = re.findall('nowrap">(.*?) \(', games)
                game["id"] = 'http://www.mobygames.com'+game_title[0][0]
                game["gamesys"] = gamesys
                results.append(game)
        return results
    except:
        return results

# Return Game data
def _get_game_data(game_url):
    gamedata = {}
    gamedata["genre"] = ""
    gamedata["release"] = ""
    gamedata["studio"] = ""
    gamedata["plot"] = ""
    try:
        f = urllib.urlopen(game_url)
        page = f.read().replace('\r\n', '').replace('\n', '')
        game_genre = re.findall('<a href="/genre/(.*?)">(.*?)</a>', page)
        if game_genre:
            gamedata["genre"] = unescape(game_genre[0][1])
        game_release = re.findall('/release-info">(.*?)</a>', page)
        if game_release:
            gamedata["release"] = game_release[1][-4:]
        game_studio = re.findall('Developed by(.*?)<a href="(.*?)">(.*?)</a>', page)
        if game_studio:
            gamedata["studio"] = unescape(game_studio[0][2])
        game_plot = re.findall('Description</h2>(.*?)<div class', page)
        if game_plot:
            p = re.compile(r'<.*?>')
            gamedata["plot"] = unescape(p.sub('', game_plot[0]))
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
                if result[3]:
                    platform = result[3]
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

