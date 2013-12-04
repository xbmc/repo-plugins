# -*- coding: cp1252 -*-
import urllib,urllib2,re,xbmcplugin,xbmcgui
import xbmcaddon

#The People's Voice plugin 2013

addon         = xbmcaddon.Addon('plugin.video.peoplesvoice')
__language__  = addon.getLocalizedString

def CATEGORIES():
        
        addDir(__language__(30010),'http://www.thepeoplesvoice.tv/watchnow',1,'http://thepeoplesvoice.tv/images/footer-logo.gif',__language__(30013))
        addDir(__language__(30016),'http://www.thepeoplesvoice.tv/schedule',3,'http://thepeoplesvoice.tv/images/footer-logo.gif',__language__(30013))
        
        
def INDEX(url):
        req = urllib2.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.2; Win64; x64; rv:16.0.1) Gecko/20121011 Firefox/16.0.1')
        response = urllib2.urlopen(req)
        link=response.read()
        response.close()
        #Scrape video source
        match=re.compile('"TPV" href="(.+?)"><span style="color: #ffffff;">(.+?)</span').findall(link)
        for url,name in match:
                addDir(__language__(30010)+name,url,2,'http://thepeoplesvoice.tv/images/footer-logo.gif',__language__(30014)+__language__(30015)+__language__(30012))   

def INDEX2(url):
        req = urllib2.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.2; Win64; x64; rv:16.0.1) Gecko/20121011 Firefox/16.0.1')
        response = urllib2.urlopen(req)
        link=response.read()
        response.close()
        #Scrape video source
        match=re.compile('"date-display-start">(.+?)</span> to <span class="date-display-end">(.+?)</span></span><br /><span class="show-title">(.+?)</span><br /><span class="show-host">(.+?)</span>').findall(link)

        for starttime,endtime,name,plot in match:
                addDir(starttime+' - '+endtime+'   '+name,'',0,'http://thepeoplesvoice.tv/images/footer-logo.gif',plot)                         

def VIDEOLINKS(url,name):

        req = urllib2.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.2; Win64; x64; rv:16.0.1) Gecko/20121011 Firefox/16.0.1')
        response = urllib2.urlopen(req)
        link=response.read()
        response.close()
        
        #Scrape video source
        match=re.compile('window.location.href = "(.+?)"').findall(link)
        
        for url in match:
                addLink(name+__language__(30011),url,'http://thepeoplesvoice.tv/images/footer-logo.gif',__language__(30013))

              


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




def addLink(name,url,iconimage,description):
        ok=True
        liz=xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
        liz.setInfo( type="Video", infoLabels={ "Title": name, "Plot": description } )
        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=url,listitem=liz)
        return ok


def addDir(name,url,mode,iconimage,description):
        u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)
        ok=True
        liz=xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
        liz.setInfo( type="Video", infoLabels={ "Title": name, "Plot": description} )
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

elif mode==2:
        print ""+url
        VIDEOLINKS(url,name)

elif mode==3:
        print ""+url
        INDEX2(url)  


xbmcplugin.endOfDirectory(int(sys.argv[1]))
