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
import datetime
import rsa
import pyaes
import base64
import ttml2srt
import ssl

ssl._create_default_https_context = ssl._create_unverified_context

global debuging
base_url = sys.argv[0]
addon_handle = int(sys.argv[1])

args = urlparse.parse_qs(sys.argv[2][1:])
addon = xbmcaddon.Addon()

mainurl="http://www.daisuki.net"
# Lade Sprach Variablen
translation = addon.getLocalizedString
defaultBackground = ""
defaultThumb = ""

def debug(content):
    log(content, xbmc.LOGDEBUG)
    
def notice(content):
    log(content, xbmc.LOGNOTICE)

def log(msg, level=xbmc.LOGNOTICE):
    addon = xbmcaddon.Addon()
    addonID = addon.getAddonInfo('id')
    xbmc.log('%s: %s' % (addonID, msg), level) 

def holejson(url):  
  content=getUrl(url)
  if content=="":
    return empty
  else:
    struktur = json.loads(content) 
    return struktur

def addDir(name, url, mode, iconimage, desc="", id="0", add=0, dele=0): 
  u = sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)
  ok = True
  liz = xbmcgui.ListItem(name, iconImage=iconimage, thumbnailImage=iconimage)
  if add==1:      
      addit = "plugin://plugin.video.daisuki/?mode=addserie&url="+urllib.quote_plus(url)+"&id="+urllib.quote_plus(id)
      commands = []
      commands.append(( translation(30113), 'XBMC.RunPlugin('+ addit +')'))    
      liz.addContextMenuItems( commands )
  if dele==1:
      delit = "plugin://plugin.video.daisuki/?mode=delserie&url="+urllib.quote_plus(url)
      commands = []
      commands.append(( translation(30114), 'XBMC.RunPlugin('+ delit +')'))          
      liz.addContextMenuItems( commands )
  liz.setInfo(type="Video", infoLabels={"Title": name, "Plot": desc})
  liz.setProperty("fanart_image", iconimage)
  ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=True)
  return ok
  
def addLink(name, url, mode, iconimage, duration="", desc="", genre='',shortname="",zeit="",production_year="",abo=1,search=""):
  debug ("addLink abo " + str(abo))
  debug ("addLink abo " + str(shortname))
  cd=addon.getSetting("password")  
  u = sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)
  ok = True
  liz = xbmcgui.ListItem(name, iconImage=defaultThumb, thumbnailImage=iconimage)
  liz.setInfo(type="Video", infoLabels={"Title": name, "Plot": desc, "Genre": genre,"Sorttitle":shortname,"Dateadded":zeit,"year":production_year })
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
  
  
def getUrl(url,data="x",header=""):
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
             #debug( e.code   )
             cc=e.read()  
             debug("Error : " +cc)
       
        opener.close()
        return content
  
def login():
  global cj
  username=addon.getSetting("user")  
  password=addon.getSetting("pass")  
  if not username=="" and  not password=="":
      main=getUrl(mainurl)
      country=re.compile('<meta property="og:url" content="http://www.daisuki.net/(.+?)/top.html"', re.DOTALL).findall(main)[0]
      debug("Country : "+ country)
      values = {'password' : password,
      'emailAddress' : username,        
      }      
      data = urllib.urlencode(values)
      debug("_------"+data)
      try:
          header = [('User-Agent', 'userAgent = "Mozilla/5.0 (Windows NT 10.0; WOW64; rv:49.0) Gecko/20100101 Firefox/49.0'),
                    ("Referer", "http://www.daisuki.net/"+country+"/top.html")]      
          content=getUrl("https://www.daisuki.net/bin/SignInServlet.html/input",data,header)                                  
          for cookief in cj:
            debug( cookief)
            if "key" in str(cookief):
               key=re.compile('key=(.+?) ', re.DOTALL).findall(str(cookief))[0]
            if "userID" in str(cookief):
               userid=re.compile('userID=(.+?) ', re.DOTALL).findall(str(cookief))[0]
          cxc=getUrl("http://www.daisuki.net/bin/SignInCheckServlet?userID="+userid+"&key="+key)             
          struktur = json.loads(cxc) 
          if not struktur["status"]=="0000":
             dialog = xbmcgui.Dialog()
             dialog.ok("Login",struktur["msg"])
          else:
              cj.save(cookie,ignore_discard=True, ignore_expires=True)                
      except:
          e = sys.exc_info()[0]
          debug("Error : ")
          debug(e)  
          dialog = xbmcgui.Dialog()
          dialog.ok(translation(30121),translation(30110))
      dialog = xbmcgui.Dialog()
      dialog.ok(translation(30121),translation(30115))        
# Setting Variablen Des Plugins


profile    = xbmc.translatePath( addon.getAddonInfo('profile') ).decode("utf-8")
temp       = xbmc.translatePath( os.path.join( profile, 'temp', '') ).decode("utf-8")

cookie=temp+"/cookie.jar"
cj = cookielib.LWPCookieJar();

if xbmcvfs.exists(cookie):
    cj.load(cookie,ignore_discard=True, ignore_expires=True)


username=addon.getSetting("user")
password=addon.getSetting("pass")

#Directory für Token Anlegen
if not xbmcvfs.exists(temp):       
       xbmcvfs.mkdirs(temp)
      
icon = xbmc.translatePath(xbmcaddon.Addon().getAddonInfo('path')+'/icon.png').decode('utf-8')
useThumbAsFanart=addon.getSetting("useThumbAsFanart") == "true"
xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_VIDEO_SORT_TITLE)
xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_LABEL)



def listserien(url):    
    main=getUrl(mainurl)
    country=re.compile('<meta property="og:url" content="http://www.daisuki.net/(.+?)/top.html"', re.DOTALL).findall(main)[0]
    debug( "Country : "+ country)
    url=url+country
    struktur=holejson(url)
    for name in struktur["response"]:
     title=name["title"]
     id=name["id"]
     image=mainurl+name["imageURL_s"]
     beschreibung=name["synopsis"]
     url=mainurl+name["animeURL"]
     addDir(title,url, 'serie', image,desc=beschreibung,id=id,add=1) 
    xbmcplugin.endOfDirectory(addon_handle,succeeded=True,updateListing=False,cacheToDisc=True)  
    
def serie(url):
    debug("Url Serie :"+url)
    content=getUrl(url)
    debug("Content Serie")
    debug(content)
    debug("--------------")
    kurz_inhalt = content[content.find('<!-- moviesBlock start -->')+1:]
    kurz_inhalt = kurz_inhalt[:kurz_inhalt.find('<!-- moviesBlock end  -->')]
    debug( kurz_inhalt)
    spl=kurz_inhalt.split('img delay')
    folge_arr=[]
    url_arr=[]
    image_arr=[]
    for element in spl:
      debug(".....")
      element="delay"+element
      try:
        nr=re.compile('/([0-9]+)/movie.jpg', re.DOTALL).findall(element)[0]
        debug("NR :"+nr)
        
        image=re.compile('delay="(.+?)"', re.DOTALL).findall(element)[0]
        debug("image :"+image)
        try:        
          folge=re.compile('false;">([^<]+)</a>', re.DOTALL).findall(element)[0]
          debug("folge1 :"+folge)
          if "#" in folge:
            folge=re.compile('#([0-9]+)', re.DOTALL).findall(folge)[0]
          debug("folge2 :"+folge)
        except:
          folge=re.compile('<p class="episodeNumber">([0-9]+?)</p>', re.DOTALL).findall(element)[0]    
        debug("folge3 :"+folge)
        urln=url.replace(".html","."+str(nr)+".html").replace("detail.","watch.")
        debug("urln :"+urln)
        if folge.isdigit()==True:
            folge=int(folge)
        if folge not in folge_arr:          
          folge_arr.append(folge)     
          url_arr.append(urln)
          image_arr.append(image)
      except:
        pass
    try:
      folge_arr, url_arr,image_arr = (list(x) for x in zip(*sorted(zip(folge_arr, url_arr,image_arr))))
      for i in range(0,len(url_arr),1): 
          debug( url_arr[i])
          debug(folge_arr[i])
          addLink("Episode "+str(folge_arr[i]),url_arr[i], 'stream', "http://www.daisuki.net"+image_arr[i]) 
       
      xbmcplugin.endOfDirectory(addon_handle,succeeded=True,updateListing=False,cacheToDisc=True)      
    except:
       xbmc.executebuiltin('Notification("No Episodes", "No Episodes ,maybe pay content")')
      
def getstream(url):
 
  urljs="http://www.daisuki.net/etc/designs/daisuki/clientlibs_anime_watch.min.js"
  content=getUrl(urljs)
  match=re.compile('publickeypem="(.+?)"', re.DOTALL).findall(content)
  key=match[0]
  pubkey_pem = key.replace("\\n", "\n")
  params = {
            "cashPath":int(time.time()*1000)
  }
  content=getUrl(url)
  debug(content)
  try:
    match=re.compile('var flashvars = {(.+?)}', re.DOTALL).findall(content)
    flash=match[0]
  except:
     dialog = xbmcgui.Dialog()
     dialog.ok("Premium",translation(30111))
     return
  api_params = {}
  s=re.compile('\'s\':"(.+?)"', re.DOTALL).findall(content)[0]
  initi=re.compile('\'init\':\'(.+?)\'', re.DOTALL).findall(content)[0]
  api_params["device_cd"]=re.compile('device_cd":"(.+?)"', re.DOTALL).findall(content)[0]
  api_params["ss1_prm"]=re.compile('ss1_prm":"(.+?)"', re.DOTALL).findall(content)[0]
  api_params["ss2_prm"]=re.compile('ss2_prm":"(.+?)"', re.DOTALL).findall(content)[0]
  api_params["ss4_prm"]=re.compile('ss3_prm":"(.+?)"', re.DOTALL).findall(content)[0]
  api_params["mv_id"]=re.compile('mv_id":"(.+?)"', re.DOTALL).findall(content)[0]

  aeskey = os.urandom(32)
  #aeskey = "This_key_for_demo_purposes_only!"
  pubkey = rsa.PublicKey.load_pkcs1_openssl_pem(pubkey_pem)
  crypton = base64.b64encode(rsa.encrypt(aeskey, pubkey))

  encrypter = pyaes.Encrypter(pyaes.AESModeOfOperationCBC(aeskey))
  ciphertext=""
  plaintext=json.dumps(api_params)
  for line in plaintext:
    ciphertext += encrypter.feed(line)

  # Make a final call to flush any remaining bytes and add paddin
  ciphertext += encrypter.feed()
  
  ciphertext = base64.b64encode(ciphertext)
  params = {
            "s": s,
            "c": api_params["ss4_prm"],
            "e": url,
            "d": ciphertext,
            "a": crypton
  }
  data = urllib.urlencode(params)
  res = getUrl("http://www.daisuki.net"+initi+"?"+data)
  struktur=json.loads(res) 
  rtn= struktur["rtn"]
  rtn=base64.b64decode(rtn)
  decrypter = pyaes.Decrypter(pyaes.AESModeOfOperationCBC(aeskey))
  decrypted = decrypter.feed(rtn)
  #decrypted += decrypter.feed(rtn[len(ciphertext) / 2:])
  debug("Decrypt :"+decrypted)
  playurl=re.compile('"play_url":"(.+?)"', re.DOTALL).findall(decrypted)[0]  
  debug("Playurl :"+playurl)
  sub=re.compile('"caption_url":"(.+?)"', re.DOTALL).findall(decrypted)[0]  
  title=re.compile('"title_str":"(.+?)"', re.DOTALL).findall(decrypted)[0]    
  return playurl,sub,title

def stream(url):  
   try:   
      urls,sub,title=getstream(url)
   except:
       return
   debug ("Streamurl :"+url)
   debug ("Streamurlsub :"+sub)

   listitem = xbmcgui.ListItem(path=urls)
   listitem.setInfo('video', { 'title': title })
   subcontent=getUrl(sub)
   subcontent='<?xml version="1.0" encoding="UTF-8"?>\n'+subcontent
   sprachen=subcontent.split("<div xml:lang=")
   listsubs=[]
   for i in range(1,len(sprachen),1):
     element=sprachen[i]
     element=sprachen[0]+"<div xml:lang="+sprachen[i]
     lang=re.compile('lang="(.+?)"', re.DOTALL).findall(element)[0]      
     text_file = open(temp+lang+".xml", "w")
     text_file.write(element)
     text_file.close()      
     ttml2srt.ttml2srt(temp+lang+".xml", True,temp+lang+".srt")
     listsubs.append(temp+lang+".srt")     
   listitem.setSubtitles(listsubs)
   xbmcplugin.setResolvedUrl(addon_handle,True, listitem) 
   
def generes(url):   
   urlkat="http://www.daisuki.net/bin/wcm/searchAnimeAPI?api=anime_categories&currentPath=%2Fcontent%2Fdaisuki%2Fde%2Fen"
   content=getUrl(urlkat)
   struktur = json.loads(content) 
   response=struktur["response"][url]
   for element in response:
     if int(element["SeriesCount"])>0:
       name=element["name"]
       id=element["id"]
       addDir(name,"http://www.daisuki.net/bin/wcm/searchAnimeAPI?api=anime_list&searchOptions=genre="+str(id)+"&currentPath=/content/daisuki/", 'listserien', "")  
   xbmcplugin.endOfDirectory(addon_handle,succeeded=True,updateListing=False,cacheToDisc=True) 

def myanimelist():    
    main=getUrl(mainurl)
    country=re.compile('<meta property="og:url" content="http://www.daisuki.net/(.+?)/top.html"', re.DOTALL).findall(main)[0]
    sprache=re.compile('[^/]+/(.+)', re.DOTALL).findall(country)[0]
    url="https://www.daisuki.net/bin/MyAnimeListServlet"
    params = {
            "pagePath": "/content/daisuki/"+country+"/mypage/myanimelist",
            "language": sprache            
    }
    header = [('User-Agent', 'userAgent = "Mozilla/5.0 (Windows NT 10.0; WOW64; rv:49.0) Gecko/20100101 Firefox/49.0'),              
              ("Referer", "https://www.daisuki.net/"+country+"/mypage/myanimelist.html")]      
    data = urllib.urlencode(params)  
    debug ("Data :"+data)
    try:
      content=getUrl(url,data,header)         
      struktur = json.loads(content)   
      for serie in struktur["items"]  :
        debug( serie)
        url=mainurl+serie["url"]
        image=mainurl+serie["imagePath"]
        title=serie["title"]
        addDir(title,url, 'serie', image,dele=1,id=1)  
    except:
       dialog = xbmcgui.Dialog()
       dialog.ok(translation(30121),translation(30112))
    xbmcplugin.endOfDirectory(addon_handle,succeeded=True,updateListing=False,cacheToDisc=True) 

def addserie(url,id):      
  urls="http://www.daisuki.net/bin/MyAnimeListServlet/add"
  params = {
            "series_id": id            
    }
  data = urllib.urlencode(params)   
  header = [('User-Agent', 'userAgent = "Mozilla/5.0 (Windows NT 10.0; WOW64; rv:49.0) Gecko/20100101 Firefox/49.0'),
            ("Referer", url),
            ("X-Requested-With", "XMLHttpRequest"),
            ("CSRF-Token","undefined")
            ]        
  content=getUrl(urls,data,header)         

def delserie(url):
  content=getUrl(url) 
  id=re.compile('g_id = ([0-9]+)</script>', re.DOTALL).findall(content)[0]
  debug( "IDID :"+id)
  urls="http://www.daisuki.net/bin/MyAnimeListServlet/remove"
  params = {
            "series_id": id            
    }
  data = urllib.urlencode(params)   
  header = [('User-Agent', 'userAgent = "Mozilla/5.0 (Windows NT 10.0; WOW64; rv:49.0) Gecko/20100101 Firefox/49.0'),
            ("Referer", url),
            ("X-Requested-With", "XMLHttpRequest"),
            ("CSRF-Token","undefined")
            ]        
  content=getUrl(urls,data,header)         
  debug("content")
  xbmc.executebuiltin("Container.Refresh")

params = parameters_string_to_dict(sys.argv[2])
mode = urllib.unquote_plus(params.get('mode', ''))
url = urllib.unquote_plus(params.get('url', ''))
id = urllib.unquote_plus(params.get('id', ''))

user=addon.getSetting("user")  
passw=addon.getSetting("pass")  
  
if mode is '':
    addDir(translation(30116),"http://www.daisuki.net/bin/wcm/searchAnimeAPI?api=anime_list&searchOptions=&currentPath=/content/daisuki/", 'listserien', "")  
    addDir(translation(30117), 'categories', "generes","")  
    addDir(translation(30118), 'studios', "generes","")  
    if not user=="" and not password=="":
      addDir(translation(30119), "login", 'login', "")
      addDir(translation(30120), "myanimelist", 'myanimelist', "")            
    addDir(translation(30108), translation(30108), 'Settings', "") 
    xbmcplugin.endOfDirectory(addon_handle,succeeded=True,updateListing=False,cacheToDisc=True) 
else:
  # Wenn Settings ausgewählt wurde
  if mode == 'Settings':
          addon.openSettings()
  # Wenn Kategory ausgewählt wurde
  if mode == 'listserien':
          listserien(url)                      
  if mode == 'serie':
          serie(url)      
  if mode == 'stream':
          stream(url)                
  if mode == 'generes':
          generes(url)               
  if mode == 'login':
          login()
  if mode == 'myanimelist':
          myanimelist()          
  if mode == 'addserie':
          addserie(url,id)                    
  if mode == 'delserie':
          delserie(url)                              
