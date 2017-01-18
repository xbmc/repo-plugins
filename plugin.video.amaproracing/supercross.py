import sys
import xbmc, xbmcplugin, xbmcgui, xbmcaddon
import re, os, time
import urllib, urllib2
import json

ROOTDIR = xbmcaddon.Addon(id='plugin.video.amaproracing').getAddonInfo('path')
FANART = ROOTDIR+'/images/fanart_supercross.jpg'
ICON = ROOTDIR+'/images/icon_supercross.png'
LIVE_FANART = 'http://www.supercrosslive.com/sites/default/files/Hero_slide_RDL.jpg'
USER_AGENT = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3'

class supercross():
    #Livestream Variables
    owner_id = '1543541'
    

    def categories(self):        
        self.addDir('Race Day Live','/supercross/live',202,ICON,LIVE_FANART)        
        self.addDir('Race Day Live Archive','/supercross/archive',203,ICON)
        self.addDir('View Supercross Youtube Channel','/supercross/youtube',201,ICON)                


    def raceDayLive(self):                              

        #Attempt to get the Live Stream
        try:            
            url = 'https://livestream.com/api/accounts/'+self.owner_id+'/events?filter=video'
            json_source = self.getLivestreamInfo(url)
            #self.addLivestreamLink(str(json_source['upcoming_events']['data'][0]['id']))             
            if json_source['data']:
                for event in json_source['data']:            
                    event_id = str(event['id'])
                    owner_id = str(event['owner_account_id'])                
                    name = event['full_name'].encode('utf-8')                
                    icon = event['logo']['url']
                    
                    if event['in_progress']:
                        name = '[COLOR=FF00B7EB]'+name+'[/COLOR]'

                    self.addDir(name,'/live_now',204,icon,FANART,event_id,owner_id)                    
            else:
                self.raceDayLiveNext()    
        except:
            self.raceDayLiveNext()
            
        finally:
            pass
    
    def getLiveStream(self,owner_id,event_id):
        #url = 'https://livestream.com/accounts/'+owner_id+'/events/'+event_id+'/viewing_info'
        url = 'https://livestream.com/api/accounts/'+owner_id+'/events/'+event_id+'/'
        
        try:
            req = urllib2.Request(url)       
            response = urllib2.urlopen(req)                    
            json_source = json.load(response)
            response.close()
            
            m3u8_url = json_source['stream_info']['m3u8_url']         
            req = urllib2.Request(m3u8_url)
            response = urllib2.urlopen(req)                    
            master = response.read()
            response.close()
            cookie = ''
            try:
                cookie =  urllib.quote(response.info().getheader('Set-Cookie'))
            except:
                pass

            line = re.compile("(.+?)\n").findall(master)  

            for temp_url in line:
                if '.m3u8' in temp_url:
                    name = 'blah'            
                    temp_url = temp_url+'|User-Agent='+USER_AGENT
                    if cookie != '':
                        temp_url = temp_url + '&Cookie='+cookie           
                    self.addLink(name +' ('+desc+')',temp_url, name +' ('+desc+')', FANART)
                else:
                    desc = ''
                    start = temp_url.find('RESOLUTION=')
                    if start > 0:
                        start = start + len('RESOLUTION=')
                        end = temp_url.find(',',start)
                        desc = temp_url[start:end]
                    else:
                        desc = "Audio"
        
        except:
            self.raceDayLiveNext()
            pass
        

    def raceDayLiveNext(self):
        """
        #Get the next live stream date
        url = 'http://www.supercrosslive.com/race-day-live'
        req = urllib2.Request(url) 
        req.add_header('User-Agent', ' Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/40.0.2214.115 Safari/537.36') 
        #req.add_header('Referer', 'http://www.promotocross.com/motocross/live')
        response = urllib2.urlopen(req) 
        html = response.read()
        start = html.find('<h2> Race Day Live presented')
        end = html.find('</h2>', start)
        next_stream = html[start+5:end]
        """
        next_stream = "No live stream currently available. Check back on day of race."
        self.addLink(next_stream,'',next_stream, LIVE_FANART)
            

    def raceDayArchive(self):
        try:
            url = 'https://livestream.com/api/accounts/'+self.owner_id
            json_source = self.getLivestreamInfo(url)
            #Load all past events            
            for past_event in json_source['past_events']['data']:            
                name = past_event['full_name']
                bg_url = past_event['background_image']['url']
                event_id = str(past_event['id'])
                
                #http://new.livestream.com/api/accounts/1543541/events/3882193/feed.json?&filter=video
                #self.addLivestreamLink('3882193')         
                self.addLivestreamLink(event_id)         

        except:            
            pass


    def getLivestreamInfo(self,url):        
        req = urllib2.Request(url) 
        req.add_header('User-Agent', USER_AGENT)         
        response = urllib2.urlopen(req)                
        json_source = json.load(response)
        response.close()  

        return json_source


    def addLivestreamLink(self,event_id):
        url = 'https://livestream.com/api/accounts/'+self.owner_id+'/events/'+event_id+'/feed.json?&filter=video'
        
        try:
            req = urllib2.Request(url) 
            req.add_header('User-Agent', USER_AGENT)                                    
            response = urllib2.urlopen(req)                    
            json_source = json.load(response)
            response.close()
           

            name = json_source['data'][0]['data']['caption']
            img_url = json_source['data'][0]['data']['thumbnail_url']            
            #Attempt to get the HD feed, if not try for the SD
            try:
                stream_url = json_source['data'][0]['data']['progressive_url_hd']+'|User-Agent='+USER_AGENT
                self.addLink(name, stream_url, name, img_url)
            except:
                stream_url = json_source['data'][0]['data']['progressive_url']+'|User-Agent='+USER_AGENT
                self.addLink(name, stream_url, name, img_url)
            finally:                
                pass
        except:
            pass



    def getYoutubeChannel(self):        
        win = str(xbmcgui.getCurrentWindowId())
        xbmc.executebuiltin('ActivateWindow('+win+',plugin://plugin.video.youtube/user/SupercrossLive/,return)')



    def addLink(self,name,url,title,iconimage,fanart=None):
        ok=True
        liz=xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
        liz.setProperty('fanart_image',FANART)
        liz.setProperty("IsPlayable", "true")
        liz.setInfo( type="Video", infoLabels={ "Title": title } )
        if fanart != None:
            liz.setProperty('fanart_image', fanart)
        else:
            liz.setProperty('fanart_image', FANART)
        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=url,listitem=liz)
        return ok


    def addDir(self,name,url,mode,iconimage,fanart=None,event_id=None,owner_id=None):       
        ok=True
        u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)
        if event_id != None:
            u = u+"&event_id="+urllib.quote_plus(event_id)
        if owner_id != None:
            u = u+"&owner_id="+urllib.quote_plus(owner_id)
        liz=xbmcgui.ListItem(name, iconImage=ICON, thumbnailImage=iconimage)
        liz.setInfo( type="Video", infoLabels={ "Title": name } )
        if fanart != None:
            liz.setProperty('fanart_image', fanart)
        else:
            liz.setProperty('fanart_image', FANART)
        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)    
        return ok

