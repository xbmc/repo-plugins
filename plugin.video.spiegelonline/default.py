# -*- coding: utf-8 -*-
# Copyright 2010 by peterpanzki
# Copyright 2013 cdwertmann

import urllib,urllib2,re,time,xbmcplugin,xbmcgui,xbmcaddon,threading

# plugin handle
SITE = "http://www1.spiegel.de/active/playlist/fcgi/playlist.fcgi/asset=flashvideo/mode=list/displaycategory="
VIDS = 20
VIDS_PER_SITE = "/count=" + str(VIDS) + "/" 
BASEURL="http://video.spiegel.de/flash/"
PLUGIN_NAME="plugin.video.spiegelonline"
handle = int(sys.argv[1])

__addon__        = xbmcaddon.Addon()
__language__     = __addon__.getLocalizedString
items = []

def show_root_menu():
    addDirectoryItem(__addon__.getLocalizedString(30003), {"cat": "newsmitfragmenten", "site": 1})  
    addDirectoryItem(__addon__.getLocalizedString(30004), {"cat": "politikundwirtschaft", "site": 1})
    addDirectoryItem(__addon__.getLocalizedString(30005), {"cat": "panorama2", "site": 1})
    addDirectoryItem(__addon__.getLocalizedString(30006), {"cat": "kino", "site": 1})
    addDirectoryItem(__addon__.getLocalizedString(30007), {"cat": "kultur", "site": 1})
    addDirectoryItem(__addon__.getLocalizedString(30008), {"cat": "sport2", "site": 1})
    addDirectoryItem(__addon__.getLocalizedString(30009), {"cat": "wissenundtechnik", "site": 1})
    addDirectoryItem(__addon__.getLocalizedString(30010), {"cat": "blogs", "site": 1})
    addDirectoryItem(__addon__.getLocalizedString(30011), {"cat": "spiegel%20tv%20magazin", "site": 1})      
    xbmcplugin.endOfDirectory(handle=handle, succeeded=True)

def show_cat_menu(cat, vnr):
    xbmcplugin.setContent(handle, "episodes")
    content = getUrl(SITE + (urllib.unquote_plus(cat)) + VIDS_PER_SITE + "start=" + vnr)
    match = re.compile('<listitem>(.+?)</listitem>',re.DOTALL).findall(content)
    for m in match:
        parts = re.compile('<videoid>(.+?)</videoid><thema>(.+?)</thema><headline>(.+?)</headline><teaser>(.+?)</teaser>.+?<date>(.+?)</date><playtime>(.+?)</playtime><thumb>(.+?)</thumb>',re.DOTALL).findall(m)
        for vid,name,headline,teaser,date,playtime,pic in parts:
            name=convert_to_UTF8(name)
            headline=convert_to_UTF8(headline)
            teaser=convert_to_UTF8(teaser)
            liStyle=xbmcgui.ListItem(label=(name + " - " + headline), iconImage="default.png", thumbnailImage=pic)
            liStyle.setInfo( type="Video", infoLabels={ "Title": name, "plotoutline": headline, "plot": teaser, "aired": date})
            liStyle.addStreamInfo('video', {'duration': getSeconds(playtime)})
            items.append({'vid': vid, "li" :liStyle})
    threads = []
    for index,i in enumerate(items):
      # pass the index to the thread function to preserve the original video order
      thread = threading.Thread(target=setVideoURL, args=(i['vid'],index,))
      thread.start()
      threads.append(thread)
    for t in threads:
      t.join()
    for i in items:
      if i['url'] != BASEURL:
        addLinkItem(i['url'],i['li'])
    #xbmc.log(str(SITE + cat + VIDS_PER_SITE + "start=" + str(int(vnr) + VIDS)), level=xbmc.LOGERROR)
    content = getUrl(SITE + cat + VIDS_PER_SITE + "start=" + str(int(vnr) + VIDS))
    match = re.compile('<listitem>(.+?)</listitem>',re.DOTALL).findall(content)
    if len(match) > 0:
        addDirectoryItem(__addon__.getLocalizedString(30001), {"cat": cat, "site": str(int(vnr) + VIDS)})
    addDirectoryItem(__addon__.getLocalizedString(30002),{"cat": "main"})        
    xbmcplugin.endOfDirectory(handle=handle, succeeded=True)
    xbmc.executebuiltin('Container.SetViewMode(504)')
    
def getVideo(id):
    content = None
    url = BASEURL + id + ".xml"
    try:
        content = getUrl(url)
    except Exception:
        xbmc.log(PLUGIN_NAME + ": Video not found: "+ str(url), level=xbmc.LOGNOTICE)
        return ""
    match = re.compile('<type(.+?)</type',re.DOTALL).findall(content)
    filename = ""
    streams = []
    for m in match:
        cat = re.compile('<filename>(.+?)</filename>.+?<totalbitrate>(.+?)</totalbitrate>',re.DOTALL).findall(m)
        for file,bitrate in cat:
            if (".mp4" in file or ".flv" in file):
                streams.append((file,int(bitrate)))
    #xbmc.log(str(streams), level=xbmc.LOGERROR)
    # sort streams by highest bitrate first
    streams.sort(key=lambda x: x[1], reverse=True)
    #xbmc.log(str(streams), level=xbmc.LOGERROR)
    for file,bitrate in streams:
        # find the best quality stream available
        if urllib.urlopen(BASEURL + file).getcode()==200:
            filename = file
            break
    return filename

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

def addDirectoryItem(name, parameters={},pic=""):
    li = xbmcgui.ListItem(name,iconImage="DefaultFolder.png", thumbnailImage=pic)
    url = sys.argv[0] + '?' + urllib.urlencode(parameters)
    return xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=url, listitem=li, isFolder=True)

def addLinkItem(url, li):
    return xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=url, listitem=li, isFolder=False, totalItems=len(items))

def setVideoURL(vid, index):
    items[index]['url']=BASEURL + getVideo(vid)

def getUrl(url):
    req = urllib2.Request(url)
    response = urllib2.urlopen(req)
    link=response.read()
    response.close()
    return link

def convert_to_UTF8(str):
    return str.decode('iso-8859-1').encode('utf8')

def getSeconds(playtime):
    t = map(int, re.split(r"[:]", playtime))
    if len(t)==1:
      return t[0]
    elif len(t)==2:
      return t[0]*60+t[1]
    elif len(t)==3:
      return t[0]*3600+t[1]*60+t[2]
    else:
      return 0

# parameter values
params = parameters_string_to_dict(sys.argv[2])
site = str(params.get("site", ""))
cat = str(params.get("cat", ""))
if not sys.argv[2]:
    # new start
    ok = show_root_menu()
else:
    if "main" in cat:
        ok = show_root_menu()
    else:
        ok = show_cat_menu(cat,site)