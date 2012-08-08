#!/usr/bin/python
# -*- coding: utf-8 -*-
import urllib,urllib2,re,xbmc,xbmcgui,xbmcplugin,sys,os,xbmcaddon,string

import SimpleDownloader as downloader
downloader = downloader.SimpleDownloader()


# plugin constants
__plugin__ = "mp3search"
__author__ = "ghua@seznam.cz"
__url__ = ""
__version__ = "0.2.1"



__settings__ = xbmcaddon.Addon(id='plugin.audio.mp3search')
__language__ = __settings__.getLocalizedString
__home__ = __settings__.getAddonInfo('path')
__profile__=xbmc.translatePath(__settings__.getAddonInfo('profile') ).decode('utf-8')
__icons__=os.path.join(__home__,'resources')
icon = xbmc.translatePath( os.path.join( __home__, 'icon.png' ) )
searchicon = xbmc.translatePath( os.path.join( __home__,'resources', 'search.png' ) )
playicon = xbmc.translatePath( os.path.join( __home__,'resources', 'play.png' ) )
downloadpath= __settings__.getSetting('download_path')#__profile__
phomepath=xbmc.translatePath( os.path.join( __home__, 'default.py' ) )
debug=False

def replaceUrl(url):
        a=string.replace(url,"%3A",":")
        a=string.replace(a,"%2F","/")
        return a

def replaceUrlSpecial(url):
        a=string.replace(url,"%3A",":")
        a=string.replace(a,"%2F","/")
        a=string.replace(a,"+","%20")
        a=string.replace(a,"%2520","%20")
        return a

def getPageParam(page,param):
    h=re.compile(param+'.+\s+<.+').findall(page)
    if (len(h))>0:
        g=re.compile('>([^<>\n\r]+)<').findall(h[0])
        if (len(g))>0:
            return g[0]
        else:
            return 'N/A'
    else:
        return 'N/F'


def downloadAudio(urlx,title,targetpath):
        paramsd = { "url": replaceUrlSpecial(urlx), "download_path": targetpath, "Title": title }
        downloader.download(title+'.mp3', paramsd)



def addLink(name, artist, album, mode, urlx, desc, descfile, duration, iconimage,icolor=None):
        u=sys.argv[0]+"?url="+urllib.quote_plus(replaceUrl(urlx))+"&mode="+urllib.quote_plus(str(mode))+"&cmd="+urllib.quote_plus(replaceUrl(urlx))+"&name="+urllib.quote_plus(name)+"&desc="+urllib.quote_plus(desc)+"&iconimage="+urllib.quote_plus(replaceUrl(iconimage))
        ok=True
        if icolor != None:
                liz=xbmcgui.ListItem(label="[COLOR FF" + icolor + "]" + name + "[/COLOR]", iconImage=iconimage, thumbnailImage=iconimage)
        else:
                liz=xbmcgui.ListItem(name, iconImage=iconimage, thumbnailImage=iconimage)
                
        liz.setInfo( type="Music", infoLabels={ "Title": name, 'artist': artist, 'album': album, 'Comment': desc, 'Duration': duration, 'File': descfile } )
        contextMenu = [(__language__(30009),'XBMC.RunScript('+phomepath+',0,"?mode=down&url='+urllib.quote_plus(urlx)+'&desc=&name='+name+'&cmd=down")')]
        liz.addContextMenuItems(contextMenu)
        
        liz.setProperty("IsPlayable","true")
        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=urlx,listitem=liz,isFolder=False)



def addDir(name, url, mode, cmd, desc, iconimage,icolor=None):
        u=sys.argv[0]+"?url="+urllib.quote_plus(replaceUrl(url))+"&mode="+urllib.quote_plus(str(mode))+"&cmd="+urllib.quote_plus(str(cmd))+"&name="+urllib.quote_plus(name)+"&desc="+urllib.quote_plus(desc)+"&iconimage="+urllib.quote_plus(replaceUrl(iconimage))
        ok=True
        if icolor != None:
                liz=xbmcgui.ListItem(label="[COLOR FF" + icolor + "]" + name + "[/COLOR]", iconImage=iconimage, thumbnailImage=iconimage)
        else:
                liz=xbmcgui.ListItem(name, iconImage=iconimage, thumbnailImage=iconimage)
                
        liz.setInfo( type="Audio", infoLabels={ "Title": name, "Plot": desc } )
        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)
        


# Get a search query from keyboard
def readKbd(default):
  kb = xbmc.Keyboard(default,__language__(30006), False)
  kb.doModal()
  if (kb.isConfirmed() and len(kb.getText()) > 2):
    return kb.getText()

#read dat file
def getDatFile(dfilepath):
        if os.path.isfile(__profile__ + dfilepath):
                fi=open(__profile__ + dfilepath,"r")
                ar=fi.read()
                ap=string.split(ar,";")
                fi.close()
                return ap
        else:
                return None
                

#save dat file
def saveDatFile(dfilepath,searched):
        if not os.path.isdir(__profile__):
                os.mkdir(__profile__)
        ar=string.join(searched,";")
        ar=string.replace(ar,";;",";")
        fi=open(__profile__ + dfilepath,"w")
        fi.write(ar)
        fi.close()
        


# Read command-line parameters
def getParams():
  param=[]
  paramstring=sys.argv[2]
  if len(paramstring)>=2:
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




#fill up searched
def fillSearched():
        ax=getDatFile("searched.dat")
        try:
                
                if len(ax)>0:
                        for sidx in range(len(ax)):
                                addDir(ax[sidx],'','searched-item','','',searchicon)
                                
        except:
                pass
        xbmcplugin.endOfDirectory(int(sys.argv[1]))



#do search
def doSearch(fquery,fpage,isave=True):

        asearched=[]
        
        req = urllib2.Request('http://togrool.com/search.xhtml?query='+fquery+'&searchtype=mp3&page='+str(fpage)+'&source=page')
        req.add_header('User-Agent', ' Mozilla/5.0 (Windows NT 5.1; rv:13.0) Gecko/20100101 Firefox/13.0.1')
        req.add_header('Cache-Control',' no-cache')
        req.add_header('Connection',' close')


        try:
                response = urllib2.urlopen(req)
                link=response.read()
                response.close()
                match=re.compile('<a href="http://togrool.com/download(.+?)\?').findall(link)

                if isave:                        
                        asearched=getDatFile("searched.dat")
                        if asearched == None:
                                asearched=[fquery]
                        else:
                                asearched.append(fquery)
                        
                        saveDatFile("searched.dat",asearched)


                for i in range(len(match)):

                        req = urllib2.Request('http://togrool.com/download'+match[i])
                        req.add_header('User-Agent', ' Mozilla/5.0 (Windows NT 5.1; rv:13.0) Gecko/20100101 Firefox/13.0.1')
                        req.add_header('Cache-Control',' no-cache')
                        req.add_header('Connection',' keep-alive')

                        try:
                                response = urllib2.urlopen(req)
                                link=response.read()
                                response.close()
                                match1=re.compile('<param name="FlashVars" value="mp3=(.+?\.mp3)').findall(link) #target mp3
                                match2=re.compile('<img src="(.+?)"').findall(link) #target icon
                                if (len(match1))>0:
                                        
                                        if (len(match2))>0:
                                                icn=match2[0]
                                        else:
                                                icn=playicon
                                                               
                                        informations = '[COLOR FF80AA20]Downloads:' + getPageParam(link,'Downloads:') + '[/COLOR]  [COLOR FF00CCCC]Rating:' + getPageParam(link,'Rating:') + '[/COLOR] [COLOR FFAA4020]Size:' + getPageParam(link,'Size:') + '[/COLOR]  [COLOR FFCC00CC]Duration:' + getPageParam(link,'Duration:')+ '[/COLOR]  [COLOR FF0080CC]Lyrics:' + getPageParam(link,'Lyrics:')+ '[/COLOR]  [COLOR FF20EE20]Bitrate:' + getPageParam(link,'Bitrate:') + '[/COLOR] '
                                        addLink(getPageParam(link,'Band name:')+' - '+getPageParam(link,'Song name:'),getPageParam(link,'Band name:'),getPageParam(link,'Album name:'),"play", replaceUrlSpecial(match1[0]), informations,'','12:34',icn)

                        except urllib2.URLError, e:
                                pass
                               
     
                addDir('>> '+__language__(30005)+' >>','','searchnext',fquery,str(fpage+1),'DefaultFolder.png',"FF80FF")
                xbmcplugin.endOfDirectory(int(sys.argv[1]))
                #Container.SetViewMode(id)


            
    
        except urllib2.URLError, e:
                pass
            



# Main -------------------------------------------------------------------------------------------------
params=getParams()

mode=''
param1=''
param2=''
namet=''
buurl=''

try:
  
  buurl = params["url"]
  mode = params["mode"]
  param1 = params["cmd"]
  param2 = params["desc"]
  namet = params["name"]      
             
except:
  mode = ''


# Menu stuff
if mode == "search":
  a_query = readKbd("")
  if a_query != None:
          doSearch(a_query,1,True)
          #sort()

elif mode == "searched-item":
  a_query = readKbd(namet)
  if a_query != None:
          doSearch(a_query,1,False)


elif mode=='searched':
        fillSearched()

elif mode == "searchnext":
  doSearch(param1,int(param2),False)
    
elif mode=='down':
        downloadAudio(buurl,namet,downloadpath)

else:
  addDir(__language__(30000)+' >','','search','','','DefaultFolder.png')
  addDir(__language__(30001)+' >','','searched','','','DefaultFolder.png')
  
  xbmcplugin.endOfDirectory(int(sys.argv[1])) 

