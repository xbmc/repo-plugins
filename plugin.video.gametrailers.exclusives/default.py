import urllib,urllib2,re,xbmcplugin,xbmcgui,xbmcaddon,os,sys

__scriptname__ = "GameTrailers_Bonus"
__author__ = "AssChin79"
__scriptid__ = "plugin.video.gametrailers.exclusives"
__version__ = "1.0.4"
__cwd__ = os.getcwd()
__cookies__ = os.path.join( __cwd__, 'resources', 'cookies' )
__cookie__ = os.path.join( __cookies__, 'cookies.lwp' )


doLogin = False

BASE_RESOURCE_PATH = os.path.join( __cwd__, 'resources', 'lib' )
sys.path.append(BASE_RESOURCE_PATH)

import weblogin
import gethtml

def Notify(title,message,times,icon):
        xbmc.executebuiltin("XBMC.Notification("+title+","+message+","+times+","+icon+")")


def STARTUP():
        #check if user has enabled login setting
        usrsettings = xbmcaddon.Addon(id=__scriptid__)
        use_account = usrsettings.getSetting('use-account')

        if use_account == 'true':
             #Get username/password, do login, and get whether to hide login notification
             username = usrsettings.getSetting('username')
             password = usrsettings.getSetting('password')
             hidesuccess = usrsettings.getSetting('hide-successful-login-messages')

             LOGIN(username,password,hidesuccess)
             
        else:
            if os.path.exists(__cookie__) == True:
                os.unlink(__cookie__)
             

def LOGIN(username,password,hidesuccess):
    logged_in = weblogin.doLogin(__cookies__, username, password)
    if logged_in == True:
        doLogin=True
        if hidesuccess == 'false':
            Notify('User login Status','Successfully acquired GT cookie','4000','')

    elif logged_in == False:
            Notify('Login Failure', 'Could not acquire GT cookie','4000','')


def COOKIE_EXIST():
    try:
        file = open(__cookie__)
        file.close()
        return True
    except:
        return False
    

def URLENCODECOOKIE():
    cf = open(__cookie__, 'r')
    cookie_send = cf.read()
    cf.close()
    
    sidMatch = re.search('gtsid_vgs=(.+?);', cookie_send, re.S).group(0)
    usrMatch = re.search('mosesuser="(.+?)"', cookie_send, re.S).group(0)
    
    encodedCookie = '|Cookie=Cookie:' + sidMatch + usrMatch.replace('"', '')
    return encodedCookie
    

def CATEGORIES():
    gtfeeds = "http://feeds.gametrailers.com"
    gtimages = "http://gametrailers.mtvnimages.com/images/podcasts"
    mirror = "http://www.msoftinfosystems.com/news/mirror/rss/gt"

    # Uri Sources: http://www.gametrailers.com/podcasts.php
    addDir('Bonus Round', gtfeeds + '/rss_ipod_br_season3.php',1,'http://www.gametrailers.com/images/podcast_bonusround.jpg')
    addDir('Electronic Entertainment Expo (E3)', gtfeeds + '/rss_ipod_gen.php?source=e311ms', 1, gtimages + '/podcasts/GTE3_2011_big.jpg')
    addDir('Epic Battle Axe', gtfeeds + '/rss_ipod_gen.php?source=eba', 1, gtimages + '/podcasts/600x600_PodCast_EBA.jpg')
    addDir('Game Interviews', gtfeeds + '/rss_ipod_gen.php?source=interviews', 1, gtimages + '/podcasts/VideoInterviews.jpg')
    addDir('Game of the Year Awards', gtfeeds + '/rss_ipod_gen.php?source=gtgoty2010', 1, gtimages + '/podcasts/600x600_GT_GOTY.jpg')
    addDir('Game Previews', gtfeeds + '/rss_ipod_gen.php?source=previews', 1, gtimages + '/podcasts/VideoPreviews.jpg')
    addDir('Game Reviews', gtfeeds + '/rss_ipod_gen.php', 1, gtimages + '/podcasts/VideoReviews.jpg')
    
    # Protected resource
    if (COOKIE_EXIST()) == True:
        addDir('GT Countdown', mirror + '/gt_countdown.xml', 1, mirror + '/gt_countdown.jpg')    

    addDir('GT Motion', gtfeeds + '/rss_ipod_gen.php?source=gtmotion', 1, gtimages + '/podcasts/GTMotion.jpg')
    
    # Protected resource
    if (COOKIE_EXIST()) == True:
        addDir('GT Retrospectives', mirror + '/gt_retrospectives.xml', 1, mirror + '/gt_retrospectives.jpg')
        addDir('GT Top 20 Today', mirror + '/gt_top20.xml', 1, mirror + '/gt_top20.jpg')
    
    addDir('Invisible Walls', gtfeeds + '/rss_ipod_gen.php?source=iw', 1, gtimages + '/podcasts/IW.jpg')
    addDir('Pach Attack', gtfeeds + '/rss_ipod_gen.php?source=pa', 1, gtimages + '/podcasts/PachAttack.jpg')

    # Protected resource
    if (COOKIE_EXIST()) == True:
        addDir('Pop Fiction',mirror + '/pop_fiction.xml', 1, mirror + '/pop_fiction.jpg')
        addDir('Science of Games',mirror + '/science_of_games.xml', 1, mirror + '/science_of_games.jpg')
        addDir('ScrewAttack',mirror + '/screwattack.xml', 1, mirror + '/screwattack.jpg')

    addDir('Spotlight: Microsoft XBOX360', gtfeeds + '/rss_ipod_gen.php?source=xb360', 1, gtimages + '/podcasts/Xbox360.jpg')
    addDir('Spotlight: Nintendo 3DS', gtfeeds + '/rss_ipod_gen.php?source=3ds', 1, gtimages + '/podcasts/600x600_PodCast_3DS.jpg')
    addDir('Spotlight: Nintendo DS', gtfeeds + '/rss_ipod_gen.php?source=ds', 1, gtimages + '/podcasts/DS.jpg')
    addDir('Spotlight: Nintendo Wii', gtfeeds + '/rss_ipod_gen.php?source=wii', 1, gtimages + '/podcasts/PodCast_Wii.jpg')
    addDir('Spotlight: Sony PS3', 'http://www.gametrailers.com/gtps3_podcast.xml', 1, gtimages + '/podcasts/SonyPS3.jpg')
    addDir('Spotlight: Sony PSP', gtfeeds + '/rss_ipod_gen.php?source=psp', 1, gtimages + '/podcasts/PSP.jpg')
    addDir('Top 100 Trailers of all Time', mirror + '/top100trailers.xml', 1, gtimages + '/moses/xmassives/platform_images/88x69_Top100.jpg')

                       
def INDEX(url):
	req = urllib2.Request(url)
	req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
	#req.add_header('User-Agent', 'iTunes/9.0.2 (Windows; U)')
	response = urllib2.urlopen(req)
	oStream = response.read()
	response.close()
         
	nmatch = re.compile("<item>(.+?)<\/item>", re.S)
    	
    	for match in nmatch.findall(oStream):
        	elems = re.compile('.+?<title>(.+?)<\/title>.+?<itunes(.+?)<\/itunes:summary>.+?<enclosure url="(.+?)".+? />.+?<guid(.+?)<\/guid>.+?<pubDate>(.+?)<\/pubDate>', re.S).findall(match)
        	for title, junk, url, guid, pubdate in elems:
            		addLink(title, pubdate, url, '')


def VIDEOLINKS(url,name):
        req = urllib2.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
        #req.add_header('User-Agent', 'iTunes/9.0.2 (Windows; U)')
        response = urllib2.urlopen(req)
        link=response.read()
        response.close()
        match=re.compile('').findall(link)
        for url in match:
                addLink(name,'',url,'')
        

                
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




def addLink(name,pDate,url,iconimage):
    if (COOKIE_EXIST()) == True:
        url = url + URLENCODECOOKIE()

    ok=True
    liz=xbmcgui.ListItem(name, label2=pDate, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
    liz.setInfo( type="Video", infoLabels={ "Title": name, "date": pDate } )
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
    STARTUP()
    print ""
    CATEGORIES()
       
elif mode==1:
    print ""+url
    INDEX(url)
        
elif mode==2:
    print ""+url
    VIDEOLINKS(url,name)



xbmcplugin.endOfDirectory(int(sys.argv[1]))
