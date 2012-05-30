import xbmcplugin
import xbmcgui
import xbmcaddon
import sys
import urllib, urllib2
import re
import showEpisode

addon = xbmcaddon.Addon(id='plugin.video.cinemassacre')

thisPlugin = int(sys.argv[1])

baseLink = "http://cinemassacre.com/"

hideMenuItem = []
hideMenuItem.append("412") # Gallery
hideMenuItem.append("486") # Fan Stuff
hideMenuItem.append("402") # Full list of AVGN Videos
hideMenuItem.append("225") # Game Collection

_regex_extractMenu = re.compile("<ul id=\"navlist\">(.*?)<ul id=\"navpages\">", re.DOTALL);

_regex_extractMenuItem = re.compile("<li class=\"cat-item cat-item-([0-9]{1,4})\"><a href=\"(http://cinemassacre.com/category/[a-z0-9\-]*/)\" title=\"(.*?)\">(.*?)</a>", re.DOTALL);
_regex_extractMenuItemSub = re.compile("<li class=\"cat-item cat-item-([0-9]{1,4})\"><a href=\"(http://cinemassacre.com/category/[a-z0-9\-]*/[a-z0-9\-]*/)\" title=\"(.*?)\">(.*?)</a>", re.DOTALL);
_regex_extractMenuItemSubSub = re.compile("<li class=\"cat-item cat-item-([0-9]{1,4})\"><a href=\"(http://cinemassacre.com/category/[a-z0-9\-]*/[a-z0-9\-]*/[a-z0-9\-]*/)\" title=\"(.*?)\">(.*?)</a>", re.DOTALL);

_regex_extractShow = re.compile("<!-- content -->(.*?)<!-- /content -->", re.DOTALL)
_regex_extractRecent = re.compile("<!-- videos -->(.*?)<!-- /videos -->", re.DOTALL);

_regex_extractEpisode = re.compile("<!-- video -->(.*?)<!-- /video -->", re.DOTALL)
_regex_extractEpisodeLink = re.compile("<h3><a href=\"(.*?)\">(.*?)</a></h3>", re.DOTALL)
_regex_extractEpisodeImg = re.compile("<img src=\"(.*?)\" alt=\"(.*?)\" />", re.DOTALL)
_regex_extractEpisodeImg2 = re.compile("<img width=\"[0-9]*\" height=\"[0-9]*\" src=\"(.*?)\" class=\".*?\" alt=\"(.*?)\" title=\".*?\" />", re.DOTALL)

def mainPage():
    global thisPlugin

    addDirectoryItem(addon.getLocalizedString(30000), {"action" : "recent", "link": ""})  
    subMenu(level1=0, level2=0)

def subMenu(level1=0, level2=0):
    global thisPlugin
    page = load_page(baseLink)
    mainMenu = extractMenu(page)
    
    if level1 == 0:
        menu = mainMenu
    elif level2 == 0:
        menu = mainMenu[int(level1)]['children']
    else:
        menu = mainMenu[int(level1)]['children'][int(level2)]['children']
    
    counter = 0
    for menuItem in menu:
        menu_name = remove_html_special_chars(menuItem['name']);
        
        menu_link = menuItem['link'];
        if len(menuItem['children']) and level1 == 0:
            addDirectoryItem(menu_name, {"action" : "submenu", "link": counter})  
        elif len(menuItem['children']):
            addDirectoryItem(menu_name, {"action" : "subsubmenu", "link": level1 + ";" + str(counter)})  
        else:        
            addDirectoryItem(menu_name, {"action" : "show", "link": menu_link})
        counter = counter + 1
    xbmcplugin.endOfDirectory(thisPlugin)

def recentPage():
    global thisPlugin
    page = load_page(baseLink)
    show = _regex_extractRecent.search(page)    
    extractEpisodes(show)
    
def extractMenu(page):
    menu = _regex_extractMenu.search(page).group(1);
    menuList = []
    
    parent = -1;
    parentHidden = True
    parent2Hidden = True
    for line in menu.split("\n"):
        menuItem = _regex_extractMenuItem.search(line)
        if menuItem is not None:
            if not menuItem.group(1) in hideMenuItem:
                parentHidden = False
                parent = parent + 1
                parent2 = -1
                menuList.append({"name" : menuItem.group(4), "link" : menuItem.group(2), "children" : []})
            else:
                parentHidden = True
        elif not parentHidden:
            menuItemSub = _regex_extractMenuItemSub.search(line)
            if menuItemSub is not None:
                if not menuItemSub.group(1) in hideMenuItem:
                    parent2Hidden = False
                    parent2 = parent2 + 1
                    menuList[parent]['children'].append({"name" : menuItemSub.group(4), "link" : menuItemSub.group(2), "children" : []});
                else:
                    parent2Hidden = True
            elif not parent2Hidden:
                menuItemSubSub = _regex_extractMenuItemSubSub.search(line)
                if menuItemSubSub is not None:
                    if not menuItemSubSub.group(1) in hideMenuItem:
                        menuList[parent]['children'][parent2]['children'].append({"name" : menuItemSubSub.group(4), "link" : menuItemSubSub.group(2), "children" : []});
    return menuList
    
def showPage(link):
    global thisPlugin
    page = load_page(urllib.unquote(link))
    show = _regex_extractShow.search(page)
    extractEpisodes(show)

def extractEpisodes(show):
    episodes = list(_regex_extractEpisode.finditer(show.group(1)))
    for episode in episodes:
        episode_html = episode.group(1)
        episod_title = _regex_extractEpisodeLink.search(episode_html).group(2)
        episod_title = remove_html_special_chars(episod_title)
        episode_link = _regex_extractEpisodeLink.search(episode_html).group(1)
        episode_img = _regex_extractEpisodeImg.search(episode_html)
        if episode_img is None:
            episode_img = _regex_extractEpisodeImg2.search(episode_html)
        episode_img = episode_img.group(1)
        addDirectoryItem(episod_title, {"action" : "episode", "link": episode_link}, episode_img, False)
    xbmcplugin.endOfDirectory(thisPlugin)


def playEpisode(link):
    link = urllib.unquote(link)
    page = load_page(link)
    showEpisode.showEpisode(page)

def load_page(url):
    print url
    req = urllib2.Request(url)
    response = urllib2.urlopen(req)
    link = response.read()
    response.close()
    return link

def addDirectoryItem(name, parameters={}, pic="", folder=True):
    li = xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=pic)
    if not folder:
        li.setProperty('IsPlayable', 'true')
    url = sys.argv[0] + '?' + urllib.urlencode(parameters)
    return xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=url, listitem=li, isFolder=folder)

def remove_html_special_chars(inputStr):
    inputStr = inputStr.replace("&#8211;", "-")
    inputStr = inputStr.replace("&#8217;", "'")#\x92
    inputStr = inputStr.replace("&#039;", chr(39))# '
    inputStr = inputStr.replace("&#038;", chr(38))# &
    return inputStr
    
def get_params():
    param = []
    paramstring = sys.argv[2]
    if len(paramstring) >= 2:
        params = sys.argv[2]
        cleanedparams = params.replace('?', '')
        if (params[len(params) - 1] == '/'):
            params = params[0:len(params) - 2]
        pairsofparams = cleanedparams.split('&')
        param = {}
        for i in range(len(pairsofparams)):
            splitparams = {}
            splitparams = pairsofparams[i].split('=')
            if (len(splitparams)) == 2:
                param[splitparams[0]] = splitparams[1]
    
    return param
    
if not sys.argv[2]:
    mainPage()
else:
    params = get_params()
    if params['action'] == "show":
        showPage(params['link'])
    elif params['action'] == "submenu":
        subMenu(params['link'])
    elif params['action'] == "subsubmenu":
        levels = urllib.unquote(params['link']).split(";")
        subMenu(levels[0], levels[1])
    elif params['action'] == "recent":
        recentPage()
    elif params['action'] == "episode":
        print "Episode"
        playEpisode(params['link'])
    else:
        mainPage()
