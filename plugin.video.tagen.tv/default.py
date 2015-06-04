# -*- coding: cp1252 -*-
import urllib,urllib2,re,xbmcplugin,xbmcgui
import xbmcaddon
import sys
# Set default encoding to 'UTF-8' instead of 'ascii'
reload(sys)
sys.setdefaultencoding("UTF8")

#tagen.tv plugin

addon         = xbmcaddon.Addon('plugin.video.tagen.tv')
__language__  = addon.getLocalizedString
__icon__ = addon.getAddonInfo('icon')



def CATEGORIES():
        addLink(__language__(30015)+__language__(30018),'rtmp://213.189.53.89:80/live/ playpath=glowna swfUrl="http://p.jwpcdn.com/6/12/jwplayer.flash.swf" pageUrl="http://tagen.tv/" swfVfy=true live=true',__icon__,__language__(30018))
        addDir(__language__(30015)+__language__(30017),'http://tagen.tv',3,__icon__,__language__(30015)+__language__(30017))
        addDir(__language__(30015)+__language__(30014),'http://tagen.tv/vod/tag/',1,__icon__,__language__(30015)+__language__(30014))
        addDir('Krzysztof Jackowski-'+__language__(30016),'http://tagen.tv/vod/tag/krzysztof-jackowski/',2,__icon__,'Krzysztof Jackowski-'+__language__(30016))
        

                     
def INDEX(url):
        req = urllib2.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
        response = urllib2.urlopen(req)
        link=response.read()
        response.close()
        #the rest
        match=re.compile('href="/vod/tag/(.+?)/"').findall(link)
        if len(match) > 0:
               for url in match:
                      formattedname = url.replace("-"," ").title()
                      addDir(formattedname,'http://tagen.tv/vod/tag/'+url,2,__icon__,url+__language__(30019)+__language__(30020))
        else:
                xbmc.log(__language__(30021), xbmc.LOGERROR )
                xbmcgui.Dialog().ok(__language__(30022), __language__(30021))
        

def INDEX2(url):
        req = urllib2.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
        response = urllib2.urlopen(req)
        link=response.read()
        response.close()
        #the rest
        match=re.compile('<a href="/vod(.+?)" class=".+?">\n        <img src="(.+?)"').findall(link)
        if len(match) > 0:
               for url,thumb in match:
                      formattedurl = url.replace("/01/","/1/").replace("/02/","/2/").replace("/03/","/3/").replace("/04/","/4/").replace("/05/","/5/").replace("/06/","/6/").replace("/07/","/7/").replace("/08/","/8/").replace("/09/","/9/")
                      addLink(url[1:-1].replace("-"," ").replace("/","-"),'rtmp://213.189.53.89:80/vod/ playpath=mp4:vod'+formattedurl[:-1]+'.mp4',thumb,url+__language__(30019)+__language__(30020))
 
        else:
                xbmc.log(__language__(30021), xbmc.LOGERROR )
                xbmcgui.Dialog().ok(__language__(30022), __language__(30021))

def PLANNER(url):
        req = urllib2.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
        response = urllib2.urlopen(req)
        link=response.read()
        response.close()
        match=re.compile('href="(.+?)" >Planer').findall(link)
        for url in match:
                addDir(url,url,4,__icon__,'http://tagen.tv'+url+__language__(30019)+__language__(30020))

def PROGRAMS(url):
        req = urllib2.Request('http://tagen.tv'+url)
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
        response = urllib2.urlopen(req)
        link=response.read()
        response.close()
        mat=re.compile("title : '(.+?)'").findall(link)
        match=re.compile("start : '(.+?)'").findall(link)
        for index in range(len(mat)):
                addDir(mat[index]+' [COLOR yellow]('+match[index]+')[/COLOR]',url,0,__icon__,__language__(30013)+' [COLOR yellow]('+match[index]+')[/COLOR]'+__language__(30012)+__language__(30019)+__language__(30020))
        

                
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
        liz.setInfo( type="Video", infoLabels={ "Title": name , "Plot": description} )
        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=url,listitem=liz)
        return ok


def addDir(name,url,mode,iconimage,description):
        u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)
        ok=True
        liz=xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
        liz.setInfo( type="Video", infoLabels={ "Title": name , "Plot": description} )
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
        INDEX2(url)

elif mode==3:
        print ""+url
        PLANNER(url)

elif mode==4:
        print ""+url
        PROGRAMS(url)
        
xbmcplugin.endOfDirectory(int(sys.argv[1]))
