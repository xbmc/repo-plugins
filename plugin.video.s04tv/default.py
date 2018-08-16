# -*- coding: utf-8 -*-

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
import os, sys, re, json
import urllib
from urlparse import *
#import xml.etree.ElementTree as ET
import cookielib
try:
    # Python 2.6-2.7
    from HTMLParser import HTMLParser
except ImportError:
    # Python 3
    from html.parser import HTMLParser

from BeautifulSoup import BeautifulSoup
import mechanize

PLUGINNAME = 'S04tv'
PLUGINID = 'plugin.video.s04tv'
BASE_URL = 'https://schalke04.de/tv/videos/'

# Shared resources
addonPath = ''
addon = xbmcaddon.Addon(id='plugin.video.s04tv')
addonPath = addon.getAddonInfo('path')

BASE_RESOURCE_PATH = os.path.join(addonPath, "resources" )
sys.path.append( os.path.join( BASE_RESOURCE_PATH, "lib" ) )
sys.path.append( os.path.join( BASE_RESOURCE_PATH, "lib", "BeautifulSoup" ) )


language = addon.getLocalizedString
thisPlugin = int(sys.argv[1])
browser = mechanize.Browser()

missingelementtext = "Missing element '%s'. Maybe the site structure has changed."

videoquality = 'hd720'

quality = addon.getSetting('videoquality')
if quality == 'mid':
    videoquality = 'medium'
elif quality == 'high':
    videoquality = 'hd720'
elif quality == 'hd':
    videoquality = 'hd1080'



def buildVideoDir(url, doc):

    #allow sorting of video titles
    xbmcplugin.addSortMethod(thisPlugin, xbmcplugin.SORT_METHOD_UNSORTED)
    #xbmcplugin.addSortMethod(thisPlugin, xbmcplugin.SORT_METHOD_DATE)
    xbmcplugin.addSortMethod(thisPlugin, xbmcplugin.SORT_METHOD_TITLE)

    hideexclusive = addon.getSetting('hideexclusivevideos').upper() == 'TRUE'
    hideflag = addon.getSetting('hidefreeexclflag').upper() == 'TRUE'
    
    soup = BeautifulSoup(''.join(doc))
    section = soup.find('section')
    if(not section):
        xbmc.log(missingelementtext%'section')
        return
    
    title = ''
    url = ''
    imageUrl = ''
        
    ahrefs = section.findAll('a')
    
    for ahref in ahrefs:
        
        url = ahref['href']
        try:
            isPayedContent = ahref['data-payed'] == 'true'
        except KeyError:
            isPayedContent = False
        
        img = ahref.find('img')
        if(img):
            imageUrl = img['src']
               
        h3 = ahref.find('h3')
        mode = 2
        if(h3 != None):
            title = ''
            parts = str(h3).decode('utf-8').split()
            for part in parts:
                title = title +' ' +part
            
            title = title.replace('<h3 class=\"card-title teaser-title\">', '').replace('</h3>', '').replace('<br />', '')
            title = HTMLParser().unescape(title)
        else:
            mode = 1
            title = language(30003)
        
        #title = title.replace('<br>', ' - ')
        
        extraInfo = {}
        if not isPayedContent:
            extraInfo['isPayedContent'] = 'False'
        else:
            extraInfo['isPayedContent'] = 'True'
            if(hideexclusive):
                #don't add exclusive videos to list
                continue
            if(not hideflag):
                title = '[EXCL] ' +title
        
        if(mode == 1):
            addDir(title, url, mode, imageUrl)
        else:
            addLink(title, url, mode, imageUrl, '', extraInfo)


def getVideoUrl(url, doc):
    xbmc.log('getVideoUrl: url=' +url)

    is_logged_in, has_schalke_tv = login()
    if not is_logged_in:
        return

    isPayedContent = xbmc.getInfoLabel( "ListItem.Property(isPayedContent)" ) == 'True'
    #payedContent requires payed Schalke TV subscription
    if(isPayedContent):
        if not has_schalke_tv:
            xbmc.log("This video requires payed Schalke TV subscription")
            xbmcgui.Dialog().ok(PLUGINNAME, language(30104), language(30105))
            return

    
    #HACK: Free content may be hosted on youtube
    if(url.startswith("https://youtu.be/")):
        videoId = url.replace("https://youtu.be/", "")
        url='plugin://plugin.video.youtube/?action=play_video&videoid=' +videoId
        listitem = xbmcgui.ListItem(path=url)
        return xbmcplugin.setResolvedUrl(thisPlugin, True, listitem)
    
    soup = BeautifulSoup(''.join(doc))
    
    section = soup.find('section')
    if(not section):
        xbmc.log(missingelementtext%'section')
        return
    
    videoContainer = soup.find('div', attrs={'class': 'video-wrapper'})
    if(not videoContainer):
        xbmc.log(missingelementtext%'video-wrapper')
        return
    
    dataoptions = videoContainer['data-options']
    if(not dataoptions):
        xbmc.log(missingelementtext%'data-options')
        return
        
    jsonResult = json.loads(dataoptions)
    jsonResultPlayerOptions = jsonResult['playerOptions']
    dataId = jsonResultPlayerOptions['data-id']
    
    playoutUrl = 'https://playout.3qsdn.com/' +dataId +'?js=true&skin=s04&data-id=' +dataId +'&container=sdnPlayer_player&preview=false&width=100%25&height=100%25'
    
    response=getUrl(playoutUrl)
    
    match_playlist=re.compile('playlist: \((.+?)\)', re.DOTALL).findall(response)
    playlist = match_playlist[0]
    
    quote_keys_regex = r'([\{\s,])(\w+)(:)'
    playlist = re.sub(quote_keys_regex, r'\1"\2"\3', playlist)

    playlist = playlist.replace("'", '"')
    playlist = playlist.replace("\\x2F", '')
    
    videourl = ''
    
    jsonPlaylist = json.loads(playlist)
    for key in jsonPlaylist:
        entry = jsonPlaylist[key]
        quality = entry['quality']
        videotype = entry['type']
        if(quality == videoquality):
            videourl = entry['src']
            
    listitem = xbmcgui.ListItem(path=videourl)
    return xbmcplugin.setResolvedUrl(thisPlugin, True, listitem)
    

def addDir(name, url, mode, iconimage):
    parameters = {'url' : url.encode('utf-8'), 'mode' : str(mode), 'name' : name.encode('utf-8')}
    u = sys.argv[0] +'?' +urllib.urlencode(parameters)
    ok = True
    listitem = xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
    listitem.setInfo(type="Video", infoLabels={"Title": name})
    ok = xbmcplugin.addDirectoryItem(thisPlugin, u, listitem, isFolder=True)
    return ok
   

def addLink(name, url, mode, iconimage, date, extraInfo):
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
    
    username = addon.getSetting('username')
    xbmc.log('Logging in with username "%s"' %username)
    password = addon.getSetting('password')
    
    if(not username or not password):
        xbmcgui.Dialog().ok(PLUGINNAME, language(30102), language(30103))
        return False, False
    
    url = 'https://schalke04.de/account/login/'
    
    cj = cookielib.CookieJar()
    br = mechanize.Browser()
    br.set_cookiejar(cj)
    br.open(url)

    for form in br.forms():
        try:
            form['email'] = username
            form['password'] = password
            br.form = form
            break
        except mechanize.ControlNotFoundError:
            pass

    br.submit()
    response = br.response().read()
    soup = BeautifulSoup(''.join(response))

    script = soup.find('script')
    if (not script):
        xbmc.log(missingelementtext % 'script')
        return False, False

    """
    script is expected to look like this:
    <script>
      dataLayer = [{
        'userID': 123456,
        'IsLoggedIn': true,
        'hasSchalkeTV': true,
        'hasSchalkeNewsletter': false,
        'isAge': 42,
        'isGender': 'mr',
        'hasHospitality': false,
        'hasPress': false,
        'hasFanclub': false,
        'hasTvAboHighlights': false,
      }];
    </script>
    """
    pattern = "'IsLoggedIn': (?P<is_logged_in>.*),\s*'hasSchalkeTV': (?P<has_schalke_tv>.*),\s*'hasSchalkeNewsletter'"
    result = re.search(pattern, script.text)

    is_logged_in = result.group('is_logged_in') == 'true'
    has_schalke_tv = result.group('has_schalke_tv') == 'true'

    xbmc.log('is_logged_in = %s' %is_logged_in)
    xbmc.log('has_schalke_tv = %s' % has_schalke_tv)

    if not is_logged_in:
        xbmc.log('login failed')
        xbmcgui.Dialog().ok(PLUGINNAME, language(30100) %username.decode('utf-8'), language(30101))
        return False, False

    return is_logged_in, has_schalke_tv


def searchMemberStatus(soup, status):
    loginSuccessful = False
    
    for textelement in soup(text=status):
        ahref = textelement.parent
        li = ahref.parent
        try:
            isChecked = li['class'] == 'checked'
            loginSuccessful = isChecked
        except KeyError:
            loginSuccessful = False
            
    return loginSuccessful


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
    


def runPlugin(url, doc):
    
    if mode==None or doc==None or len(doc)<1:
        buildVideoDir(url, doc)
       
    elif mode==1:
        buildVideoDir(url, doc)
        
    elif mode == 2:
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
