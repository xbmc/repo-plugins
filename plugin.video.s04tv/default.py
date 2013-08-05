# Copyright (C) 2013 Malte Loepmann (maloep@googlemail.com)
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


__language__ = __addon__.getLocalizedString
thisPlugin = int(sys.argv[1])

missingelementtext = "Missing element '%s'. Maybe the site structure has changed."

def buildHomeDir(url, doc):
    xbmc.log('buildHomeDir')
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
                        addDir(a.text, url, 2, '', '')
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
                addDir(a.text, url, 3, '', '')
        
        
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
                addDir(a.text, url, 3, '', '')


def buildVideoDir(url, doc):
    xbmc.log('buildVideoDir')
    
    #allow sorting of video titles
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_UNSORTED)    
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_DATE)
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_TITLE)
    
    hideexclusive = __addon__.getSetting('hideexclusivevideos').upper() == 'TRUE'
    hideflag = __addon__.getSetting('hidefreeexclflag').upper() == 'TRUE'
    hidedate = __addon__.getSetting('hidedate').upper() == 'TRUE'
    
    soup = BeautifulSoup(''.join(doc))
    articles = soup.findAll('article')
    if(not articles):
        xbmc.log(missingelementtext%'article')
        return
    
    for article in articles:
                
        div = article.find('div')
        if(not div):
            xbmc.log(missingelementtext%'div')
            continue
        
        flag = div['class']
        
        #for some reason findNextSibling does not work here
        p = div.findAllNext('p', limit=1)
        if(not p):
            xbmc.log(missingelementtext%'p')
            continue
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
                
        if(not hidedate):
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
                
        url = BASE_URL + url
        addDir(title, url, 4, imageUrl, date, extraInfo)


def getVideoUrl(url, doc):
    xbmc.log('getVideoUrl')
    
    #check if we are allowed to watch this video
    isFreeContent = xbmc.getInfoLabel( "ListItem.Property(IsFreeContent)" ) == 'True'
    if(not isFreeContent):
        success = login()
        if(not success):
            return
    
    soup = BeautifulSoup(''.join(doc))
    
    #title
    p = soup.find('p', attrs={'class': 'breadcrumbs'})
    if(not p):
        xbmc.log(missingelementtext%'p')
        return
    a = p.find('a')
    if(not a):
        xbmc.log(missingelementtext%'a')
        return
    title = a['title']
    if(title == ''):
        title = __language__(30005)
    
    #grab url
    div = soup.find('div', attrs={'class': 'videobox'})
    if(not div):
        xbmc.log(missingelementtext%'div')
        return
    script = div.find('script', attrs={'type': 'text/javascript'})
    if(not script):
        xbmc.log(missingelementtext%'script')
        return
    scripttext = script.next
    indexbegin = scripttext.find("videoid: '")
    indexbegin = indexbegin + len("videoid: '")
    indexend = scripttext.find("'", indexbegin)
    xmlurl = ''
    if(indexbegin >= 0 and indexend > indexbegin):
        xmlurl = scripttext[indexbegin:indexend]
    else:
        xbmc.log('Could not find videoid in script')
        return
    
    #load xml file
    xmlstring = getUrl(BASE_URL +xmlurl)
    root = ET.fromstring(xmlstring)
    
    urlElement = root.find('invoke/url')
    if(urlElement == None):
        print 'urlElement: ' +str(urlElement)
        xbmc.log(missingelementtext%'invoke/url')
        return
    
    xmlstring = getUrl(urlElement.text)
    root = ET.fromstring(xmlstring)
    metas = root.findall('head/meta')
    if(metas == None):
        xbmc.log(missingelementtext%'head/meta')
        return
    vid_base_url = ''
    for meta in metas:
        if( meta.attrib.get('name') == 'httpBase'):
            vid_base_url = meta.attrib.get('content')
            break
    
    quality = __addon__.getSetting('videoquality')
    quality = '_%s.mp4'%quality
    videos = root.findall('body/switch/video')
    if(videos == None):
        xbmc.log(missingelementtext%'body/switch/video')
        return
    for video in videos:
        src = video.attrib.get('src')
        if(src.find(quality) > 0):
            break
    
    v = '2.11.3'
    fp = 'WIN%2011,8,800,97'
    r = num_gen(5, string.ascii_uppercase)
    g = num_gen(12, string.ascii_uppercase)
    videourl = vid_base_url +src +'&v=%s&fp=%s&r=%s&g=%s'%(v,fp,r,g)
    addLink(title, videourl, '')


def addDir(name, url, mode, iconimage, date, extraInfo = {}):
    parameters = {'url' : url.encode('utf-8'), 'mode' : str(mode), 'name' : name.encode('utf-8')}
    u = sys.argv[0] +'?' +urllib.urlencode(parameters)
    #xbmc.log('addDir url = ' +str(u))
    ok = True
    liz = xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
    if(date != ''):
        liz.setInfo(type="Video", infoLabels={"Title": name, "Date": date})
    else:
        liz.setInfo(type="Video", infoLabels={"Title": name})
    for key in extraInfo.keys():
        liz.setProperty(key, extraInfo[key])
    ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=True)
    return ok
   

def addLink(name,url,iconimage):
    #xbmc.log('addLink url = ' +str(url))
    ok = True
    liz = xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
    liz.setInfo(type="Video", infoLabels={ "Title": name})
    ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=url, listitem=liz)
    
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
    loginresponse = getUrl(loginurl)
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
            xbmcgui.Dialog().ok(PLUGINNAME, __language__(30100) %username, __language__(30101))
            return False
    else:
        xbmc.log('login failed')
        xbmcgui.Dialog().ok(PLUGINNAME, __language__(30100) %username, __language__(30101))
        return False
    

def getUrl(url):
        url = url.replace('&amp;','&')
        xbmc.log('Get url: '+url)
        req = urllib2.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
        response = urllib2.urlopen(req)
        link=response.read()
        response.close()
        return link
    

def num_gen(size=1, chars=string.digits):
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
#sort video items
xbmcplugin.endOfDirectory(thisPlugin)
