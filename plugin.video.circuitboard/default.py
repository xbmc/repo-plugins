import xbmcplugin
import xbmcgui
import xbmcaddon
import sys
import urllib, urllib2
import re
import pprint
import urlparse
import showEpisode

thisPlugin = int(sys.argv[1])
addon = xbmcaddon.Addon(id='plugin.video.circuitboard')

baseLink = "http://cbtv.circuit-board.de/"
newEpisodes = "http://cbtv.circuit-board.de/?feed=rss"

_regex_extractShows = re.compile("<li class=\"page_item page-item-.*?\"><a href=\"("+baseLink+"\?page_id=.*?)\"><img src=\"("+baseLink+"wp-content/uploads/icon[s]*/.*?)\" class=\"page_icon\" alt=\".*?\">(.*?)</a></li>");
_regex_extractEpisodes = re.compile("<li><span class=\"class1\"><a href=\"("+baseLink+"\?p=.*?)\">(.*?)</a></span></li>")
_regex_extractNew = re.compile("<item>[ \r\n\t]*<title>(.*?)</title>[ \r\n\t]*<link>("+baseLink+"\?p=[0-9]*)</link>.*?<description><!\[CDATA\[(.*?)\]\]></description>.*?</item>",re.DOTALL)

def mainPage():
    page = load_page(baseLink)
    
    addDirectoryItem(addon.getLocalizedString(30000), {"action" : "new", "link": newEpisodes})
    
    
    for show in _regex_extractShows.finditer(page):
        menu_link = show.group(1)
        pic = show.group(2)
        menu_name = remove_html_special_chars(show.group(3))
        addDirectoryItem(menu_name, {"action" : "show", "link": menu_link}, pic)
    xbmcplugin.endOfDirectory(thisPlugin)

def showPage(link):
    page = load_page(urllib.unquote(link))
    
    for episode in _regex_extractEpisodes.finditer(page):
        episode_link = episode.group(1)
        episode_title = remove_html_special_chars(episode.group(2))
        
        addDirectoryItem(episode_title, {"action" : "episode", "link": episode_link}, "", False)
    xbmcplugin.endOfDirectory(thisPlugin)
    

def showNew(link):
    page = load_page(urllib.unquote(link))
    
    for episode in _regex_extractNew.finditer(page):
        episode_link = episode.group(2)
        episode_title = remove_html_special_chars(episode.group(1))
        
        addDirectoryItem(episode_title, {"action" : "episode", "link": episode_link}, "", False)
    xbmcplugin.endOfDirectory(thisPlugin)
    
def playEpisode(link):
    episode_page = load_page(urllib.unquote(link))
    showEpisode.showEpisode(episode_page)

def load_page(url):
    print url
    req = urllib2.Request(url)
    response = urllib2.urlopen(req)
    link=response.read()
    response.close()
    return link

def addDirectoryItem(name, parameters={}, pic="", folder=True):
    li = xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=pic)
    if not folder:
        li.setProperty('IsPlayable', 'true')
    url = sys.argv[0] + '?' + urllib.urlencode(parameters)
    return xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=url, listitem=li, isFolder=folder)

def remove_html_special_chars(input):
    input = input.replace("&#8211;","-")
    input = input.replace("&#8217;","'")#\x92
    input = input.replace("&#8220;","\"")#\x92
    input = input.replace("&#8221;","\"")#\x92
    input = input.replace("&#039;",chr(39))# '
    input = input.replace("&#038;",chr(38))# &
    input = input.replace("&amp;",chr(38))# &
    
    return input
    
def get_params():
    param=[]
    paramstring=sys.argv[2]
    if len(paramstring)>=2:
        params=sys.argv[2]
        cleanedparams=params.replace('?','')
        if (params[len(params)-1]=='/'):
            params=params[0:len(params)-2]
        pairsofparams=cleanedparams.split('&')
        param={}
        for i in range(len(pairsofparams)):
            splitparams={}
            splitparams=pairsofparams[i].split('=')
            if (len(splitparams))==2:
                param[splitparams[0]]=splitparams[1]
                                
    return param
    
if not sys.argv[2]:
    mainPage()
else:
    params=get_params()
    if params['action'] == "show":
        showPage(params['link'])
    if params['action'] == "new":
        showNew(params['link'])
    elif params['action'] == "episode":
        playEpisode(params['link'])
    else:
        mainPage()
