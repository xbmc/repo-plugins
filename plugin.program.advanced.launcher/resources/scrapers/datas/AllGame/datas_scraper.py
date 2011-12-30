# -*- coding: UTF-8 -*-

import re
import os
import urllib

# Return Game search list
def _get_games_list(search):
    params = urllib.urlencode({'sql': search, 'opt1': 81})
    results = []
    display = []
    try:
        f = urllib.urlopen('http://www.allgame.com/search.php', params)
        for line in f.readlines():
            if '"game.php?id=' in line:
                game = {}
                game["id"] = ''.join(re.findall('<a[^>]*id=(.*?)">', line))
                game["title"] = unescape(''.join(re.findall('<a[^>]*>(.*?)</a>', line)))
            if '"platform.php?id=' in line:
                game["gamesys"] = ''.join(re.findall('<a[^>]*>(.*?)</a>', line))
                results.append(game)
                display.append(game["title"]+" / "+game["gamesys"])
        print results,display
        return results,display
    except:
        return results,display

# Return 1st Game search
def _get_first_game(search,gamesys):
    params = urllib.urlencode({'sql': search, 'opt1': 81})
    results = []
    try:
        f = urllib.urlopen('http://www.allgame.com/search.php', params)
        for line in f.readlines():
            if '"game.php?id=' in line:
                game = {}
                game["id"] = ''.join(re.findall('<a[^>]*id=(.*?)">', line))
                game["title"] = unescape(''.join(re.findall('<a[^>]*>(.*?)</a>', line)))
            if '"platform.php?id=' in line:
                game["gamesys"] = ''.join(re.findall('<a[^>]*>(.*?)</a>', line))
                if ( game["gamesys"].lower() == gamesys.lower() ):
                    results.append(game)
        return results
    except:
        return results

# Return Game data
def _get_game_data(game_id):
    gamedata = {}
    gamedata["genre"] = ""
    gamedata["release"] = ""
    gamedata["studio"] = ""
    gamedata["plot"] = ""
    try:
        f = urllib.urlopen('http://www.allgame.com/game.php?id='+game_id)
        page = f.read().replace('\r\n', '')
        game_genre = ''.join(re.findall('<a href="genre.php[^>]*>(.*?)</a>', page))
        if game_genre:
            gamedata["genre"] = game_genre
        release_date = re.findall('<h3>Release Date</h3>[^>]*>(.*?)</p>', page)
        if release_date:
            gamedata["release"] = release_date[0][-4:]
        game_studio = re.findall('<h3>Developer</h3>[^>]*>(.*?)</p>', page)
        if game_studio:
            p = re.compile(r'<.*?>')
            gamestudio = p.sub('', game_studio[0])
	    if gamestudio:
                gamedata["studio"] = gamestudio.rstrip()
        plot = re.findall('<h2[^>]*>(.*?)</p>(.*?)<p>(.*?)</p>', page)
        if plot:
            p = re.compile(r'<.*?>')
            gamedata["plot"] = unescape(p.sub('', plot[0][2]))
        return gamedata
    except:
        return gamedata  

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

