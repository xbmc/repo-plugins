#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import urlparse
import xbmcgui
import xbmcplugin
import xbmcaddon
import xbmc
import xbmcvfs
import hashlib
import urllib, urllib2, socket, cookielib, re, os, shutil,json
import pyxbmct

addon_handle = int(sys.argv[1])
addon = xbmcaddon.Addon()
translation = addon.getLocalizedString
icon = xbmc.translatePath(xbmcaddon.Addon().getAddonInfo('path')+'/icon.png').decode('utf-8')
global quality
global qualityhtml1
quality=addon.getSetting("quality")
qualityhtml1=addon.getSetting("qualityhtml1")
username=addon.getSetting("user")
password=addon.getSetting("pass")
global movies
movies=addon.getSetting("movies")
filtertype=addon.getSetting("filtertype")





profile    = xbmc.translatePath( addon.getAddonInfo('profile') ).decode("utf-8")
temp       = xbmc.translatePath( os.path.join( profile, 'temp', '') ).decode("utf-8")
if not xbmcvfs.exists(temp):  
  xbmcvfs.mkdirs(temp)

favdatei   = xbmc.translatePath( os.path.join(temp,"favorit.txt") ).decode("utf-8")



def debug(content):
    log(content, xbmc.LOGDEBUG)
    
def notice(content):
    log(content, xbmc.LOGNOTICE)

def log(msg, level=xbmc.LOGNOTICE):
    addon = xbmcaddon.Addon()
    addonID = addon.getAddonInfo('id')
    xbmc.log('%s: %s' % (addonID, msg), level) 


cookie   = xbmc.translatePath( os.path.join(temp,"cookie.jar") ).decode("utf-8")    
cj = cookielib.LWPCookieJar();


if xbmcvfs.exists(cookie):
   cj.load(cookie,ignore_discard=True, ignore_expires=True)


opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
baseurl="https://www.anime-on-demand.de"


class Infowindow(pyxbmct.AddonDialogWindow):    
    text=""
    pos=0
    image=""
    trailer=""
    starttext=""
    def __init__(self, text=''):
        self.title=re.compile('<h1 style="margin: 0;">(.+?)</h1>', re.DOTALL).findall(text)[0]
        try:
              self.image=baseurl+ re.compile('class="newspic" src="(.+?)"', re.DOTALL).findall(text)[0]
        except:
               pass
        kurz_inhalt = text[text.find('<div class="article-text">')+1:]
        kurz_inhalt = kurz_inhalt[:kurz_inhalt.find('</div>')]  
        if "<table " in kurz_inhalt: 
          self.starttext=text        
          kurz_inhalt = kurz_inhalt[:kurz_inhalt.find('<table ')]  
        kurz_inhalt=ersetze(kurz_inhalt)       
        kurz_inhalt= kurz_inhalt.replace("</p>","\n")
        spl=kurz_inhalt.split('\n')
        self.text=""
        self.textlen=0
        for i in range(1,len(spl),1):
          entry=spl[i]
          debug("Entry :"+entry)
          if not "img alt=" in entry and not "iframe " in entry :
             entry=entry.replace("<br />","\n")
             entry=entry.replace("</li>","\n")
             kuerzen=re.compile('<(.+?)>', re.DOTALL).findall(entry)
             for kurz in kuerzen:
                debug("Kurz :"+kurz)
                entry=entry.replace("<"+kurz+">","")    
             self.text=self.text+entry+"\n"
             self.textlen=self.textlen+1
        self.title=ersetze(self.title)
        try:
          self.trailer=re.compile('src="https://www.youtube.com/embed/(.+?)"', re.DOTALL).findall(text)[0]        
          debug("TRailer: "+self.trailer)
        except:
           pass
        super(Infowindow, self).__init__(self.title)
        self.setGeometry(600,600,23,10)
        self.set_info_controls()
        # Connect a key action (Backspace) to close the window.
        self.connect(pyxbmct.ACTION_NAV_BACK, self.close)
    def set_info_controls(self):   
      debug("set_info_controls start")    
      self.ueberschrift=pyxbmct.Label(self.title,alignment=pyxbmct.ALIGN_CENTER) 
      self.placeControl(self.ueberschrift, 0, 0,columnspan=10,rowspan=1) 
      
      if not "<tbody>" in self.starttext:  
        if self.image=="" and not self.trailer=="" :
             self.image="https://img.youtube.com/vi/"+self.trailer+"/hqdefault.jpg"        
        self.image = pyxbmct.Image( self.image,aspectRatio=2)
        self.placeControl(self.image, 1, 1,columnspan=6,rowspan=6)
        self.beschreibung=pyxbmct.TextBox( font='font10')
        self.placeControl(self.beschreibung, 7, 0,columnspan=10,rowspan=14) 
        self.beschreibung.setText(self.text)      
        self.button = pyxbmct.Button('Trailer', font='font14')
        if not self.trailer=="":            
            self.placeControl(self.button, 20, 0,columnspan=4,rowspan=2) 
            self.connect(self.button, self.startv)
        self.raus = pyxbmct.Button('Exit', font='font14')
        self.placeControl(self.raus, 20, 6,columnspan=4,rowspan=2) 
        self.connect(self.raus, self.close)
        self.setFocus(self.raus)  
      else:
        self.image = pyxbmct.Image( self.image,aspectRatio=2)
        self.placeControl(self.image, 1, 4,columnspan=2,rowspan=2)
        
        self.beschreibung=pyxbmct.TextBox(font='font10')
        self.placeControl(self.beschreibung, 3, 0,columnspan=10,rowspan=7) 
        self.beschreibung.setText(self.text)      
        
        #self.sp1=pyxbmct.Label("16.-22.01.2017",font='font11')
        #self.placeControl(self.sp1, 9, 0,columnspan=3,rowspan=2)     
        #self.sp2=pyxbmct.Label("Titel",font='font11')
        #self.placeControl(self.sp2, 9, 3,columnspan=3,rowspan=2)       
        #self.sp3=pyxbmct.Label("Episode",font='font11')
        #self.placeControl(self.sp3, 9, 6,columnspan=3,rowspan=2) 
        kurz_inhalt = self.starttext[self.starttext.find('<tbody>')+1:]
        kurz_inhalt = kurz_inhalt[:kurz_inhalt.find('</tbody>')]    
        kurz_inhalt=kurz_inhalt.replace("\n","")
        starty=9
        startx=0
        counter=0
        counter2=0
        spl=kurz_inhalt.split('</tr>')               
        for i in range(0,len(spl),1):
          entry=spl[i]
          entry=entry.replace("<br />","###")
          match=re.compile('>(.+?)</td>', re.DOTALL).findall(entry)
          for feld in match:              
              feld=ersetze(feld)
              kuerzen=re.compile('<(.+?)>', re.DOTALL).findall(feld)
              for kurz in kuerzen:
                feld=feld.replace("<"+kurz+">","") 
              if len(feld)>20:
                 gr=5
              else:
                 gr=0
              if "###" in feld:
                  sp2=feld.split('###')              
                  for i2 in range(0,len(sp2),1):
                    entry2=sp2[i2]
                    self.sp1=pyxbmct.Label(entry2,font='font10')                    
                    self.placeControl(self.sp1, starty, startx,columnspan=2+gr,rowspan=2)                
                    starty=starty+1
                    counter=counter+1
                  starty=starty-counter
                  if counter2<counter:
                    counter2=counter-1
                  counter=0
                  startx=startx+2+gr
              else:
                 self.sp1=pyxbmct.Label(feld,font='font10')
                 self.placeControl(self.sp1, starty, startx,columnspan=2+gr,rowspan=2)                
                 startx=startx+2+gr 
          starty=starty+1+counter2      
          counter2=0          
          startx=0 
          
      #self.z1=pyxbmct.Label("AAAA")
      #self.placeControl(self.z1, 10, 0,columnspan=3,rowspan=2) 
      #self.z1=pyxbmct.Label("BBBB")
      #self.placeControl(self.z1, 10, 3,columnspan=3,rowspan=2) 
      #self.z1=pyxbmct.Label("CCCC")
      #self.placeControl(self.z1, 10, 6,columnspan=3,rowspan=2)       
      self.connectEventList([pyxbmct.ACTION_MOVE_LEFT,
                             pyxbmct.ACTION_MOVE_RIGHT,
                             pyxbmct.ACTION_MOUSE_DRAG,
                             pyxbmct.ACTION_MOUSE_LEFT_CLICK],
                             self.leftright)
      self.connectEventList(
             [pyxbmct.ACTION_MOVE_UP,
             pyxbmct.ACTION_MOUSE_WHEEL_UP],
            self.hoch)         
      self.connectEventList(
            [pyxbmct.ACTION_MOVE_DOWN,
             pyxbmct.ACTION_MOUSE_WHEEL_DOWN],
            self.runter)         

            
    def  startv(self):
      self.close()
      plugin='plugin://plugin.video.youtube/?action=play_video&videoid='+ self.trailer  
      xbmc.executebuiltin("xbmc.PlayMedia("+plugin+")")
      
    
      debug("Pressed Button")
    def  leftright(self):
        if self.getFocus() == self.raus:
             self.setFocus(self.button)     
        elif self.getFocus() == self.beschreibung:
             self.setFocus(self.button) 
        elif self.getFocus() == self.button:
             self.setFocus(self.raus)               
        else:
             self.setFocus(self.raus)    
    def hoch(self):
        self.pos=self.pos-1
        if self.pos < 0:
          self.pos=0
        self.beschreibung.scroll(self.pos)
    def runter(self):
        self.pos=self.pos+1        
        self.beschreibung.scroll(self.pos)
        posnew=self.beschreibung.getPosition()
        debug("POSITION : "+ str(posnew))             
     
def ersetze(inhalt):
   inhalt=inhalt.replace('&#39;','\'')  
   inhalt=inhalt.replace('&quot;','"')    
   inhalt=inhalt.replace('&gt;','>')      
   inhalt=inhalt.replace('&amp;','&') 
   inhalt=inhalt.replace('&uuml;','ü') 
   inhalt=inhalt.replace('&ouml;','ö')  
   inhalt=inhalt.replace('&auml;','ä') 
   inhalt=inhalt.replace('&Uuml;','Ü') 
   inhalt=inhalt.replace('&Ouml;','Ö')  
   inhalt=inhalt.replace('&Auml;','Ä')    
   inhalt=inhalt.replace('&szlig;','ß') 
   inhalt=inhalt.replace('&nbsp;',' ') 
   inhalt=inhalt.replace('&rsquo;','\'') 
   inhalt=inhalt.replace('&ndash;','-')
   inhalt=inhalt.replace('&hellip;','...')
   inhalt=inhalt.replace('&Eacute','E')
   inhalt=inhalt.replace('\n','') 
   inhalt=inhalt.replace('\t','') 
   inhalt=inhalt.replace('&copy;','(c)') 
   inhalt=inhalt.replace('&ldquo;','"') 
   inhalt=inhalt.replace('&rdquo;','"') 
   inhalt=inhalt.replace('&bdquo;','"') 
   return inhalt

def addDir(name, url, mode, iconimage, desc="",title="",bild=""):
	u = sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&title="+str(title)+"&bild="+str(bild)
	ok = True
	liz = xbmcgui.ListItem(name, iconImage=icon, thumbnailImage=iconimage)
	liz.setInfo(type="Video", infoLabels={"Title": name, "Plot": desc})			

	ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=True)
	return ok   
  
  
def addLink(name, url, mode, iconimage, duration="", desc="", genre='',csrftoken="",type="",play='true'):
  debug("addlink :" + url)  
  u = sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&csrftoken="+csrftoken+"&type="+type
  ok = True
  liz = xbmcgui.ListItem(name, thumbnailImage=iconimage)
  liz.setInfo(type="Video", infoLabels={"Title": name, "Plot": desc, "Genre": genre})
  liz.setProperty('IsPlayable', play)
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
        debug("::::: filtertype "+str(filtertype))        
        if ( "(OmU)" in  title and filtertype=="0" ) or ( not "(OmU)" in  title and filtertype=="1" ) or filtertype=="2":     
            addDir(name=ersetze(title), url=link, mode="Serie", iconimage=img, desc=desc,title=title,bild=img)
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
   
    
def Serie(url,title="",bild=""):
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
  menulist=""
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
      ret,menulist=flashvideo(entry,img,csrftoken,menulist)
      if ret==1:
        ret,menulist=html5video(entry,img,csrftoken,menulist)
    except :
       error=1  
  debug ("#############################################################################")
  f = open( os.path.join(temp,"menu.txt"), 'w')  
  f.write(menulist)
  f.close()
  addDir(translation(30127), url, mode="simil", iconimage="", desc="")      
  found=0
  if xbmcvfs.exists(favdatei):
     f=open(favdatei,'r')     
     for line in f:
           if url in line:
              found=1
  if found==0:           
             addDir(translation(30128), url, mode="favadd", iconimage="", desc="",title=title,bild=bild)      
  else :
             addDir(translation(30129), url, mode="favdel", iconimage="", desc="")     
  xbmcplugin.endOfDirectory(addon_handle,succeeded=True,updateListing=False,cacheToDisc=True)  
  
def favadd(url,titel,bild):
  debug(" favadd url :"+url)
  textfile=url+"###"+titel+"###"+bild+"\n"
  try:
    f=open(favdatei,'r')
    for line in f:
      textfile=textfile+line
    f.close()
  except:
    pass
  f=open(favdatei,'w')
  f.write(textfile)
  f.close()
  xbmc.executebuiltin('Notification('+ translation(30131)+',"'+translation(30132)+'")')
  xbmc.executebuiltin("Container.Refresh")
    

def favdel(url):
  debug(" FAVDEL url :"+url)
  textfile=""
  f=open(favdatei,'r')
  for line in f:
     if not url in line and not line=="\n":
      textfile=textfile+line
  f.close()
  f=open(favdatei,'w')
  f.write(textfile)
  f.close()
  xbmc.executebuiltin('Notification('+ translation(30133)+',"'+translation(30134)+'")')
  xbmc.executebuiltin("Container.Refresh")  

def listfav()  :
    if xbmcvfs.exists(favdatei):
        f=open(favdatei,'r')
        for line in f:
          spl=line.split('###')       
          addDir(name=spl[1], url=spl[0], mode="Serie", iconimage=spl[2].strip(), desc="",title=spl[1],bild=spl[2].strip())
        f.close()
    xbmcplugin.endOfDirectory(addon_handle,succeeded=True,updateListing=False,cacheToDisc=True)
    
def  simil(url):
  userAgent = "Mozilla/5.0 (Windows NT 6.2; WOW64; rv:23.0) Gecko/20100101 Firefox/23.0"
  opener.addheaders = [('User-Agent', userAgent)]
  content=opener.open(url).read()  
  kurz_inhalt = content[content.find('<div class="jcarousel">')+1:]                                      
  kurz_inhalt = kurz_inhalt[:kurz_inhalt.find('</div>')]
  spl=kurz_inhalt.split('<li>')
  for i in range(1,len(spl),1):
      entry=spl[i]                        
      match=re.compile('<a href="(.+?)">(.+?)</a>', re.DOTALL).findall(entry)
      urlx=baseurl+match[0][0]
      title=match[0][1]
      img=baseurl+re.compile('src="(.+?)"', re.DOTALL).findall(entry)[0]
      addDir(name=title, url=urlx, mode="Serie", iconimage=img, desc="",title=title,bild=img)
  xbmcplugin.endOfDirectory(addon_handle,succeeded=True,updateListing=False,cacheToDisc=True)
  
def html5video(entry,img,csrftoken,menulist):     
    error=0
    debug("Start HTMLvideo")
    try:
      match=re.compile(' title="([^"]+)"', re.DOTALL).findall(entry)
      title=match[0] 
      debug ("Title :"+title)  
      try:      
        if '<p class="episodebox-shorttext">' in entry:
           match=re.compile('<p class="episodebox-shorttext">(.+)</p>', re.DOTALL).findall(entry)
        else:
           match=re.compile('<div itemprop="description">(.+)</p>', re.DOTALL).findall(entry)
        desc=match[0]    
        desc=desc.replace("<br />","") 
        desc=desc.replace("<p>","") 
        desc=desc.replace("&quot;","\"") 
      except:
        desc=""
      debug("csrftoken : "+csrftoken)      
      match=re.compile('title="([^"]+)" data-playlist="([^"]+)"', re.DOTALL).findall(entry)
      for type,link in match:        
        title2=title + " ( "+ type.replace("starten","").replace("Japanischen Stream mit Untertiteln","OmU").replace("Deutschen Stream","Syncro") +" )"
        debug("Link: "+ link)                   
        debug("title :"+title2) 
        idd=hashlib.md5(title2).hexdigest()        
        menulist=menulist+idd+"###"+baseurl+link+"###"+csrftoken+"###html5###\n"
        if ( not "Syncro" in  title2 and filtertype=="0" ) or ( "Syncro" in  title2 and filtertype=="1" ) or filtertype=="2": 
          addLink(name=ersetze(title2), url="plugin://plugin.video.aod/", mode="hashplay", iconimage=img, desc=desc,csrftoken=idd,type="html5")      
    except :
       error=1
    return error,menulist
def hashplay(idd):
  debug("hashplay url :"+idd)
  f=xbmcvfs.File( os.path.join(temp,"menu.txt"),"r")   
  daten=f.read()
  zeilen=daten.split('\n')  
  for zeile in zeilen:    
    debug ("Read Zeile :"+zeile)
    felder=zeile.split("###")
    debug("Felder ")
    debug(felder)
    if felder[0]==idd:    
          debug("Gefunden")
          uurl=felder[1]
          csrftoken=felder[2]          
          type=felder[3]                      
          debug("Type :"+type)
          Folge(uurl,csrftoken,type)
    
           
  
def flashvideo(entry,img,csrftoken,menulist):    
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
         debug("URL :" + link)
         debug("title :"+title)
         idd=hashlib.md5(title).hexdigest()        
         menulist=menulist+idd+"###"+link+"###"+csrftoken+"###flash###\n"     
         addLink(name=ersetze(title), url="plugin://plugin.video.aod/", mode="hashplay", iconimage=img, desc=desc,csrftoken=idd,type="flash")      
    except :
       error=1
    return error,menulist

def Folge(url,csrftoken,type):
  global opener
  global cj
  global username
  global password
  debug("Folge URL :"+url+"#")
  debug("Folge csrftoken :"+csrftoken+"#")
  debug("Folge type :"+type+"#")
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
      debug("Folge  html5")
      match = re.compile('"file":"([^"]+)"', re.DOTALL).findall(content)
      stream=match[1].replace("\\u0026","&")
      debug("1")
      debug("stream :" + stream)
      content2=opener.open(stream).read()   
      debug("-------Content2---------")      
      debug(content2)      
      debug("----------------")      
      spl=content2.split('#EXT-X-STREAM-INF')
      debug("qualityhtml1 :"+qualityhtml1)
      if not qualityhtml1=="6":
        element=spl[int(qualityhtml1)+1]
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
      if qualityhtml1=="6":
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
title = urllib.unquote_plus(params.get('title', ''))
bild = urllib.unquote_plus(params.get('bild', ''))


def abisz():
  addDir("0-9", baseurl+"/animes/begins_with/0-9", 'catall', "")
  letters = [chr(i) for i in xrange(ord('a'), ord('z')+1)]
  for letter in letters:
		addDir(letter.upper(), baseurl+"/animes/begins_with/"+letter.upper(), 'catall', "")
  xbmcplugin.endOfDirectory(addon_handle)

def newmenu():
    addDir(translation(30113), translation(30113), 'new_episodes', "")    
    addDir(translation(30114), translation(30114), 'new_simulcast', "")    
    addDir(translation(30115), translation(30115), 'new_animes', "")    
    xbmcplugin.endOfDirectory(addon_handle,succeeded=True,updateListing=False,cacheToDisc=True)   

def newsmenu():
  addDir(translation(30119), "/articles/category/3/1", 'readnews', "") 
  addDir(translation(30120), "/articles/category/2/1", 'readnews', "") 
  addDir(translation(30121), "/articles/category/1/1", 'readnews', "") 
  addDir(translation(30122), "/articles/category/4/1", 'readnews', "") 
  xbmcplugin.endOfDirectory(addon_handle,succeeded=True,updateListing=False,cacheToDisc=True)         
  
def readnews(kat):
    url=baseurl+kat
    content = geturl(url)    
    elemente = content.split('<div class="category-item">') 
    for i in range(1, len(elemente), 1):
      element=elemente[i]   
      match = re.compile('<a href="(.+?)">(.+?)</a>', re.DOTALL).findall(element)
      url=match[0][0]
      name=match[0][1]
      image = re.compile('src="(.+?)"', re.DOTALL).findall(element)[0]
      addLink(name=ersetze(name), url=baseurl+url, mode="artikel", iconimage=baseurl+image,play="false") 
    xbmcplugin.endOfDirectory(addon_handle,succeeded=True,updateListing=False,cacheToDisc=True)         
    
def artikel(url):
    debug("Start Artikel")
    debug("Artikel  ULR:"+ url)
    content = geturl(url) 
    listitem = xbmcgui.ListItem(path="")
    xbmcplugin.setResolvedUrl(addon_handle, False, listitem)
    debug(" ARtikeL ##")
    #try:
    window=Infowindow (text=content)     
    window.doModal()
    del window
    #except:
   #     debug("ERROR ARTIKEL")
    #xbmc.executebuiltin('Notification("Fehler","News nicht darstellbar")')

def menu():
    addDir(translation(30118), "", 'newsmenu', "")  
    addDir(translation(30117), translation(30117), 'newmenu', "") 
    addDir(translation(30130), translation(30130), 'listfav', "") 
    addDir(translation(30116), translation(30116), 'top10', "")    
    addDir(translation(30107), translation(30107), 'All', "") 
    addDir(translation(30104), translation(30104), 'AZ', "")
    addDir(translation(30105), translation(30105), 'cat', "")    
    addDir(translation(30106), translation(30106), 'lang', "")         
    addDir(translation(30111), translation(30111), 'cookies', "") 
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
    kuerzen=re.compile('<(.+?)>', re.DOTALL).findall(name)
    for kurz in kuerzen:
        name=name.replace("<"+kurz+">","") 
    if ( "(OmU)" in  name and filtertype=="0" ) or ( not "(OmU)" in  name and filtertype=="1" ) or filtertype=="2": 
        addDir(name=name, url=link, mode="Serie", iconimage=img, desc="",title=name,bild=img)
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
          Serie(url,title,bild) 
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
  if mode == 'hashplay':          
          hashplay(csrftoken)
  if mode == 'newsmenu':          
          newsmenu()
  if mode == 'newmenu':          
          newmenu()          
  if mode == 'readnews':          
          readnews(url)            
  if mode == 'artikel':          
          artikel(url)                      
  if mode == 'simil':          
          simil(url)          
  if mode == 'favadd':          
          favadd(url,title,bild)          
  if mode == 'favdel':          
          favdel(url)                             
  if mode == 'listfav':          
          listfav()     