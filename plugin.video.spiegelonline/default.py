# Copyright 2010 by peterpanzki
import urllib,urllib2,re,time,xbmcplugin,xbmcgui

# plugin handle
SITE = "http://www1.spiegel.de/active/playlist/fcgi/playlist.fcgi/asset=flashvideo/mode=list/displaycategory="
VIDS = 20
VIDS_PER_SITE = "/count=" + str(VIDS) + "/" 
handle = int(sys.argv[1])

def show_root_menu():
    addDirectoryItem("News", {"cat": "newsmitfragmenten", "site": 1})  
    addDirectoryItem("Politik & Wirtschaft", {"cat": "politikundwirtschaft", "site": 1})
    addDirectoryItem("Panorama", {"cat": "panorama2", "site": 1})
    addDirectoryItem("Kino", {"cat": "kino", "site": 1})
    addDirectoryItem("Kultur", {"cat": "kultur", "site": 1})
    addDirectoryItem("Sport", {"cat": "sport2", "site": 1})
    addDirectoryItem("Wissen & Technik", {"cat": "wissenundtechnik", "site": 1})
    addDirectoryItem("Serien & Blogs", {"cat": "blogs", "site": 1})
    addDirectoryItem("Spiegel TV Magazin", {"cat": "spiegel%20tv%20magazin", "site": 1})      
    xbmcplugin.endOfDirectory(handle=handle, succeeded=True)

def show_cat_menu(cat, vnr):
    content = getUrl(SITE + cat + VIDS_PER_SITE + "start=" + vnr)
    match = re.compile('<listitem>(.+?)</listitem>',re.DOTALL).findall(content)
    for m in match:
        parts = re.compile('<videoid>(.+?)</videoid><thema>(.+?)</thema><headline>(.+?)</headline><teaser>(.+?)</teaser>.+?<date>(.+?)</date><playtime>(.+?)</playtime><thumb>(.+?)</thumb>',re.DOTALL).findall(m)
        for vid,name,headline,teaser,date,playtime,pic in parts:
            liStyle=xbmcgui.ListItem(name + " - " + headline, iconImage="default.png", thumbnailImage=pic)
            liStyle.setInfo( type="Video", infoLabels={ "Title": name, "duration": playtime, "plotoutline": headline, "plot": teaser, "date": date})
            addLinkItem("http://video.spiegel.de/flash/" + getVideo(vid), liStyle)
    content = getUrl(SITE + cat + VIDS_PER_SITE + "start=" + str(int(vnr) + VIDS))
    match = re.compile('<listitem>(.+?)</listitem>',re.DOTALL).findall(content)
    if len(match) > 0:
        addDirectoryItem("Nächste Seite", {"cat": cat, "site": str(int(vnr) + VIDS)})
    addDirectoryItem("Zum Hauptmenü",{"cat": "main"})        
    xbmcplugin.endOfDirectory(handle=handle, succeeded=True)
    
def getVideo(id):
    content = getUrl("http://video.spiegel.de/flash/" + id + ".xml")
    match = re.compile('<type(.+?)</type',re.DOTALL).findall(content)
    hbitrate = 0
    filename = ""
    for m in match:
        cat = re.compile('<filename>(.+?)</filename>.+?<totalbitrate>(.+?)</totalbitrate>',re.DOTALL).findall(m)
        for file,bitrate in cat:
            if (".mp4" in file or ".flv" in file) and int(bitrate) > hbitrate:
                hbitrate = int(bitrate)
                filename = file
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

def addLinkItem(url,li):
    return xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=url, listitem=li, isFolder=False)

def getUrl(url):
    req = urllib2.Request(url)
    response = urllib2.urlopen(req)
    link=response.read()
    response.close()
    return link

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