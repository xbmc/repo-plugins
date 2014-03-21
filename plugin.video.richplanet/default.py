# -*- coding: cp1252 -*-
import urllib,urllib2,re,xbmcplugin,xbmcgui
import xbmcaddon
import CommonFunctions

#Richplanet TV Shows - 2013

addon         = xbmcaddon.Addon('plugin.video.richplanet')
__language__  = addon.getLocalizedString
common = CommonFunctions
common.plugin = 'plugin.video.richplanet'


def CATEGORIES():
        addDir(__language__(30011),'http://blip.tv/richplanet#!page=1',1,'http://2.i.blip.tv/g?src=Richplanet-poster_image478.png&w=220&h=325&fmt=jpg','')
        addDir(__language__(30012),'http://blip.tv/search?search=richplanet%202013',3,'http://2.i.blip.tv/g?src=Richplanet-poster_image478.png&w=220&h=325&fmt=jpg','')
        addDir(__language__(30013),'http://blip.tv/search?search=richplanet%202012',3,'http://2.i.blip.tv/g?src=Richplanet-poster_image478.png&w=220&h=325&fmt=jpg','')
        addDir(__language__(30014),'http://blip.tv/search?search=richplanet%202011',3,'http://2.i.blip.tv/g?src=Richplanet-poster_image478.png&w=220&h=325&fmt=jpg','')
        addDir(__language__(30015),'http://blip.tv/search?search=richplanet%202010',3,'http://2.i.blip.tv/g?src=Richplanet-poster_image478.png&w=220&h=325&fmt=jpg','')
        addDir(__language__(30016),'http://blip.tv/search?search=richplanet%20UFO',3,'http://2.i.blip.tv/g?src=Richplanet-poster_image478.png&w=220&h=325&fmt=jpg','')
        addDir(__language__(30021),'http://blip.tv/search?search=richplanet',4,'http://2.i.blip.tv/g?src=Richplanet-poster_image478.png&w=220&h=325&fmt=jpg','')

def INDEX(url):
        req = urllib2.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.2; Win64; x64; rv:16.0.1) Gecko/20121011 Firefox/16.0.1')
        response = urllib2.urlopen(req)
        link=response.read()
        response.close()
        match=re.compile('content="(.+?)" />\n\t<span class="Thumbnail">\n\t\t\t<span class="Icon Play">Play</span>\n\t\t\t<img src="(.+?)"\n\t\t\t\twidth="190" height="107"\n\t\t\t\tclass="ThumbnailImage" \n\t\t\t\talt="(.+?)"\n\t\t\t/>\n\n\n\n\t</span>\n\n\t<span class="Title" itemprop="name">\n\t\t\n\t\t\t.+?\n\t\t\n\t</span>\n\n\t<span class="Season">\n\t\t\n\t\t\n\n\n\t</span>\n\n\t<span class="Runtime">\n\t\t.+?\n\t</span>\n\n\t<span class="ReleaseDate">\n\t\t.+?\n\t</span>\n\n\t<span class="Description">\n\t\t\n\t\t\t(.+?)\n\t\t\n\t</span>').findall(link)
        for url,thumbnail,name,description in match:
                name = name.replace('&quot;', '"').replace('&#39;', '\'').replace('&amp;', '&')# Cleanup the title.
                description = description.replace('&quot;', '"').replace('&#39;', '\'').replace('&amp;', '&').replace('&#8217;', '´').replace('&#8221;', '"').replace('&#8220;', '"')  # Cleanup the plot.
                addDir(name,url,2,'http:'+thumbnail,description)

def INDEX2(url):
        req = urllib2.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.2; Win64; x64; rv:16.0.1) Gecko/20121011 Firefox/16.0.1')
        response = urllib2.urlopen(req)
        link=response.read()
        response.close()
        match=re.compile('Thumb"\n\t\tsrc="(.+?)"\n\t\talt="(.+?)" />\n\t<div class="MyBlipEpisodeCard">\n\t\t<a href="(.+?)" class').findall(link)
        
        for thumbnail,name,url in match:
                name = name.replace('&quot;', '"').replace('&#39;', '\'').replace('&amp;', '&')# Cleanup the title.
                addDir(name,'http://www.blip.tv'+url,2,'http:'+thumbnail,name)

  

def VIDEOLINKS(url,name):

        req = urllib2.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.2; Win64; x64; rv:16.0.1) Gecko/20121011 Firefox/16.0.1')
        response = urllib2.urlopen(req)
        link=response.read()
        response.close()
        longdescription1=re.compile('"DescContainer">\n\t\t\t\t<h3>.+?</h3>\n\t\t\t\t<p>(.+?)</p>').findall(link)#full description
        if len(longdescription1) > 0:
               longdescription = longdescription1[0]
        else:
               longdescription = __language__(30010)

        req = urllib2.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.2; Win64; x64; rv:16.0.1) Gecko/20121011 Firefox/16.0.1')
        response = urllib2.urlopen(req)
        link=response.read()
        response.close()
        match=re.compile('iframe src=&quot;(.+?).x?p=1&quot;').findall(link)#newer type videos

        req = urllib2.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
        response = urllib2.urlopen(req)
        link=response.read()
        response.close()
        match=re.compile('swf#file=(.+?)&autostart').findall(link)#older type videos

        req = urllib2.Request(match[0])
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
        response = urllib2.urlopen(req)
        link=response.read()
        response.close()
        match=re.compile('content url="(.+?)" blip').findall(link)
        for url in match:
                addLink(name,url,'http://a.i.blip.tv/g?src=Richplanet-website_banner610.png&w=220&h=150&fmt=jpg',longdescription)


                
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




def addLink(name,url,iconimage,longdescription):
        ok=True
        liz=xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
        liz.setInfo( type="Video", infoLabels={ "Title": name, "Plot": longdescription  } )
        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=url,listitem=liz,isFolder=False)
        return ok


def addDir(name,url,mode,iconimage,description):
        u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)
        ok=True
        liz=xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
        liz.setInfo( type="Video", infoLabels={ "Title": name, "Plot": description } )
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

if(mode == 4):
	query = common.getUserInput(__language__(30021), '')
	query2 = query.replace('%', '$/$25').replace('$/$', '%').replace(' ', '%20').replace('&', '%26')# Stop it from doing invalid URLs
	url = 'http://blip.tv/search?search=richplanet%20'+query2
	mode = 3

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
