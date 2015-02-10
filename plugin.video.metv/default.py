# -*- coding: utf-8 -*-
# MeTV XBMC Addon

import sys
import httplib

import urllib, urllib2, cookielib, datetime, time, re, os, string
import xbmcplugin, xbmcgui, xbmcaddon, xbmcvfs, xbmc
import cgi, gzip
from StringIO import StringIO



USER_AGENT = 'Mozilla/5.0 (iPad; CPU OS 6_0 like Mac OS X) AppleWebKit/536.26 (KHTML, like Gecko) Version/6.0 Mobile/10A5376e Safari/8536.25'
GENRE_TV  = "TV"
UTF8          = 'utf-8'
METVBASE = 'http://metvnetwork.com%s'

addon         = xbmcaddon.Addon('plugin.video.metv')
__addonname__ = addon.getAddonInfo('name')
__language__  = addon.getLocalizedString


home          = addon.getAddonInfo('path').decode(UTF8)
icon          = xbmc.translatePath(os.path.join(home, 'icon.png'))
addonfanart   = xbmc.translatePath(os.path.join(home, 'fanart.jpg'))


def log(txt):
    message = '%s: %s' % (__addonname__, txt.encode('ascii', 'ignore'))
    xbmc.log(msg=message, level=xbmc.LOGDEBUG)

def cleanfilename(name):    
    valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
    return ''.join(c for c in name if c in valid_chars)

def demunge(munge):
        try:
            munge = urllib.unquote_plus(munge).decode(UTF8)
        except:
            pass
        return munge

def getRequest(url, user_data=None, headers = {'User-Agent':USER_AGENT, 'Accept':"text/html", 'Accept-Encoding':'gzip,deflate,sdch', 'Accept-Language':'en-US,en;q=0.8'}  ):
              log("getRequest URL:"+str(url))
              req = urllib2.Request(url.encode(UTF8), user_data, headers)

              try:
                 response = urllib2.urlopen(req)
                 if response.info().getheader('Content-Encoding') == 'gzip':
                    log("Content Encoding == gzip")
                    buf = StringIO( response.read())
                    f = gzip.GzipFile(fileobj=buf)
                    link1 = f.read()
                 else:
                    link1=response.read()
              except:
                 link1 = ""

              if not (str(url).endswith('.zip')):
                 link1 = str(link1).replace('\n','')
              return(link1)


def getSources(fanart):
              urlbase   = METVBASE % ('/videos/')
              pg = getRequest(urlbase)
              blob = re.search('<div class="video-library-list clearfix">(.+?)video-library-list -->',pg).group(1)
              cats = re.findall('href="(.+?)".+?src="(.+?)".+?<h2>(.+?)<', blob)
              for caturl, catimage, catname in cats:
                  pg = getRequest(METVBASE % (caturl))
                  try:
                     (cathead,catsyn)=re.search('<span class="new-episodes">(.+?)<.+?"video-landing-main-desc-wrap clearfix".+?-->(.+?)<',pg).groups()
                     catdesc = '%s \n %s' % (cathead.strip(), catsyn.strip())
                  except:
                     catdesc = re.search('"video-landing-main-desc-wrap clearfix".+?-->(.+?)<',pg).group(1).strip()
                  addDir(catname,caturl,'GC',catimage,fanart,catdesc,GENRE_TV,'',False)

def getCats(cat_url):
              urlbase   = METVBASE % (cat_url)
              pg = getRequest(urlbase)
              try:
                series = re.search('class="new-episodes">.+?<h2>(.+?)</h2>',pg).group(1)
              except:
                series = 'MeTV'
              showart = METVBASE % (re.search('<img class="video-landing-billboard" src="(.+?)"',pg).group(1))
              blob = re.search('<div class="video-landing-episodes-wrap clearfix">(.+?)video-landing-episodes-wrap -->',pg).group(1)
              shows = re.findall('episode-title"><a href="(.+?)">(.+?)<.+?thumb-img" src="(.+?)".+?episode-desc">(.+?)<',blob)
              for showpage,showname, showimg, showdesc in shows:
                 showname = '%s - %s' % (series, showname)
                 showdesc = showdesc.replace('</span>','')
                 try:
                   showurl = re.search('/media/(.+?)/',showimg).group(1)
                 except:
                   showurl = 'BADASS'+showpage
                 showurl = "%s?url=%s&name=%s&mode=GS" %(sys.argv[0], urllib.quote_plus(showurl), urllib.quote_plus(showname))
                 addLink(showurl.encode(UTF8),showname,showimg,showart,showdesc,GENRE_TV,'')


def getUrl(mediaID):
            if mediaID.startswith('BADASS'):
              mediaID = METVBASE % mediaID.replace('BADASS','')
              pg = getRequest(mediaID)
              mediaID = re.search('mediaId=(.+?)&',pg).group(1)
            in0 = '<tns:in0>%s</tns:in0>' % mediaID
            in1 = '<tns:in1 xsi:nil="true" />'
            SoapMessage = """<SOAP-ENV:Envelope xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"><SOAP-ENV:Body><tns:getPlaylistByMediaId xmlns:tns="http://service.data.media.pluggd.com">"""+in0+in1+"""</tns:getPlaylistByMediaId></SOAP-ENV:Body></SOAP-ENV:Envelope>"""
            html = getRequest("http://ps2.delvenetworks.com/PlaylistService", 
                               user_data = SoapMessage, 
                               headers={ "Host": "ps2.delvenetworks.com", 
                               "User-Agent":"Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10.6; en-US; rv:1.9.2.10) Gecko/20100914 Firefox/3.6.10",
                               "Content-type": "text/xml; charset=\"UTF-8\"", "Content-length": "%d" % len(SoapMessage), 
                               "Referer": "http://static.delvenetworks.com/deployments/player/player-3.27.1.0.swf?playerForm=Chromeless", 
                               "X-Page-URL": "http://metvnetwork.com/video/", "SOAPAction": "\"\""})
            streams = re.findall('<Stream>(.+?)</Stream>',html)
            show_url=''
            highbitrate = float(0)
            for stream in streams:
               (url, bitrate) = re.search('<url>(.+?)</u.+?<videoBitRate>(.+?)</v',stream).groups()
               if (float(bitrate)) > highbitrate:
                  show_url = url
                  highbitrate = float(bitrate)
            show_url  = show_url.split('mp4:',1)[1]
            finalurl  = 'http://s2.cpl.delvenetworks.com/%s' % show_url
            return finalurl

def getShow(mediaID, show_name):
            xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, xbmcgui.ListItem(path = getUrl(mediaID)))


def play_playlist(name, list):
        playlist = xbmc.PlayList(1)
        playlist.clear()
        item = 0
        for i in list:
            item += 1
            info = xbmcgui.ListItem('%s) %s' %(str(item),name))
            playlist.add(i, info)
        xbmc.executebuiltin('playlist.playoffset(video,0)')


def addDir(name,url,mode,iconimage,fanart,description,genre,date,showcontext=True,playlist=None,autoplay=False):
        u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+mode
        dir_playable = False
        cm = []

        if mode != 'SR':
            u += "&name="+urllib.quote_plus(name)
            if (fanart is None) or fanart == '': fanart = addonfanart
            u += "&fanart="+urllib.quote_plus(fanart)
            dir_image = "DefaultFolder.png"
            dir_folder = True
        else:
            dir_image = "DefaultVideo.png"
            dir_folder = False
            dir_playable = True

        ok=True
        liz=xbmcgui.ListItem(name, iconImage=dir_image, thumbnailImage=iconimage)
        liz.setInfo( type="Video", infoLabels={ "Title": name, "Plot": description, "Genre": genre, "Year": date } )
        liz.setProperty( "Fanart_Image", fanart )

        if dir_playable == True:
         liz.setProperty('IsPlayable', 'true')
        if not playlist is None:
            playlist_name = name.split(') ')[1]
            cm.append(('Play '+playlist_name+' PlayList','XBMC.RunPlugin(%s?mode=PP&name=%s&playlist=%s)' %(sys.argv[0], playlist_name, urllib.quote_plus(str(playlist).replace(',','|')))))
        liz.addContextMenuItems(cm)
        return xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=dir_folder)

def addLink(url,name,iconimage,fanart,description,genre,date,showcontext=True,playlist=None, autoplay=False):
        return addDir(name,url,'SR',iconimage,fanart,description,genre,date,showcontext,playlist,autoplay)


# MAIN EVENT PROCESSING STARTS HERE

xbmcplugin.setContent(int(sys.argv[1]), 'tvshows')

parms = {}
try:
    parms = dict( arg.split( "=" ) for arg in ((sys.argv[2][1:]).split( "&" )) )
    for key in parms:
       parms[key] = demunge(parms[key])
except:
    parms = {}

p = parms.get

mode = p('mode',None)
if mode==  None:  getSources(p('fanart'))
elif mode=='SR':  xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, xbmcgui.ListItem(path=p('url')))
elif mode=='PP':  play_playlist(p('name'), p('playlist'))
elif mode=='GC':  getCats(p('url'))
elif mode=='GS':  getShow(p('url'), p('name'))

xbmcplugin.endOfDirectory(int(sys.argv[1]))

