#!/usr/bin/python
# -*- coding: utf-8 -*-
#
#     Copyright (C) 2012 mr.olix@gmail.com
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
from BeautifulSoup import BeautifulSoup

# set debug to generate log entries
DEBUG = False
LIBNAME = 'neterra'

'''
class handles html get and post for neterratv website
'''
class neterra:
    #static values
    CLASSNAME = 'neterra'
    COOKIEFILE = 'cookies.lwp'
    PLUGINID = 'plugin.video.neterratv'
    MAINURL = 'http://www.neterra.tv/bg/'
    LOGINURL = 'http://www.neterra.tv/bg/login.php'
    USERAGENT = {'User-agent' : 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'}
    BTVURL = 'http://www.neterra.tv/bg/media.php?id=1&bm=2'
    
    
    #globals
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
called everytime the script runs
'''
    def __init__(self, username, password):
        self.__log('start __init__')
        self.__username__ = username
        self.__password__ = password
        self.initCookie()
        self.openSite(self.BTVURL)        
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
        startpoint = htmlstr.find('<form action="login.php" method="post" id="login" name="login">')
        if (startpoint != -1):
            #if not logged in
            #login
            self.logIn()
            #open page again
            handle = urlopen(req)
            htmlstr = handle.read()
        self.updateCookie()
        self.__log('Finished openSite')
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
        theurl = 'http://www.neterra.tv/bg/login.php'
        self.__log('----URL request started for: ' + theurl + ' ----- ')
        txdata = 'username=' + self.__username__ + '&password=' + self.__password__ + '&submitted=1'
        req = request(self.LOGINURL, txdata, self.USERAGENT)
        self.__log('----URL requested: ' + theurl + ' txdata: ' + txdata)
        # create a request object
        handle = urlopen(req)        
        link = handle.read() 
        self.__log('----URL request finished for: ' + theurl + ' ----- ')
        self.updateCookie()
        #check for string in page 
        #<form action="login.php" method="post" id="login" name="login">
        startpoint = link.find('<form action="login.php" method="post" id="login" name="login">')
        if (startpoint == -1):
            isLoggedIn = True
        self.__log('Finished logIn')
        return isLoggedIn
    
    '''
returns playable link from html stream
''' 
    def getPlayLink(self, html):
        self.__log('Start getPlayLink')
        #find <PARAM NAME="url" VALUE="mms
        startpoint = html.find('<PARAM NAME="url" VALUE="mms')
        self.__log('startpoint: ' + str(startpoint))
        #find next > from start
        endpoint = html.find('>', startpoint)
        self.__log('endpoint: ' + str(endpoint))
        res = html[startpoint:endpoint]
        self.__log('res: ' + str(res))
        startpoint = res.find("mms")
        mmsurl = res[startpoint:len(res) - 1]
        self.__log('Playablelink is mmsurl: ' + mmsurl)
        self.__log('Finished getPlayLink')
        return mmsurl
    '''
returns a soup obejct
'''
    def getTree(self, html):
        self.__log('In getTree')
        return BeautifulSoup(html)
        #return BeautifulSoup(html, convertEntities=BeautifulSoup.HTML_ENTITIES)
        
    '''
    returns list with TV stations from the tabke head_tv_select 
''' 
    def getTVStations(self, html):
        self.__log('Start getTVStations')
        tree = self.getTree(html)
        sections = tree.find('div', {'class': 'head_tv_select'})
        links = sections.findAll('a')
        items = []
        for lnk in links:                    
            items.append((lnk.text.encode('utf-8'), lnk.attrs[1][1]))        
        self.__log('Finished getTVStations')
        return items

    '''
    returns link to TV stream 
''' 
    def getTVStreamLinks(self, html):
        self.__log('Start getTVStreamLink')
        # DOCTYPE is mal formatted. Replace to ensure characters are handled correct by soup        
        html = html.replace('<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN", "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">', '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">')
        i = html.find('table id="mostrecent"')
        #return list
        items = []
        if i > 0:
            tree = self.getTree(html)
           
            # get the links for the table mostrecent  
            sections = tree.find('table', {'id': 'mostrecent'})
            
            #get all the rows
            rows = sections.findAll('tr')
            
            #loop over the rows
            #get TV station name from first cell
            #get links from the next cells
            
            
            #header list
            headers = []
            rowcount = 0
            for row in rows:
                rowcount = rowcount + 1           
                #print "Row:" + row.text
                cells = row.contents
                column = 0
                tvstationname = ''
                #get qualities from table headers and fill header list
                if rowcount == 1:
                    for cell in cells:
                        headers.append(cell.text)
                else:            
                    for cell in cells:                    
                        url = ''
                        text = str(cell)
                        #strip of TD tags
                        if column == 0:
                            # for first cell get the text with name of the station
                            tvstationname = cell.text
                            #print "TV station: " + tvstationname
                            url = ''
                        else:
                            # for all others get the onclick link
                            # example: onclick="playLiveStream('205957', '15',5, '576', '518')        
                            startpoint = text.find('playLiveStream')
                            if startpoint > 1:
                                endpoint = text.find('">', startpoint)
                                text = text[startpoint:endpoint]                
                                text = text.replace("'", '')
                                text = text.replace('playLiveStream', '')
                                text = text.replace('(', '')
                                text = text.replace(')', '')
                                text = text.replace(' ', '')
                                parameters = text.split(",")                            
                                #skip entries for flash player
                                if int(parameters[2])==5:                                
                                    url=''
                                else:
                                    #build the url
                                    # example http://www.neterra.tv/bg/playlivestream.php?epid=94718&q=12&plid=3
                                    url = 'http://www.neterra.tv/bg/playlivestream.php?epid=' + str(parameters[0]) + '&q=' + str(parameters[1]) + '&plid=' + str(parameters[2])                                           
                            else:
                                url = ''                    
                        if len(url) > 1:
                            print 'Columnnr: ' + str(column)
                            items.append([tvstationname+' '+headers[column], url])
                        #increase column number
                        column = column + 1  
        else:
            items.append(['No TV streams found','nix'])
        self.__log('Finished getTVStreamLink')
        return items

        '''
        returns link to recorded series or shows  
    ''' 
    def getTVStationsRecordedList(self, html):
            self.__log('Start getTVStationsRecordedStreamsLinks')
            #replace the DOCTYPE to ensure correct html encoding
            html = html.replace('<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN", "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">', '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">')
            tree = self.getTree(html)            
            items = []
            # check if table exist
            i = html.find('class="predavane_main_holder"')
            if i>0:       
                sections = tree.find('table', {'class': 'predavane_main_holder'})        
                #get all cells
                cells = sections.findAll('td')                
                #loop over cells and fill items
                for cell in cells:
                    if cell.text<>'&nbsp;':
                        items.append([cell.text,cell.a['href']])
                        print 'Cell href: ' + cell.a['href']
            else:
                items.append(['No recorded found','nix'])
            self.__log('Finished getTVStationsRecordedStreamsLinks')
            return items

    '''
    return link to TV stream 
''' 
    def getTVRecordedStreamLinks(self, html):
        self.__log('Start getTVRecordedStreamLinks')
        html = html.replace('<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN", "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">', '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">')
        tree = self.getTree(html)  
        sections = tree.find('table', {'id': 'mostrecent'})
        
        #get all the rows
        rows = sections.findAll('tr')
        
        #loop over the rows
        #get TV station name from first cell
        #get links from the next cells
        #return list
        items = []
        #header list
        headers = []
        rowcount = 0
        for row in rows:
            rowcount = rowcount + 1           
            #print "Row:" + row.text
            cells = row.contents            
            column = 0
            tvstationname = ''
            #get qualities from table headers and fill header list
            if rowcount == 1:
                for cell in cells:
                    headers.append(cell.text.replace('&nbsp;',''))
            else:            
                for cell in cells:                    
                    url = ''
                    text = str(cell)
                    #strip of TD tags
                    if column == 0:
                        # for first cell get the text with name of the station
                        tvstationname = cell.text.replace('&nbsp;','')                                
                        url = ''
                    else:
                        # for all others get the onclick link
                        # example: onclick="playLiveStream('205957', '15',5, '576', '518')        
                        startpoint = text.find('playStream')
                        if startpoint > 1:
                            endpoint = text.find('">', startpoint)
                            text = text[startpoint:endpoint]                
                            text = text.replace("'", '')
                            text = text.replace('playStream', '')
                            text = text.replace('(', '')
                            text = text.replace(')', '')
                            text = text.replace(' ', '')
                            parameters = text.split(",")                            
                            #skip entries for flash player
                            if int(parameters[2])==5:                                
                                url=''
                            else:
                                #build the url
                                # http://www.neterra.tv/bg/playlivestream.php?epid=94718&q=12&plid=3
                                url = 'http://www.neterra.tv/bg/playstream.php?epid=' + str(parameters[0]) + '&q=' + str(parameters[1]) + '&plid=' + str(parameters[2])                                           
                        else:
                            url = ''                    
                    if len(url) > 1:
                        print 'Columnnr: ' + str(column)
                        items.append([tvstationname+' '+headers[column], url])
                    #increase column number
                    column = column + 1        
        self.__log('Finished getTVRecordedStreamLinks')
        return items

'''
Public methods not part of neterra class
'''

def getTVPlayLink(tv_url, tv_username, tv_password):
    log('Start getTVPlayLink')
    #get a neterra class
    Neterra = neterra(tv_username, tv_password)
    log('Finished getTVPlayLink')
    #get a play link for the URL
    return Neterra.getPlayLink(Neterra.openSite(tv_url))


def showTVStations(tv_username, tv_password):
    log('Start showTVStations')
    #get a neterra class
    Neterra = neterra(tv_username, tv_password)
    log('Finished showTVStations')
    #return list of all TV stations
    return Neterra.getTVStations(Neterra.openSite(Neterra.MAINURL))

def getTVStationsStreams(tv_url, tv_username, tv_password):
    log('Start getTVStationsStreams')
    #get a neterra class
    Neterra = neterra(tv_username, tv_password)
    link = Neterra.MAINURL + tv_url    
    log('Finished getTVStationsStreams')
    #return list with all TV station stream for the selected TV station
    return Neterra.getTVStreamLinks(Neterra.openSite(link))

def showTVStationRecorded(tv_url, tv_username, tv_password):
    log('Start showTVStationRecorded')
    #get a neterra class
    Neterra = neterra(tv_username, tv_password)
    link = Neterra.MAINURL + tv_url    
    log('Finished showTVStationRecorded')
    #return list with all TV station stream for the selected TV station
    return Neterra.getTVStationsRecordedList(Neterra.openSite(link))

def showTVStationRecordedStreams(tv_url, tv_username, tv_password):
    log('Start showTVStationRecorded')
    #get a neterra class
    Neterra = neterra(tv_username, tv_password)
    link = Neterra.MAINURL + tv_url    
    log('Finished showTVStationRecorded')
    #return list with all TV station stream for the selected TV station
    return Neterra.getTVRecordedStreamLinks(Neterra.openSite(link))
         
def log(text):
    debug = None
    if (debug == True):
        xbmc.log('%s libname: %s' % (LIBNAME, text))
    else:
        if(DEBUG == True):
            xbmc.log('%s libname: %s' % (LIBNAME, text))
            