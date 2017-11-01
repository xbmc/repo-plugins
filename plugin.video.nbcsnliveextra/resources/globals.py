import re
import os
import sys
import xbmc, xbmcplugin, xbmcgui, xbmcaddon
import json
import uuid
import hmac
import hashlib
import string, random
import urllib, urllib2
import HTMLParser
import time
import cookielib
import base64
from StringIO import StringIO
import gzip
from datetime import datetime, timedelta
import calendar
from urllib2 import URLError, HTTPError

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
    #resource_id = '<rss version="2.0" xmlns:media="http://search.yahoo.com/mrss/"><channel><title>nbcsports</title><item><title>NBC Sports PGA Event</title><guid>123456789</guid><media:rating scheme="urn:vchip">TV-PG</media:rating></item></channel></rss>'
    resource_id = '<rss version="2.0" xmlns:media="http://search.yahoo.com/mrss/"><channel><title>golf</title><item><title>RSM%20Classic%20-%20Rd%201</title><guid>nbcs_100188</guid><media:rating scheme="urn:v-chip"></media:rating></item></channel></rss>'


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

    signed_requestor_id = json_source['adobePassSignedRequestorId']
    signed_requestor_id = signed_requestor_id.replace('\n',"")


    return signed_requestor_id


def SET_STREAM_QUALITY(url):
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

    xbmc.log(str(master))

    cookies = ''
    for cookie in cj:
        if cookies != '':
            cookies = cookies + "; "
        cookies = cookies + cookie.name + "=" + cookie.value

    line = re.compile("(.+?)\n").findall(master)
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
                if end != -1: desc = temp_url[start:end]
                else: desc = temp_url[start:]
                try:
                    int(desc)
                    desc = str(int(desc)/1000) + ' kbps'
                except:
                    pass

    pref_quality = None
    if 'kbit/s' in QUALITY: pref_quality = int(filter(str.isdigit, QUALITY))

    if len(stream_title) > 0:
        ret =-1
        stream_title.sort(key=natural_sort_key, reverse=True)
        if str(PLAY_BEST) == 'true':
            ret = 0
        elif pref_quality != None:
            index = 0
            dif = 99999999
            for value in stream_title:
                temp_quality = int(filter(str.isdigit, stream_title[index]))
                if abs(temp_quality - pref_quality) < dif:
                    dif = abs(temp_quality - pref_quality)
                    ret = index

                index = index + 1
        else:
            dialog = xbmcgui.Dialog()
            ret = dialog.select('Choose Stream Quality', stream_title)

        if ret >=0:
            url = stream_url.get(stream_title[ret])
        else:
            sys.exit()
    else:
        msg = "No playable streams found."
        dialog = xbmcgui.Dialog()
        ok = dialog.ok('Streams Not Found', msg)

    return url


def natural_sort_key(s):
    _nsre = re.compile('([0-9]+)')
    return [int(text) if text.isdigit() else text.lower()
            for text in re.split(_nsre, s)]


def utc_to_local(utc_dt):
    # get integer timestamp to avoid precision lost
    timestamp = calendar.timegm(utc_dt.timetuple())
    local_dt = datetime.fromtimestamp(timestamp)
    assert utc_dt.resolution >= timedelta(microseconds=1)
    return local_dt.replace(microsecond=utc_dt.microsecond)


def addLink(name,url,title,iconimage,fanart,info=None):
    ok=True
    liz=xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage,)

    liz.setProperty('fanart_image',fanart)
    liz.setProperty("IsPlayable", "true")
    liz.setInfo( type="Video", infoLabels={ "Title": title } )
    if info != None:
        liz.setInfo( type="Video", infoLabels=info)
    ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=url,listitem=liz)
    xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
    return ok

def addFreeLink(name,link_url,iconimage,fanart=None,scrape_type=None,info=None):
    params = get_params()
    ok=True
    u=sys.argv[0]+"?url="+urllib.quote_plus(link_url)+"&mode=6&icon_image="+urllib.quote_plus(iconimage)
    liz=xbmcgui.ListItem(name, iconImage=ICON, thumbnailImage=iconimage)
    liz.setProperty("IsPlayable", "true")
    liz.setInfo( type="Video", infoLabels={ "Title": name } )
    if info != None:
        liz.setInfo( type="Video", infoLabels=info)

    liz.setProperty('fanart_image', fanart)
    ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz)
    xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
    return ok

def addPremiumLink(name,link_url,iconimage,fanart=None,scrape_type=None,info=None):
    params = get_params()
    ok=True
    u=sys.argv[0]+"?url="+urllib.quote_plus(link_url)+"&mode=5&icon_image="+urllib.quote_plus(iconimage)
    liz=xbmcgui.ListItem(name, iconImage=ICON, thumbnailImage=iconimage)
    liz.setProperty("IsPlayable", "true")
    liz.setInfo( type="Video", infoLabels={ "Title": name } )
    if info != None:
        liz.setInfo( type="Video", infoLabels=info)

    liz.setProperty('fanart_image', fanart)
    ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz)
    xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
    return ok


def addDir(name,url,mode,iconimage,fanart=None,scrape_type=None,isFolder=True,info=None):
    params = get_params()
    ok=True
    u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)+"&scrape_type="+urllib.quote_plus(str(scrape_type))+"&icon_image="+urllib.quote_plus(str(iconimage))
    liz=xbmcgui.ListItem(name, iconImage=ICON, thumbnailImage=iconimage)
    liz.setInfo( type="Video", infoLabels={ "Title": name } )
    if info != None:
        liz.setInfo( type="Video", infoLabels=info)

    liz.setProperty('fanart_image', fanart)
    ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=isFolder)
    xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
    return ok


def get_params():
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

# KODI ADDON GLOBALS
ADDON_HANDLE = int(sys.argv[1])
ADDON = xbmcaddon.Addon()
ADDON_ID = ADDON.getAddonInfo('id')
ADDON_VERSION = ADDON.getAddonInfo('version')
ADDON_PATH = xbmc.translatePath(ADDON.getAddonInfo('path'))
ADDON_PATH_PROFILE = xbmc.translatePath(ADDON.getAddonInfo('profile'))
KODI_VERSION = float(re.findall(r'\d{2}\.\d{1}', xbmc.getInfoLabel("System.BuildVersion"))[0])
LOCAL_STRING = ADDON.getLocalizedString
ROOTDIR = xbmcaddon.Addon(id=ADDON_ID).getAddonInfo('path')
FANART = ROOTDIR+"/fanart.jpg"
ICON = ROOTDIR+"/icon.png"
ROOT_URL = 'http://stream.nbcsports.com/data/mobile/'


#Settings file location
settings = xbmcaddon.Addon(id=ADDON_ID)

#Main settings
QUALITY = str(settings.getSetting(id="quality"))
CDN = int(settings.getSetting(id="cdn"))
USERNAME = str(settings.getSetting(id="username"))
PASSWORD = str(settings.getSetting(id="password"))
PROVIDER = str(settings.getSetting(id="provider"))
CLEAR = str(settings.getSetting(id="clear_data"))
FREE_ONLY = str(settings.getSetting(id="free_only"))
PLAY_MAIN = str(settings.getSetting(id="play_main"))
PLAY_BEST = str(settings.getSetting(id="play_best"))

filter_ids = [
            "show-all",
            "nbc-nfl",
            "nbc-premier-league",
            "nbc-nascar",
            "nbc-nhl",
            "nbc-golf",
            "nbc-pga",
            "nbc-nd",
            "nbc-college-football",
            "nbc-f1",
            "nbc-nba",
            "nbc-mlb",
            "nbc-rugby",
            "nbc-horses",
            "nbc-tennis",
            "nbc-indy",
            "nbc-moto",
            "nbc-olympic-sports",
            "nbc-csn-bay-area",
            "nbc-csn-california",
            "nbc-csn-chicago",
            "nbc-csn-mid-atlantic",
            "nbc-csn-new-england",
            "nbc-csn-philadelphia",
            "nbc-sny"
            ]

#Create a filter list
filter_list = []
for fid in filter_ids:
    if str(settings.getSetting(id=fid)) == "true":
        filter_list.append(fid)

#User Agents
UA_NBCSN = 'NBCSports-iOS/9971 CFNetwork/811.5.4 Darwin/16.6.0'


#Create Random Device ID and save it to a file
fname = os.path.join(ADDON_PATH_PROFILE, 'device.id')
if not os.path.isfile(fname):
    if not os.path.exists(ADDON_PATH_PROFILE):
        os.makedirs(ADDON_PATH_PROFILE)
    #new_device_id = ''.join([random.choice('0123456789abcdef') for x in range(64)])
    new_device_id =str(uuid.uuid1())
    device_file = open(fname,'w')
    device_file.write(new_device_id)
    device_file.close()

fname = os.path.join(ADDON_PATH_PROFILE, 'device.id')
device_file = open(fname,'r')
DEVICE_ID = device_file.readline()
device_file.close()


#Event Colors
FREE = 'FF43CD80'
LIVE = 'FF00B7EB'
UPCOMING = 'FFFFB266'
FREE_UPCOMING = 'FFCC66FF'
