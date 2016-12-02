import re
import os
import sys
import xbmc, xbmcplugin, xbmcgui, xbmcaddon
import json
import string, random
import urllib, urllib2, httplib2
import HTMLParser
import time
import cookielib
import base64
from StringIO import StringIO
import gzip
from datetime import datetime, timedelta


def stringToDate(string, date_format):
    try:
        date = datetime.strptime(str(string), date_format)
    except TypeError:
        date = datetime(*(time.strptime(str(string), date_format)[0:6]))                

    return date

def FIND(source,start_str,end_str):    
    start = source.find(start_str)
    end = source.find(end_str,start+len(start_str))

    if start != -1:        
        return source[start+len(start_str):end]
    else:
        return ''

def GET_RESOURCE_ID():
    #########################
    # Get resource_id
    #########################
    """
    GET http://stream.nbcsports.com/data/mobile/passnbc.xml HTTP/1.1
    Host: stream.nbcsports.com
    Connection: keep-alive
    Accept: */*
    User-Agent: NBCSports/1030 CFNetwork/711.3.18 Darwin/14.0.0
    Accept-Language: en-us
    Accept-Encoding: gzip, deflate
    Connect
    """
    #req = urllib2.Request(ROOT_URL+'passnbc.xml')  
    #req.add_header('User-Agent',  UA_NBCSN)
    #response = urllib2.urlopen(req)        
    #resource_id = response.read()
    #response.close() 
    #resource_id = resource_id.replace('\n', ' ').replace('\r', '')
    resource_id = '<rss version="2.0" xmlns:media="http://search.yahoo.com/mrss/"><channel><title>nbcsports</title><item><title>NBC Sports PGA Event</title><guid>123456789</guid><media:rating scheme="urn:vchip">TV-PG</media:rating></item></channel></rss>'

    return resource_id

def GET_SIGNED_REQUESTOR_ID():

    ##################################################
    # Use this call to get Adobe's Signed ID
    ##################################################
    """
    GET http://stream.nbcsports.com/data/mobile/configuration-2014-RSN-Sections.json HTTP/1.1
    http://stream.nbcsports.com/data/mobile/apps/NBCSports/configuration-ios.json
    Host: stream.nbcsports.com
    Connection: keep-alive
    Accept: */*
    User-Agent: NBCSports/1030 CFNetwork/711.3.18 Darwin/14.0.0
    Accept-Language: en-us
    Accept-Encoding: gzip, deflate
    Connection: keep-alive
    """
    req = urllib2.Request(ROOT_URL+'apps/NBCSports/configuration-ios.json')  
    req.add_header('User-Agent',  UA_NBCSN)
    response = urllib2.urlopen(req)        

    json_source = json.load(response)                       
    response.close() 

    print "ADOBE PASS"
    signed_requestor_id = json_source['adobePassSignedRequestorId']
    signed_requestor_id = signed_requestor_id.replace('\n',"")
    print signed_requestor_id
    
    return signed_requestor_id

def SET_STREAM_QUALITY(url):
    xbmc.log(url)
    '''
    if QUALITY == 0:
        q_lvl = "200000"
        q_lvl_golf = "296k"
    elif QUALITY == 1:
        q_lvl = "400000"
        q_lvl_golf = "496k"
    elif QUALITY == 2:
        q_lvl = "600000"
        q_lvl_golf = "796k"
    elif QUALITY == 3:
        q_lvl = "900000"
        q_lvl_golf = "1296k"
    elif QUALITY == 4:
        q_lvl = "1400000"
        q_lvl_golf = "1896k"
    elif QUALITY == 5:
        q_lvl = "2200000"
        q_lvl_golf = "2596k"
    else:
        q_lvl = "3450000"
        #q_lvl = "4296000"
        q_lvl_golf = "4296k"
    '''


    stream_url = {}
    stream_title = []

    #Open master file a get cookie(s)
    cj = cookielib.LWPCookieJar()
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
    opener.addheaders = [ ("Accept", "*/*"),
                        ("Accept-Encoding", "deflate"),
                        ("Accept-Language", "en-us"),                                                                                                              
                        ("User-Agent", UA_NBCSN)]

    resp = opener.open(url)
    master = resp.read()
    resp.close()  

    cookies = '' 
    for cookie in cj:                    
        if cookies != '':
            cookies = cookies + "; "
        cookies = cookies + cookie.name + "=" + cookie.value
    
    xbmc.log(master)
    xbmc.log(cookies)
    line = re.compile("(.+?)\n").findall(master)  
    
    xplayback = ''.join([random.choice('0123456789ABCDEF') for x in range(32)])
    xplayback = xplayback[0:7]+'-'+xplayback[8:12]+'-'+xplayback[13:17]+'-'+xplayback[18:22]+'-'+xplayback[23:]

    for temp_url in line:
        if '#EXT' not in temp_url:
            temp_url = temp_url.rstrip()
            start = 0
            if 'http' not in temp_url:
                if 'master' in url:
                    start = url.find('master')
                elif 'manifest' in url:
                    start = url.find('manifest')                
            
            if url.find('?') != -1:
                replace_url_chunk = url[start:url.find('?')]    
            else:
                replace_url_chunk = url[start:]    
            
            
            temp_url = url.replace(replace_url_chunk,temp_url)              
            temp_url = temp_url.rstrip() + "|User-Agent=" + UA_NBCSN
            
            
            if '_alid_=' in cookies:                
                temp_url = temp_url + "&Cookie=" + cookies
            
            
            stream_title.append(desc)
            stream_url.update({desc:temp_url})
        else:
            desc = ''
            start = temp_url.find('BANDWIDTH=')
            if start > 0:
                start = start + len('BANDWIDTH=')
                end = temp_url.find(',',start)
                desc = temp_url[start:end]
                try:
                    int(desc)
                    desc = str(int(desc)/1000) + ' kbps'
                except:
                    pass            
    
    
    if len(stream_title) > 0:
        ret =-1      
        stream_title.sort(key=natural_sort_key)  
        print "PLAY BEST SETTING"
        print PLAY_BEST
        if str(PLAY_BEST) == 'true':
            ret = len(stream_title)-1            
        else:
            dialog = xbmcgui.Dialog() 
            ret = dialog.select('Choose Stream Quality', stream_title)
            print ret
        if ret >=0:
            url = stream_url.get(stream_title[ret])           
        else:
            sys.exit()
    else:
        msg = "No playable streams found."
        dialog = xbmcgui.Dialog() 
        ok = dialog.ok('Streams Not Found', msg)

    '''
    url = url.replace('master.m3u8',q_lvl_golf+'/proge.m3u8')       
    url = url.replace('manifest(format=m3u8-aapl-v3)','QualityLevels('+q_lvl+')/Manifest(video,format=m3u8-aapl-v3,audiotrack=audio_en_0)')       
    url = url.replace('manifest(format=m3u8-aapl,filtername=vodcut)','QualityLevels('+q_lvl+')/Manifest(video,format=m3u8-aapl,filtername=vodcut)')
    url = url.replace('manifest(format=m3u8-aapl-v3,filtername=vodcut)','QualityLevels('+q_lvl+')/Manifest(video,format=m3u8-aapl-v3,audiotrack=audio_en_0,filtername=vodcut)')
    '''
    
    print "STREAM URL === " + url 

    return url


def natural_sort_key(s):
    _nsre = re.compile('([0-9]+)')
    return [int(text) if text.isdigit() else text.lower()
            for text in re.split(_nsre, s)] 


def SAVE_COOKIE(cj):
    # Cookielib patch for Year 2038 problem
    # Possibly wrap this in if to check if device is using a 32bit OS
    for cookie in cj:
        # Jan, 1 2038
        if cookie.expires >= 2145916800:
            #Jan, 1 2037
            cookie.expires =  2114380800
    
    cj.save(ignore_discard=True);  


def CLEAR_SAVED_DATA():
    print "IN CLEAR"
    try:
        os.remove(ADDON_PATH_PROFILE+'/device.id')
    except:
        pass
    try:
        os.remove(ADDON_PATH_PROFILE+'/provider.info')
    except:
        pass
    try:
        os.remove(ADDON_PATH_PROFILE+'/cookies.lwp')
    except:
        pass
    try:
        os.remove(ADDON_PATH_PROFILE+'/auth.token')
    except:
        pass
    ADDON.setSetting(id='clear_data', value='false')   



# KODI ADDON GLOBALS
ADDON_HANDLE = int(sys.argv[1])
ROOTDIR = xbmcaddon.Addon(id='plugin.video.nbcsnliveextra').getAddonInfo('path')
ADDON = xbmcaddon.Addon()
ADDON_ID = ADDON.getAddonInfo('id')
ADDON_VERSION = ADDON.getAddonInfo('version')
ADDON_PATH = xbmc.translatePath(ADDON.getAddonInfo('path'))
ADDON_PATH_PROFILE = xbmc.translatePath(ADDON.getAddonInfo('profile'))
KODI_VERSION = float(re.findall(r'\d{2}\.\d{1}', xbmc.getInfoLabel("System.BuildVersion"))[0])
LOCAL_STRING = ADDON.getLocalizedString
FANART = ROOTDIR+"/fanart.jpg"
ICON = ROOTDIR+"/icon.png"
ROOT_URL = 'http://stream.nbcsports.com/data/mobile/'

#Settings file location
settings = xbmcaddon.Addon(id='plugin.video.nbcsnliveextra')

#Main settings
#QUALITY = int(settings.getSetting(id="quality"))
#USER_AGENT = str(settings.getSetting(id="user-agent"))
CDN = int(settings.getSetting(id="cdn"))
USERNAME = str(settings.getSetting(id="username"))
PASSWORD = str(settings.getSetting(id="password"))
PROVIDER = str(settings.getSetting(id="provider"))
CLEAR = str(settings.getSetting(id="clear_data"))
FREE_ONLY = str(settings.getSetting(id="free_only"))
PLAY_MAIN = str(settings.getSetting(id="play_main"))
PLAY_BEST = str(settings.getSetting(id="play_best"))

if CLEAR == 'true':
   CLEAR_SAVED_DATA()

provider_dictionary = { "Bright House" : "Brighthouse",
                        "Cable One" : "auth_cableone_net",
                        "Charter" : "Charter_Direct",
                        "Comcast (xfinity)" : "Comcast_SSO",
                        "Cox" : "Cox",
                        "Dish Network" : "Dish",
                        "Direct TV" : "DTV",
                        "Frontier" : "FRONTIER",    
                        "Optimum" : "Cablevision",
                        "Playstation Vue" : "sony_auth-gateway_net",
                        "Summit Broadband" : "summit-broadband",
                        "Time Warner Cable" : "TWC",
                        "Verizon" : "Verizon"
                    }


MSO_ID = provider_dictionary[PROVIDER]
IDP_URL = 'https://sp.auth.adobe.com/adobe-services/authenticate/saml?domain_name=adobe.com&noflash=true&mso_id='+MSO_ID+'&requestor_id=nbcsports&no_iframe=true&client_type=iOS&client_version=1.10.1&redirect_url=http://adobepass.ios.app/'
ORIGIN = ''
REFERER = ''


#User Agents
UA_IPHONE = 'Mozilla/5.0 (iPhone; CPU iPhone OS 10_0_2 like Mac OS X) AppleWebKit/602.1.50 (KHTML, like Gecko) Mobile/14A456'
UA_PC = 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/43.0.2357.81 Safari/537.36'
UA_ADOBE_PASS = 'AdobePassNativeClient/1.10.1 (iPhone; U; CPU iPhone OS 10.0.2 like Mac OS X; en-us)'
UA_NBCSN = 'AppleCoreMedia/1.0.0.14A456 (iPhone; U; CPU OS 10_0_2 like Mac OS X; en_us)'


#Create Random Device ID and save it to a file
fname = os.path.join(ADDON_PATH_PROFILE, 'device.id')
if not os.path.isfile(fname):
    if not os.path.exists(ADDON_PATH_PROFILE):
        os.makedirs(ADDON_PATH_PROFILE)
    new_device_id = ''.join([random.choice('0123456789abcdef') for x in range(64)])
    device_file = open(fname,'w')   
    device_file.write(new_device_id)
    device_file.close()

fname = os.path.join(ADDON_PATH_PROFILE, 'device.id')
device_file = open(fname,'r') 
DEVICE_ID = device_file.readline()
device_file.close()

#Create a file for storing Provider info
fname = os.path.join(ADDON_PATH_PROFILE, 'provider.info')
if os.path.isfile(fname):    
    provider_file = open(fname,'r')
    last_provider = provider_file.readline()
    provider_file.close()
    if MSO_ID != last_provider:
        CLEAR_SAVED_DATA()

provider_file = open(fname,'w')   
provider_file.write(MSO_ID)
provider_file.close()


#Event Colors
FREE = 'FF43CD80'
LIVE = 'FF00B7EB'
UPCOMING = 'FFFFB266'
FREE_UPCOMING = 'FFCC66FF'