#!/usr/bin/python
# -*- coding: utf-8 -*-
import urllib,urllib2,re,xbmcplugin,xbmcgui,sys,xbmcaddon,base64,httplib,socket,time
from pyamf import remoting

pluginhandle = int(sys.argv[1])
xbox = xbmc.getCondVisibility("System.Platform.xbox")
settings = xbmcaddon.Addon(id='plugin.video.time_com')
translation = settings.getLocalizedString

forceViewMode=settings.getSetting("forceViewMode")
if forceViewMode=="true":
  forceViewMode=True
else:
  forceViewMode=False
viewMode=str(settings.getSetting("viewMode"))

maxBitRate=settings.getSetting("maxBitRate")
qual=[512000,1024000,2048000,3072000,4096000,5120000]
maxBitRate=qual[int(maxBitRate)]

pageSize=settings.getSetting("pageSize")
sizes=["10","20","50","100"]
pageSize=sizes[int(pageSize)]

def index():
        content = getUrl("http://www.time.com/time/video/search/0,32112,,00.html?cmd=tags&q=")
        contentMain = content
        content = content[content.find('<div class="filterVideo">'):]
        content = content[:content.find('</ul>'):]
        match=re.compile('&q=(.+?)">(.+?)</a></li>', re.DOTALL).findall(content)
        for id, title in match:
          if title=="Newest":
            url="http://api.brightcove.com/services/library?command=find_playlist_by_id&playlist_id="+id+"&get_item_count=true&page_number=0&video_fields=id,name,thumbnailURL,referenceId,shortDescription,longDescription,tags,length&custom_fields=relatedtopics,videoredirect&callback=&token=Svy7-e9mdkTCJdeOamQnB3soRQtQLA6s1Ypb2wtmE2g."
          elif title=="Most Viewed":
            url="http://api.brightcove.com/services/library?command=find_all_videos&get_item_count=true&page_number=0&page_size="+pageSize+"&sort_order=DESC&sort_by=plays_trailing_week&video_fields=id,name,thumbnailURL,referenceId,shortDescription,longDescription,tags,length&custom_fields=relatedtopics,videoredirect&callback=&token=Svy7-e9mdkTCJdeOamQnB3soRQtQLA6s1Ypb2wtmE2g."
          else:
            url="http://api.brightcove.com/services/library?command=find_videos_by_tags&and_tags="+id+"&get_item_count=true&page_number=0&page_size="+pageSize+"&sort_order=DESC&sort_by=modified_date&video_fields=id,name,thumbnailURL,referenceId,shortDescription,longDescription,tags,length&custom_fields=relatedtopics,videoredirect&callback=&token=Svy7-e9mdkTCJdeOamQnB3soRQtQLA6s1Ypb2wtmE2g."
          addDir(title,url,'listVideos',"")
        addDir(translation(30002),"",'listTopics',"")
        addDir(translation(30003),"",'search',"")
        content = contentMain[contentMain.find('<h4>Video Series</h4>'):]
        content = content[:content.find('</ul>')]
        match=re.compile('&q=(.+?)">(.+?)</a></li>', re.DOTALL).findall(content)
        for id, title in match:
          url="http://api.brightcove.com/services/library?command=find_videos_by_tags&and_tags="+id+"&get_item_count=true&page_number=0&page_size="+pageSize+"&sort_order=DESC&sort_by=modified_date&video_fields=id,name,thumbnailURL,referenceId,shortDescription,longDescription,tags,length&custom_fields=relatedtopics,videoredirect&callback=&token=Svy7-e9mdkTCJdeOamQnB3soRQtQLA6s1Ypb2wtmE2g."
          addDir(title,url,'listVideos',"")
        xbmcplugin.endOfDirectory(pluginhandle)
        if forceViewMode==True:
          xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')

def listVideos(url):
        content = getUrl(url)
        if content.find('"videos":')>=0:
          content = content[content.find('"videos":'):]
        match=re.compile('"page_number":(.+?),"page_size":(.+?),"total_count":(.+?)\\}', re.DOTALL).findall(content)
        pageNr=0
        pageSize=0
        totalItems=0
        if len(match)>0:
          pageNr=int(match[0][0])
          pageSize=int(match[0][1])
          totalItems=int(match[0][2])
        spl=content.split('{"id"')
        for i in range(1,len(spl),1):
            entry=spl[i]
            match=re.compile('"shortDescription":"(.+?)"', re.DOTALL).findall(entry)
            desc=""
            if len(match)>0:
              desc=match[0]
              desc=cleanTitle(desc)
            match=re.compile('"name":"(.+?)"', re.DOTALL).findall(entry)
            title=match[0]
            title=cleanTitle(title)
            match=re.compile('"length":(.+?),', re.DOTALL).findall(entry)
            length=int(match[0])/1000
            min=int(length/60)
            sec=int(length%60)
            length=str(min)+":"+str(sec)
            match=re.compile(":(.+?),", re.DOTALL).findall(entry)
            id=match[0]
            match=re.compile('"thumbnailURL":"(.+?)"', re.DOTALL).findall(entry)
            thumb=match[0].replace("\\","")
            addLink(title,id,'playBrightCoveStream',thumb,desc,length)
        if totalItems>0 and ((pageNr+1)*pageSize)<totalItems:
          newUrl=url.replace("page_number="+str(pageNr),"page_number="+str(pageNr+1))
          addDir(translation(30001),newUrl,'listVideos',"")
        xbmcplugin.endOfDirectory(pluginhandle)
        if forceViewMode==True:
          xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')

def listTopics():
        content = getUrl("http://www.time.com/time/video/topics")
        match=re.compile("cmd=tags&q=(.+?)'", re.DOTALL).findall(content)
        allTags=[]
        for tag in match:
            if not tag in allTags:
              url="http://api.brightcove.com/services/library?command=find_videos_by_tags&and_tags="+tag+"&get_item_count=true&page_number=0&page_size="+pageSize+"&sort_order=DESC&sort_by=modified_date&video_fields=id,name,thumbnailURL,referenceId,shortDescription,longDescription,tags,length&custom_fields=relatedtopics,videoredirect&callback=&token=Svy7-e9mdkTCJdeOamQnB3soRQtQLA6s1Ypb2wtmE2g."
              addDir(urllib.unquote_plus(tag),url,'listVideos',"")
              allTags.append(tag)
        xbmcplugin.endOfDirectory(pluginhandle)
        if forceViewMode==True:
          xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')

def search():
        keyboard = xbmc.Keyboard('', translation(30003))
        keyboard.doModal()
        if keyboard.isConfirmed() and keyboard.getText():
          search_string = keyboard.getText().replace(" ","%20")
          listVideos("http://api.brightcove.com/services/library?command=find_videos_by_text&text="+search_string+"&get_item_count=true&page_number=0&page_size="+pageSize+"&video_fields=id,name,thumbnailURL,referenceId,shortDescription,longDescription,tags,length&custom_fields=relatedtopics,videoredirect&callback=&token=Svy7-e9mdkTCJdeOamQnB3soRQtQLA6s1Ypb2wtmE2g.")

def playBrightCoveStream(bc_videoID):
        bc_playerID = 29323562001
        bc_publisherID = 293884104
        bc_const = "7aa45a3f2e7aadf8fa76da04bef79fb11f4a3fc2"
        conn = httplib.HTTPConnection("c.brightcove.com")
        envelope = remoting.Envelope(amfVersion=3)
        envelope.bodies.append(("/1", remoting.Request(target="com.brightcove.player.runtime.PlayerMediaFacade.findMediaById", body=[bc_const, bc_playerID, bc_videoID, bc_publisherID], envelope=envelope)))
        conn.request("POST", "/services/messagebroker/amf?playerId=" + str(bc_playerID), str(remoting.encode(envelope).read()), {'content-type': 'application/x-amf'})
        response = conn.getresponse().read()
        response = remoting.decode(response).bodies[0][1].body
        streamUrl = ""
        for item in sorted(response['renditions'], key=lambda item:item['encodingRate'], reverse=False):
          encRate = item['encodingRate']
          if encRate < maxBitRate:
            streamUrl = item['defaultURL']
        if streamUrl=="":
          streamUrl=response['FLVFullLengthURL']
        if streamUrl!="":
          url = streamUrl[0:streamUrl.find("&")]
          playpath = streamUrl[streamUrl.find("&")+1:]
          listItem = xbmcgui.ListItem(path=url+' playpath='+playpath)
          xbmcplugin.setResolvedUrl(pluginhandle,True,listItem)

def cleanTitle(title):
        title=title.replace("&lt;","<").replace("&gt;",">").replace("&amp;","&").replace("&#039;","'").replace("&quot;","\"").replace("&szlig;","ß").replace("&ndash;","-")
        title=title.replace("&Auml;","Ä").replace("&Uuml;","Ü").replace("&Ouml;","Ö").replace("&auml;","ä").replace("&uuml;","ü").replace("&ouml;","ö")
        title=title.strip()
        return title

def getUrl(url):
        req = urllib2.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; rv:11.0) Gecko/20100101 Firefox/13.0')
        if xbox==True:
          socket.setdefaulttimeout(30)
          response = urllib2.urlopen(req)
        else:
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

def addLink(name,url,mode,iconimage,desc="",duration=""):
        u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)
        ok=True
        liz=xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
        liz.setInfo( type="Video", infoLabels={ "Title": name , "Plot": desc, "Duration": duration } )
        liz.setProperty('IsPlayable', 'true')
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

if mode == 'listVideos':
    listVideos(url)
elif mode == 'listTopics':
    listTopics()
elif mode == 'playBrightCoveStream':
    playBrightCoveStream(url)
elif mode == 'search':
    search()
else:
    index()
