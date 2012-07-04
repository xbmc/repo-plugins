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
	
def createListOfGames(index=0):
    htmlData=downloadWebData(url='http://de.twitch.tv/directory?page='+str(index+1))
    if htmlData is None:
        return
    gameDiv=re.compile("(?<=<div class='boxart'>).+?</div>.+?(?=</div>)", re.MULTILINE|re.DOTALL).findall(htmlData)
    for x in gameDiv:
        name = re.compile("(?<=<h5 class='title'>).+?(?=</h5>)").findall(x)[0]
        dir = 'http://de.twitch.tv/directory/?category=' + urllib.quote_plus(name)
        image = re.compile('(?<=setPlaceholder\(this\);" src="http://).+?(?=" />)').findall(x)[0]
        image = urllib.quote(image)
        image = 'http://' + image
        addDir(name,dir,'channel',image)
    addDir(translation(31001),'','games','',index+1)
    xbmcplugin.endOfDirectory(thisPlugin)
	
def search():
    keyboard = xbmc.Keyboard('', translation(30101))
    keyboard.doModal()
    if keyboard.isConfirmed() and keyboard.getText():
        search_string = urllib.quote_plus(keyboard.getText())
        sdata = downloadWebData('http://api.swiftype.com/api/v1/public/engines/search.json?callback=jQuery1337&q='+search_string+'&engine_key=9NXQEpmQPwBEz43TM592&page=1&per_page=20')
        sdata = sdata.replace('jQuery1337','');
        sdata = sdata[1:len(sdata)-1]
        jdata = json.loads(sdata)
        records = jdata['records']['broadcasts']
        for x in records:
            addLink(x['title'],x['user'],'play',x['thumbnail'],x['user'])
        xbmcplugin.endOfDirectory(thisPlugin)
	
def createListForGame(url, index=0):
    htmlData=downloadWebData(url+ '&page=' + str(index+1))
    if htmlData is None:
        return
    videoDiv=re.compile("(?<=<div class='video  clearfix).+?(?=</div>)", re.MULTILINE|re.DOTALL).findall(htmlData)
    for x in videoDiv:
        image = re.compile('(?<=http://)static-cdn.jtvnw.net/previews/.+?(?=")', re.MULTILINE|re.DOTALL).findall(x)[0]
        image = urllib.quote(image)
        image = 'http://' + image
        nameAndLink = re.compile("(?<=<p class='title'>).+?(?=</a></p>)", re.MULTILINE|re.DOTALL).findall(x)[0]
        name = re.compile('(?<=\>).+?\Z', re.MULTILINE|re.DOTALL).findall(nameAndLink)[0]
        channelname = re.compile('(?<=<a href="/).+?(?=">)').findall(nameAndLink)[0]
        addLink(name,'...','play',image,channelname)
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
        """Helper method to grab the swf url, resolving HTTP 301/302 along the way"""
        base_url = 'http://www.justin.tv/widgets/live_embed_player.swf?channel=%s' % channel_name
        headers = {'User-agent' : httpHeaderUserAgent,
                   'Referer' : 'http://www.justin.tv/'+channel_name}
        req = urllib2.Request(base_url, None, headers)
        response = urllib2.urlopen(req)
        return response.geturl()		
		
def playLive(name, play=False, password=None):
        swf_url = getSwfUrl(name)
        headers = {'User-agent' : httpHeaderUserAgent,
                   'Referer' : swf_url}
        url = 'http://usher.justin.tv/find/'+name+'.json?type=live&group='
        data = json.loads(get_request(url,headers))
        if data == []:
            xbmc.executebuiltin("XBMC.Notification("+translation(31000)+","+translation(32002)+")")
            return
        try:
            token = ' jtv='+data[0]['token'].replace('\\','\\5c').replace(' ','\\20').replace('"','\\22')
        except:
            xbmc.executebuiltin("XBMC.Notification("+translation(31000)+","+translation(32004)+")")
            return
        rtmp = data[0]['connect']+'/'+data[0]['play']
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

