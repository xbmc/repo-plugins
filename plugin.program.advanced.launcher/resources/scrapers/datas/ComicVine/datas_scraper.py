# -*- coding: UTF-8 -*-

import re
import os
import urllib
import simplejson

# Return Comics search list
def _get_games_list(search):
    comicvine_key = "a1aaa516eaf233abf29c8aefaa46dc39cc0f0873"
    results = []
    display = []
    search = urllib.quote(search.lower().replace('vol.',''))
    try:
        url = urllib.urlopen('http://www.comicvine.com/search/autocomplete/?json=%7B%22models%22%3A%5B%22comics.issue%22%2C%22comics.volume%22%5D%2C%22q%22%3A%22'+search+'%22%2C%22search_matches%22%3A8%2C%22alias_matches%22%3A2%7D')
        json = simplejson.loads(url.read())
        comics_results = json['results']
        for i in comics_results:
            comic = {}
            comic["id"] = str(i["id"].encode('utf-8','ignore'))
            f = urllib.urlopen('http://api.comicvine.com/issue/'+comic["id"]+'/?api_key='+comicvine_key+'&format=xml&field_list=publish_year,description,volume,name')
            page = f.read().replace('\r\n', '').replace('\n', '')
            print page
            issue_name = ''.join(re.findall('</description><name><!\[CDATA\[(.*?)\]\]></name><publish_year>', page))
            release = ''.join(re.findall('<publish_year>(.*?)</publish_year>', page))
            comic["title"] = str(i["name"]+': '+issue_name+' ('+release+')')
            comic["gamesys"] = 'Comic'
            results.append(comic)
            display.append(comic["title"].encode('utf-8','ignore'))
        return results,display
    except:
        return results,display

        
# Return 1st Comic search
def _get_first_game(search,gamesys):
    results = []
    search = urllib.quote(search.lower().replace('vol.',''))
    try:
        url = urllib.urlopen('http://www.comicvine.com/search/autocomplete/?json=%7B%22models%22%3A%5B%22comics.issue%22%2C%22comics.volume%22%5D%2C%22q%22%3A%22'+search+'%22%2C%22search_matches%22%3A8%2C%22alias_matches%22%3A2%7D')
        json = simplejson.loads(url.read())
        comics_results = json['results']
        comic = {}
        comic["id"] = str(comics_results[0]["id"].encode('utf-8','ignore'))
        comic["title"] = str(comics_results[0]["name"].encode('utf-8','ignore')+' ('+comics_results[0]["publisher"].encode('utf-8','ignore')+')')
        comic["gamesys"] = 'Comic'
        results.append(comic)
        return results
    except:
        return results
        
# Return Comic data
def _get_game_data(game_id):
    comicvine_key = "a1aaa516eaf233abf29c8aefaa46dc39cc0f0873"
    gamedata = {}
    gamedata["genre"] = ""
    gamedata["release"] = ""
    gamedata["studio"] = ""
    gamedata["plot"] = ""
    try:
        f = urllib.urlopen('http://api.comicvine.com/issue/'+game_id+'/?api_key='+comicvine_key+'&format=xml&field_list=publish_year,description,volume,name')
        page = f.read().replace('\r\n', '').replace('\n', '')
        print page
        release_date = ''.join(re.findall('<publish_year>(.*?)</publish_year>', page))
        gamedata["release"] = release_date.encode('utf-8','ignore')
        plot = ''.join(re.findall('<description><!\[CDATA\[(.*?)\]\]></description>', page))
        title = re.findall('<name><!\[CDATA\[(.*?)\]\]></name>', page)
        p = re.compile(r'<.*?>')
        gamedata["plot"] = unescape(p.sub('', title[0].encode('utf-8','ignore')+" : "+plot.encode('utf-8','ignore')))
        volume = ''.join(re.findall('<api_detail_url><!\[CDATA\[(.*?)\]\]></api_detail_url>', page))
        if volume:
            f = urllib.urlopen(volume+'?api_key='+comicvine_key+'&format=xml&field_list=publisher')
            page = f.read().replace('\r\n', '').replace('\n', '')
            studio = ''.join(re.findall('<name><!\[CDATA\[(.*?)\]\]></name>', page))
            gamedata["studio"] = studio.encode('utf-8','ignore')
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
