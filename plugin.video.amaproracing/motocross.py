import sys
import xbmcplugin, xbmcgui, xbmcaddon
import re, os, time
import urllib, urllib2
import json

ROOTDIR = xbmcaddon.Addon(id='plugin.video.amaproracing').getAddonInfo('path')
ROOTURL = 'http://www.promotocross.com'
FANART = ROOTDIR+'/images/fanart_motocross.jpg'
ICON = ROOTDIR+'/images/icon_motocross.png'
MAIN_URL = 'http://www.promotocross.com'

class motocross():

    def CATEGORIES(self):
        self.addDir('Archive','/GET_YEAR',100,'')    
        self.addDir('Highlights','/GET_HIGHLIGHTS',101,'')        
        self.SET_LIVE_LINK(MAIN_URL+'/motocross/live') 


    def GET_YEAR(self):                   
        url = MAIN_URL
        req = urllib2.Request(url)      
        req.add_header('User-Agent', ' Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
        response = urllib2.urlopen(req)
        link=response.read()
        response.close()        
        link = link.replace('\n',"")
        start = link.index("Archive</a><ul")        
        end = link.index("</ul>",start)    
        link = link[start:end]
        
        match = re.compile('id=""><a href="(.*?)">(.+?)</a></li>').findall(link)                
        #print match
        
        for year_link, year in match:   
            print "YEAR LINK==="+year_link
            if int(year) > 2011:
                if year_link.startswith('/'):
                    year_link = MAIN_URL + year_link
                year_link = year_link.replace('" title="','')      
                self.addDir(year,year_link,104,ICON)
                #print GET_YEAR_link
        

    def GET_RACES(self,url,name):
        global full_name
        full_name = name
        req = urllib2.Request(url)
        req.add_header('User-Agent', ' Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
        response = urllib2.urlopen(req)
        link=response.read()
        response.close()        
        link = link.replace('\n',"")

        match = re.compile('<strong>(.+?)</strong>').findall(link)    
        if not match:       
            match = re.compile('<h3>(.+?)</h3>').findall(link) 

        #print match
            
        for location in match:           
            self.addDir(location,link,105,ICON)

        
    def GET_RACE_DAY_VIDEOS(self,url,name,year):    
        ####################################################################
        #Attempt to read the code block where the links for the event reside    
        ####################################################################
        print "HERE IS THE YEAR==="+str(year)
        link = url
        start = link.find('<strong>'+name+'</strong>')
        if start == -1:
            start = link.index('<h3>'+name+'</h3>')
        
        if int(year) == 2014:        
            end = link.find('</p><p><span style="color:#e51937;">',start)         
            if end < 0:        
                end = link.find('</div>',start)            

        elif 2011 < int(year) < 2014:
            #For 2013 videos
            print "In 2013/2012 vids"        
            end = link.find('</p><p><strong>',start)                     
            end2 = link.find('<div style="clear:both;">',start)                     

            if end < 0:                        
                end = link.find('</p></div>',start) 
            elif 0 < end2 < end:            
                end = end2

        elif int(year) < 2012:
            end = link.find('</ul></div>',start)                     



        link = link[start:end]
        #print "HERE IS LINK = "+link

        if int(year) < 2014:                
            self.GET_VIDEO_LINK(link,'')          
        else:
            ######################################################
            # Url contains video titles. Grab those as  selections
            ######################################################
            match = re.compile('<p>(.+?): <a href').findall(link)    
            for video in match:           
                self.addDir(video,link,106,ICON)
            match = re.compile('<br />(.+?): <a href').findall(link)    
            for video in match:           
                self.addDir(video,link,106,ICON)
    


    def GET_VIDEO_LINK(self,url,name):
        link = url
        if name != '':
            start = link.find(name+': <a')
            end = link.find('<br />',start)        
            if end < 0:
                end = len(link)    
            link = link[start:end]        
        
        #ex.'<a href="http://www.allisports.com/motocross/video/2013-hangtown-450-moto-1-full-race-archive" target="_blank">'
        use_rooturl = 0
        match = re.compile('<a href="(.+?)" target="_blank">(.+?)</a>').findall(link)    
        if not match:
            use_rooturl = 1
            match = re.compile('<a href="(.+?)" class="use-ajax">(.+?)</a>').findall(link) 
            if not match:   
                use_rooturl = 0    
                match = re.compile('<a href="(.+?)">(.+?)</a>').findall(link) 
               

        #################################################
        #Go to each links page and retrieve the embedcode     
        #################################################
        for link,video_name in match:           
            if use_rooturl == 1:
                link = ROOTURL+link
            print "LINK ==="+link
            req = urllib2.Request(link)
            req.add_header('User-Agent', ' Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
            response = urllib2.urlopen(req)
            video_link=response.read()
            response.close()        
            video_link = video_link.replace('\n',"")        

            ###############################################################################################################################################################
            #Get video image
            #ex. <meta property="og:image" content="http://www.promotocross.com/sites/default/files/images/video/thumbnail/start_450_moto_1_glenhelen_ortiz_49_1280.jpg" />
            ###############################################################################################################################################################
            start_str = '<meta property="og:image" content="'
            start = video_link.index(start_str)        
            end = video_link.index('" />',start)            
            image_link = video_link[start+len(start_str):end]                
            #print "IMAGE LINK =" +image_link
            ###############################################################################################################################################################


            #################################################################################################################################################
            #Get SWF embedcode
            #ex. <meta property="og:video" content="http://player.ooyala.com/player.swf?embedCode=45Mm8xbjpdrkHW1TKb8N-BFXJTTPunCK&amp;keepEmbedCode=true" />
            #################################################################################################################################################
            start = video_link.find('<meta property="og:video" content=')        
            end = video_link.find('keepEmbedCode=true" />',start)            
            swf_link = video_link[start:end]                
            
            start = swf_link.find('swf?embedCode=')        
            end = swf_link.find('&amp;',start) 
            embedcode = swf_link[start+14:end]                
            ##################################################################################################################################################


            #################################################################################################
            #If SWF embedcode not found search for NBC vplayer
            #ex. http://vplayer.nbcsports.com/p/BxmELC/allisports/select/n_vapP81zrz8?autoPlay=true?form=html
            #################################################################################################
            if start == -1:
                self.CHECK_FOR_NBC_VIDEO(video_link,video_name,image_link)              
            else:
                params = self.get_params()
                year=urllib.unquote_plus(params["year"])
                ####################################################################################################
                #Set default RTMP settings for ooyala player and inject the embedcode to specify which video to play
                ####################################################################################################
                
                if year == "2014" or year == '2013':
                    app = 'ondemand?_fcs_vhost=cp58064.edgefcs.net'
                    swfurl = 'http://player.ooyala.com/static/cacheable/27d91126daacf9df38e10be48dcfa3a5/player_v2.swf'    
                    rtmpurl = 'rtmp://63.80.4.116/ondemand?_fcs_vhost=cp58064.edgefcs.net'                    
                    pageurl = 'http://www.promotocross.com/sites/all/themes/lucasmoto2013/ooyala.php?embedCode='+embedcode
                    playpath = 'mp4:/c/'+embedcode+'/DOcJ-FxaFrRg4gtDEwOjFyazowODE7G_'                           
                elif year == '2012':                
                    app = 'ondemand?_fcs_vhost=cp58064.edgefcs.net'                
                    pageurl = 'http://www.promotocross.com/mx/archive'
                    swfurl = 'http://player.ooyala.com/static/cacheable/27d91126daacf9df38e10be48dcfa3a5/player_v2.swf'
                    rtmpurl = 'rtmp://209.18.41.108/ondemand?_fcs_vhost=cp58064.edgefcs.net'
                    playpath = 'mp4:/c/'+embedcode+'/DOcJ-FxaFrRg4gtGEwOmk2OjBrO5dC5F'



                rtmp = rtmpurl + ' playpath=' + playpath + ' app=' + app + ' pageURL=' + pageurl + ' swfURL=' + swfurl             
                self.addLink(video_name,rtmp,video_name,image_link) 
                ####################################################################################################   

            ####################################################################################################

    def CHECK_FOR_NBC_VIDEO(self,url,video_name,image_link):
        #######################################################################
        #Search for vplayer hyper-link in url code
        #######################################################################
        #print "INCOMING URL:"+url
        start = url.find('http://vplayer.nbcsports.com')        
        end = url.find('?autoPlay=true',start)
        url = url[start:end]                      
        #print 'DONE GETTING URL:'+str(start)+' '+str(end)+url
        #######################################################################

        req = urllib2.Request(url)            
        req.add_header('User-Agent', ' Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
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
        #print "HERE IS WHAT'S COMING BACK ==="+str(start)+' '+str(end)+video_link
        #######################################################################
            
        req = urllib2.Request(video_link)            
        req.add_header('User-Agent', ' Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
        response = urllib2.urlopen(req)
        video_link=response.read()
        response.close()      
        
        #######################################################################
        #Read SMIL response file and pull the highest quality video from it
        #######################################################################
        print "NOW THE SMIL="+video_link
          
        match=re.compile('<video src="(.+?)" system-bitrate="(.+?)" height="(.+?)" width="(.+?)"/>').findall(video_link,10)
            
        for link,bitrate,height,width in match:           
            #Add only the first (highest quality) video as a selection
            self.addLink(video_name,link,video_name,image_link) 
            break
        #######################################################################


    def addDir(self,name,url,mode,iconimage,fanart=None):   
        params = self.get_params()
        prev_name = ''
        full_name = ''
        try:
            prev_name=urllib.unquote_plus(params["full_name"])
        except:
            pass 
        if mode > 104:
            if prev_name != '':
                full_name = prev_name + ' - ' + name
            else:
                full_name = name

        u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)+"&full_name="+urllib.quote_plus(full_name)

        year = ''
        if mode == 104:
            year = name
        else:        
            try:
                year=urllib.unquote_plus(params["year"])
            except:
                pass 

        u = u+"&year="+urllib.quote_plus(year)
        ok=True
        liz=xbmcgui.ListItem(name, iconImage=ICON, thumbnailImage=iconimage)
        liz.setInfo( type="Video", infoLabels={ "Title": name } )
        if fanart == None:
            fanart = FANART
        liz.setProperty('fanart_image', fanart)
        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)    
        return ok


    def GET_PID(self):
        ##########################################################################################################
        #Request the NBC sports moto stream, which redirects to a link that contains a PID variable that is needed    
        ##########################################################################################################
        req = urllib2.Request('http://motostream.nbcsports.com/ ')            
        #req.add_header('Connection','keep-alive')
        req.add_header('Accept','text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8')
        req.add_header('User-Agent', ' Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3') 
        req.add_header('Accept-Encoding', 'gzip,deflate,sdch')
        req.add_header('Accept-Language', 'en-US,en;q=0.8')
        req.add_header('Referer', 'http://www.promotocross.com/motocross/live')

        response = urllib2.urlopen(req)        
        pid_url = response.geturl()
        response.close()  
        print 'REDIRECT URL:' + pid_url    
        ##########################################################################################################

        ##########################################################################################################
        #Get the PID value from the url and create a link to the json file which contains the f4m file link
        #'http://stream.nbcsports.com/motocross/?pid=15620&referrer='
        ##########################################################################################################    
        start_str = 'http://stream.nbcsports.com/motocross/?pid='
        start = pid_url.find(start_str)
        end = pid_url.find('&referrer=',start)            
        pid = pid_url[start+len(start_str):end]                

        print "PID="+pid
        return pid


    def GET_HIGHLIGHTS(self):               
        #highlights = 'http://stream.nbcsports.com/data/mobile/moto-2013.json'
        highlights = 'http://stream.nbcsports.com/data/mobile/mcms/prod/nbc-moto.json '
                     #http://hdliveextra-pmd.edgesuite.net/HD/image_sports/mobile/2014-08-23T22-56-41.233Z--1280x720_m61.jpg
                     #http://hdliveextra-pmd.edgesuite.net/HD/image_sports/mobile/2014-08-16T18-55-51.666Z--1280x720_m61.jpg
        print "HIGHLIGHT SOURCES:"+highlights

        ###########################################
        #Read the json file and extraxt the f4m url
        ###########################################    
        req = urllib2.Request(highlights) 
        req.add_header('User-Agent', ' Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3') 
        #req.add_header('Referer', 'http://www.promotocross.com/motocross/live')
        response = urllib2.urlopen(req)        
        #data_sources = response.read()
        json_source = json.load(response)
        response.close()  
              
        #print data_sources
        #video_source =  json_source['videoSources']
        video_source =  json_source['showCase']
        for item in video_source:
            #url =  item['sourceUrl'] + '|' + header_encoded            
            url = item['iosStreamUrl']
            name = item['title']
            #info = item['info']
            imgurl = item['image']
            imgurl = 'http://hdliveextra-pmd.edgesuite.net/HD/image_sports/mobile/'+imgurl+'_m61.jpg'
            self.addLink(name,url,name,imgurl) 
    

    def SET_LIVE_LINK(self,url): 
        req = urllib2.Request(url)            
        req.add_header('User-Agent', ' Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
        response = urllib2.urlopen(req)
        live_source = response.read()
        response.close()  

        start_text = '<a href="http://motostream.nbcsports.com"><img typeof="foaf:Image" src="'
        start = live_source.find(start_text)        
        end = live_source.find('"',start+len(start_text))
        live_details_img = live_source[start+len(start_text):end] 

        #print 'Image Link'+ str(start) + ' '+ str(end) + live_details_img
        
        self.addDir('Live Stream','live',102,live_details_img,live_details_img)    


    def PLAY_LIVE(self):        
        pid = self.GET_PID()

        #*********************************************************
        # LINK TO GET LIVE SOURCES 
        #ex. #http://stream.nbcsports.com/data/event_config_15620.json
        #*********************************************************
        live_sources = 'http://stream.nbcsports.com/data/live_sources_'+pid+'.json'    
        print "LIVE SOURCES:"+live_sources
        ##########################################################################################################


        ###########################################
        #Read the json file and extraxt the f4m url
        ###########################################
        req = urllib2.Request(live_sources)     
        req.add_header('User-Agent', ' Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3') 
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
               
            header = {  'User-Agent' : 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.153 Safari/537.36',
                        'Accept' : '*/*',                  
                        'Referer' : 'http://stream.nbcsports.com/motocross/?pid='+pid+'&referrer=http://www.promotocross.com/motocross/live',
                        'Accept-Language' : 'en-US,en;q=0.8'} 
               
            header_encoded = urllib.urlencode(header)       
            url =  urllib.quote_plus(url+'|')       
            full_url = url + header_encoded     
            #print full_url
            
            ios_url = ios_url.replace('manifest(format=m3u8-aapl-v3)','QualityLevels(3450000)/Manifest(video,format=m3u8-aapl-v3,audiotrack=audio_en_0)')                       
            ios_url = ios_url + '?' + header_encoded 
            endcoded_cookies = self.GET_COOKIE(ios_url)
            if endcoded_cookies != '':
                ios_url = ios_url + '&' + endcoded_cookies      
                print ios_url

            self.addLink(name,ios_url, name,FANART) 
        except:
            pass


    def GET_COOKIE(self,url):
        #Used to get cookie for non-archived videos 
        url = url.replace('|','?')
        print 'COOKIE URL===' + url
        alid = ''
        hdntl = ''
        cookies = ''
        endcoded_cookies = ''

        req = urllib2.Request(url)            
        req.add_header('User-Agent', ' Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
        response = urllib2.urlopen(req)    
        header = response.info()
        #print header
        try: 
            get_cookies = header['Set-Cookie']
            #print 'Read Cookies:' + get_cookies 
            ###################################################
            #Only keep the cookies we need
            # _alid_ for all
            # hdntl for live streams
            ###################################################
            start = get_cookies.find('_alid_')
            end = get_cookies.find(';',start)

            alid =  get_cookies[start:end+1]    
            print 'ALID===' + alid
            cookies = alid

            start = get_cookies.find('hdntl')
            if start != -1:
                end = get_cookies.find(';',start)
                hdntl =  get_cookies[start:end+1]
                print 'HDNTL===' + hdntl
                cookies = cookies + ' ' + hdntl

            if cookies != '':
                cookies = {'Cookie' : cookies}
                endcoded_cookies = urllib.urlencode(cookies)
            
            print 'Encoded Cookies:' + endcoded_cookies
        except:
            pass

        return endcoded_cookies

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
