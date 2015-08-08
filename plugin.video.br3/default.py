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
# Cookies und Url Parser Laden
cj = cookielib.CookieJar()
opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
# Es geht um Videos
xbmcplugin.setContent(addon_handle, 'movies')
baseurl="http://www.br.de"
icon = xbmc.translatePath(xbmcaddon.Addon().getAddonInfo('path')+'/icon.png').decode('utf-8')
useThumbAsFanart=addon.getSetting("useThumbAsFanart") == "true"
defaultBackground = ""
defaultThumb = ""
global debuging
debuging=addon.getSetting("debug")
global bitrate
bitrate=addon.getSetting("bitrate")
profile    = xbmc.translatePath( addon.getAddonInfo('profile') ).decode("utf-8")
temp       = xbmc.translatePath( os.path.join( profile, 'temp', '') ).decode("utf-8")

if xbmcvfs.exists(temp):
  shutil.rmtree(temp)
xbmcvfs.mkdirs(temp)


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
	if useThumbAsFanart:
		if not iconimage or iconimage==icon or iconimage==defaultThumb:
			iconimage = defaultBackground
		liz.setProperty("fanart_image", iconimage)
	else:
		liz.setProperty("fanart_image", defaultBackground)
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

def getbuchstabe(url):
    adresse=baseurl+"/mediathek/video/sendungen/index.html#letter=" + url
    req = urllib2.Request(adresse)
    inhalt = urllib2.urlopen(req).read()
    inhalt=inhalt.replace('&quot;','"')  
    inhalt=inhalt.replace('&#39;','\'')  
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
    req2 = urllib2.Request(url)
    inhalt = urllib2.urlopen(req2).read()
    inhalt=inhalt.replace('&quot;','"')  
    inhalt=inhalt.replace('&#39;','\'')  
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
    req = urllib2.Request(url)
    inhalt = urllib2.urlopen(req).read()
    kurz_inhalt = inhalt[inhalt.find('<div class="containerInner">')+1:]
    kurz_inhalt = kurz_inhalt[:kurz_inhalt.find('<div class="sectionHead clearFix">')]
    match=re.compile('data-filter_entire_broadcasts_url="([^"]+)"', re.DOTALL).findall(kurz_inhalt)
    url2=baseurl+match[0]
    jsonurl(url2)
    
def folge(url):
    req = urllib2.Request(url)
    if debuging=="true":
      xbmc.log("Folge URL"+ url)
    inhalt = urllib2.urlopen(req).read()
    inhalt=inhalt.replace("'",'"')         
    kurz_inhalt = inhalt[inhalt.find('<div class="clearFix">')+1:]
    kurz_inhalt = kurz_inhalt[:kurz_inhalt.find('<span class="playBtn ir">Video starten</span>')]   
    match=re.compile('dataURL:"([^"]+)"', re.DOTALL).findall(kurz_inhalt)
    xmlfile=baseurl+match[0]
    xbmc.log("BR xmlfile: "+ xmlfile )
    req = urllib2.Request(xmlfile)
    inhalt = urllib2.urlopen(req).read() 
    inhalt=inhalt.replace('&gt;','>')      
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
    video=match[0]
    if debuging=="true":
      xbmc.log("XXX Subtitle:"+ temp+ "br3.srt")       
    listitem = xbmcgui.ListItem(path=video)
    if sub :
      listitem.setSubtitles([ temp+ "br3.srt"])
    xbmcplugin.setResolvedUrl(addon_handle,True, listitem)      
    
    
       
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
    addDir(translation(30002), translation(30002), 'Settings', "")   
    xbmcplugin.endOfDirectory(addon_handle,succeeded=True,updateListing=False,cacheToDisc=True)
else:
  # Wenn Settings ausgewählt wurde
  if mode == 'Settings':
          addon.openSettings()
  # Wenn Kategory ausgewählt wurde
  if mode == 'A-Z':
          abisz()
  if mode == 'Buchstabe':
          getbuchstabe(url)
  if mode == 'list_serie':
          list_serie(url)          
  if mode == 'jsonurl':
          jsonurl(url)   
  if mode == 'folge':
          folge(url)             
