"""
 Copyright (c) 2010 Johan Wieslander, <johan[d0t]wieslander<(a)>gmail[d0t]com>

 Permission is hereby granted, free of charge, to any person
 obtaining a copy of this software and associated documentation
 files (the "Software"), to deal in the Software without
 restriction, including without limitation the rights to use,
 copy, modify, merge, publish, distribute, sublicense, and/or sell
 copies of the Software, and to permit persons to whom the
 Software is furnished to do so, subject to the following
 conditions:

 The above copyright notice and this permission notice shall be
 included in all copies or substantial portions of the Software.

 THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
 EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
 OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
 NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
 HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
 WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
 FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
 OTHER DEALINGS IN THE SOFTWARE.
"""
import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon
import re
import urllib2
import urllib

__settings__ = xbmcaddon.Addon(id='plugin.video.happymtb')
__language__ = __settings__.getLocalizedString

BASE_URL = "http://happymtb.org/video"
BASE_SITE_URL = "http://happymtb.org"
 
from BeautifulSoup import MinimalSoup as BeautifulSoup, SoupStrainer

def getHTML(url):
        try:
            print 'getHTML :: url = ' + url
            req = urllib2.Request(url)
            response = urllib2.urlopen(req)
            link = response.read()
            response.close()
        except urllib2.HTTPError, e:
            print "HTTP error: %d" % e.code
        except urllib2.URLError, e:
            print "Network error: %s" % e.reason.args[1]
        else:
            return link

def listPage(url):
    html = getHTML(urllib.unquote_plus(url))
    soup = BeautifulSoup(html) 
    for videobox in soup.findAll('div', 'videobox'):
        thumb = videobox.find('img', 'thumbnail')['src']
        try:
            title = videobox.find('a', 'title').contents
            title = title[0].encode("utf-8")
        except:
            title = "No title"
        RE_ID = 'jpg-s/(\d*)_\d.jpg'
        RE_ID_obj = re.compile(RE_ID, re.IGNORECASE)
        url = RE_ID_obj.sub(r"mp4/\g<1>.mp4?start=0", thumb)
        listitem=xbmcgui.ListItem(title, iconImage="DefaultFolder.png", thumbnailImage=thumb)
        listitem.setInfo(type="Video", infoLabels={ "Title": title })
        listitem.setPath(url)
        listitem.setProperty("IsPlayable", "true")
        xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=url, listitem=listitem)
    nav_page = soup.find('div', 'nav_page')
    for next in nav_page.findAll('a'):
        line = next.contents
        line = line[0].encode("utf-8")
        if 'sta' in line:
            url = next['href']
            url = BASE_SITE_URL + url
            addPosts(__language__(30000), urllib.quote_plus(url))
    return
    
def nextPage(params):
    get = params.get
    url = get("url")
    return listPage(url)

def firstPage():
    addPosts(__language__(30001), '&search=True')
    listPage(BASE_URL)
    return

def addPosts(title, url):
 listitem=xbmcgui.ListItem(title, iconImage="DefaultFolder.png")
 listitem.setInfo( type="Video", infoLabels={ "Title": title } )
 xurl = "%s?next=True&url=" % sys.argv[0]
 xurl = xurl + url
 listitem.setPath(xurl)
 folder = True
 xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=xurl, listitem=listitem, isFolder=folder)

def search_site():
    encodedSearchString = search()
    if not encodedSearchString == "":
        url = BASE_URL + '/?cid=&s=' + encodedSearchString
        listPage(url)
    else:
        firstPage()
    return

def search():
    searchString = unikeyboard("", __language__(30002))
    if searchString == "":
        xbmcgui.Dialog().ok(__language__(30003),__language__(30004))
    elif searchString:
        dialogProgress = xbmcgui.DialogProgress()
        dialogProgress.create(__language__(30003), __language__(30005) , searchString)
        #The XBMC onscreen keyboard outputs utf-8 and this need to be encoded to unicode
    encodedSearchString = urllib.quote_plus(searchString.decode("utf_8").encode("raw_unicode_escape"))
    return encodedSearchString

#From old undertexter.se plugin    
def unikeyboard(default, message):
    keyboard = xbmc.Keyboard(default, message)
    keyboard.doModal()
    if (keyboard.isConfirmed()):
        return keyboard.getText()
    else:
        return ""

#FROM plugin.video.youtube.beta  -- converts the request url passed on by xbmc to our plugin into a dict  
def getParameters(parameterString):
    commands = {}
    splitCommands = parameterString[parameterString.find('?')+1:].split('&')
    for command in splitCommands: 
        if (len(command) > 0):
            splitCommand = command.split('=')
            name = splitCommand[0]
            value = splitCommand[1]
            commands[name] = value
    return commands

if (__name__ == "__main__" ):
    if (not sys.argv[2]):
        firstPage()
    else:
        params = getParameters(sys.argv[2])
        get = params.get
        if (get("search")):
            search_site()
        if (get("next")) and not (get("search")):
            nextPage(params)

xbmcplugin.endOfDirectory(int(sys.argv[1]))