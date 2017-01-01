# -*- coding: utf-8 -*-

import urllib
import urllib2
import datetime
import re
import os
import xbmcplugin
import xbmcgui
import xbmcaddon
import xbmcvfs
from BeautifulSoup import BeautifulStoneSoup, BeautifulSoup, BeautifulSOAP
try:
    import json
except:
    import simplejson as json

addon = xbmcaddon.Addon(id='plugin.video.BlanketFort')
profile = addon.getAddonInfo('profile').decode('utf-8')
home = addon.getAddonInfo('path').decode('utf-8')
favorites = xbmc.translatePath(os.path.join(profile, 'favorites' )).decode('utf-8')
icon = xbmc.translatePath(os.path.join(home, 'icon.png'))
fanart = xbmc.translatePath(os.path.join(home, 'fanart.jpg'))
if os.path.exists(favorites)==True:
    FAV = open(favorites).read()

def makeRequest(url):
        try:
            req = urllib2.Request(url)
            response = urllib2.urlopen(req)
            data = response.read()
            response.close()
            return data
        except urllib2.URLError, e:
            if hasattr(e, 'code'):
                xbmc.log('We failed with error code - %s.' % e.code)
                xbmc.executebuiltin("XBMC.Notification(BlanketFort,We failed with error code - "+str(e.code)+",10000,"+icon+")")
            elif hasattr(e, 'reason'):
                xbmc.log('We failed to reach a server.')
                xbmc.log('Reason: ', e.reason)
                xbmc.executebuiltin("XBMC.Notification(BlanketFort,We failed to reach a server. - "+str(e.reason)+",10000,"+icon+")")


def getSoup(url):
        if url.startswith('http://'):
            data = makeRequest(url)
        else:
            if xbmcvfs.exists(url):
                if url.startswith("smb://"):
                    copy = xbmcvfs.copy( url, xbmc.translatePath(os.path.join(profile, 'temp', 'sorce_temp.txt')))
                    if copy:
                        data = open( xbmc.translatePath(os.path.join(profile, 'temp', 'sorce_temp.txt')), "r").read()
                        xbmcvfs.delete( xbmc.translatePath(os.path.join(profile, 'temp', 'sorce_temp.txt')) )
                    else:
                        xbmc.log("--- failed to copy from smb: ----")
                else:
                    data = open(url, 'r').read()
            else:
                xbmc.log("---- Soup Data not found! ----")
                return
        soup = BeautifulSOAP(data, convertEntities=BeautifulStoneSoup.XML_ENTITIES)
        return soup


def getData(url,fanart):
        soup = getSoup(url)
        if len(soup('channels')) > 0:
            channels = soup('channel')
            for channel in channels:
                name = channel('name')[0].string
                thumbnail = channel('thumbnail')[0].string
                if thumbnail == None:
                    thumbnail = ''

                try:
                    if not channel('fanart'):
                        if addon.getSetting('use_thumb') == "true":
                            fanArt = thumbnail
                        else:
                            fanArt = fanart
                    else:
                        fanArt = channel('fanart')[0].string
                    if fanArt == None:
                        raise
                except:
                    fanArt = fanart

                try:
                    desc = channel('info')[0].string
                    if desc == None:
                        raise
                except:
                    desc = ''

                try:
                    genre = channel('genre')[0].string
                    if genre == None:
                        raise
                except:
                    genre = ''

                try:
                    date = channel('date')[0].string
                    if date == None:
                        raise
                except:
                    date = ''
                try:
                    addDir(name.encode('utf-8', 'ignore'),url.encode('utf-8'),2,thumbnail,fanArt,desc,genre,date)
                except:
                    xbmc.log('There was a problem adding directory from getData(): '+name.encode('utf-8', 'ignore'))
        else:
            getItems(soup('item'),fanart)


def getChannelItems(name,url,fanart):
        soup = getSoup(url)
        channel_list = soup.find('channel', attrs={'name' : name})
        items = channel_list('item')
        try:
            fanArt = channel_list('fanart')[0].string
            if fanArt == None:
                raise
        except:
            fanArt = fanart
        for channel in channel_list('subchannel'):
            name = channel('name')[0].string
            try:
                thumbnail = channel('thumbnail')[0].string
                if thumbnail == None:
                    raise
            except:
                thumbnail = ''
            try:
                if not channel('fanart'):
                    if addon.getSetting('use_thumb') == "true":
                        fanArt = thumbnail
                else:
                    fanArt = channel('fanart')[0].string
                if fanArt == None:
                    raise
            except:
                pass
            try:
                desc = channel('info')[0].string
                if desc == None:
                    raise
            except:
                desc = ''

            try:
                genre = channel('genre')[0].string
                if genre == None:
                    raise
            except:
                genre = ''

            try:
                date = channel('date')[0].string
                if date == None:
                    raise
            except:
                date = ''
            try:
                addDir(name.encode('utf-8', 'ignore'),url.encode('utf-8'),3,thumbnail,fanArt,desc,genre,date)
            except:
                xbmc.log('There was a problem adding directory - '+name.encode('utf-8', 'ignore'))
        getItems(items,fanArt)


def getSubChannelItems(name,url,fanart):
        soup = getSoup(url)
        channel_list = soup.find('subchannel', attrs={'name' : name})
        items = channel_list('subitem')
        getItems(items,fanart)


def getItems(items,fanart):
        for item in items:
            try:
                name = item('title')[0].string
            except:
                xbmc.log('-----Name Error----')
                name = ''

            try:
                url = []
                for i in item('link'):
                    url.append(i.string)
            except:
                xbmc.log('---- URL Error Passing ----'+name)
                continue

            try:
                thumbnail = item('thumbnail')[0].string
                if thumbnail == None:
                    raise
            except:
                thumbnail = ''
            try:
                if not item('fanart'):
                    if addon.getSetting('use_thumb') == "true":
                        fanArt = thumbnail
                    else:
                        fanArt = fanart
                else:
                    fanArt = item('fanart')[0].string
                if fanArt == None:
                    raise
            except:
                fanArt = fanart
            try:
                desc = item('info')[0].string
                if desc == None:
                    raise
            except:
                desc = ''

            try:
                genre = item('genre')[0].string
                if genre == None:
                    raise
            except:
                genre = ''

            try:
                date = item('date')[0].string
                if date == None:
                    raise
            except:
                date = ''



def get_params():
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


def getFavorites():
        for i in json.loads(open(favorites).read()):
            name = i[0]
            url = i[1]
            iconimage = i[2]
            try:
                fanArt = i[3]
                if fanArt == None:
                    raise
            except:
                if addon.getSetting('use_thumb') == "true":
                    fanArt = iconimage
                else:
                    fanArt = fanart
            addLink(url,name,iconimage,fanArt,'','','')





def play_playlist(name, list):
        playlist = xbmc.PlayList(1)
        playlist.clear()
        item = 0
        for i in list:
            item += 1
            info = xbmcgui.ListItem('%s) %s' %(str(item),name))
            playlist.add(i, info)
        xbmc.executebuiltin('playlist.playoffset(video,0)')


def addDir(name,url,mode,iconimage,fanart,description,genre,date,showcontext=True):
        u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)+"&fanart="+urllib.quote_plus(fanart)
        ok=True
        liz=xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
        liz.setInfo( type="Video", infoLabels={ "Title": name, "Plot": description, "Genre": genre, "Date": date } )
        liz.setProperty( "Fanart_Image", fanart )
        # if showcontext == True:
            # try:
                # if name in str(SOURCES):
                    # contextMenu = [('Remove from Sources','XBMC.Container.Update(%s?mode=8&name=%s)' %(sys.argv[0], urllib.quote_plus(name)))]
                    # liz.addContextMenuItems(contextMenu, True)
            # except:
                # pass
        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)
        return ok


def addLink(url,name,iconimage,fanart,description,genre,date,showcontext=True,playlist=None):
        u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode=12"
        ok=True
        liz=xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
        liz.setInfo( type="Video", infoLabels={ "Title": name, "Plot": description, "Genre": genre, "Date": date } )
        liz.setProperty( "Fanart_Image", fanart )
        liz.setProperty('IsPlayable', 'true')



  # Thanks to daschacka, an epg scraper for http://i.teleboy.ch/programm/station_select.php - http://forum.xbmc.org/showpost.php?p=936228&postcount=1076
def getepg(link):
        url=urllib.urlopen(link)
        source=url.read()
        url.close()
        source2 = source.split("Jetzt")
        source3 = source2[1].split('programm/detail.php?const_id=')
        sourceuhrzeit = source3[1].split('<br /><a href="/')
        nowtime = sourceuhrzeit[0][40:len(sourceuhrzeit[0])]
        sourcetitle = source3[2].split("</a></p></div>")
        nowtitle = sourcetitle[0][17:len(sourcetitle[0])]
        nowtitle = nowtitle.replace("ö","oe")
        nowtitle = nowtitle.replace("ä","ae")
        nowtitle = nowtitle.replace("ü","ue")
        return "  - "+nowtitle+" - "+nowtime


xbmcplugin.setContent(int(sys.argv[1]), 'movies')
try:
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_UNSORTED)
except:
    pass
try:
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_LABEL)
except:
    pass
try:
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_DATE)
except:
    pass
try:
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_GENRE)
except:
    pass

params=get_params()

url=None
name=None
mode=None
playlist=None

try:
    url=urllib.unquote_plus(params["url"]).decode('utf-8')
except:
    pass
try:
    name=urllib.unquote_plus(params["name"])
except:
    pass
try:
    iconimage=urllib.unquote_plus(params["iconimage"])
except:
    pass
try:
    fanart=urllib.unquote_plus(params["fanart"])
except:
    pass
try:
    mode=int(params["mode"])
except:
    pass
try:
    playlist=eval(urllib.unquote_plus(params["playlist"]).replace('|',','))
except:
    pass

xbmc.log("Mode: "+str(mode))
if not url is None:
    xbmc.log("URL: "+str(url.encode('utf-8')))
xbmc.log("Name: "+str(name))


if mode==None:
    xbmc.log("getData")
    data = 'http://pastebin.com/raw/Cnm4FeBJ' 
    getData(data, fanart)

elif mode==2:
    xbmc.log("getChannelItems")
    getChannelItems(name,url,fanart)

elif mode==3:
    xbmc.log("")
    getSubChannelItems(name,url,fanart)

elif mode==4:
    xbmc.log("")
    getFavorites()

elif mode==5:
    xbmc.log("")
    try:
        name = name.split('\\ ')[1]
    except:
        pass
    try:
        name = name.split('  - ')[0]
    except:
        pass
    addFavorite(name,url,iconimage,fanart)

elif mode==6:
    xbmc.log("rmFavorite")
    try:
        name = name.split('\\ ')[1]
    except:
        pass
    try:
        name = name.split('  - ')[0]
    except:
        pass
    rmFavorite(name)

elif mode==7:
    xbmc.log("addSource")
    addSource(url)

elif mode==8:
    xbmc.log("rmSource")
    rmSource(name)

elif mode==9:
    xbmc.log("getUpdate")
    getUpdate()

elif mode==10:
    xbmc.log("getCommunitySources")
    getCommunitySources()

elif mode==11:
    xbmc.log("addSource")
    addSource(url)

elif mode==12:
    xbmc.log("setResolvedUrl")
    item = xbmcgui.ListItem(path=url)
    xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)

elif mode==13:
    xbmc.log("play_playlist")
    play_playlist(name, playlist)

xbmcplugin.endOfDirectory(int(sys.argv[1]))