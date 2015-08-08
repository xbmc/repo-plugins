import sys
import xbmcplugin, xbmcgui, xbmcaddon
import re, os, time
import urllib, urllib2
import json
import HTMLParser

ROOTDIR = xbmcaddon.Addon(id='plugin.video.amaproracing').getAddonInfo('path')
FANART = ROOTDIR+'/images/fanart_flattrack.jpg'
ICON = ROOTDIR+'/images/icon_flattrack.png'
ROOT_URL = 'http://www.amaprolive.com/ft/dvr/'

class flattrack():


    def ARCHIVE(self):
        url = self.GET_PLAYLIST_URL()        
        req = urllib2.Request(url)
        req.add_header('User-Agent', ' Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
        response = urllib2.urlopen(req)                  
        source=response.read()  
        response.close()            
       
        match = re.compile("<media:player url='(.+?)v=(.+?)'/><media:thumbnail url='(.+?)' height='360'(.+?)<media:title type='plain'>(.+?)</media:title>").findall(source)
       
        for junk,embed_code, thumbnail, junk2, title in match:
            embed_code = embed_code[0:11]
            youtube_link = 'plugin://plugin.video.youtube?path=/root/video&action=play_video&videoid='+embed_code
            self.addLink(title,youtube_link,title,thumbnail,FANART) 

    def GET_PLAYLIST_URL(self):        
        req = urllib2.Request(ROOT_URL)
        req.add_header('User-Agent', ' Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
        response = urllib2.urlopen(req)                  
        source=response.read()  
        response.close()

        start = source.find('gdata.youtube.com/feeds/api/playlists/')
        end = source.find('?v=',start)                
        playlist_link = source[start:end]    
        print "SUBSTRING==="+str(start)+" "+str(end)
        playlist_link = "http://"+playlist_link
        print playlist_link
        return playlist_link
        

    def addLink(self,name,url,title,iconimage,fanart):
        ok=True
        liz=xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage,)
     
        liz.setProperty('fanart_image',fanart)
        liz.setProperty("IsPlayable", "true")
        liz.setInfo( type="Video", infoLabels={ "Title": title } )
        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=url,listitem=liz)
        return ok


    def addDir(self,name,url,mode,iconimage,fanart=None,page=1): 
        params = self.get_params()      
        ok=True
        u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)+"&page="+urllib.quote_plus(str(page))
        liz=xbmcgui.ListItem(name, iconImage=ICON, thumbnailImage=iconimage)
        liz.setInfo( type="Video", infoLabels={ "Title": name } )
        liz.setProperty('fanart_image', fanart)
        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)    
        return ok


    def get_params(self):
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
