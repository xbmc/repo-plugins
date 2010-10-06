import urllib,urllib2,re,xbmcplugin,xbmcgui,xbmcaddon

__settings__ = xbmcaddon.Addon(id='plugin.video.twit')
__language__ = __settings__.getLocalizedString


def CATEGORIES():
		addLink(__language__(30017),'http://bglive-a.bitgravity.com/twit/live/high','','','http://twit.tv/sites/all/themes/twit/img/logo.gif')	
		addDir(__language__(30000),'http://feeds.twit.tv/twit_video_large',1,'http://static.mediafly.com/publisher/images/ba85558acd844c7384921f9f96989a37/icon-600x600.png')
		addDir(__language__(30001),'http://feeds.twit.tv/tnt_video_large',1,'http://static.mediafly.com/publisher/images/9ff0322cc0444e599a010cdb9005d90a/icon-600x600.png')
		addDir(__language__(30002),'http://feeds.twit.tv/fc_video_large',1,'http://static.mediafly.com/publisher/images/f7f40bcf20c742cfb55cbccb56c2c68c/icon-600x600.png')
		addDir(__language__(30003),'http://feeds.twit.tv/ipad_video_large',1,'http://static.mediafly.com/publisher/images/201bc64beb6b4956971650fd1462a704/icon-600x600.png')
		addDir(__language__(30004),'http://feeds.twit.tv/gtt_video_large',1,'http://static.mediafly.com/publisher/images/0cc717b3cc94406a885e5df42cac2b13/icon-600x600.png')
		addDir(__language__(30005),'http://feeds.twit.tv/twig_video_large',1,'http://static.mediafly.com/publisher/images/8248233e64fc4c68b722be0ec75d637d/icon-600x600.png')
		addDir(__language__(30006),'http://feeds.twit.tv/ww_video_large',1,'http://static.mediafly.com/publisher/images/ad659facf4cb4fe795b595d9b4275daf/icon-600x600.png')
		addDir(__language__(30007),'http://feeds.twit.tv/mbw_video_large',1,'http://static.mediafly.com/publisher/images/a24b7b336fb14a2ba3f1e31223f622ac/icon-600x600.png')
		addDir(__language__(30008),'http://feeds.twit.tv/ttg_video_large',1,'http://static.mediafly.com/publisher/images/d51aaf03dcfe4502a49e885d4201c278/icon-600x600.png')
		addDir(__language__(30009),'http://feeds.twit.tv/sn_video_large',1,'http://static.mediafly.com/publisher/images/1ac666ad22d940239754fe953207fb42/icon-600x600.png')
		addDir(__language__(30010),'http://feeds.twit.tv/natn_video_large',1,'http://static.mediafly.com/publisher/images/7f7185fe4b564de7a6c79f8f57bb59eb/icon-600x600.png')
		addDir(__language__(30011),'http://feeds.twit.tv/dgw_video_large',1,'http://static.mediafly.com/publisher/images/72acf86f350b40c5b5fd132dcacc78be/icon-600x600.png')
		addDir(__language__(30012),'http://feeds.twit.tv/nsfw_video_large',1,'http://static.mediafly.com/publisher/images/54f4a471ae6c418d89647968a2ea9c91/icon-600x600.png')
		addDir(__language__(30013),'http://feeds.twit.tv/dksh_video_large',1,'http://static.mediafly.com/publisher/images/c9ed18a67b134406a4d5fd357db8b0c9/icon-600x600.png')
		addDir(__language__(30014),'http://feeds.twit.tv/floss_video_large',1,'http://static.mediafly.com/publisher/images/06cecab60c784f9d9866f5dcb73227c3/icon-600x600.png')
		addDir(__language__(30015),'http://feeds.twit.tv/twil_video_large',1,'http://static.mediafly.com/publisher/images/b2911bcc34174461ba970d2e38507340/icon-600x600.png')
		addDir(__language__(30016),'http://feeds.twit.tv/specials_video_large',1,'http://static.mediafly.com/publisher/images/eed22d09b9524474ac49bc022b556b2b/icon-600x600.png')

        
        
def INDEX(url):
        req = urllib2.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
        response = urllib2.urlopen(req)
        link=response.read()
        response.close()
        match=re.compile('url="(.+?)" fileSize=".+?" type="video/mp4" medium="video" bitrate="1000" framerate="29.97" samplingrate="48" channels="1" duration=".+?" width="864" height="480" mediafly:profile="H264b_864x480_1000" />\n').findall(link)
        name=re.compile('<title>(.+?)</title>\n').findall(link)
        plot=re.compile('<itunes:subtitle>(.+?)</itunes:subtitle>\n').findall(link)
        date=re.compile('<pubDate>(.+?)</pubDate>\n').findall(link)
	icon=re.compile('<img src="(.+?)"').findall(link)	
	del name[0];del name[0];del plot[0];del date[0] # The first two strings do not apply.
        for index in range(len(match)):
		if len(match) == len(icon):
                	addLink(name[index],match[index],plot[index],date[index],icon[index])
    		else:
			addLink(name[index],match[index],plot[index],date[index],'') 

                
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




def addLink(name,url,plot,date,iconimage):
        ok=True
        liz=xbmcgui.ListItem(name+'  '+date, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
        liz.setInfo( type="Video", infoLabels={ "Title":name,"Plot":plot } )
        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=url,listitem=liz)
        return ok


def addDir(name,url,mode,iconimage):
        u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)
        ok=True
        liz=xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
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
        

xbmcplugin.endOfDirectory(int(sys.argv[1]))
