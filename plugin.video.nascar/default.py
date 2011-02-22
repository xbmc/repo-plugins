import urllib,urllib2,re,xbmcplugin,xbmcgui,xbmcaddon

#NascarX - by divingmule. Special Thanks to Vionage for the tutorial. http://wiki.xbmc.org/?title=HOW-TO_write_plugins_for_XBMC

__settings__ = xbmcaddon.Addon(id='plugin.video.nascar')
__language__ = __settings__.getLocalizedString


def INDEX(url):
        url = 'http://i.cdn.turner.com/nascar/feeds/partners/embeded_player/latest.xml'
        req = urllib2.Request(url)
        req.addheaders = [('Referer', 'http://www.nascar.com/videos'),
                          ('Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.2.3) Gecko/20100401 Firefox/3.6.3 ( .NET CLR 3.5.30729)')]
        response = urllib2.urlopen(req)
        link=response.read()
        response.close()
        match=re.compile('<CATEGORY>.+?</CATEGORY>\n<TITLE>(.+?)</TITLE>\n<DESCRIPTION>.+?</DESCRIPTION>\n<URL ID="(.+?)">\n<SITEURL>.+?</SITEURL>\n</URL>\n<IMAGE>(.+?)</IMAGE>').findall(link)
        for name,url,thumbnail in match:
                addLink('http://ht.cdn.turner.com/nascar/big/'+url+'.nascar_640x360.mp4',name,thumbnail)
				

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


def addLink(url,name,iconimage):
        ok=True
        liz=xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
        liz.setInfo( type="Video", infoLabels={ "Title": name } )
        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=url,listitem=liz)
        return ok


def addDir(name,url,mode,iconimage):
        u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)
        ok=True
        liz=xbmcgui.ListItem(name, iconImage="special://home/addons/plugin.video.nascar/fanart.jpg", thumbnailImage=iconimage)
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
        INDEX(url)

xbmcplugin.endOfDirectory(int(sys.argv[1]))
