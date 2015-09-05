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
from StringIO import StringIO
import xml.etree.ElementTree as ET
import binascii
from subtitles import download_subtitles


# Setting Variablen Des Plugins
global debuging
base_url = sys.argv[0]
addon_handle = int(sys.argv[1])
args = urlparse.parse_qs(sys.argv[2][1:])
addon = xbmcaddon.Addon()
# Lade Sprach Variablen
translation = addon.getLocalizedString
debuging=""
# Es geht um Videos
xbmcplugin.setContent(addon_handle, 'movies')
baseurl="http://www.br.de"
icon = xbmc.translatePath(xbmcaddon.Addon().getAddonInfo('path')+'/icon.png').decode('utf-8')
useThumbAsFanart=addon.getSetting("useThumbAsFanart") == "true"
defaultBackground = ""
defaultThumb = ""
global bitrate
bitrate=addon.getSetting("bitrate")
global kurzvideos
kurzvideos=addon.getSetting("kurzvideos")

profile    = xbmc.translatePath( addon.getAddonInfo('profile') ).decode("utf-8")
temp       = xbmc.translatePath( os.path.join( profile, 'temp', '') ).decode("utf-8")

if xbmcvfs.exists(temp):
  shutil.rmtree(temp)
xbmcvfs.mkdirs(temp)

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
   return inhalt
   
def addDir(name, url, mode, iconimage, desc=""):
	u = sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)
	ok = True
	liz = xbmcgui.ListItem(name, iconImage=icon, thumbnailImage=iconimage)
	liz.setInfo(type="Video", infoLabels={"Title": name, "Plot": desc})
	if useThumbAsFanart:
		if not iconimage or iconimage==icon or iconimage==defaultThumb:
			iconimage = defaultBackground
		liz.setProperty("fanart_image", iconimage)
	else:
		liz.setProperty("fanart_image", defaultBackground)
	ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=True)
	return ok
  
def addLink(name, url, mode, iconimage, duration="", desc="", genre=''):
	u = sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)
	ok = True
	liz = xbmcgui.ListItem(name, iconImage=defaultThumb, thumbnailImage=iconimage)
	liz.setInfo(type="Video", infoLabels={"Title": name, "Plot": desc, "Genre": genre})
	liz.setProperty('IsPlayable', 'true')
	liz.addStreamInfo('video', { 'duration' : duration })
	liz.setProperty("fanart_image", iconimage)
	#liz.setProperty("fanart_image", defaultBackground)
	xbmcplugin.setContent(int(sys.argv[1]), 'tvshows')
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
  
  
def abisz():
  letters = [chr(i) for i in xrange(ord('a'), ord('z')+1)]
  for letter in letters:
		addDir(letter.upper(), letter.upper(), 'Buchstabe', "")
  xbmcplugin.endOfDirectory(addon_handle)
 
def geturl(url):
   cj = cookielib.CookieJar()
   opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
   req = urllib2.Request(url)
   inhalt = urllib2.urlopen(req).read()   
   return inhalt
  
def getbuchstabe(url):
    adresse=baseurl+"/mediathek/video/sendungen/index.html#letter=" + url
    inhalt = geturl(adresse)
    inhalt=ersetze(inhalt) 
    kurz_inhalt = inhalt[inhalt.find('<ul class="clearFix">')+1:]
    kurz_inhalt = kurz_inhalt[:kurz_inhalt.find('<div class="containerBreadcrumb container clearFix')]
    spl=kurz_inhalt.split('</li>')
    for i in range(1,len(spl),1):
      entry=spl[i]
      error=0
      try:
        match=re.compile('<a href="([^"]+)" title="([^"]+)"', re.DOTALL).findall(entry)
        serien_url=baseurl+match[0][0]    
        match=re.compile('<span>([^<]+)</span>', re.DOTALL).findall(entry)
        serien_title=match[0]
        match=re.compile('<img src="([^"]+)"', re.DOTALL).findall(entry)
        serien_bild=baseurl+match[0]       
        if serien_title[0].upper()==url:
          addDir(name=serien_title, url=serien_url, mode="list_serie", iconimage=serien_bild )
       
      except :
         error=1
         if debuging=="true":
           xbmc.log("URL ERROR: "+ entry )
    xbmcplugin.endOfDirectory(addon_handle,succeeded=True,updateListing=False,cacheToDisc=True)


def jsonurl(url) :   
    if debuging=="true":
       xbmc.log("Json Url"+ url)
    inhalt = geturl(url)
    inhalt=ersetze(inhalt)
    spl=inhalt.split('<article ')
    for i in range(1,len(spl),1):
      entry=spl[i].replace('\\"','"') 
      entry=entry.replace('\\/','/') 
      if "duration" in entry:
        match=re.compile('<a href="([^"]+)"', re.DOTALL).findall(entry)      
        url=baseurl+match[0]
        match=re.compile('data-src-m="([^"]+)"', re.DOTALL).findall(entry)      
        image=baseurl+match[0]
        match=re.compile('<span class="episode">([^<]+)</span>', re.DOTALL).findall(entry)      
        title=match[0]  
        match=re.compile('<time class=\"duration\" datetime=\"[^\"]+\">([0-9]+) Min.</time>', re.DOTALL).findall(entry)      
        if match:
         dauer=match[0]
        else:
          dauer=""
        match=re.compile('responsive.png\" alt=\"([^"]+)"', re.DOTALL).findall(entry)  
        if match:
         inhaltstext=match[0]
        else:
          inhaltstext=""
        if debuging=="true":
           xbmc.log("Dauer "+ dauer )          
        addLink(name=title, url=url, mode="folge", iconimage=image,duration=dauer,desc=inhaltstext)      
    if '"next":' in inhalt:
       match=re.compile('"next": "([^"]+)"', re.DOTALL).findall(inhalt) 
       next=baseurl+match[0]
       addDir(name="Next", url=next, mode="jsonurl", iconimage="" )  
    xbmcplugin.endOfDirectory(addon_handle,succeeded=True,updateListing=False,cacheToDisc=True)

def list_serie(url):
    debug(url)
    inhalt = geturl(url)
    folge1_inhalt = inhalt[inhalt.find('<section id="playerFrame" class="clearFix">')+1:]
    folge1_inhalt = folge1_inhalt[:folge1_inhalt.find('<h4 class="hidden">Weiterführende Informationen und zusätzliche Funktionen</h4>')]
    match=re.compile('<meta itemprop="thumbnail" content="([^"]+)', re.DOTALL).findall(folge1_inhalt)   
    image=match[0]
    match=re.compile('<li class="title">(.+?)</li>', re.DOTALL).findall(folge1_inhalt)   
    if match:
       title=match[0]
    else:
       title=""
    match=re.compile('<meta itemprop="description" content="([^"]+)', re.DOTALL).findall(folge1_inhalt) 
    if match:
       inhaltstext=match[0]
    else:
        inhaltstext=""
    match=re.compile('<time class=\"duration\" datetime=\"[^\"]+\">([0-9]+) Min.</time>', re.DOTALL).findall(folge1_inhalt)      
    if match:
         dauer=match[0]
    else:
         dauer=""
    addLink(name=title, url=url, mode="folge", iconimage=image,duration=dauer,desc=inhaltstext)      
    kurz_inhalt = inhalt[inhalt.find('<div class="containerInner">')+1:]
    kurz_inhalt = kurz_inhalt[:kurz_inhalt.find('<div class="sectionHead clearFix">')]
    if kurzvideos=="false":
       match=re.compile('data-filter_entire_broadcasts_url="([^"]+)"', re.DOTALL).findall(kurz_inhalt)
    else:
       match=re.compile("data-more_url='([^']+)'", re.DOTALL).findall(kurz_inhalt)      
    url2=baseurl+match[0]
    jsonurl(url2)
    
    
def folge(url):
    if debuging=="true":
      xbmc.log("Folge URL"+ url)
    inhalt = geturl(url)
    inhalt=inhalt.replace("'",'"')         
    kurz_inhalt = inhalt[inhalt.find('<div class="clearFix">')+1:]
    kurz_inhalt = kurz_inhalt[:kurz_inhalt.find('<span class="playBtn ir">Video starten</span>')]   
    match=re.compile('dataURL:"([^"]+)"', re.DOTALL).findall(kurz_inhalt)
    xmlfile=baseurl+match[0]
    xbmc.log("BR xmlfile: "+ xmlfile )
    inhalt = geturl(xmlfile) 
    inhalt=ersetze(inhalt)
    sub=re.compile('dataTimedText url="([^"]+)', re.DOTALL).findall(inhalt)
    if sub:
      subtitle= baseurl + sub[0] 
      download_subtitles(subtitle, temp)    
    inhalt = inhalt[:inhalt.find('<asset type="HDS')]  
    spl=inhalt.split('<asset ')
    if bitrate=="Select":
        quls=re.compile('<recommendedBandwidth>([^<]+)</recommendedBandwidth>', re.DOTALL).findall(inhalt)
        dialog = xbmcgui.Dialog()
        nr=dialog.select("Bitrate", quls)      
        br=quls[nr]  
        for i in range(1,len(spl),1):
          entry=spl[i]    
          if debuging=="true":
             xbmc.log("Folge entry"+ entry)
          if br in entry :
            was=entry     
    else:
      if  bitrate=="Max":
         was=spl[-1] 
      if  bitrate=="Min":
         was=spl[1] 
    if debuging=="true":         
       xbmc.log("XXX was"+ was)          
    match=re.compile('<downloadUrl\>([^<]+)</downloadUrl>', re.DOTALL).findall(was)
    if match :
      video=match[0]
    else :
       match=re.compile('<url>([^<]+)</url', re.DOTALL).findall(was)
       video=match[0]
    if debuging=="true":
      debug("XXX video: video")
      xbmc.log("XXX Subtitle:"+ temp+ "br3.srt")       
    listitem = xbmcgui.ListItem(path=video)
    if sub :
      listitem.setSubtitles([ temp+ "br3.srt"])
    xbmcplugin.setResolvedUrl(addon_handle,True, listitem)  
def playlive(url):
      listitem = xbmcgui.ListItem(path=url) 
      xbmcplugin.setResolvedUrl(addon_handle,True, listitem)  
def getdatum (starturl,sender):
   debug("XXX Start getdatum" )
   dialog = xbmcgui.Dialog()
   d = dialog.input(translation(30009), type=xbmcgui.INPUT_DATE)
   d=d.replace(' ','0')  
   d= d[6:] + "-" + d[3:5] + "-" + d[:2]
   url=baseurl+ starturl
   inhalt = geturl(url)  
   kurz_inhalt = inhalt[inhalt.find('<div class="epg epgCalendar" style="display: none">')+1:]
   kurz_inhalt = kurz_inhalt[:kurz_inhalt.find('<div class="epgNavi time" role="navigation">')] 
   match=re.compile('<a href="([^_]+)_date-' + d + '([^"]+)', re.DOTALL).findall(kurz_inhalt)   
   urlnew=baseurl+match[0][0]+'_date-' +d +match[0][1]
   inhalt = geturl(urlnew) 
   inhalt=ersetze(inhalt)  
   if sender=="BR3":
     kurz_inhalt = inhalt[inhalt.find('<div class="epgNavi time" role="navigation">')+1:]
     kurz_inhalt = kurz_inhalt[:kurz_inhalt.find('<section id="ARD-alpha" class="epgBroadcasts">')] 
   else :
     kurz_inhalt = inhalt[inhalt.find('<section id="ARD-alpha" class="epgBroadcasts">')+1:]
     kurz_inhalt = kurz_inhalt[:kurz_inhalt.find('<h3>Legende</h3>')]
   spl=kurz_inhalt.split('<dt class="clearFix">')
   for i in range(1,len(spl),1):
       entry=spl[i]
       match=re.compile('<a href="([^"]+)"', re.DOTALL).findall(entry)   
       if(match) :
         url=baseurl+match[0]
         if url!="" :
            debug("URL:" +url)
            match=re.compile('<time datetime="[^"]+">([^<]+)</time>', re.DOTALL).findall(entry) 
            time=match[0]
            debug("TIME:" +match[0]) 
            match=re.compile('<span>([^<]+)</span>', re.DOTALL).findall(entry)     
            name=match[0]
            debug("NAME:" +name)   
            match=re.compile('<li class="headline"><span>([^<]+)</span>', re.DOTALL).findall(entry)     
            addLink(name=time +" Uhr : "+ name , url=url, mode="folge", iconimage="",duration="",desc="")   
   xbmcplugin.endOfDirectory(addon_handle,succeeded=True,updateListing=False,cacheToDisc=True)         

def search(url=""):
   dialog = xbmcgui.Dialog()
   d = dialog.input(translation(30010), type=xbmcgui.INPUT_ALPHANUM)
   url=baseurl+"/mediathek/video/video/index.html?query=" + d
   getcontent_search(url)
  
def getcontent_search(url):
   debug("getcontent_search :" + url)
   inhalt=geturl(url)
   inhalt=ersetze(inhalt)
   kurz_inhalt = inhalt[inhalt.find('<span class="resultsCount">')+1:]
   kurz_inhalt = kurz_inhalt[:kurz_inhalt.find('<script type="text/javascript">')] 
   spl=kurz_inhalt.split('<div class="teaserInner clearFix">')
   for i in range(1,len(spl),1):
       entry=spl[i]
       match=re.compile('<a href="([^"]+)"', re.DOTALL).findall(entry)   
       url=baseurl+match[0]
       match=re.compile('<img src="([^"]+)"', re.DOTALL).findall(entry) 
       img=match[0]
       match=re.compile('<span class="name">([^<]+)</span>', re.DOTALL).findall(entry)
       name=match[0]
       match=re.compile('<span class="episode">([^<]+)</span>', re.DOTALL).findall(entry)
       beschreibung=match[0]
       match=re.compile('<time class="duration" datetime="[^"]+">[0-9]+ Min.</time>', re.DOTALL).findall(entry)
       dauer=match[0]
       addLink(name=name +" ( "+ beschreibung + " )", url=url, mode="folge", iconimage=img,duration=dauer,desc=beschreibung) 
   #debug(inhalt)       
   match=re.compile('<a class="sprite ir" href="([^"]+)"', re.DOTALL).findall(inhalt)       
   if match:
     addDir(name="Next", url=baseurl+match[0], mode="getcontent_search", iconimage="" )   
   xbmcplugin.endOfDirectory(addon_handle,succeeded=True,updateListing=False,cacheToDisc=True)   

   

       
params = parameters_string_to_dict(sys.argv[2])
mode = urllib.unquote_plus(params.get('mode', ''))
url = urllib.unquote_plus(params.get('url', ''))
name = urllib.unquote_plus(params.get('name', ''))
showName = urllib.unquote_plus(params.get('showName', ''))
hideShowName = urllib.unquote_plus(params.get('hideshowname', '')) == 'True'
nextPage = urllib.unquote_plus(params.get('nextpage', '')) == 'True'
einsLike = urllib.unquote_plus(params.get('einslike', '')) == 'True'    

# Haupt Menu Anzeigen      
if mode is '':
    addDir(translation(30001), translation(30001), 'A-Z', "")
    addDir(translation(30005), translation(30005), 'Datum_BR3', "")
    addDir(translation(30006), translation(30006), 'Datum_ALPHA', "")
    addLink(translation(30007) , url="http://livestreams.br.de/i/bralpha_germany@119899/master.m3u8", mode="playlive", iconimage="",duration="",desc="") 
    addLink(translation(30008), url="http://livestreams.br.de/i/bfssued_germany@119890/master.m3u8", mode="playlive", iconimage="",duration="",desc="")
    addDir(translation(30011), translation(30011), 'Search', "")
    addDir(translation(30002), translation(30002), 'Settings', "")   
    xbmcplugin.endOfDirectory(addon_handle,succeeded=True,updateListing=False,cacheToDisc=True)
else:
  # Wenn Settings ausgewählt wurde
  if mode == 'Settings':
          addon.openSettings()
  # Wenn Kategory ausgewählt wurde
  if mode == 'A-Z':
          abisz()
  if mode == 'Datum_BR3':
          getdatum("/mediathek/video/programm/index.html","BR3")
  if mode == 'Datum_ALPHA':
          getdatum("/mediathek/video/programm/index.html?tab=ARD-alpha","BRALPHA")
  if mode == 'Buchstabe':
          getbuchstabe(url)
  if mode == 'list_serie':
          list_serie(url)          
  if mode == 'jsonurl':
          jsonurl(url)   
  if mode == 'folge':
          folge(url)      
  if mode == 'playlive':
          playlive(url)     
  if mode == 'Search':
          search()             
  if mode == 'getcontent_search':
          getcontent_search(url)             
