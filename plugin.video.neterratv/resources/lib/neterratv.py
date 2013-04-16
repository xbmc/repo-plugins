#!/usr/bin/python
# -*- coding: utf-8 -*-
#
#     Copyright (C) 2013 mr.olix@gmail.com
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program. If not, see <http://www.gnu.org/licenses/>.

from xbmcswift import xbmc, xbmcaddon

import urllib2
import cookielib
import os.path


# set debug to generate log entries
DEBUG = False

#libname
LIBNAME = 'neterratv'

'''
class handles html get and post for neterratv website
'''
class neterra:
    #static values
    CLASSNAME = 'neterra'
    PLUGINID = 'plugin.video.neterratv'
     
    COOKIEFILE = 'cookies.lwp' #file to store cookie information    
    USERAGENT = {'User-agent' : 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'}
    
    LIVE = 'live'
    VOD = 'vod'
    PRODS = 'prods'
    ISSUES = 'issues'
    MUSIC = 'music'
    TIMESHIFT = 'timeshift'
    MOVIES = 'movies'
    GETSTREAM = 'get_stream'
    MAINURL = 'http://www.neterra.tv/' #main url
    LOGINURL = 'http://www.neterra.tv/user/login_page' #login url
    TVLISTURL = 'http://www.neterra.tv/page/service/tv_channels' #url to get list of all TV stations
    CONTENTURL = 'http://www.neterra.tv/content/' #content url
    SMALLICONS = '&choice_view=1'
    USEROPTION = 'change_user_options'
    USEROPTIONLIVE = 'type_view=live&choice_view=1'
    USEROPTIONVOD = 'type_view=vod_prods&choice_view=1' #sets view to small icons
    USEROPTIONVODIUSSUES = 'type_view=vod_issues&choice_view=1' #sets view to small icons
    USEROPTIONMOVIES = 'type_view=movies&choice_view=1' #sets view to small icons
    USEROPTIONMUSIC = 'type_view=music&choice_view=1' #sets view to small icons
    USEROPTIONMUSICISSUES = 'type_view=music_issues&choice_view=1' #sets view to small icons
    USEROPTIONTIMESHIFT = 'type_view=timeshift&choice_view=1' #sets view to small icons
    DEFAULTPOSTSETTINGS = 'offset=0&category=&date=&text=' #default options
    ISLOGGEDINSTR = '<form method="POST" action="http://www.neterra.tv/user/login_page" id="login_fail_form">' #string to check if user is logged in
    
    #flashplayer settings
    SWFBUFFERDEFAULT = 'buffer=3000'        
    SWFPLAYERURL = 'swfUrl=http://www.neterra.tv/players/players/flowplayer/flowplayer.rtmp-3.2.10.swf' #url to flash player
    
    #globals variables
    __cj__ = None
    __cookiepath__ = None
    __isLoggedIn__ = None
    __username__ = None
    __password__ = None    
    
    '''
method for logging
'''
    def __log(self, text):
        debug = None
        if (debug == True):
            xbmc.log('%s class: %s' % (self.CLASSNAME, text))
        else:
            if(DEBUG == True):
                xbmc.log('%s class: %s' % (self.CLASSNAME, text))
            
    '''
default constructor initialize all class variables here
called every time the script runs
'''
    def __init__(self, username, password):
        self.__log('start __init__')
        self.__username__ = username
        self.__password__ = password
        self.initCookie()
        #TODO may remove opening of default URL
        self.openSite(self.MAINURL)        
        self.__log('finished __init__')
        
        '''
init the cookie handle for the class
it loads information from cookie file
'''
    def initCookie(self):
        self.__log('start initCookie')
        addon = xbmcaddon.Addon(self.PLUGINID)
        cookiepath = xbmc.translatePath(addon.getAddonInfo('profile')) 
        cookiepath = cookiepath + self.COOKIEFILE
        cookiepath = xbmc.translatePath(cookiepath)
        #set global
        self.__cookiepath__ = cookiepath
        self.__log('Cookiepath: ' + cookiepath)
        cj = cookielib.LWPCookieJar()
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
        urllib2.install_opener(opener)
        #if exist load file and cookie information 
        if (os.path.isfile(cookiepath)):
            cj.load(cookiepath, False, False)
            self.__log('Cookies loaded from file: ' + cookiepath)
            for index, cookie in enumerate(cj):
                self.__log('cookies come here: ')                
        else:               
            self.__log('No cookie file found at: ' + cookiepath)
        #set global object
        self.__cj__ = cj   
        self.__log('Finished initCookie')
        
        '''
updates the cookie to cookie file
'''
    def updateCookie(self):
        self.__log('Start updateCookie')
        self.__cj__.save(self.__cookiepath__)
        self.__log('Finished updateCookie')
        
        '''
opens url and returns html stream 
also checks if user is logged in
'''
    def openSite(self, url):        
        self.__log('Start openSite')
        urlopen = urllib2.urlopen
        request = urllib2.Request
        theurl = url
        txtdata = ''
        req = request(theurl, txtdata, self.USERAGENT)
        # create a request object
        handle = urlopen(req)
        htmlstr = handle.read()
        startpoint = htmlstr.find(self.ISLOGGEDINSTR)
        #if not logged in
        if (startpoint != -1):            
            #login
            self.logIn()
            #open page again
            handle = urlopen(req)
            htmlstr = handle.read()
        self.updateCookie()
        self.__log('htmlstr: ' + htmlstr)
        self.__log('Finished openSite: ' + theurl)
        return htmlstr

        '''
opens url and returns html stream 
'''
    def openContentStream(self,url,issue_id):        
        self.__log('Start openContentStream')
        urlopen = urllib2.urlopen
        request = urllib2.Request
        theurl = url
        txtdata = issue_id
        self.__log('txtdata:_ ' + txtdata)
        req = request(theurl, txtdata, self.USERAGENT)
        # create a request object
        handle = urlopen(req)
        htmlstr = handle.read()
        startpoint = htmlstr.find(self.ISLOGGEDINSTR)
        #if not logged in
        if (startpoint != -1):            
            #login
            self.logIn()
            #open page again
            handle = urlopen(req)
            htmlstr = handle.read()
        self.updateCookie()
        self.__log('Finished ContenStream: ' + theurl)
        self.__log('htmlstr: ' + htmlstr)
        return htmlstr
    

    '''
login into the neterra tv webpage
returns true if login successful
'''    
    def logIn(self):
        self.__log('Start logIn')
        isLoggedIn = False
        urlopen = urllib2.urlopen
        request = urllib2.Request
        theurl = self.LOGINURL
        self.__log('----URL request started for: ' + theurl + ' ----- ')
        txdata = 'login_username=' + self.__username__ + '&login_password=' + self.__password__ + '&login=1&login_type=1'
        req = request(self.LOGINURL, txdata, self.USERAGENT)
        self.__log('----URL requested: ' + theurl + ' txdata: ' + txdata)
        # create a request object
        handle = urlopen(req)     
        link = handle.read() 
        self.__log(link)
        self.__log('----URL request finished for: ' + theurl + ' ----- ')
        self.updateCookie()
        startpoint = link.find(self.ISLOGGEDINSTR)
        if (startpoint != -1):
            isLoggedIn = True
        self.__log('Finished logIn')        
        return isLoggedIn
        
    '''
    returns list with VOD stations 
''' 
    def getVODStations(self, html):        
        self.__log('Start getVODStations')        
        self.__log('html: ' + html)
        startpoint = html.find('prods')
        endpoint = html.find('count')
        text = html[startpoint:endpoint]
        self.__log('text: ' + text)
        text = text.replace('prods','')
        text = text.replace('count','')
        text = text.replace('[','')
        text = text.replace(']','')
        text = text.replace('{','')
        text = text.replace('}','')
        self.__log('text: ' +  text)
        links = text.split(',')
        items = []
        if links:
            for lnk in links:
                text=lnk
                if (text.find('media_id')!=-1):                                            
                    text = text.replace('"','')
                    text = text.replace(':','')
                    media_id = text.replace('media_id','')                                        
                    self.__log('media_id: ' + media_id)
                if (text.find('media_name')!=-1):                                         
                    text = text.replace('"','')
                    text = text.replace(':','')
                    media_name = text.replace('media_name','')                                       
                    self.__log('media_name: ' + media_name)                                                
                    items.append((media_name.decode('unicode_escape').encode('UTF-8'), media_id))
        else:
            items.append('Error no items found', 'Error')      
        self.__log('Finished getVODStations')
        return items

    '''
    returns list with VOD prods 
''' 
    def getVODProds(self, html):        
        self.__log('Start getVODProds')
        self.__log('html: ' + html)
        startpoint = html.find('prods')
        endpoint = html.find('count')
        text = html[startpoint:endpoint]
        self.__log('text: ' + text)
        text = text.replace('prods','')
        text = text.replace('count','')
        text = text.replace('[','')
        text = text.replace(']','')
        text = text.replace('{','')
        text = text.replace('}','')
        self.__log('text: ' +  text)
        links = text.split(',')
        items = []
        if links:
            for lnk in links:
                text=lnk.encode('utf-8')
                if (text.find('product_id')!=-1):                                            
                    text = text.replace('"','')
                    text = text.replace(':','')
                    product_id = text.replace('product_id','')                                        
                    self.__log('product_id: ' + product_id)
                if (text.find('product_name')!=-1):                      
                    text = text.replace('"','')
                    text = text.replace(':','')
                    product_name = text.replace('product_name','')                                                                               
                    self.__log('product_name: ' + product_name.decode('unicode_escape','ignore').encode('utf-8'))                                    
                    items.append((product_name.decode('unicode_escape','ignore').encode('utf-8'), product_id))
        else:
            items.append('Error no items found', 'Error')      
        self.__log('Finished getVODProds')
        return items

    '''
    returns list with TV stations 
''' 
    def getTVStations(self, html):        
        self.__log('Start getTVStations')
        self.__log('html: ' + html)
        startpoint = html.find('tv_choice_result')        
        endpoint = html.find('"breadcrum_info"')        
        text = html[startpoint:endpoint]
        self.__log('text: ' + text)
        text = text.replace('tv_choice_result','')        
        text = text.replace('"breadcrum_info"','')        
        text = text.replace('[','')
        text = text.replace(']','')
        text = text.replace('{','')
        text = text.replace('}','')
        self.__log('text: ' +  text)
        links = text.split(',')
        items = []
        if links:
            for lnk in links:
                text=lnk.encode('utf-8')                
                if (text.find('"product_name"')!=-1):                      
                    text = text.replace('"','')
                    text = text.replace(':','')
                    product_name = text.replace('product_name','')                                                                               
                if (text.find('issues_id')!=-1):                                            
                    text = text.replace('"','')
                    text = text.replace(':','')
                    issues_id = text.replace('issues_id','')                                        
                    self.__log('issues_id: ' + issues_id)
                    self.__log('product_name: ' + product_name.decode('unicode_escape','ignore').encode('utf-8'))                                    
                    items.append((product_name.decode('unicode_escape','ignore').encode('utf-8'), 'http://www.neterra.tv/content#ignore_list=0&type=live&issue_id='+issues_id))
        else:
            items.append('Error no items found', 'Error')      
        self.__log('Finished getTVStations')
        return items



    '''
    returns list with Music prods 
''' 
    def getMusicProds(self, html):        
        self.__log('Start getMusicProds')
        self.__log('html: ' + html)
        startpoint = html.find('prods')
        endpoint = html.find('count')
        text = html[startpoint:endpoint]
        self.__log('text: ' + text)
        text = text.replace('prods','')
        text = text.replace('count','')
        text = text.replace('[','')
        text = text.replace(']','')
        text = text.replace('{','')
        text = text.replace('}','')
        self.__log('text: ' +  text)
        links = text.split(',')
        items = []
        if links:
            for lnk in links:
                text=lnk.encode('utf-8')
                if (text.find('product_id')!=-1):                                            
                    text = text.replace('"','')
                    text = text.replace(':','')
                    product_id = text.replace('product_id','')                                        
                    self.__log('product_id: ' + product_id)
                if (text.find('product_name')!=-1):                      
                    text = text.replace('"','')
                    text = text.replace(':','')
                    product_name = text.replace('product_name','')                                                                               
                    self.__log('product_name: ' + product_name.decode('unicode_escape','ignore').encode('utf-8'))                                    
                    items.append((product_name.decode('unicode_escape','ignore').encode('utf-8'), product_id))
        else:
            items.append('Error no items found', 'Error')      
        self.__log('Finished getMusicProds')
        return items
    
    '''
    returns list with movie prods 
''' 
    def getMovieProds(self, html):        
        self.__log('Start getMovieProds')
        self.__log('html: ' + html)
        startpoint = html.find('"prods":[[')        
        text = html[startpoint:]
        self.__log('text: ' + text)
        text = text.replace('"prods":','')       
        text = text.replace('[','')
        text = text.replace(']','')
        text = text.replace('{','')
        text = text.replace('}','')
        self.__log('text: ' +  text)
        links = text.split(',')
        items = []
        if links:
            product_name=''
            product_id =''
            for lnk in links:
                text=lnk
                self.__log('Item: ' + text)                                    
                if (text.find('product_id')!=-1):                                            
                    text = text.replace('"','')
                    text = text.replace(':','')
                    product_id = text.replace('product_id','')                                        
                    self.__log('product_id: ' + product_id)
                if (text.find('product_name')!=-1):                      
                    text = text.replace('"','')
                    text = text.replace(':','')
                    product_name = text.replace('product_name','')                                                                               
                    self.__log('product_name: ' + product_name.decode('unicode_escape','ignore').encode('utf-8'))                                    
                    items.append((product_name.decode('unicode_escape','ignore').encode('utf-8'), product_id))
                    product_name=''
                    product_id =''
        else:
            items.append('Error no items found', 'Error')      
            self.__log('Finished getMovieProds')
        return items

    '''
    returns list with timeshift prods 
''' 
    def getTimeshiftProds(self, html):        
        self.__log('Start getTimeshiftProds')
        self.__log('html: ' + html)
        startpoint = html.find('tv_choice_result')        
        text = html[startpoint:]
        self.__log('text: ' + text)
        text = text.replace('tv_choice_result','')
        text = text.replace('"count":0','')
        text = text.replace('[','')
        text = text.replace(']','')
        text = text.replace('{','')
        text = text.replace('}','')
        self.__log('text: ' +  text)
        links = text.split(',')
        items = []
        if links:
            issues_name=''
            issues_id =''
            for lnk in links:
                text=lnk
                self.__log('Item: ' + text)                                    
                if (text.find('issues_name')!=-1):                      
                    text = text.replace('"','')
                    text = text.replace(':','')
                    issues_name = text.replace('issues_name','')                                                                               
                    self.__log('issues_name: ' + issues_name.decode('unicode_escape','ignore').encode('utf-8'))                                    
                if (text.find('issues_id')!=-1):                                            
                    text = text.replace('"','')
                    text = text.replace(':','')
                    issues_id = text.replace('issues_id','')                                        
                    self.__log('issues_id: ' + issues_id)
                    items.append((issues_name.decode('unicode_escape','ignore').encode('utf-8'), issues_id))
                    issues_name=''
                    issues_id =''
        else:
            items.append('Error no items found', 'Error')      
        self.__log('Finished getTimeshiftProds')
        return items


    '''
    returns list with VOD issues 
''' 
    def getVODIssues(self, html):        
        self.__log('Start getVODIssues')
        self.__log('html: ' + html)       
        text = html
        self.__log('text: ' + text)
        text = text.replace('prods":','')
        text = text.replace('count','')
        text = text.replace('[','')
        text = text.replace(']','')
        text = text.replace('{','')
        text = text.replace('}','')
        self.__log('text: ' +  text)
        links = text.split(',')
        items = []
        if links:
            issues_id=''
            issues_url=''
            issues_date_aired=''                
            for lnk in links:
                text=lnk
                if (text.find('issues_id')!=-1):                                            
                    text = text.replace('"','')
                    text = text.replace(':','')
                    issues_id = text.replace('issues_id','')                                        
                    self.__log('issues_id: ' + issues_id)                    
                if (text.find('issues_date_aired')!=-1):                      
                    text = text.replace('"','')
                    text = text.replace(':','')
                    text = text.replace('issues_date_aired','')
                    text = text.replace('null','')
                    issues_date_aired = text                                                           
                    self.__log('issues_date_aired: ' + issues_date_aired)                                      
                if (text.find('issues_url')!=-1):                      
                    text = text.replace('"','')
                    text = text.replace(':','')
                    text = text.replace('issues_url','')
                    issues_url = text.replace('null','')                                       
                    self.__log('issues_url: ' + issues_url.decode('unicode_escape','ignore').encode('utf-8'))
                    #.decode('unicode_escape','ignore').encode('utf-8'))                                    
                    items.append((issues_url.decode('unicode_escape','ignore').encode('utf-8')+' '+issues_date_aired, issues_id))
                    issues_url=''
                    issues_date_aired=''
                    issues_id=''
        else:
            items.append('Error no items found', 'Error')      
        self.__log('Finished getVODIssues')
        return items


    '''
    returns list with music issues 
''' 
    def getMusicIssues(self, html):        
        self.__log('Start getMusicIssues')
        self.__log('html: ' + html)        
        text = html#[startpoint:endpoint]
        self.__log('text: ' + text)
        text = text.replace('prods":','')
        text = text.replace('count','')
        text = text.replace('[','')
        text = text.replace(']','')
        text = text.replace('{','')
        text = text.replace('}','')
        self.__log('text: ' +  text)
        links = text.split(',')
        items = []
        if links:
            issues_id=''
            issues_url=''
            issues_date_aired=''                
            for lnk in links:
                text=lnk
                if (text.find('issues_id')!=-1):                                            
                    text = text.replace('"','')
                    text = text.replace(':','')
                    issues_id = text.replace('issues_id','')                                        
                    self.__log('issues_id: ' + issues_id)                    
                if (text.find('issues_date_aired')!=-1):                      
                    text = text.replace('"','')
                    text = text.replace(':','')
                    text = text.replace('issues_date_aired','')
                    text = text.replace('null','')
                    issues_date_aired = text                                                           
                    self.__log('issues_date_aired: ' + issues_date_aired)                                      
                if (text.find('issues_url')!=-1):                      
                    text = text.replace('"','')
                    text = text.replace(':','')
                    text = text.replace('issues_url','')
                    issues_url = text.replace('null','')                                       
                    self.__log('issues_url: ' + issues_url.decode('unicode_escape','ignore').encode('utf-8'))
                    #.decode('unicode_escape','ignore').encode('utf-8'))                                    
                    items.append((issues_url.decode('unicode_escape','ignore').encode('utf-8')+' '+issues_date_aired, issues_id))
                    issues_url=''
                    issues_date_aired=''
                    issues_id=''
        else:
            items.append('Error no items found', 'Error')      
        self.__log('Finished getMusicIssues')
        return items

    '''
    returns list with movie issues 
''' 
    def getMovieIssues(self, html):        
        self.__log('Start getMovieIssues')
        self.__log('html: ' + html)       
        text = html
        self.__log('text: ' + text)
        text = text.replace('prods":','')
        text = text.replace('count','')
        text = text.replace('[','')
        text = text.replace(']','')
        text = text.replace('{','')
        text = text.replace('}','')
        self.__log('text: ' +  text)
        links = text.split(',')
        items = []
        if links:
            issues_id=''
            issues_url=''
            issues_date_aired=''                
            for lnk in links:
                text=lnk
                if (text.find('issues_id')!=-1):                                            
                    text = text.replace('"','')
                    text = text.replace(':','')
                    issues_id = text.replace('issues_id','')                                        
                    self.__log('issues_id: ' + issues_id)                    
                if (text.find('issues_date_aired')!=-1):                      
                    text = text.replace('"','')
                    text = text.replace(':','')
                    text = text.replace('issues_date_aired','')
                    text = text.replace('null','')
                    issues_date_aired = text                                                           
                    self.__log('issues_date_aired: ' + issues_date_aired)                                      
                if (text.find('issues_url')!=-1):                      
                    text = text.replace('"','')
                    text = text.replace(':','')
                    text = text.replace('issues_url','')
                    issues_url = text.replace('null','')                                       
                    self.__log('issues_url: ' + issues_url.decode('unicode_escape','ignore').encode('utf-8'))
                    #.decode('unicode_escape','ignore').encode('utf-8'))                                    
                    items.append((issues_url.decode('unicode_escape','ignore').encode('utf-8')+' '+issues_date_aired, issues_id))
                    issues_url=''
                    issues_date_aired=''
                    issues_id=''
        else:
            items.append('Error no items found', 'Error')      
        self.__log('Finished getMovieIssues')
        return items
  
    '''
    returns the stream to live TV
'''
    def getTVStream(self,url):
        self.__log('Start getTVStream')
        #parse url for id
        self.__log('url: ' + url)
        startpoint = url.rfind('issue_id=')
        #remove / from string
        text = url[startpoint:len(url)]             
        self.__log('text: ' + text)   
        self.logIn()
        #stream = self.openContentStream(self.CONTENTSTREAMURL,text)
        stream = self.openContentStream(self.CONTENTURL+self.GETSTREAM,text)
        self.__log('Finished getTVStream')
        return stream
    
    def getIssueStream(self,url):
        self.__log('Start getIssueStream')
        #parse url for id
        self.__log('url: ' + url)        
        text = 'issue_id='+url             
        self.__log('text: ' + text)   
        self.logIn()
        stream = self.openContentStream(self.CONTENTURL+self.GETSTREAM,text)
        self.__log('Finished getIssueStream')
        return stream
'''
    end of neterratv class
'''

'''
    Public methods in lib neterra 
    Note: These methods are not part of the neterratv class
'''
   

'''
    plays live stream
'''
def playLiveStream(tv_username, tv_password, url):
    log('Start playLiveStream')
    #get a neterra class
    Neterra = neterra(tv_username, tv_password)    
    html=Neterra.getTVStream(url)
    log(html)
    #parse html for flashplayer link
    startpoint = html.find('rtmp')
    endpoint = html.find('file_link')-3
    #remove crap from string
    rtmp = html[startpoint:endpoint]                
    rtmp = rtmp.replace('\\','')    
    startpoint = html.find('file_link')+len('file_link')+3
    endpoint = html.find(',',startpoint)-1
    playpath = html[startpoint:endpoint]
    #log some details
    log('playpath: ' + playpath)
    log('rtmp: ' + rtmp)        
    #url=rtmp+' '+ neterra.SWFPLAYERURL+' playpath='+playpath+' live=1 '+neterra.SWFBUFFERDEFAULT +' conn=O:1 conn=NN:capabilities:239 conn=O:1 conn=NN:audioCodecs:3575 conn=O:1 conn=NN:videoCodecs:252 conn=O:1 conn=NN:videoFunction:1 conn=O:1 conn=NN:objectEncoding:3 conn=O:1 conn=NS:flashVer:3:WIN 11,6,602,180' #conn=O:0'
    url=rtmp+' '+ neterra.SWFPLAYERURL+' playpath='+playpath+' live=1 '+neterra.SWFBUFFERDEFAULT
    #call player
    xbmc.Player().play(url)
    log('URL: ' + url)
    log('Finished playLiveStream')
    html=''
    return html

'''
    play issue stream
'''
def playIssueStream(tv_username, tv_password, url):
    log('Start playIssueStream')
    #get a neterra class
    Neterra = neterra(tv_username, tv_password)    
    html=Neterra.getIssueStream(url)
    log(html)
    #parse html for flashplayer link
    startpoint = html.find('rtmp')
    endpoint = html.find('file_link')-3
    #remove / from string
    rtmp = html[startpoint:endpoint]                
    rtmp = rtmp.replace('\\','')
    startpoint = rtmp.find('/vod')
    endpoint = len(rtmp)
    app = rtmp[startpoint+1:endpoint]
    startpoint = html.find('file_link')+len('file_link')+3
    endpoint = html.find(',',startpoint)-1
    playpath = html[startpoint:endpoint]
    playpath = playpath.replace('\\','')
    tcUrl = rtmp
    #log some details
    log('playpath: ' + playpath)
    log('rtmp: ' + rtmp)
    log('app: ' +app)
    log('tcUrl: '+tcUrl)
    #ensure app name is given as there rtmplib has problems to parse information from rtmp string
    url=rtmp+' app='+app+' tcUrl='+tcUrl+' '+neterra.SWFPLAYERURL+' playpath='+playpath+' live=0 ' + neterra.SWFBUFFERDEFAULT
    #call player
    xbmc.Player().play(url)
    log('URL: ' + url)
    log('Finished playIssueStream')
    html=''
    return html

'''
    returns list of all live TV stations
'''
def showTVStations(tv_username, tv_password):
    log('Start showTVStations')
    #get a neterra class
    Neterra = neterra(tv_username, tv_password)
    log('Finished showTVStations')
    Neterra.openContentStream(neterra.CONTENTURL+neterra.USEROPTION,neterra.USEROPTIONLIVE)
    #return list of all TV stations
    return Neterra.getTVStations(Neterra.openContentStream(neterra.CONTENTURL+neterra.LIVE,neterra.DEFAULTPOSTSETTINGS))

'''
    returns list of all TV stations that provide VOD's
'''
def showVODStations(tv_username, tv_password):
    log('Start showVODVStations')
    #get a neterra class
    Neterra = neterra(tv_username, tv_password)
    #call the URL to switch userview to small icons    
    Neterra.openContentStream(neterra.CONTENTURL+neterra.USEROPTION,neterra.USEROPTIONVOD)
    log('Finished showVODTVStations')
    #return list of all VOD TV's
    return Neterra.getVODStations(Neterra.openContentStream(neterra.CONTENTURL+neterra.VOD,neterra.DEFAULTPOSTSETTINGS))


'''
    returns list of available Music products
'''
def showMusicProds(tv_username, tv_password):
    log('Start showMusicProds')
    #get a neterra class
    Neterra = neterra(tv_username, tv_password)
    Neterra.openContentStream(neterra.CONTENTURL+neterra.USEROPTION,neterra.USEROPTIONMUSIC)
    log('Finished showMusicProds')
    #return list of all prods for music
    return Neterra.getMusicProds(Neterra.openContentStream(neterra.CONTENTURL+neterra.MUSIC,neterra.DEFAULTPOSTSETTINGS))

'''
    returns list of available timeshift products
'''
def showTimeshiftProds(tv_username, tv_password):
    log('Start showTimeshiftProds')
    #get a neterra class
    Neterra = neterra(tv_username, tv_password)
    Neterra.openContentStream(neterra.CONTENTURL+neterra.USEROPTION,neterra.USEROPTIONTIMESHIFT)
    log('Finished showTimeshiftProds')
    #return list of all prods for music
    return Neterra.getTimeshiftProds(Neterra.openContentStream(neterra.CONTENTURL+neterra.TIMESHIFT,neterra.DEFAULTPOSTSETTINGS))

'''
    returns list of available movie products
'''
def showMovieProds(tv_username, tv_password):
    log('Start showMovieProds')
    #get a neterra class
    Neterra = neterra(tv_username, tv_password)    
    Neterra.openContentStream(neterra.CONTENTURL+neterra.USEROPTION,neterra.USEROPTIONMOVIES)
    log('Finished showMovieProds')
    return Neterra.getMovieProds(Neterra.openContentStream(neterra.CONTENTURL+neterra.MOVIES,neterra.DEFAULTPOSTSETTINGS))

'''
    returns list of available VOD products like shows or series for selected_ID (prod ID)
'''
def showVODProds(selected_ID,tv_username, tv_password):
    log('Start showVODProds')
    #get a neterra class
    Neterra = neterra(tv_username, tv_password)
    Neterra.openContentStream(neterra.CONTENTURL+neterra.USEROPTION,neterra.USEROPTIONVOD)
    log('Finished showVODProds')
    #return list of all prods for VOD
    return Neterra.getVODProds(Neterra.openContentStream(neterra.CONTENTURL+neterra.PRODS,neterra.DEFAULTPOSTSETTINGS+'&id='+selected_ID))

'''
    returns list of available issues for the selected_ID (issue id)
'''
def showVODIssues(selected_ID,tv_username, tv_password):
    log('Start showVODIssues')
    #get a neterra class
    Neterra = neterra(tv_username, tv_password)
    Neterra.openContentStream(neterra.CONTENTURL+neterra.USEROPTION,neterra.USEROPTIONVODIUSSUES)
    log('Finished showVODIssues')
    #return list of all prods for VOD
    return Neterra.getVODIssues(Neterra.openContentStream(neterra.CONTENTURL+neterra.ISSUES,neterra.DEFAULTPOSTSETTINGS+'&id='+selected_ID))

'''
    returns list of available issues for the selected_ID (issue id)
'''
def showMusicIssues(selected_ID,tv_username, tv_password):
    log('Start showMusicIssues')
    #get a neterra class
    Neterra = neterra(tv_username, tv_password)
    Neterra.openContentStream(neterra.CONTENTURL+neterra.USEROPTION,neterra.USEROPTIONMUSICISSUES)
    log('Finished showMusicIssues')
    #return list of all prods for VOD
    return Neterra.getMusicIssues(Neterra.openContentStream(neterra.CONTENTURL+neterra.ISSUES,neterra.DEFAULTPOSTSETTINGS+'&id='+selected_ID))

'''
    returns list of available issues for the selected_ID (issue id)
'''
def showMovieIssues(selected_ID,tv_username, tv_password):
    log('Start showMovieIssues')
    #get a neterra class
    Neterra = neterra(tv_username, tv_password)    
    log('Finished showMovieIssues')
    #return list of all prods for VOD
    return Neterra.getMovieIssues(Neterra.openContentStream(neterra.CONTENTURL+neterra.ISSUES,neterra.DEFAULTPOSTSETTINGS+'&id='+selected_ID))

'''
    public log method
'''         
def log(text):
    debug = None
    if (debug == True):
        xbmc.log('%s libname: %s' % (LIBNAME, text))
    else:
        if(DEBUG == True):
            xbmc.log('%s libname: %s' % (LIBNAME, text))
            