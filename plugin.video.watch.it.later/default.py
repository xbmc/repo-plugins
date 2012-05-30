#!/usr/bin/python
# -*- coding: utf-8 -*-
import xbmc, xbmcplugin, xbmcgui, xbmcaddon, locale, sys, urllib, urllib2, re, os, datetime, base64
from operator import itemgetter

pluginhandle=int(sys.argv[1])

addonID = "plugin.video.watch.it.later"
addon_work_folder=xbmc.translatePath("special://profile/addon_data/"+addonID)
settings = xbmcaddon.Addon(id=addonID)
translation = settings.getLocalizedString

if not os.path.isdir(addon_work_folder):
  os.mkdir(addon_work_folder)

playListFile=xbmc.translatePath("special://profile/addon_data/"+addonID+"/playlist")

playlistsTemp=[]
for i in range(0,4,1):
  playlistsTemp.append(settings.getSetting("pl"+str(i)))
myLocalPlaylists=[]
for pl in playlistsTemp:
  if pl!="":
    myLocalPlaylists.append(pl)
playlistsTemp=[]
for i in range(5,9,1):
  playlistsTemp.append(settings.getSetting("pl"+str(i)))
myOnlinePlaylists=[]
for pl in playlistsTemp:
  if pl!="":
    myOnlinePlaylists.append(pl)

def index():
        addDir(translation(30001),"",'playListMain',"")
        addDir(translation(30002),"",'addCurrentUrl',"")
        xbmcplugin.endOfDirectory(pluginhandle)

def addCurrentUrl():
        playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
        if playlist.getposition()>=0:
          title = playlist[playlist.getposition()].getdescription()
          title = str(datetime.date.today()).replace("-",".") + " - " + title
          url = playlist[playlist.getposition()].getfilename()
          if url.find("http://")==0 or url.find("rtmp://")==0 or url.find("rtmpe://")==0 or url.find("rtmps://")==0 or url.find("rtmpt://")==0 or url.find("rtmpte://")==0 or url.find("mms://")==0 or url.find("plugin://")==0:
            dialog = xbmcgui.Dialog()
            pl = "Online: "+myOnlinePlaylists[dialog.select(translation(30004), myOnlinePlaylists)]
          else:
            dialog = xbmcgui.Dialog()
            pl = str(translation(30003))+": "+myLocalPlaylists[dialog.select(translation(30004), myLocalPlaylists)]
          playlistEntry="###TITLE###="+title+"###URL###="+url+"###PLAYLIST###="+pl+"###END###"
          if os.path.exists(playListFile):
            fh = open(playListFile, 'r')
            content=fh.read()
            fh.close()
            if content.find(playlistEntry)==-1:
              fh=open(playListFile, 'a')
              fh.write(playlistEntry+"\n")
              fh.close()
          else:
            fh=open(playListFile, 'a')
            fh.write(playlistEntry+"\n")
            fh.close()
        else:
          xbmc.executebuiltin('XBMC.Notification(Info:,'+str(translation(30005))+'!,5000)')

def playListMain():
        playlists=[]
        if os.path.exists(playListFile):
          fh = open(playListFile, 'r')
          for line in fh:
            pl=line[line.find("###PLAYLIST###=")+15:]
            pl=pl[:pl.find("###END###")]
            if not pl in playlists:
              playlists.append(pl)
          fh.close()
          for pl in playlists:
            addDir(pl,pl,'showPlaylist',"")
        xbmcplugin.endOfDirectory(pluginhandle)

def showPlaylist(playlist):
        allEntrys=[]
        fh = open(playListFile, 'r')
        all_lines = fh.readlines()
        for line in all_lines:
          pl=line[line.find("###PLAYLIST###=")+15:]
          pl=pl[:pl.find("###END###")]
          url=line[line.find("###URL###=")+10:]
          url=url[:url.find("###PLAYLIST###")]
          title=line[line.find("###TITLE###=")+12:]
          title=title[:title.find("###URL###")]
          if pl==playlist:
            entry=[title,urllib.quote_plus(url)]
            allEntrys.append(entry)
        fh.close()
        allEntrys=sorted(allEntrys, key=itemgetter(0), reverse=True)
        for entry in allEntrys:
          addRemovableLink(entry[0],entry[1],'playVideoFromPlaylist',"",pl)
        xbmcplugin.endOfDirectory(pluginhandle)

def playVideoFromPlaylist(url):
        listitem = xbmcgui.ListItem(path=urllib.unquote_plus(url))
        return xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)

def getUrl(url):
        req = urllib2.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; rv:11.0) Gecko/20100101 Firefox/11.0')
        response = urllib2.urlopen(req,timeout=30)
        link=response.read()
        response.close()
        return link

def parameters_string_to_dict(parameters):
        ''' Convert parameters encoded in a URL to a dict. '''
        paramDict = {}
        if parameters:
            paramPairs = parameters[1:].split("&")
            for paramsPair in paramPairs:
                paramSplits = paramsPair.split('=')
                if (len(paramSplits)) == 2:
                    paramDict[paramSplits[0]] = paramSplits[1]
        return paramDict

def addRemovableLink(name,url,mode,iconimage,playlist):
        u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)
        ok=True
        liz=xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
        liz.setInfo( type="Video", infoLabels={ "Title": name } )
        liz.setProperty('IsPlayable', 'true')
        playlistEntry="###TITLE###="+name+"###URL###="+urllib.unquote_plus(url)+"###PLAYLIST###="+playlist+"###END###"
        liz.addContextMenuItems([('Remove from Playlist', 'XBMC.RunScript(special://home/addons/'+addonID+'/removeFromPlaylist.py,'+urllib.quote_plus(playlistEntry)+')',)])
        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz)
        return ok

def addDir(name,url,mode,iconimage):
        u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)
        ok=True
        liz=xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
        liz.setInfo( type="Video", infoLabels={ "Title": name } )
        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)
        return ok

params=parameters_string_to_dict(sys.argv[2])
mode=params.get('mode')
url=params.get('url')
if type(url)==type(str()):
  url=urllib.unquote_plus(url)

if mode == 'addCurrentUrl':
    addCurrentUrl()
elif mode == 'showAllPlaylists':
    showAllPlaylists()
elif mode == 'playListMain':
    playListMain()
elif mode == 'showPlaylist':
    showPlaylist(url)
elif mode == 'playVideoFromPlaylist':
    playVideoFromPlaylist(url)
elif mode == 'managePlaylist':
    managePlaylist()
else:
    index()