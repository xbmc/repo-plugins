import xbmcgui
import xbmcplugin
import os
import xbmcaddon
import urllib2
import re
import calendar
import datetime

addon = xbmcaddon.Addon(id='plugin.image.dilbert')
thisPlugin = int(sys.argv [1])
u1='http://www.dilbert.com'
today=datetime.datetime.today()
oneday=datetime.timedelta(1)
day=today
req = urllib2.Request(u1)
req.add_header('User-Agent', ' Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
response = urllib2.urlopen(req)
page=response.read()
response.close()
match=re.compile('(.dyn.str_strip.*strip.*.zoom.gif)').findall(page)
lastu=''
for link in match:
    u='http://dilbert.com/'+link
    print(u)
    name='Today Dilbert'
    iconimage=os.path.join(addon.getAddonInfo('path'),"icon.png")
    liz=xbmcgui.ListItem(unicode(name), iconImage=iconimage,thumbnailImage=iconimage)
    liz.setInfo( type="Image", infoLabels={ "Title": name })
    xbmcplugin.addDirectoryItem(handle=thisPlugin,url=u,listitem=liz,isFolder=False)
    lastu=u
del req
cachedir=os.path.join(addon.getAddonInfo('path'),'cache')
if  not os.path.exists(cachedir):
    os.makedirs(cachedir)
    print('Created cached directory '+cachedir)
# n= number of entries added to the menu
n=0
# i= number of entries actually read from the network (not cached)
i=0
while i < 5 or n <10:
    p=os.path.join(cachedir,day.strftime('%Y-%m-%d')+'.link')
    if os.path.isfile(p):
        print('reading cache')
        text_file = open(p, "r")
        u=text_file.read()
        text_file.close()
        name=day.strftime('%Y-%m-%d')+' Dilbert'
        iconimage=os.path.join(addon.getAddonInfo('path'),"icon.png")
        liz=xbmcgui.ListItem(unicode(name), iconImage=iconimage,thumbnailImage=iconimage)
        liz.setInfo( type="Image", infoLabels={ "Title": name })
        xbmcplugin.addDirectoryItem(handle=thisPlugin,url=u,listitem=liz,isFolder=False)
        n=n+1
    else:
        req = urllib2.Request(u1+'/'+day.strftime('%Y-%m-%d')+'/')
        req.add_header('User-Agent', ' Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
        response = urllib2.urlopen(req)
        page=response.read()
        response.close()
        match=re.compile('(.dyn.str_strip.*strip.*.zoom.gif)').findall(page)
        for link in match:
            u='http://dilbert.com/'+link
            if u != lastu:
                print(u)
                name=day.strftime('%Y-%m-%d')+' Dilbert'
                iconimage=os.path.join(addon.getAddonInfo('path'),"icon.png")
                liz=xbmcgui.ListItem(unicode(name), iconImage=iconimage,thumbnailImage=iconimage)
                liz.setInfo( type="Image", infoLabels={ "Title": name })
                xbmcplugin.addDirectoryItem(handle=thisPlugin,url=u,listitem=liz,isFolder=False)
                n=n+1
                if not os.path.isfile(p):
                    print('writing cache '+p)
                    text_file = open(p, "w")
                    text_file.write(u)
                    text_file.close()
            lastu=u
        i=i+1
    day=day-oneday
xbmcplugin.endOfDirectory(handle=thisPlugin, succeeded=True, updateListing=False, cacheToDisc=True)
