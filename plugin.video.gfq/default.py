#############################################################################################
#
# Name: plugin.video.gfq
# Author: Bawitdaba
# Description: Guys From Queens Network live video streams and podcast episodes
# Type: Video Addon
# Comments: Original release derived from the TWiT addon made by divingmule and Adam B
#
#############################################################################################

import urllib,urllib2,re,os
import xbmcplugin,xbmcgui,xbmcaddon
from BeautifulSoup import BeautifulSoup

__settings__ = xbmcaddon.Addon(id='plugin.video.gfq')
__language__ = __settings__.getLocalizedString
home = __settings__.getAddonInfo('path')
fanart = xbmc.translatePath( os.path.join( home, 'fanart.jpg' ) )


def categories():
        addDir(__language__(30000),'addLiveLinks',3,xbmc.translatePath( os.path.join( home, 'resources/live.png' ) ))
        addDir(__language__(30100),'http://blip.tv/gfqnetwork/rss',1,xbmc.translatePath( os.path.join( home, 'resources/live.png' ) ))

	headers = {'User-agent' : 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:6.0) Gecko/20100101 Firefox/6.0'}
	req = urllib2.Request('http://www.guysfromqueens.com/feeds',None,headers)
	response = urllib2.urlopen(req)
	showHTML=response.read()
	response.close()

	showHTML=showHTML.replace('&amp;','&')
	showHTML=showHTML.replace('&quot;','"')
	showHTML=showHTML.replace('&apos;',"'")
	showHTML=showHTML.replace('&#039;',"'")
	showHTML=showHTML.replace('&lt;','<')
	showHTML=showHTML.replace('&gt;','>')
	showHTML=showHTML.replace('&nbsp;',' ')
	showHTML=showHTML.replace('&shy;','-')

	# Cut HTML off before inactive shows are listed
	showHTML=showHTML.split('id="searchform"')[0]

        soup = BeautifulSoup(showHTML, convertEntities=BeautifulSoup.HTML_ENTITIES)

        items_left = soup.findAll('div', attrs={'style' : "float: left; width: 300px; margin: 0 30px 20px 0;"})
        items_right = soup.findAll('div', attrs={'style' : "float: left; width: 300px;"})
        items = items_left + items_right
        ShowTitles = []
        CoverLinks = []
        ShowLinks = []

	for index in range (len(items)):
		sub_items = BeautifulSoup(str(items[index]))

		title_items = sub_items.findAll('h2')
		ShowTitles=ShowTitles+re.compile('<h2>(.*)</h2>').findall(str(title_items))

		cover_items = sub_items.findAll('img')
		CoverLinks=CoverLinks+re.compile('<img width="150" height="150" .* src="(.*)" title=".*').findall(str(cover_items))

		link_items = sub_items.findAll('a')
		ShowLinks=ShowLinks+re.compile('.*<a href="(.*)" target="_blank">RSS .*video.*</a>.*').findall(str(link_items))

		#print 'debug:::: ShowTitles: '+str(len(ShowTitles))
		#print 'debug:::: CoverLinks: '+str(len(CoverLinks))
		#print 'debug:::: ShowLinks: '+str(len(ShowLinks))

	Sorted_ShowTitles = sorted(ShowTitles)

	for sort_index in range (len(Sorted_ShowTitles)):
		for index in range (len(ShowTitles)):
			if Sorted_ShowTitles[sort_index] == ShowTitles[index]:
				CoverLink=str(CoverLinks[index])
				CoverLink=CoverLink.replace('-150x150','')
				print 'debug:::: CoverLink: '+str(CoverLink)
				addDir(ShowTitles[index],ShowLinks[index],1,CoverLink)
		 		

def addLiveLinks():
        addLink(__language__(30001)+' ','URL',__language__(30001)+' ','',7,xbmc.translatePath( os.path.join( home, 'resources/vaughn.png' ) ))
        addLink(__language__(30002)+' ','http://cgw.ustream.tv/Viewer/getStream/1/3068635.amf',__language__(30002)+' ','',5,xbmc.translatePath( os.path.join( home, 'resources/ustream.png' ) ))
        addLink(__language__(30003)+' ','URL',__language__(30003)+' ','',6,xbmc.translatePath( os.path.join( home, 'resources/justintv.png' ) ))
        addLink(__language__(30004)+' ','http://s25.streamerportal.com:8235/live',__language__(30004)+' ','',4,xbmc.translatePath( os.path.join( home, 'resources', 'resources/live.png' ) ))

def index(url,iconimage):
        headers = {'User-agent' : 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:6.0) Gecko/20100101 Firefox/6.0'}
        req = urllib2.Request(url,None,headers)
        response = urllib2.urlopen(req)
        link=response.read()
        response.close()

	link=link.replace('&amp;','&')
	link=link.replace('&quot;','"')
	link=link.replace('&apos;',"'")
	link=link.replace('&lt;','<')
	link=link.replace('&gt;','>')
	link=link.replace('&nbsp;',' ')
	link=link.replace('&shy;','-')

        soup = BeautifulSoup(link)

        info = soup.findAll('enclosure')

        title = soup.findAll('title')
        del title[0];del title[0]
        name=re.compile('<title>(.+?)</title>').findall(str(title))

	description=''
        desc = soup.findAll('itunes:subtitle')
	if len(desc) != 0:
            del desc[0]
            description=re.compile('<itunes:subtitle>(.+?)</itunes:subtitle>').findall(str(desc))

        pubdate = soup.findAll('pubdate')
        del pubdate[0]
        date=re.compile('<pubdate>(.+?)</pubdate>').findall(str(pubdate))

	if len(name) != len(date):
            pubdate = soup.findAll('pubdate')
            date=re.compile('<pubdate>(.+?)</pubdate>').findall(str(pubdate))

        link = link.replace('>','>\r\n')

        soup = BeautifulSoup(link)
        info = soup.findAll('enclosure')

	vidurls=re.compile('.*<enclosure.*url="(.+?)".*').findall(str(info))

	#print 'debug:::: Name Length: '+str(len(name))
	#print 'debug:::: URL Length: '+str(len(vidurls))
	#print 'debug:::: URL test: '+str(vidurls[0])
	#print 'debug:::: Description Length: '+str(len(description))
	#print 'debug:::: Date Length: '+str(len(date))

        for index in range (len(name)):
            if len(name)==len(description):
                addLink(name[index],vidurls[index],description[index],date[index],4,iconimage)
            else:
                addLink(name[index],vidurls[index],'',date[index],4,iconimage)


def getSwf(inURL):
        req = urllib2.Request(inURL)
        response = urllib2.urlopen(req)
        swfUrl = response.geturl()
        return swfUrl

def getUstream(url):
        def getSwf():
                url = 'http://www.ustream.tv/flash/viewer.swf'
                req = urllib2.Request(url)
                response = urllib2.urlopen(req)
                swfUrl = response.geturl()
                return swfUrl



        headers = {'User-agent' : 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.8.1.13) Gecko/20080311 Firefox/2.0.0.13'}
        data = None
        req = urllib2.Request(url,data,headers)
        response = urllib2.urlopen(req)
        link=response.read()
        response.close()
        match = re.compile('.*(rtmp://.+?)\x00.*').findall(link)
        rtmp = match[0]
        sName = re.compile('.*streamName\W\W\W(.+?)[/]*\x00.*').findall(link)
        playpath = ' playpath='+sName[0]
        swf = ' swfUrl='+getSwf()
        pageUrl = ' pageUrl=http://www.ustream.tv/gfqlive'
        url = rtmp + playpath + swf + pageUrl + ' swfVfy=1 live=true'
        playLive(url)

def getVaughn():
        rtmpIP = 'live.vaughnlive.tv:443/live'
        #rtmpIP = 'video-viewing-slc-02.vaughnsoft.com:443/live'
	app = 'app=live'
        swfUrl = 'swfUrl=http://vaughnlive.tv/swf/live_vaughnlive_player_v3.swf?channel=gfqnetwork'
        tcUrl = 'rtmp://' + rtmpIP
        pageUrl = 'pageUrl=http://vaughnlive.tv/gfqnetwork'
        Playpath = 'Playpath=live_gfqnetwork'
        live = 'live=true'

        url = tcUrl + ' ' + swfUrl + ' ' + app + ' ' + Playpath + ' ' + pageUrl + ' ' + live

        item = xbmcgui.ListItem(path=url)
        xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)

def getJtv():
        headers = {'User-agent' : 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:6.0) Gecko/20100101 Firefox/6.0',
                   'Referer' : 'http://www.justin.tv/guysfromqueens'}
        req = urllib2.Request('http://usher.justin.tv/find/guysfromqueens.xml?type=live',None,headers)
        response = urllib2.urlopen(req)
        link=response.read()
        response.close()
        soup = BeautifulSoup(link)
        token = ' jtv='+soup.token.string.replace('\\','\\5c').replace(' ','\\20').replace('"','\\22')
        rtmp = soup.connect.string+'/'+soup.play.string
        Pageurl = ' Pageurl=http://www.justin.tv/guysfromqueens'
        swf = ' swfUrl=http://www.justin.tv/widgets/live_embed_player.swf?channel=guysfromqueens'
        url = rtmp+token+swf+Pageurl
        item = xbmcgui.ListItem(path=url)
        xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)


def playLive(url):
        item = xbmcgui.ListItem(path=url)
        xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)


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


def addLink(name,url,description,date,mode,iconimage):
        ok=True

        try:
	    if date != '':
            	description = description + "\n \n Published: " + date
        except:
	    if date != '':
            	description = "Published: " + date

        u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)+"&iconimage="+urllib.quote_plus(iconimage)

        liz=xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
	liz.setInfo(type="Video", infoLabels={"Title":name,"Plot":description,"Date": date})
        liz.setProperty( "Fanart_Image", fanart )
        liz.setProperty('IsPlayable', 'true')
        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz)

        return ok


def addDir(name,url,mode,iconimage):
        ok=True
        u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)+"&iconimage="+urllib.quote_plus(iconimage)
        liz=xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
        liz.setInfo( type="Video", infoLabels={ "Title": name } )
        liz.setProperty( "Fanart_Image", fanart )
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
    iconimage=urllib.unquote_plus(params["iconimage"])
except:
    pass
try:
    mode=int(params["mode"])
except:
    pass

#print "Mode: "+str(mode)
#print "URL: "+str(url)
#print "Name: "+str(name)

if mode==None or url==None or len(url)<1:
    print ""
    categories()

elif mode==1:
    print ""
    index(url,iconimage)

elif mode==2:
    print ""
    getVideo(url)

elif mode==3:
    print ""
    addLiveLinks()

elif mode==4:
    print ""
    playLive(url)

elif mode==5:
    print ""
    getUstream(url)

elif mode==6:
    print ""
    getJtv()

elif mode==7:
    print ""
    getVaughn()

xbmcplugin.endOfDirectory(int(sys.argv[1]))