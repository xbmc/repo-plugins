import sys
import xbmcplugin, xbmcgui, xbmcaddon
import re, os, time
import urllib, urllib2, httplib2
import json
import HTMLParser

ROOTDIR = xbmcaddon.Addon(id='plugin.video.amaproracing').getAddonInfo('path')
FANART = ROOTDIR+'/images/fanart_roadracing.jpg'
ICON = ROOTDIR+'/images/icon_roadracing.png'
ROOT_URL = 'www.amaprolive.com/rr/dvr/'

#/videos2/?currentPage=1'

class roadracing():


    def ARCHIVE(self):
        #page = self.GET_PAGE()
        #print 'COMING INTO ARCHIVE==='+url+str(page)              
        #req = urllib2.Request('http://gdata.youtube.com/feeds/api/playlists/PLY7CVMpwTxs5qbGvnx5k31IhouC9MlFUe?v=2&alt=json-in-script&format=5&callback=processYouTubeJSON')
        req = urllib2.Request('http://gdata.youtube.com/feeds/api/playlists/PLY7CVMpwTxs5qbGvnx5k31IhouC9MlFUe')
        req.add_header('User-Agent', ' Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
        response = urllib2.urlopen(req)                  
        source=response.read()  
        response.close()            
        #<media:player url='http://www.youtube.com/watch?v=pjMXUL5AlP4&amp;feature=youtube_gdata_player'/><media:thumbnail url='http://i.ytimg.com/vi/pjMXUL5AlP4/0.jpg' height='360' width='480' time='00:11:03'/><media:thumbnail url='http://i.ytimg.com/vi/pjMXUL5AlP4/1.jpg' height='90' width='120' time='00:05:31.500'/><media:thumbnail url='http://i.ytimg.com/vi/pjMXUL5AlP4/2.jpg' height='90' width='120' time='00:11:03'/><media:thumbnail url='http://i.ytimg.com/vi/pjMXUL5AlP4/3.jpg' height='90' width='120' time='00:16:34.500'/><media:title type='plain'>GEICO Motorcycle AMA Pro Road Racing Pre-Race Show - New Jersey Motorsports Park - 2013</media:title><yt:duration seconds='1326'/></media:group><gd:rating average='4.5555553' max='5' min='1' numRaters='9' rel='http://schemas.google.com/g/2005#overall'/><yt:statistics favoriteCount='0' viewCount='2035'/><yt:description>Watch the stars of GEICO Motorcycle AMA Pro Road Racing before they suit up and put their helmets on at New Jersey Motorsports Park by watching the AMA Pro Racing Pre-Race Show presented by 1-800-Motorcycle. Paul Page, Danielle Teal and Scott Russell give you behind the scenes access to what's going on both on and off the track.
        #<li class="strYT300 show" onclick="clickChannel('NcV1r3D--WA', 'http://www.youtube.com/embed/NcV1r3D--WA?autoplay=1&amp;enablejsapi=1&amp;origin=http://www.amaprolive.com', '2014 DAYTONA 200 FULL Race (HD) - AMA Pro GoPro Daytona SportBike - Daytona International Speedway')"><div class="titlec">2014 DAYTONA 200 FULL Race (HD) - AMA Pro GoPro Daytona SportBike - Daytona International Speedway</div><div class="imgWrap"><img src="http://i.ytimg.com/vi/NcV1r3D--WA/mqdefault.jpg" width="290"><img class="hoverimage" src="/assets/icons/btn-play-rr.png" alt=""></div><div class="tabY-desc">Watch the 73rd running of the historic DAYTONA 200 featuring the GoPro Daytona SportBike class at Daytona International Speedway. Pole-winner Danny Es...</div></li>
        #source = source.replace('?','\?')
        print "RESPONSE==="+str(source)
        match = re.compile("<media:player url='(.+?)v=(.+?)'/><media:thumbnail url='(.+?)' height='360'(.+?)<media:title type='plain'>(.+?)</media:title>").findall(source)
        #&amp;feature=youtube_gdata_player
        #match = re.compile("<link rel='alternate' type='text/html' href='http://www.youtube.com/watch?v=(.+?)&amp;feature=youtube_gdata'/>").findall(source)
        #<media:thumbnail url='(.+?)'/><media:title type='plain'>(.+?)</media:title>").findall(source)   
        print match

        for junk,embed_code, thumbnail, junk2, title in match:
            embed_code = embed_code[0:11]
            print "EMBED_CODE="+embed_code
            print "THUMB="+thumbnail                   
            print "TITLE="+title
            youtube_link = 'plugin://plugin.video.youtube?path=/root/video&action=play_video&videoid='+embed_code                           
            print 'YOUTUBE LINK==='+youtube_link                                    
            #self.addLink(name,youtube_link,name,img_url,fanart) 
            self.addLink(title,youtube_link,title,thumbnail,FANART) 
        

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