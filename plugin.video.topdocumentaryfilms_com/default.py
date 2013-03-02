#!/usr/bin/python
# -*- coding: utf-8 -*-
import urllib,urllib2,re,xbmcplugin,xbmcgui,sys,xbmcaddon,socket

socket.setdefaulttimeout(30)
pluginhandle = int(sys.argv[1])
xbox = xbmc.getCondVisibility("System.Platform.xbox")
addon = xbmcaddon.Addon(id='plugin.video.topdocumentaryfilms_com')
translation = addon.getLocalizedString
forceViewMode=addon.getSetting("forceViewMode")
viewMode=str(addon.getSetting("viewMode"))

def index():
        addDir(translation(30001),"http://topdocumentaryfilms.com/all/",'listVideos',"")
        addDir(translation(30004),"http://topdocumentaryfilms.com/",'listVideos',"")
        content = getUrl("http://topdocumentaryfilms.com/all/")
        content = content[content.find("<h2>Documentary Categories</h2>"):]
        content = content[:content.find("</div><ul>")]
        match=re.compile('href="http://topdocumentaryfilms.com/category/(.+?)/" title="(.+?)">(.+?)</a>(.+?)</li>', re.DOTALL).findall(content)
        for id, temp, title, count in match:
          addDir(title+count,"http://topdocumentaryfilms.com/category/"+id+"/",'listVideos',"")
        xbmcplugin.endOfDirectory(pluginhandle)
        if forceViewMode=="true":
          xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')

def listVideos(url):
        content = getUrl(url)
        spl=content.split('<h2 class="postTitle')
        for i in range(1,len(spl),1):
            entry=spl[i]
            match=re.compile('href="(.+?)"', re.DOTALL).findall(entry)
            url=match[0]
            match=re.compile('src="(.+?)"', re.DOTALL).findall(entry)
            thumb=match[0]
            match=re.compile('<p>(.+?)</p>', re.DOTALL).findall(entry)
            desc=""
            if len(match)>0:
              desc=match[0]
            year=""
            match=re.compile('rel="tag">(.+?)<', re.DOTALL).findall(entry)
            if len(match)>0:
              year=match[0]
            match=re.compile('title="(.+?)"', re.DOTALL).findall(entry)
            title=match[0]
            if year!="":
              title=title+" ("+year+")"
            title=cleanTitle(title)
            addDir(title,url,'playVideo',thumb,desc)
        match=re.compile('href="(.+?)">(.+?)</a>', re.DOTALL).findall(content)
        for url, title in match:
          if title=="Next":
            addDir(translation(30002),url,'listVideos',"")
        xbmcplugin.endOfDirectory(pluginhandle)
        if forceViewMode=="true":
          xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')

def playVideo(url):
          content = getUrl(url)
          match0=re.compile('src="http://www.youtube.com/embed/videoseries\\?list=(.+?)&', re.DOTALL).findall(content)
          match1=re.compile('src="http://www.youtube.com/embed/(.+?)\\?', re.DOTALL).findall(content)
          match2=re.compile('src="http://www.youtube.com/p/(.+?)\\?', re.DOTALL).findall(content)
          match3=re.compile('src="http://player.vimeo.com/video/(.+?)\\?', re.DOTALL).findall(content)
          match4=re.compile('src="http://blip.tv/play/(.+?).html', re.DOTALL).findall(content)
          match5=re.compile('src="http://channel.nationalgeographic.com/(.+?)/videos/(.+?)/embed/', re.DOTALL).findall(content)
          match6=re.compile('src="http://www.dailymotion.com/embed/video/(.+?)"', re.DOTALL).findall(content)
          match7=re.compile('src="http://www.dailymotion.com/widget/jukebox\\?list\\[\\]=%2Fplaylist%2F(.+?)%2F', re.DOTALL).findall(content)
          url=""
          if len(match0)>0:
            pl=match0[0]
            if '"' in pl:
              pl=pl[:pl.find('"')]
            playYoutubePlaylist(pl)
            url="pl"
          elif len(match1)>0:
            url = getYoutubeUrl(match1[0])
          elif len(match2)>0:
            playYoutubePlaylist(match2[0])
            url="pl"
          elif len(match3)>0:
            url = getVimeoUrl(match3[0])
          elif len(match4)>0:
            url = getBlipUrl(match4[0])
          elif len(match5)>0:
            content = getUrl("http://channel.nationalgeographic.com/channel/videos/"+match5[0][1]+"/embed/")
            match=re.compile('"slug": "(.+?)"', re.DOTALL).findall(content)
            if len(match)>0:
              url=match[0]
          elif len(match6)>0:
            url = getDailyMotionUrl(match6[0])
          elif len(match7)>0:
            url="pl"
            playDmPlaylist(match7[0])
          if url!="":
            if url!="pl":
              xbmc.Player().play(url)
          else:
            xbmc.executebuiltin('XBMC.Notification(Info:,'+translation(30003)+',5000)')

def playYoutubePlaylist(id):
          ids=[]
          titles=[]
          content = getUrl("http://gdata.youtube.com/feeds/api/playlists/"+id)
          spl=content.split('<media:player')
          playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
          playlist.clear()
          if len(spl)>1:
            for i in range(1,len(spl),1):
                entry=spl[i]
                match=re.compile('v=(.+?)&', re.DOTALL).findall(entry)
                url=getYoutubeUrl(match[0])
                match=re.compile("<media:title type='plain'>(.+?)</media:title>", re.DOTALL).findall(entry)
                listitem = xbmcgui.ListItem(match[0])
                playlist.add(url,listitem)
            xbmc.Player().play(playlist)
          else:
            xbmc.executebuiltin('XBMC.Notification(Info:,'+translation(30003)+',5000)')

def getYoutubeUrl(id):
          if xbox==True:
            url = "plugin://video/YouTube/?path=/root/video&action=play_video&videoid=" + id
          else:
            url = "plugin://plugin.video.youtube/?path=/root/video&action=play_video&videoid=" + id
          return url

def getVimeoUrl(id):
          if xbox==True:
            url = "plugin://video/Vimeo/?path=/root/video&action=play_video&videoid=" + id
          else:
            url = "plugin://plugin.video.vimeo/?path=/root/video&action=play_video&videoid=" + id
          return url

def getBlipUrl(baseID):
          content = urllib.unquote_plus(getRedirectedUrl("http://blip.tv/play/"+baseID+".html"))
          match=re.compile('/rss/flash/(.+?)&', re.DOTALL).findall(content)
          if len(match)>0:
            id=match[0]
          elif content.find("http://blip.tv/rss/flash/")>=0:
            id=content[content.find("http://blip.tv/rss/flash/")+25:]
          if xbox==True:
            url = "plugin://video/BlipTV/?path=/root/video&action=play_video&videoid=" + id
          else:
            url = "plugin://plugin.video.bliptv/?path=/root/video&action=play_video&videoid=" + id
          return url

def getDailyMotionUrl(id):
          if xbox==True:
            url = "plugin://video/DailyMotion.com/?url="+id+"&mode=playVideo"
          else:
            url = "plugin://plugin.video.dailymotion_com/?url="+id+"&mode=playVideo"
          return url

def playDmPlaylist(id):
          url="https://api.dailymotion.com/playlist/"+id+"/videos?fields=id,title&sort=recent&limit=100"
          content = getUrl(url).replace("\\","")
          match=re.compile('{"id":"(.*?)","title":"(.+?)"}', re.DOTALL).findall(content)
          playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
          playlist.clear()
          for id, title in match:
            url=getDailyMotionUrl(id)
            listitem = xbmcgui.ListItem(title)
            playlist.add(url,listitem)
          xbmc.Player().play(playlist)

def cleanTitle(title):
        return title.replace("&lt;","<").replace("&gt;",">").replace("&amp;","&").replace("&#038;","&").replace("&#39;","'").replace("&#039;","'").replace("&#8211;","-").replace("&#8220;","-").replace("&#8221;","-").replace("&#8217;","'").replace("&quot;","\"").strip()

def getUrl(url):
        req = urllib2.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; rv:19.0) Gecko/20100101 Firefox/19.0')
        response = urllib2.urlopen(req)
        link=response.read()
        response.close()
        return link

def getRedirectedUrl(url):
        req = urllib2.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; rv:19.0) Gecko/20100101 Firefox/19.0')
        response = urllib2.urlopen(req)
        response.close()
        return str(response.geturl())

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

def addDir(name,url,mode,iconimage,desc=""):
        u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)
        ok=True
        liz=xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
        liz.setInfo( type="Video", infoLabels={ "Title": name, "Plot": desc } )
        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)
        return ok

params=parameters_string_to_dict(sys.argv[2])
mode=params.get('mode')
url=params.get('url')
if type(url)==type(str()):
  url=urllib.unquote_plus(url)

if mode == 'listChannelVideos':
    listChannelVideos(url)
elif mode == 'listVideos':
    listVideos(url)
elif mode == 'listChannel':
    listChannel(url)
elif mode == 'playVideo':
    playVideo(url)
else:
    index()
