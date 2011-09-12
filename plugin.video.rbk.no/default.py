#/*
# *      Copyright (C) 2010 Arne Morten Kvarving
# *
# *
# *  This Program is free software; you can redistribute it and/or modify
# *  it under the terms of the GNU General Public License as published by
# *  the Free Software Foundation; either version 2, or (at your option)
# *  any later version.
# *
# *  This Program is distributed in the hope that it will be useful,
# *  but WITHOUT ANY WARRANTY; without even the implied warranty of
# *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# *  GNU General Public License for more details.
# *
# *  You should have received a copy of the GNU General Public License
# *  along with this program; see the file COPYING.  If not, write to
# *  the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.
# *  http://www.gnu.org/copyleft/gpl.html
# *
# */

import urllib2,re,xbmcaddon,string,xbmc,xbmcgui,xbmcplugin
from BeautifulSoup import BeautifulSoup as BS

def INDEX(start):
        req = urllib2.Request('http://www.rbk.no/index.jsp?stats=nyhetsarkiv&start='+start)
        response = urllib2.urlopen(req)
        link=response.read()
        response.close()
        link = string.split(link,'<h1>Nyhetsarkiv</h1>')
        link = string.split(link[1],'<a href="index.jsp?stats=nyhetsarkiv&start=')
        match=re.compile('(http://www.rbk.no/incoming/article[0-9]+\.ece)').findall(link[0])
        for article in match:
                req2 = urllib2.Request(article)
                response = urllib2.urlopen(req2)
                link = response.read()
                response.close()
                name = re.compile('<h1>(.*)</h1>').findall(link)
                plot = re.compile('p class="leadIn"><b>(?:<p>)?([^<]*)(?:</p>)?</b>').findall(link)
                date = re.compile('Publisert: ([^ ]+)').findall(link)
                id = re.compile('TV2Player.insert\(([0-9]+)').findall(link)
                if len(id) == 0:
                        # utub it is then?
                        id = re.compile('youtube.com/embed/([^?"]+)(?:\?|")').findall(link)
                        for i in id:
                                try:
                                        thumb = re.compile('<div class="image">[^>]*src="([^"]*)"').findall(link)[0]
                                except:
                                        thumb=''
                                        pass
                                url = 'plugin://plugin.video.youtube/?action=play_video&videoid='+i
                                addLink(name[0],url,thumb,plot[0],date[0])
                else:
                        for i in id:
                                url = sys.argv[0]+"?id="+i
                                thumb = 'http://www.tv2.no/tvid/VMan-P'+i[:3]+'/VMan-P'+i+'.jpg'
                                addLink(name[0],url,thumb,plot[0],date[0])

def RESOLVE(id):
        url = 'http://webtv.tv2.no/embed/metafile.asx?p='+id+'&i=0&external=0&ads=true&bw=2000'
        req3 = urllib2.Request(url)
        response = urllib2.urlopen(req3)
        link = response.read()
        response.close()
        url = re.compile('<REF HREF="(.*?)">').findall(link)
        name = re.compile('<TITLE>(.+?)</TITLE>').findall(link)
        plot = re.compile('<ABSTRACT>(.+?)</ABSTRACT>').findall(link)
        try:
                plot = plot[1];
        except:
                plot = "";
                pass
        try:
                name = name[0];
        except:
                name = "";
                pass

        thumb = 'http://www.tv2.no/tvid/VMan-P'+id[:3]+'/VMan-P'+id+'.jpg'
        resolveLink(url[0],name,thumb,plot)
                
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

def addLink(name,url,iconimage,plot,date):
        ok=True
        name=str(BS(name,convertEntities=BS.HTML_ENTITIES,fromEncoding='utf-8'))
        plot=str(BS(plot,convertEntities=BS.HTML_ENTITIES,fromEncoding='utf-8'))
        liz=xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
        liz.setInfo( type="Video", infoLabels={ "Title": name } )
        liz.setInfo( type="Video", infoLabels={ "Plot": plot} )
        liz.setInfo( type="Video", infoLabels={ "Date": date} )
        liz.setProperty("IsPlayable","true");
        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=url,listitem=liz,isFolder=False)
        return ok

def resolveLink(url,name,thumb,plot):
        li=xbmcgui.ListItem(name,
                            path = url,
                            thumbnailImage=thumb)
        li.setInfo( type="Video", infoLabels={ "Title": name } )
        li.setInfo( type="Video", infoLabels={ "Plot": plot} )
        xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, li)
        return True

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

def addDir(name,start,iconimage):
        u=sys.argv[0]+"?start="+start
        liz=xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
        liz.setInfo( type="Video", infoLabels={ "Title": name } )
        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)
        return ok

__settings__ = xbmcaddon.Addon(id='plugin.video.rbk.no')
__language__ = __settings__.getLocalizedString
params=get_params()
try:
        start = params["start"]
except:
        start = "0";
        pass
try:
        id = params["id"]
except:
        id = "0";
        pass

iid = int(id);
if iid > 0:
        RESOLVE(id)
else:
        INDEX(start)
        istart = int(start);
        if istart > 0:
                addDir(__language__(30001),str(istart-25),'')
        addDir(__language__(30000),str(istart+25),'')
        xbmcplugin.addSortMethod(int(sys.argv[1]),xbmcplugin.SORT_METHOD_DATE)
        xbmcplugin.endOfDirectory(int(sys.argv[1]))

