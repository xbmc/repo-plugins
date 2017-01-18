import sys
import xbmcplugin, xbmcgui, xbmcaddon, xbmc
import re, os, time
import HTMLParser, urllib, urllib2
import json

ROOTDIR = xbmcaddon.Addon(id='plugin.video.amaproracing').getAddonInfo('path')
ROOTURL = 'http://www.promotocross.com'
FANART = ROOTDIR+'/images/fanart_motocross.jpg'
ICON = ROOTDIR+'/images/icon_motocross.png'
MAIN_URL = 'http://www.promotocross.com'
USER_AGENT = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3'

class motocross():

    def categories(self):
        self.addDir('Full Motos On Demand','/GET_YEAR',100,'')    
        self.addDir('Videos On Demand','/GET_HIGHLIGHTS',101,'')        
        self.setLiveLink(MAIN_URL+'/mx/live') 
 

    def fullMotoYears(self):
        url = 'http://www.promotocross.com/media-block-get-filter-options-ajax/ajax/filter-year/451/16/video/all/all/all/all/all'
        req = urllib2.Request(url)      
        req.add_header('User-Agent', USER_AGENT)
        response = urllib2.urlopen(req)        
        json_source = json.load(response)
        response.close()

        options = json_source['options']                
        year_dict = {}
        for option in  options:           
            year_dict[option] = options[option]
            
        for key in sorted(year_dict, reverse=True):            
            self.addDir(year_dict[key],key,103,'')


    def fullMotosOnDemand(self, url):        
        n=0
        found_stream = True        
        while found_stream:
            xbmc.log(url+str(n*11))
            req = urllib2.Request(url+str(n*11))      
            req.add_header('User-Agent', USER_AGENT)
            response = urllib2.urlopen(req)        
            json_source = json.load(response)
            response.close()

            xbmc.log(str(json_source))

            link = json_source[1]['data']
            link = link.decode('utf-8')
            link = link.replace('\n',"")            
            
            match = re.compile('<img typeof="foaf:Image" src="(.+?)"(.*?)/></a>(.*?)<a href="(.*?)">(.+?)Full Race', re.IGNORECASE).findall(link)         
            found_stream = False
            for image_url, junk, junk2, temp_url, title in match:                
                found_stream = True
                title = title.replace('(','')
                title = title.replace(':','')                
                stream = MAIN_URL+temp_url
                #self.addDir(title,MAIN_URL+url,104,image_url)                
                self.addStream(title,stream,106,image_url)

            n = n+1
    

    
    def scrapeStream(self,url,video_name,image_link):        
        req = urllib2.Request(url)
        req.add_header('User-Agent', USER_AGENT)
        response = urllib2.urlopen(req)
        link=response.read()
        response.close()        
        url = link.replace('\n',"")
        #######################################################################
        #Search for vplayer hyper-link in url code
        #######################################################################    
        start_str = "build_button('"
        start = url.find(start_str)
        end = url.find('?autoPlay=true',start)
        url = url[start+len(start_str):end]                              
        #######################################################################

        req = urllib2.Request(url)            
        req.add_header('User-Agent', USER_AGENT)
        response = urllib2.urlopen(req)
        video_link=response.read()
        response.close()                  
        video_link = video_link.replace('\n',"")                    
        
        #######################################################################
        #Pull SMIL file link from url response
        #######################################################################
        start_text = 'http://link.theplatform.com'
        start = video_link.index(start_text)        
        end = video_link.find('" type="application/smil+xml" />')
        video_link = video_link[start:end]                          
        #######################################################################
            
        req = urllib2.Request(video_link)            
        req.add_header('User-Agent', USER_AGENT)
        response = urllib2.urlopen(req)
        video_link=response.read()
        response.close()      
                
          
        match=re.compile('<video src="(.+?)" system-bitrate="(.+?)" height="(.+?)" width="(.+?)"/>').findall(video_link,10)
        stream_url = ''
        stream_url = {}
        stream_title = [] 
        for link,bitrate,height,width in match:  
            bitrate = str(int(bitrate) / 1024)
            title = bitrate+'kbps ('+width+'x'+height+')'
            stream_title.append(title)                
            stream_url.update({title:link+'|User-Agent='+USER_AGENT})

        dialog = xbmcgui.Dialog()
        ret = dialog.select('Choose Stream Quality', stream_title)        
        if ret >=0:
            stream_url = stream_url.get(stream_title[ret]) 
        else:
            sys.exit()

        return stream_url
        




    def playStream(self, stream_url):        
        listitem = xbmcgui.ListItem(path=stream_url)
        xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, listitem)


    def getPID(self):        
        req = urllib2.Request('http://motostream.nbcsports.com/')                    
        req.add_header('Accept','text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8')
        req.add_header('User-Agent', USER_AGENT) 
        req.add_header('Accept-Encoding', 'deflate')
        req.add_header('Accept-Language', 'en-US,en;q=0.8')
        req.add_header('Referer', 'http://www.promotocross.com/motocross/live')

        response = urllib2.urlopen(req)        
        pid_url = response.geturl()
        response.close()  

        
        start_str = 'http://stream.nbcsports.com/motocross/?pid='
        start = pid_url.find(start_str)
        end = pid_url.find('&referrer=',start)            
        pid = pid_url[start+len(start_str):end]                
        
        return pid


    def getVideoTypes(self):
        url = 'http://www.promotocross.com/mx/video'
        req = urllib2.Request(url)      
        req.add_header('User-Agent', USER_AGENT)
        response = urllib2.urlopen(req)        
        html_source = response.read()
        response.close()
       
        start_str = '<select class="filter-category form-select">'
        start = html_source.find(start_str)
        end = html_source.find('</select>',start)            
        options = html_source[start+len(start_str):end]    
                
        match = re.compile('<option value="(.+?)">(.+?)</option>', re.IGNORECASE).findall(options)         

        for value_id, name in match:    
            url = 'http://www.promotocross.com/media-block-get-results-ajax/ajax/'+value_id+'/16/video/all/all/all/all/all/0'
            self.addDir(name,url,107,'')                
            

    def getVOD(self,url):                       
        req = urllib2.Request(url)      
        req.add_header('User-Agent', USER_AGENT)
        response = urllib2.urlopen(req)        
        json_source = json.load(response)
        response.close()
        
        link = json_source[1]['data']
        link = link.encode('utf-8')
        link = link.replace('\n',"")                 

        
        match = re.compile('<img typeof="foaf:Image" src="(.+?)"(.*?)/></a>(.*?)<a href="(.*?)">(.+?)</a>', re.IGNORECASE).findall(link)         
        found_stream = False
        for image_url, junk, junk2, temp_url, title in match:                
            found_stream = True
            title = title.replace('(','')
            title = title.replace(':','') 
            title = HTMLParser.HTMLParser().unescape(title)
            stream = MAIN_URL+temp_url            
            self.addStream(title,stream,106,image_url)


        #Next Page    
        list_id = int(url[url.rfind('/')+1:])        
        url = url[0:url.rfind('/')+1]+str(list_id+11)        
        self.addDir('Next Page >>',url,107,'') 



    def setLiveLink(self,url): 
        
        req = urllib2.Request(url)            
        req.add_header('User-Agent', USER_AGENT)
        response = urllib2.urlopen(req)
        live_source = response.read()
        response.close()  

        pid = self.getPID()
        
        start_text = '<img alt="" class="media-image" height="540" width="960" typeof="foaf:Image" src="'
        start = live_source.find(start_text)        
        end = live_source.find('"',start+len(start_text))
        live_details_img = live_source[start+len(start_text):end] 

        
        
        self.addDir('Race Day Live Stream',pid,102,live_details_img,live_details_img)    


    def playLive(self,pid):                
        live_sources = 'http://stream.nbcsports.com/data/live_sources_'+pid+'.json'           
        req = urllib2.Request(live_sources)     
        req.add_header('User-Agent', USER_AGENT) 
        try:               
            response = urllib2.urlopen(req)         
            json_source = json.load(response)
            response.close()            
            
            video_source =  json_source['videoSources']


            for item in video_source:
                url =  item['sourceUrl']
                ios_url =  item['iossourceUrl']
                name = item['name'] + ' - ' + item['title']
                status = item['type']
               
            header = {  'User-Agent' : USER_AGENT,
                        'Accept' : '*/*',                  
                        'Referer' : 'http://stream.nbcsports.com/motocross/?pid='+pid+'&referrer=http://www.promotocross.com/motocross/live',
                        'Accept-Language' : 'en-US,en;q=0.8'} 
               
            header_encoded = urllib.urlencode(header)       
            url =  urllib.quote_plus(url+'|')       
            full_url = url + header_encoded     
            
            ios_url = ios_url.replace('manifest(format=m3u8-aapl-v3)','QualityLevels(3450000)/Manifest(video,format=m3u8-aapl-v3,audiotrack=audio_en_0)')        
            ios_url = ios_url + '|User-Agent='+USER_AGENT            
            
            self.addLink(name,ios_url, name,FANART) 
        except:
            pass


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


    def addLink(self,name,url,title,iconimage):
        params = self.get_params()
        full_name = ''
        try:
            full_name = urllib.unquote_plus(params["full_name"])
        except:
            pass 
        
        if full_name != '':
            title = full_name + ' ' + title

        ok=True
        liz=xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage,)
        liz.setProperty('fanart_image',iconimage)
        liz.setInfo( type="Video", infoLabels={ "Title": title } )
        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=url,listitem=liz)
        return ok


    def addDir(self,name,url,mode,iconimage,fanart=None):   
        params = self.get_params()
        u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)+"&img_url="+urllib.quote_plus(iconimage)

        ok=True
        liz=xbmcgui.ListItem(name, iconImage=ICON, thumbnailImage=iconimage)
        liz.setInfo( type="Video", infoLabels={ "Title": name } )
        if fanart == None:
            fanart = FANART
        liz.setProperty('fanart_image', fanart)
        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)    
        return ok


    def addStream(self,name,url,mode,iconimage,fanart=None):       
        ok=True
        u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)
        u = u+"&img_url="+urllib.quote_plus(iconimage)            
        liz=xbmcgui.ListItem(name, iconImage=ICON, thumbnailImage=iconimage)            
        liz.setInfo(type="Video", infoLabels='')
        if fanart != None:
            liz.setProperty('fanart_image', fanart)
        else:
            liz.setProperty('fanart_image', FANART)

        liz.setProperty("IsPlayable", "true")
        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=False)
        xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
        
        return ok
