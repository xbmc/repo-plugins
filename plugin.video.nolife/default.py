# -*- coding: utf-8 -*-
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
Nolife Online addon for XBMC
Authors:     gormux, DeusP
"""

import re, xbmcplugin, xbmcgui, xbmcaddon, urllib, urllib2, sys, cookielib, pickle
from BeautifulSoup import BeautifulSoup

# Global variable definition
## Header for every log in this plugin
pluginLogHeader = "[XBMC_NOLIFE] "

## Values for the mode parameter
MODE_LAST_SHOWS, MODE_CATEGORIES, MODE_SEARCH, MODE_SHOW_BY_URL, MODE_LINKS = range(5)

settings  = xbmcaddon.Addon(id='plugin.video.nolife')
url       = 'http://online.nolife-tv.com/index.php?'
name      = 'Nolife Online'
mode      = None
version   = settings.getAddonInfo('version')
useragent = "XBMC Nolife-plugin/" + version
language = settings.getLocalizedString

def remove_html_tags(data):
    """Permits to remove all HTML tags
        
    This function removes the differents HTML tags of a string
    """
    page = re.compile(r'<.*?>')
    return page.sub('', data)

def requestinput():
    """Request input from user
        
    Uses the XBMC's keyboard to get a string
    """
    kbd = xbmc.Keyboard('default', 'heading', True)
    kbd.setDefault('')
    kbd.setHeading('Recherche')
    kbd.setHiddenInput(False)
    kbd.doModal()
    if (kbd.isConfirmed()):
        name_confirmed  = kbd.getText()
        return name_confirmed
    else:
        return 'Null'

def parse_categories():
    """
    Gets categories from family types
    """
    settings           = xbmcaddon.Addon(id='plugin.video.nolife')
    fam                = 'garbage'
    emissions          = []
    try:
        _type = int(settings.getSetting( "type" ))
        if   _type == 1:
            myurl  = "http://mobile.nolife-tv.com/online/familles-type"
        elif _type == 0:
            myurl  = "http://mobile.nolife-tv.com/online/familles-theme"
    except:
        _type = str(settings.getSetting( "type" ))
        myurl = "http://mobile.nolife-tv.com/online/familles-" + _type
    req   = urllib2.Request(myurl)
    page  = urllib2.urlopen(req).read()
    soup  = BeautifulSoup(page)
    liste = soup.findAll('li')

    for elem in liste:
        if re.compile('list-divider').findall(str(elem)):
            fam = re.compile('>.*<').findall(str(elem))[0].strip('<>')
        else:
            if fam != 'garbage':
                reg_cat   = '<h1 style="padding-left:10px;">.*</h1>'
                catname   = re.compile(reg_cat).findall(
                                            str(elem))[0][31:][:-5]
                reg_sid   = '<a href=.*'
                sid       = re.compile(reg_sid).findall(
                                            str(elem))[0][9:][:-17][43:]
                reg_thumb = 'data-thumb=".*"'
                thumb     = re.compile(reg_thumb).findall(
                                            str(elem))[0][12:][:-1]
                if name != []:
                    emission = [fam, catname, sid, thumb]
                    emissions.append(emission)
    return emissions

def login():
    """Log into the Nolife website
        
    This method log the user into the website, checks credentials and return the current
    """
    
    settings = xbmcaddon.Addon(id='plugin.video.nolife')
    user     = settings.getSetting( "username" )
    pwd      = settings.getSetting( "password" )
    loginrequest = urllib.urlencode({'vb_login_username': user,
                                'vb_login_password': pwd,
                                's': '',
                                'securitytoken': 'guest',
                                'do': 'login',
                                'vb_login_md5password': '',
                                'vb_login_md5password_utf': ''})
    

    requestHandler.addheaders = [("User-agent", useragent)]
    page = requestHandler.open("http://forum.nolife-tv.com/login.php", loginrequest)
    res = BeautifulSoup(page.read())
    if re.compile('pas valide').findall(str(res)):
        xbmc.log(msg=pluginLogHeader + "Invalid username, aborting",level=xbmc.LOGERROR)
        err = xbmcgui.Dialog()
        err.ok("Erreur", "Nom d'utilisateur ou mot de passe invalide.","Veuillez vérifier les informations de connexion dans","les paramètres de l'addon.")
        doanerror
    elif re.compile('votre quota').findall(str(res)):
        xbmc.log(msg=pluginLogHeader + "User account locked",level=xbmc.LOGERROR)
        err = xbmcgui.Dialog()
        err.ok("Message", "Trop d'erreurs d'authentification.","Veuillez patienter 15 minutes avant de rééssayer","Vérifiez également vos informations de connexion.")
        doanerror
    else:
        xbmc.log(msg=pluginLogHeader + "Valid User",level=xbmc.LOGERROR)

def initialIndex():
    """Creates initial index
    
    Create the initial menu with the right identification values for the add-on to know which option have been selected
    """
    add_dir(unicode(language(33016)), 'http://mobile.nolife-tv.com', MODE_LAST_SHOWS, '')
    add_dir(unicode(language(33017)), 'http://mobile.nolife-tv.com', MODE_CATEGORIES, '')
    add_dir(unicode(language(33018)), 'http://mobile.nolife-tv.com', MODE_SEARCH, '')

def getlastVideos():
    """Get last uploaded videos
        
    Get the videos in the "last videos" menu option
    """
    postrequest = urllib.urlencode({'emissions': 0,
                                   'famille': 0,
                                   'a': 'ge'})
    
    page = requestHandler.open("http://mobile.nolife-tv.com/do.php", postrequest)
    liste = BeautifulSoup(page.read()).findAll('li')
    for element in liste:
        if re.compile('data-icon="arrow-r"').findall(str(element)):
            
            if  re.compile('icones/32/on').findall(str(element)):
                _seen = True
            else:
                _seen = False
            
            reg_date = '<p style="padding-right:25px;'\
                ' padding-left:10px;">.*</p>'
            _thumb    = re.compile('data-thumb=".*"').findall(
                                                              str(element))[0][12:][:-1]
            _date_len = remove_html_tags(
                                         re.compile(reg_date).findall(str(element))[0]
                                         )
            _duration = _date_len.split(' - ')[1]
            
            reg_vid = 'a href="emission-.*" '
            _vid   = re.compile(reg_vid).findall(str(element))[0][17:][:-2]
            
            reg_desc = '<p style="padding-left:10px;"><strong>.*'
            _desc  = remove_html_tags(
                                      re.compile(reg_desc).findall(str(element))[0][30:])
            
            _name  = remove_html_tags(
                                      re.compile('<h3.*').findall(str(element))[0])
            
            addlink( _name + " - " + _desc,
                    "plugin://plugin.video.nolife?id=" + _vid,
                    _thumb, 
                    _duration,
                    _seen )

    
def getcategories():
    """Gets all categories and adds directories
    
    Get the differents categories of the videos
    """
    emissions = parse_categories()
    cat = []
    for element in emissions:
        cat.append(element[0])
    categories = set(cat)
    for category in categories:
        add_dir(category, category, MODE_SHOW_BY_URL, '')

def search():
    """Searches a video on Nolife website
        
    This function allows to search for a show
    """
    searchstring        = requestinput()
    if searchstring == 'Null':
        mode = 1
    else:
        postrequest = urllib.urlencode({'search': searchstring,
                                       'submit': 'Rechercher'})

        page = requestHandler.open("http://mobile.nolife-tv.com/online/", postrequest)
        liste = BeautifulSoup(page.read()).findAll('li')

        for element in liste:
            if re.compile('data-icon="arrow-r"').findall(str(element)):
                if  re.compile('icones/32/on').findall(str(element)):
                    _seen = True
                else:
                    _seen = False
                reg_srch = 'a href="emission-.*" '
                _searchid = re.compile(reg_srch).findall(
                                                    str(element))[0][17:][:-2]
                reg_desc = '<p style="padding-left:10px;"><strong>.*'
                _thumb    = re.compile('data-thumb=".*"').findall(
                                                    str(element))[0][12:][:-1]
                _bdesc = re.compile(reg_desc).findall(str(element))[0][30:]
                _bname = re.compile('<h3.*').findall(str(element))[0]
                _desc = remove_html_tags(_bdesc)
                _name = remove_html_tags(_bname)
                reg_date = '<p style="padding-right:25px;'\
                           ' padding-left:10px;">.*</p>'
                _date_len = remove_html_tags(
                            re.compile(reg_date).findall(str(element))[0]
                            )
                _duration = _date_len.split(' - ')[1]
                addlink(_name + " - " + _desc, 
                        "plugin://plugin.video.nolife?id=" + _searchid, 
                        _thumb, 
                        _duration,
                        _seen )

def getshows(category):
    """
    Gets shows in a category
    """
    emissions = parse_categories()
    for emission in emissions:
        if emission[0] == category:
            add_dir(emission[1], emission[2], MODE_LINKS, emission[3])

def getlinks(show):
    """
    Get videos links from a show
    """
    settings   = xbmcaddon.Addon(id='plugin.video.nolife')
    show_n     = settings.getSetting( "show_n" )
    showall    = settings.getSetting( "showall" )
    showseen   = settings.getSetting( "showseen" )
    user       = settings.getSetting( "username" )
    pwd        = settings.getSetting( "password" )
    if showall == "true":
        show_n = 65536
    emissions  = []
    finished   = False
    if show == "3" and showall == "true":
        show_n = 100
    i          = 0

    while finished == False:
        postrequest = urllib.urlencode({'emissions': i,
                                        'famille': show,
                                        'a': 'ge' })
        headers = { "Content-type": "application/x-www-form-urlencoded",
                    "Accept": "text/plain" }
        page = requestHandler.open("http://mobile.nolife-tv.com/do.php", postrequest)
        liste = BeautifulSoup(page.read()).findAll('li')
        if liste == []:
            finished = True
        else:
            for element in liste:
                if int(float(show_n)) == len(emissions):
                    finished = True
                    break
                if ( re.compile('data-icon="arrow-r"').findall(str(element))
                     and int(float(show_n)) > len(emissions) ):
                    if re.compile('icones/32/on').findall(str(element)):
                        _seen = True
                    else:
                        _seen = False

                    reg_date = '<p style="padding-right:25px;'\
                               ' padding-left:10px;">.*</p>'
                    _date_len = remove_html_tags(
                                re.compile(reg_date).findall(str(element))[0]
                                )
                    _thumb    = re.compile('data-thumb=".*"').findall(
                                                    str(element))[0][12:][:-1]
                    _duration = _date_len.split(' - ')[1]

                    req_id = 'a href="emission-.*" '
                    _id = re.compile(req_id).findall(
                                                    str(element))[0][17:][:-2]

                    req_desc = '<p style="padding-left:10px;"><strong>.*'
                    _desc = remove_html_tags(
                            re.compile(req_desc).findall(str(element))[0][30:]
                            )

                    _name     = remove_html_tags(
                                re.compile('<h3.*').findall(str(element))[0]
                                )

                    emissions.append([_id, 
                                      _name, 
                                      _desc, 
                                      _duration, 
                                      _seen, 
                                      _thumb])
            i = i + 1   

    for emission in emissions:
        if ( showseen == "false" and emission[4] == False ):
            if emission[2] == '':
                addlink(emission[1], 
                        "plugin://plugin.video.nolife?id=" + emission[0], 
                        emission[5], 
                        emission[3],
                        emission[4] )

            else:
                addlink(emission[1] + ' - ' + emission[2], 
                        "plugin://plugin.video.nolife?id=" + emission[0], 
                        emission[5], 
                        emission[3],
                        emission[4] )
        elif showseen == "false":
            continue
        else:
            if emission[2] == '':
                addlink(emission[1], 
                        "plugin://plugin.video.nolife?id=" + emission[0], 
                        emission[5], 
                        emission[3],
                        emission[4] )

            else:
                addlink(emission[1] + ' - ' + emission[2], 
                        "plugin://plugin.video.nolife?id=" + emission[0], 
                        emission[5], 
                        emission[3],
                        emission[4] )


def playvideo(requestHandler, video):
    """
    Plays video
    """
    settings = xbmcaddon.Addon(id='plugin.video.nolife')
    user     = settings.getSetting( "username" )
    pwd      = settings.getSetting( "password" )
    quality  = settings.getSetting( "quality" )
    if   quality == "HQ" or quality == "1":
        _video = video + "?quality=2"
    elif quality == "LQ" or quality == "0":
        _video = video + "?quality=1"
    elif quality == "TV" or quality == "2":
        _video = video + "?quality=3"
    elif quality == "720p" or quality == "3":
        _video = video + "?quality=4"
    elif quality == "1080p" or quality == "4":
        _video = video + "?quality=5"
    else:
        _video = video

    page = requestHandler.open(_video)
    url  = page.geturl()
    xbmc.log(msg=pluginLogHeader + "URL :" + url,level=xbmc.LOGDEBUG)
    listitem   = xbmcgui.ListItem( label='', 
                                   iconImage='', 
                                   thumbnailImage='', 
                                   path=url )

    xbmcplugin.setResolvedUrl(0, True, listitem)

def get_params():
    """
    Get parameters
    """
    param       = []
    paramstring = sys.argv[2]

    if len(paramstring) >= 2:
        params        = sys.argv[2]
        cleanedparams = params.replace('?','')

        if (params[len(params)-1] == '/'):
            params = params[0:len(params)-2]

        pairsofparams = cleanedparams.split('&')
        param = {}

        for i in range(len(pairsofparams)):
            splitparams = {}
            splitparams = pairsofparams[i].split('=')
            if (len(splitparams)) == 2:
                param[splitparams[0]] = splitparams[1]
    return param

def addlink(name, url, iconimage, duration, bool_seen):
    """
    Add a link to a directory, for playable elements
    """
    ok  = True
    liz = xbmcgui.ListItem(name, 
                           iconImage="DefaultFolder.png", 
                           thumbnailImage=iconimage)
    liz.setInfo( 
                 type="Video", 
                 infoLabels={ "title": name, 
                              "duration" : duration,
                              "playcount": int(bool_seen) } 
               )
    liz.setProperty("IsPlayable","true")
    ok  = xbmcplugin.addDirectoryItem( handle=int(sys.argv[1]), 
                                       url=url, 
                                       listitem=liz, 
                                       isFolder=False )
    return ok


def add_dir(name, url, mode, iconimage):
    """
    Adds a directory to the list
    """
    ok  = True
    
    # Hack to avoid incompatiblity of urllib with unicode string
    if isinstance(name, str):
        xbmc.log(msg="[XXX] str dir",level=xbmc.LOGERROR)
        url = sys.argv[0]+"?url="+urllib.quote_plus(url)+\
            "&mode="+str(mode)+"&name="+urllib.quote_plus(name)
    else:
        url = sys.argv[0]+"?url="+urllib.quote_plus(url)+\
        "&mode="+str(mode)+"&name="+urllib.quote_plus(name.encode("ascii", "ignore"))
    liz = xbmcgui.ListItem(name,
                           iconImage="DefaultFolder.png",
                           thumbnailImage=iconimage)
    liz.setInfo( 
                 type="Video", 
                 infoLabels={ "Title": name } 
               )
    ok  = xbmcplugin.addDirectoryItem( handle=int(sys.argv[1]), 
                                       url=url, 
                                       listitem=liz, 
                                       isFolder=True )
    return ok

## Start of the add-on
xbmc.log(msg=pluginLogHeader + "-----------------------",level=xbmc.LOGDEBUG)
xbmc.log(msg=pluginLogHeader + "Nolife plugin main loop",level=xbmc.LOGDEBUG)
pluginHandle = int(sys.argv[1])

## Reading parameters given to the add-on
params = get_params()
xbmc.log(msg=pluginLogHeader + "Parameters read",level=xbmc.LOGDEBUG)


try:
    url = urllib.unquote_plus(params["url"])
except:
    pass
try:
    mode = int(params["mode"])
except:
    pass
try:
    _id = int(params["id"])
except:
    _id = 0

xbmc.log(msg=pluginLogHeader + "requested mode : " + str(mode),level=xbmc.LOGDEBUG)
xbmc.log(msg=pluginLogHeader + "requested url : " + url,level=xbmc.LOGDEBUG)
xbmc.log(msg=pluginLogHeader + "requested id : " + str(_id),level=xbmc.LOGDEBUG)

# Starting request handler
# FIXME : Find a way to keep the cookies in the add-on session to avoid relogin all the time
xbmc.log(msg=pluginLogHeader + "No cookies, adding a jar",level=xbmc.LOGDEBUG)
cj = cookielib.CookieJar()
requestHandler = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
login()

# Determining and executing action
if( mode == None or url == None or len(url) < 1 ) and _id == 0:
    xbmc.log(msg=pluginLogHeader + "Loading initial index",level=xbmc.LOGDEBUG)
    initialIndex()
elif mode == MODE_LAST_SHOWS and _id == 0:
    xbmc.log(msg=pluginLogHeader + "Retrieving last plushied videos",level=xbmc.LOGDEBUG)
    getlastVideos()
elif mode == MODE_CATEGORIES and _id == 0:
    xbmc.log(msg=pluginLogHeader + "Retrieving shows categories",level=xbmc.LOGDEBUG)
    getcategories()
elif mode == MODE_SEARCH and _id == 0:
    xbmc.log(msg=pluginLogHeader + "Starting a search",level=xbmc.LOGDEBUG)
    search()
elif mode == MODE_SHOW_BY_URL and _id == 0:
    xbmc.log(msg=pluginLogHeader + "Retrieving shows for the url : " + url,level=xbmc.LOGDEBUG)
    getshows(url)
elif mode == MODE_LINKS and _id == 0:
    xbmc.log(msg=pluginLogHeader + "Getting links",level=xbmc.LOGDEBUG)
    getlinks(url)
elif _id > 0:
    xbmc.log(msg=pluginLogHeader + "Trying to play video id : " + str(_id),level=xbmc.LOGDEBUG)
    playvideo(requestHandler, "http://mobile.nolife-tv.com/online/player-" + str(_id));

xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_NONE)
xbmcplugin.endOfDirectory(int(sys.argv[1]), cacheToDisc=True)
