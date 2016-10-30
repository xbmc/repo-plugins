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

addon_handle = int(sys.argv[1])
addon = xbmcaddon.Addon()
translation = addon.getLocalizedString
icon = xbmc.translatePath(xbmcaddon.Addon().getAddonInfo('path')+'/icon.png').decode('utf-8')
global quality
global qualityhtml
quality=addon.getSetting("quality")
qualityhtml=addon.getSetting("qualityhtml")
username=addon.getSetting("user")
password=addon.getSetting("pass")
global movies
movies=addon.getSetting("movies")



profile    = xbmc.translatePath( addon.getAddonInfo('profile') ).decode("utf-8")
temp       = xbmc.translatePath( os.path.join( profile, 'temp', '') ).decode("utf-8")
if not xbmcvfs.exists(temp):  
  xbmcvfs.mkdirs(temp)




def debug(content):
    log(content, xbmc.LOGDEBUG)
    
def notice(content):
    log(content, xbmc.LOGNOTICE)

def log(msg, level=xbmc.LOGNOTICE):
    addon = xbmcaddon.Addon()
    addonID = addon.getAddonInfo('id')
    xbmc.log('%s: %s' % (addonID, msg), level) 

    
cookie=temp+"/cookie.jar"
cj = cookielib.LWPCookieJar();


if xbmcvfs.exists(cookie):
   cj.load(cookie,ignore_discard=True, ignore_expires=True)


opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
baseurl="https://www.anime-on-demand.de"
    
    
    
    
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
	ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=True)
	return ok   
  
  
def addLink(name, url, mode, iconimage, duration="", desc="", genre='',csrftoken="",type=""):
  debug("addlink :" + url)  
  u = sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&csrftoken="+csrftoken+"&type="+type
  ok = True
  liz = xbmcgui.ListItem(name, thumbnailImage=iconimage)
  liz.setInfo(type="Video", infoLabels={"Title": name, "Plot": desc, "Genre": genre})
  liz.setProperty('IsPlayable', 'true')
  liz.addStreamInfo('video', { 'duration' : duration })
  liz.setProperty("fanart_image", iconimage)
  #liz.setProperty("fanart_image", defaultBackground)
  xbmcplugin.setContent(int(sys.argv[1]), 'tvshows')
  ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz)
  return ok
  
def alles(url=""):
   debug ("###Start ALL" + url)   
   content=geturl(url)   
   kurz_inhalt = content[content.find('<div class="three-box-container">')+1:]
   kurz_inhalt = kurz_inhalt[:kurz_inhalt.find('<div class="l-contentcontainer l-navigationscontainer">')]
   spl=kurz_inhalt.split('<div class="three-box animebox">')
   for i in range(1,len(spl),1):
      entry=spl[i]
      if not "zum Film" in entry or movies=="true"    :  
        match=re.compile('<h3 class="animebox-title">([^<]+)</h3>', re.DOTALL).findall(entry)
        title=match[0]
        match=re.compile('<img src="([^"]+)"', re.DOTALL).findall(entry)
        img=baseurl+match[0]
        match=re.compile('<a href="([^"]+)">', re.DOTALL).findall(entry)
        link=baseurl+match[0]
        match=re.compile('<p class="animebox-shorttext">.+</p>', re.DOTALL).findall(entry)
        desc=match[0]
        desc=desc.replace('<p class="episodebox-shorttext">','').replace('<p class="animebox-shorttext">','')
        desc=desc.replace("</p>",'')   
        addDir(name=ersetze(title), url=link, mode="Serie", iconimage=img, desc=desc)
   xbmcplugin.endOfDirectory(addon_handle,succeeded=True,updateListing=False,cacheToDisc=True)
   
def login(url):
    global opener
    global cj
    global username
    global password
    userAgent = "Mozilla/5.0 (Windows NT 6.2; WOW64; rv:23.0) Gecko/20100101 Firefox/23.0"
    opener.addheaders = [('User-Agent', userAgent)]
    content=opener.open(baseurl+"/users/sign_in").read()
    match = re.compile('ame="authenticity_token" value="([^"]+)"', re.DOTALL).findall(content)
    token1=match[0]
    debug ("USERNAME: "+ username)
    values = {'user[login]' : username,
        'user[password]' : password,
        'user[remember_me]' : '1',
        'commit' : 'Einloggen' ,
        'authenticity_token' : token1
    }
    data = urllib.urlencode(values)
    content=opener.open(baseurl+"/users/sign_in",data).read()
    content=opener.open(url).read()
    return content
   
    
def Serie(url):
  global opener
  global cj
  global username
  global password
  debug ("#############################################################################################")
  debug ("URL : " + url)
  userAgent = "Mozilla/5.0 (Windows NT 6.2; WOW64; rv:23.0) Gecko/20100101 Firefox/23.0"
  opener.addheaders = [('User-Agent', userAgent)]
  content=opener.open(url).read()  
  debug("COntent :")
  debug("-------------------------------")
  debug(content)
  if not '<a href="/users/edit">Benutzerkonto</a>' in content :    
    content=login(url)
  cj.save(cookie,ignore_discard=True, ignore_expires=True)
  match = re.compile('<meta name="csrf-token" content="([^"]+)"', re.DOTALL).findall(content)
  csrftoken=match[0]
  kurz_inhalt = content[content.find('<div class="three-box-container">')+1:]                                      
  kurz_inhalt = kurz_inhalt[:kurz_inhalt.find('<div class="l-contentcontainer l-navigationscontainer">')]
  if '<div class="three-box episodebox flip-container">' in kurz_inhalt:
     spl=kurz_inhalt.split('<div class="three-box episodebox flip-container">')
  else:
     spl=kurz_inhalt.split('<div class="l-off-canvas-container">')
  debug("------------------------------")
  debug ("Kurzinhalt:")
  debug (kurz_inhalt)  
  for i in range(1,len(spl),1):
    try:
      entry=spl[i]                        
      debug("------------------------------")
      debug("Entry:")
      debug(entry)          
      debug ("-------------------------------")     
      match=re.compile('src="([^"]+)"', re.DOTALL).findall(entry)
      img=baseurl+match[0]
      ret=flashvideo(entry,img,csrftoken)
      if ret==1:
        html5video(entry,img,csrftoken)
    except :
       error=1
  debug ("#############################################################################")
  
  xbmcplugin.endOfDirectory(addon_handle,succeeded=True,updateListing=False,cacheToDisc=True)  
def html5video(entry,img,csrftoken):     
    error=0
    debug("Start Flashvideo")
    try:
      match=re.compile('title="([^"]+)"', re.DOTALL).findall(entry)
      title=match[0]      
      if '<p class="episodebox-shorttext">' in entry:
           match=re.compile('<p class="episodebox-shorttext">(.+)</p>', re.DOTALL).findall(entry)
      else:
           match=re.compile('<div itemprop="description">(.+)</p>', re.DOTALL).findall(entry)
      desc=match[0]    
      desc=desc.replace("<br />","") 
      desc=desc.replace("<p>","") 
      debug("csrftoken : "+csrftoken)
      
      match=re.compile('title="([^"]+)" data-playlist="([^"]+)"', re.DOTALL).findall(entry)
      for type,link in match:
        title2=title + "( "+ type.replace("starten","").replace("Japanischen Stream mit Untertiteln","OmU").replace("Deutschen Stream","Syncro") +" )"
        debug("Link: "+ link)      
        addLink(name=ersetze(title2), url=baseurl+link, mode="Folge", iconimage=img, desc=desc,csrftoken=csrftoken,type="html5")      
    except :
       error=1
    return error
       
def flashvideo(entry,img,csrftoken):    
    error=0 
    debug("Start Flashvideo")
    try:
      match=re.compile('title="([^"]+)" data-stream="([^"]+)" data-dialog-header="([^"]+)"', re.DOTALL).findall(entry)
      title=match[0][2]        
      debug("Title :"+ title)       
      found=0      
      linka=""
      linko=""
      for qua,linka,name in match:        
        titl=quality+ "-Stream"         
        if titl.lower() in qua.lower():
            link=linka
            found=1
        else:
             linko=linka
      if found==0:         
         link=linko
      if link :
         link=baseurl+link
         debug("Link: "+ link)
         if '<p class="episodebox-shorttext">' in entry:
           match=re.compile('<p class="episodebox-shorttext">(.+)</p>', re.DOTALL).findall(entry)
         else:
           match=re.compile('<div itemprop="description">(.+)</p>', re.DOTALL).findall(entry)
         desc=match[0]    
         desc=desc.replace("<br />","") 
         desc=desc.replace("<p>","") 
         debug("csrftoken : "+csrftoken)
         addLink(name=ersetze(title), url=link, mode="Folge", iconimage=img, desc=desc,csrftoken=csrftoken,type="flash")      
    except :
       error=1
    return error

def Folge(url,csrftoken,type):
  global opener
  global cj
  global username
  global password
  try :        
    opener.addheaders = [('X-CSRF-Token', csrftoken),
                     ('X-Requested-With', "XMLHttpRequest"),
                     ('Accept', "application/json, text/javascript, */*; q=0.01")]      
    content=opener.open(url).read()    
    debug("Content:")
    debug("--------------------:")
    debug(content)
    debug("----------------:")
    if type=="html5":
      match = re.compile('"file":"([^"]+)"', re.DOTALL).findall(content)
      stream=match[1].replace("\\u0026","&")
      debug("1")
      debug("stream :" + stream)
      content2=opener.open(stream).read()   
      debug("----------------")      
      debug(content2)      
      debug("----------------")      
      spl=content2.split('#EXT-X-STREAM-INF')
      if qualityhtml=="MAX":
        element=spl[1]
        debug("Element: "+element)
        match = re.compile('chunklist(.+)', re.DOTALL).findall(element)
        qual="chunklist"+match[0]
        debug("Qal : "+qual)
        liste=stream.split('/')
        laenge=len(liste)
        pfadt=liste[0:-1]
        s="/"
        pfad=s.join(pfadt)
        debug("Pfad : "+ pfad)
        stream=pfad+"/"+qual[0:-1]    
      if qualityhtml=="MIN":
        element=spl[-1]
        debug("Element: "+element)
        match = re.compile('chunklist(.+)', re.DOTALL).findall(element)
        qual="chunklist"+match[0]
        debug("Qal : "+qual)
        liste=stream.split('/')
        laenge=len(liste)
        pfadt=liste[0:-1]
        s="/"
        pfad=s.join(pfadt)
        debug("Pfad : "+ pfad)
        stream=pfad+"/"+qual[0:-1]      
      if qualityhtml=="Select":
        file=[]
        namen=[]
        liste=stream.split('/')
        laenge=len(liste)
        pfadt=liste[0:-1]
        s="/"
        pfad=s.join(pfadt)
        for i in range(1,len(spl),1):
          element=spl[i]
          match = re.compile('BANDWIDTH=(.+?),RESOLUTION=(.+?)chunklist', re.DOTALL).findall(element)
          band=match[0][0]
          res=match[0][1]
          match = re.compile('chunklist(.+)', re.DOTALL).findall(element)
          qual="chunklist"+match[0]
          file.append(qual)
          namen.append(res + "( "+ str(int(band)/1024) +" kb/s )")
        dialog = xbmcgui.Dialog()
        nr=dialog.select("Qualität", namen) 
        files=file[nr]
        debug("Files :"+files)
        stream=pfad+"/"+files[0:-1]
        debug("##AV ##"+ stream)        
      debug("----------------")
      listitem = xbmcgui.ListItem (path=stream)
    if type=="flash":
      match = re.compile('"streamurl":"([^"]+)"', re.DOTALL).findall(content)
      stream=match[0]  
      match = re.compile('(.+)mp4:(.+)', re.DOTALL).findall(stream)  
      path="mp4:"+match[0][1]
      server=match[0][0] 
      listitem = xbmcgui.ListItem (path=server +"swfUrl=https://ssl.p.jwpcdn.com/6/12/jwplayer.flash.swf playpath="+path+" token=83nqamH3#i3j app=aodrelaunch/ swfVfy=true")
    
    xbmcplugin.setResolvedUrl(addon_handle,True, listitem)    
    debug(content)
  except IOError, e:          
        if e.code == 401:
            dialog = xbmcgui.Dialog()
            dialog.ok("Login",translation(30110))
       

   
def geturl(url):   
   userAgent = "Mozilla/5.0 (Windows NT 6.2; WOW64; rv:23.0) Gecko/20100101 Firefox/23.0"
   opener.addheaders = [('User-Agent', userAgent)]
   req = urllib2.Request(url)
   inhalt = urllib2.urlopen(req).read()   
   cj.save(cookie,ignore_discard=True, ignore_expires=True)
   return inhalt   
  
def parameters_string_to_dict(parameters):
	paramDict = {}
	if parameters:
		paramPairs = parameters[1:].split("&")
		for paramsPair in paramPairs:
			paramSplits = paramsPair.split('=')
			if (len(paramSplits)) == 2:
				paramDict[paramSplits[0]] = paramSplits[1]
	return paramDict


def category() :
  global opener
  global cj
  global username
  global password
  url=baseurl+"/animes"
  userAgent = "Mozilla/5.0 (Windows NT 6.2; WOW64; rv:23.0) Gecko/20100101 Firefox/23.0"
  opener.addheaders = [('User-Agent', userAgent)]
  content=opener.open(url).read()  
  if not '<a href="/users/edit">Benutzerkonto</a>' in content :    
    content=login(url)
  cj.save(cookie,ignore_discard=True, ignore_expires=True)

  kurz_inhalt = content[content.find('<ul class="inline-block-list" style="display: block; text-align: center;">')+1:]                                      
  kurz_inhalt = kurz_inhalt[:kurz_inhalt.find('</ul>')]  
  match=re.compile('<a href="([^"]+)">([^<]+)</a>', re.DOTALL).findall(kurz_inhalt)
  for link,name in match:
      addDir(name=ersetze(name), url=baseurl+link, mode="catall",iconimage="", desc="")
  xbmcplugin.endOfDirectory(addon_handle,succeeded=True,updateListing=False,cacheToDisc=True)
 
def language() :
  global opener
  global cj
  global username
  global password
  url=baseurl+"/animes"
  userAgent = "Mozilla/5.0 (Windows NT 6.2; WOW64; rv:23.0) Gecko/20100101 Firefox/23.0"
  opener.addheaders = [('User-Agent', userAgent)]
  content=opener.open(url).read()  
  if not '<a href="/users/edit">Benutzerkonto</a>' in content :    
    content=login(url)
  cj.save(cookie,ignore_discard=True, ignore_expires=True)

  kurz_inhalt = content[content.find('<ul class="inline-block-list" style="display: block; text-align: center;">')+1:]     
  kurz_inhalt = kurz_inhalt[kurz_inhalt.find('<ul class="inline-block-list" style="display: block; text-align: center;">')+1:]                                      
  kurz_inhalt = kurz_inhalt[:kurz_inhalt.find('</ul>')]  
  match=re.compile('<a href="([^"]+)">([^<]+)</a>', re.DOTALL).findall(kurz_inhalt)
  for link,name in match:
     if not "HTML5" in name:
      addDir(name=ersetze(name), url=baseurl+link, mode="catall",iconimage="", desc="")
  xbmcplugin.endOfDirectory(addon_handle,succeeded=True,updateListing=False,cacheToDisc=True)
 
params = parameters_string_to_dict(sys.argv[2])  
mode = urllib.unquote_plus(params.get('mode', ''))
url = urllib.unquote_plus(params.get('url', ''))
type = urllib.unquote_plus(params.get('type', ''))
csrftoken = urllib.unquote_plus(params.get('csrftoken', ''))


def abisz():
  addDir("0-9", baseurl+"/animes/begins_with/0-9", 'catall', "")
  letters = [chr(i) for i in xrange(ord('a'), ord('z')+1)]
  for letter in letters:
		addDir(letter.upper(), baseurl+"/animes/begins_with/"+letter.upper(), 'catall', "")
  xbmcplugin.endOfDirectory(addon_handle)

def menu():
    addDir(translation(30113), translation(30113), 'new_episodes', "")    
    addDir(translation(30114), translation(30114), 'new_simulcast', "")    
    addDir(translation(30115), translation(30115), 'new_animes', "")    
    addDir(translation(30116), translation(30116), 'top10', "")    
    addDir(translation(30107), translation(30107), 'All', "") 
    addDir(translation(30104), translation(30104), 'AZ', "")
    addDir(translation(30105), translation(30105), 'cat', "")    
    addDir(translation(30106), translation(30106), 'lang', "")     
    #addDir(translation(30111), translation(30111), 'cookies', "") 
    addDir(translation(30108), translation(30108), 'Settings', "") 
    xbmcplugin.endOfDirectory(addon_handle,succeeded=True,updateListing=False,cacheToDisc=True)
def Start_listen(start_string):
 content=geturl("http://www.anime-on-demand.de/")
 kurz_inhalt = content[content.find(start_string)+1:]                                      
 kurz_inhalt = kurz_inhalt[:kurz_inhalt.find('<hr />')]
 spl=kurz_inhalt.split('<li>')
 for i in range(1,len(spl),1):
    entry=spl[i]
    debug("-------")
    debug(entry)
    match=re.compile('src="(.+?)"', re.DOTALL).findall(entry)
    img=baseurl+match[0]
    match=re.compile('<a href="(.+?)">(.+?)</a>', re.DOTALL).findall(entry)
    folge=match[0][0]
    Serie=match[0][1]
    try :
       match=re.compile('<span class="neweps">(.+?)</span>', re.DOTALL).findall(entry)
       folgen=match[0]
       name=ersetze(Serie + " ( "+ folgen + " ) ")
    except:
       name=ersetze(Serie)
    link=baseurl+folge
    addDir(name=name, url=link, mode="Serie", iconimage=img, desc="")
 xbmcplugin.endOfDirectory(addon_handle,succeeded=True,updateListing=False,cacheToDisc=True)
def cookies():
  if xbmcvfs.exists(temp):
    shutil.rmtree(temp)
  xbmcvfs.mkdirs(temp)
  menu()

    
if mode is '':
 menu()

else:
  # Wenn Settings ausgewählt wurde
  if mode == 'Settings':
          addon.openSettings()
  # Wenn Kategory ausgewählt wurde
  if mode == 'All':
          alles(baseurl+"/animes")
  if mode == 'Serie':
          Serie(url) 
  if mode == 'Folge':
          Folge(url,csrftoken,type)            
  if mode == 'cat':
          category()  
  if mode == 'lang':
          language()  
  if mode == 'catall':
          alles(url)
  if mode == 'AZ':
          abisz()
  if mode == 'cookies':
          cookies()
  if mode == 'getcontent_search':
          getcontent_search(url)             
  if mode == 'new_episodes':
          Start_listen("Neue Episoden")  
  if mode == 'new_simulcast':
          Start_listen("Neue Simulcasts")  
  if mode == 'new_animes':
          Start_listen("Neue Anime-Titel")  
  if mode == 'top10':
          Start_listen("Anime Top 10")            
