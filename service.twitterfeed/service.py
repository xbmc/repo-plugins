#!/usr/bin/python
# -*- coding: utf-8 -*-

import time, sys, os, urlparse
import xbmc ,xbmcgui, xbmcaddon,xbmcvfs
import urllib2,urllib,json
import twitter,shutil
import webbrowser
import re,md5
from requests_oauthlib import OAuth1Session
from thread import start_new_thread
from requests.packages import urllib3
import socket, cookielib
import popupwindow

urllib3.disable_warnings()
 
REQUEST_TOKEN_URL = 'https://api.twitter.com/oauth/request_token'
ACCESS_TOKEN_URL = 'https://api.twitter.com/oauth/access_token'
AUTHORIZATION_URL = 'https://api.twitter.com/oauth/authorize'
SIGNIN_URL = 'https://api.twitter.com/oauth/authenticate'
consumer_key = "X54OL8ozrRMQWmYrQJV2Ihirr"
consumer_secret = "0RHD0CRm7noPvwVYvPL5FAaqazBu49JUecUN7tWam7yaMqeLZi"
oauth_token=""
oauth_token_secret=""


__addon__ = xbmcaddon.Addon()
__addonname__ = __addon__.getAddonInfo('name')
__addondir__    = xbmc.translatePath( __addon__.getAddonInfo('path') )
background = os.path.join(__addondir__,"bg.png")

profile    = xbmc.translatePath( __addon__.getAddonInfo('profile') ).decode("utf-8")
temp       = xbmc.translatePath( os.path.join( profile, 'temp', '') ).decode("utf-8")
translation = __addon__.getLocalizedString

  
wid = xbmcgui.getCurrentWindowId()
window=xbmcgui.Window(wid)
window.show()
  
# Einlesen von Parametern, Notwendig für Reset der Twitter API
def parameters_string_to_dict(parameters):
	paramDict = {}
	if parameters:
		paramPairs = parameters[1:].split("&")
		for paramsPair in paramPairs:
			paramSplits = paramsPair.split('=')
			if (len(paramSplits)) == 2:
				paramDict[paramSplits[0]] = paramSplits[1]
	return paramDict

# Soll Twitter Api Resetter Werden
if len(sys.argv) > 1:
    params = parameters_string_to_dict(sys.argv[2])
    mode = urllib.unquote_plus(params.get('mode', ''))
    if mode=="clear":      
      xbmc.log("Twitter : CLEAR AUTH")
      # ES wird mit dem Service ueber ein Verstecktes Feld Kommuiniziert
      __addon__.setSetting(id='clear', value='CLEARIT')
      # Meldung das der Settings gelöscht werden
      dialog2 = xbmcgui.Dialog()
      ok = xbmcgui.Dialog().ok( translation(30024), translation(30025) )
      exit()
  


def debug(content):
    log(content, xbmc.LOGDEBUG)
    
def notice(content):
    log(content, xbmc.LOGNOTICE)

def log(msg, level=xbmc.LOGNOTICE):
    addon = xbmcaddon.Addon()
    addonID = addon.getAddonInfo('id')
    xbmc.log('%s: %s' % (addonID, msg), level) 
    
def geturl(url):
   req = urllib2.Request(url)
   inhalt = urllib2.urlopen(req).read()   
   return inhalt    
        
# Get Token
def get_access_token(consumer_key, consumer_secret):
    oauth_client = OAuth1Session(consumer_key, client_secret=consumer_secret)
    xbmc.log("Twitter: Requesting temp token from Twitter")
    try:
        resp = oauth_client.fetch_request_token(REQUEST_TOKEN_URL)
    except ValueError, e:
        xbmc.log("Twitter: Invalid respond from Twitter requesting temp token: %s" % e)
        return
    url = oauth_client.authorization_url(AUTHORIZATION_URL)

    # Will der User das gleich ein Browser aufgerufen wird
    __addon__.setSetting(id='clear', value='')
    dialog = xbmcgui.Dialog()
    dl=dialog.select("Twitter",[ translation(30019),translation(30020),translation(30021)] )
    if dl==0:
        webbrowser.open(url)
    if dl==1:
           xbmc.log("Twitter: URL ---> "+url)
           # Zeige Url als Text an
           dialog = xbmcgui.Dialog()
           dialog.ok(translation(30023), url[:40] +"\n"+ url[40:80] +"\n" +url[80:120] )
    if dl==2:
            return 1
    # Eingabe des Pins
    keyboard = xbmc.Keyboard('')
    keyboard.setHeading(translation(30022))
    keyboard.doModal()
    if (keyboard.isConfirmed()):
      PIN=keyboard.getText()
    else:
      PIN='0000'
    if  PIN=='0000':
       return 1
    xbmc.log("Pin: "+ PIN)
    oauth_client = OAuth1Session(consumer_key, client_secret=consumer_secret,
                                 resource_owner_key=resp.get('oauth_token'),
                                 resource_owner_secret=resp.get('oauth_token_secret'),
                                 verifier=PIN
    )
    try:
        resp = oauth_client.fetch_access_token(ACCESS_TOKEN_URL)
    except ValueError, e:
         return 1
    xbmc.log("Twitter: Setze oauth"   )
    xbmc.log("Twitter Token : " + resp.get('oauth_token'))
    xbmc.log("Twitter Secret : "+ resp.get('oauth_token_secret'))
    
    global oauth_token
    global oauth_token_secret
    oauth_token= resp.get('oauth_token')
    oauth_token_secret=resp.get('oauth_token_secret')
    
    #Speicher Token fürs naechste mal
    f = open( os.path.join(temp,"init.ok"), 'w')
    zeile="oauth_token: "+ oauth_token +"#"    
    f.write(zeile)
    zeile="oauth_token_secret: "+ oauth_token_secret +"#"
    f.write(zeile)
    f.close()    


def repace_it(was,replace_array,search_array):
    was=was.lower()
    for  suche,ersetze in replace_array:
      was=was.replace(suche,ersetze)
    debug("1. repace_channels :" + was)
    for  suche,ersetze in search_array:
      debug("suche :"+ suche)
      debug("ersetze :"+ ersetze)
      if  suche in was:
        was=ersetze
    debug("2.repace_channels :" + was)
    return was
    
def block(text,blacklist):
    text=text.encode('utf-8')
    debug("Blacklist"+ blacklist)
    debug("Text zu durchsuchen ist :" +text)
    blacklist_array=blacklist.split(",")
    if blacklist and blacklist!="":
       for blocked in blacklist_array:
           debug("Block Wort " + blocked + "#")
           if blocked.lower() in text.lower() and not blocked == "":
              debug("Gebloggt wegen : "+ blocked)
              return True
    return False
def readersetzen():
  global listtype
  global listurl
  global listfile
  debug("Start Readersetzen")
  channelr=[]
  channels=[]
  sendungs=[]
  sendungr=[]
  videos=[]
  videor=[]
  content=""
  if listtype=="File":
    if not listfile == "":
      fp=open(listfile,"r")
    else:
       filename = os.path.join(__addondir__,"filter.txt")
       fp=open(filename,"r") 
    content=fp.read()
  else :
    content=geturl(listurl)
  if not content=="":
    debug("Content Da")
    match=re.compile(':([^:]+):([^:]+):"([^"]*)"="([^"]*)"', re.DOTALL).findall(content)  
    for type,mode,suche,ersetze in match:
       debug("XXXXY #"+ type +"# --> #"+ mode + "# WAS: "+ suche + "-->"+ ersetze)
       if type=="channel" and mode=="replace" :
         channelr.append([suche,ersetze])
       if type=="channel" and mode=="isin" :
         channels.append([suche,ersetze])
       if type=="show" and mode=="replace" :
         sendungr.append([suche,ersetze])
       if type=="show" and mode=="isin" :
         sendungs.append([suche,ersetze])
       if type=="video" and mode=="replace" :
         videor.append([suche,ersetze])
       if type=="video" and mode=="isin" :
         videor.append([suche,ersetze])
  return channelr,channels,sendungr,sendungs,videor,videos
    
def lesetext(blacklist,tweets,textarray,idarray,imagearray,sinceid)  :
    for tweet in tweets:  
         text= tweet.user.name +" : "+ tweet.text.replace("\n"," ")
         if  tweet.id > sinceid :
             sinceid=tweet.id              
             debug("Neue Tweet ID " + str(tweet.id))         
         if not block(text,blacklist) : 
               debug("Tweet ok")         
               if bild=="true":
                   userimage=tweet.user.profile_image_url    
               else :
                   userimage=""   
               debug("Tweet ID " + str(tweet.id))
               if not text in textarray:             
                  textarray.append(text)
                  idarray.append(tweet.id)   
                  imagearray.append(userimage)             
         else:
             debug("Gebannt Thread")
    if len(textarray) >0:
       idarray,textarray,imagearray = (list(x) for x in zip(*sorted(zip(idarray,textarray,imagearray))))                                              
    return textarray,idarray,imagearray,sinceid
    
if __name__ == '__main__':
    xbmc.log("Twitter:  Starte Plugin")

    start=1   
    heute=0
    #Directory für Token Anlegen
    if not xbmcvfs.exists(temp):       
       xbmcvfs.mkdirs(temp)
    if not xbmcvfs.exists( os.path.join(temp,"init.ok")) and  __addon__.getSetting("clear")!="CLEARIT": 
       f = open( os.path.join(temp,"init.ok"), 'w')    
       f.close() 
    # Starte Service    
    monitor = xbmc.Monitor()
    search=""
    sinceid1=None    
    sinceid2=None    
    sinceid3=None    
    sinceid4=None    
    
    # Solange der Service läuft
    searchold=""
    ratetag=0
    while not monitor.abortRequested():
      ratetag=ratetag+1
      xbmc.log("Hole Umgebung")
      country=__addon__.getSetting("country").lower()        
      limit=__addon__.getSetting("limit")         
      alles_anzeige=__addon__.getSetting("alles_anzeige")   
      hashtag=__addon__.getSetting("hashtag") 
      bild=__addon__.getSetting("bild") 
      Timeline_s=__addon__.getSetting("Timeline_s")
      Hash_s=__addon__.getSetting("Hash_s")
      Video_s=__addon__.getSetting("Video_s")
      tv=__addon__.getSetting("tv")
      video=__addon__.getSetting("video")
      urlfilter=__addon__.getSetting("urls")
      lesezeit=__addon__.getSetting("lesezeit")
      greyout=__addon__.getSetting("greyout")
      blacklist=__addon__.getSetting("blacklist")
      listtype=__addon__.getSetting("listtype")
      listurl=__addon__.getSetting("listurl")
      listfile=__addon__.getSetting("listfile")  
      xmessage=__addon__.getSetting("x-message")  
      ymessage=__addon__.getSetting("y-message")  
      hoehemessage=__addon__.getSetting("hoehe-message")  
      breitemessage=__addon__.getSetting("breite-message")  
      hoehebild=__addon__.getSetting("hoehe-bild")  
      breitebild=__addon__.getSetting("breite-bild")  
      font=__addon__.getSetting("font")  
      fontcolor=__addon__.getSetting("fontcolor")  
      if listfile=="":
         filename = os.path.join(__addondir__,"filter.txt")
         __addon__.setSetting(id="listfile", value=filename)
      old_heute=heute         
      heute=time.localtime(time.time())[2]      
      if heute!= old_heute:
         channelr,channels,sendungr,sendungs,videor,videos=readersetzen()         
      if Video_s=='true' or Hash_s=='true':
          if Video_s=='true' and Hash_s=='true':
            ratlimit=20
            ratetag=ratetag+20
          else:
            ratlimit=8
            ratetag=ratetag+8
      else :
            ratlimit=70
            ratetag=ratetag+70

      debug("Ratelimit "+ str(ratlimit))
      if start==0:
        debug("Pause wegen Rate Limit")
        if monitor.waitForAbort(ratlimit):
          break      
      start=0
      
      # Wenn kein Token oder Authentifizerung löschen wurde Neu Authentifizieren
      if not xbmcvfs.exists( os.path.join(temp,"init.ok")) or __addon__.getSetting("clear")=="CLEARIT": 
        debug("Starte neue Authentifizierung")
        try:      
          get_access_token(consumer_key, consumer_secret)       
          continue
        except :
          debug("Neue Token Holen Fehlgeschlagen")
          continue
      else:         
          # Alten Token Laden
          debug("Lese Token aus File")
          f=xbmcvfs.File( os.path.join(temp,"init.ok"),"r")   
          daten=f.read()
          if daten=="":
            continue
          match=re.compile('oauth_token: ([^#]+)', re.DOTALL).findall(daten)
          oauth_token=match[0]
          match=re.compile('oauth_token_secret: ([^#]+)', re.DOTALL).findall(daten)
          oauth_token_secret=match[0]              
          
          debug("Twitter: Starte Auth")  
          try:         
            api = twitter.Api(consumer_key=consumer_key,consumer_secret=consumer_secret,access_token_key=oauth_token,access_token_secret=oauth_token_secret)                 
          except :
            debug("ERROR Authentifizierung klappt nicht")   
            continue            
      


      if Video_s=='true' and  video=="true" and xbmc.getCondVisibility('Player.HasMedia') and not xbmc.getCondVisibility('Pvr.IsPlayingTv'):
         title=""
         title=xbmc.getInfoLabel('VideoPlayer.TVShowTitle') 
         debug("Title :" + title)
         if title=="":           
             title=xbmc.getInfoLabel('VideoPlayer.Title') 
             if title=="":
                 continue             
         title=title.lower()
         match=re.compile('([^-]+)', re.DOTALL).findall(title)
         if match:
            title=match[0]
         match=re.compile('([^:]+)', re.DOTALL).findall(title)
         if match:
            title=match[0]
         title=repace_it(title,videor,videos)  
         search="#" + title
         debug("Video:")
         debug ("Search : "+ search)
      if Video_s=='true' and  tv=="true" and xbmc.getCondVisibility('Pvr.IsPlayingTv'):
        # Nur wenn ein Fernsehnder an ist          
        xbmc.log("Hole Ferseh tweets")
        
        now = xbmc.getInfoLabel('Player.Title')
        channel = xbmc.getInfoLabel('VideoPlayer.ChannelName')        
        
        if channel=="" :
             continue
             
        channel=repace_it(channel,channelr,channels)
        now=repace_it(now,sendungr,sendungs)     
        
        if now :
          search="#"+ channel +" OR "+ "#"+ now
        else:
           search="#"+ channel                     
      
      if Hash_s=='true':
          if hashtag :
              xbmc.log("#Hastag :" + hashtag)
              searchh=hashtag
          else:
             xbmc.log("Setze Kodi")
             searchh="kodi"
      
      if   country=="" :
           country=None    
      if not searchold==search:
          searchold=search  
          try:          
            popupwindow.deletemessage(__addon__)
          except:
             pass
      x=0
      tweets1=[]
      tweets2=[]
      tweets3=[]
      tweets4=[]
      try:       
         debug ("-------")
         if Video_s=="true" and tv=="true" and xbmc.getCondVisibility('Pvr.IsPlayingTv'):   
               debug("Search TV: "+ search)
               debug("Hole TV")
               x=1
               tweets1=api.GetSearch(search,since_id=sinceid1,lang=country,result_type="recent")
               debug("Search: "+ search)
         elif Video_s=="true" and video=="true":    
               debug("Search Video: "+ search)         
               debug("Hole Video")
               x=1
               tweets3=api.GetSearch(search,since_id=sinceid3,lang=country,result_type="recent")               
               debug("Search: "+ search)               
         if Hash_s=='true':
               debug("Hole Hashtag")
               x=1
               tweets2=api.GetSearch(searchh,since_id=sinceid2,lang=country,result_type="recent")
               debug("Search: "+ searchh)
         if ratetag>=70:
          ratetag=0
          if Timeline_s=="true":
              debug("Hole Timeline")
              x=1
              tweets4 = api.GetHomeTimeline(since_id=sinceid4)             
              debug("TWEE :")
              search=""
         if x==0:
              tweets=[]
         if search:
            debug ("Search: " +search)
      except Exception as e:
          debug("Tweets Holen Fehlerhaft")    
          debug(e)          
          continue
      textarray=[]
      idarray=[]
      imagearray=[]
      tweets=tweets1+tweets2+tweets3+tweets4       
      textarray,idarray,imagearray,sinceid1=lesetext(blacklist,tweets1,textarray,idarray,imagearray,sinceid1)      
      textarray,idarray,imagearray,sinceid2=lesetext(blacklist,tweets2,textarray,idarray,imagearray,sinceid2)      
      textarray,idarray,imagearray,sinceid3=lesetext(blacklist,tweets3,textarray,idarray,imagearray,sinceid3)      
      textarray,idarray,imagearray,sinceid4=lesetext(blacklist,tweets4,textarray,idarray,imagearray,sinceid4)                                                            
      if len(textarray) >0:          
          for i in range(len(textarray)):              
              popupwindow.savemessage(__addon__,textarray[i],imagearray[i],greyout,lesezeit,xmessage,ymessage,breitemessage,hoehemessage,breitebild,hoehebild,font,fontcolor)                  
      
