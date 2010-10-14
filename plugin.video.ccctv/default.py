# Copyright 2010 by peterpanzki
import urllib,urllib2,re,xbmcplugin,xbmcgui

# plugin handle
handle = int(sys.argv[1])
SITE = "http://media.ccc.de"

def show_root_menu():
    content = getUrl(SITE + "/browse")
    match = re.compile('<div class="thumbnail">(.+?)<div class="icons">',re.DOTALL).findall(content)
    for m in match:
        cat = re.compile('<img src="(.+?)".+?title="(.+?)".+?href="(.+?)"',re.DOTALL).findall(m)
        for img,name,url in cat:
            addDirectoryItem(name,parameters={"url": url},pic=(SITE + img))        
    xbmcplugin.endOfDirectory(handle=handle, succeeded=True)

def show_sites(site):
    content = getUrl(urllib.unquote(SITE + "/browse/" + site))
    match = re.compile('<div class="thumbnail">(.+?)<div class="icons">',re.DOTALL).findall(content)
    for m in match:
        cat = re.compile('<img src="(.+?)".+?title="(.+?)".+?href="(.+?)"',re.DOTALL).findall(m)
        for img,name,url in cat:
            try:
                if url.find(".html") != -1:
                    a = getUrl(urllib.unquote(SITE + "/browse/" + site + "/" + url))
                    newsite = re.compile('<b>Original File:</b> <a href="(.+?)"').findall(a)                
                    liStyle=xbmcgui.ListItem(name, iconImage="default.png", thumbnailImage=SITE + img.replace(" ","%20"))
                    liStyle.setInfo( type="Video", infoLabels={ "Title": name })
                    addLinkItem(newsite[0].replace(" ","%20"), liStyle)             
                else:
                    addDirectoryItem(name,parameters={"url": urllib.unquote((site + "/" + url))},pic=(SITE + img))
            except:
                1
    xbmcplugin.endOfDirectory(handle=handle, succeeded=True)

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
site = str(params.get("url", ""))
if not sys.argv[2]:
    # new start
    ok = show_root_menu()
else:
    ok = show_sites(site)