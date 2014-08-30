import sys
import xbmcplugin, xbmcgui, xbmcaddon
import re, os, time
import urllib, urllib2, httplib2
import json
import HTMLParser

ROOTDIR = xbmcaddon.Addon(id='plugin.video.amaproracing').getAddonInfo('path')
FANART = ROOTDIR+'/images/fanart_endurocross.jpg'
ICON = ROOTDIR+'/images/icon_endurocross.png'
ENDURO_FANART = ROOTDIR+'/images/fanart_enduro.jpg'
ENDURO_ICON = ROOTDIR+'/images/icon_enduro.png'
ENDUROCROSS_URL = 'http://www.endurocross.com'
NAT_ENDURO_URL = 'http://www.nationalenduro.com'
#/videos2/?currentPage=1'

class endurocross():

    def CATEGORIES(self):
        self.addDir('Geico AMA Endurocross Championship Series',ENDUROCROSS_URL,301,ICON,FANART,1)
        self.addDir('Kenda AMA National Enduro Championship Series',NAT_ENDURO_URL,301,ENDURO_ICON, ENDURO_FANART,1)


    def ARCHIVE(self,url):
        page = self.GET_PAGE()
        #print 'COMING INTO ARCHIVE==='+url+str(page)
        if url.find(ENDUROCROSS_URL) > -1:
            page_url = url + '/videos/page/' + str(page)
        elif url.find(NAT_ENDURO_URL) > -1:
            page_url = url + '/videos2/?currentPage='+ str(page)
        
        req = urllib2.Request(page_url)
        req.add_header('User-Agent', ' Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
        response = urllib2.urlopen(req)
        link=response.read()
        response.close()     

        if url == ENDUROCROSS_URL:
            match = self.ENDUROCROSS_SCRAPE(link)
            icon = ICON
            fanart = FANART
        elif url == NAT_ENDURO_URL:
            match = self.NAT_ENDURO_SCRAPE(link)         
            icon = ENDURO_ICON
            fanart = ENDURO_FANART
                           
        if page < 9:
            self.addDir('Next>>',url,301,icon,fanart,page+1)

    def ENDUROCROSS_SCRAPE(self,link):
        link = link.replace('\n',"")
        start = link.index('<h1>All videos</h1>')
        end = link.index('<div id="tickets">',start)    
        link = link[start:end]        
        print "ENDUROCROSS PAGE==="+link

        match = re.compile('<h3><a href="(.+?)/">(.+?)</a></h3>').findall(link)   

        for url, name in match:     
            name = HTMLParser.HTMLParser().unescape(name)      
            if url.startswith('/'):
                url = ENDUROCROSS_URL + url
            #print "VIDEO URL===" + url
            req = urllib2.Request(url)
            req.add_header('User-Agent', ' Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
            response = urllib2.urlopen(req)
            link=response.read()
            response.close()        
            link = link.replace('\n',"")

            start_str = '<meta property="og:image" content="'
            start = link.find(start_str)                           
            end = link.find('"',start+len(start_str)) 
            img_url = link[start+len(start_str):end]
            print "IMAGE URL==="+img_url

            self.GET_YOUTUBE_LINK(link,name,img_url,FANART)           

    def NAT_ENDURO_SCRAPE(self,link):
        link = link.replace('\n',"")
        start = link.index('<div id="contentWrapper"><div id="content">')
        end = link.index('</div></div> <!-- Content -->',start)    
        link = link[start:end]        
        print "ENDURO NAT PAGE==="+link

        #match = re.compile('<h2 class="title"><a class="journal-entry-navigation-current" href="(.+?)">(.+?)</a></h2><div class="journal-entry-tag journal-entry-tag-post-title"><span class="posted-on"><img title="Date" alt="Date" class="inline-icon date-icon" rel="blk_ko_18" src="/universal/images/transparent.png" />(.+?)</span></div><div class="body"><p><iframe width="560" height="315" src=(.+?) frameborder="0" allowfullscreen></iframe></p>').findall(link)   
        match_names = re.compile('<a class="journal-entry-navigation-current" href="(.+?)">(.+?)</a>').findall(link)
        #for junk1, name in match_names:
            #print "My Name==="+name

        match = re.compile('<p><iframe width="560" height="315" src=(.+?) frameborder="0" allowfullscreen></iframe></p>').findall(link)   
        i = 0
        for youtube_link in match:            
            #print "My LINK=="+youtube_link
            self.GET_YOUTUBE_LINK(youtube_link, HTMLParser.HTMLParser().unescape(str(match_names[i][1])),ENDURO_ICON,ENDURO_FANART)
            i = i + 1


    def GET_YOUTUBE_LINK(self,link,name,img_url,fanart):            
        start_str = 'www.youtube.com/embed/'
        start = link.find(start_str)                                   
        end = link.find('"',start+len(start_str))    

        if start != -1 and end != -1:
            embed_code = link[start+len(start_str):end]
            youtube_link = 'plugin://plugin.video.youtube?path=/root/video&action=play_video&videoid='+embed_code                           
            #print 'YOUTUBE LINK==='+youtube_link            
            self.addLink(name,youtube_link,name,img_url,fanart)        


    def GET_PAGE(self):
        params = self.get_params()
        page = 1
        try:
            page=int(urllib.unquote_plus(params["page"]))
        except:
            pass         
        return page
       

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