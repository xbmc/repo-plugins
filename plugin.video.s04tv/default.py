# Copyright (C) 2015 Malte Loepmann (maloep@googlemail.com)
#
# This program is free software; you can redistribute it and/or modify it under the terms 
# of the GNU General Public License as published by the Free Software Foundation; 
# either version 2 of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; 
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. 
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with this program; 
# if not, see <http://www.gnu.org/licenses/>.

import xbmc, xbmcplugin, xbmcgui, xbmcaddon
import os, sys, re, json, string, random
import urllib, urllib2
from urlparse import *
import xml.etree.ElementTree as ET


PLUGINNAME = 'S04tv'
PLUGINID = 'plugin.video.s04tv'
BASE_URL = 'http://www.s04.tv'

# Shared resources
addonPath = ''
__addon__ = xbmcaddon.Addon(id='plugin.video.s04tv')
addonPath = __addon__.getAddonInfo('path')
        
BASE_RESOURCE_PATH = os.path.join(addonPath, "resources" )
sys.path.append( os.path.join( BASE_RESOURCE_PATH, "lib" ) )
sys.path.append( os.path.join( BASE_RESOURCE_PATH, "lib", "BeautifulSoup" ) )

from BeautifulSoup import BeautifulSoup
from BeautifulSoup import Tag
import mechanize

__language__ = __addon__.getLocalizedString
thisPlugin = int(sys.argv[1])
browser = mechanize.Browser()

missingelementtext = "Missing element '%s'. Maybe the site structure has changed."


videoquality = __addon__.getSetting('videoquality')
if videoquality == 'low':
    max_res = 480
elif videoquality == 'mid':
    max_res = 640
elif videoquality == 'high':
    max_res = 960
elif videoquality == 'hd':
    max_res = 1280


def buildHomeDir(url, doc):
    xbmc.log('buildHomeDir')
    path = xbmc.translatePath('special://profile/addon_data/%s' %(PLUGINID))

    if not os.path.exists(path):
        try:
            os.makedirs(path)
        except:
                path = ''
    
    soup = BeautifulSoup(''.join(doc))
    
    nav = soup.find('nav')
    if(not nav):
        xbmc.log(missingelementtext%'nav')
        return
    
    for navitem in nav.contents:
        #first tag is our ul
        if(type(navitem) == Tag):
            for ulitem in navitem.contents:
                if(type(ulitem) == Tag):
                    if(ulitem.name == 'li'):
                        a = ulitem.find('a')
                        if(not a):
                            xbmc.log(missingelementtext%'a')
                            continue
                        url = BASE_URL + a['href']
                        addDir(a.text, url, 2, '')
            break
        

def buildSubDir(url, doc):
    xbmc.log('buildSubDir')
    soup = BeautifulSoup(''.join(doc))
    
    nav = soup.find('ul', attrs={'class': 'contentnav'})
    if(not nav):
        #no subdir (home page or flat category)
        buildVideoDir(url, doc)
        return
    
    div =  nav.find('div')
    if(not div):
        #no subdir (home page or flat category)
        buildVideoDir(url, doc)
        return
    
    ul = div.find('ul')
    for ulitem in ul.contents:
        if(type(ulitem) == Tag):
            if(ulitem.name == 'li'):
                a = ulitem.find('a')
                if(not a):
                    xbmc.log(missingelementtext%'a')
                    continue
                url = BASE_URL + a['href']
                addDir(a.text, url, 3, '')
        
        
def buildSubSubDir(url, doc):
    xbmc.log('buildSubSubDir')
    soup = BeautifulSoup(''.join(doc))
    
    #get pagenumber
    indexpage = url.find('page/')
    indexpage = indexpage + len('page/')
    indexminus = url.find('-', indexpage)
    pagenumber = ''
    if(indexpage >=0 and indexminus > indexpage): 
        pagenumber = url[indexpage:indexminus]
    
    #check if we have corresponding sub menus
    li = soup.find('li', attrs={'class':'dm_%s'%pagenumber})
    if(not li):
        #no sub sub dir
        buildVideoDir(url, doc)
        return
    
    div =  li.find('div')
    if(not div):
        xbmc.log(missingelementtext%'div')
        return
    ul = div.find('ul')
    if(not ul):
        xbmc.log(missingelementtext%'ul')
        return
    for ulitem in ul.contents:
        if(type(ulitem) == Tag):
            if(ulitem.name == 'li'):
                a = ulitem.find('a')
                if(not a):
                    xbmc.log(missingelementtext%'a')
                    continue
                url = BASE_URL + a['href']
                addDir(a.text, url, 3, '')


def buildVideoDir(url, doc):
    xbmc.log('buildVideoDir')    
    
    #allow sorting of video titles
    xbmcplugin.addSortMethod(thisPlugin, xbmcplugin.SORT_METHOD_UNSORTED)    
    xbmcplugin.addSortMethod(thisPlugin, xbmcplugin.SORT_METHOD_DATE)
    xbmcplugin.addSortMethod(thisPlugin, xbmcplugin.SORT_METHOD_TITLE)
    
    hideexclusive = __addon__.getSetting('hideexclusivevideos').upper() == 'TRUE'
    hideflag = __addon__.getSetting('hidefreeexclflag').upper() == 'TRUE'
    hidedate = __addon__.getSetting('hidedate').upper() == 'TRUE'
    
    soup = BeautifulSoup(''.join(doc))
    articles = soup.findAll('article')
    if(not articles):
        xbmc.log(missingelementtext%'article')
        return
    
    origUrl = url
    
    for article in articles:
                
        #HACK: ignore related videos
        try:
            id = article['id']
            if(id and id.startswith('rel_vid')):
                continue
        except:
            pass
                
        div = article.find('div')
        if(not div):
            xbmc.log(missingelementtext%'div')
            continue
        
        flag = div['class']
        
        #for some reason findNextSibling does not work here and contents is not set properly
        date = ''
        if(origUrl.find('home') < 0):
            p = div.findAllNext('p', limit=1)
            if(not p):
                xbmc.log(missingelementtext%'p')
            else:
                date = p[0].text
                
        img = div.findAllNext('img', limit=1)
        if(not img):
            xbmc.log(missingelementtext%'img')
            continue
        imageUrl = img[0]['src']
        
        #HACK: this is only required on home page
        h2 = img[0].findAllNext('h2', limit=1)
        if(h2):
            a = h2[0].findAllNext('a', limit=1)
            if(not a):
                xbmc.log(missingelementtext%'a')
                continue
            url = a[0]['href']
            span = a[0].find('span')
        else:
            a = img[0].findAllNext('a', limit=1)
            if(not a):
                xbmc.log(missingelementtext%'a')
                continue
            url = a[0]['href']
            span = a[0].find('span')
        
        if(not span):
            xbmc.log(missingelementtext%'span')
            continue
        
        title = ''
        for text in span.contents:
            if(type(text) != Tag):
                if(title != ''):
                    title = title +': '
                title = title +text
                
        #only required for homescreen
        span2 = span.nextSibling
        if(span2):
            title = title +': ' +span2.text
                
        if(not hidedate and date != ''):
            title = title + ' (%s)'%date
                
        extraInfo = {}
        if(flag == 'flag_free'):
            if(not hideflag):
                title = '[FREE] ' +title
            extraInfo['IsFreeContent'] = 'True'
        elif(flag == 'flag_excl'):
            if(hideexclusive):
                #don't add exclusive videos to list
                continue
            if(not hideflag):
                title = '[EXCL] ' +title
            extraInfo['IsFreeContent'] = 'False'
        
        if(not url.startswith("http")):
            url = BASE_URL + url
        addLink(title, url, 4, imageUrl, date, extraInfo)
    
    #paging
    pageid = 0
    page = 0
    match_page = re.compile('http://www.s04.tv/cache/TV/pages/videoverteil_(.+)_(.+).htm', re.DOTALL).findall(origUrl)
    if(match_page):
        pageid = match_page[0][0]
        page = (int)(match_page[0][1])
        addDir(__language__(30003), 'http://www.s04.tv/cache/TV/pages/videoverteil_%s_%s.html'%(pageid, page + 1), 3, '')
    else:
        paging = soup.find('ul', attrs={'class': 'paging'})
        if(paging):
            a = paging.find('a')
            onclick = a['onclick']
            match_page = re.compile('changeVideoPage\(0,(.+)\)', re.DOTALL).findall(onclick)
            pageid = (int)(match_page[0])
            addDir(__language__(30003), 'http://www.s04.tv/cache/TV/pages/videoverteil_%s_%s.html'%(pageid, 2), 3, '')
        


def getVideoUrl(url, doc):
    xbmc.log('getVideoUrl: url=' +url)
    
	#HACK: Free content may be hosted on youtube
    if(url.startswith("https://youtu.be/")):
        videoId = url.replace("https://youtu.be/", "")
        url='plugin://plugin.video.youtube/?action=play_video&videoid=' +videoId
        listitem = xbmcgui.ListItem(path=url)
        return xbmcplugin.setResolvedUrl(thisPlugin, True, listitem)
	
    #check if we need to login
    isFreeContent = xbmc.getInfoLabel( "ListItem.Property(IsFreeContent)" ) == 'True'
    if(not isFreeContent):
        success = login()
        if(not success):
            return
    
    soup = BeautifulSoup(''.join(doc))   
    iframe = soup.find('iframe', attrs={'class': 'videoframe'})
    if(not iframe):
        xbmc.log(missingelementtext%'iframe')
        return
    
    playerUrl = iframe['src']
        
    response=getUrl(playerUrl)
    
    match_streamid=re.compile('streamid="(.+?)"', re.DOTALL).findall(response)
    streamid = match_streamid[0]
    
    match_partnerid=re.compile('partnerid="(.+?)"', re.DOTALL).findall(response)
    partnerid = match_partnerid[0]

    match_portalid=re.compile('portalid="(.+?)"', re.DOTALL).findall(response)
    portalid = match_portalid[0]

    match_sprache=re.compile('sprache="(.+?)"', re.DOTALL).findall(response)
    sprache = match_sprache[0]

    match_auth=re.compile('auth="(.+?)"', re.DOTALL).findall(response)
    auth = match_auth[0]

    match_timestamp=re.compile('timestamp="(.+?)"', re.DOTALL).findall(response)
    timestamp = match_timestamp[0]

    wsUrl = 'http://www.s04.tv/webservice/video_xml.php?play='+streamid+'&partner='+partnerid+'&portal='+portalid+'&v5ident=&lang='+sprache
    response=getUrl(wsUrl)
    
    match_url=re.compile('<url>(.+?)<', re.DOTALL).findall(response)
    
    response=getUrl(match_url[0]+'&timestamp='+timestamp+'&auth='+auth)
    
    match_new_auth=re.compile('auth="(.+?)"', re.DOTALL).findall(response)
    match_new_url=re.compile('url="(.+?)"', re.DOTALL).findall(response)

    m3u8_url = match_new_url[0].replace('/z/','/i/').replace('manifest.f4m','master.m3u8')+'?hdnea='+match_new_auth[0]+'&g='+char_gen(12)+'&hdcore=3.2.0'
    response=getUrl(m3u8_url)
    match_sec_m3u8=re.compile('http(.+?)null=', re.DOTALL).findall(response)
    
    lines = response.split('\n')
    choose_url = False    
    stored_res = 0
    
    xbmc.log('max_res = ' +str(max_res))
    for line in lines:
        if '#EXT-X-STREAM-INF' in line:
            match_res=re.compile('RESOLUTION=(.+?)x', re.DOTALL).findall(line)
            if(match_res):
                res = (int)(match_res[0])
                xbmc.log('res = ' +str(res))
            if res > stored_res and res <= max_res:
                choose_url = True
                stored_res = res
                xbmc.log('new res = ' +str(stored_res))
        elif choose_url == True:
            sec_m3u8 = line
            choose_url = False
    
    listitem = xbmcgui.ListItem(path=sec_m3u8)
    return xbmcplugin.setResolvedUrl(thisPlugin, True, listitem)


def addDir(name, url, mode, iconimage):
    parameters = {'url' : url.encode('utf-8'), 'mode' : str(mode), 'name' : name.encode('utf-8')}
    u = sys.argv[0] +'?' +urllib.urlencode(parameters)
    ok = True
    listitem = xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
    listitem.setInfo(type="Video", infoLabels={"Title": name})
    ok = xbmcplugin.addDirectoryItem(thisPlugin, u, listitem, isFolder=True)
    return ok
   

def addLink(name, url, mode, iconimage, date, extraInfo = {}):
    parameters = {'url' : url.encode('utf-8'), 'mode' : str(mode), 'name' : name.encode('utf-8')}
    u = sys.argv[0] +'?' +urllib.urlencode(parameters)
    ok = True
    listitem = xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
    if(date != ''):
        listitem.setInfo(type="Video", infoLabels={"Title": name, "Date": date})
    else:
        listitem.setInfo(type="Video", infoLabels={"Title": name})
    listitem.setProperty('IsPlayable', 'true')
    for key in extraInfo.keys():
        listitem.setProperty(key, extraInfo[key])
    ok = xbmcplugin.addDirectoryItem(thisPlugin, u, listitem)
    
    return ok


def login():
    
    username = __addon__.getSetting('username')
    xbmc.log('Logging in with username "%s"' %username)
    password = __addon__.getSetting('password')
    
    if(username == '' or password == ''):
        xbmcgui.Dialog().ok(PLUGINNAME, __language__(30102), __language__(30103))
        return False
        
    loginparams = {'username_field' : username, 'password_field' : password}
    loginurl = 'https://ssl.s04.tv/get_content.php?lang=TV&form=login&%s' %urllib.urlencode(loginparams)
    
    
    browser.open(loginurl)
    loginresponse = browser.response().read()
    xbmc.log('login response: ' +loginresponse)
    
    #loginresponse should look like this: ({"StatusCode":"1","stat":"OK","UserData":{"SessionID":"...","Firstname":"...","Lastname":"...","Username":"lom","hasAbo":1,"AboExpiry":"31.07.14"},"out":"<form>...</form>"});
    #remove (); from response
    jsonstring = loginresponse[1:len(loginresponse) -2]
    jsonResult = json.loads(jsonstring)
    if(jsonResult['stat'] == "OK"):
        userdata = jsonResult['UserData']
        if(userdata['hasAbo'] == 1):
            xbmc.log('login successful')
            return True
        else:
            xbmc.log('no valid abo')
            xbmcgui.Dialog().ok(PLUGINNAME, __language__(30100) %username.decode('utf-8'), __language__(30101))
            return False
    else:
        xbmc.log('login failed')
        xbmcgui.Dialog().ok(PLUGINNAME, __language__(30100) %username.decode('utf-8'), __language__(30101))
        return False
    

def getUrl(url):
        url = url.replace('&amp;','&')
        url = url.replace('&#38;','&')
        xbmc.log('Get url: '+url)
        browser.set_handle_robots(False)
        try:
            browser.open(url)        
            response = browser.response().read()
        except Exception, (exc):
            xbmc.log('Error while opening url: ' +str(exc))
            return ''
        return response
    

def num_gen(size=1, chars=string.digits):
        return ''.join(random.choice(chars) for x in range(size))


def char_gen(size=1, chars=string.ascii_uppercase):
    return ''.join(random.choice(chars) for x in range(size))


def runPlugin(url, doc):
    
    if mode==None or doc==None or len(doc)<1:
        buildHomeDir(url, doc)
       
    elif mode==1:
        buildHomeDir(url, doc)
            
    elif mode==2:
        buildSubDir(url, doc)
        
    elif mode==3:
        buildSubSubDir(url, doc)
        
    elif mode == 4:
        getVideoUrl(url, doc)


xbmc.log('S04TV: start addon')

params = parse_qs(urlparse(sys.argv[2]).query)
url=None
name=None
mode=None

try:
    url=params["url"][0]
except:
    pass
try:
    name=params["name"][0]
except:
    pass
try:
    mode=int(params["mode"][0])
except:
    pass

print "Mode: "+str(mode)
print "URL: "+str(url)
print "Name: "+str(name)

if(url == None):
    url = BASE_URL

doc = getUrl(url)
runPlugin(url, doc)
xbmcplugin.endOfDirectory(thisPlugin)
