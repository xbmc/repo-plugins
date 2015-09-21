#!/usr/bin/python
#
#
# Written by Ksosez, BlueCop, Romans I XVI, locomot1f, MetalChris
# Released under GPL(v2)

import urllib, urllib2, xbmcplugin, xbmcaddon, xbmcgui, os, random, string, re
import cookielib
import time
from datetime import datetime, timedelta
from bs4 import BeautifulSoup, SoupStrainer

## Get the settings

selfAddon = xbmcaddon.Addon(id='plugin.video.espn_3')
translation = selfAddon.getLocalizedString
defaultimage = 'special://home/addons/plugin.video.espn_3/icon.png'
defaultfanart = 'special://home/addons/plugin.video.espn_3/fanart.jpg'
defaultlive = 'special://home/addons/plugin.video.espn_3/resources/media/new_live.png'
defaultreplay = 'special://home/addons/plugin.video.espn_3/resources/media/new_replay.png'
defaultupcoming = 'special://home/addons/plugin.video.espn_3/resources/media/new_upcoming.png'
StreamType = selfAddon.getSetting('StreamType')
pluginpath = selfAddon.getAddonInfo('path')
pluginhandle = int(sys.argv[1])

ADDONDATA = xbmc.translatePath('special://profile/addon_data/plugin.video.espn_3/')
if not os.path.exists(ADDONDATA):
    os.makedirs(ADDONDATA)
USERFILE = os.path.join(ADDONDATA,'userdata.xml')


cj = cookielib.LWPCookieJar()
networkmap = {'n360':'ESPN3'}

channels = '&channel='
channels += 'espn3'

def CATEGORIES():
    curdate = datetime.utcnow()
    upcoming = int(selfAddon.getSetting('upcoming'))+1
    days = (curdate+timedelta(days=upcoming)).strftime("%Y%m%d")
    addDir(translation(30029), 'http://sports-ak.espn.go.com/watchespn/feeds/startup?action=live'+channels, 1, defaultlive)
    addDir(translation(30030), 'http://sports-ak.espn.go.com/watchespn/feeds/startup?action=upcoming'+channels+'&endDate='+days+'&startDate='+curdate.strftime("%Y%m%d"), 2,defaultupcoming)
    enddate = '&endDate='+ (curdate+timedelta(days=1)).strftime("%Y%m%d")
    replays1 = [5,10,15,20,25]
    replays1 = replays1[int(selfAddon.getSetting('replays1'))]
    start1 = (curdate-timedelta(days=replays1)).strftime("%Y%m%d")
    replays2 = [10,20,30,40,50]
    replays2 = replays2[int(selfAddon.getSetting('replays2'))]
    start2 = (curdate-timedelta(days=replays2)).strftime("%Y%m%d")
    replays3 = [30,60,90,120]
    replays3 = replays3[int(selfAddon.getSetting('replays3'))]
    start3 = (curdate-timedelta(days=replays3)).strftime("%Y%m%d")
    replays4 = [60,90,120,240]
    replays4 = replays4[int(selfAddon.getSetting('replays4'))]
    start4 = (curdate-timedelta(days=replays4)).strftime("%Y%m%d")
    startAll = (curdate-timedelta(days=365)).strftime("%Y%m%d")
    addDir(translation(30031)+str(replays1)+' Days', 'http://sports-ak.espn.go.com/watchespn/feeds/startup?action=replay'+channels+enddate+'&startDate='+start1, 2, defaultreplay)
    addDir(translation(30031)+str(replays2)+' Days', 'http://sports-ak.espn.go.com/watchespn/feeds/startup?action=replay'+channels+enddate+'&startDate='+start2, 2, defaultreplay)
    addDir(translation(30031)+str(replays3)+' Days', 'http://sports-ak.espn.go.com/watchespn/feeds/startup?action=replay'+channels+enddate+'&startDate='+start3, 2, defaultreplay)
    addDir(translation(30031)+str(replays3)+'-'+str(replays4)+' Days', 'http://sports-ak.espn.go.com/watchespn/feeds/startup?action=replay'+channels+'&endDate='+start3+'&startDate='+start4, 2, defaultreplay)
    addDir(translation(30032), 'http://sports-ak.espn.go.com/watchespn/feeds/startup?action=replay'+channels+enddate+'&startDate='+startAll, 2, defaultreplay)
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

def LISTNETWORKS(url,name):
    pass

def LISTSPORTS(url,name):
    data = get_html(url)
    #data = '<?xml version="1.0" encoding="CP1252"?>'+data
    SaveFile('videocache.xml', data, ADDONDATA)
    if 'action=replay' in url:
        image = defaultreplay
    elif 'action=upcoming' in url:
        image = defaultupcoming
    else:
        image = defaultimage
    addDir(translation(30034), url, 1, image)
    sports = []
    events = BeautifulSoup(data, 'html.parser', parse_only = SoupStrainer('event'))
    for event in events.find_all('event'):
        sport = event.find('sportdisplayvalue').string.title().encode('utf-8')
        if sport not in sports:
            sports.append(sport)
    for sport in sports:
        addDir(sport, url, 3, image)
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_VIDEO_SORT_TITLE)
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

def INDEXBYSPORT(url,name):
    INDEX(url,name,bysport=True)
    
def INDEX(url,name,bysport=False):
    if 'action=live' in url:
        data = get_html(url)
        #data = '<?xml version="1.0" encoding="CP1252"?>'+data
    else:
        data = ReadFile('videocache.xml', ADDONDATA)
    events = BeautifulSoup(data, 'html.parser', parse_only = SoupStrainer('event'))
    for event in events.find_all('event'):
        sport = event.find('sportdisplayvalue').string.title().encode('utf-8')
        desktopStreamSource = event.find('desktopstreamsource').string
        if name <> sport and bysport == True:
            continue
        elif desktopStreamSource == 'HLS' and StreamType == 'true':
        	  pass
        else:
            ename = event.find('name').string.encode('utf-8')
            eventid = event.get('id')
            simulcastAiringId = event.find('simulcastairingid').string
            desktopStreamSource = event.find('desktopstreamsource').string
            bamContentId = event.get('bamcontentid')
            bamEventId = event.get('bameventid')
            authurl = eventid
            authurl += ','+bamContentId
            authurl += ','+bamEventId
            authurl += ','+simulcastAiringId
            authurl += ','+desktopStreamSource
            sport2 = event.find('sport').string.title()
            if sport <> sport2:
                sport += ' ('+sport2+')'
            league = event.find('league').string
            location = event.find('site').string
            networkid = event.find('networkid').string
            if networkid is not None:
                network = networkmap[networkid]
            fanart = event.find('large').string
            fanart = fanart.split('&')[0]
            thumb = event.find('large').string
            mpaa = event.find('parentalrating').string
            starttime = int(event.find('starttimegmtms').string)/1000
	    eventedt = int(event.find('starttime').string)
            etime = time.strftime("%I:%M %p",time.localtime(float(starttime)))
            endtime = int(event.find('endtimegmtms').string)/1000
            start = time.strftime("%m/%d/%Y %I:%M %p",time.localtime(starttime))
            aired = time.strftime("%Y-%m-%d",time.localtime(starttime))
            date = time.strftime("%m/%d/%Y",time.localtime(starttime))
            udate = time.strftime("%m/%d",time.localtime(starttime))
            now = datetime.now().strftime('%H%M')
            etime24 = time.strftime("%H%M",time.localtime(starttime)) 

            if 'action=live' in url and now > etime24:
                length = str(int(round((endtime - time.time())/60)))
                ename = '[COLOR=FF'+str(selfAddon.getSetting('color'))+']'+" - ".join((etime, ename))+'[/COLOR]'
            elif 'action=live' in url:
                length = str(int(round((endtime - time.time())/60)))
                ename = " - ".join((etime, ename))
            else:
                length = str(int(round((endtime - starttime)/60)))
                ename = " - ".join((udate, etime, ename))
            
            
            end = event.find('summary').string
            if end == '':
                end = event.find('caption').string
            else: end = 'No Summary/ Caption Provided'

            plot = ''
            if sport <> None and sport <> ' ':
                plot += 'Sport: '+sport+'\n'
            if league <> None and league <> ' ':
                plot += 'League: '+league+'\n'
            if location <> None and location <> ' ':
                plot += 'Location: '+location+'\n'
            if start <> None and start <> ' ':
                plot += 'Air Date: '+start+'\n'
            if length <> None and length <> ' ' and 'action=live' in url:
                plot += 'Duration: Approximately '+length+' minutes remaining'+'\n'
	    elif length <> None and length <> ' ' and ('action=replay' in url or 'action=upcoming' in url):
		plot += 'Duration: '+length+' minutes'+'\n'
            plot += end
            infoLabels = {'title':ename,
                          'genre':sport,
                          'plot':plot,
                          'aired':aired,
                          'premiered':aired,
                          'duration':length,
                          'studio':'ESPN 3',
                          'mpaa':mpaa}
            if 'action=upcoming' in url:
                mode = 5
            elif networkid == 'n360':
                mode = 4
            elif networkid == 'n501':
                mode = 6
            elif networkid == 'n502':
                mode = 7   
            elif networkid == 'n599':
                mode = 8
            elif networkid == 'ngl':
                mode = 9
            elif networkid == 'nbb':
                mode = 10  
            addLink(ename, authurl, mode, fanart, fanart, infoLabels=infoLabels)
    xbmcplugin.setContent(pluginhandle, 'episodes')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

def PLAYESPN3(url):
    PLAY(url,'n360')
    
def PLAY(url,videonetwork):
    data = ReadFile('userdata.xml', ADDONDATA)
    soup = BeautifulSoup(data, 'html.parser')
    affiliateid = soup('name')[0].string
    swid = soup('personalization')[0]['swid']
    identityPointId = affiliateid+':'+swid
    
    # Split up the url so they can be used as needed
    url_split = url
    url_split = url.split(',')
    eventid = str(url_split[0])    
    contentId = str(url_split[1])
    eventId = str(url_split[2]) 
    simulcastAiringId = str(url_split[3]) 
    streamType = str(url_split[4]) 
    
    pk = ''.join([random.choice(string.ascii_letters + string.digits) for n in xrange(51)])
    pkan = pk + ('%3D')
    config = 'https://espn.go.com/watchespn/player/config'
    data = get_html(config)
    networks = BeautifulSoup(data, 'html.parser', parse_only = SoupStrainer('network'))
    for network in networks:
        if videonetwork == network['id']:
            playedId = network['playerid']
            cdnName = network['defaultcdn']
            channel = network['name']
            if streamType == 'HLS':
                 networkurl = 'http://broadband.espn.go.com/espn3/auth/watchespn/startSession?v=1.5'
            elif streamType == 'HDS' or streamType == 'RTMP':
                 networkurl = 'https://espn-ws.bamnetworks.com/pubajaxws/bamrest/MediaService2_0/op-findUserVerifiedEvent/v-2.1'
            authurl = authurl = networkurl
            if '?' in authurl:
                authurl +='&'
            else:
                authurl +='?'
            
            if streamType == 'HLS':
		       authurl += 'affiliate='+affiliateid
		       authurl += '&cdnName='+cdnName
		       authurl += '&channel='+channel
		       authurl += '&playbackScenario=FMS_CLOUD'
		       authurl += '&pkan='+pkan
		       authurl += '&pkanType=SWID'
		       authurl += '&eventid='+eventid
		       authurl += '&simulcastAiringId='+simulcastAiringId
		       authurl += '&rand='+str(random.randint(100000,999999))
		       authurl += '&playerId='+playedId
            elif streamType == 'HDS' or streamType == 'RTMP':
		       authurl += 'identityPointId='+affiliateid
		       authurl += '&cdnName='+cdnName
		       authurl += '&channel='+channel
		       authurl += '&playbackScenario=FMS_CLOUD'
		       authurl += '&partnerContentId='+eventid
		       authurl += '&eventId='+eventId
		       authurl += '&contentId='+contentId
		       authurl += '&rand='+str(random.randint(100000,999999))
		       authurl += '&playerId='+playedId     
            html = get_html(authurl)
            tree = BeautifulSoup(html, 'html.parser')
            authstatus = tree.find('auth-status')
            blackoutstatus = tree.find('blackout-status')
            if not authstatus.find('successstatus'):
                if not authstatus.find('notauthorizedstatus'):
                    if authstatus.find('errormessage').string:
                        dialog = xbmcgui.Dialog()
                        import textwrap
                        errormessage = authstatus.find('errormessage').string
                        try:
                            errormessage = textwrap.fill(errormessage, width=50).split('\n')
                            dialog.ok(translation(30037), errormessage[0],errormessage[1],errormessage[2])
                        except:
                            dialog.ok(translation(30037), errormessage[0])
                        return
                else:
                    if not blackoutstatus.find('successstatus'):
                        if blackoutstatus.find('blackout').string:
                            dialog = xbmcgui.Dialog()
                            dialog.ok(translation(30040), blackoutstatus.find('blackout').string)
                            return
            #streamType = tree.find('streamtype').string
            smilurl = tree.find('url').string
            #xbmc.log('ESPN3:  smilurl: '+smilurl)
            #xbmc.log('ESPN3:  streamType: '+streamType)
            if smilurl == ' ' or smilurl == '':
                dialog = xbmcgui.Dialog()
                dialog.ok(translation(30037), translation(30038),translation(30039))
                return

            if streamType == 'HLS':
                 finalurl = smilurl
                 item = xbmcgui.ListItem(path=finalurl)
                 return xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)

            elif streamType == 'HDS' or streamType == 'RTMP':  
		       auth = smilurl.split('?')[1]
		       smilurl += '&rand='+str(random.randint(100000,999999))
		   
		       #Grab smil url to get rtmp url and playpath
		       html = get_html(smilurl)
		       soup = BeautifulSoup(html, 'html.parser')
		       rtmp = soup.findAll('meta')[0]['base']
		       # Live Qualities
		       #     0,     1,     2,      3,      4
		       # Replay Qualities
		       #            0,     1,      2,      3
		       # Lowest, Low,  Medium, High,  Highest
		       # 200000,400000,800000,1200000,1800000
		       playpath=False
		       if selfAddon.getSetting("askquality") == 'true':
		           streams = soup.findAll('video')
		           quality=xbmcgui.Dialog().select(translation(30033), [str(int(stream['system-bitrate'])/1000)+'kbps' for stream in streams])
		           if quality!=-1:
		               playpath = streams[quality]['src']
		           else:
		               return
		       if 'ondemand' in rtmp:
		           if not playpath:
		               playpath = soup.findAll('video')[int(selfAddon.getSetting('replayquality'))]['src']
		           finalurl = rtmp+'/?'+auth+' playpath='+playpath
		       elif 'live' in rtmp:
		           if not playpath:
		               select = int(selfAddon.getSetting('livequality'))
		               videos = soup.findAll('video')
		               videosLen = len(videos)-1
		               if select > videosLen:
		                   select = videosLen
		               playpath = videos[select]['src']
		           finalurl = rtmp+' live=1 playlist=1 subscribe='+playpath+' playpath='+playpath+'?'+auth
		       item = xbmcgui.ListItem(path=finalurl)
		       return xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)


def saveUserdata():
    userdata1 = 'http://broadband.espn.go.com/espn3/auth/watchespn/userData?format=xml'
    data1 = get_html(userdata1)
    SaveFile('userdata.xml', data1, ADDONDATA)
    soup = BeautifulSoup(data1, 'html.parser')
    checkrights = 'http://broadband.espn.go.com/espn3/auth/espnnetworks/user'

def get_html(url):
    try:
        xbmc.log('ESPN3:  get_html: '+url)
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
        opener.addheaders = [('User-Agent', 'Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:38.0) Gecko/20100101 Firefox/38.0')]
        usock = opener.open(url)
        response = usock.read()
        #xbmc.log('ESPN3:  get_response: '+response)
        usock.close()
        return response
    except: 
        xbmc.log('ESPN3:  get_response: Could not open URL: '+url)
        return False

def get_params():
    param = []
    paramstring = sys.argv[2]
    if len(paramstring) >= 2:
        params = sys.argv[2]
        cleanedparams = params.replace('?', '')
        if (params[len(params) - 1] == '/'):
            params = params[0:len(params) - 2]
        pairsofparams = cleanedparams.split('&')
        param = {}
        for i in range(len(pairsofparams)):
            splitparams = {}
            splitparams = pairsofparams[i].split('=')
            if (len(splitparams)) == 2:
                param[splitparams[0]] = splitparams[1]

    return param

def SaveFile(filename, data, dir):
    path = os.path.join(dir, filename)
    try:
        file = open(path,'w')
    except:
        file = open(path,'w+')
    file.write(data)
    file.close()

def ReadFile(filename, dir):
    path = os.path.join(dir, filename)
    if filename == 'userdata.xml':
        try:
            file = open(path,'r')
        except:
            saveUserdata()
            file = open(path,'r')
    else:
        file = open(path,'r')
    return file.read()

def addLink(name, url, mode, iconimage, fanart=False, infoLabels=False):
    u = sys.argv[0] + "?url=" + urllib.quote_plus(url) + "&mode=" + str(mode) + "&name=" + urllib.quote_plus(name)
    ok = True
    liz = xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
    if not infoLabels:
        infoLabels={"Title": name}
    liz.setInfo(type="Video", infoLabels=infoLabels)
    liz.setProperty('IsPlayable', 'true')
    if not fanart:
        fanart=defaultfanart
    liz.setProperty('fanart_image',fanart)
    ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz)
    return ok


def addDir(name, url, mode, iconimage, fanart=False, infoLabels=False):
    u = sys.argv[0] + "?url=" + urllib.quote_plus(url) + "&mode=" + str(mode) + "&name=" + urllib.quote_plus(name)
    ok = True
    liz = xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
    if not infoLabels:
        infoLabels={"Title": name}
    liz.setInfo(type="Video", infoLabels=infoLabels)
    if not fanart:
        fanart=defaultfanart
    liz.setProperty('fanart_image',fanart)
    ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=True)
    return ok

params = get_params()
url = None
name = None
mode = None
cookie = None

try:
    url = urllib.unquote_plus(params["url"])
except:
    pass
try:
    name = urllib.unquote_plus(params["name"])
except:
    pass
try:
    mode = int(params["mode"])
except:
    pass

xbmc.log("Mode: " + str(mode))
xbmc.log("URL: " + str(url))
xbmc.log("Name: " + str(name))

if mode == None or url == None or len(url) < 1:
    xbmc.log("Generate Main Menu")
    CATEGORIES()
elif mode == 1:
    xbmc.log("Indexing Videos")
    INDEX(url,name)
elif mode == 2:
    xbmc.log("List sports")
    LISTSPORTS(url,name)
elif mode == 3:
    xbmc.log("Index by sport")
    INDEXBYSPORT(url,name)
elif mode == 4:
    PLAYESPN3(url)
elif mode == 5:
    xbmc.log("Upcoming")
    dialog = xbmcgui.Dialog()
    dialog.ok(translation(30035), translation(30036))

