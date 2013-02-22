#!/usr/bin/python
# -*- coding: utf-8 -*-
import xbmcplugin, xbmcgui, sys, urllib, urllib2, cookielib, re, random, xbmcaddon, time, socket

socket.setdefaulttimeout(30)
thisPlugin = int(sys.argv[1])
settings = xbmcaddon.Addon(id='plugin.video.fernsehkritik_tv')
useCouch = settings.getSetting('useCouch') == 'true'
userAgentString = 'Mozilla/5.0 (X11; Linux x86_64; rv:18.0) Gecko/20100101 Firefox/18.0'

def translation(id):
    return str(settings.getLocalizedString(id).encode('utf-8'))

def index():
    addDir(translation(30001), 'http://fernsehkritik.tv/tv-magazin/')
    addDir(translation(30002), 'http://fernsehkritik.tv/pktv/')
    if useCouch:
        addDir(translation(30009), 'https://couch.fernsehkritik.tv/feed/postecke/mp4')
        addDir(translation(30010), 'https://couch.fernsehkritik.tv/feed/postecke/mp3')
    addDir(translation(30005), 'http://fernsehkritik.tv/extras/')
    addDir(translation(30007), 'http://fernsehkritik.tv/extras/sftv/')
    addDir(translation(30008), 'http://fernsehkritik.tv/extras/pktv/')
    addDir(translation(30006), 'http://fernsehkritik.tv/extras/aktuell/')
    xbmcplugin.endOfDirectory(thisPlugin)

def listVideos(url):
    if 'couch.fernsehkritik.tv/feed' not in url:
        content = getUrl(url)
    else:
        content = getCouchFeed(url)
    
    if url == 'http://fernsehkritik.tv/tv-magazin/' or url == 'http://fernsehkritik.tv/tv-magazin/komplett/':
        latestEntry = None
        
        # if Couch user, get first episode from Couch feed
        if useCouch and url == 'http://fernsehkritik.tv/tv-magazin/':
            contentLatest = getCouchFeed('https://couch.fernsehkritik.tv/feed/mov')
            episodeMatch  = re.compile('<title>\s*Folge (\d+) vom (\d{1,2}\. [\wä]+ \d{4})\s*.*?<itunes:summary>\s*(.*?)\s*</itunes:summary>', re.DOTALL).search(contentLatest)
            latestEntry   = assembleEpisodeEntry(episodeMatch.group(1), 'https://couch.fernsehkritik.tv/feed/fernsehkritik' + episodeMatch.group(1) + '.mov', episodeMatch.group(2), episodeMatch.group(3))
            addLink(latestEntry['title'], latestEntry['url'], 2, 'http://fernsehkritik.tv/images/magazin/folge' + latestEntry['number'] + '.jpg', latestEntry['desc'])
        
        episodes = re.compile('<h2>\s*<a[^>]+href="(?:\.\.|)?/folge-(\d+)/?"[^>]*>\s*Folge (?:\d+) vom (\d{1,2}\. [\wä]+ \d{4})\s*</a>', re.DOTALL).finditer(content)
        
        for episode in episodes:
            
            if useCouch:
                episodeUrl = 'https://couch.fernsehkritik.tv/dl/fernsehkritik' + episode.group(1) + '.mov'
            else:
                episodeUrl = 'http://fernsehkritik.tv/folge-' + episode.group(1) + '/'
            
            episodeDesc  = re.compile('<div id="d' + episode.group(1) + '">.*?<div class="desc">\s*<ul>\s*(.*?)\s*</ul>', re.DOTALL).search(content).group(1)
            episodeDesc  = re.sub('<[^>]*?>', '', episodeDesc.replace('<li>', '• '))
            
            # If first episode is already in the list, don't add it again
            # (i.e. if it's already available for non-couch users)
            if useCouch and latestEntry != None and latestEntry['number'] == episode.group(1):
                continue
            
            entry = assembleEpisodeEntry(episode.group(1), episodeUrl, episode.group(2), episodeDesc)
            addLink(entry['title'], entry['url'], 2, 'http://fernsehkritik.tv/images/magazin/folge' + entry['number'] + '.jpg', entry['desc'])
        
        if url == 'http://fernsehkritik.tv/tv-magazin/':
            # Insert missing episode
            episodeNumber = str(int(episode.group(1)) - 1)
            
            if useCouch:
                episodeUrl = 'http://couch.fernsehkritik.tv/dl/fernsehkritik' + episodeNumber + '.mov'
            else:
                episodeUrl = 'http://fernsehkritik.tv/folge-' + episodeNumber + '/'
                
            content       = getUrl('http://fernsehkritik.tv/feed/')
            episodeMatch  = re.compile('<item>\s*<title>\s*Folge ' + episodeNumber + ' vom (\d{1,2}\. [\wä]+ \d{4})\s*</title>.+?<description>(.+?)</description>', re.DOTALL).search(content)
            episodeDesc   = re.sub('&lt;.+?&gt;', '', episodeMatch.group(2).replace('&lt;li&gt;', '• '))
            entry         = assembleEpisodeEntry(episodeNumber, episodeUrl, episodeMatch.group(1), episodeDesc)
            addLink(entry['title'], entry['url'], 2, 'http://fernsehkritik.tv/images/magazin/folge' + episodeNumber + '.jpg', episodeDesc)
            
            # Insert directory for older episodes
            addDir(translation(30004), 'http://fernsehkritik.tv/tv-magazin/komplett/')
    
    elif url == 'https://couch.fernsehkritik.tv/feed/postecke/mp4' or url == 'https://couch.fernsehkritik.tv/feed/postecke/mp3':
        episodes = re.compile('<item>\s*<title>\s*(.*?)\s*</title>.*?<enclosure url="([^"]+)".*?<itunes:summary><!\[CDATA\[(.*?)\]\]></itunes:summary>', re.DOTALL).finditer(content)
        for episode in episodes:
            addLink(episode.group(1), episode.group(2), 2, '', episode.group(3), url == 'https://couch.fernsehkritik.tv/feed/postecke/mp4')
    
    else:
        spl = content.split('<div class="lclmo" id=')
        for i in range(1, len(spl), 1):
            entry  = spl[i]
            match  = re.compile('<a href="(.+?)">(.+?)</a>', re.DOTALL).findall(entry)
            url    = match[0][0]
            title  = match[0][1].replace('&quot;','')
            match  = re.compile('src="(.+?)"', re.DOTALL).findall(entry)
            thumb  = match[0]
            thumb  = thumb.replace('../', '/')
            newUrl = ''
            if url.find('/pktv/') == 0:
                newUrl = 'http://fernsehkritik.tv' + url
            elif url.find('#extra-') == 0:
                newUrl = url[7:]
            else:
                newUrl = 'http://fernsehkritik.tv' + url
            addLink(title,newUrl,2,'http://fernsehkritik.tv' + thumb)
    
    xbmcplugin.endOfDirectory(thisPlugin)

def playVideo(urlOne):
    if useCouch and 'couch.fernsehkritik.tv' in urlOne:
        opener   = urllib2.build_opener(urllib2.HTTPCookieProcessor(getCouchSession()))
        response = opener.open(urlOne)
        videoUrl = response.geturl()
        response.close()
        
        listitem = xbmcgui.ListItem(path=videoUrl)
        return xbmcplugin.setResolvedUrl(thisPlugin, True, listitem)
        
    elif urlOne.find('http://') == 0:
        content  = getUrl(urlOne)
        match    = re.compile('<a href="(.+?)">', re.DOTALL).findall(content)
        filename = ''
        for url in match:
            if url.find('.mov') >= 0:
                filename = url
        if filename != '':
            listitem = xbmcgui.ListItem(path=filename)
            return xbmcplugin.setResolvedUrl(thisPlugin, True, listitem)
        else:
            content = getUrl(urlOne + '/Start')
            try:
              match   = re.compile(r'var flattr_tle = \'(.+?)\'', re.DOTALL).findall(content)
              title   = match[0]
              if content.find('playlist = [') >= 0:
                  content  = content[content.find('playlist = ['):]
                  content  = content[:content.find('];')]
                  match    = re.compile(r"\{ url: base \+ '(\d+(?:-\d+)?\.flv)' \}", re.DOTALL).findall(content)
                  
                  urlFull="stack://"
                  for i,filename in enumerate(match):
                      url = 'http://dl' + str(random.randint(1, 3)) + '.fernsehkritik.tv/fernsehkritik' + filename + " , "
                      urlFull += url
                  urlFull=urlFull[:-3]
                  
                  listitem = xbmcgui.ListItem(path=urlFull)
                  return xbmcplugin.setResolvedUrl(thisPlugin, True, listitem)
              else:
                  match = re.compile("file=='(.+?)'", re.DOTALL).findall(content)
                  filename = match[0]
                  listitem = xbmcgui.ListItem(path='http://dl' + str(random.randint(1,3)) + '.fernsehkritik.tv/antik/' + filename)
                  return xbmcplugin.setResolvedUrl(thisPlugin, True, listitem)
            except:
              xbmc.executebuiltin('XBMC.Notification(Info:,'+str(translation(30209))+',5000)')
    else:
        content = getUrl('http://fernsehkritik.tv/swf/extras_cfg.php?id=' + urlOne)
        match   = re.compile('"file":"(.+?)"', re.DOTALL).findall(content)
        file    = match[0]
        listitem = xbmcgui.ListItem(path=file)
        return xbmcplugin.setResolvedUrl(thisPlugin, True, listitem)

def getUrl(url):
    if useCouch and 'couch.fernsehkritik.tv' in url:
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(getCouchSession()))
        opener.addheaders = [('User-Agent', userAgentString)]
        response = opener.open(url)
    else:
        request = urllib2.Request(url)
        request.add_header('User-Agent',userAgentString)
        response = urllib2.urlopen(request)
        
    link = response.read()
    response.close()
    
    return link

def getCouchFeed(url):
    passwordMgr = urllib2.HTTPPasswordMgrWithDefaultRealm()
    passwordMgr.add_password(None, url, settings.getSetting('couchUsername'), settings.getSetting('couchPassword'))
    authHandler   = urllib2.HTTPBasicAuthHandler(passwordMgr)
    opener        = urllib2.build_opener(authHandler)
    request       = opener.open(url)
    content       = request.read()
    request.close()
    return content

def assembleEpisodeEntry(episodeNumber, url, germanDate, desc):
    episode = {}
    episode['number'] = episodeNumber
    episode['date']   = time.strftime('%d. %B %Y', parseGermanDate(germanDate))
    episode['title']  = translation(30003).format(episode=episode['number'], date=episode['date'])
    episode['url']    = url
    episode['desc']   = desc
    
    return episode


def getCouchSession():
    if not useCouch:
        return None
    
    cookieJar = None
    if hasattr(getCouchSession, 'cj'):
        cookieJar = getCouchSession.cj
    
    if cookieJar == None:
        postData = {
            'username' : settings.getSetting('couchUsername'),
            'password' : settings.getSetting('couchPassword')
        }
        postDataEncoded   = urllib.urlencode(postData)
        cookieJar         = cookielib.CookieJar()
        opener            = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookieJar))
        opener.addheaders = [('User-Agent', userAgentString)]
        # Get session cookie
        response          = opener.open('https://couch.fernsehkritik.tv/')
        # Log in
        response          = opener.open('https://couch.fernsehkritik.tv/login.php', postDataEncoded)
        response.close()
    
    return cookieJar

def addLink(name, url, mode=1, iconimage='', description='', isVideo=True):
    u    = sys.argv[0] + '?url=' + urllib.quote_plus(url) + '&mode=' + str(mode)
    ok   = True
    icon = 'DefaultVideo.png'
    if (not isVideo):
        icon = 'DefaultAudio.png'
    liz  = xbmcgui.ListItem(name, iconImage=icon, thumbnailImage=iconimage)
    liz.setInfo( type="Video", infoLabels={ 'Title': name, 'Plot': description, 'Director': 'Holger Kreymeier' } )
    liz.setProperty('IsPlayable', 'true')
    ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz)
    return ok

def addDir(name, url, mode=1, iconimage=''):
    u   = sys.argv[0] + '?url=' + urllib.quote_plus(url) + '&mode=' + str(mode)
    ok  = True
    liz = xbmcgui.ListItem(name, iconImage='DefaultFolder.png', thumbnailImage=iconimage)
    liz.setInfo(type="Video", infoLabels={ 'Title': name })
    ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=True)
    return ok

def parseGermanDate(dateString):
    # Parse month manually to avoid changing the locale
    months = [
        'Januar', 'Februar', 'März', 'April',
        'Mai', 'Juni', 'Juli', 'August',
        'September', 'Oktober', 'November', 'Dezember']
    for key,month in enumerate(months):
        dateString = dateString.replace(month, str(int(key) + 1).zfill(2))
    
    return time.strptime(dateString, '%d. %m %Y')

def parameters_string_to_dict(parameters):
    """Convert parameters encoded in a URL to a dict."""
    paramDict = {}
    if parameters:
        paramPairs = parameters[1:].split('&')
        for paramsPair in paramPairs:
            paramSplits = paramsPair.split('=')
            if (len(paramSplits)) == 2:
                paramDict[paramSplits[0]] = paramSplits[1]
    return paramDict

params=parameters_string_to_dict(sys.argv[2])
mode=params.get('mode')
url=params.get('url')
if type(url)==type(str()):
  url=urllib.unquote_plus(url)

if mode == "1":
    listVideos(url)
elif mode == "2":
    playVideo(url)
else:
    index()
