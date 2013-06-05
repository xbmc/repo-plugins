import xbmcgui
import xbmcplugin
import os
import xbmcaddon
import urllib2
import re
import calendar
import datetime

addon = xbmcaddon.Addon(id='plugin.image.garfield')
thisPlugin = int(sys.argv [1])
u1='http://www.gocomics.com/garfield/'
today=datetime.datetime.today()
oneday=datetime.timedelta(1)
day=today
req = urllib2.Request(u1)
req.add_header('User-Agent', ' Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
response = urllib2.urlopen(req)
page=response.read()
response.close()
match=re.compile('meta property=.og:image. content=.(http://assets.amuniversal.com/[0-9a-f]+)').findall(page)
lastu=''
for link in match:
    print(link)
    name='Today Garfield'
    iconimage=os.path.join(addon.getAddonInfo('path'),"icon.png")
    liz=xbmcgui.ListItem(unicode(name), iconImage=iconimage,thumbnailImage=iconimage)
    liz.setInfo( type="Image", infoLabels={ "Title": name })
    xbmcplugin.addDirectoryItem(handle=thisPlugin,url=link,listitem=liz,isFolder=False)
    lastu=link
del req
i=0
while i < 7:
    req = urllib2.Request(u1+'/'+day.strftime('%Y/%m/%d')+'/')
    req.add_header('User-Agent', ' Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
    response = urllib2.urlopen(req)
    page=response.read()
    response.close()
    match=re.compile('meta property=.og:image. content=.(http://assets.amuniversal.com/[0-9a-f]+)').findall(page)
    for link in match:
        if link != lastu:
            print(link)
            name=day.strftime('%Y-%m-%d')+' Garfield'
            iconimage=os.path.join(addon.getAddonInfo('path'),"icon.png")
            liz=xbmcgui.ListItem(unicode(name), iconImage=iconimage,thumbnailImage=iconimage)
            liz.setInfo( type="Image", infoLabels={ "Title": name })
            xbmcplugin.addDirectoryItem(handle=thisPlugin,url=link,listitem=liz,isFolder=False)
        lastu=link
    day=day-oneday
    i=i+1
xbmcplugin.endOfDirectory(handle=thisPlugin, succeeded=True, updateListing=False, cacheToDisc=True)
