#!/usr/bin/python
# -*- coding: utf-8 -*-
import urllib,urllib2,re,xbmcplugin,xbmcgui,sys,xbmcaddon,base64,socket,os,datetime

familyFilter="1"

socket.setdefaulttimeout(30)
pluginhandle = int(sys.argv[1])
addonID = 'plugin.video.dailymotion_com'
addon = xbmcaddon.Addon(addonID)
translation = addon.getLocalizedString
channelFavsFile=xbmc.translatePath("special://profile/addon_data/"+addonID+"/"+addonID+".favorites")
familyFilterFile=xbmc.translatePath("special://profile/addon_data/"+addonID+"/family_filter_off")

if os.path.exists(familyFilterFile):
  familyFilter="0"

while (not os.path.exists(xbmc.translatePath("special://profile/addon_data/"+addonID+"/settings.xml"))):
  addon.openSettings()

forceViewMode=addon.getSetting("forceViewMode")
viewMode=str(addon.getSetting("viewMode"))
maxVideoQuality=addon.getSetting("maxVideoQuality")
qual=["480p","720p","1080p"]
maxVideoQuality=qual[int(maxVideoQuality)]
language=addon.getSetting("language")
languages=["en_EN","ar_ES","au_EN","be_FR","be_NL","br_PT","ca_EN","ca_FR","de_DE","es_ES","es_CA","gr_EL","fr_FR","in_EN","ie_EN","it_IT","mx_ES","ma_FR","nl_NL","at_DE","pl_PL","pt_PT","ru_RU","ro_RO","ch_FR","ch_DE","ch_IT","tn_FR","tr_TR","en_GB","en_US","vn_VI","jp_JP","cn_ZH"]
language=languages[int(language)]
dmUser=addon.getSetting("dmUser")
itemsPerPage=addon.getSetting("itemsPerPage")
itemsPage=["25","50","75","100"]
itemsPerPage=itemsPage[int(itemsPerPage)]

def index():
        if dmUser=="":
          addFavDir(translation(30024),"","favouriteUsers","")
        else:
          addDir(translation(30034),"","personalMain","")
        addDir(translation(30006),"",'listChannels',"")
        addDir(translation(30007),"",'sortUsers1',"")
        addDir(translation(30002),"",'search',"")
        addDir(translation(30003),"",'listLive',"")
        addDir(translation(30039), '3D:ALL','sortVideos1','','')
        xbmcplugin.endOfDirectory(pluginhandle)
        if forceViewMode=="true":
          xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')

def personalMain():
        addDir(translation(30035),"https://api.dailymotion.com/user/"+dmUser+"/following?fields=username,avatar_large_url,videos_total,views_total&sort=popular&limit="+itemsPerPage+"&family_filter="+familyFilter+"&localization="+language+"&page=1",'listUsers',"")
        addDir(translation(30036),"https://api.dailymotion.com/user/"+dmUser+"/subscriptions?fields=description,duration,id,owner.username,taken_time,thumbnail_large_url,title,views_total&sort=recent&limit="+itemsPerPage+"&family_filter="+familyFilter+"&localization="+language+"&page=1",'listVideos',"")
        addDir(translation(30037),"https://api.dailymotion.com/user/"+dmUser+"/favorites?fields=description,duration,id,owner.username,taken_time,thumbnail_large_url,title,views_total&sort=recent&limit="+itemsPerPage+"&family_filter="+familyFilter+"&localization="+language+"&page=1",'listVideos',"")
        addDir(translation(30038),"",'listUserPlaylists',"")
        xbmcplugin.endOfDirectory(pluginhandle)
        if forceViewMode=="true":
          xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')

def listUserPlaylists():
        url="https://api.dailymotion.com/user/"+dmUser+"/playlists?fields=id,name,videos_total&sort=recent&limit="+itemsPerPage+"&family_filter="+familyFilter+"&localization="+language+"&page=1"
        content = getUrl(url)
        match=re.compile('{"id":"(.+?)","name":"(.+?)","videos_total":(.+?)}', re.DOTALL).findall(content)
        for id, title, vids in match:
          addDir(title+" ("+vids+")", id+"_"+dmUser+"_"+title,'showPlaylist','')
        xbmcplugin.endOfDirectory(pluginhandle)
        if forceViewMode=="true":
          xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')

def showPlaylist(id):
        url="https://api.dailymotion.com/playlist/"+id+"/videos?fields=description,duration,id,owner.username,taken_time,thumbnail_large_url,title,views_total&sort=recent&limit="+itemsPerPage+"&family_filter="+familyFilter+"&localization="+language+"&page=1"
        listVideos(url)

def favouriteUsers():
        xbmcplugin.addSortMethod(pluginhandle, xbmcplugin.SORT_METHOD_LABEL)
        if os.path.exists(channelFavsFile):
          fh = open(channelFavsFile, 'r')
          content = fh.read()
          match=re.compile('###USER###=(.+?)###THUMB###=(.*?)###END###', re.DOTALL).findall(content)
          for user, thumb in match:
            addUserFavDir(user, 'owner:'+user,'sortVideos1',thumb)
          fh.close()
        xbmcplugin.endOfDirectory(pluginhandle)
        if forceViewMode=="true":
          xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')

def listChannels():
        content = getUrl("https://api.dailymotion.com/channels?family_filter="+familyFilter+"&localization="+language)
        match=re.compile('{"id":"(.+?)","name":"(.+?)","description":"(.+?)"}', re.DOTALL).findall(content)
        for id, title, desc in match:
          addDir(title, 'channel:'+id,'sortVideos1','',desc)
        xbmcplugin.endOfDirectory(pluginhandle)
        if forceViewMode=="true":
          xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')

def sortVideos1(url):
        type=url[:url.find(":")]
        id=url[url.find(":")+1:]
        if type=="3D": url="https://api.dailymotion.com/videos?fields=description,duration,id,owner.username,taken_time,thumbnail_large_url,title,views_total&filters=3d&sort=recent&limit="+itemsPerPage+"&family_filter="+familyFilter+"&localization="+language+"&page=1"
        else: url="https://api.dailymotion.com/videos?fields=description,duration,id,owner.username,taken_time,thumbnail_large_url,title,views_total&"+type+"="+id+"&sort=recent&limit="+itemsPerPage+"&family_filter="+familyFilter+"&localization="+language+"&page=1"
        addDir(translation(30008),url,'listVideos',"")
        addDir(translation(30009),url.replace("sort=recent","sort=visited"),'sortVideos2',"")
        addDir(translation(30020),url.replace("sort=recent","sort=commented"),'sortVideos2',"")
        addDir(translation(30010),url.replace("sort=recent","sort=rated"),'sortVideos2',"")
        xbmcplugin.endOfDirectory(pluginhandle)
        if forceViewMode=="true":
          xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')

def sortVideos2(url):
        addDir(translation(30011),url.replace("sort=visited","sort=visited-today").replace("sort=commented","sort=commented-today").replace("sort=rated","sort=rated-today"),"listVideos","")
        addDir(translation(30012),url.replace("sort=visited","sort=visited-week").replace("sort=commented","sort=commented-week").replace("sort=rated","sort=rated-week"),"listVideos","")
        addDir(translation(30013),url.replace("sort=visited","sort=visited-month").replace("sort=commented","sort=commented-month").replace("sort=rated","sort=rated-month"),"listVideos","")
        addDir(translation(30014),url,'listVideos',"")
        xbmcplugin.endOfDirectory(pluginhandle)
        if forceViewMode=="true":
          xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')

def sortUsers1():
        url="https://api.dailymotion.com/users?fields=username,avatar_large_url,videos_total,views_total&sort=popular&limit="+itemsPerPage+"&family_filter="+familyFilter+"&localization="+language+"&page=1"
        addDir(translation(30040),url,'sortUsers2',"")
        addDir(translation(30016),url+"&filters=featured",'sortUsers2',"")
        addDir(translation(30017),url+"&filters=official",'sortUsers2',"")
        addDir(translation(30018),url+"&filters=creative",'sortUsers2',"")
        xbmcplugin.endOfDirectory(pluginhandle)
        if forceViewMode=="true":
          xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')

def sortUsers2(url):
        addDir(translation(30019),url,'listUsers',"")
        addDir(translation(30020),url.replace("sort=popular","sort=commented"),'listUsers',"")
        addDir(translation(30021),url.replace("sort=popular","sort=rated"),'listUsers',"")
        xbmcplugin.endOfDirectory(pluginhandle)
        if forceViewMode=="true":
          xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')

def listVideos(url):
        content = getUrl(url).replace("\\","")
        match=re.compile('{"description":"(.*?)","duration":(.+?),"id":"(.+?)","owner.username":"(.+?)","taken_time":(.+?),"thumbnail_large_url":"(.*?)","title":"(.+?)","views_total":(.+?)}', re.DOTALL).findall(content)
        for desc, duration, id, user, date, thumb, title, views in match:
          duration=str(int(duration)/60+1)
          desc="User: "+user+"  |  "+views+" Views  |  "+datetime.datetime.fromtimestamp(int(date)).strftime('%Y-%m-%d')+"\n"+desc
          if user=="hulu": pass
          elif user=="ARTEplus7": addLink(cleanTitle(title),id,'playArte',thumb,user,desc,duration)
          else: addLink(cleanTitle(title),id,'playVideo',thumb,user,desc,duration)
        match=re.compile('"page":(.+?),', re.DOTALL).findall(content)
        currentPage=int(match[0])
        nextPage=currentPage+1
        if '"has_more":true' in content:
          addDir(translation(30001)+" ("+str(nextPage)+")",url.replace("page="+str(currentPage),"page="+str(nextPage)),'listVideos',"")
        xbmcplugin.endOfDirectory(pluginhandle)
        if forceViewMode=="true":
          xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')

def listUsers(url):
        content = getUrl(url).replace("\\","")
        match=re.compile('{"username":"(.+?)","avatar_large_url":"(.*?)","videos_total":(.+?),"views_total":(.+?)}', re.DOTALL).findall(content)
        for user, thumb, videos, views in match:
          addUserDir(cleanTitle(user),'owner:'+user,'sortVideos1',thumb,"Views: "+views+"\nVideos: "+videos)
        match=re.compile('"page":(.+?),', re.DOTALL).findall(content)
        currentPage=int(match[0])
        nextPage=currentPage+1
        if '"has_more":true' in content:
          addDir(translation(30001)+" ("+str(nextPage)+")",url.replace("page="+str(currentPage),"page="+str(nextPage)),'listUsers',"")
        xbmcplugin.endOfDirectory(pluginhandle)
        if forceViewMode=="true":
          xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')

def listLive():
        content = getUrl("https://api.dailymotion.com/videos?fields=id,thumbnail_large_url%2Ctitle%2Cviews_last_hour&filters=live&sort=visited-hour&limit="+itemsPerPage+"&family_filter="+familyFilter+"&localization="+language).replace("\\","")
        match=re.compile('\\{"id":"(.+?)","thumbnail_large_url":"(.+?)","title":"(.+?)","views_last_hour":(.+?)\\}', re.DOTALL).findall(content)
        for id, thumb, title, views in match:
          addLiveLink(title,id,'playVideo',thumb,views)
        xbmcplugin.endOfDirectory(pluginhandle)
        if forceViewMode=="true":
          xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')

def search():
        keyboard = xbmc.Keyboard('', translation(30002))
        keyboard.doModal()
        if keyboard.isConfirmed() and keyboard.getText():
          search_string = keyboard.getText().replace(" ","+")
          listVideos("https://api.dailymotion.com/videos?fields=description,duration,id,owner.username,taken_time,thumbnail_large_url,title,views_total&search="+search_string+"&sort=relevance&limit="+itemsPerPage+"&family_filter="+familyFilter+"&localization="+language+"&page=1")

def playVideo(id):
        content = getUrl2("http://www.dailymotion.com/sequence/"+id)
        if content.find('"statusCode":410')>0 or content.find('"statusCode":403')>0:
          xbmc.executebuiltin('XBMC.Notification(Info:,'+str(translation(30022))+' (DailyMotion)!,5000)')
        else:
          matchAuto=re.compile('"autoURL":"(.+?)"', re.DOTALL).findall(content)
          matchLive=re.compile('"customURL":"(.+?)"', re.DOTALL).findall(content)
          matchFullHD=re.compile('"hd1080URL":"(.+?)"', re.DOTALL).findall(content)
          matchHD=re.compile('"hd720URL":"(.+?)"', re.DOTALL).findall(content)
          matchHQ=re.compile('"hqURL":"(.+?)"', re.DOTALL).findall(content)
          matchSD=re.compile('"sdURL":"(.+?)"', re.DOTALL).findall(content)
          matchSD2=re.compile('"video_url":"(.+?)"', re.DOTALL).findall(content)
          url=""
          if len(matchAuto)>0:
            content=getUrl(urllib.unquote_plus(matchAuto[0]).replace("\\",""))
            match=re.compile('"height":(.+?),"template":"(.+?)"', re.DOTALL).findall(content)
            for height, urlTemp in match:
              if int(height) <= int(maxVideoQuality[:maxVideoQuality.find("p")]):
                url=urllib.unquote_plus(urlTemp).replace(".mnft",".mp4")
          elif len(matchLive)>0:
            url=urllib.unquote_plus(matchLive[0]).replace("\\","")
            url=getUrl(url)
          elif len(matchFullHD)>0 and maxVideoQuality=="1080p":
            url=urllib.unquote_plus(matchFullHD[0]).replace("\\","")
          elif len(matchHD)>0 and (maxVideoQuality=="720p" or maxVideoQuality=="1080p"):
            url=urllib.unquote_plus(matchHD[0]).replace("\\","")
          elif len(matchHQ)>0:
            url=urllib.unquote_plus(matchHQ[0]).replace("\\","")
          elif len(matchSD)>0:
            url=urllib.unquote_plus(matchSD[0]).replace("\\","")
          elif len(matchSD2)>0:
            url=urllib.unquote_plus(matchSD2[0]).replace("\\","")
          if url!="":
            listitem = xbmcgui.ListItem(path=url)
            return xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)

def playArte(id):
        try:
          content = getUrl("http://www.dailymotion.com/video/"+id)
          match=re.compile('<a class="link" href="http://videos.arte.tv/(.+?)/videos/(.+?).html">', re.DOTALL).findall(content)
          lang=match[0][0]
          vid=match[0][1]
          url="http://videos.arte.tv/"+lang+"/do_delegate/videos/"+vid+",view,asPlayerXml.xml"
          content = getUrl(url)
          match=re.compile('<video lang="'+lang+'" ref="(.+?)"', re.DOTALL).findall(content)
          url=match[0]
          content = getUrl(url)
          match1=re.compile('<url quality="hd">(.+?)</url>', re.DOTALL).findall(content)
          match2=re.compile('<url quality="sd">(.+?)</url>', re.DOTALL).findall(content)
          urlNew=""
          if len(match1)==1:
            urlNew=match1[0]
          elif len(match2)==1:
            urlNew=match2[0]
          urlNew=urlNew.replace("MP4:","mp4:")
          base=urlNew[:urlNew.find("mp4:")]
          playpath=urlNew[urlNew.find("mp4:"):]
          listitem = xbmcgui.ListItem(path=base+" playpath="+playpath+" swfVfy=1 swfUrl=http://videos.arte.tv/blob/web/i18n/view/player_24-3188338-data-5168030.swf")
          return xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)
        except:
          xbmc.executebuiltin('XBMC.Notification(Info:,'+str(translation(30022))+' (Arte)!,5000)')

def addFav():
        keyboard = xbmc.Keyboard('', translation(30033))
        keyboard.doModal()
        if keyboard.isConfirmed() and keyboard.getText():
          user=keyboard.getText()
          channelEntry = "###USER###="+user+"###THUMB###=###END###"
          if os.path.exists(channelFavsFile):
            fh = open(channelFavsFile, 'r')
            content=fh.read()
            fh.close()
            if content.find(channelEntry)==-1:
              fh=open(channelFavsFile, 'a')
              fh.write(channelEntry+"\n")
              fh.close()
          else:
            fh=open(channelFavsFile, 'a')
            fh.write(channelEntry+"\n")
            fh.close()
          xbmc.executebuiltin('XBMC.Notification(Info:,'+str(translation(30030))+'!,5000)')

def favourites(param):
        mode=param[param.find("###MODE###=")+11:]
        mode=mode[:mode.find("###")]
        channelEntry=param[param.find("###USER###="):]
        if mode=="ADD":
          if os.path.exists(channelFavsFile):
            fh = open(channelFavsFile, 'r')
            content=fh.read()
            fh.close()
            if content.find(channelEntry)==-1:
              fh=open(channelFavsFile, 'a')
              fh.write(channelEntry+"\n")
              fh.close()
          else:
            fh=open(channelFavsFile, 'a')
            fh.write(channelEntry+"\n")
            fh.close()
          xbmc.executebuiltin('XBMC.Notification(Info:,'+str(translation(30030))+'!,5000)')
        elif mode=="REMOVE":
          refresh=param[param.find("###REFRESH###=")+14:]
          refresh=refresh[:refresh.find("###USER###=")]
          fh = open(channelFavsFile, 'r')
          content=fh.read()
          fh.close()
          entry=content[content.find(channelEntry):]
          fh=open(channelFavsFile, 'w')
          fh.write(content.replace(channelEntry+"\n",""))
          fh.close()
          if refresh=="TRUE":
            xbmc.executebuiltin("Container.Refresh")

def cleanTitle(title):
        title=title.replace("&lt;","<").replace("&gt;",">").replace("&amp;","&").replace("&#039;","'").replace("&quot;","\"").replace("&szlig;","ß").replace("&ndash;","-")
        title=title.replace("&Auml;","Ä").replace("&Uuml;","Ü").replace("&Ouml;","Ö").replace("&auml;","ä").replace("&uuml;","ü").replace("&ouml;","ö")
        title=title.replace("u00c4","Ä").replace("u00e4","ä").replace("u00d6","Ö").replace("u00f6","ö").replace("u00dc","Ü").replace("u00fc","ü").replace("u00df","ß")
        title=title.strip()
        return title

def getUrl(url):
        req = urllib2.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; rv:19.0) Gecko/20100101 Firefox/19.0')
        response = urllib2.urlopen(req)
        link=response.read()
        response.close()
        return link

def getUrl2(url):
        if familyFilter=="1": ff="on"
        else: ff="off"
        req = urllib2.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; rv:19.0) Gecko/20100101 Firefox/19.0')
        req.add_header('Cookie',"lang="+language+"; family_filter="+ff)
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

def addLink(name,url,mode,iconimage,user,desc,duration):
        u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)
        ok=True
        liz=xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
        liz.setInfo( type="Video", infoLabels={ "Title": name, "Plot": desc, "Duration": duration } )
        liz.setProperty('IsPlayable', 'true')
        if dmUser=="":
          playListInfos="###MODE###=ADD###USER###="+user+"###THUMB###=DefaultVideo.png###END###"
          liz.addContextMenuItems([(translation(30028).format(user=user), 'XBMC.RunPlugin(plugin://plugin.video.dailymotion_com/?mode=favourites&url='+urllib.quote_plus(playListInfos)+')',)])
        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz)
        return ok

def addLiveLink(name,url,mode,iconimage,desc):
        u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)
        ok=True
        liz=xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
        liz.setInfo( type="Video", infoLabels={ "Title": name, "Plot": desc } )
        liz.setProperty('IsPlayable', 'true')
        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz)
        return ok

def addDir(name,url,mode,iconimage,desc=""):
        u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)
        ok=True
        liz=xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
        liz.setInfo( type="Video", infoLabels={ "Title": name, "Plot": desc } )
        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)
        return ok

def addUserDir(name,url,mode,iconimage,desc):
        u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)
        ok=True
        liz=xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
        liz.setInfo( type="Video", infoLabels={ "Title": name, "Plot": desc } )
        if dmUser=="":
          playListInfos="###MODE###=ADD###USER###="+name+"###THUMB###="+iconimage+"###END###"
          liz.addContextMenuItems([(translation(30028).format(user=name), 'XBMC.RunPlugin(plugin://plugin.video.dailymotion_com/?mode=favourites&url='+urllib.quote_plus(playListInfos)+')',)])
        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)
        return ok

def addFavDir(name,url,mode,iconimage):
        u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)
        ok=True
        liz=xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
        liz.setInfo( type="Video", infoLabels={ "Title": name } )
        liz.addContextMenuItems([(translation(30033), 'XBMC.RunPlugin(plugin://plugin.video.dailymotion_com/?mode=addFav)',)])
        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)
        return ok

def addUserFavDir(name,url,mode,iconimage):
        u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)
        ok=True
        liz=xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
        liz.setInfo( type="Video", infoLabels={ "Title": name } )
        if dmUser=="":
          playListInfos="###MODE###=REMOVE###REFRESH###=TRUE###USER###="+name+"###THUMB###="+iconimage+"###END###"
          liz.addContextMenuItems([(translation(30029), 'XBMC.RunPlugin(plugin://plugin.video.dailymotion_com/?mode=favourites&url='+urllib.quote_plus(playListInfos)+')',)])
        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)
        return ok

params=parameters_string_to_dict(sys.argv[2])
mode=params.get('mode')
url=params.get('url')
if type(url)==type(str()):
  url=urllib.unquote_plus(url)

if mode == 'listVideos':
    listVideos(url)
elif mode == 'listLive':
    listLive()
elif mode == 'listUsers':
    listUsers(url)
elif mode == 'listChannels':
    listChannels()
elif mode == 'favourites':
    favourites(url)
elif mode == 'addFav':
    addFav()
elif mode == 'personalMain':
    personalMain()
elif mode == 'listPersonalUsers':
    listPersonalUsers()
elif mode == 'favouriteUsers':
    favouriteUsers()
elif mode == 'listUserPlaylists':
    listUserPlaylists()
elif mode == 'showPlaylist':
    showPlaylist(url)
elif mode == 'sortVideos1':
    sortVideos1(url)
elif mode == 'sortVideos2':
    sortVideos2(url)
elif mode == 'sortUsers1':
    sortUsers1()
elif mode == 'sortUsers2':
    sortUsers2(url)
elif mode == 'playVideo':
    playVideo(url)
elif mode == 'playArte':
    playArte(url)
elif mode == 'search':
    search()
else:
    index()
