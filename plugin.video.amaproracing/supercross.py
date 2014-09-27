import sys
import xbmcplugin, xbmcgui, xbmcaddon
import re, os, time
import urllib, urllib2
import json

ROOTDIR = xbmcaddon.Addon(id='plugin.video.amaproracing').getAddonInfo('path')
FANART = ROOTDIR+'/images/fanart_supercross.jpg'
ICON = ROOTDIR+'/images/icon_supercross.png'
MAIN_URL = 'http://www.supercrossonline.com'

class supercross():

    def CATEGORIES(self):
        self.addDir('Archive','/supercross',201,ICON)


    def ARCHIVE(self):
        url = MAIN_URL+'/supercrosslive/'                
        req = urllib2.Request(url)
        req.add_header('User-Agent', ' Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
        response = urllib2.urlopen(req)
        link=response.read()
        response.close()        
        link = link.replace('\n',"")
        start = link.index('<strong>Archived Streams:</strong>')
        end = link.index('</p>',start)    
        link = link[start:end]
        link = link.replace(' target="_blank"','')
        print link
        #<a href="http://www.supercrossonline.com/News/SupercrossLive/2014/04/24/1/"> East Rutherfrod Pre-Race Press Conference - Thursday, April 24</a>
        #match = re.compile('<a href="(.+?)" target="_blank">Supercross LIVE!(.+?)<').findall(link)    
        #if not match: 
        match = re.compile('<a href="(.+?)">(.+?)<').findall(link)    
            
        for link, location in match: 
            page_url = self.GET_VIDEO_PAGE(link)
            if page_url != '':                
                self.GET_MP4(page_url,location)            
        return

    def GET_VIDEO_PAGE(self,url):
        #Go to link and Find This
        #<iframe width="640" scrolling="no" height="360" frameborder="0" src="http://new.livestream.com/accounts/1543541/events/2641627/videos/38811042/player?autoPlay=false&amp;height=360&amp;mute=false&amp;width=640"></iframe></p>
        if url.startswith('/'):
                url = MAIN_URL + url

        print "HERE URL===" + url
        req = urllib2.Request(url)
        req.add_header('User-Agent', ' Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
        response = urllib2.urlopen(req)
        link=response.read()
        response.close()        
        link = link.replace('\n',"")

        ##############################################
        #Skip past google iframe crap
        ##############################################
        start = link.find('<div id="menucontainer">')
        end = link.find('</body>')
        link = link[start:end]        
        ##############################################

        start_str = '<iframe width="640" scrolling="no" height="360" frameborder="0" src="'
        start = link.find(start_str)        
        if start == -1:                    
            start_str = '<iframe src="'
            start = link.find(start_str)   
            
        end = link.find('?autoPlay=false&amp;height=360&amp;mute=false&amp;width=640"',start)    
        if start != -1 and end != -1:
            link = link[start+len(start_str):end]
        else:
            link = ''
        return link
           

    def GET_MP4(self,url,location):
        #print 'HERE"S my link==='+url
        req = urllib2.Request(url)
        req.add_header('User-Agent', ' Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
        response = urllib2.urlopen(req)
        link=response.read()
        response.close()    

        start_str = '"progressive_url_hd":"'       
        start = link.find(start_str)

        #if start == -1:
            #start_str = '"progressive_url":"'       
            #start = link.find(start_str)

        end = link.find('"',start+len(start_str))  
        if start != -1 and end != -1:
            video_url = link[start+len(start_str):end]

            start_str = '"thumbnail_url":"'
            start = link.find(start_str)
            end = link.find('"',start+len(start_str)) 
            image_url = link[start+len(start_str):end]
            
            self.addLink(location,video_url,location,image_url) 

    def addLink(self,name,url,title,iconimage):
        ok=True
        liz=xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage,)
        liz.setProperty('fanart_image',FANART)
        
        liz.setInfo( type="Video", infoLabels={ "Title": title } )
        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=url,listitem=liz)
        return ok


    def addDir(self,name,url,mode,iconimage,fanart=None):       
        ok=True
        u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)
        liz=xbmcgui.ListItem(name, iconImage=ICON, thumbnailImage=iconimage)
        liz.setInfo( type="Video", infoLabels={ "Title": name } )
        liz.setProperty('fanart_image', FANART)
        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)    
        return ok
