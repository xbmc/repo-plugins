#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright by AddonScriptorDE
# Updated by L0RE since 3.2.2
import urllib,urllib2,re,xbmcplugin,xbmcgui,sys,xbmcaddon,os,random,json

pluginhandle = int(sys.argv[1])

addonID = "plugin.video.mtv_de"
playlistFile=xbmc.translatePath("special://profile/addon_data/"+addonID+"/"+addonID+".playlists")
artistsFavsFile=xbmc.translatePath("special://profile/addon_data/"+addonID+"/"+addonID+".artistsFavs")
titlesListFile=xbmc.translatePath("special://profile/addon_data/"+addonID+"/"+addonID+".titles")
blacklistFile=xbmc.translatePath("special://profile/addon_data/"+addonID+"/"+addonID+".blacklist")
addon = xbmcaddon.Addon(id=addonID)
translation = addon.getLocalizedString
filterVids=addon.getSetting("filterVids")
forceViewMode = addon.getSetting("forceViewMode") == "true"
useThumbAsFanart = addon.getSetting("useThumbAsFanart") == "true"
viewMode = str(addon.getSetting("viewMode"))




global playit
playit=0

def debug(content):
    log(content, xbmc.LOGDEBUG)
    
def notice(content):
    log(content, xbmc.LOGNOTICE)

def log(msg, level=xbmc.LOGNOTICE):
    addon = xbmcaddon.Addon()
    addonID = addon.getAddonInfo('id')
    xbmc.log('%s: %s' % (addonID, msg), level)   
def index():
        country = addon.getSetting("country") 
        artistsFavsCount=0
        if os.path.exists(artistsFavsFile):
          fh = open(artistsFavsFile, 'r')
          artistsFavsCount = len(fh.readlines())
          fh.close()
        titlesCount=0
        if os.path.exists(titlesListFile):
          fh = open(titlesListFile, 'r')
          if filterVids=="true": 
            all_lines = fh.readlines()
            titlesCount=0
            for line in all_lines:
              if line.lower().find("all eyes on")==-1 and line.lower().find("interview")==-1:
                titlesCount=titlesCount+1
          else:
            titlesCount = len(fh.readlines())
          fh.close()
        debug("COntry :"+ country)
        if country=="0":
           addDir("TV-Shows","http://www.mtv.de/shows/async_data.json?sort=playable",'listShows',"")
           addDir(translation(30007),"http://www.mtv.de/musik?expanded=true",'listVideos_old',"")
           addDir(translation(30222),"",'charts',"")      
           addDir(translation(30217),"http://www.mtv.ch/musik",'listVideos_old',"")
        if country=="1":
             addDir("TV-Shows","http://www.mtv.ch/shows/async_data.json?sort=playable",'listShows',"")
             addDir(translation(30007),"http://www.mtv.ch/musik?expanded=true",'listVideos_old',"")                          
             addDir(translation(30216),"http://www.mtv.ch/charts/11-single-top-50",'listVideos_old',"")
             addDir(translation(30217),"http://www.mtv.ch/news/72401",'listVideos_old',"")
             addDir(translation(30218),"http://www.mtv.ch/charts/206-mtv-ch-videocharts",'listVideos_old',"")             
        addDir(str(translation(30009))+" ("+str(artistsFavsCount)+")","ARTISTSFAVS",'artistsFavs',"")
        #addTCDir(str(translation(30010))+" ("+str(titlesCount)+")","ARTISTS",'titles',"")
        addDir(translation(30008),"ARTISTS_AZ",'artists',"")
        #searchaddDir(translation(30005),"SEARCH_ARTIST",'search',"")
        addDir(translation(30005),"SEARCH_ARTIST",'search',"")
        addDir(translation(30006),"SEARCH_SPECIAL",'search',"")
        addDir(translation(30011),"PLAYLISTMAIN",'playlistMain',"")
        xbmcplugin.endOfDirectory(pluginhandle)

def charts():
          
           addDir(translation(30232),"",'jahrescharts',"")
           addDir(translation(30233),"",'top100charts',"")
           addDir(translation(30234),"",'themenchart',"")                                     
           addDir(translation(30227),"http://www.mtv.de/charts/302-single-top-20",'listVideos_old',"")                                                                     
           addDir(translation(30230),"http://www.mtv.de/charts/296-most-wanted-2000-s",'listVideos_old',"")  
           addDir(translation(30231),"http://www.mtv.de/charts/295-most-wanted-90-s",'listVideos_old',"")             
           
           xbmcplugin.endOfDirectory(pluginhandle)
def  top100charts():
           addDir(translation(30001),"http://www.mtv.de/charts/288-single-top-100?expanded=true",'listVideos_old',"")
           addDir(translation(30004),"http://www.mtv.de/charts/8-mtv-de-videocharts?expanded=true",'listVideos_old',"") 
           addDir(translation(30228),"http://www.mtv.de/charts/287-midweek-single-top-100?expanded=true"  ,'listVideos_old',"")
           xbmcplugin.endOfDirectory(pluginhandle)
           
def jahrescharts():           
           addDir(translation(30003),"http://ww.mtv.de/charts/241-top-100-jahrescharts-2014?expanded=true",'listVideos_old',"")
           addDir(translation(30220),"http://www.mtv.de/charts/275-top-100-jahrescharts-2015?expanded=true",'listVideos_old',"")          
           addDir(translation(30219),"http://www.mtv.de/charts/274-top-100-jahrescharts-2016?expanded=true",'listVideos_old',"")
           xbmcplugin.endOfDirectory(pluginhandle)
def themenchart():           
           addDir(translation(30211),"http://www.mtv.de/charts/293-dance-charts?expanded=true",'listVideos_old',"")    
           addDir(translation(30229),"http://www.mtv.de/charts/289-download-charts-single?expanded=true",'listVideos_old',"")            
           addDir(translation(30226),"http://www.mtv.de/charts/286-top-100-music-streaming?expanded=true",'listVideos_old',"") 
           xbmcplugin.endOfDirectory(pluginhandle)
           
def cleanTitle(title):
        return title.replace("&lt;","<").replace("&gt;",">").replace("&amp;","&").replace("&#x27;","'").replace("&#039;","\\").replace("&quot;","\"").strip()

def playlistMain():
        playlists=[]
        if os.path.exists(playlistFile):
          fh = open(playlistFile, 'r')
          for line in fh:
            pl=line[line.find("PLAYLIST###=")+12:]
            pl=pl[:pl.find("###")]
            if not pl in playlists:
              playlists.append(pl)
          fh.close()
          if len(playlists)==1:
            playlist(playlists[0])
          else:
            for pl in playlists:
              addDir(pl,pl,'playlist',"")
        xbmcplugin.endOfDirectory(pluginhandle)

def playlist(playlist):
        xbmcplugin.addSortMethod(pluginhandle, xbmcplugin.SORT_METHOD_UNSORTED)
        xbmcplugin.addSortMethod(pluginhandle, xbmcplugin.SORT_METHOD_PRODUCTIONCODE)
        xbmcplugin.addSortMethod(pluginhandle, xbmcplugin.SORT_METHOD_LABEL)
        if os.path.exists(playlistFile):
          fh = open(playlistFile, 'r')
          count=fh.read().count("###PLAYLIST###="+playlist+"###")
          rndNumbers=random.sample(range(count), count)
          fh.close()
          fh = open(playlistFile, 'r')
          all_lines = fh.readlines()
          i=0
          for line in all_lines:
            pl=line[line.find("PLAYLIST###=")+12:]
            pl=pl[:pl.find("###")]
            url=line[line.find("###URL###=")+10:]
            url=url[:url.find("###TITLE###")]
            title=line[line.find("###TITLE###=")+12:]
            title=title[:title.find("###THUMB###")]
            thumb=line[line.find("###THUMB###=")+12:]
            thumb=thumb[:thumb.find("###END###")]
            if pl==playlist:
              addPlaylistLink(title,urllib.quote_plus(url),'playVideoFromPlaylist',thumb,(rndNumbers[i]+1),playlist)
              i=i+1
          fh.close()
        xbmcplugin.endOfDirectory(pluginhandle)

def artists():
        letters = [chr(i) for i in xrange(ord('a'), ord('z')+1)]
        for letter in letters:
          addDir(letter.upper(),letter,'artistsAZ',"")
        xbmcplugin.endOfDirectory(pluginhandle)

def artistsAZ(letter):
        content = getUrl("http://www.mtv.de/artists/"+letter)
        content = content[content.find('<li class="artist-link">'):]
        content = content[:content.find("</ul>")]
        xbmc.log("XXXXXX artistsAZ:::"+ content)
        spl=content.split('<li class="artist-link"> ')
        for i in range(1,len(spl),1):
            entry=spl[i]
            match=re.compile('<a href="(.+?)">(.+?)</a>', re.DOTALL).findall(entry)
            url="http://www.mtv.de"+match[0][0]

            thumb=""
            title=match[0][1]
            title=cleanTitle(title)
            addArtistDir(title,url,'listVideos_old',thumb)
        xbmcplugin.endOfDirectory(pluginhandle)

def artistsFavs():
        xbmcplugin.addSortMethod(pluginhandle, xbmcplugin.SORT_METHOD_LABEL)
        if os.path.exists(artistsFavsFile):
          fh = open(artistsFavsFile, 'r')
          all_lines = fh.readlines()
          for line in all_lines:
            url=line[line.find("###URL###=")+10:]
            url=url[:url.find("###TITLE###")]
            title=line[line.find("###TITLE###=")+12:]
            title=title[:title.find("###END###")]
            addArtistFavDir(title,urllib.quote_plus(url),'listVideosFromFavs',"")
          fh.close()
        xbmcplugin.endOfDirectory(pluginhandle)

def listVideosFromFavs(url):
        listVideos_old(urllib.unquote_plus(url))

def titles():
        xbmcplugin.addSortMethod(pluginhandle, xbmcplugin.SORT_METHOD_PRODUCTIONCODE)
        xbmcplugin.addSortMethod(pluginhandle, xbmcplugin.SORT_METHOD_LABEL)
        contentBlacklist=""
        if os.path.exists(blacklistFile):
          fh = open(blacklistFile, 'r')
          contentBlacklist=fh.read()
          fh.close()
        numTitles=-1
        if os.path.exists(titlesListFile):
          fh = open(titlesListFile, 'r')
          all_lines = fh.readlines()
          numTitles=len(all_lines)
          rndNumbers=random.sample(range(numTitles), numTitles)
          i=0
          for line in all_lines:
            url=line[line.find("###URL###=")+10:]
            url=url[:url.find("###TITLE###")]
            title=line[line.find("###TITLE###=")+12:]
            title=title[:title.find("!!!END!!!")]
            if contentBlacklist.find(title)==-1:
              if filterVids=="true":
                if title.lower().find("all eyes on")==-1 and title.lower().find("interview")==-1:
                  addLink(title,url,'playVideo',"",(rndNumbers[i]+1))
              else:
                addLink(title,url,'playVideo',"",(rndNumbers[i]+1))
            i=i+1
          fh.close()
        xbmcplugin.endOfDirectory(pluginhandle)
        try:
          wnd = xbmcgui.Window(xbmcgui.getCurrentWindowId())
          wnd.getControl(wnd.getFocusId()).selectItem(1)
        except:
          pass

def playVideoFromPlaylist(url):
        listitem = xbmcgui.ListItem(path=urllib.unquote_plus(url))
        return xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)

def listShows(url):
        content = getUrl(url)
        content=content.replace("\\n","\n")
        content=content.replace("\u003c","<")
        content=content.replace("\u003e",">")
        content=content.replace("\\\"","\"")
        spl=content.split('viacom-icon play')
        xbmc.log("Anzahl schows"+ str(len(spl)))
        for i in range(1,len(spl),1):
            entry=spl[i]
            match=re.compile('<a href="(.+?)"', re.DOTALL).findall(entry)
            url="http://www.mtv.de"+match[0]
            match=re.compile('http://www.mtv.de/shows/([0-9]+)', re.DOTALL).findall(url)
            id=match[0]
            url='http://www.mtv.de/shows/'+ id +'/async_data.json'
            match=re.compile('<h4>(.+?)</h4>', re.DOTALL).findall(entry)
            title=match[0]
            match=re.compile('src="(.+?)"', re.DOTALL).findall(entry)
            thumb=match[0]
            addDir(title,url,'listVideos_new',thumb)
        xbmcplugin.addSortMethod(int(sys.argv[1]),1)
        xbmcplugin.endOfDirectory(pluginhandle)

def listShow(url):
        content = getUrl(url)
        if content.find("<div class='season-info'>")>=0:
          content = content[content.find("<div class='season-info'>"):]
          content = content[:content.find("</ol>")]
          spl=content.split("<li")
          for i in range(1,len(spl),1):
              entry=spl[i]
              match=re.compile('href="(.+?)" class=".*?">(.+?)<', re.DOTALL).findall(entry)
              url="http://www.mtv.de"+match[0][0]
              title="Season "+match[0][1]               
              addDir(title,url,'listVideos_new',"")
          xbmcplugin.addSortMethod(int(sys.argv[1]),1)
          xbmcplugin.endOfDirectory(pluginhandle)
        else:
          listVideos_new(url)

def listVideos_new(url):
        debug("listVideos_new URL:: "+ url)
        contentTitles=""
        if os.path.exists(titlesListFile):
          fh = open(titlesListFile, 'r')
          contentTitles=fh.read()
          fh.close()
        contentBlacklist=""
        if os.path.exists(blacklistFile):
          fh = open(blacklistFile, 'r')
          contentBlacklist=fh.read()
          fh.close()
        content = getUrl(url)
        debug(content)
        content=content.replace("\/","/")
        struktur = json.loads(content)
        so=struktur['seasons']
        for nr,wert in so.items():
          for element in wert['playlist']:     
            title_e = unicode(element['title']).encode('utf-8')          
            subtitle_e = unicode(element['subtitle']).encode('utf-8')          
            title=title_e +" ( "+ subtitle_e + " )"            
            #title = unicode(title).encode('utf-8')
            try:
              thumb="http://images.mtvnn.com/"+ str(element['riptide_image_id']) +"/306x172_"
            except: 
              thumb=""
            try:
              url=element['mrss']+ "-ad_site-de.mtv-ad_site_referer-http://www.mtv.de/&umaSite=mtv.de"
              addLink(title,url,'playVideo',thumb)
            except:
               error=1
        xbmcplugin.addSortMethod(int(sys.argv[1]),1)
        xbmcplugin.endOfDirectory(pluginhandle)
        xbmc.executebuiltin('XBMC.RunScript(special://home/addons/'+addonID+'/titles.py,'+urllib.quote_plus(title.encode('utf-8'))+')')
        if forceViewMode:
          xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')
          

def listVideos_old(url):
        debug("listVideos_old URL :"+ url)
        content = getUrl(url)
        ids=[]
        title=[]
        subtitle=[]
        mrss=[]
        chartn=[]
        charto=[]
        playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
        playlist.clear()
        riptide_image_id=[]
        jsonlist = content[content.find("window.pagePlaylist ="):]
        jsonlist = jsonlist[jsonlist.find("["):]
        jsonlist = jsonlist[:jsonlist.find("];")+1]
        jsonlist=jsonlist.replace("\/","/")
        debug("_-----")
        debug (jsonlist)
        struktur = json.loads(jsonlist)
        anzahl=len(struktur)
        for element in range (0,anzahl):
            ids.append(struktur[element]['id'])
            title.append(unicode(struktur[element]['title']).encode('utf-8'))
            subtitle.append(unicode(struktur[element]['subtitle']).encode('utf-8'))
            mrss.append(struktur[element]['mrss']+struktur[element]['mrssvars'].replace("\u0026","&"))            
            try:
              riptide_image_id.append("http://images.mtvnn.com/"+str(struktur[element]['riptide_image_id']) +"/306x172_")
            except:
               riptide_image_id.append("")             
        zusatzlist = content[content.find('<ul class="video-collection">'):]
        zusatzlist = zusatzlist[:zusatzlist.find('window.pagePlaylist')]
        spl = zusatzlist.split('<li class="playable video-collection-video"> ')        
        chartn = ids[:]
        charto = ids[:]
        for i in range(1, len(spl), 1):
             entry=spl[i]   
             debug("Entry : "+ entry)
             try:
               match = re.compile('<div class="teaser-image" data-object-id="([^"]+)">', re.DOTALL).findall(entry)
               id=match[0]             
             except:
                continue
             match = re.compile('<div class="chart-position">([^<]+)</div>', re.DOTALL).findall(entry)
             chartnew=match[0]
             try:          
                match = re.compile('<div class="chart-history-position">([^<]+)</div>', re.DOTALL).findall(entry)
                chartold=match[0]
             except:
                 chartold=-1
             try:
                id_video=ids.index(int(id))               
                chartn[id_video]=int(chartnew)
                charto[id_video]=int(chartold)
             except:
                debug("Kein Video zu :" +id)    
        if len(chartn) >0 :
            sort_chartn,sort_ids,sort_title,sort_subtitle,sort_mrss,sort_charto,sort_riptide_image_id = (list(x) for x in zip(*sorted(zip(chartn,ids,title,subtitle,mrss,charto,riptide_image_id))))
            anzahl=len(sort_ids)
            for element in range (0,anzahl):
              if int(sort_charto[element])==0 :
                 nr="[COLOR green] "+ str(sort_chartn[element]) +". ( NEU ) [/COLOR]"
              elif int(sort_charto[element])==-1  or sort_chartn[element] > 500 :
                 if int(sort_charto[element])==-1 :
                   nr =str(sort_chartn[element]) +"."
                 else:
                   nr=""
              elif sort_chartn[element] < sort_charto[element]:
                 nr="[COLOR green] "+ str(sort_chartn[element]) +". ( + "+ str(int(sort_charto[element])-int(sort_chartn[element])) +" ) [/COLOR]"
              elif sort_chartn[element] > sort_charto[element] :
                 nr="[COLOR red] "+ str(sort_chartn[element]) +". ( - "+ str(int(sort_chartn[element])-int(sort_charto[element])) +" ) [/COLOR]"
              else :
                 nr=str(sort_chartn[element]) +". ( - )"
              title_video=nr +sort_title[element] + " - "+ sort_subtitle[element]          
              addLink(title_video,sort_mrss[element],'playVideo',sort_riptide_image_id[element]) 
              
              uri=sys.argv[0]+"?url="+urllib.quote_plus(sort_mrss[element])+"&mode=playVideo"
              listitem = xbmcgui.ListItem(title_video, thumbnailImage=sort_riptide_image_id[element])
              playlist.add(uri, listitem)              
        
        xbmcplugin.endOfDirectory(pluginhandle)
        if playit==1 :
           xbmc.Player().play(playlist)
        #xbmc.executebuiltin('XBMC.RunScript(special://home/addons/'+addonID+'/titles.py,'+urllib.quote_plus(newTitles)+')')
        if forceViewMode:
          xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')
          
def listVideosLatest(url):
        urlMain=url
        contentBlacklist=""
        if os.path.exists(blacklistFile):
          fh = open(blacklistFile, 'r')
          contentBlacklist=fh.read()
          fh.close()
        contentTitles=""
        newTitles=""
        if os.path.exists(titlesListFile):
          fh = open(titlesListFile, 'r')
          contentTitles=fh.read()
          fh.close()
        content = getUrl(url)
        spl=content.split(" teaser'>")
        for i in range(1,len(spl),1):
          entry=spl[i]
          match=re.compile('href="(.+?)"', re.DOTALL).findall(entry)
          url="http://www.mtv.de/"+match[0]
          match=re.compile('src="(.+?)"', re.DOTALL).findall(entry)
          thumb=match[0].replace("/306x172","/960x540!")
          match=re.compile('title="(.+?)"', re.DOTALL).findall(entry)
          titleNew=match[0]
          titleNew=cleanTitle(titleNew)
          titleInfos="###URL###="+url+"###TITLE###="+titleNew+"!!!END!!!"
          if contentTitles.find(titleInfos)==-1 and newTitles.find(titleInfos)==-1:
            newTitles = newTitles + titleInfos
          if contentBlacklist.find(titleNew)==-1:
            addLink(titleNew,url,'playVideo',thumb)
        if urlMain.find("?page=")==-1:
          nextPage="2"
        else:
          nextPage=str(int(urlMain[-1:])+1)
        addDir(translation(30012)+" ("+nextPage+")","http://www.mtv.de/musikvideos?page="+nextPage,'listVideosLatest',"")
        xbmcplugin.endOfDirectory(pluginhandle)
        xbmc.executebuiltin('XBMC.RunScript(special://home/addons/'+addonID+'/titles.py,'+urllib.quote_plus(newTitles)+')')
        if forceViewMode:
          xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')

def playShow(id):
        content = getUrl("http://api.mtvnn.com/v2/mrss.xml?uri=mgid:sensei:video:mtvnn.com:local_playlist-"+id+"-DE")
        match=re.compile("<media:content duration='(.+?)' isDefault='true' type='text/xml' url='(.+?)'></media:content>", re.DOTALL).findall(content)
        playVideoMain(match[0][1])

def playVideo(url):      
        playit==1
        debug("-----> "+ url)
        content = getUrl(url)
        match=re.compile("<media:content duration='(.+?)' isDefault='true' type='text/xml' url='(.+?)'></media:content>", re.DOTALL).findall(content)
        try:
          playurl=match[0][1]
          #playurl=playurl.replace("video:mtvni.com","video:mtv.de")
          content = getUrl(playurl)
          if content.find("/www/custom/intl/errorslates/video_error.flv")>=0 or content.find("/www/custom/intl/errorslates/copyright_error.flv")>=0 or content.find('<error message="uri not found" />')>=0:
            xbmc.executebuiltin('XBMC.Notification(Info:,'+str(translation(30209))+',5000)')
          else:
            match=re.compile('type="video/mp4" bitrate="(.+?)">\n<src>(.+?)</src>', re.DOTALL).findall(content)
            match2=re.compile('type="video/mp4" bitrate="(.+?)">\n[ ]+?<src>(.+?)</src>', re.DOTALL).findall(content)
            match3=re.compile('type="video/x-flv" bitrate="(.+?)">\n<src>(.+?)</src>', re.DOTALL).findall(content)
            match4=re.compile('type="video/x-flv" bitrate="(.+?)">\n        <src>(.+?)</src>', re.DOTALL).findall(content)
            urlNew=""
            bitrate=0
            if len(match)>0:
              pass
            elif len(match2)>0:
              match=match2
            elif len(match3)>0:
              match=match3
            elif len(match4)>0:
              match=match4
            for br,url in match:
              if int(br)>bitrate:
                bitrate=int(br)
                urlNew=url
            if urlNew!="":
              if urlNew.find("http://")==0:
                listitem = xbmcgui.ListItem(path=urlNew)
              elif urlNew.find("rtmp://")==0 or urlNew.find("rtmpe://")==0:    
                playVideoMain(urlNew)               
        except:                
          content=content.replace("\n"," ")        
          debug("CONTENT playVideo: "+ content)
          try:
              match=re.compile("<src>([^<]+)</src>", re.DOTALL).findall(content)
              playurl=match[0]
          except:
              match=re.compile("player url='(.+?)'", re.DOTALL).findall(content)
              playurl=match[0]
          debug("-----> "+ playurl)
          #playurl=playurl.replace("video:mtvni.com","video:mtv.de")     
          playVideoMain(playurl)        
def SearchUrl(url):
         content = getUrl(url)
         content = content[:content.find("window.pagePlaylist")]
         xbmc.log("XXXXXX Video:"+  content)
         match=re.compile('mrss=([^&]+)', re.DOTALL).findall(content)
         #video=match[0] + "-ad_site-de.mtv-ad_site_referer-http://www.mtv.de/&umaSite=mtv.de"
         video=match[0]
         xbmc.log("XXXXXX Video:"+ video)
         playVideo(video)
         
def playVideoMain(url):
            url=url.replace("rtmpe","rtmp")
            listitem = xbmcgui.ListItem(path=url+" swfVfy=1 swfUrl=http://media.mtvnservices.com/player/prime/mediaplayerprime.1.8.1.swf")
            return xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)

def search(SEARCHTYPE):
        keyboard = xbmc.Keyboard('', 'Search')
        keyboard.doModal()
        if keyboard.isConfirmed() and keyboard.getText():
          search_string = keyboard.getText().replace(" ","+")
          url="http://www.mtv.de/searches?q="+search_string+"&ajax=1"
          content = getUrlSearch(url)
          if SEARCHTYPE=="SEARCH_ARTIST":
            if content.find("<h1>Künstler</h1>")>=0:
              content=content[content.find("<h1>Künstler</h1>"):]
              content=content[:content.find("</a></div>")]
              spl=content.split('</a>')
              for i in range(1,len(spl),1):
                  entry=spl[i]
                  match=re.compile('<a class="dropdown-item" href="(.+?)"', re.DOTALL).findall(entry)
                  url=match[0]
                  match=re.compile('<div class="title">(.+?)</div>', re.DOTALL).findall(entry)
                  title=match[0]
                  title=cleanTitle(title)
                  addArtistDir(title,"http://www.mtv.de"+url,'listVideos_old',"")
          elif SEARCHTYPE=="SEARCH_SPECIAL":
            if content.find("<h1>Musikvideos</h1>")>=0:
              content=content[content.find("<h1>Musikvideos</h1>"):]
              content=content[:content.find("</a></div>")]
              spl=content.split('</a>')
              for i in range(1,len(spl),1):
                  entry=spl[i]
                  match=re.compile('<a class="dropdown-item" href="([^"]+)', re.DOTALL).findall(entry)
                  url=match[0]
                  match=re.compile('<div class="title">(.+?)</div>', re.DOTALL).findall(entry)
                  title1=match[0]
                  match=re.compile('<div class="subtitle">(.+?)</div>', re.DOTALL).findall(entry)
                  title=match[0]+" - "+title1
                  title=cleanTitle(title)
                  if filterVids=="true":
                    if title.lower().find("all eyes on")==-1 and title.lower().find("interview")==-1:
                      addLink(title,"http://www.mtv.de"+url,'SearchUrl',"")
                  else:
                    addLink(title,"http://www.mtv.de"+url,'SearchUrl',"")
          xbmcplugin.endOfDirectory(pluginhandle)

def getUrl(url):
        debug("URL :"+ url)
        req = urllib2.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.3; WOW64; rv:38.0) Gecko/20100101 Firefox/38.0')
        response = urllib2.urlopen(req,timeout=60)
        link=response.read()        
        response.close()
        return link

def getUrlSearch(url):
        req = urllib2.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; rv:11.0) Gecko/20100101 Firefox/11.0')
        req.add_header('X-Requested-With', 'XMLHttpRequest')
        req.add_header('Referer', 'http://www.mtv.de/charts')
        response = urllib2.urlopen(req)
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

def addLink(name,url,mode,iconimage,rndPos=""):
        u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)
        ok=True
        liz=xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
        if rndPos=="":
          liz.setInfo( type="Video", infoLabels={ "Title": name } )
        else:
          liz.setInfo( type="Video", infoLabels={ "Title": name, "Code": str(rndPos) } )
        liz.setProperty('IsPlayable', 'true')
        nameNew=name
        if name.find(". ")==2:
          nameNew=name[4:]
        if useThumbAsFanart:
          liz.setProperty("fanart_image", iconimage)
        playListInfos="###MODE###=ADD###URL###="+u+"###TITLE###="+nameNew+"###THUMB###="+iconimage+"###END###"
        liz.addContextMenuItems([(translation(30202), 'XBMC.RunScript(special://home/addons/'+addonID+'/playlist.py,'+urllib.quote_plus(playListInfos)+')',),(translation(30204), 'XBMC.RunScript(special://home/addons/'+addonID+'/blacklist.py,'+urllib.quote_plus(playListInfos)+')',)])
        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz)        
        return ok

def addPlaylistLink(name,url,mode,iconimage,rndPos,playlist):
        ok=True
        liz=xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
        liz.setInfo( type="Video", infoLabels={ "Title": name, "Code": str(rndPos) } )
        liz.setProperty('IsPlayable', 'true')
        playListInfos="###MODE###=REMOVE###REFRESH###=TRUE###URL###="+urllib.unquote_plus(url)+"###TITLE###="+name+"###THUMB###="+iconimage+"###END###PLAYLIST###="+playlist+"###PLEND###"
        liz.addContextMenuItems([(translation(30203), 'XBMC.RunScript(special://home/addons/'+addonID+'/playlist.py,'+urllib.quote_plus(playListInfos)+')',)])
        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=urllib.unquote_plus(url),listitem=liz)
        return ok

def addDir(name,url,mode,iconimage):
        u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)
        ok=True
        liz=xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
        liz.setInfo( type="Video", infoLabels={ "Title": name } )
        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)
        return ok

def addShowLink(name,url,mode,iconimage):
        u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)
        ok=True
        liz=xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
        liz.setInfo( type="Video", infoLabels={ "Title": name } )
        liz.setProperty('IsPlayable', 'true')
        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz)
        return ok

def addTCDir(name,url,mode,iconimage):
        u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)
        ok=True
        liz=xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
        liz.setInfo( type="Video", infoLabels={ "Title": name } )
        liz.addContextMenuItems([(translation(30207), 'XBMC.RunScript(special://home/addons/'+addonID+'/deleteTitles.py)',)])
        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)
        return ok

def addArtistDir(name,url,mode,iconimage):
        u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)
        ok=True
        liz=xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
        liz.setInfo( type="Video", infoLabels={ "Title": name } )
        playListInfos="###MODE###=ADD###URL###="+url+"###TITLE###="+name+"###END###"
        liz.addContextMenuItems([(translation(30205), 'XBMC.RunScript(special://home/addons/'+addonID+'/artistsFavs.py,'+urllib.quote_plus(playListInfos)+')',)])
        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)
        return ok

def addArtistFavDir(name,url,mode,iconimage):
        u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)
        ok=True
        liz=xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
        liz.setInfo( type="Video", infoLabels={ "Title": name } )
        playListInfos="###MODE###=REMOVE###REFRESH###=TRUE###URL###="+urllib.unquote_plus(url)+"###TITLE###="+name+"###END###"
        liz.addContextMenuItems([(translation(30206), 'XBMC.RunScript(special://home/addons/'+addonID+'/artistsFavs.py,'+urllib.quote_plus(playListInfos)+')',)])
        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)
        return ok

params=parameters_string_to_dict(sys.argv[2])
mode=params.get('mode')
url=params.get('url')
if type(url)==type(str()):
  url=urllib.unquote_plus(url)

if mode == 'listVideos_old':
    listVideos_old(url)
elif mode == 'listVideos_new':
    listVideos_new(url)
elif mode == 'listVideosLatest':
    listVideosLatest(url)
elif mode == 'listVideosFromFavs':
    listVideosFromFavs(url)
elif mode == 'listShows':
    listShows(url)
elif mode == 'listShow':
    listShow(url)
elif mode == 'listEpisodes':
    listEpisodes(url)
elif mode == 'playVideo':
    playVideo(url)
elif mode == 'SearchUrl':
    SearchUrl(url)
elif mode == 'playShow':
    playShow(url)
elif mode == 'playVideoFromPlaylist':
    playVideoFromPlaylist(url)
elif mode == 'search':
    search(url)
elif mode == 'titles':
    titles()
elif mode == 'artists':
    artists()
elif mode == 'artistsAZ':
    artistsAZ(url)
elif mode == 'artistsFavs':
    artistsFavs()
elif mode == 'playlist':
    playlist(url)
elif mode == 'playlistMain':
    playlistMain()
elif mode == 'charts':
    charts()    
elif mode == 'jahrescharts':
    jahrescharts()        
elif mode == 'top100charts':
    top100charts()
elif mode == 'themenchart':
    themenchart()    
else:
    index()
