import urllib2, urllib

import xbmcplugin, xbmcgui

import youtube

max_elems = 10
page = 1
path = "/"


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

def addLink(name,descr, url,iconimage):
        li = xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
        li.setProperty("IsPlayable", "true")
        li.setInfo( type="Video", infoLabels={ "Title": name , "plot": descr, "plotoutline": descr} )
        xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=url,listitem=li, isFolder=False, totalItems=max_elems)

def addDir(name,path,page,iconimage):
    u=sys.argv[0]+"?path=%s&page=%s"%(path,str(page))
    li=xbmcgui.ListItem(name, iconImage="DefaultFolder.png",thumbnailImage=iconimage)
    li.setInfo( type="Video", infoLabels={ "Title": name })
    xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=li,isFolder=True)

params=get_params()



try:
        page = int(urllib.unquote_plus(params["page"]))
except:
        pass

try:
    path = urllib.unquote_plus(params["path"])
except:
    pass

if path == "/":
    addDir("Order By: Publication Date", "/orderbypublished", 1, "")
    addDir("Order By: View Count", "/orderbyviewcount", 1, "")
    addDir("Order By: Relevance", "/orderbyrelevance", 1, "")

else:
    if path == "/orderbypublished":
        orderby = "published"
    elif path == "/orderbyrelevance":
        orderby = "relevance"
    elif path == "/orderbyviewcount":
        orderby = "viewCount"
    else:
        orderby = "published"

    addDir("> Next Page", path, page+1, "")

    # videos
    for entry in youtube.fetch_data(page, max_elems, orderby):
        addLink(entry.title, entry.description, entry.videourl(), entry.img())

xbmcplugin.endOfDirectory(int(sys.argv[1]))
