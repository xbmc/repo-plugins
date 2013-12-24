# -*- coding: utf-8 -*-
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
Jeuxvideo.com addon for XBMC
Authors:     gormux
"""

import os, re, xbmcplugin, xbmcgui, xbmcaddon, urllib, urllib2, sys, cookielib, pickle, datetime
import feedparser
import BeautifulSoup


"""
Class used as a C-struct to store video informations
"""
class videoInfo:
    pass

# Global variable definition
## Header for every log in this plugin
pluginLogHeader = "[XBMC_JVCOM] "

## Values for the mode parameter
MODE_LASTVIDS, MODE_PODCAST, MODE_LIVE, MODE_POD, MODE_LASTVIDS_ALL, MODE_LASTVIDS_PC, MODE_LASTVIDS_PS4, MODE_LASTVIDS_ONE, MODE_LASTVIDS_PS3, MODE_LASTVIDS_360, MODE_LASTVIDS_WIIU, MODE_LASTVIDS_WII, MODE_LASTVIDS_3DS, MODE_LASTVIDS_VITA, MODE_LASTVIDS_DS, MODE_LASTVIDS_PSP, MODE_LASTVIDS_IPHONE, MODE_LASTVIDS_ANDROID, MODE_LASTVIDS_WEB, MODE_GL_ALL, MODE_GL_PC, MODE_GL_PS4, MODE_GL_ONE, MODE_GL_PS3, MODE_GL_360, MODE_GL_WIIU, MODE_GL_WII, MODE_GL_3DS, MODE_GL_VITA, MODE_GL_DS, MODE_GL_PSP, MODE_GL_IPHONE, MODE_GL_ANDROID, MODE_GL_WEB, MODE_REPORTAGES, MODE_CHRONIQUES, MODE_USUL, MODE_CROSSED, MODE_DRAWINGAME, MODE_EXPINU, MODE_FOND, MODE_LFG, MODE_INDE, MODE_SPEED = range(44)

settings  = xbmcaddon.Addon(id='plugin.video.jvcom')
url       = 'http://www.jeuxvideo.com/jvxml.htm'
name      = 'JeuxVideo.com'
mode      = None
version   = settings.getAddonInfo('version')
useragent = "XBMC jvcom-plugin/" + version
language = settings.getLocalizedString
'''fanartimage = os.path.join(settings.getAddonInfo("path"), "fanart.jpg")'''

def remove_html_tags(data):
    """Permits to remove all HTML tags
        
    This function removes the differents HTML tags of a string
    """
    page = re.compile(r'<.*?>')
    return page.sub('', data)

def initialIndex():
    """Creates initial index
    
    Create the initial menu with the right identification values for the add-on to know which option have been selected
    """
    add_dir(unicode(language(30010)), 'http://http://www.jeuxvideo.com/jvxml.htm', MODE_LASTVIDS, '')
    add_dir(unicode(language(30011)), 'http://http://www.jeuxvideo.com/jvxml.htm', MODE_LIVE, '')
    add_dir(unicode(language(30013)), 'http://http://www.jeuxvideo.com/jvxml.htm', MODE_POD, '')

def indexLast():
    add_dir(unicode(language(30015)), 'http://www.jeuxvideo.com/rss/rss-videos.xml', MODE_LASTVIDS_ALL, '')
    add_dir(unicode(language(30016)), 'http://www.jeuxvideo.com/rss/rss-videos-pc.xml', MODE_LASTVIDS_PC, '')
    add_dir(unicode(language(30017)), 'http://www.jeuxvideo.com/rss/rss-videos-ps4.xml', MODE_LASTVIDS_PS4, '')
    add_dir(unicode(language(30018)), 'http://www.jeuxvideo.com/rss/rss-videos-xo.xml', MODE_LASTVIDS_ONE, '')
    add_dir(unicode(language(30019)), 'http://www.jeuxvideo.com/rss/rss-videos-ps3.xml', MODE_LASTVIDS_PS3, '')
    add_dir(unicode(language(30020)), 'http://www.jeuxvideo.com/rss/rss-videos-360.xml', MODE_LASTVIDS_360, '')
    add_dir(unicode(language(30021)), 'http://www.jeuxvideo.com/rss/rss-videos-wiiu.xml', MODE_LASTVIDS_WIIU, '')
    add_dir(unicode(language(30022)), 'http://www.jeuxvideo.com/rss/rss-videos-wii.xml', MODE_LASTVIDS_WII, '')
    add_dir(unicode(language(30023)), 'http://www.jeuxvideo.com/rss/rss-videos-3ds.xml', MODE_LASTVIDS_3DS, '')
    add_dir(unicode(language(30024)), 'http://www.jeuxvideo.com/rss/rss-videos-vita.xml', MODE_LASTVIDS_VITA, '')
    add_dir(unicode(language(30025)), 'http://www.jeuxvideo.com/rss/rss-videos-ds.xml', MODE_LASTVIDS_DS, '')
    add_dir(unicode(language(30026)), 'http://www.jeuxvideo.com/rss/rss-videos-psp.xml', MODE_LASTVIDS_PSP, '')
    add_dir(unicode(language(30027)), 'http://www.jeuxvideo.com/rss/rss-videos-iphone.xml', MODE_LASTVIDS_IPHONE, '')
    add_dir(unicode(language(30028)), 'http://www.jeuxvideo.com/rss/rss-videos-android.xml', MODE_LASTVIDS_ANDROID, '')
    add_dir(unicode(language(30029)), 'http://www.jeuxvideo.com/rss/rss-videos-wb.xml', MODE_LASTVIDS_WEB, '')

def indexGL():
    quality  = settings.getSetting( "quality" )
    if   quality == "720p" or quality == "2" or quality == "HQ" or quality == "1":
        add_dir(unicode(language(30015)), 'http://www.jeuxvideo.com/rss/itunes-hd.xml', MODE_GL_ALL, '')
        add_dir(unicode(language(30016)), 'http://www.jeuxvideo.com/rss/itunes-pc-hd.xml', MODE_GL_PC, '')
        add_dir(unicode(language(30017)), 'http://www.jeuxvideo.com/rss/itunes-ps4-hd.xml', MODE_GL_PS4, '')
        '''add_dir(unicode(language(30018)), '', MODE_GL_ONE, '')'''
        add_dir(unicode(language(30019)), 'http://www.jeuxvideo.com/rss/itunes-ps3-hd.xml', MODE_GL_PS3, '')
        add_dir(unicode(language(30020)), 'http://www.jeuxvideo.com/rss/itunes-360-hd.xml', MODE_GL_360, '')
        add_dir(unicode(language(30021)), 'http://www.jeuxvideo.com/rss/itunes-wiiu-hd.xml', MODE_GL_WIIU, '')
        add_dir(unicode(language(30022)), 'http://www.jeuxvideo.com/rss/itunes-wii-hd.xml', MODE_GL_WII, '')
        add_dir(unicode(language(30023)), 'http://www.jeuxvideo.com/rss/itunes-3ds-hd.xml', MODE_GL_3DS, '')
        add_dir(unicode(language(30024)), 'http://www.jeuxvideo.com/rss/itunes-vita-hd.xml', MODE_GL_VITA, '')
        add_dir(unicode(language(30025)), 'http://www.jeuxvideo.com/rss/itunes-ds-hd.xml', MODE_GL_DS, '')
        add_dir(unicode(language(30026)), 'http://www.jeuxvideo.com/rss/itunes-psp-hd.xml', MODE_GL_PSP, '')
        add_dir(unicode(language(30027)), 'http://www.jeuxvideo.com/rss/itunes-iphone-hd.xml', MODE_GL_IPHONE, '')
        add_dir(unicode(language(30028)), 'http://www.jeuxvideo.com/rss/itunes-android-hd.xml', MODE_GL_ANDROID, '')
        add_dir(unicode(language(30029)), 'http://www.jeuxvideo.com/rss/itunes-wb-hd.xml', MODE_GL_WEB, '')
    if quality == "LQ" or quality == "0":
        add_dir(unicode(language(30015)), 'http://www.jeuxvideo.com/rss/itunes.xml', MODE_GL_ALL, '')
        add_dir(unicode(language(30016)), 'http://www.jeuxvideo.com/rss/itunes-pc.xml', MODE_GL_PC, '')
        add_dir(unicode(language(30017)), 'http://www.jeuxvideo.com/rss/itunes-ps4.xml', MODE_GL_PS4, '')
        '''add_dir(unicode(language(30018)), '', MODE_GL_ONE, '')'''
        add_dir(unicode(language(30019)), 'http://www.jeuxvideo.com/rss/itunes-ps3.xml', MODE_GL_PS3, '')
        add_dir(unicode(language(30020)), 'http://www.jeuxvideo.com/rss/itunes-360.xml', MODE_GL_360, '')
        add_dir(unicode(language(30021)), 'http://www.jeuxvideo.com/rss/itunes-wiiu.xml', MODE_GL_WIIU, '')
        add_dir(unicode(language(30022)), 'http://www.jeuxvideo.com/rss/itunes-wii.xml', MODE_GL_WII, '')
        add_dir(unicode(language(30023)), 'http://www.jeuxvideo.com/rss/itunes-3ds.xml', MODE_GL_3DS, '')
        add_dir(unicode(language(30024)), 'http://www.jeuxvideo.com/rss/itunes-vita.xml', MODE_GL_VITA, '')
        add_dir(unicode(language(30025)), 'http://www.jeuxvideo.com/rss/itunes-ds.xml', MODE_GL_DS, '')
        add_dir(unicode(language(30026)), 'http://www.jeuxvideo.com/rss/itunes-psp.xml', MODE_GL_PSP, '')
        add_dir(unicode(language(30027)), 'http://www.jeuxvideo.com/rss/itunes-iphone.xml', MODE_GL_IPHONE, '')
        add_dir(unicode(language(30028)), 'http://www.jeuxvideo.com/rss/itunes-android.xml', MODE_GL_ANDROID, '')
        add_dir(unicode(language(30029)), 'http://www.jeuxvideo.com/rss/itunes-wb.xml', MODE_GL_WEB, '')

def indexPOD():
    quality  = settings.getSetting( "quality" )
    if   quality == "720p" or quality == "2" or quality == "HQ" or quality == "1":
        add_dir(unicode(language(30030)), 'http://www.jeuxvideo.com/rss/itunes_reportage-hd.xml', MODE_REPORTAGES, '')
        add_dir(unicode(language(30031)), 'http://www.jeuxvideo.com/rss/itunes-chroniques-hd.xml', MODE_CHRONIQUES, '')
        add_dir(unicode(language(30032)), 'http://www.jeuxvideo.com/rss/itunes-chroniques-hd-345.xml', MODE_USUL, '')
        add_dir(unicode(language(30033)), 'http://www.jeuxvideo.com/rss/itunes-chroniques-hd-436.xml', MODE_CROSSED, '')
        add_dir(unicode(language(30034)), 'http://www.jeuxvideo.com/rss/itunes-chroniques-hd-463.xml', MODE_DRAWINGAME, '')
        add_dir(unicode(language(30035)), 'http://www.jeuxvideo.com/rss/itunes-chroniques-hd-344.xml', MODE_EXPINU, '')
        add_dir(unicode(language(30036)), 'http://www.jeuxvideo.com/rss/itunes-chroniques-hd-442.xml', MODE_FOND, '')
        add_dir(unicode(language(30037)), 'http://www.jeuxvideo.com/rss/itunes-chroniques-hd-448.xml', MODE_LFG, '')
        add_dir(unicode(language(30038)), 'http://www.jeuxvideo.com/rss/itunes-chroniques-hd-354.xml', MODE_INDE, '')
        add_dir(unicode(language(30039)), 'http://www.jeuxvideo.com/rss/itunes-chroniques-hd-342.xml', MODE_SPEED, '')
    if quality == "LQ" or quality == "0":
        add_dir(unicode(language(30030)), 'http://www.jeuxvideo.com/rss/itunes_reportage.xml', MODE_REPORTAGES, '')
        add_dir(unicode(language(30031)), 'http://www.jeuxvideo.com/rss/itunes-chroniques.xml', MODE_CHRONIQUES, '')
        add_dir(unicode(language(30032)), 'http://www.jeuxvideo.com/rss/itunes-chroniques-345.xml', MODE_USUL, '')
        add_dir(unicode(language(30033)), 'http://www.jeuxvideo.com/rss/itunes-chroniques-436.xml', MODE_CROSSED, '')
        add_dir(unicode(language(30034)), 'http://www.jeuxvideo.com/rss/itunes-chroniques-463.xml', MODE_DRAWINGAME, '')
        add_dir(unicode(language(30035)), 'http://www.jeuxvideo.com/rss/itunes-chroniques-344.xml', MODE_EXPINU, '')
        add_dir(unicode(language(30037)), 'http://www.jeuxvideo.com/rss/itunes-chroniques-442.xml', MODE_FOND, '')
        add_dir(unicode(language(30036)), 'http://www.jeuxvideo.com/rss/itunes-chroniques-448.xml', MODE_LFG, '')
        add_dir(unicode(language(30037)), 'http://www.jeuxvideo.com/rss/itunes-chroniques-354.xml', MODE_INDE, '')
        add_dir(unicode(language(30038)), 'http://www.jeuxvideo.com/rss/itunes-chroniques-342.xml', MODE_SPEED, '')

def playvideo(requestHandler, video):
    """
    Plays video
    """
    requestHandler.addheaders = [("User-agent", useragent)]
    page = requestHandler.open(_video)
    url  = page.geturl()
    xbmc.log(msg=pluginLogHeader + "URL :" + url,level=xbmc.LOGDEBUG)
    listitem   = xbmcgui.ListItem( label='', 
                                   iconImage='', 
                                   thumbnailImage='', 
                                   path=url )

    xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, listitem)
    if autorefresh == "true":
        xbmc.executebuiltin("Container.Refresh")

def indexVideos(url):
    videos=[]
    feed = feedparser.parse(url)
    for e in feed['entries']:
        for item in e['links']:
            if 'video' in item['type']:
                link=item['href']
            else:
                link=''
        videos.append([ link,
                        e['subtitle'],
                        e['subtitle'],
                        0,
                        0,
                        ''])
    for video in videos:
        addlink(video[1],
                video[0],
                video[5],
                video[3],
                video[4] )

def indexLastVideos(url):
    videos=[]
    quality  = settings.getSetting( "quality" )
    feed = feedparser.parse(url)
    for e in feed['entries']:
        page = requestHandler.open(e['id'])
        soup = BeautifulSoup.BeautifulSoup(page.read())
        video = {}
        for cd in soup.findAll(text=True):
            if 'CDATA' in cd:
                if 'video_callback' in cd:
                    for i in cd.split('"'):
                        if '720p.mp4' in i:
                            video['720p'] = i
                        if 'high.mp4' in i:
                            video['high'] = i
                        if 'low.mp4' in i:
                            video['low'] = i
        try:                    
            if   quality == "720p" or quality == "2":
                link = video['720p']
            if quality == "HQ" or quality == "1":
                link = video['high']
            if quality == "LQ" or quality == "0":
                link = video['low']
        except:
            continue

        videos.append([ link,
                        e['title'],
                        e['title'],
                        0,
                        0,
                        ''])
    for video in videos:
        addlink(video[1],
                video[0],
                video[5],
                video[3],
                video[4] )

def get_params():
    """
    Get parameters
    """
    param       = []
    paramstring = sys.argv[2]

    if len(paramstring) >= 2:
        params        = sys.argv[2]
        cleanedparams = params.replace('?','')

        if (params[len(params)-1] == '/'):
            params = params[0:len(params)-2]

        pairsofparams = cleanedparams.split('&')
        param = {}

        for i in range(len(pairsofparams)):
            splitparams = {}
            splitparams = pairsofparams[i].split('=')
            if (len(splitparams)) == 2:
                param[splitparams[0]] = splitparams[1]
    return param

def addlink(name, url, iconimage, duration, bool_seen):
    """
    Add a link to a directory, for playable elements
    """
    ok  = True
    liz = xbmcgui.ListItem(name, 
                           iconImage="DefaultFolder.png", 
                           thumbnailImage=iconimage)
    liz.setInfo( 
                 type="Video", 
                 infoLabels={ "title": name, 
                              "playcount": int(bool_seen) } 
               )
    liz.addStreamInfo("video", { 'duration':duration })
    liz.setProperty("IsPlayable","true")
    ok  = xbmcplugin.addDirectoryItem( handle=int(sys.argv[1]), 
                                       url=url, 
                                       listitem=liz, 
                                       isFolder=False )
    return ok


def add_dir(name, url, mode, iconimage):
    """
    Adds a directory to the list
    """
    ok  = True
    print 'loop in adddir'
    
    # Hack to avoid incompatiblity of urllib with unicode string
    if isinstance(name, str):
        url = sys.argv[0]+"?url="+urllib.quote_plus(url)+\
            "&mode="+str(mode)+"&name="+urllib.quote_plus(name)
    else:
        url = sys.argv[0]+"?url="+urllib.quote_plus(url)+\
        "&mode="+str(mode)+"&name="+urllib.quote_plus(name.encode("ascii", "ignore"))
    showid = url.split('?')[1].split('&')[0].split('=')[1]
    thumbnailimage = os.path.join(settings.getAddonInfo("path"), 'resources', 'images', showid + '.jpeg')
    if not iconimage == '':
        liz = xbmcgui.ListItem(name,
                               iconImage=iconimage,
                               thumbnailImage=iconimage)
    else:
        liz = xbmcgui.ListItem(name,
                               iconImage=thumbnailimage,
                               thumbnailImage=thumbnailimage)

    liz.setInfo( 
                 type="Video", 
                 infoLabels={ "Title": name } 
               )
    #liz.setProperty('fanart_image', fanartimage)
    ok  = xbmcplugin.addDirectoryItem( handle=int(sys.argv[1]), 
                                       url=url, 
                                       listitem=liz, 
                                       isFolder=True )
    return ok

## Start of the add-on
xbmc.log(msg=pluginLogHeader + "-----------------------",level=xbmc.LOGDEBUG)
xbmc.log(msg=pluginLogHeader + "JVCOM plugin main loop",level=xbmc.LOGDEBUG)
pluginHandle = int(sys.argv[1])

## Reading parameters given to the add-on
params = get_params()
xbmc.log(msg=pluginLogHeader + "Parameters read",level=xbmc.LOGDEBUG)

try:
    url = urllib.unquote_plus(params["url"])
except:
    pass
try:
    mode = int(params["mode"])
except:
    pass
try:
    _id = int(params["id"])
except:
    _id = 0

xbmc.log(msg=pluginLogHeader + "requested mode : " + str(mode),level=xbmc.LOGDEBUG)
xbmc.log(msg=pluginLogHeader + "requested url : " + url,level=xbmc.LOGDEBUG)
xbmc.log(msg=pluginLogHeader + "requested id : " + str(_id),level=xbmc.LOGDEBUG)

# Starting request handler
cj = cookielib.LWPCookieJar()
requestHandler = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))

# Determining and executing action
if( mode == None or url == None or len(url) < 1 ) and _id == 0:
    xbmc.log(msg=pluginLogHeader + "Loading initial index",level=xbmc.LOGDEBUG)
    initialIndex()
elif mode == MODE_LASTVIDS and _id == 0:
    xbmc.log(msg=pluginLogHeader + "Getting categories in last videos",level=xbmc.LOGDEBUG)
    indexLast()
elif mode in [MODE_GL_ALL, MODE_GL_PC, MODE_GL_PS4, MODE_GL_ONE, MODE_GL_PS3, MODE_GL_360, MODE_GL_WIIU, MODE_GL_WII, MODE_GL_3DS, MODE_GL_VITA, MODE_GL_DS, MODE_GL_PSP, MODE_GL_IPHONE, MODE_GL_ANDROID, MODE_GL_WEB] and _id == 0:
    xbmc.log(msg=pluginLogHeader + "Getting Gaming Live",level=xbmc.LOGDEBUG)
    indexVideos(url)
elif mode in [MODE_LASTVIDS_ALL, MODE_LASTVIDS_PC, MODE_LASTVIDS_PS4, MODE_LASTVIDS_ONE, MODE_LASTVIDS_PS3, MODE_LASTVIDS_360, MODE_LASTVIDS_WIIU, MODE_LASTVIDS_WII, MODE_LASTVIDS_3DS, MODE_LASTVIDS_VITA, MODE_LASTVIDS_DS, MODE_LASTVIDS_PSP, MODE_LASTVIDS_IPHONE, MODE_LASTVIDS_ANDROID, MODE_LASTVIDS_WEB] and _id == 0:
    xbmc.log(msg=pluginLogHeader + "Getting last videos",level=xbmc.LOGDEBUG)
    indexLastVideos(url)
elif mode in [MODE_REPORTAGES, MODE_CHRONIQUES, MODE_USUL, MODE_CROSSED, MODE_DRAWINGAME, MODE_EXPINU, MODE_FOND, MODE_LFG, MODE_INDE, MODE_SPEED] and _id == 0:
    xbmc.log(msg=pluginLogHeader + "Getting Podcasts",level=xbmc.LOGDEBUG)
    indexVideos(url)
    #elif mode == MODE_PODCAST and _id == 0:
    #    xbmc.log(msg=pluginLogHeader + "Retrieving shows categories",level=xbmc.LOGDEBUG)
    #    indexLast()
elif mode == MODE_POD and _id == 0:
    indexPOD()
elif mode == MODE_LIVE and _id == 0:
    indexGL()
elif _id > 0:
    xbmc.log(msg=pluginLogHeader + "Trying to play video id : " + str(_id),level=xbmc.LOGDEBUG)
    playvideo(requestHandler);

xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_NONE)
xbmcplugin.endOfDirectory(int(sys.argv[1]), cacheToDisc=True)
