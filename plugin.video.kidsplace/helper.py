import xbmcplugin
import xbmcgui
import xbmcaddon
import sys, re
import urllib, urllib2

from StringIO import StringIO
import gzip

thisPlugin = int(sys.argv[1])

def load_page(url , proxy=False):
    print url
    if proxy == True:
        proxy_address = xbmcplugin.getSetting(thisPlugin,'proxy_address')
        proxy_port = xbmcplugin.getSetting(thisPlugin,'proxy_port')
        if len(proxy_address):
            us_proxy = "http://"+proxy_address+":"+proxy_port
            print 'Using proxy: ' + us_proxy
            proxy_handler = urllib2.ProxyHandler({'http':us_proxy})
            opener = urllib2.build_opener(proxy_handler)
            urllib2.install_opener(opener)
    
    req = urllib2.Request(url)
    req.add_header('Accept-encoding', 'gzip')
    response = urllib2.urlopen(req)
    
    if response.info().get('Content-Encoding') == 'gzip':
        buf = StringIO( response.read())
        f = gzip.GzipFile(fileobj=buf)
        link = f.read()
    else:
        link = response.read()
    
    response.close()
    return link


def removeHtmlSpecialChars(inputStr):
    inputStr = inputStr.replace("&#8211;", "-")
    inputStr = inputStr.replace("&#8216;", "'")
    inputStr = inputStr.replace("&#8217;", "'")#\x92
    inputStr = inputStr.replace("&#8220;","\"")#\x92
    inputStr = inputStr.replace("&#8221;","\"")#\x92
    inputStr = inputStr.replace("&#8230;", "'")
   
    inputStr = inputStr.replace("&#038;", chr(38))# &
    inputStr = inputStr.replace("&#039;", chr(39))# '
    inputStr = inputStr.replace("&apos;", "'")# '
    inputStr = inputStr.replace("&amp;", "&")# '
    
    return inputStr

def addDirectoryItem(name, parameters={}, pic="", folder=True, duration='', plot='', date='', size=0, year=0):
    if not folder:
        li = xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=pic)
        li.setProperty('IsPlayable', 'true')
        li.setInfo("video",{
            "size": size,
            "date": date,
            "year": year,
            "title": name,
            "plot": plot,
            "duration": duration
          }); 
    else:
        li = xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=pic)
    url = sys.argv[0] + '?' + urllib.urlencode(parameters)
    return xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=url, listitem=li, isFolder=folder)

def endOfDirectory():
    xbmcplugin.endOfDirectory(thisPlugin)

def setResolvedUrl(streamUrl):
    item = xbmcgui.ListItem(path=streamUrl)
    xbmcplugin.setResolvedUrl(thisPlugin, True, item)

def extractMrss(feed):
    extractItem = re.compile("<item>.*?</item>",re.DOTALL)
    
    extractInfo = re.compile("<title>(.*?)</title>.*?(<media:content.*?url=\"(.*?)\".*?/>).*?<media:thumbnail.*?url=\"(.*?)\"",re.DOTALL)
    extractInfoPlayer = re.compile("<media:player url=\"(.*?)\"/>",re.DOTALL)
    extractInfoContentDuration = re.compile("duration=\"(.*?)\"")
    extractInfoDescription = re.compile("<description>(.*?)</description>",re.DOTALL)
    mediaItems = []
    for item in extractItem.finditer(feed):
        itemContent = item.group(0)
        
        media = extractInfo.search(itemContent)
        mediaPlayerItem = extractInfoPlayer.search(itemContent)
        mediaDurationItem = extractInfoContentDuration.search(media.group(2))
        mediaDescriptionItem = extractInfoDescription.search(itemContent)
        
        mediaTitle = removeHtmlSpecialChars(media.group(1))
        mediaUrl = media.group(3)
        mediaThumb = media.group(4)
        mediaPlayer = ""
        if mediaPlayerItem is not None:
            mediaPlayer = mediaPlayerItem.group(1)
        mediaDuration = ""
        if mediaDurationItem is not None:
            mediaDurationValue = mediaDurationItem.group(1)
            if mediaDurationValue.find(":"):
                mediaDuration = str(mediaDurationValue)
            else:
                mediaDuration = str(int(mediaDurationValue)/60)
        mediaDescription = ""
        if mediaDescriptionItem is not None:
            mediaDescription = mediaDescriptionItem.group(1)
        mediaItems.append({"title":mediaTitle, "img":mediaThumb, "url":mediaUrl, "player":mediaPlayer, "duration":mediaDuration, "plot":mediaDescription})
    return mediaItems

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

def removeTags(input):
    p = re.compile(r'<.*?>')
    return p.sub('', input)
