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
videoq = __settings__.getSetting('video_quality')
home = __settings__.getAddonInfo('path')
fanart = xbmc.translatePath( os.path.join( home, 'fanart.jpg' ) )


def categories():
        addDir(__language__(30000),'addLiveLinks',3,xbmc.translatePath( os.path.join( home, 'resources/live.png' ) ))
        addDir(__language__(30101),'http://feeds.feedburner.com/BehindTheCountervideo?format=xml',1,'http://www.guysfromqueens.com/wp-content/uploads/2011/11/btc-video600x600.jpg')
        addDir(__language__(30102),'http://feeds.feedburner.com/BigBrotherRewindvideo?format=xml',1,'http://www.guysfromqueens.com/wp-content/uploads/powerpress/bbr2011-600x600-971.jpg')
        addDir(__language__(30103),'http://feeds.feedburner.com/ImJustSayingvideo?format=xml',1,'http://img185.imageshack.us/img185/3955/imjustsayingitunesbanne.jpg')
        addDir(__language__(30104),'http://feeds.feedburner.com/SpencerKobrensTheBaldTruthvideo?format=xml',1,'http://www.guysfromqueens.com/wp-content/uploads/2011/11/tbt-video600x600.jpg')
        addDir(__language__(30105),'http://feeds.feedburner.com/TechNewsWeeklyvideo?format=xml',1,'http://www.guysfromqueens.com/wp-content/uploads/2011/11/tnw-video600x600.jpg')
        addDir(__language__(30106),'http://feeds.feedburner.com/TheAndrewZarianShowvideo?format=xml',1,'http://www.guysfromqueens.com/wp-content/uploads/2011/11/azshow-video-600x600.jpg')
        addDir(__language__(30107),'http://blip.tv/Chauncehaydenshow/rss',1,'http://a.images.blip.tv/Steppinout-300x300_show_image550.jpg')
        addDir(__language__(30108),'http://feeds.feedburner.com/TheFreeForAllvideo?format=xml',1,'http://www.guysfromqueens.com/wp-content/uploads/2011/11/ffa-video600x600.jpg')
        addDir(__language__(30109),'http://feeds.feedburner.com/TheNewsWithJessicavideo?format=xml',1,'http://www.guysfromqueens.com/wp-content/uploads/2011/11/news-video600x600.jpg')
        addDir(__language__(30110),'http://feeds.feedburner.com/WhatTheTechvideo?format=xml',1,'http://www.guysfromqueens.com/wp-content/uploads/2011/11/wtt600x600-video.jpg')

def addLiveLinks():
        addLink(__language__(30001)+' ','URL',__language__(30001)+' ','',7,xbmc.translatePath( os.path.join( home, 'resources/live-stickam.png' ) ))
        addLink(__language__(30002)+' ','http://cgw.ustream.tv/Viewer/getStream/1/3068635.amf',__language__(30002)+' ','',5,xbmc.translatePath( os.path.join( home, 'resources/live-ustream.png' ) ))

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
	#print 'debug:::: info: '+str(info)

	vidurls=re.compile('<enclosure.*url="(.+?)".*').findall(str(info))

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


	#print 'debug:::: Name Length: '+str(len(name))
	#print 'debug:::: URL Length: '+str(len(vidurls))
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
        headers = {'User-agent' : 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:6.0) Gecko/20100101 Firefox/6.0',
                   'Referer' : 'http://www.ustream.tv/gfqlive'}
        data = None
        req = urllib2.Request(url,data,headers)
        response = urllib2.urlopen(req)
        link=response.read()
        response.close()

        match = re.compile('(rtmp://.+?)\x00').findall(link)
        rtmp = match[0]

        sName = re.compile('streamName\W\W\W(.+?)[/]*\x00').findall(link)
        playpath = ' playpath='+sName[0]+' app=ustreamVideo/3068635'
        swf = ' swfUrl='+getSwf('http://www.ustream.tv/flash/viewer.swf')
        pageUrl = ' pageUrl=http://www.ustream.tv/gfqlive'
        url = rtmp + playpath + swf + pageUrl + ' swfVfy=1 live=true'

        item = xbmcgui.ListItem(path=url)
        xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)


def getStickam():
	UserID = '175141254'

        headers = {'User-agent' : 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:6.0) Gecko/20100101 Firefox/6.0',
                   'Referer' : 'http://www.stickam.com/guysfromqueens'}
        req = urllib2.Request('http://player.stickam.com/servlet/flash/getChannel?type=join&performerID=' + UserID,None,headers)
        response = urllib2.urlopen(req)
        link=response.read()
        response.close()
        soup = BeautifulSoup(link)

        match = re.compile('freeServerIP=(.+?),.*channelID=(.+?)&.*').findall(str(link))
	match = match[0]
	rtmpIP = match[0]
	HostID = match[1]

	app = 'app=video_chat2_stickam_peep/'+HostID
	swfUrl = 'swfUrl='+getSwf('http://player.stickam.com/flash/stickam/stickam_simple_video_player.swf')
	tcUrl = 'rtmp://' + rtmpIP + '/video_chat2_stickam_peep/' + HostID + '/public/mainHostFeed'
	pageUrl = 'pageUrl=http://www.stickam.com/guysfromqueens'
	connamf = 'conn=O:1 conn=NS:channel:' + UserID + ' conn=O:1'
	live = 'live=true'

	url = tcUrl + ' ' + swfUrl + ' ' + app + ' ' + pageUrl + ' ' + connamf + ' ' + live

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
    getStickam()

xbmcplugin.endOfDirectory(int(sys.argv[1]))