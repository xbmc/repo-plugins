#!/usr/bin/python
# -*- coding: utf-8 -*-
import urllib,urllib2,re,xbmc,xbmcgui,xbmcplugin,sys,os,xbmcaddon,string

# plugin constants
__plugin__ = "mp3search"
__author__ = "ghua@seznam.cz"
__url__ = ""
__version__ = "0.1"



__settings__ = xbmcaddon.Addon(id='plugin.audio.mp3search')
__language__ = __settings__.getLocalizedString
__home__ = __settings__.getAddonInfo('path')
__profile__=xbmc.translatePath(__settings__.getAddonInfo('profile') ).decode('utf-8')
__icons__=os.path.join(__home__,'resources')
icon = xbmc.translatePath( os.path.join( __home__, 'icon.png' ) )
searchicon = xbmc.translatePath( os.path.join( __home__,'resources', 'search.png' ) )
playicon = xbmc.translatePath( os.path.join( __home__,'resources', 'play.png' ) )


def replaceUrl(url):
        a=string.replace(url,"%3A",":")
        a=string.replace(a,"%2F","/")
        return a


def addLink(name, mode, url, desc, duration, iconimage,icolor=None):
        u=sys.argv[0]+"?url="+urllib.quote_plus(replaceUrl(url))+"&mode="+urllib.quote_plus(str(mode))+"&cmd="+urllib.quote_plus(replaceUrl(url))+"&name="+urllib.quote_plus(name)+"&desc="+urllib.quote_plus(desc)+"&iconimage="+urllib.quote_plus(replaceUrl(iconimage))
        ok=True
        if icolor != None:
                liz=xbmcgui.ListItem(label="[COLOR FF" + icolor + "]" + name + "[/COLOR]", iconImage=iconimage, thumbnailImage=iconimage)
        else:
                liz=xbmcgui.ListItem(name, iconImage=iconimage, thumbnailImage=iconimage)
                
        liz.setInfo( type="Music", infoLabels={ "Title": name, "Plot": desc, "Duration": duration } )
        liz.setProperty("IsPlayable","false")
        
        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=False)



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
def readKbd():
  kb = xbmc.Keyboard("",__language__(30006), False)
  kb.doModal()
  if (kb.isConfirmed() and len(kb.getText()) > 2):
    return kb.getText()

# Play a link
def playLink(listen_url,lstItem=None,isave=True):

        if isave:                
                aplayed=getDatFile("played.dat")
                if aplayed == None:
                        aplayed=[listen_url]
                else:
                        aplayed.append(listen_url)
                        
                saveDatFile("played.dat",aplayed)                
        xbmc.Player().play(replaceUrl(listen_url),lstItem)


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
        #1.nacist
        ax=getDatFile("searched.dat")
        try:
                
                if len(ax)>0:
                        for sidx in range(len(ax)):
                                addDir(ax[sidx],'','searched-item','','',searchicon)
                                
        except:
                pass
        xbmcplugin.endOfDirectory(int(sys.argv[1]))


#fill up searched
def fillPlayed():
        #1.load file
        ax=getDatFile("played.dat")
        try:
                
                if len(ax)>0:
                        for sidx in range(len(ax)):
                                m=re.compile("downloadmp3-(.+?)\.xhtml").findall(ax[sidx])
                                addLink(m[0],"played-item", ax[sidx], '','unknown', playicon,"8080FF")
                                
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
          match2=re.compile('<div class="img"><img src="(.+?)"').findall(link)
          match3=re.compile('<div class="item-title">(.+?)<.+?>(.+?)<').findall(link)
    
          kusurl='http://togrool.com/downloadmp3'


          if len(match)==0:
                #xbmc.executebuiltin('XBMC.Notification("'+__language__(30003)+'","'+__language__(30004)+'",5000,"'+icon+'")')
                pass
          else:
                if isave:
                        
                        asearched=getDatFile("searched.dat")
                        if asearched == None:
                                asearched=[fquery]
                        else:
                                asearched.append(fquery)
                        
                        saveDatFile("searched.dat",asearched)
                  

        
                for idx in range(0,len(match)):
                        addLink(match3[idx][0]+match3[idx][1],"play", kusurl+match[idx], '','unknown', match2[idx])

                          
                addDir('>> '+__language__(30005)+' >>','','searchnext',fquery,str(fpage+1),'DefaultFolder.png',"FF80FF")
                      
          xbmcplugin.endOfDirectory(int(sys.argv[1])) 

        except urllib2.URLError, e:
            dlg=xbmcgui.Dialog()
            tdlg=dlg.ok(__language__(30007),__language__(30007)+' '+str(e.code),'') 
            

# Main ----------------------------------------------------
params=getParams()

try:
  mode = params["mode"]
  param1 = params["cmd"]
  param2 = params["desc"]
  namet = params["name"]      


  
except:
  mode = 0 


# Menu stuff
if mode == "search":
  a_query = readKbd()
  if a_query != None:
          doSearch(a_query,1,True)
          #sort()

elif mode == "searched-item":
  a_query = namet
  doSearch(a_query,1,False)


elif mode=='searched':
        fillSearched()

elif mode=='played':
        fillPlayed()

elif mode=='played-item':
        playLink(param1,None,False)

elif mode=='play':
        playLink(param1,None,True)

elif mode == "searchnext":
  doSearch(param1,int(param2),False)
    
elif mode=='down':
        saveAudioFile(param1,__profile__)


else:
  addDir(__language__(30000)+' >','','search','','','DefaultFolder.png')
  addDir(__language__(30001)+' >','','searched','','','DefaultFolder.png')
  addDir(__language__(30002)+' >','','played','','','DefaultFolder.png')
  


  xbmcplugin.endOfDirectory(int(sys.argv[1])) 


