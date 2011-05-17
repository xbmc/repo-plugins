import urllib,urllib2,re,os
import xbmcplugin,xbmcgui,xbmcaddon
from BeautifulSoup import BeautifulSoup

__settings__ = xbmcaddon.Addon(id='plugin.video.twit')
__language__ = __settings__.getLocalizedString
videoq = __settings__.getSetting('video_quality')
home = __settings__.getAddonInfo('path')


def CATEGORIES():
        addDir(__language__(30017),'addLiveLinks',4,xbmc.translatePath( os.path.join( home, 'resources/live.png' ) ))
        addDir(__language__(30000),'http://feeds.twit.tv/twit_video_large',1,'http://static.mediafly.com/publisher/images/ba85558acd844c7384921f9f96989a37/icon-600x600.png')
        addDir(__language__(30001),'http://feeds.twit.tv/tnt_video_large',1,'http://static.mediafly.com/publisher/images/9ff0322cc0444e599a010cdb9005d90a/icon-600x600.png')
        addDir(__language__(30002),'http://feeds.twit.tv/fc_video_large',1,'http://static.mediafly.com/publisher/images/f7f40bcf20c742cfb55cbccb56c2c68c/icon-600x600.png')
        addDir(__language__(30003),'http://feeds.twit.tv/ipad_video_large',1,'http://static.mediafly.com/publisher/images/201bc64beb6b4956971650fd1462a704/icon-600x600.png')
        addDir(__language__(30031),'http://feeds.twit.tv/aaa_video_large',1,'http://static.mediafly.com/publisher/images/7874016b2dd3490fa1e8b606dff4d2fa/icon-600x600.png')
        addDir(__language__(30004),'http://feeds.twit.tv/gtt_video_large',1,'http://static.mediafly.com/publisher/images/0cc717b3cc94406a885e5df42cac2b13/icon-600x600.png')
        addDir(__language__(30005),'http://feeds.twit.tv/twig_video_large',1,'http://static.mediafly.com/publisher/images/8248233e64fc4c68b722be0ec75d637d/icon-600x600.png')
        addDir(__language__(30006),'http://feeds.twit.tv/ww_video_large',1,'http://static.mediafly.com/publisher/images/ad659facf4cb4fe795b595d9b4275daf/icon-600x600.png')
        addDir(__language__(30007),'http://feeds.twit.tv/mbw_video_large',1,'http://static.mediafly.com/publisher/images/a24b7b336fb14a2ba3f1e31223f622ac/icon-600x600.png')
        addDir(__language__(30029),'http://feeds.twit.tv/tri_video_large',1,'http://static.mediafly.com/publisher/images/c60ef74e0a3545e490d7cefbc369d168/icon-600x600.png')
        addDir(__language__(30030),'http://feeds.twit.tv/photo_video_large',1,'http://static.mediafly.com/publisher/images/dd28d32fd045471598a55c850cb53117/icon-600x600.png')		
        addDir(__language__(30008),'http://feeds.twit.tv/ttg_video_large',1,'http://static.mediafly.com/publisher/images/d51aaf03dcfe4502a49e885d4201c278/icon-600x600.png')
        addDir(__language__(30009),'http://feeds.twit.tv/sn_video_large',1,'http://static.mediafly.com/publisher/images/1ac666ad22d940239754fe953207fb42/icon-600x600.png')
        addDir(__language__(30010),'http://twit.tv/tsh',2,'http://twit.tv/files/imagecache/coverart/coverart/tsh600.jpg')
        addDir(__language__(30011),'http://feeds.twit.tv/dgw_video_large',1,'http://static.mediafly.com/publisher/images/72acf86f350b40c5b5fd132dcacc78be/icon-600x600.png')
        addDir(__language__(30012),'http://feeds.twit.tv/nsfw_video_large',1,'http://static.mediafly.com/publisher/images/54f4a471ae6c418d89647968a2ea9c91/icon-600x600.png')
        addDir(__language__(30013),'http://feeds.twit.tv/dksh_video_large',1,'http://static.mediafly.com/publisher/images/c9ed18a67b134406a4d5fd357db8b0c9/icon-600x600.png')
        addDir(__language__(30014),'http://feeds.twit.tv/floss_video_large',1,'http://static.mediafly.com/publisher/images/06cecab60c784f9d9866f5dcb73227c3/icon-600x600.png')
        addDir(__language__(30015),'http://feeds.twit.tv/twil_video_large',1,'http://static.mediafly.com/publisher/images/b2911bcc34174461ba970d2e38507340/icon-600x600.png')
        addDir(__language__(30016),'http://feeds.twit.tv/specials_video_large',1,'http://static.mediafly.com/publisher/images/eed22d09b9524474ac49bc022b556b2b/icon-600x600.png')
        addDir(__language__(30022),'http://feeds.twit.tv/htg_video_large',1,'http://static.mediafly.com/publisher/images/441a40308195459b8e24f341dc68885c/icon-600x600.png')
        addDir(__language__(30023),'http://feeds.twit.tv/fr_video_large',1,'http://static.mediafly.com/publisher/images/5a081f72180e41939e549ec7d12be24d/icon-600x600.png')
        addDir(__language__(30024),'http://feeds.twit.tv/twich_video_large',1,'http://static.mediafly.com/publisher/images/f76d60fdd2ea4822adbc50d2027839ce/icon-600x600.png')
        addDir(__language__(30027),'http://feeds.twit.tv/cgw_video_large',1,'http://static.mediafly.com/publisher/images/e974ef72d2134d7b91c2908e8ceb5850/icon-600x600.png')
        addDir(__language__(30025),'http://twit.tv/FIB',2,'http://leoville.tv/podcasts/coverart/fib600audio.jpg')
        addDir(__language__(30026),'http://twit.tv/twif',2,'http://leo.am/podcasts/coverart/twif600audio.jpg')
        addDir(__language__(30035),'http://feeds.twit.tv/twirt_video_large',1,'http://static.mediafly.com/publisher/images/bdbcfb9db7274a9ba914300792c5f4ad/icon-600x600.png')


def INDEX(url):
        req = urllib2.Request(url)
        req.addheaders = [('Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.2.3) Gecko/20100401 Firefox/3.6.3 ( .NET CLR 3.5.30729)')]
        response = urllib2.urlopen(req)
        link=response.read()
        response.close()
        if videoq==__language__(30018):
            link=link.replace('_h264b_640x368_500','_h264b_864x480_1500')
        elif videoq==__language__(30019):
            link=link.replace('_h264b_640x368_500','_h264b_864x480_1000')		
        elif videoq==__language__(30020):
            link=link.replace('_h264b_640x368_500','_h264b_640x368_256')
        else:
            link=link
        link=link.replace('&amp;',' & ')
        soup = BeautifulSoup(link)
        info = soup.findAll('enclosure')
        url=re.compile('<enclosure url="(.+?)" length=".+?" type="video/mp4" mediafly:profile="H264b_640x368_500">').findall(str(info))
        title = soup.findAll('title')
        del title[0];del title[0]
        name=re.compile('<title>(.+?)</title>').findall(str(title))
        desc = soup.findAll('itunes:subtitle')
        del desc[0]
        description=re.compile('<itunes:subtitle>(.+?)</itunes:subtitle>').findall(str(desc))
        pubdate = soup.findAll('pubdate')
        del pubdate[0]
        date=re.compile('<pubdate>(.+?)</pubdate>').findall(str(pubdate))
        for index in range (len(name)):
            if len(name)==len(description):
                addLink(name[index],url[index],description[index],date[index],xbmc.translatePath( os.path.join( home, 'icon.png' ) ))
            else:
                addLink(name[index],url[index],'',date[index],xbmc.translatePath( os.path.join( home, 'icon.png' ) ))

def INDEXWebsite(url):
        req = urllib2.Request(url)
        req.addheaders = [('Referer', 'http://twit.tv/'),
                ('Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.2.3) Gecko/20100401 Firefox/3.6.3 ( .NET CLR 3.5.30729)')]
        response = urllib2.urlopen(req)
        link=response.read()
        response.close()
        link=link.replace('&amp;','').replace('#039;',"'").replace('amp;','').replace('quot;','"')
        match=re.compile('<h3 class="podcast-date">(.+?)</h3>\n    <h2><a href="(.+?)" title="(.+?)" alt=".+?">.+?</a></h2>\n    <p>(.+?)</p>\n').findall(link)
        for date,url,name,description in match:		
                addWebLink(name,'http://twit.tv'+url,description,date,3,xbmc.translatePath( os.path.join( home, 'icon.png' ) ))
        page=re.compile('<div class="episode-prevnext clearfix"><a href=".+?" class="episode-next pager-prev active"><span>Next</span></a><a href="(.+?)" class="episode-prev pager-next active"><span>Prev</span></a></div>').findall(link)
        if len(page)<1:
                page=re.compile('<span>Next</span></span><a href="(.+?)" class="episode-prev pager-next active">').findall(link)
        for url in page:
                addDir('Next Page','http://twit.tv'+url,2,'')


def VIDEOLINKS(url):
        req = urllib2.Request(url)
        req.addheaders = [('Referer', 'http://twit.tv/'),
                ('Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.2.3) Gecko/20100401 Firefox/3.6.3 ( .NET CLR 3.5.30729)')]
        response = urllib2.urlopen(req)
        link=response.read()
        response.close()
        link=link.replace(' ','')
        match=re.compile('</div>\n<divclass="download"><ahref="(.+?)">DownloadVideo\(\High\)\</a>').findall(link)
        if len(match)<1:
                dialog = xbmcgui.Dialog()
                ok = dialog.ok('TWiT',__settings__.getLocalizedString(30028))
                print 'Sorry video not up yet'
        for url in match:
                aurl=url[0:-15]
                if videoq==__language__(30018):
                        url=aurl+('864x480_1500.mp4')
                elif videoq==__language__(30019):
                        url=aurl+('864x480__1000.mp4')		
                elif videoq==__language__(30020):
                        url=aurl+('864x480_640x368_256.mp4')
                else:
                        url=url
                item = xbmcgui.ListItem(path=url)
                xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)


def addLiveLinks():
        addLinkLive(__language__(30032),'http://bglive-a.bitgravity.com/twit/live/high',5,xbmc.translatePath( os.path.join( home, 'resources/live.png' ) ))
        addLinkLive(__language__(30033),'http://bglive-a.bitgravity.com/twit/live/low',5,xbmc.translatePath( os.path.join( home, 'resources/live.png' ) ))
        #addLink(__language__(30034),'rtmp://flash76.ustream.tv:1935/ustreamVideo/1524 playpath=streams/live app=ustreamVideo/1524 swfUrl="http://cdn1.ustream.tv/swf/4/viewer.rsl.558.swf" pageUrl="http://live.twit.tv/" live=true','','',xbmc.translatePath( os.path.join( home, 'resources/live.png' ) ))


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


def addLink(name,url,description,date,iconimage):
        ok=True
        liz=xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
        description = description + "\n \n Published: " + date
        liz.setInfo( type="Video", infoLabels={ "Title": name,"Plot":description,"Date": date } )
        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=url,listitem=liz)
        return ok

def addWebLink(name,url,description,date,mode,iconimage):
        u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)
        ok=True
        description = description + "\n \n Published: " + date
        liz=xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
        liz.setInfo( type="Video", infoLabels={ "Title": name,"Plot":description,"Date": date } )
        liz.setProperty('IsPlayable', 'true')
        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz)
        return ok

def addDir(name,url,mode,iconimage):
        u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)
        ok=True
        liz=xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
        liz.setInfo( type="Video", infoLabels={ "Title": name } )
        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)
        return ok

def addLinkLive(name,url,mode,iconimage):
        u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)
        ok=True
        liz=xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage, path=url)
        liz.setProperty('IsPlayable', 'true')
        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz)
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
    INDEXWebsite(url)

elif mode==3:
    print ""+url
    VIDEOLINKS(url)

elif mode==4:
    print ""+url
    addLiveLinks()
    
elif mode==5:
    print ""+url
    playLive(url)

xbmcplugin.endOfDirectory(int(sys.argv[1]))
