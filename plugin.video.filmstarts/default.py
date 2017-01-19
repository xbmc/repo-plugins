#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import urlparse
import xbmcgui
import xbmcplugin
import xbmcaddon
import xbmc
import xbmcvfs
import urllib, urllib2, socket, cookielib, re, os, shutil,json
import time
from datetime import datetime
from datetime import timedelta


# Setting Variablen Des Plugins
global debuging
base_url = sys.argv[0]
addon_handle = int(sys.argv[1])
args = urlparse.parse_qs(sys.argv[2][1:])
addon = xbmcaddon.Addon()
# Lade Sprach Variablen
translation = addon.getLocalizedString


xbmcplugin.setContent(addon_handle, 'movies')

baseurl="http://www.filmstarts.de"

icon = xbmc.translatePath(xbmcaddon.Addon().getAddonInfo('path')+'/icon.png').decode('utf-8')
bitrate=addon.getSetting("bitrate")

profile    = xbmc.translatePath( addon.getAddonInfo('profile') ).decode("utf-8")
temp       = xbmc.translatePath( os.path.join( profile, 'temp', '') ).decode("utf-8")

if xbmcvfs.exists(temp):
  shutil.rmtree(temp)
xbmcvfs.mkdirs(temp)
cookie=os.path.join( temp, 'cookie.jar')
cj = cookielib.LWPCookieJar();

if xbmcvfs.exists(cookie):
    cj.load(cookie,ignore_discard=True, ignore_expires=True)                  

def debug(content):
    log(content, xbmc.LOGDEBUG)
    
def notice(content):
    log(content, xbmc.LOGNOTICE)

def log(msg, level=xbmc.LOGNOTICE):
    addon = xbmcaddon.Addon()
    addonID = addon.getAddonInfo('id')
    xbmc.log('%s: %s' % (addonID, msg), level) 
    
def ersetze(inhalt):
   inhalt=inhalt.replace('&#39;','\'')  
   inhalt=inhalt.replace('&quot;','"')    
   inhalt=inhalt.replace('&gt;','>')      
   inhalt=inhalt.replace('&amp;','&') 
   inhalt=inhalt.replace('&#287;','G') 
   inhalt=inhalt.replace('&#252;','ü') 
   inhalt=inhalt.replace('&#228;','ä')    
   inhalt=inhalt.replace('&#246;','ö') 
   inhalt=inhalt.replace('&#304;','i') 
   inhalt=inhalt.replace('&#350;','Ş') 
   inhalt=inhalt.replace('&#223;','ß') 
   return inhalt

def imagereplace(icon):   
  debug ("ICON :"+icon)
  try:
    quelle  = re.compile('(_[0-9]+_[0-9]+)/', re.DOTALL).findall(icon) [0]
  except:
        quelle="XXXXXXXXXXXXXXX"
  icon=icon.replace(quelle,"_1200_1600")
  debug( "ICON :"+icon)
  return icon
  
def addDir(name, url, mode, thump, desc="",page=1,xtype="",datum=""):
  thump=imagereplace(thump)  
  try:
     id  = re.compile('serien/(.+?)/videos/', re.DOTALL).findall(url) [0]
     icon="http://de.web.img1.acsta.net/r_1200_1600/seriesposter/"+id+"/poster_large.jpg"
  except:
     icon=thump    
  u = sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&page="+str(page)+"&xtype="+xtype+"&datum="+datum
  ok = True
  liz = xbmcgui.ListItem(name)  
  liz.setArt({ 'fanart' : thump })
  liz.setArt({ 'thumb' : thump })
  liz.setArt({ 'banner' : icon })
  liz.setArt({ 'fanart' : icon })
  liz.setInfo(type="Video", infoLabels={"Title": name, "Plot": desc})
	
  ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=True)
  return ok
  
def addLink(name, url, mode, thump, duration="", desc="", genre='',director="",bewertung=""):
  debug("URL ADDLINK :"+url)
  thump=imagereplace(thump) 
  try:
     id  = re.compile('serien/(.+?)/videos/', re.DOTALL).findall(url) [0]
     icon="http://de.web.img1.acsta.net/r_1200_1600/seriesposter/"+id+"/poster_large.jpg"
  except:
     icon=thump  
  debug( icon  )
  u = sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)
  ok = True
  liz = xbmcgui.ListItem(name,thumbnailImage=thump)
  liz.setArt({ 'fanart' : icon })
  liz.setInfo(type="Video", infoLabels={"Title": name, "Plot": desc, "Genre": genre, "Director":director,"Rating":bewertung})
  liz.setProperty('IsPlayable', 'true')
  liz.addStreamInfo('video', { 'duration' : duration })
	#xbmcplugin.setContent(int(sys.argv[1]), 'tvshows')
  ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz)
  return ok
  
def parameters_string_to_dict(parameters):
	paramDict = {}
	if parameters:
		paramPairs = parameters[1:].split("&")
		for paramsPair in paramPairs:
			paramSplits = paramsPair.split('=')
			if (len(paramSplits)) == 2:
				paramDict[paramSplits[0]] = paramSplits[1]
	return paramDict

def decodeurl(url):
    debug("URL :"+ url)   
    codestring=['3F','2D','13', '1E', '19', '1F', '20', '2A', '21', '22', '2B', '23', '24', '2C', '25', '26', 'BA', 'B1', 'B2', 'BB', 'B3', 'B4', 'BC', 'B5', 'B6', 'BD', 'B7', 'B8', 'BE', 'B9', 'BF', '30', '31', '32', '3B', '33', '34', '3C', '35', '3D', '4A', '41', '42', '4B', '43', '44', '4C', '45', '46', '4D', '47', '48', '4E', '49', '4F', 'C0', 'C1', 'C2', 'CB', 'C3', 'C4', 'CC', 'C5', 'C6', 'CD']
    decodesring=['_',':','%', '-', '.', '/', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Z', 'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z']
    ziel=""    
    for i in range(0,len(url),2):   
      debug("##")
      zeichen=url[i:i+2]
      debug("1. Zeichen :"+zeichen)
      ind=codestring.index(zeichen)
      z=decodesring[ind]
      debug("2. Zeichen :"+z)
      ziel=ziel+z  
    debug("ziel :"+ ziel)      
    return ziel

    
def geturl(url,data="x",header=""):
        global cj
        debug("Get Url: " +url)
        for cook in cj:
          debug(" Cookie :"+ str(cook))
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))        
        userAgent = "Mozilla/5.0 (Windows NT 10.0; WOW64; rv:49.0) Gecko/20100101 Firefox/49.0"
        if header=="":
          opener.addheaders = [('User-Agent', userAgent)]        
        else:
          opener.addheaders = header        
        try:
          if data!="x" :
             content=opener.open(url,data=data).read()
          else:
             content=opener.open(url).read()
        except urllib2.HTTPError as e:
             #debug( e.code )  
             cc=e.read()  
             debug("Error : " +cc)
       
        opener.close()
        cj.save(cookie,ignore_discard=True, ignore_expires=True) 
        return content

def trailer():
    addDir(translation(30008), "http://www.filmstarts.de/trailer/beliebteste.html", 'trailerpage', "")
    addDir(translation(30009), "http://www.filmstarts.de/trailer/imkino/", 'trailerpage', "")
    addDir(translation(30010), "http://www.filmstarts.de/trailer/bald/", 'trailerpage', "")
    addDir(translation(30011), "http://www.filmstarts.de/trailer/neu/", 'trailerpage', "")
    addDir(translation(30012), baseurl+"/trailer/archiv/", 'filterart', "")
    xbmcplugin.endOfDirectory(addon_handle,succeeded=True,updateListing=False,cacheToDisc=True)
def kino():
    addDir(translation(30013), "http://www.filmstarts.de/filme-imkino/kinostart/", 'kinovideos', "")
    addDir(translation(30014), "http://www.filmstarts.de/filme-imkino/neu/", 'kinovideos', "")
    addDir(translation(30015), "http://www.filmstarts.de/filme-imkino/besten-filme/user-wertung/", 'kinovideos', "")     
    addDir(translation(30016), "http://www.filmstarts.de/filme-imkino/kinderfilme/", 'kinovideos', "")             
    addDir(translation(30017), "", 'selectwoche', "")             
    addDir(translation(30018), "http://www.filmstarts.de/filme/besten/user-wertung/", 'filterkino', "")         
    addDir(translation(30019), "http://www.filmstarts.de/filme/schlechtesten/user-wertung/", 'filterkino', "")         
    addDir(translation(30020), "http://www.filmstarts.de/filme/kinderfilme/", 'filterkino', "")    
    xbmcplugin.endOfDirectory(addon_handle,succeeded=True,updateListing=False,cacheToDisc=True)    

def series():
    addDir(translation(30021), "http://www.filmstarts.de/serien/top/", 'filterserien', "")
    addDir(translation(30022), "http://www.filmstarts.de/serien/beste/", 'filterserien', "")
    addDir(translation(30023), "http://www.filmstarts.de/serien/top/populaerste/", 'serienvideos', "")  
    addDir(translation(30024), "http://www.filmstarts.de/serien/kommende-staffeln/meisterwartete/", 'serienvideos', "")
    addDir(translation(30025), "http://www.filmstarts.de/serien/neue/", 'serienvideos', "")         
    addDir(translation(30026), "http://www.filmstarts.de/serien/videos/neueste/", 'neuetrailer', "",xtype="")      
    addDir(translation(30027), "http://www.filmstarts.de/serien-archiv/", 'filterserien', "")
    xbmcplugin.endOfDirectory(addon_handle,succeeded=True,updateListing=False,cacheToDisc=True)

def news():
    addDir(translation(30028), "http://www.filmstarts.de/videos/shows/funf-sterne/", 'newsvideos', "")
    addDir(translation(30029), "http://www.filmstarts.de/videos/shows/filmstarts-fehlerteufel/", 'newsvideos', "")
    addDir(translation(30030), "http://www.filmstarts.de/trailer/interviews/", 'newsvideos', "")
    addDir(translation(30031), "http://www.filmstarts.de/videos/shows/meine-lieblings-filmszene/", 'newsvideos', "")
    xbmcplugin.endOfDirectory(addon_handle,succeeded=True,updateListing=False,cacheToDisc=True)

def newsvideos(url,page=1):
   page=int(page)    
   if page >1:
      getu=url+"?page="+str(page)
   else:
      getu=url     
   content=geturl(getu)
   debug("newsvideos URL :"+url)    
   kurz_inhalt = content[content.find('<div class="colcontent">')+1:]
   kurz_inhalt = kurz_inhalt[:kurz_inhalt.find('centeringtable')]
   elemente=kurz_inhalt.split('<div class="datablock vpadding10b">')
   for i in range(1,len(elemente),1):   
      element=elemente[i] 
      try:
        debug("1.")
        link = re.compile("href='(.+?)'", re.DOTALL).findall(element)[0]  
        title = re.compile('</strong>([^>]+?)<', re.DOTALL).findall(element)[0]       
      except:
        debug("2.")
        match = re.compile("href='(.+?)'>(.+?)</a>", re.DOTALL).findall(element)
        link=match[0][0]
        title=match[0][1]
        title=title.replace("<span class='bold'>","")
        title=title.replace("</span>","")
        title=title.replace("\n","")        
        debug("LINK :"+link)
        debug("title :"+title)
      img = re.compile("src='(.+?)'", re.DOTALL).findall(element)[0]                  
      addLink(title, baseurl+link, 'playVideo', img)
   try:
      xyx = re.compile('(<li class="navnextbtn">[^<]+<span class="acLnk)', re.DOTALL).findall(content)[0]        
      addDir(translation(30046), url, 'newsvideos', "",page=page+1)
   except:
      pass
   xbmcplugin.endOfDirectory(addon_handle,succeeded=True,updateListing=False,cacheToDisc=True)      


def selectwoche(url):
   dialog = xbmcgui.Dialog()
   d = dialog.input("Wähle die Woche des KinoProgramms", type=xbmcgui.INPUT_DATE)
   d=d.replace(' ','0')  
   d= d[6:] + "-" + d[3:5] + "-" + d[:2]
   addDir(translation(30032), "http://www.filmstarts.de/filme-vorschau/de/?week=", 'kinovideos', "",datum=d)         
   addDir(translation(30033), "http://www.filmstarts.de/filme-vorschau/usa/?week=", 'kinovideos', "",datum=d)    
   xbmcplugin.endOfDirectory(addon_handle,succeeded=True,updateListing=False,cacheToDisc=True)        
   
def filterserien():
    debug("filterart url :"+ url)
    if not "genre-" in url:
        addDir(translation(30034), url, 'genre', "",xtype="filterserien")
    if not "jahrzehnt" in url:        
      addDir(translation(30035), url, 'jahre',"")
    if not "produktionsland-" in url:
      addDir(translation(30036), url, 'laender', "")
    addDir(translation(30037), url, 'serienvideos', "")     
    xbmcplugin.endOfDirectory(addon_handle,succeeded=True,updateListing=False,cacheToDisc=True)
    
def filterkino(url):
    debug("filterart url :"+ url)
    if not "genre-" in url:
        addDir(translation(30034), url, 'genre', "",xtype="filterkino")
    if not "jahrzehnt" in url:        
      addDir(translation(30035), url, 'jahre',"")
    if not "produktionsland-" in url:
      addDir(translation(30036), url, 'laender', "")
    addDir(translation(30037), url, 'kinovideos', "")     
    xbmcplugin.endOfDirectory(addon_handle,succeeded=True,updateListing=False,cacheToDisc=True)
    
def filterart(url):
    debug("filterart url :"+ url)
    if not "genre-" in url:
        addDir(translation(30034), url, 'genre', "",xtype="filterart")
    if not "sprache-" in url:        
      addDir(translation(30038), url, 'sprache',"")
    if not "format-" in url:
      addDir(translation(30039), url, 'types', "")
    addDir(translation(30037), url, 'archivevideos', "")     
    xbmcplugin.endOfDirectory(addon_handle,succeeded=True,updateListing=False,cacheToDisc=True)
    
def sprache(url):  
   content=geturl(url)
   kurz_inhalt = content[content.find('Alle Sprachen</span>')+1:]
   kurz_inhalt = kurz_inhalt[:kurz_inhalt.find('</li></ul>')]
   match = re.compile('<span class="acLnk ([^"]+)">(.+?)</span> <span class="lighten">\((.+?)\)</span>', re.DOTALL).findall(kurz_inhalt)
   for url,name,anzahl in match:    
      url=decodeurl(url)
      addDir(name +" ( "+anzahl +" )", baseurl+url, 'filterart', "")
   xbmcplugin.endOfDirectory(addon_handle,succeeded=True,updateListing=False,cacheToDisc=True)   


def jahre(url,type="filterserien"):
   content=geturl(url)
   debug("Genre URL :"+url)    
   kurz_inhalt = content[content.find('Alle Jahre</span>')+1:]
   kurz_inhalt = kurz_inhalt[:kurz_inhalt.find('</li></ul>')]
   elemente=kurz_inhalt.split('</li><li')
   for i in range(1,len(elemente),1):   
        element=elemente[i]    
        debug("-------")
        debug(element)
        try:
          match = re.compile('<span class="acLnk ([^"]+)">([^<]+?)</span> <span class="lighten">\(([^<]+?)\)</span>', re.DOTALL).findall(element)  
          url=decodeurl(match[0][0])
          name=match[0][1]
          anzahl=match[0][2]
          debug("Decoed :"+url)
          addDir(name +" ( "+anzahl +" )", baseurl+url, type, "")
        except:
          match = re.compile('<a href="(.+?)">(.+?)</a>', re.DOTALL).findall(element)   
          url=match[0][0]
          name=match[0][1]
          addDir(name , baseurl+url, type, "")
   xbmcplugin.endOfDirectory(addon_handle,succeeded=True,updateListing=False,cacheToDisc=True)   

def neuetrailer(url,page=1):
    page=int(page)
    debug("archivevideos URL :"+url)
    if page >1:
      getu=url+"?page="+str(page)
    else:
      getu=url     
    content=geturl(getu)
    kurz_inhalt = content[content.find('<div class="tabs_main">')+1:]
    kurz_inhalt = kurz_inhalt[:kurz_inhalt.find('<div class="pager pager margin_40t">')]
    elemente=kurz_inhalt.split('<article data-block')
    for i in range(1,len(elemente),1):  
        try:    
          element=elemente[i]    
          element=element.replace('<strong>',"")
          element=element.replace('</strong>',"")
          try:
              image = re.compile("src='([^']+)'", re.DOTALL).findall(element)[0]
          except:           
              image = re.compile('"src":"([^"]+)"', re.DOTALL).findall(element)[0]        
          match = re.compile('<a href="([^"]+?)">([^<]+)</a>', re.DOTALL).findall(element)    
          urlx=match[0][0]
          text=match[0][1]
          debug("IMG :"+ image)
          if not urlx=="":
            addLink(text, baseurl+urlx, 'playVideo', image)
        except:
          pass
    if 'fr">Nächste<i class="icon-arrow-right">' in content:  
      addDir(translation(30006), url, 'neuetrailer', "",page=page+1)
    xbmcplugin.endOfDirectory(addon_handle,succeeded=True,updateListing=False,cacheToDisc=True)  
    
def laender(url,type="filterserien"):
   content=geturl(url)
   debug("Genre URL :"+url)    
   kurz_inhalt = content[content.find('Alle Länder</span>')+1:]
   kurz_inhalt = kurz_inhalt[:kurz_inhalt.find('</li></ul>')]
   elemente=kurz_inhalt.split('</li><li')
   for i in range(1,len(elemente),1):   
        element=elemente[i]  
        element=element.replace('<strong>',"")
        element=element.replace('</strong>',"")        
        debug("-------")
        debug(element)
        try:
          match = re.compile('<span class="acLnk ([^"]+)">([^<]+?)</span> <span class="lighten">\(([^<]+?)\)</span>', re.DOTALL).findall(element)  
          url=decodeurl(match[0][0])
          name=match[0][1]
          anzahl=match[0][2]
          debug("Decoed :"+url)
          addDir(name +" ( "+anzahl +" )", baseurl+url, type, "")
        except:
          match = re.compile('<a href="(.+?)">(.+?)</a>', re.DOTALL).findall(element)   
          url=match[0][0]
          name=match[0][1]
          addDir(name , baseurl+url, type, "")
   xbmcplugin.endOfDirectory(addon_handle,succeeded=True,updateListing=False,cacheToDisc=True)      
   
def types(url):
   content=geturl(url)
   kurz_inhalt = content[content.find('Alle Formate</span>')+1:]
   kurz_inhalt = kurz_inhalt[:kurz_inhalt.find('</li></ul>')]  
   if "<a href" in kurz_inhalt:
      match = re.compile('<a href="/trailer/archiv/(format-.+?)/">(.+?)</a> <span class="lighten">\((.+?)\)</span>', re.DOTALL).findall(kurz_inhalt)
      for urln,name,anzahl in match:                 
          addDir(name +" ( "+anzahl +" )", baseurl+urln, 'filterart', "")
   else:  
      match = re.compile('<span class="acLnk ([^"]+)">(.+?)</span> <span class="lighten">\((.+?)\)</span>', re.DOTALL).findall(kurz_inhalt)
      for url,name,anzahl in match:      
          debug("name : "+ name)
          debug("anzahl : "+ anzahl)
          url=decodeurl(url)
          addDir(name +" ( "+anzahl +" )", baseurl+url, 'filterart', "")
   xbmcplugin.endOfDirectory(addon_handle,succeeded=True,updateListing=False,cacheToDisc=True)   
   
def genre(url,type="filterart"):
   content=geturl(url)
   debug("Genre URL :"+url)    
   kurz_inhalt = content[content.find('Alle Genres</span>')+1:]
   kurz_inhalt = kurz_inhalt[:kurz_inhalt.find('</li></ul>')]
   elemente=kurz_inhalt.split('</li><li')
   for i in range(1,len(elemente),1):   
        element=elemente[i]  
        element=element.replace('<strong>',"")
        element=element.replace('</strong>',"")        
        debug("-------")
        debug(element)
        try:
          match = re.compile('<span class="acLnk ([^"]+)">([^<]+?)</span> <span class="lighten">\(([^<]+?)\)</span>', re.DOTALL).findall(element)  
          url=decodeurl(match[0][0])
          name=match[0][1]
          anzahl=match[0][2]
          debug("Decoed :"+url)
          addDir(name +" ( "+anzahl +" )", baseurl+url, type, "")
        except:
          match = re.compile('<a href="(.+?)">(.+?)</a>', re.DOTALL).findall(element)   
          url=match[0][0]
          name=match[0][1]
          addDir(name , baseurl+url, type, "")
   xbmcplugin.endOfDirectory(addon_handle,succeeded=True,updateListing=False,cacheToDisc=True)     
   
def archivevideos(url,page=1):   
   page=int(page)
   debug("archivevideos URL :"+url)   
   if page >1:
    getu=url+"?page="+str(page)
   else:
    getu=url     
   content=geturl(getu)   
   elemente=content.split('<article class=')
   for i in range(1,len(elemente),1):
     try:
        element=elemente[i]          
        element=element.replace('<strong>',"")
        element=element.replace('</strong>',"")
        debug("-##-")
        image = re.compile('src="(.+?)"', re.DOTALL).findall(element)[0]
        match = re.compile('<a href="(.+?)">([^<]+)</a>', re.DOTALL).findall(element)
        name=match[0][1]
        urlx=match[0][0]     
        if not "En savoir plus" in name :
            addLink(name, baseurl+urlx, 'playVideo', image)
     except:
        debug("....")
        debug(element)
   if 'fr">Nächste<i class="icon-arrow-right">' in content:
     addDir(translation(30006), url, 'archivevideos', "",page=page+1)
   xbmcplugin.endOfDirectory(addon_handle,succeeded=True,updateListing=False,cacheToDisc=True)     
   
def serienvideos(url,page=1):   
   debug("Start serienvideos")   
   page=int(page)
   debug("serienvideos URL :"+url)
   if page >1: 
    getu=url+"?page="+str(page)
   else:
    getu=url     
   content=geturl(getu)   
   elemente=content.split('<div class="data_box">')
   for i in range(1,len(elemente),1):
     try:
        element=elemente[i]       
        if not "button btn-disabled" in element:          
          debug("Element :")        
          debug (element)
          image = re.compile("src='(.+?)'", re.DOTALL).findall(element)[0]
          urlg = re.compile('href="(.+?)"', re.DOTALL).findall(element)[0]
          urlg=urlg.replace(".html","/videos/")
          name= re.compile("title='(.+?)'", re.DOTALL).findall(element)[0] 
          name=ersetze(name)
          try:
            desc= re.compile('<p class="margin_5t">([^<]+)', re.DOTALL).findall(element)[0]           
          except:
            desc=""                              
          if not "http://" in urlg:
            urlg=baseurl+urlg
          debug("URLG : "+urlg)
          addDir(name, urlg, 'tvstaffeln', image,desc=desc)                  
     except:
        debug("....")
        debug(element)
   if 'fr">Nächste<i class="icon-arrow-right">' in content:  
     addDir(translation(30006), url, 'serienvideos', "",page=page+1)
  

   xbmcplugin.endOfDirectory(addon_handle,succeeded=True,updateListing=False,cacheToDisc=True)   

   
   
def kinovideos(url,page=1,datum=""):   
   debug("Start serienvideos")   
   page=int(page)
   debug("serienvideos URL :"+url)
   if page >1:
    getu=url+"?page="+str(page)
   else:
    getu=url     
   if not datum=="":
    getu=getu+datum    
   content=geturl(getu)   
   elemente=content.split('<div class="data_box">')
   for i in range(1,len(elemente),1):
     try:
        element=elemente[i]       
        if not "button btn-disabled" in element:          
          debug("Element :")        
          debug (element)
          image = re.compile("src='(.+?)'", re.DOTALL).findall(element)[0]
          try:
            urlg = re.compile('button btn-primary " href="(.+?)"', re.DOTALL).findall(element)[0]          
          except:
            urlg = re.compile('acLnk ([^ ]+?) button btn-primary', re.DOTALL).findall(element)[0]                    
            urlg=decodeurl(urlg)
            debug("URLG ::"+urlg)
          name= re.compile("title='(.+?)'", re.DOTALL).findall(element)[0] 
          desc=re.compile("<p>([^<]+)</p>", re.DOTALL).findall(element)[0]
          
          match=re.compile('<span itemprop="genre">(.+?)</span>', re.DOTALL).findall(element)          
          genres=[]
          for namex in match:
            genres.append(namex)
          genstr=",".join(genres)
          debug("GENRES")
          debug(genstr)          
           
          try:           
            kurz_inhalt = element[element.find('<span class="film_info lighten fl">Von </span>')+1:]
            kurz_inhalt = kurz_inhalt[:kurz_inhalt.find('</div>')]          
            ressigeur= re.compile('title="(.+?)"', re.DOTALL).findall(kurz_inhalt)[0] 
          except:
             ressigeur=""
          debug("Ressigeur :"+ ressigeur)
          
          try:
            match=re.compile('<span class="acLnk ([^"]+)">[^"]+?<span class="note">(.+?)</span></span>', re.DOTALL).findall(element)
            bewertung=""
            debug("X")
            for link, note in match:
              debug("y")
              link=decodeurl(link)
              debug("Notes: "+note)
              debug("link: "+link)
              if "spiegel" in link:
               bewertung=note
            debug("bewertung :"+ bewertung)
          except:
             bewertung=""
          
          name=ersetze(name)
          if not "http://" in urlg:
            urlg=baseurl+urlg
          debug("URLG : "+urlg)
          addLink(name, urlg, 'playVideo', image,desc=desc,genre=genstr,director=ressigeur,bewertung=bewertung)                  
     except:
        debug("....")
        debug(element)
   if not datum =="":       
      try:
        Start=datetime.strptime(datum, "%Y-%m-%d")
      except TypeError:
        Start=datetime(*(time.strptime(datum, "%Y-%m-%d")[0:6]))
      Nextweek = Start + timedelta(days=7)
      Beforweek = Start - timedelta(days=7)
      nx=Nextweek.strftime("%Y-%m-%d")
      bx=Beforweek.strftime("%Y-%m-%d")
      addDir(translation(30040), url, 'kinovideos', "",datum=nx)      
      addDir(translation(30041), url, 'kinovideos', "",datum=bx)              
   if 'fr">Nächste<i class="icon-arrow-right">' in content:  
     addDir(translation(30006), url, 'kinovideos', "",page=page+1)
   xbmcplugin.endOfDirectory(addon_handle,succeeded=True,updateListing=False,cacheToDisc=True)      
   
   
def tvstaffeln(url):
    content=geturl(url)
    debug ("tvstaffeln url :"+url)
    kurz_inhalt = content[content.find('<ul class="column-1">')+1:]
    kurz_inhalt = kurz_inhalt[:kurz_inhalt.find("id='seriesseasonnumb")]    
    elemente=kurz_inhalt.split('span class="acLnk')    
    x=0
    for i in range(1,len(elemente),1):
            try:
                element=elemente[i]
                element=element.replace('<strong>',"")
                element=element.replace('</strong>',"")  
                debug(" .... TVSTAFFELN .....")                 
                name= re.compile('w-scrollto">([^<]+)', re.DOTALL).findall(element)[0]  
                name=name.replace("\n","")
                anzahl= re.compile('<span class="lighten fs11">\((.+?)\)</span>', re.DOTALL).findall(element)[0]  
                debug("name :"+name)
                debug("anzahl :"+anzahl)
                addDir(name +" ( "+anzahl +" )", url, "tvfolgen", "",xtype=name)
                x=x+1
            except:
                pass
    if x>0:
            addDir(translation(30007), url, 'tvfolgen', "",xtype="")
            xbmcplugin.endOfDirectory(addon_handle,succeeded=True,updateListing=False,cacheToDisc=True)         
    else:     
            tvfolgen(url,"") 

def tvfolgen(url,xtype):   
    debug(" Start TVfolgen")   
    debug(url)
    content=geturl(url)
    if "id='seriesseasonnumber" in content:
      elemente=content.split("id='seriesseasonnumber")
      for i in range(1,len(elemente),1):
        element=elemente[i]   
        debug("Element : ")
        debug (element)
        debug ("xtype :"+xtype)
        if xtype in element:
            elemente2=element.split("article data-bloc")
            for i in range(1,len(elemente2),1):
                element2=elemente2[i]
                element2=element2.replace('<strong>',"")
                element2=element2.replace('</strong>',"")        
                image = re.compile('"src":"(.+?)"', re.DOTALL).findall(element2)[0]
                match = re.compile('<a href="(.+?)">([^<]+)</a>', re.DOTALL).findall(element2)
                name=match[0][1]
                urlx=match[0][0]                   
                addLink(name, baseurl+urlx, 'playVideo', image)    
    else:
        kurz_inhalt = content[content.find('<div class="list-line margin_20b">')+1:]
        kurz_inhalt = kurz_inhalt[:kurz_inhalt.find('<div class="social">')]    
        elemente2=kurz_inhalt.split("article data-bloc")
        for i in range(1,len(elemente2),1):
                element2=elemente2[i]
                element2=element2.replace('<strong>',"")
                element2=element2.replace('</strong>',"")        
                image = re.compile('"src":"(.+?)"', re.DOTALL).findall(element2)[0]
                match = re.compile('<a href="(.+?)">([^<]+)</a>', re.DOTALL).findall(element2)
                name=match[0][1]
                urlx=match[0][0]                   
                addLink(name, baseurl+urlx, 'playVideo', image)    
    xbmcplugin.endOfDirectory(addon_handle,succeeded=True,updateListing=False,cacheToDisc=True)      
    
def playVideo(url):
    debug("Playvideo URL:"+url)
    content = geturl(url)
    try:
      match = re.compile('"html5PathHD":"(.*?)"', re.DOTALL).findall(content)
      ul=decodeurl(match[0])    
    except:
       ul=""
    finalUrl=""
    if ul and ul.startswith("http://"):
        finalUrl=ul
    else:
        match = re.compile('"refmedia":(.+?),', re.DOTALL).findall(content)
        media = match[0]
        match = re.compile('"relatedEntityId":(.+?),', re.DOTALL).findall(content)
        ref = match[0]
        match = re.compile('"relatedEntityType":"(.+?)"', re.DOTALL).findall(content)
        typeRef = match[0]
        content = geturl(baseurl + '/ws/AcVisiondataV4.ashx?media='+media+'&ref='+ref+'&typeref='+typeRef)
        finalUrl = ""
        match = re.compile('hd_path="(.+?)"', re.DOTALL).findall(content)
        finalUrl = match[0]
        if finalUrl.startswith("youtube:"):
            finalUrl = getYoutubeUrl(finalUrl.split(":")[1])
    if finalUrl:
        listitem = xbmcgui.ListItem(path=finalUrl)
        xbmcplugin.setResolvedUrl(addon_handle, True, listitem)
   
   
   
page=0   
params = parameters_string_to_dict(sys.argv[2])
mode = urllib.unquote_plus(params.get('mode', ''))
url = urllib.unquote_plus(params.get('url', ''))
page = urllib.unquote_plus(params.get('page', ''))
name = urllib.unquote_plus(params.get('name', ''))
xtype = urllib.unquote_plus(params.get('xtype', ''))
datum = urllib.unquote_plus(params.get('datum', ''))


def trailerpage(url,page=1) :
   page=int(page)
   debug("archivevideos URL :"+url)
   if page >1:
    getu=url+"?page="+str(page)
   else:
    getu=url     
   content=geturl(getu)  
   kurz_inhalt = content[content.find('<!-- /titlebar_01 -->')+1:]
   kurz_inhalt = kurz_inhalt[:kurz_inhalt.find('</section>')]   
   debug("--------------------------------------------")
   debug(kurz_inhalt)
   elemente=kurz_inhalt.split('article data-block')
   for i in range(1,len(elemente),1):
     try:
        element=elemente[i]
        debug("....START")
        debug(element)
        try:
            image = re.compile("src='(.+?)'", re.DOTALL).findall(element)[0]
        except:
           image = re.compile('"src":"(.+?)"', re.DOTALL).findall(element)[0]        
        urlx = re.compile('href="(.+?)"', re.DOTALL).findall(element)[0]        
        name = re.compile('<strong>(.+?)</strong>', re.DOTALL).findall(element)[0]        
        addLink(name, baseurl+urlx, 'playVideo', image)
     except:
        debug("....NOK")
        debug(element)
   if 'fr">Nächste<i class="icon-arrow-right">' in content:
     addDir(translation(30006), url, 'trailerpage', "",page=page+1)
   xbmcplugin.endOfDirectory(addon_handle,succeeded=True,updateListing=False,cacheToDisc=True)     
        
# Haupt Menu Anzeigen      
if mode is '':
    addDir(translation(30002), "", 'trailer', "")
    addDir(translation(30003), "", 'series', "")
    addDir(translation(30004), "", 'kino', "")
    addDir(translation(30005), "", 'news', "")
    #addDir(translation(30001), translation(30001), 'Settings', "")   
    xbmcplugin.endOfDirectory(addon_handle,succeeded=True,updateListing=False,cacheToDisc=True)
else:
  # Wenn Settings ausgewählt wurde
  if mode == 'Settings':
          addon.openSettings()
  # Wenn Kategory ausgewählt wurde
  if mode == 'trailer':
          trailer()
  if mode == 'filterart':
          filterart(url)
  if mode == 'genre':
          genre(url,xtype)  
  if mode == 'archivevideos':
          archivevideos(url,page)               
  if mode == 'playVideo':
          playVideo(url)                     
  if mode == 'types':
          types(url)                               
  if mode == 'sprache':
          sprache(url)
  if mode == 'trailerpage':
          trailerpage(url,page)    
  if mode == 'series':
          series()                
  if mode == 'filterserien':
          filterserien()              
  if mode == 'serienvideos':
          serienvideos(url,page)       
  if mode == 'tvstaffeln':                 
          tvstaffeln(url)
  if mode == 'tvfolgen':                 
          tvfolgen(url,xtype)         
  if mode == 'jahre':                          
          jahre(url,type="filterserien")
  if mode == 'laender':                          
          laender(url,type="filterserien")          
  if mode == 'neuetrailer':                          
          neuetrailer(url,page)          
  if mode == 'kino':                          
          kino()
  if mode == 'kinovideos':                          
          kinovideos(url,datum=datum)          
  if mode == 'selectwoche':                            
          selectwoche(url)
  if mode == 'filterkino':                            
          filterkino(url)          
  if mode == 'news':                            
          news()                   
  if mode == 'newsvideos':                            
          newsvideos(url,page)          