import urllib2
import urllib
import xbmc
import xbmcplugin
import xbmcgui
import xbmcaddon
import xbmcvfs
import sys
import os
import cookielib

addon = xbmcaddon.Addon(id='plugin.video.mlbmc')
language = addon.getLocalizedString
home = xbmc.translatePath(addon.getAddonInfo('path'))
profile = xbmc.translatePath(addon.getAddonInfo('profile'))
cookie_file = os.path.join(profile, 'cookie_file')
fanart = os.path.join(home, 'fanart.jpg')
fanart1 = 'http://mlbmc-xbmc.googlecode.com/svn/icons/fanart1.jpg'
fanart2 = 'http://mlbmc-xbmc.googlecode.com/svn/icons/fanart2.jpg'
icon = os.path.join(home, 'icon.png')
addon_version = addon.getAddonInfo('version')
debug = addon.getSetting('debug')
cookie_jar = cookielib.LWPCookieJar(cookie_file)

TeamCodes = {
    '108': ('Los Angeles Angels', 'ana'),
    '109': ('Arizona Diamondbacks', 'ari'),
    '144': ('Atlanta Braves', 'atl'),
    '110': ('Baltimore Orioles', 'bal'),
    '111': ('Boston Red Sox', 'bos'),
    '112': ('Chicago Cubs', 'chc'),
    '113': ('Cincinnati Reds', 'cin'),
    '114': ('Cleveland Indians', 'cle'),
    '115': ('Colorado Rockies', 'col'),
    '145': ('Chicago White Sox', 'cws'),
    '116': ('Detroit Tigers', 'det'),
    '146': ('Florida Marlins', 'fla'),
    '117': ('Houston Astros', 'hou'),
    '118': ('Kansas City Royals', 'kc'),
    '119': ('Los Angeles Dodgers', 'la'),
    '158': ('Milwaukee Brewers', 'mil'),
    '142': ('Minnesota Twins', 'min'),
    '121': ('New York Mets', 'nym'),
    '147': ('New York Yankees', 'nyy'),
    '133': ('Oakland Athletics', 'oak'),
    '143': ('Philadelphia Phillies', 'phi'),
    '134': ('Pittsburgh Pirates', 'pit'),
    '135': ('San Diego Padres', 'sd'),
    '136': ('Seattle Mariners', 'sea'),
    '137': ('San Francisco Giants', 'sf'),
    '138': ('St Louis Cardinals', 'stl'),
    '139': ('Tampa Bay Rays', 'tb'),
    '140': ('Texas Rangers', 'tex'),
    '141': ('Toronto Blue Jays', 'tor'),
    '120': ('Washington Nationals', 'was')
    }


def addon_log(string):
    if debug == 'true':
        xbmc.log("[MLBMC-%s]: %s" %(addon_version, string))


def getRequest(url, data=None, headers=None):
    if not xbmcvfs.exists(cookie_file):
        addon_log('Creating cookie_file!')
        cookie_jar.save()
    if headers is None:
        headers = {'User-agent' : 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:19.0) Gecko/20100101 Firefox/19.0',
                   'Referer' : 'http://www.mlb.com'}
    cookie_jar.load(cookie_file, ignore_discard=True, ignore_expires=True)
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookie_jar))
    urllib2.install_opener(opener)
    try:
        req = urllib2.Request(url,data,headers)
        response = urllib2.urlopen(req)
        data = response.read()
        cookie_jar.save(cookie_file, ignore_discard=True, ignore_expires=False)
        response.close()
        if debug == "true":
            addon_log("getRequest : %s" %url)
            addon_log(response.info())
            if response.geturl() != url:
                addon_log('Redirect URL: %s' %response.geturl())
        return data
    except urllib2.URLError, e:
        reason = None
        addon_log('We failed to open "%s".' %url)
        if hasattr(e, 'reason'):
            reason = str(e.reason)
            addon_log('We failed to reach a server.')
            addon_log('Reason: '+ reason)
        if hasattr(e, 'code'):
            reason = str(e.code)
            addon_log( 'We failed with error code - %s.' % reason )
            if 'highlights.xml' in url:
                return
        if reason:
            xbmc.executebuiltin("XBMC.Notification("+language(30015)+","+language(30019)+reason+",10000,"+icon+")")
        return


def getLengthInMinutes(length):
    l_split = length.split(':')
    minutes = int(l_split[-2])
    if int(l_split[-1]) >= 30:
        minutes += 1
    if len(l_split) >= 3:
        minutes += (int(l_split[-3]) * 60)
    if minutes < 1:
        minutes = 1
    return minutes


def addLink(name,url,duration,mode,iconimage,plot='',podcasts=False):
    u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)+"&podcasts="+str(podcasts)
    if addon_version.startswith('2'):
        if ':' in duration:
            duration = getLengthInMinutes(duration)
    liz=xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
    liz.setInfo( type="Video", infoLabels={ "Title": name, "duration": duration, "plot": plot } )
    liz.setProperty('IsPlayable', 'true')
    liz.setProperty( "Fanart_Image", fanart2 )
    ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz)
    return ok


def addDir(name,url,mode,iconimage,game_type=''):
    u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)
    if game_type != '':
        u+="&game_type="+urllib.quote_plus(game_type)
    ok=True
    liz=xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
    liz.setInfo( type="Video", infoLabels={ "Title": name } )
    liz.setProperty( "Fanart_Image", fanart )
    ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)
    return ok


def addGameDir(name,url,mode,iconimage):
    u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)
    ok=True
    liz=xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
    liz.setInfo( type="Video", infoLabels={ "Title": name } )
    liz.setProperty( "Fanart_Image", fanart2 )
    ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)
    return ok


def addPlaylist(name,url,mode,iconimage):
    u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)
    ok=True
    liz=xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
    liz.setInfo( type="Video", infoLabels={ "Title": name } )
    liz.setProperty( "Fanart_Image", fanart )
    ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz)
    return ok


def coloring( text , color , colorword ):
    if color == "white":
        color="FFFFFFFF"
    if color == "blue":
        color="FF0000FF"
    if color == "cyan":
        color="FF00B7EB"
    if color == "violet":
        color="FFEE82EE"
    if color == "pink":
        color="FFFF1493"
    if color == "red":
        color="FFFF0000"
    if color == "green":
        color="FF00FF00"
    if color == "lightgrey":
        color="D3D3D3D3"
    if color == "orange":
        color="FFFF8C00"
    colored_text = text.replace( colorword , "[COLOR=%s]%s[/COLOR]" % ( color , colorword ) )
    return colored_text


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