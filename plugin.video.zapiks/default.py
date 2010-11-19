import urllib,urllib2,re,xbmcplugin,xbmcgui,xbmcaddon
from BeautifulSoup import BeautifulSoup

__settings__ = xbmcaddon.Addon(id='plugin.video.zapiks')
__language__ = __settings__.getLocalizedString
sort = __settings__.getSetting('sort_by')


def CATEGORIES():
        if sort==__language__(30010):
		    u = '1'
		    addDir(__language__(30000),'http://www.zapiks.fr/surf_'+u,1,'special://home/addons/plugin.video.zapiks/resources/images/surf.png')
		    addDir(__language__(30001),'http://www.zapiks.fr/snowboard_'+u,1,'special://home/addons/plugin.video.zapiks/resources/images/snowboard.png')
		    addDir(__language__(30002),'http://www.zapiks.fr/vtt_'+u,1,'special://home/addons/plugin.video.zapiks/resources/images/vtt.png')
		    addDir(__language__(30003),'http://www.zapiks.fr/bmx_'+u,1,'special://home/addons/plugin.video.zapiks/resources/images/bmx.png')
		    addDir(__language__(30004),'http://www.zapiks.fr/skate_'+u,1,'special://home/addons/plugin.video.zapiks/resources/images/skate.png')
		    addDir(__language__(30005),'http://www.zapiks.fr/ski_'+u,1,'special://home/addons/plugin.video.zapiks/resources/images/ski.png')
        elif sort==__language__(30011):
		    u = '/popular_1.php'
		    addDir(__language__(30000),'http://www.zapiks.fr/surf_'+u,1,'special://home/addons/plugin.video.zapiks/resources/images/surf.png')
		    addDir(__language__(30001),'http://www.zapiks.fr/snowboard_'+u,1,'special://home/addons/plugin.video.zapiks/resources/images/snowboard.png')
		    addDir(__language__(30002),'http://www.zapiks.fr/vtt_'+u,1,'special://home/addons/plugin.video.zapiks/resources/images/vtt.png')
		    addDir(__language__(30003),'http://www.zapiks.fr/bmx_'+u,1,'special://home/addons/plugin.video.zapiks/resources/images/bmx.png')
		    addDir(__language__(30004),'http://www.zapiks.fr/skate_'+u,1,'special://home/addons/plugin.video.zapiks/resources/images/skate.png')
		    addDir(__language__(30005),'http://www.zapiks.fr/ski_'+u,1,'special://home/addons/plugin.video.zapiks/resources/images/ski.png')
        elif sort==__language__(30012):
		    u = '/alltimebuzzed_1.php'
		    addDir(__language__(30000),'http://www.zapiks.fr/surf_'+u,1,'special://home/addons/plugin.video.zapiks/resources/images/surf.png')
		    addDir(__language__(30001),'http://www.zapiks.fr/snowboard_'+u,1,'special://home/addons/plugin.video.zapiks/resources/images/snowboard.png')
		    addDir(__language__(30002),'http://www.zapiks.fr/vtt_'+u,1,'special://home/addons/plugin.video.zapiks/resources/images/vtt.png')
		    addDir(__language__(30003),'http://www.zapiks.fr/bmx_'+u,1,'special://home/addons/plugin.video.zapiks/resources/images/bmx.png')
		    addDir(__language__(30004),'http://www.zapiks.fr/skate_'+u,1,'special://home/addons/plugin.video.zapiks/resources/images/skate.png')
		    addDir(__language__(30005),'http://www.zapiks.fr/ski_'+u,1,'special://home/addons/plugin.video.zapiks/resources/images/ski.png')
        elif sort==__language__(30013):
		    u = '/premium_1.php'
		    addDir(__language__(30000),'http://www.zapiks.fr/_surf_'+u,1,'special://home/addons/plugin.video.zapiks/resources/images/surf.png')
		    addDir(__language__(30001),'http://www.zapiks.fr/_snowboard_'+u,1,'special://home/addons/plugin.video.zapiks/resources/images/snowboard.png')
		    addDir(__language__(30002),'http://www.zapiks.fr/_vtt_'+u,1,'special://home/addons/plugin.video.zapiks/resources/images/vtt.png')
		    addDir(__language__(30003),'http://www.zapiks.fr/_bmx_'+u,1,'special://home/addons/plugin.video.zapiks/resources/images/bmx.png')
		    addDir(__language__(30004),'http://www.zapiks.fr/_skate_'+u,1,'special://home/addons/plugin.video.zapiks/resources/images/skate.png')
		    addDir(__language__(30005),'http://www.zapiks.fr/_ski_'+u,1,'special://home/addons/plugin.video.zapiks/resources/images/ski.png')
        else:
		    u ='1'
		    addDir(__language__(30000),'http://www.zapiks.fr/surf_'+u,1,'special://home/addons/plugin.video.zapiks/resources/images/surf.png')
		    addDir(__language__(30001),'http://www.zapiks.fr/snowboard_'+u,1,'special://home/addons/plugin.video.zapiks/resources/images/snowboard.png')
		    addDir(__language__(30002),'http://www.zapiks.fr/vtt_'+u,1,'special://home/addons/plugin.video.zapiks/resources/images/vtt.png')
		    addDir(__language__(30003),'http://www.zapiks.fr/bmx_'+u,1,'special://home/addons/plugin.video.zapiks/resources/images/bmx.png')
		    addDir(__language__(30004),'http://www.zapiks.fr/skate_'+u,1,'special://home/addons/plugin.video.zapiks/resources/images/skate.png')
		    addDir(__language__(30005),'http://www.zapiks.fr/ski_'+u,1,'special://home/addons/plugin.video.zapiks/resources/images/ski.png')

			
def INDEX(url):
        req = urllib2.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
        response = urllib2.urlopen(req)
        link=response.read()
        response.close()
        link=link.replace('&rsquo;',"'").replace('&#039;',"'").replace('&egrave;','e').replace('&amp;',' & ').replace('&ecirc;','e').replace('&uuml;','u').replace('&eacute;','e').replace('&agrave;','a').replace('&Auml;','A').replace('&quot;','"').replace('&euml;','e').replace('&iuml;','i')
        match=re.compile('<div class="media_thumbnail medium">\n        \t\t\t\t<a href="(.+?)" title="(.+?)">\n        \t\t\t\t\t<img class="thumb" src="(.+?)" alt="video" /><br />\n        \t\t\t\t\t<span class="description">.+?</span>\n').findall(link)
        for url,name,thumbnail in match:
                addLink(name,'http://www.zapiks.fr'+url,2,thumbnail)
        page=re.compile('<h4 class="pagination"><span class="prev"></span><span class="next"><a href=".+?"><img src="/c/i/resultset_last.png" alt="&gt;|" title="&gt;|" height="16" width="16"></a><a href=".+?"><img src=".+?" alt="&gt;" title="&gt;" height="16" width="16"></a></span> <a href=".+?" class="current">.+?</a>  <a href="(.+?)" class="normal">.+?</a>').findall(link)
        if len(page)>1:del page[0];del page[0]
        for url in page:
                addDir(__language__(30006),'http://www.zapiks.fr'+url,1,'special://home/addons/plugin.video.zapiks/resources/images/next.png')

				
def VIDEOLINKS(url):
        req = urllib2.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
        response = urllib2.urlopen(req)
        link=response.read()
        response.close()
        match=re.compile('</div>\t\n\t\t\t<div class="embed">\n\t\t\t\t        <div id="flashvideo(.+?)" class="video" align="center">\n').findall(link)
        for id in match:
                u = 'http://www.zapiks.fr/view/index.php?file='+id+'&lang=fr'
                req = urllib2.Request(u)
                req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
                response = urllib2.urlopen(req)
                link=response.read()
                response.close()
                soup = BeautifulSoup(link)
                video_link=soup.find('file').contents[0]
                play=xbmc.Player().play(video_link)
	
                
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


def addLink(name,url,mode,iconimage):
        u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)
        ok=True
        liz=xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
        liz.setInfo( type="Video", infoLabels={ "Title": name } )
        liz.setProperty("IsPlayable","false")
        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=False)
        return ok


def addDir(name,url,mode,iconimage):
        u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)
        ok=True
        liz=xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
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
        
elif mode==2:
        print "NEW LINK: "+url
        VIDEOLINKS(url)
		
xbmcplugin.endOfDirectory(int(sys.argv[1]))
