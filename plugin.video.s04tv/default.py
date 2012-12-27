# Copyright (C) 2012 Malte Loepmann (maloep@googlemail.com)
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

import xbmcplugin
import xbmcgui
import xbmcaddon
import os, sys, re
import urllib, urllib2
from urlparse import *

PLUGINNAME = 'S04tv'
PLUGINID = 'plugin.video.s04tv'
BASE_URL = 'https://www.s04tv.de/'

# Shared resources
addonPath = ''

import xbmcaddon
__addon__ = xbmcaddon.Addon(id='plugin.video.s04tv')
addonPath = __addon__.getAddonInfo('path')
        
BASE_RESOURCE_PATH = os.path.join(addonPath, "resources" )
sys.path.append( os.path.join( BASE_RESOURCE_PATH, "lib" ) )
sys.path.append( os.path.join( BASE_RESOURCE_PATH, "lib", "BeautifulSoup" ) )
sys.path.append( os.path.join( BASE_RESOURCE_PATH, "lib", "mechanize" ) )

from BeautifulSoup import BeautifulSoup
import mechanize

__language__ = __addon__.getLocalizedString
thisPlugin = int(sys.argv[1])

browser = mechanize.Browser()


def buildVideoList(doc):
    xbmc.log('buildVideoList')
    
    #parse complete document
    soup = BeautifulSoup(''.join(doc))
    
    container = soup.findAll('div', attrs={'class' : 'layout_full'})
    if(not container):
        xbmc.log('Error while building video list. class "layout_full" not found.')
        return
    
    #iterate content
    for content in container[0].contents:
        #ignore NavigableStrings
        if(type(content).__name__ == 'NavigableString'):        
            continue
                        
        itemTitle = findTitle(content, 'div', {'class' : 'field Headline'})        
        if(itemTitle == ''):
            xbmc.log('Error while building video list. class "field Headline" not found.')
            continue
        
        titlePart2 = findTitle(content, 'div', {'class' : 'field untertitel'})        
        if(titlePart2 == ''):
            titlePart2 = findTitle(content, 'div', {'class' : 'field Beitragsart'})
        
        if(titlePart2 != ''):
            itemTitle = itemTitle +': ' +titlePart2
        
        linkValue = ''
        imageUrlValue = ''
        imageTag = content.find('div', attrs={'class' : 'field Bild'})
        if(imageTag):
            link = imageTag.find('a')
            linkValue = link['href']
            imageUrl = imageTag.find('img')    
            imageUrlValue = BASE_URL +imageUrl['src']
        else:
            xbmc.log('Error while building video list. class "field Bild" not found.')
            continue
            
        url = BASE_URL + linkValue
        addDir(itemTitle, url, 2, imageUrlValue)
    
    #previous page
    previousTag = soup.find('a', attrs={'class' : 'previous'})
    if(previousTag):
        pageLink = previousTag['href']
        itemTitle = __language__(30002)
        url = BASE_URL + pageLink
        addDir(itemTitle, url, 1, '')
    
    #next page
    nextTag = soup.find('a', attrs={'class' : 'next'})
    if(nextTag):
        pageLink = nextTag['href']
        itemTitle = __language__(30003)
        url = BASE_URL + pageLink
        addDir(itemTitle, url, 1, '')


def buildVideoLinks(doc, name):
    xbmc.log('buildVideoLinks')

    #parse complete document
    soup = BeautifulSoup(''.join(doc))
    videoTag = soup.find('video')
    
    if(videoTag):
        sourceTag = videoTag.find('source')
        if(sourceTag):
            videoUrl = sourceTag['src']
            xbmc.log('start playing video: ' +videoUrl)
            addLink(name, videoUrl, os.path.join(addonPath, 'icon.png'))
        else:
            xbmc.log('Error while loading video from page. Maybe you are not logged in or site structure has changed.')
    else:
        xbmc.log('Error while loading video from page. Maybe you are not logged in or site structure has changed.')
        

def provideTestvideoDir():

    xbmc.log('provideTestvideo')
    
    url = 'https://www.s04tv.de/index.php/s04tv-kostenlos.html'
    browser.open(url)    
    doc = browser.response().read()
    soup = BeautifulSoup(''.join(doc))
    
    xbmc.log('site loaded')
    
    imageTag = soup.find('div', attrs={'class' : 'field Bild'})
    if(not imageTag):
        xbmc.log('Error while loading test video. div "field Bild" not found.')
        return
    
    link = imageTag.find('a')
    if(not link):
        xbmc.log('Error while loading test video. "a href" not found.')
    linkValue = link['href']
    imageUrl = imageTag.find('img')    
    imageUrlValue = BASE_URL +imageUrl['src']
    
    newUrl = BASE_URL +linkValue
    
    xbmc.log('new url: ' +newUrl)
    browser.open(newUrl)
    
    doc = browser.response().read()
    soup = BeautifulSoup(''.join(doc))
    
    videoTag = soup.find('video')
    if(not videoTag):
        xbmc.log('Error while loading test video. "video" tag not found.')
        return
    sourceTag = videoTag.find('source')
    if(not sourceTag):
        xbmc.log('Error while loading test video. "video" tag not found.')
        return
    
    videoUrl = sourceTag['src']
    addLink(__language__(30004), videoUrl, imageUrlValue)


def addDir(name,url,mode,iconimage):
    parameters = {'url' : url, 'mode' : str(mode), 'name' : __language__(30005)}
    u = sys.argv[0] +'?' +urllib.urlencode(parameters)
    xbmc.log('addDir url = ' +str(u))
    ok = True
    liz = xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
    liz.setInfo(type="Video", infoLabels={"Title": name})
    ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=True)
    return ok
   

def addLink(name,url,iconimage):
    xbmc.log('addLink url = ' +str(url))
    ok = True
    liz = xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
    liz.setInfo(type="Video", infoLabels={ "Title": name})
    ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=url, listitem=liz)
    return ok


def findTitle(content, searchTag, attrs):
    itemTitle = ''
    titlePart1 = content.find(searchTag, attrs)                
    if(titlePart1):
        titlePart1Value = titlePart1.find('div', attrs={'class' : 'value'})                
        if(titlePart1Value):
            itemTitle = titlePart1Value.string
    if(itemTitle == None):
        itemTitle = ''
    return itemTitle



def login(cookieFile):

    username = __addon__.getSetting('username')
    xbmc.log('username: ' +username) 
    password = __addon__.getSetting('password')
    
    cj = mechanize.LWPCookieJar()
    
    try:
        xbmc.log('load cookie file')
        #ignore_discard=True loads session cookies too
        cj.load(cookieFile, ignore_discard=True)
        browser.set_cookiejar(cj)
        
        xbmc.log('cookies loaded, checking if they are still valid...')
        browser.open("https://www.s04tv.de")
        doc = browser.response().read()
        
        loginStatus = checkLogin(doc, username)
        if(loginStatus == 0):
            return True
    #if cookie file does not exist we just keep going...
    except IOError:
        xbmc.log('Error loading cookie file. Trying to log in again.')
        pass
    
    xbmc.log('Logging in')    
        
    browser.open("https://www.s04tv.de")
    #HACK: find out how to address form by name
    browser.select_form(nr=0)
    browser.form['username'] = username
    browser.form['password'] = password
    browser.submit()
    
    cj.save(cookieFile, ignore_discard=True)
    
    doc = browser.response().read()
    loginStatus = checkLogin(doc, username)            
    return loginStatus == 0
    

def checkLogin(doc, username):
    
    print 'checkLogin'
    
    matchLoginSuccessful = re.search('Sie sind angemeldet als', doc, re.IGNORECASE)
    if(matchLoginSuccessful):
        xbmc.log('login successful')
        return 0
    
    matchLoginFailed = re.search('Anmeldung fehlgeschlagen', doc, re.IGNORECASE)
    if(matchLoginFailed):
        xbmc.log('login failed')
        xbmcgui.Dialog().ok(PLUGINNAME, __language__(30100) %username, __language__(30101))
        return 1
    
    matchLoginFailed = re.search('Bitte geben Sie Benutzername und Passwort ein', doc, re.IGNORECASE)
    if(matchLoginFailed):
        xbmc.log('no username or password')
        xbmcgui.Dialog().ok(PLUGINNAME, __language__(30102), __language__(30103))
        return 1
    
    #not logged in but we don't know the reason
    xbmc.log('You are not logged in.')
    #Guess we are not logged in
    return 1
    


def runPlugin(doc):
    
    if mode==None or doc==None or len(doc)<1:
        buildVideoList(doc)
       
    elif mode==1:
        buildVideoList(doc)
            
    elif mode==2:
        buildVideoLinks(doc,name)


print 'S04TV: start addon'

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

path = xbmc.translatePath('special://profile/addon_data/%s' %(PLUGINID))

if not os.path.exists(path):
    try:
        os.makedirs(path)
    except:
        path = ''

success = login(os.path.join(path, 'cookies.txt'))


if(success):
    browser.open(url)
    doc = browser.response().read()
    runPlugin(doc)
else:
    provideTestvideoDir()

xbmcplugin.endOfDirectory(thisPlugin)
    
    

