import urllib,urllib2,re,xbmcplugin,xbmcgui,xbmcaddon

__settings__ = xbmcaddon.Addon(id='plugin.video.cnet.podcasts')
__language__ = __settings__.getLocalizedString

def CATEGORIES():
        addDir(__language__(30038),'',1,'')
        addDir(__language__(30039),'',2,'')
		
def CATEGORIESHD():
        addDir(__language__(30000),'http://feeds2.feedburner.com/cnet/allhdpodcast',3,'http://www.cnet.com/i/pod/images/allCNETvideo_600x600.jpg')
        addDir(__language__(30002),'http://feeds.feedburner.com/cnet/buzzreporthd',3,'http://www.cnet.com/i/pod/images/podcastsHD_buzzreport_600x600.jpg')
        addDir(__language__(30004),'http://feeds.feedburner.com/cnet/cnetnewshd',3,'http://www.cnet.com/i/pod/images/podcastsHD_news_600x600.jpg')
        addDir(__language__(30006),'http://feeds2.feedburner.com/cnet/cartechvideohd',3,'http://www.cnet.com/i/pod/images/podcastsHD_cartech_600x600.jpg')
        addDir(__language__(30008),'http://feeds.feedburner.com/cnet/applebytehd',3,'http://www.cnet.com//i/pod/images/podcastsHD_applebyte_600x600.jpg')
        addDir(__language__(30010),'http://feeds.feedburner.com/cnet/conversationshd',3,'http://www.cnet.com/i/pod/images/podcastsHD_conversations_600x600.jpg')
        addDir(__language__(30012),'http://feeds2.feedburner.com/cnet/loadedhd',3,'http://www.cnet.com/i/pod/images/podcastsHD_loaded_600x600.jpg')
        addDir(__language__(30014),'http://feeds2.feedburner.com/cnet/top5hd',3,'http://www.cnet.com/i/pod/images/podcastsHD_top5_600x600.jpg')
        addDir(__language__(30018),'http://feeds2.feedburner.com/cnet/firstlookhd',3,'http://www.cnet.com/i/pod/images/podcastsHD_firstlook_600x600.jpg')
        addDir(__language__(30020),'http://feeds2.feedburner.com/cnet/techreviewhd',3,'http://www.cnet.com/i/pod/images/cnetTechReviewHD_600x600.jpg')
        addDir(__language__(30022),'http://feeds2.feedburner.com/cnet/howtohd',3,'http://www.cnet.com/i/pod/images/podcastsHD_howto_600x600.jpg')
        addDir(__language__(30024),'http://feeds2.feedburner.com/cnet/greenshowhd',3,'http://www.cnet.com/i/pod/images/podcastsHD_greenshow_600x600.jpg')
        addDir(__language__(30026),'http://feeds2.feedburner.com/cnet/prizefighthd',3,'http://www.cnet.com/i/pod/images/podcastsHD_prizefight_600x600.jpg')
        addDir(__language__(30028),'http://feeds2.feedburner.com/cnet/tapthatapphd',3,'http://www.cnet.com/i/pod/images/tapThatAppHD_600x600.jpg')
        addDir(__language__(30033),'http://feeds.feedburner.com/cnet/bolhqvideo',3,'http://www.cnet.com/i/pod/images/bol_600x600.jpg')
        addDir(__language__(30035),'http://feeds.feedburner.com/cnet/the404hqvideo',3,'http://www.cnet.com/i/pod/images/the404_600x600.jpg')
        addDir(__language__(30036),'http://feeds.feedburner.com/cnet/pregamehq',3,'http://www.cnet.com/i/pod/images/pregame_d_600x600.jpg')
        addDir(__language__(30037),'http://feeds.feedburner.com/cnet/roundtablehqvideo',3,'http://www.cnet.com/i/pod/images/reporters_roundtable_600x600.jpg')

def CATEGORIESSD():
        addDir(__language__(30001),'http://feeds2.feedburner.com/allcnetvideopodcasts',3,'http://www.cnet.com/i/pod/images/allCNETvideo_300x300.jpg')
        addDir(__language__(30003),'http://feeds.feedburner.com/cnet/buzzreport',3,'http://www.cnet.com/i/pod/images/buzzreport_600x600.jpg')
        #addDir(__language__(30005),'http://feeds.feedburner.com/cnet/cnetnews',3,'http://www.cnet.com/i/pod/images/podcasts_news_600x600.jpg')
        addDir(__language__(30007),'http://feeds.feedburner.com/cnet/cartechvideo?format=xml',3,'http://www.cnet.com/i/pod/images/cartech_600x600.jpg')
        addDir(__language__(30009),'http://feeds.feedburner.com/cnet/applebyte',3,'http://www.cnet.com//i/pod/images/applebyte_600x600.jpg')
        addDir(__language__(30011),'http://feeds.feedburner.com/cnet/conversations',3,'http://www.cnet.com/i/pod/images/cnetconversations_600x600.jpg')
        addDir(__language__(30013),'http://feeds2.feedburner.com/cnet/loaded',3,'http://www.cnet.com/i/pod/images/loaded_600x600.jpg')
        addDir(__language__(30015),'http://feeds2.feedburner.com/cnet/top5',3,'http://www.cnet.com/i/pod/images/top5_600x600.jpg')
        addDir(__language__(30016),'http://feeds2.feedburner.com/cnet/dialedinvideo',3,'http://www.cnet.com/i/pod/images/dialedin_600x600.jpg')
        #addDir(__language__(30017),'http://feeds2.feedburner.com/cnet/dialedinvideo',3,'http://www.cnet.com/i/pod/images/dialedin_600x600.jpg')
        addDir(__language__(30019),'http://feeds2.feedburner.com/cnet/firstlook',3,'http://www.cnet.com/i/pod/images/firstlook_600x600.jpg')
        addDir(__language__(30021),'http://feeds2.feedburner.com/cnet/techreview',3,'http://www.cnet.com/i/pod/images/cnetTechReview_600x600.jpg')
        addDir(__language__(30023),'http://feeds2.feedburner.com/cnet/howto',3,'http://www.cnet.com/i/pod/images/HowTo_300x300.jpg')
        addDir(__language__(30025),'http://feeds2.feedburner.com/cnet/greenshow',3,'http://www.cnet.com/i/pod/images/greenshow_300x300.jpg')
        addDir(__language__(30027),'http://feeds2.feedburner.com/cnet/prizefight',3,'http://www.cnet.com/i/pod/images/prizefight_300x300.jpg')
        addDir(__language__(30029),'http://feeds2.feedburner.com/cnet/tapthatapp',3,'http://www.cnet.com/i/pod/images/tapThatApp_600x600.jpg')
        addDir(__language__(30030),'http://feeds.feedburner.com/cnet/roundtablevideo',3,'http://www.cnet.com/i/pod/images/reporters_roundtable_600x600.jpg')
        addDir(__language__(30031),'http://feeds.feedburner.com/cnet/the404video',3,'http://www.cnet.com/i/pod/images/the404_600x600.jpg')
        addDir(__language__(30032),'http://feeds.feedburner.com/cnet/pregame',3,'http://www.cnet.com/i/pod/images/pregame_d_600x600.jpg')
        addDir(__language__(30034),'http://feeds.feedburner.com/cnet/bolvideo',3,'http://www.cnet.com/i/pod/images/bol_600x600.jpg')        

		
		
def INDEX(url):
        req = urllib2.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
        response = urllib2.urlopen(req)
        link=response.read()
        response.close()
        code=re.sub('\r','',link)
        code=re.sub('\n',' ',code)
        code=re.sub('\t',' ',code)
        code=re.sub('  ','',code)
        code=re.sub('&lt;','',code)
        code=re.sub('/&gt;','',code)
        match=re.compile('<title><!\[\CDATA\[(.+?)]\]\></title> <link>(.+?)</link> <author>.+?</author> <description>(.+?)img src=".+?" height="1" width="1"</description>').findall(code)
        if len(match)<1:
                match=re.compile('<title><!\[\CDATA\[(.+?)]\]\></title> <link>(.+?)</link> <author>.+?</author><itunes:subtitle><!\[\CDATA\[(.+?)]\]\></itunes:subtitle>').findall(code)   
        for name,url,plot in match:		
                addLink(name,url,plot,'')

                
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




def addLink(name,url,plot,iconimage):
        ok=True
        liz=xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
        liz.setInfo( type="Video", infoLabels={ "Title": name,"Plot":plot } )
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

if mode==None:
        print ""
        CATEGORIES()
       
elif mode==1:
        print ""
        CATEGORIESHD()
		
elif mode==2:
        print ""
        CATEGORIESSD()

elif mode==3:
        print ""+url
        INDEX(url)
		
xbmcplugin.endOfDirectory(int(sys.argv[1]))
