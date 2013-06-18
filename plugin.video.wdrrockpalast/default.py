#!/usr/bin/python
# -*- coding: utf8 -*-

""" 
WDR Rockpalast
Copyright (C) 2012 Xycl

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see <http://www.gnu.org/licenses/>.



Paths used by WDR Rockpalast

New:
rtmp://gffstream.fcod.llnwd.net:443/a792
<playpath>mp4:e2/tv/rockpalast/live/2010/airbourne 
<swfUrl>http://www.wdr.de/themen/global/flashplayer/wsPlayer.swf 
<pageUrl>http://www.wdr.de/tv/rockpalast/extra/videos/2010/0322/airbourne.jsp

Old:
rtmp://gffstream.fcod.llnwd.net/a792/e2/tv/rockpalast/live/2010/airbourne.mp4
"""


# os imports
import urllib, urllib2, re, os
# xbmc imports
import xbmcplugin, xbmcgui, xbmc
from HTMLParser import HTMLParser

        
def smart_unicode(s):
    """credit : sfaxman"""
    if not s:
        return ''
    try:
        if not isinstance(s, basestring):
            if hasattr(s, '__unicode__'):
                s = unicode(s)
            else:
                s = unicode(str(s), 'UTF-8')
        elif not isinstance(s, unicode):
            s = unicode(s, 'UTF-8')
    except:
        if not isinstance(s, basestring):
            if hasattr(s, '__unicode__'):
                s = unicode(s)
            else:
                s = unicode(str(s), 'ISO-8859-1')
        elif not isinstance(s, unicode):
            s = unicode(s, 'ISO-8859-1')
    return s


def smart_utf8(s):
    return smart_unicode(s).encode('utf-8')

    
def log(msg, level=xbmc.LOGDEBUG):

    if type(msg).__name__=='unicode':
        msg = msg.encode('utf-8')

    filename = smart_utf8(os.path.basename(sys._getframe(1).f_code.co_filename))
    lineno  = str(sys._getframe(1).f_lineno)

    try:
        module = "function " + sys._getframe(1).f_code.co_name
    except:
        module = " "

    xbmc.log(str("[%s] line %5d in %s %s >> %s"%("plugin.video.wdrrockpalast", int(lineno), filename, module, msg.__str__())), level)   
    
    
def show_concerts():
    req = urllib2.Request('http://www.wdr.de/tv/rockpalast/videos/uebersicht.jsp')
    req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
    response = urllib2.urlopen(req)
    link=response.read()
    response.close()
    match=re.compile('<li><a href="([^"]+)">(.*?)</a></li>').findall(link)

    for url,name in match:
        name = name.decode('ISO-8859-1').encode('utf-8')
        log("Found concert %s"%name)
        add_dir(HTMLParser().unescape(name), 'HTTP://www.wdr.de'+url, 1, 'HTTP://www.wdr.de/tv/rockpalast/codebase/img/audioplayerbild_512x288.jpg')
            
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_VIDEO_TITLE)
    xbmcplugin.endOfDirectory(int(sys.argv[1]))


def play_video(from_url, name):
    # load page containing the video
    req = urllib2.Request(from_url)
    req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
    response = urllib2.urlopen(req)
    video_page=response.read()
    response.close()

    # find video url
    video_url=re.compile('dslSrc=([^&]+?)&amp;').findall(video_page)
    org_video_url = urllib.unquote_plus(video_url[0])

    # find the rtmp parameters
    match=re.compile('([\w+]*?://[^/]*?)/([^/]*?)/(.*)').findall(org_video_url)
    host, path, playpath_from_url = match[0]
    playpath, extension = os.path.splitext(playpath_from_url)

    # build complete path
    rtmp_path = host + ":443/" + path +" playpath="+ extension[1:] + ":" + playpath + " swfUrl=http://www.wdr.de/themen/global/flashplayer/wsPlayer.swf pageUrl=" + from_url

    if len(name)>2:
        title = name
    else:
        title_url=re.compile('<title>(.+?)- Rockpalast').findall(video_page)
        
        try:
            title = urllib.unquote_plus(title_url[0])
        except:
            title = 'unnamed'

    log("Playing %s"%title)
    log("URL = %s"%rtmp_path)
    listitem = xbmcgui.ListItem(title, iconImage="DefaultFolder.png", thumbnailImage='HTTP://www.wdr.de/tv/rockpalast/codebase/img/audioplayerbild_512x288.jpg')
    listitem.setInfo('video', {'Title': title})
    xbmc.Player(xbmc.PLAYER_CORE_AUTO).play( rtmp_path, listitem)       
        

def get_params():
    """ extract params from argv[2] to make a dict (key=value) """
    param_dict = {}
    try:
        if sys.argv[2]:
            param_pairs=sys.argv[2][1:].split( "&" )
            for params_pair in param_pairs:
                param_splits = params_pair.split('=')
                if (len(param_splits))==2:
                    param_dict[urllib.unquote_plus(param_splits[0])] = urllib.unquote_plus(param_splits[1])
    except:
        pass
    return param_dict


def add_dir(name, url, mode, iconimage):
    u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)
    ok=True
    liz=xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
    liz.setInfo( type="Video", infoLabels={ "Title": name } )
    ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=False)
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


if mode==None or url==None or len(url)<1:
    show_concerts()
       
elif mode==1:
    play_video(url, name)


