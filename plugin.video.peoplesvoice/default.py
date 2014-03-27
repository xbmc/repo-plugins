# -*- coding: cp1252 -*-
import urllib,urllib2,re,xbmcplugin,xbmcgui
import xbmcaddon

#The People's Voice plugin 2013

addon         = xbmcaddon.Addon('plugin.video.peoplesvoice')
__language__  = addon.getLocalizedString
__icon__ = addon.getAddonInfo('icon')

def CATEGORIES():
        
        addDir(__language__(30010)+__language__(30018),'http://www.thepeoplesvoice.tv/watchnow/',1,__icon__,__language__(30013))
        addDir(__language__(30016),'http://www.thepeoplesvoice.tv/whatson/',3,__icon__,__language__(30013))
        addDir(__language__(30017),'http://www.thepeoplesvoice.tv/show/',4,__icon__,__language__(30013))
        addLink(__language__(30010)+__language__(30011),'http://cdn.rbm.tv:1935/rightbrainmedia-live-106/_definst_/ddstream_3/playlist.m3u8',__icon__,__language__(30013)+__language__(30012))
        
def INDEX(url):
        
        req = urllib2.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.2; Win64; x64; rv:16.0.1) Gecko/20121011 Firefox/16.0.1')
        response = urllib2.urlopen(req)
        link=response.read()
        response.close()
        #Scrape video source
        match=re.compile('"TPV" src="(.+?)"').findall(link)
        if len(match) > 0:        
                for url in match:
                       addDir(__language__(30010)+__language__(30018),url,2,__icon__,__language__(30014)+__language__(30015)+__language__(30012))   
        else:
                xbmc.log(__language__(30019), xbmc.LOGERROR )
                xbmcgui.Dialog().ok(__language__(30010), __language__(30019))
        
def INDEX2(url):

        req = urllib2.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.2; Win64; x64; rv:16.0.1) Gecko/20121011 Firefox/16.0.1')
        response = urllib2.urlopen(req)
        link=response.read()
        response.close()
        #Scrape program schedule
        match=re.compile('src="(.+?)" width=".+?></td>\n<td><b>(.+?)<').findall(link)#schedule
        week = [__language__(30021),__language__(30022),__language__(30023),__language__(30024),__language__(30025),__language__(30026),__language__(30027)]
        day = 0
        dayset = 0
        if len(match) > 0:
                for image,name in match:
                        name = name.replace('&quot;', '"').replace('&#039;', "'").replace('&amp;', '&').replace('&#8217;', "'")  # Cleanup the title.
                        name = name.replace(' GMT', 'GMT').replace('T 0:', 'T 00:').replace('T 1:', 'T 01:').replace('T 2:', 'T 02:').replace('T 3:', 'T 03:').replace('T 4:', 'T 04:').replace('T 5:', 'T 05:').replace('T 6:', 'T 06:').replace('T 7:', 'T 07:').replace('T 8:', 'T 08:').replace('T 9:', 'T 09:')
                        if name[4] < dayset and dayset == "2":
                                day = day +1
                        if day > 6:
                                day = 0
                        dayset = name[4]
                        addDir(week[day]+name,'http://rbm.myrbm.tv/player.php?pID=145',2,image,week[day]+name)
        else:
                xbmc.log(__language__(30020), xbmc.LOGERROR )
                xbmcgui.Dialog().ok(__language__(30010), __language__(30020))


def INDEX3(url):

        req = urllib2.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.2; Win64; x64; rv:16.0.1) Gecko/20121011 Firefox/16.0.1')
        response = urllib2.urlopen(req)
        link=response.read()
        response.close()
        #Scrape shows
        match=re.compile('<b>(.+?)</b></br>(.+?)</p>\n</p>\n<p></a></br></p>\n<p><a href=".+?"><img src="(.+?)" width').findall(link)
        if len(match) > 0:
                for name,description,image in match:
                        description = description.replace('&quot;', '"').replace('&#039;', "'").replace('&amp;', '&').replace('&#8217;', "'").replace('&#8211;', "-")  # Cleanup the description.
                        name = name.replace('&quot;', '"').replace('&#039;', "'").replace('&amp;', '&').replace('&#8217;', "'")  # Cleanup the description.
                        addDir(name,'',0,image,description)
        else:
                xbmc.log(__language__(30019), xbmc.LOGERROR )
                xbmcgui.Dialog().ok(__language__(30010), __language__(30019))
                

def VIDEOLINKS(url,name):

        req = urllib2.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.2; Win64; x64; rv:16.0.1) Gecko/20121011 Firefox/16.0.1')
        response = urllib2.urlopen(req)
        link=response.read()
        response.close()   
        #Scrape video source
        match=re.compile('href="(.+?)">(.+?)<').findall(link)#video links 
        for url,name in match:
                name = name.replace('&quot;', '"').replace('&#039;', "'").replace('&amp;', '&').replace('&#8217;', "'")  # Cleanup the title.
                addLink(name+__language__(30018),url,__icon__,__language__(30013))

              


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

elif mode==4:
        print ""+url
        INDEX3(url)
 

xbmcplugin.endOfDirectory(int(sys.argv[1]))
