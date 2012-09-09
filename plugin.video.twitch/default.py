import xbmcplugin
import xbmcgui
import sys
import urllib2,urllib,re
import xbmcaddon
import os
import xbmcvfs
try:
    import json
except:
    import simplejson as json

thisPlugin = int(sys.argv[1])
settings = xbmcaddon.Addon(id='plugin.video.twitch')
httpHeaderUserAgent = 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:6.0) Gecko/20100101 Firefox/6.0'
translation = settings.getLocalizedString
ITEMS_PER_SITE=20

def downloadWebData(url):
    try:
        req = urllib2.Request(url)
        req.add_header('User-Agent', httpHeaderUserAgent)
        response = urllib2.urlopen(req)
        data=response.read()
        response.close()
        return data
    except urllib2.URLError, e:
        xbmc.executebuiltin("XBMC.Notification("+translation(31000)+"," + translation(32001) +")")
	
def createMainListing():
    addDir(translation(30005),'','featured','')
    addDir(translation(30001),'','games','')
    addDir(translation(30002),'','following','')
    addDir(translation(30003),'','search','')
    addDir(translation(30004),'','settings','')
    xbmcplugin.endOfDirectory(thisPlugin)

def createFollowingList():
    username = settings.getSetting('username').lower()
    if not username:
        settings.openSettings()
        username = settings.getSetting('username').lower()
    jsonString = downloadWebData(url='http://api.justin.tv/api/user/favorites/'+username+'.json?limit=40&offset=0')
    xmlDataOnlineStreams = downloadWebData(url='http://api.justin.tv/api/stream/list.xml')
    if jsonString is None or xmlDataOnlineStreams is None:
        return
    jsonData=json.loads(jsonString)
    for x in jsonData:
        name = x['status']
        image = x['image_url_huge']
        loginname = x['login']
        if len(name) <= 0:
            name = loginname
        if xmlDataOnlineStreams.count('<login>'+loginname+'</login>') > 0:
            addLink(name,loginname,'play',image,loginname)
    xbmcplugin.endOfDirectory(thisPlugin)
	
def createListOfFeaturedStreams():
    jsonString=downloadWebData(url='https://api.twitch.tv/kraken/streams/featured')
    jsonData=json.loads(jsonString)
    for x in jsonData['featured']:
        try:
            image = x['stream']['channel']['logo']
            image = image.replace("http://","",1)
            image = urllib.quote(image)
            image = 'http://' + image
        except:
            image = ""
        name = x['stream']['channel']['status']
        if name == '':
            name = x['stream']['channel']['display_name']
        channelname = x['stream']['channel']['name']
        addLink(name,'...','play',image,channelname)
    xbmcplugin.endOfDirectory(thisPlugin)
 
def createListOfGames(index=0):
    jsonString=downloadWebData(url='https://api.twitch.tv/kraken/games/top?limit='+str(ITEMS_PER_SITE)+'&offset='+str(index*ITEMS_PER_SITE))
    jsonData=json.loads(jsonString)
    for x in jsonData['top']:
        try:
            name = str(x['game']['name'])
            game = urllib.quote(name)
            image = ''
        except:
            continue
        try:
            image = x['game']['images']['super']
            image = image.replace("http://","",1)
            image = urllib.quote(image)
            image = 'http://' + image
        except:
            image = ''
        addDir(name,game,'channel',image)
    if len(jsonData['top']) >= ITEMS_PER_SITE:
        addDir(translation(31001),'','games','',index+1)
    xbmcplugin.endOfDirectory(thisPlugin)

def search():
    keyboard = xbmc.Keyboard('', translation(30101))
    keyboard.doModal()
    if keyboard.isConfirmed() and keyboard.getText():
        search_string = urllib.quote_plus(keyboard.getText())
        sdata = downloadWebData('http://api.swiftype.com/api/v1/public/engines/search.json?callback=jQuery1337&q='+search_string+'&engine_key=9NXQEpmQPwBEz43TM592&page=1&per_page='+str(ITEMS_PER_SITE))
        sdata = sdata.replace('jQuery1337','');
        sdata = sdata[1:len(sdata)-1]
        jdata = json.loads(sdata)
        records = jdata['records']['broadcasts']
        for x in records:
            addLink(x['title'],x['user'],'play',x['thumbnail'],x['user'])
        xbmcplugin.endOfDirectory(thisPlugin)
	
def createListForGame(gameName, index=0):
    jsonString=downloadWebData(url='https://api.twitch.tv/kraken/streams?game='+gameName+'&limit='+str(ITEMS_PER_SITE)+'&offset='+str(index*ITEMS_PER_SITE))
    jsonData=json.loads(jsonString)
    for x in jsonData['streams']:
        try:
            image = x['channel']['logo']
            image = image.replace("http://","",1)
            image = urllib.quote(image)
            image = 'http://' + image
        except:
            image = ""
        name = x['channel']['status']
        if name == '':
            name = x['channel']['display_name']
        channelname = x['channel']['name']
        addLink(name,'...','play',image,channelname)
    if len(jsonData['streams']) >= ITEMS_PER_SITE:
        addDir(translation(31001),url,'channel','',index+1)
    xbmcplugin.endOfDirectory(thisPlugin)
	
def addLink(name,url,mode,iconimage,channelname):
        u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&channelname="+channelname
        ok=True
        liz=xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
        liz.setInfo( type="Video", infoLabels={ "Title": name } )
        liz.setProperty('IsPlayable', 'true')
        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz)
        return ok
		
def addDir(name,url,mode,iconimage,index=0):
        u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&siteIndex="+str(index)
        ok=True
        liz=xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
        liz.setInfo( type="Video", infoLabels={ "Title": name } )
        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)
        return ok
		
def get_request(url, headers=None):
        try:
            if headers is None:
                headers = {'User-agent' : httpHeaderUserAgent,
                           'Referer' : 'http://www.justin.tv/'}
            req = urllib2.Request(url,None,headers)
            response = urllib2.urlopen(req)
            link=response.read()
            response.close()
            return link
        except urllib2.URLError, e:
            errorStr = str(e.read())
            if hasattr(e, 'code'):
                if str(e.code) == '403':
                    if 'archive' in url:
                        xbmc.executebuiltin("XBMC.Notification("+translation(31000)+"," +translation(32003)+ " " +name+")")
                xbmc.executebuiltin("XBMC.Notification("+translation(31000)+"," + translation(32001) +")")

	
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
		
def getSwfUrl(channel_name):
        ''' Helper method to grab the swf url, resolving HTTP 301/302 along the way'''
        base_url = 'http://www.justin.tv/widgets/live_embed_player.swf?channel=%s' % channel_name
        headers = {'User-agent' : httpHeaderUserAgent,
                   'Referer' : 'http://www.justin.tv/'+channel_name}
        req = urllib2.Request(base_url, None, headers)
        response = urllib2.urlopen(req)
        return response.geturl()
		
def getBestJtvTokenPossible(name):
        '''Helper method to find another jtv token'''
        swf_url = getSwfUrl(name)
        headers = {'User-agent' : httpHeaderUserAgent,
                   'Referer' : swf_url}
        url = 'http://usher.justin.tv/find/'+name+'.json?type=any&group='
        data = json.loads(get_request(url,headers))
        bestVideoHeight = -1
        bestIndex = -1
        index = 0
        for x in data:
            value = x.get('token', '')
            videoHeight = int(x['video_height'])
            if (value != '') and (videoHeight > bestVideoHeight):
                bestVideoHeight = x['video_height']
                bestIndex = index  
            index = index + 1
        return data[bestIndex]

def playLive(name, play=False, password=None):
        swf_url = getSwfUrl(name)
        headers = {'User-agent' : httpHeaderUserAgent,
                   'Referer' : swf_url}
        chosenQuality = settings.getSetting('video')
        videoTypeName = 'any'
        if chosenQuality == '0':
            videoTypeName = 'any'
        elif chosenQuality == '1':
            videoTypeName = '720p'
        elif chosenQuality == '2':
            videoTypeName = '480p'
        elif chosenQuality == '3':
            videoTypeName = '360p'
        url = 'http://usher.justin.tv/find/'+name+'.json?type='+videoTypeName+'&private_code=null&group='
        data = json.loads(get_request(url,headers))
        tokenIndex = 0
        if data == []:
            xbmc.executebuiltin("XBMC.Notification("+translation(31000)+","+translation(32002)+")")
            return
        try:
            '''trying to get a token in desired quality'''
            token = ' jtv='+data[tokenIndex]['token'].replace('\\','\\5c').replace(' ','\\20').replace('"','\\22')
            rtmp = data[tokenIndex]['connect']+'/'+data[tokenIndex]['play']
        except:
            xbmc.executebuiltin("XBMC.Notification("+translation(32005)+","+translation(32006)+")")
            jtvtoken = getBestJtvTokenPossible(name)
            if jtvtoken == '':
                xbmc.executebuiltin("XBMC.Notification("+translation(31000)+","+translation(32004)+")")
                return
            token = ' jtv='+jtvtoken['token'].replace('\\','\\5c').replace(' ','\\20').replace('"','\\22')
            rtmp = jtvtoken['connect']+'/'+jtvtoken['play']
        
        swf = ' swfUrl=%s swfVfy=1 live=1' % swf_url
        Pageurl = ' Pageurl=http://www.justin.tv/'+name
        url = rtmp+token+swf+Pageurl
        if play == True:
            info = xbmcgui.ListItem(name)
            playlist = xbmc.PlayList(1)
            playlist.clear()
            playlist.add(url, info)
            xbmc.executebuiltin('playlist.playoffset(video,0)')
        else:
            item = xbmcgui.ListItem(path=url)
            xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)

params=parameters_string_to_dict(sys.argv[2])
mode=params.get('mode')
url=params.get('url')
sIndex=params.get('siteIndex')
try:
    index = int(sIndex)
except Exception:
    index = 0
channelname=params.get('channelname')
if type(url)==type(str()):
	url=urllib.unquote_plus(url)
if mode == 'games':
	createListOfGames(index)  
elif mode == 'featured':
	createListOfFeaturedStreams()
elif mode == 'channel':
	createListForGame(url, index)
elif mode == 'play':
	playLive(channelname)
elif mode == 'following':
	createFollowingList()
elif mode == 'settings':
	settings.openSettings()
elif mode == 'search':
	search()
else:
	createMainListing()

