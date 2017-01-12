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


import ssl

try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    # Legacy Python that doesn't verify HTTPS certificates by default
    pass
else:
    # Handle target environment that doesn't support HTTPS verification
    ssl._create_default_https_context = _create_unverified_https_context

# Setting Variablen Des Plugins
global debuging
base_url = sys.argv[0]
addon_handle = int(sys.argv[1])

args = urlparse.parse_qs(sys.argv[2][1:])
addon = xbmcaddon.Addon()
# Lade Sprach Variablen
translation = addon.getLocalizedString
defaultBackground = ""
defaultThumb = ""
cliplist=[]
filelist=[]
profile    = xbmc.translatePath( addon.getAddonInfo('profile') ).decode("utf-8")
temp       = xbmc.translatePath( os.path.join( profile, 'temp', '') ).decode("utf-8")
#Directory für Token Anlegen
if not xbmcvfs.exists(temp):       
       xbmcvfs.mkdirs(temp)
       
xbmcplugin.setContent(int(sys.argv[1]), 'musicvideos')
icon = xbmc.translatePath(xbmcaddon.Addon().getAddonInfo('path')+'/icon.png').decode('utf-8')
useThumbAsFanart=addon.getSetting("useThumbAsFanart") == "true"



def debug(content):
    log(content, xbmc.LOGDEBUG)
    
def notice(content):
    log(content, xbmc.LOGNOTICE)

def log(msg, level=xbmc.LOGNOTICE):
    addon = xbmcaddon.Addon()
    addonID = addon.getAddonInfo('id')
    xbmc.log('%s: %s' % (addonID, msg), level) 

def parameters_string_to_dict(parameters):
  paramDict = {}
  if parameters:
    paramPairs = parameters[1:].split("&")
    for paramsPair in paramPairs:
      paramSplits = paramsPair.split('=')
      if (len(paramSplits)) == 2:
        paramDict[paramSplits[0]] = paramSplits[1]
  return paramDict
  
    
def addDir(name, url, mode, iconimage, desc=""):
  u = sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)
  ok = True
  liz = xbmcgui.ListItem(name, iconImage=icon, thumbnailImage=iconimage)
  liz.setInfo(type="Video", infoLabels={"Title": name, "Plot": desc})
  if useThumbAsFanart:
    if not iconimage or iconimage==icon or iconimage==defaultThumb:
      iconimage = defaultBackground    
    liz.setArt({ 'fanart': iconimage })
  else:
    liz.setArt({ 'fanart': defaultBackground })  
  xbmcplugin.setContent(int(sys.argv[1]), 'musicvideos')
  ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=True)
  return ok
  
def addLink(name, url, mode, iconimage, duration="", desc="",artist_id="",genre="",shortname="",production_year=0,zeit=0,liedid=0):  
  cd=addon.getSetting("password")  
  u = sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)
  ok = True
  liz = xbmcgui.ListItem(name, iconImage=defaultThumb, thumbnailImage=iconimage)
  liz.setInfo(type="Video", infoLabels={"Title": name, "Plot": desc, "Genre": genre,"Sorttitle":shortname,"Dateadded":zeit,"year":production_year })
  liz.setProperty('IsPlayable', 'true')
  liz.addStreamInfo('video', { 'duration' : duration })
  liz.setArt({ 'fanart': iconimage }) 
  xbmcplugin.setContent(int(sys.argv[1]), 'musicvideos')
  commands = []
  listatrist = "plugin://plugin.video.ampya/?mode=songs_from_artist&url="+urllib.quote_plus(str(artist_id))  
  listsimiliar = "plugin://plugin.video.ampya/?mode=list_similiar&url="+urllib.quote_plus(str(liedid))  
  commands.append(( "Mehr vom Künstler" , 'ActivateWindow(Videos,'+ listatrist +')'))
  commands.append(( "Ähnliche Lieder" , 'ActivateWindow(Videos,'+ listsimiliar +')'))
  liz.addContextMenuItems( commands )  
  ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz)
  return ok


def getUrl(url,data="x"):        
        debug("Get Url: " +url)
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor())
        userAgent = "Dalvik/2.1.0 (Linux; U; Android 5.0;)"
        opener.addheaders = [('User-Agent', userAgent)]
        try:
          if data!="x" :
             content=opener.open(url,data=data).read()
          else:
             content=opener.open(url).read()
        except urllib2.HTTPError as e:
             #print e.code   
             cc=e.read()  
             struktur = json.loads(cc)  
             error=struktur["errors"][0] 
             error=unicode(error).encode("utf-8")
             debug("ERROR : " + error)
             dialog = xbmcgui.Dialog()
             nr=dialog.ok("Error", error)
             return ""
             
        opener.close()
        return content


      #addDir(namenliste[i], namenliste[i], mode+datum,logoliste[i],ids=str(idliste[i]))
   #xbmcplugin.endOfDirectory(addon_handle,succeeded=True,updateListing=False,cacheToDisc=True)   

def ListeChannels(url):
  content=getUrl(url)
  struktur = json.loads(content)
  for element in struktur:   
    title=element["asset"]["title"]
    kuenstler_name=element["asset"]["display_artist_title"]
    kuenstler_id=element["asset"]["artist_id"]
    video_file_id=element["asset"]["video_file_id"]
    Token=element["asset"]["token"]
    duration=element["asset"]["duration"]
    iconimage=getbild(video_file_id)
    id=element["asset"]["id"]

    
    
    debug("VIDEOID: "+str(video_file_id))
    debug("iconimage :"+iconimage)
    
    
    addLink(title +"("+kuenstler_name+")", Token, "playvideo", iconimage, duration=duration, desc="",artist_id=kuenstler_id,liedid=id)
    debug("--------------")
  xbmcplugin.endOfDirectory(addon_handle,succeeded=True,updateListing=False,cacheToDisc=True)   

def getbild(video_file_id):
    longid="%07d"%video_file_id
    einsbisdrei=str(longid)[0:5]
    iconimage="http://files.putpat.tv/artwork/posterframes/"+ einsbisdrei +"/" + longid +"/v"+longid+"_posterframe_putpat_large.jpg"
    return iconimage
    
def ListeVideos(url):
  content=getUrl(url)
  struktur = json.loads(content)
  for element in struktur:   
    title=element["asset"]["title"]
    kuenstler_name=element["asset"]["display_artist_title"]
    kuenstler_id=element["asset"]["artist_id"]
    video_file_id=element["asset"]["video_file_id"]
    Token=element["asset"]["token"]
    #duration=element["asset"]["duration"]
    iconimage=getbild(video_file_id)
    id=element["asset"]["id"]
    
    debug("VIDEOID: "+str(video_file_id))
    debug("iconimage :"+iconimage)
    
    
    addLink(title +"("+kuenstler_name+")", Token, "playvideo", iconimage, desc="",artist_id=kuenstler_id,liedid=id)
    debug("--------------")
  xbmcplugin.endOfDirectory(addon_handle,succeeded=True,updateListing=False,cacheToDisc=True)   

def Playvideo(token):
  file="https://www.putpat.tv/ws.json?method=Asset.getClipForToken&token="+token+"&streaming_method=http&client=android_phone&player_id=2"
  content=getUrl(file)
  struktur = json.loads(content)
  file2=struktur[0]["clip"]["tokens"]["medium"]
  debug("File2 : "+file2)
  listitem = xbmcgui.ListItem(path=file2)  
  xbmcplugin.setResolvedUrl(addon_handle,True, listitem)  

def Listekanaele(url):
  content=getUrl(url)
  struktur = json.loads(content)
  for name in struktur:
   debug("....")
   debug(name["channel"])
   debug("....")
   id=name["channel"]["id"]
   title=name["channel"]["title"]
   addLink(title , str(id), "playKanal", "http://files.putpat.tv/artwork/channelgraphics/"+str(id)+"/channellogo_150.png")
  xbmcplugin.endOfDirectory(addon_handle,succeeded=True,updateListing=False,cacheToDisc=True) 
  
def monitor_playlist(url,id)   :
    global playlist
    global cliplist
    counter=0
    counter2=0
    while counter2<5:
        while xbmc.Player().isPlaying():
            counter2=0
            if counter > 120:
                debug("Suche neue Clips")
                clipseinlesen(url,id)        
                counter=0
            time.sleep(1)
            counter=counter+1    
        time.sleep(1)
        counter2=counter2+1    
        

      
        
def clipseinlesen(url,id):
    content=getUrl(url)
    struktur = json.loads(content)
    global cliplist
    global filelist
    global playlist  
    for name in struktur:
      debug("-------")
      #debug(name["channel"])
      debug("Such iD : "+ id)
      ids=name["channel"]["id"]
      debug("iD : "+ str(ids))
      if int(id)==int(ids):
        for clip in name["channel"]["clips"]:
           debug("-----XX-------")    
           debug(clip)           
           urln=clip["clip"]["tokens"]["medium"]
           debug(urln)
           try:
              artist=clip["clip"]["asset"]["artist"]["title"].encode("utf-8")
           except:
              artist=""
           title=clip["clip"]["asset"]["title"] .encode("utf-8")
           clipid=clip["clip"]["video_file_id"]           
           bild=getbild(clipid)
           if not clipid in cliplist:
             debug("Adde Clib : "+artist + ' - ' + title)
             listItem = xbmcgui.ListItem(artist + ' - ' + title, thumbnailImage = bild)
             playlist.add(urln, listItem)
             cliplist.append(clipid)   
             filelist.append(url)
           
def playKanal(url,id):
    global cliplist       
    global playlist    
    playlist = xbmc.PlayList(1)
    playlist.clear() 
    cliplist=[]
    debug("Playliste gelöscht")
    clipseinlesen(url,id)    
    xbmc.Player().play(playlist)     
    #monitor_playlist(url,id)    

def Search():
     dialog = xbmcgui.Dialog()
     d = dialog.input(translation(30010), type=xbmcgui.INPUT_ALPHANUM)
     d=urllib.quote(d, safe='')
     content=getUrl("https://www.putpat.tv/ws.json?method=Asset.quickbarSearch&searchterm="+d+"&client=android_phone&player_id=2")
     struktur = json.loads(content)
     result=struktur["quickbar_search"]
     videos=result["music_videos"]  
     artists=result["artists"]     
     if len(artists)>0:
       addDir("Künstler",d, "list_artists", "")           
     if len(videos)>0:
        addDir("Lieder",d, "list_songs", "")    
     xbmcplugin.endOfDirectory(addon_handle,succeeded=True,updateListing=False,cacheToDisc=True)  
     
def list_songs(url):     
    debug("list_artists")
    content=getUrl("https://www.putpat.tv/ws.json?method=Asset.quickbarSearch&searchterm="+url+"&client=android_phone&player_id=2")
    struktur = json.loads(content)
    result=struktur["quickbar_search"]
    videos=result["music_videos"]    
    for video in videos:     
      Token=video["token"]
      kuenstler_name=video["display_artist_title"]
      title=video["title"]
      kuenstler_id=video["artist_id"]
      video_file_id=video["video_file_id"]
      iconimage=getbild(video_file_id)
      id=video["id"]
      addLink(title +"("+kuenstler_name+")", Token, "playvideo", iconimage, desc="",artist_id=kuenstler_id,liedid=id)      
    xbmcplugin.endOfDirectory(addon_handle,succeeded=True,updateListing=False,cacheToDisc=True)      
     
def list_artists(url):     
    debug("list_artists")
    content=getUrl("https://www.putpat.tv/ws.json?method=Asset.quickbarSearch&searchterm="+url+"&client=android_phone&player_id=2")
    struktur = json.loads(content)
    result=struktur["quickbar_search"]
    videos=result["music_videos"]
    artists=result["artists"]
    for artist in artists:     
        addDir(artist["title"],str(artist["id"]), "songs_from_artist", "")        
    xbmcplugin.endOfDirectory(addon_handle,succeeded=True,updateListing=False,cacheToDisc=True)   
def songs_from_artist(id):
    ListeVideos("https://www.putpat.tv/ws.json?method=Artist.assetsByArtistId&artistId="+id+"&client=android_phone&player_id=2")
def list_similiar(id):
    ListeVideos("https://www.putpat.tv/ws.json?method=Asset.similarAssets&limit=50&assetId="+id+"&client=android_phone&player_id=2")    

params = parameters_string_to_dict(sys.argv[2])
mode = urllib.unquote_plus(params.get('mode', ''))
url = urllib.unquote_plus(params.get('url', ''))

if mode is '':
    addDir(translation(30103), translation(30003), 'Top',"")
    addDir(translation(30104), translation(30004), 'New', "")   
    addDir(translation(30105), translation(30105), 'Empfehlungen', "")  
    addDir(translation(30106), translation(30106), 'Kanaele', "")  
    addDir(translation(30107), translation(30107), 'Suche', "")  
    addDir(translation(30108), translation(30108), 'Settings', "")        
    xbmcplugin.endOfDirectory(addon_handle,succeeded=True,updateListing=False,cacheToDisc=True) 
else:
  # Wenn Settings ausgewählt wurde
  if mode == 'Settings':
          addon.openSettings()
  # Wenn Kategory ausgewählt wurde
  if mode == 'Top':
          ListeVideos("https://www.putpat.tv/ws.json?method=Asset.collection&type=top_rated&client=android_phone&player_id=2") 
  if mode == 'New':
          ListeVideos("https://www.putpat.tv/ws.json?method=Asset.collection&type=new&client=android_phone&player_id=2") 
  if mode == 'Empfehlungen':
          ListeVideos("https://www.putpat.tv/ws.json?method=Asset.similarAssets&limit=20&assetId=1&client=android_phone&player_id=2")    
  if mode == 'Kanaele':
          Listekanaele("https://www.putpat.tv/ws.json?method=Channel.allWithClips&streamingMethod=http&client=android_phone&player_id=2")           
  if mode == 'playvideo':
          Playvideo(token=url) 
  if mode == 'Suche':
          Search() 
  if mode == 'Kanaele':
          Listekanaele("https://www.putpat.tv/ws.json?method=Channel.allWithClips&streamingMethod=http&client=android_phone&player_id=2")              
  if mode == 'playKanal':
          playKanal("https://www.putpat.tv/ws.json?method=Channel.allWithClips&streamingMethod=http&client=android_phone&player_id=2",id=url)              
if mode == 'list_artists':
          list_artists(url) 
if mode == 'list_songs':
          list_songs(url) 
if mode == 'songs_from_artist':     
     songs_from_artist(url)
if mode == 'list_similiar':     
     list_similiar(url)     
