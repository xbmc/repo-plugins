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

import os, re, xbmcplugin, xbmcgui, xbmcaddon, urllib, urllib2, sys, cookielib, pickle, datetime
from BeautifulSoup import BeautifulSoup


"""
Class used as a C-struct to store video informations
"""
class videoInfo:
    pass

"""
Class used to report login error
"""
class loginExpcetion(Exception):
    pass

# Global variable definition
## Header for every log in this plugin
pluginLogHeader = "[XBMC_NOLIFE] "

## Values for the mode parameter
MODE_LAST_SHOWS, MODE_CATEGORIES, MODE_SEARCH, MODE_SHOW_BY_URL, MODE_LINKS = range(5)

## Values for the subscription mode
FREE, STANDARD, SUPPORT = range(3)

settings  = xbmcaddon.Addon(id='plugin.video.nolife')
url       = 'http://online.nolife-tv.com/index.php?'
name      = 'Nolife Online'
mode      = None
version   = settings.getAddonInfo('version')
useragent = "XBMC Nolife-plugin/" + version
language = settings.getLocalizedString
subscription = FREE
fanartimage = os.path.join(settings.getAddonInfo("path"), "fanart.jpg")

"""
Data directory for cookie saving
"""
data_dir = xbmc.translatePath(settings.getAddonInfo('profile'))
cookie_file = os.path.join(settings.getAddonInfo('path'), 'cookies')

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
                reg_cat   = '<h1 style="padding-left:55px;">.*</h1>'
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
    
    xbmc.log(msg=pluginLogHeader + "Logging in",level=xbmc.LOGDEBUG)
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
        xbmc.log(msg=pluginLogHeader + "Invalid username, aborting",level=xbmc.LOGFATAL)
        err = xbmcgui.Dialog()
        err.ok(unicode(language(30023)), unicode(language(30017)), unicode(language(30018)))
        settings.setSetting('loginok', "")
        raise loginExpcetion()
    elif re.compile('votre quota').findall(str(res)):
        xbmc.log(msg=pluginLogHeader + "User account locked",level=xbmc.LOGSEVERE)
        err = xbmcgui.Dialog()
        err.ok(unicode(language(30022)), unicode(language(30019)), unicode(language(30020)), unicode(language(30021)))
        settings.setSetting('loginok', "")
        raise loginExpcetion()
    else:
        xbmc.log(msg=pluginLogHeader + "Valid User",level=xbmc.LOGDEBUG)
        settings.setSetting('loginok', "ok")

def initialIndex():
    """Creates initial index
    
    Create the initial menu with the right identification values for the add-on to know which option have been selected
    """
    add_dir(unicode(language(30014)), 'http://mobile.nolife-tv.com', MODE_LAST_SHOWS, '')
    add_dir(unicode(language(30015)), 'http://mobile.nolife-tv.com', MODE_CATEGORIES, '')
    add_dir(unicode(language(30016)), 'http://mobile.nolife-tv.com', MODE_SEARCH, '')

def getlastVideos():
    """Get last uploaded videos
        
    Get the videos in the "last videos" menu option
    """
    showseen       = settings.getSetting( "showseen" )
    showpromo      = settings.getSetting( "showpromo" )
    showannounce   = settings.getSetting( "showannounce" )
    agelimit       = settings.getSetting( "agelimit" )
    showlast       = int(settings.getSetting( "showlast" ).split('.')[0])
    i = 0
    emissions = []
    finished = False
    while finished == False:
        postrequest = urllib.urlencode({'emissions': i,
                                   'famille': 0,
                                   'a': 'ge'})
        
        page = requestHandler.open("http://mobile.nolife-tv.com/do.php", postrequest)
        liste = BeautifulSoup(page.read()).findAll('li')
        for element in liste:
            if len(emissions) == showlast:
                finished = True
                break
        
            videoInfo = extractVideoInfo(element)
            if videoInfo != None:
                if (showseen == "true" or (showseen == "false" and videoInfo.seen == False)):
                    if videoInfo.videocat == "Autopromo" and showpromo == "false":
                        continue
                    if videoInfo.videocat == "Annonce" and showannounce == "false":
                        continue
                    if ( videoInfo.agelimit == None or agelimit == "Aucun" ):
                        if isAvailableForUser(videoInfo.availability):
                            emissions.append([videoInfo.id,
                                    videoInfo.name,
                                    videoInfo.desc,
                                    videoInfo.duration,
                                    videoInfo.seen,
                                    videoInfo.thumb])
                    elif int(videoInfo.agelimit) < int(agelimit):
                        if isAvailableForUser(videoInfo.availability):
                            emissions.append([videoInfo.id,
                                    videoInfo.name,
                                    videoInfo.desc,
                                    videoInfo.duration,
                                    videoInfo.seen,
                                    videoInfo.thumb])
        i = i + 1

    for emission in emissions:
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
            videoInfo = extractVideoSearchInfo(element)

            if videoInfo != None:
                if isAvailableForUser(videoInfo.availability):
                    addlink(videoInfo.name + " - " + videoInfo.desc,
                        "plugin://plugin.video.nolife?id=" + videoInfo.id,
                        videoInfo.thumb,
                        videoInfo.duration,
                        videoInfo.seen )

def getshows(category):
    """
    Gets shows in a category
    """
    emissions = parse_categories()
    excluded_shows = [ '75', '104', '89' ]
    for emission in emissions:
        if  not emission[2] in excluded_shows:
            if emission[0] == category:
                add_dir(emission[1], emission[2], MODE_LINKS, emission[3])

def isAvailableForUser(type_of_show):
    """
    Return true is the show is available for user, false otherwise
    """
    if "Archive" in type_of_show:
        if subscription >= SUPPORT:
            return True
        else:
            return False
    elif "Standard" in type_of_show:
        if subscription >= STANDARD or settings.getSetting("extracts") == 'true':
            return True
        else:
            return False
    else:
        return True

def getlinks(show):
    """
    Get videos links from a show
    """
    settings   = xbmcaddon.Addon(id='plugin.video.nolife')
    show_n     = settings.getSetting( "show_n" )
    showall    = settings.getSetting( "showall" )
    showseen   = settings.getSetting( "showseen" )

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
                
                videoInfo = extractVideoInfo(element)

                if isAvailableForUser(videoInfo.availability):
                        emissions.append([videoInfo.id,
                                            videoInfo.name,
                                            videoInfo.desc,
                                            videoInfo.duration,
                                            videoInfo.seen,
                                            videoInfo.thumb])
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
    quality  = settings.getSetting( "quality" )
    autorefresh = settings.getSetting("autorefresh")
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

    requestHandler.addheaders = [("User-agent", useragent)]
    page = requestHandler.open(_video)
    url  = page.geturl()
    xbmc.log(msg=pluginLogHeader + "URL :" + url,level=xbmc.LOGDEBUG)
    listitem   = xbmcgui.ListItem( label='', 
                                   iconImage='', 
                                   thumbnailImage='', 
                                   path=url )

    xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, listitem)
    if autorefresh == "true":
        xbmc.executebuiltin("Container.Refresh")

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
                              "playcount": int(bool_seen) } 
               )
    liz.addStreamInfo("video", { 'duration':duration })
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
        url = sys.argv[0]+"?url="+urllib.quote_plus(url)+\
            "&mode="+str(mode)+"&name="+urllib.quote_plus(name)
    else:
        url = sys.argv[0]+"?url="+urllib.quote_plus(url)+\
        "&mode="+str(mode)+"&name="+urllib.quote_plus(name.encode("ascii", "ignore"))
    showid = url.split('?')[1].split('&')[0].split('=')[1]
    thumbnailimage = os.path.join(settings.getAddonInfo("path"), 'resources', 'images', showid + '.jpeg')
    if not iconimage == '':
        liz = xbmcgui.ListItem(name,
                               iconImage=iconimage,
                               thumbnailImage=iconimage)
    else:
        liz = xbmcgui.ListItem(name,
                               iconImage=thumbnailimage,
                               thumbnailImage=thumbnailimage)

    liz.setInfo( 
                 type="Video", 
                 infoLabels={ "Title": name } 
               )
    liz.setProperty('fanart_image', fanartimage)
    ok  = xbmcplugin.addDirectoryItem( handle=int(sys.argv[1]), 
                                       url=url, 
                                       listitem=liz, 
                                       isFolder=True )
    return ok

def get_subscription_mode():
    """
    Return the subscription mode for the current user
    """
    url = "http://mobile.nolife-tv.com/abonnement/"

    page = requestHandler.open(url)
    htmlContent = page.read();
    if "Soutien" in htmlContent:
        xbmc.log(msg=pluginLogHeader + "User has a support account",level=xbmc.LOGNOTICE)
        return SUPPORT
    elif "Standard" in htmlContent:
        xbmc.log(msg=pluginLogHeader + "User has a standard account",level=xbmc.LOGNOTICE)
        return STANDARD
    else :
        xbmc.log(msg=pluginLogHeader + "User has no account",level=xbmc.LOGNOTICE)
        return FREE


def extractVideoInfo(element):
    """
    Extract video info from html and store it in videoInfo class    
    """
    info = None
    if re.compile('data-icon="arrow-r"').findall(str(element)):
        info = videoInfo()
        if  re.compile('mark_read').findall(str(element)):
            info.seen = True
        else:
            info.seen = False
        
        reg_date = '<p style="padding-right:25px;'\
            ' padding-left:55px;">.*</p>'
        info.thumb    = re.compile('data-thumb=".*"').findall(str(element))[0][12:][:-1]
        _date_len = remove_html_tags(re.compile(reg_date).findall(str(element))[0])
        info.duration = sum(int(x) * 60 ** i for i,x in enumerate(reversed(_date_len.split(' - ')[1].strip('s').split(":"))))
        
        req_id = 'a href="emission-.*" '
        info.id = re.compile(req_id).findall(str(element))[0][17:][:-2]
        
        req_availability = '<p style="float:right; margin-right:-15px; clear:right;"><strong>.*'
        info.availability = remove_html_tags(re.compile(req_availability).findall(str(element))[0][57:].replace("[", "").replace("]", ""))

        reg_vid = 'a href="emission-.*" '
        info.vid   = re.compile(reg_vid).findall(str(element))[0][17:][:-2]
        
        reg_desc = '<p style="padding-left:55px;"><strong>.*'
        info.desc  = remove_html_tags(re.compile(reg_desc).findall(str(element))[0][30:])

        info.name  = remove_html_tags(re.compile('<h3.*').findall(str(element))[0])
        
        info.videocat = remove_html_tags(re.compile('<strong.*').findall(str(element))[0])

        try:
            info.agelimit = re.compile('<img.*').findall(str(element))[1][56:][:2]
        except:
            info.agelimit = None

    return info

def extractVideoSearchInfo(element):
    """
    Extract video info from html from a search page and store it in videoInfo class
    """
    info = None
    if re.compile('data-icon="arrow-r"').findall(str(element)):
        info = videoInfo()
        if  re.compile('mark_read').findall(str(element)):
            info.seen = True
        else:
            info.seen = False
    
        reg_srch = 'a href="emission-.*" '
        info.id = re.compile(reg_srch).findall(str(element))[0][17:][:-2]

        reg_desc = '<p style="padding-left:55px;"><strong>.*'
        info.thumb    = re.compile('data-thumb=".*"').findall(str(element))[0][12:][:-1]
        _bdesc = re.compile(reg_desc).findall(str(element))[0][30:]
        _bname = re.compile('<h3.*').findall(str(element))[0]
        info.desc = remove_html_tags(_bdesc)
        info.name = remove_html_tags(_bname)

        req_availibity = '<p style="float:right; margin-right:-15px; clear:right;"><strong>.*'
        info.availability = remove_html_tags(re.compile(req_availibity).findall(str(element))[0][30:])
    
        reg_date = '<p style="padding-right:25px; padding-left:55px;">.*</p>'
        _date_len = remove_html_tags(re.compile(reg_date).findall(str(element))[0])
        info.duration = _date_len.split(' - ')[1]

    return info

def createCookie():
    """
    Create a cookie.
    If an older cookie exists its removed before the creation of the new cookie
    """
    xbmc.log(msg=pluginLogHeader + "Creation of new cookie",level=xbmc.LOGDEBUG)
    settings.setSetting('loginok', "")
    if os.path.isfile(cookie_file):
        os.remove(cookie_file)
    cj = cookielib.LWPCookieJar()
    return cj
    

def loadCookie():
    """
    Load a cookie file
    """
    xbmc.log(msg=pluginLogHeader + "Loading cookie",level=xbmc.LOGDEBUG)
    cj = cookielib.LWPCookieJar()
    cj.load(filename=cookie_file, ignore_discard=True)
    return cj
    
def saveCookie():
    """
    Save cookieJar to cookie file
    """
    xbmc.log(msg=pluginLogHeader + "Saving cookie",level=xbmc.LOGDEBUG)
    cj.save(filename=cookie_file, ignore_discard=True)

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
if not os.path.isfile(cookie_file) or (datetime.datetime.now() - datetime.datetime.fromtimestamp(os.stat(cookie_file).st_mtime)).seconds > 900:
        xbmc.log(msg=pluginLogHeader + "Cookie is too old or does not exists",level=xbmc.LOGDEBUG)
        cj = createCookie()
        saveCookie()

cj = loadCookie()
requestHandler = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))

xbmc.log(msg=pluginLogHeader + "Login state : " + settings.getSetting('loginok'),level=xbmc.LOGDEBUG)
if settings.getSetting('authenticate') == "true":
    if not settings.getSetting('loginok') == "ok":
        xbmc.log(msg=pluginLogHeader + "User not logged",level=xbmc.LOGDEBUG)
        xbmc.log(msg=pluginLogHeader + "Process to login",level=xbmc.LOGDEBUG)
        login()
        xbmc.log(msg=pluginLogHeader + "Reading subscription mode",level=xbmc.LOGDEBUG)
        settings.setSetting('subscriptionMode',str(get_subscription_mode()))
        saveCookie()
else:
    xbmc.log(msg=pluginLogHeader + "Authenticated mode not requested",level=xbmc.LOGDEBUG)
    xbmc.log(msg=pluginLogHeader + "Reading subscription mode",level=xbmc.LOGDEBUG)
    settings.setSetting('subscriptionMode','0')
    
# Find the access mode of the user
subscription = settings.getSetting('subscriptionMode')
xbmc.log(msg=pluginLogHeader + "User mode value : " + subscription,level=xbmc.LOGDEBUG)

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
