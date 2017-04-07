#   Copyright (C) 2017 Lunatixz, lordindy
#
#
# This file is part of TV Adverts.
#
# TV Adverts is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# TV Adverts is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with TV Adverts.  If not, see <http://www.gnu.org/licenses/>.

import urllib, urllib2, re, os, socket, json
import xbmcplugin, xbmcgui, xbmcaddon, xbmc
from BeautifulSoup import BeautifulSoup
from simplecache import use_cache, SimpleCache

## GLOBALS ##
baseurl='http://www.advertolog.com'
TIMEOUT = 15

# Plugin Info
ADDON_ID = 'plugin.video.adverts'
REAL_SETTINGS = xbmcaddon.Addon(id=ADDON_ID)
SETTINGS_LOC = REAL_SETTINGS.getAddonInfo('profile')
ADDON_NAME = REAL_SETTINGS.getAddonInfo('name')
ADDON_PATH = REAL_SETTINGS.getAddonInfo('path').decode('utf-8')
ADDON_VERSION = REAL_SETTINGS.getAddonInfo('version')
ICON = os.path.join(ADDON_PATH, 'icon.png')
FANART = os.path.join(ADDON_PATH, 'fanart.jpg')

# User Settings
DEBUG = REAL_SETTINGS.getSetting('Enable_Debugging') == 'true'
forceSet = REAL_SETTINGS.getSetting('force_preference') == "true"
if xbmcgui.Window(10000).getProperty('PseudoTVRunning') == "True":
    forceSet = True
    
socket.setdefaulttimeout(TIMEOUT)

def log(msg, level=xbmc.LOGDEBUG):
    msg = stringify(msg[:1000])
    if DEBUG == False and level == xbmc.LOGDEBUG:
        return
    if level == xbmc.LOGERROR:
        msg += ' ,' + traceback.format_exc()
    xbmc.log(ADDON_ID + '-' + ADDON_VERSION + '-' + msg, level)

def ascii(string):
    if isinstance(string, basestring):
        if isinstance(string, unicode):
           string = string.encode('ascii', 'ignore')
    return string

def uni(string):
    if isinstance(string, basestring):
        if isinstance(string, unicode):
           string = string.encode('utf-8', 'ignore' )
        else:
           string = ascii(string)
    return string

def stringify(string):
    if isinstance(string, list):
        string = stringify(string[0])
    elif isinstance(string, (int, float, long, complex, bool)):
        string = str(string)
    elif isinstance(string, (str, unicode)):
        string = uni(string)
    elif not isinstance(string, (str, unicode)):
        string = ascii(string)
    if isinstance(string, basestring):
        return string
    return ''

def cleanString(string):
    newstr = uni(string)
    newstr = newstr.replace('&', '&amp;')
    newstr = newstr.replace('>', '&gt;')
    newstr = newstr.replace('<', '&lt;')
    newstr = newstr.replace('"', '&quot;')
    return uni(newstr)

def uncleanString(string):
    newstr = uni(string)
    newstr = newstr.replace('&amp;', '&')
    newstr = newstr.replace('&gt;', '>')
    newstr = newstr.replace('&lt;', '<')
    newstr = newstr.replace('&quot;', '"')
    return uni(newstr)
    
def replaceXmlEntities(link):
    entities = (
        ("%3A",":"),("%2F","/"),("%3D","="),("%3F","?"),("%26","&"),("%22","\""),("%7B","{"),("%7D",")"),("%2C",","),("%24","$"),("%23","#"),("%40","@")
      );
    for entity in entities:
       link = link.replace(entity[0],entity[1]);
    return link;
                 
def get_params():
    param=[]
    if len(sys.argv[2])>=2:
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
        
        
class Adverts():
    def __init__(self):
        self.cache = SimpleCache()

        
    # sites not updated regularly, no need to burden site. Cache for 14days
    @use_cache(14)
    def openURL(self, url):
        req = urllib2.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
        response = urllib2.urlopen(req).read()
        return response

        
    def CATEGORIES(self):
        self.addDir('Countries','http://www.advertolog.com/countries/',3)
        self.addDir('Brands','http://www.advertolog.com/brands/',4)
        self.addDir('Years','http://www.advertolog.com/countries/',8)         
        self.addDir('Business Sectors','http://www.advertolog.com/business-sectors/',6)
        # self.addDir('Awards','http://www.advertolog.com/festivals-awards/',6)

            
    def BRANDORCOUNTRYPAGE(self, url):
        link = self.openURL(url)
        link=link.decode('utf-8')
        soup = BeautifulSoup(link,convertEntities=BeautifulSoup.HTML_ENTITIES)
        catlink=re.compile('<a href="(.+?)" >TV & Cinema</a>').findall(link)
        if catlink:
            url=baseurl+catlink[0]
            link = self.openURL(url)
            soup = BeautifulSoup(link)

        #find the adverts, if any                    
        if soup.find('ul', "col-media-list"):
            adverts=soup.find('ul', "col-media-list").findAll('li')
            for ad in adverts:
                if ad.find(text="  TV & Cinema"):
                    name=ad.a.img["alt"].encode('UTF-8')
                    adurl=ad.a["href"]
                    thumbnail=ad.a.img["src"]
                    if forceSet == True:
                        self.VIDEOLINKS(baseurl+adurl,name,len(adverts))
                    else:
                        self.addDir(name,baseurl+adurl,2,thumbnail)
                    
                    
    def BRANDORCOUNTRYYEAR(self, url):
        link = self.openURL(url)
        link=link.decode('utf-8')
        soup = BeautifulSoup(link,convertEntities=BeautifulSoup.HTML_ENTITIES)
        catlink=re.compile('<a href="(.+?)" >TV & Cinema</a>').findall(link)
        if catlink:
            url=baseurl+catlink[0]
            link = self.openURL(url)
            soup = BeautifulSoup(link)
                
        # find the year links, if any
        yearlink=soup.find(text='Year:')
        if yearlink:
            yearlink=soup.find(text='Year:').findNext('div').findAll('a')
            years=[]
            for links in yearlink:
                temp=re.compile('<a href="(.+?)">(.+?)</a>').findall(str(links))
                years.append(temp[0])
            for yearurl, name in years:
                self.addDir(name,baseurl+yearurl,1)
                
        #Get the "Next Page" link, if any
        if soup.find(text=re.compile("Next \xbb\xbb")):
            if soup.find(text=re.compile("Next \xbb\xbb")).findPrevious('span').findAll('a'):
                nextpage=soup.find(text=re.compile("Next \xbb\xbb")).findPrevious('span').findAll('a')
                nextpage=re.compile('\[<a href="(.+?)">Next').findall(str(nextpage))
                nextpage=baseurl+nextpage[0]
                self.addDir("''Next Page >>",nextpage,1)

                    
    def VIDEOLINKS(self, url, name, total=1):
        link = self.openURL(url)
        soup = BeautifulSoup(link)
        found = False
        #GET THE VIDEO LINKS FROM THE PAGE, IF ANY
        #get the image
        image=re.compile('meta property="og:image" content="(.+?)" />').findall(link)
        if image:
            image[0]=replaceXmlEntities(image[0])
        else:
            image=''
       
       #get the default video link (most are hidden due to subscription, but the low res video link is hidden in the header tag    
        vid=re.compile('meta property="og:video" content="(.+?)" />').findall(link)
        if vid:
            vid[0]=replaceXmlEntities(vid[0])
            vid[0]=re.sub('http.*?clip":{"url":','/',vid[0])
            vid[0]=re.search('h.*?.mp4', vid[0]).group()
            vid = vid[0]

        #get alternate high res links if any
        vids=soup.find('ul',"resolutions")
        if vids:
            vids=soup.find('ul',"resolutions").findAll('a')
            if vids:
                vids=soup.find('ul',"resolutions").findAll('a')
                for url in vids:     
                    if forceSet == True:
                        if url.string.lower() == REAL_SETTINGS.getSetting('limit_preferred_resolution').lower():
                            found = True
                            self.addLink(name,url['name'],9,image[0],total)
                            return
                    else:
                        self.addLink(url.string,url['name'],9,image[0],total)
                                    
        if not vids: # attempt to find stray low quality video
            if len(re.compile("url:'(.+?).mp4',").findall(link)) > 0:
                vid=((re.compile("url:'(.+?).mp4',").findall(link))[0]) + '.mp4'
                
                if len(vid) > 0:
                    self.addLink('360p',vid,9,image[0])
                else:
                    self.addLink('SWF video unavailable','',9,image[0])
                return
        self.addLink('video unavailable','',9,image[0])
        
        
    def LISTCOUNTRIES(self, url, year=False):
        link = self.openURL(url)
        countries=re.compile('<a href="/countries/(.+?)">(.+?)</a>').findall(link)
        for url,country in countries:         
            if year: 
                if forceSet == True:
                    if country.lower() == REAL_SETTINGS.getSetting('limit_preferred_region').lower():
                        self.BRANDORCOUNTRYPAGE('http://www.advertolog.com/countries/'+url)
                        break
                else:
                    self.addDir(country,'http://www.advertolog.com/countries/'+url,7)
            else:
                if forceSet == True:
                    if country.lower() == REAL_SETTINGS.getSetting('limit_preferred_region').lower():
                        self.BRANDORCOUNTRYPAGE('http://www.advertolog.com/countries/'+url)
                        break
                else:
                    self.addDir(country,'http://www.advertolog.com/countries/'+url,1)
                
                    
    def LISTBRANDLETTERS(self, url):
        link = self.openURL(url)
        match=re.compile('<h3 style="font-weight:bold; font-size:24px;"><a href=".+?" style="text-decoration:none">(.+?)</a></h3>').findall(link)
        #Get the brand letters
        letters=re.compile('<h3 style="font-weight:bold; font-size:24px;"><a href=".+?" style="text-decoration:none">(.+?)</a></h3>').findall(link)
        letters=map(lambda x: x.lower(), letters)
        for letter in letters:
            self.addDir(letter.upper(),'http://www.advertolog.com/brands/letter-'+letter+'/',5)
           
               
    def LISTBRANDS(self, url):
        link = self.openURL(url)
        soup = BeautifulSoup(link,convertEntities=BeautifulSoup.HTML_ENTITIES)
        brands=re.compile('<a href="(.+?)" id="CompanyListingTitle_.+?">(.+?)</a>').findall(link)
        for url, name in brands:
            self.addDir(name,baseurl+url,1)
        #Get the "Next Page" link, if any
        if soup.find(text=re.compile("Next ")):
            if soup.find(text=re.compile("Next ")).findPrevious('span').findAll('a'):
                nextpage=soup.find(text=re.compile("Next ")).findPrevious('span').findAll('a')
                nextpage=re.compile('\[<a href="(.+?)">Next ').findall(str(nextpage))
                nextpage=baseurl+nextpage[0]
                self.addDir("''Next Page >>",nextpage,5)

                    
    def LISTSECTORS(self, url):
        link = self.openURL(url)
        soup = BeautifulSoup(link,convertEntities=BeautifulSoup.HTML_ENTITIES)
        sectors=re.compile('<a href="(.+?)/">\n        (.+?)</a>').findall(str(soup))
        sectors.sort()
        for url, name in sectors:
            self.addDir(name,baseurl+url,1)


    def LinkPlay(self, name, url):
        listitem = xbmcgui.ListItem(name, path=url)
        xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, listitem)

        
    def addLink(self, name, u, mode, thumb=ICON, total=0):
        name = uncleanString(name)
        log('addLink, name = ' + name)
        liz=xbmcgui.ListItem(name)
        liz.setProperty('IsPlayable', 'true')
        liz.setArt({'thumb':thumb,'fanart':FANART})
        liz.setInfo( type="Video", infoLabels={"label":name,"title":name} )
        u=sys.argv[0]+"?url="+urllib.quote_plus(u)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)
        xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,totalItems=total)


    def addDir(self, name, u, mode, thumb=ICON):
        name = uncleanString(name)
        log('addDir, name = ' + name)
        liz=xbmcgui.ListItem(name)
        liz.setProperty('IsPlayable', 'false')
        liz.setInfo(type="Video", infoLabels={"label":name,"title":name} )
        liz.setArt({'thumb':thumb,'fanart':FANART})
        u=sys.argv[0]+"?url="+urllib.quote_plus(u)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)
        xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)

        
params=get_params()
url=None
name=None
mode=None

try:
    url=urllib.unquote_plus(params["url"])
except:
    pass
try:
    name=urllib.unquote_plus(params["name"])
except:
    pass
try:
    mode=int(params["mode"])
except:
    pass

log("Mode: "+str(mode))
log("URL : "+str(url))
log("Name: "+str(name))

if mode==None or url==None or len(url)<1:
    Adverts().CATEGORIES()  
elif mode==1:
    Adverts().BRANDORCOUNTRYPAGE(url)    
elif mode==2:
    Adverts().VIDEOLINKS(url,name)
elif mode==3:
    Adverts().LISTCOUNTRIES(url)         
elif mode==4:
    Adverts().LISTBRANDLETTERS(url)
elif mode==5:
    Adverts().LISTBRANDS(url)
elif mode==6:
    Adverts().LISTSECTORS(url)   
elif mode==7:
    Adverts().BRANDORCOUNTRYYEAR(url) 
elif mode==8:
    Adverts().LISTCOUNTRIES(url,True)  
elif mode == 9: 
    Adverts().LinkPlay(name, url)
        
xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_LABEL )
xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_NONE )
xbmcplugin.endOfDirectory(int(sys.argv[1]), cacheToDisc=True)