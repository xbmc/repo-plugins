import urllib,urllib2,re
import xbmcplugin,xbmcgui,xbmcaddon
import simplejson as json
import gzip,StringIO,os

__settings__ = xbmcaddon.Addon(id='plugin.video.flw.outdoors')
__language__ = __settings__.getLocalizedString
__home__ = __settings__.getAddonInfo('path')
icon = xbmc.translatePath( os.path.join( __home__, 'icon.png' ) )


def CATEGORIES():
        addDir(__language__(30000),'flwlatestvideos',1,icon)
        addDir(__language__(30001),'flwtourtv',1,icon)
        addDir(__language__(30002),'flwseriestv',1,icon)
        addDir(__language__(30003),'collegefishingtv',1,icon)
        addDir(__language__(30004),'forrestwoodcuptv',1,icon)
        addDir(__language__(30005),'walleyetourtv',1,icon)
        addDir(__language__(30006),'bfltv',1,icon)
        addDir(__language__(30007),'tipsfromthepros',1,icon)
        addDir(__language__(30008),'fantasyonflw',1,icon)		
        addDir(__language__(30009),'flwpodcast',1,icon)
        addDir(__language__(30010),'flwtour',1,icon)
        addDir(__language__(30011),'collegeonflw',1,icon)


def INDEX(url):
        url='http://www.flwoutdoors.com/flwMedia/ajax.cfm?callsign='+url+'&method=getVideosInChannel'
        page=urllib2.urlopen(url)
        gzip_filehandle=gzip.GzipFile(fileobj=StringIO.StringIO(page.read()))
        data=json.loads(gzip_filehandle.read())
        videos = data["CHANNEL"]["AFILE"]
        for video in videos:
                title = video["TITLE"]
                path = video["PATH"]
                thumbnail = video["THUMBNAIL"]
                description = video["DESCRIPTION"]
                addLink (title,path,description,thumbnail)


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


def addLink(name,url,description,iconimage):
        ok=True
        liz=xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
        liz.setInfo( type="Video", infoLabels={ "Title": name, "Plot": description } )
        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=url,listitem=liz)
        return ok


def addDir(name,url,mode,iconimage):
        u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)
        ok=True
        liz=xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
        liz.setInfo( type="Video", infoLabels={ "Title": name } )
        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)
        return ok
        
              
params=get_params()
url=None
name=None
mode=None

try:
        url=urllib.unquote_plus(params["url"])
except:
        pass
try:
        name=urllib.unquote_plus(params["name"])
except:
        pass
try:
        mode=int(params["mode"])
except:
        pass

print "Mode: "+str(mode)
print "URL: "+str(url)
print "Name: "+str(name)

if mode==None or url==None or len(url)<1:
        print ""
        CATEGORIES()
       
elif mode==1:
        print ""+url
        INDEX(url)

xbmcplugin.endOfDirectory(int(sys.argv[1]))
