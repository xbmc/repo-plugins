import urllib
import urllib2
import re
import os
import xbmcplugin
import xbmcgui
import xbmcaddon
from BeautifulSoup import BeautifulStoneSoup

__settings__ = xbmcaddon.Addon(id='plugin.video.cnet.podcasts')
__language__ = __settings__.getLocalizedString
home = __settings__.getAddonInfo('path')
icon = xbmc.translatePath( os.path.join( home, 'icon.png' ) )


def CATEGORIES():
        addDir(__language__(30000), 'allcnetvideopodcasts', 'allhdpodcast', 'http://audiopodcasts.cnet.com/', 1, 'allCNETvideo_600x600.jpg')
        addDir(__language__(30029), 'AlwaysOnsd', 'AlwaysOnhd', '', 1, 'http://i.d.com.com/i/tron/cnettv/podcast/AlwaysOn_600x600.jpg')
        addDir(__language__(30004), 'applebyte', 'applebytehd', '', 1, 'podcastsHD_applebyte_600x600.jpg')
        addDir(__language__(30003), 'cartechvideo', 'cartechvideohd', '', 1, 'podcastsHD_cartech_600x600.jpg')
        addDir(__language__(30001), 'cnetoncarssd', 'cnetoncarshd', '', 1, 'http://i.i.com.com/cnwk.1d/i/tim/2012/08/27/onCars_600x600.jpg')
        addDir(__language__(30005), 'conversations', 'conversationshd', '', 1, 'podcastsHD_conversations_600x600.jpg')
        addDir(__language__(30030), 'CNETUpdateSD', 'CNETUpdateHD', '', 1, 'http://i.i.com.com/cnwk.1d/i/tim/2012/04/25/CNET_update_iTunes_600x600_300x300.jpg')
        addDir(__language__(30002), 'news', 'cnetnewshd', '', 1, 'podcastsHD_news_600x600.jpg')
        addDir(__language__(30007), 'top5', 'top5hd', '', 1, 'podcastsHD_top5_600x600.jpg')
        addDir(__language__(30006), 'crackingopensd', 'crackingopenhd', '', 1, 'http://i.i.com.com/cnwk.1d/i/tim/2012/07/26/crackingOpen_600x600.jpg')
        addDir(__language__(30009), 'firstlook', 'firstlookhd', '', 1, 'http://i.i.com.com/cnwk.1d/i/tim/2012/07/24/firstLook_600x600_600x600.jpg')
        addDir(__language__(30008), 'howto', 'howtohd', '', 1, 'http://i.i.com.com/cnwk.1d/i/tim/2012/07/24/howTo_600x600_600x600.jpg')
        addDir(__language__(30010), 'InsideScoopsd', 'InsideScoophd', '', 1, 'http://i.i.com.com/cnwk.1d/i/tim/2012/09/19/insideScoop_600x600.jpg')
        addDir(__language__(30013), 'prizefight', 'prizefighthd', '', 1, 'podcastsHD_prizefight_600x600.jpg')
        addDir(__language__(30025), 'rumorhasitsd', 'rumorhasithq', '', 1, 'rumorHasIt_300x300.jpg')
        addDir(__language__(30014), 'tapthatapp', 'tapthatapphd', '', 1, 'tapThatAppHD_600x600.jpg')
        addDir(__language__(30016), 'the404video', 'the404hqvideo', 'The404', 1, 'the404_600x600.jpg')


def GetInHMS(seconds):
    hours = seconds / 3600
    seconds -= 3600*hours
    minutes = seconds / 60
    seconds -= 60*minutes
    if hours == 0:
        return "%02d:%02d" % (minutes, seconds)
    return "%02d:%02d:%02d" % (hours, minutes, seconds)


def INDEX(url,hd_url,audio_url,iconimage):
        playback = __settings__.getSetting('playback')
        if playback == '0':
            link = audio_url
        elif playback == '1':
            link = hd_url
        else:
            link = url
        if link == '':
            link = url
        link = 'http://feeds.feedburner.com/cnet/'+link+'?format=xml'
        replace_list = ['rumorhasit', 'crackingopen', 'alwayson', 'cnetupdate', 'cnetoncars']
        for i in replace_list:
            if i in link:
                link = link.replace('cnet/','')
        print 'Feed Url: '+link
        req = urllib2.Request(link)
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
        response = urllib2.urlopen(req)
        link=response.read()
        response.close()
        soup = BeautifulStoneSoup(link, convertEntities=BeautifulStoneSoup.XML_ENTITIES)
        for i in soup('item'):
            name = i('title')[0].string
            try:
                media_url = i('media:content')[0]['url']
                if media_url == None: raise
            except:
                print ' --- No media:content url for "%s" --- ' %name
                continue
            try:
                desc = i('itunes:summary')[0].string
                if desc == None: raise
            except:
                desc = ''
            try:
                date = i('pubdate')[0].string
                if date == None: raise
            except:
                date = ''
            try:
                seconds = i('itunes:duration')[0].string
                duration = str(GetInHMS(int(seconds)))
            except:
                duration = ''
            description = desc+' \n\n'+date
            u=sys.argv[0]+"?mode=2&url="+urllib.quote_plus(media_url)
            liz=xbmcgui.ListItem(name, iconImage=iconimage, thumbnailImage=iconimage)
            liz.setInfo( type="Video", infoLabels={ "Title": name,"Plot":description, "Duration":duration } )
            liz.setProperty( "Fanart_Image", iconimage )
            liz.setProperty('IsPlayable', 'true')
            ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz)


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


def addDir(name,url,hd_url,audio_url,mode,iconimage):
        if not iconimage.startswith('http'):
            iconimage = 'http://www.cnet.com/i/pod/images/'+iconimage
        if __settings__.getSetting('playback') == '0':
            if not audio_url == '':
                name = name + __language__(30028)
        u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&hd_url="+urllib.quote_plus(hd_url)+"&audio_url="+\
        urllib.quote_plus(audio_url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)+"&iconimage="+str(iconimage)
        ok=True
        liz=xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
        liz.setInfo( type="Video", infoLabels={ "Title": name } )
        liz.setProperty( "Fanart_Image", iconimage )
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
    hd_url=urllib.unquote_plus(params["hd_url"])
except:
    pass
try:
    audio_url=urllib.unquote_plus(params["audio_url"])
except:
    pass
try:
    name=urllib.unquote_plus(params["name"])
except:
    pass
try:
    iconimage=str(params["iconimage"])
except:
    pass
try:
    mode=int(params["mode"])
except:
    pass

print "Mode: "+str(mode)
print "URL: "+str(url)
print "Name: "+str(name)

if mode==None:
    CATEGORIES()

elif mode==1:
    INDEX(url,hd_url,audio_url,iconimage)

elif mode==2:
    item = xbmcgui.ListItem(path=url)
    xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)

xbmcplugin.endOfDirectory(int(sys.argv[1]))
