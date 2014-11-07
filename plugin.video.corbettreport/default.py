# -*- coding: cp1252 -*-
import urllib,urllib2,re,xbmcplugin,xbmcgui
import xbmcaddon
import sys
# Set default encoding to 'UTF-8' instead of 'ascii'
reload(sys)
sys.setdefaultencoding("UTF8")

#CorbettReport.com Video Podcast plugin 2013

addon         = xbmcaddon.Addon('plugin.video.corbettreport')
__language__  = addon.getLocalizedString
__icon__ = addon.getAddonInfo('icon')
__fanart__ = addon.getAddonInfo('fanart')



def CATEGORIES():
        addDir(__language__(30011),'http://www.corbettreport.com/category/videos/',1,__icon__,__language__(30018))
        addDir(__language__(30016),'http://www.corbettreport.com/category/podcasts/',3,'',__language__(30018))
        addDir(__language__(30017),'http://www.corbettreport.com/category/interviews/',3,'',__language__(30018))
        addDir(__language__(30023),'http://www.corbettreport.com/category/videos/',4,__icon__,__language__(30018))
     
                       
def INDEX(url):
        req = urllib2.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
        response = urllib2.urlopen(req)
        link=response.read()
        response.close()
        #the rest
        match=re.compile('post-title"><a href="(.+?)" rel="bookmark" title="Permanent Link to (.+?)"').findall(link)
        if len(match) > 0:
               for url,name in match:
                      name = name.replace('&#8211;', '"').replace('&#8217;', ' ').replace('&amp;', '&').replace('&#8210;', "'").replace('&#8220;', "'").replace('&#8221;', "'")  # Cleanup the title.
                      addDir(name,url,2,__icon__,name+__language__(30019)+__language__(30020))
        else:
                xbmc.log(__language__(30021), xbmc.LOGERROR )
                xbmcgui.Dialog().ok(__language__(30022), __language__(30021))

def INDEX2(url):
        req = urllib2.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
        response = urllib2.urlopen(req)
        link=response.read()
        response.close()
        #interviews and podcasts
        match=re.compile('<option value="(.+?)">(.+?)</option').findall(link)
        if len(match) > 0:
               for url,name in match:
                      name = name.replace('&quot;', '"').replace('&#8217;', ' ').replace('&amp;', '&').replace('&#8211;', "'").replace('&#8220;', "'").replace('&#8221;', "'")  # Cleanup the title.
                      addDir(name,url,2,__icon__,name+" "+name+__language__(30019)+__language__(30020))
        else:
                xbmc.log(__language__(30021), xbmc.LOGERROR )
                xbmcgui.Dialog().ok(__language__(30022), __language__(30021))

        

def INDEX3(url):
        req = urllib2.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
        response = urllib2.urlopen(req)
        link=response.read()
        response.close()
        #the rest
        match=re.compile('<option value="(.+?)">(.+?)</option>').findall(link)#ALL Videos
        if len(match) > 0:
               for url,name in match:
                      name = name.replace('&#8211;', '"').replace('&#8217;', ' ').replace('&amp;', '&').replace('&#8210;', "'").replace('&#8220;', "'").replace('&#8221;', "'")  # Cleanup the title.
                      addDir(name,url,2,__icon__,name+__language__(30019)+__language__(30020))
        else:
                xbmc.log(__language__(30021), xbmc.LOGERROR )
                xbmcgui.Dialog().ok(__language__(30022), __language__(30021))

def VIDEOLINKS(url,name):
        req = urllib2.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
        response = urllib2.urlopen(req)
        link=response.read()
        response.close()
        match=re.compile('">Podcast: <a href="(.+?)"').findall(link)
        for url in match:
                addLink(name,url,__fanart__)
        

                
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




def addLink(name,url,iconimage):
        ok=True
        liz=xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
        liz.setInfo( type="Video", infoLabels={ "Title": name } )
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
        VIDEOLINKS(url,name)

elif mode==3:
        print ""+url
        INDEX2(url)

elif mode==4:
        print ""+url
        INDEX3(url)



xbmcplugin.endOfDirectory(int(sys.argv[1]))
