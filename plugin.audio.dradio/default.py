# -*- coding: utf-8 -*-

#  Copyright 2012 escoand
#
#  This file is part of the dradio.de xbmc plugin.
#
#  This plugin is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This plugin is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this plugin.  If not, see <http://www.gnu.org/licenses/>.


import urllib, urllib2, re, os, sys
import xbmcaddon, xbmcplugin, xbmcgui, xbmc


def STATIONS():
    #addDir("Beide Programme", 'http://www.dradio.de/aod/html/?station=0', 1, '')
    addDir("Deutschlandfunk", 'http://www.dradio.de/aod/html/?station=1', 1, 'http://www.dradio.de/picts/dfunk.gif')
    addDir("Deutschlandradio Kultur", 'http://www.dradio.de/aod/html/?station=3', 1, 'http://www.dradio.de/picts/dkultur.gif')


def BROADCASTS(url):
	link = get_url(url)
	brs = re.compile('<strong[^>]*><span[^>]*>([^<]+)</span></strong>.*?<a [^>]*href="([^"]+)"[^>]*>Nachh.ren</a>', re.DOTALL).findall(link)
	for name, url in brs:
		addDir(name, url, 2, '')


def CATEGORIES(url):
    link = get_url(url)
    entries = re.compile('<ul class="p05">(.*?)</ul>', re.DOTALL).findall(link)
    for entry in entries:
        days = re.compile('<li><a [^>]*href="([^"]+)"[^>]*>(heute|[^<]*gestern)</a></li>').findall(entry)
        for url, day in days:
            addDir('Beiträge ' + day, url, 2, '')
    entries = re.compile('<a [^>]*href="([^"]+)"[^>]*>.*?Sendungen A-Z.*?</a>').findall(link)
    #for url in entries:
    #	url = re.sub('\?.*', '?select=all', url)
    #	addDir('Sendungen von A bis Z', url, 3, '')
    addDir('Sendungen von A bis Z', 'http://www.dradio.de/dlf/sendungen/?select=all', 3, '')


def INDEX(url):
    link = get_url(url)
    entries = re.compile('<div class="suchergebnis">(.*?)</div>', re.DOTALL).findall(link)
    for entry in entries:
        match = re.compile('<p>Sendezeit: (.*)</p>').findall(entry)
        for date in match:
            name = date + " - "
        match = re.compile('<a [^>]*href="([^"]+\.mp3)"[^>]*>(.*)</a>').findall(entry)
        for url, title in match:
            title = re.sub('<[^>]+>', '', title)
            title = re.sub('^[0-9]+\.&nbsp;', '', title)
            addLink(name + title, url, '')
    match = re.compile('<a [^>]*href="([^"]+)"[^>]*>vor</a>').findall(link)
    for url in match:
        addDir('weitere Beiträge ...', url, 2, '')
        #INDEX(url)
    entries = re.compile('<ul class="p05">(.*?)</ul>', re.DOTALL).findall(link)
    for entry in entries:
        days = re.compile('<li><a [^>]*href="([^"]+)"[^>]*>([^<]+ Tag)</a></li>').findall(entry)
        for url, day in days:
            addDir(day + ' ...', url, 2, '')


def get_params():
    param = []
    paramstring = sys.argv[2]
    if len(paramstring) >= 2:
        params = sys.argv[2]
        cleanedparams = params.replace('?','')
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


def get_url(url):
    if url.startswith('/'):
    	url='http://www.dradio.de/'+url
    headers = {'User-agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:6.0) Gecko/20100101 Firefox/6.0'}
    print url
    req = urllib2.Request(url, None, headers)
    response = urllib2.urlopen(req)
    link = response.read()
    response.close()
    return link


def addLink(name,url,iconimage):
    ok=True
    liz=xbmcgui.ListItem(name, iconImage="DefaultAudio.png", thumbnailImage=iconimage)
    liz.setInfo( type="Video", infoLabels={ "Title": name } )
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
    STATIONS()

elif mode == 1:
    print ""+url
    CATEGORIES(url)

elif mode == 2:
    print ""+url
    INDEX(url)

elif mode == 3:
    print ""+url
    BROADCASTS(url)


xbmcplugin.endOfDirectory(int(sys.argv[1]))
