#!/usr/bin/python
# -*- coding: utf-8 -*-

import urllib
import urllib2
import os
import sys
import socket
import xbmc
import xbmcgui
import xbmcaddon
import xbmcplugin
import xbmcvfs
import time
import datetime
import json
import re

from dateutil import parser

__addon__ = xbmcaddon.Addon()
__addonID__ = __addon__.getAddonInfo('id')
__addonname__ = __addon__.getAddonInfo('name')
__version__ = __addon__.getAddonInfo('version')
__path__ = __addon__.getAddonInfo('path')
__profiles__ = __addon__.getAddonInfo('profile')
__LS__ = __addon__.getLocalizedString

HOME = xbmcgui.Window(10000)
OSD = xbmcgui.Dialog()

EPOCH = datetime.datetime(1970, 1, 1)
RSS_TIME_FORMAT = '%Y-%m-%d %H:%M:%S'

__xml__ = xbmc.translatePath('special://skin').split(os.sep)[-2] + '.script-gto-info.xml'

__usertranslations__ = xbmc.translatePath(os.path.join(__profiles__, 'ChannelTranslate.json'))

__prefer_hd__ = True if __addon__.getSetting('prefer_hd').upper() == 'TRUE' else False
__enableinfo__ = True if __addon__.getSetting('enableinfo').upper() == 'TRUE' else False
__pvronly__ = True if __addon__.getSetting('pvronly').upper() == 'TRUE' else False
__preferred_scraper__ = __addon__.getSetting('scraper')

mod = __import__(__preferred_scraper__, locals(), globals(), fromlist=['Scraper'])
Scraper = getattr(mod, 'Scraper')

# Helpers

def getScraperIcon(icon):
    return xbmc.translatePath(os.path.join(__path__, 'resources', 'lib', 'media', icon))

def notifyOSD(header, message, icon=xbmcgui.NOTIFICATION_INFO, disp=4000, enabled=__enableinfo__):
    if enabled:
        OSD.notification(header.encode('utf-8'), message.encode('utf-8'), icon, disp)

def writeLog(message, level=xbmc.LOGDEBUG):
        try:
            xbmc.log('[%s %s]: %s' % (__addonID__, __version__,  message.encode('utf-8')), level)
        except Exception:
            xbmc.log('[%s %s]: %s' % (__addonID__, __version__,  'Fatal: Message could not displayed'), xbmc.LOGERROR)

# End Helpers

if not os.path.isfile(__usertranslations__):
    xbmcvfs.copy(xbmc.translatePath(os.path.join(__path__, 'ChannelTranslate.json')), __usertranslations__)

writeLog('Getting PVR translations from %s' % (__usertranslations__), xbmc.LOGDEBUG)
with open(__usertranslations__, 'r') as transfile:
    ChannelTranslate=transfile.read().rstrip('\n')

infoprops = ['Title', 'Picture', 'Subtitle', 'Description', 'Channel', 'ChannelID', 'Logo', 'Date', 'StartTime', 'RunTime', 'EndTime', 'Genre', 'Cast', 'isRunning', 'isInFuture', 'isInDB', 'dbTitle', 'dbOriginalTitle', 'Fanart', 'dbTrailer', 'dbRating', 'dbUserRating', 'BroadcastID', 'hasTimer', 'BlobID']

# convert HTML Entities to unicode chars

entities = {'&lt;':'<', '&gt;':'>', '&nbsp;':' ', '&amp;':'&', '&quot;':'"'}
tags = {'<br/>':' ', '<hr/>': ''}

def entity2unicode(text):
    for entity in entities.iterkeys():
        text = text.replace(entity, entities[entity])

    # 2nd pass to eliminate html like '<br/>'

    for tag in tags.iterkeys():
        text = text.replace(tag, tags[tag])
    return text

# get remote URL, replace '\' and optional split into css containers

def getUnicodePage(url, container=None):
    try:
        req = urllib2.urlopen(url.encode('utf-8'), timeout=30)
    except UnicodeDecodeError:
        req = urllib2.urlopen(url)

    except ValueError:
        return False
    except urllib2.URLError, e:
        writeLog(str(e.reason), xbmc.LOGERROR)
        return False
    except socket.timeout:
        writeLog('Socket timeout', xbmc.LOGERROR)
        return False

    encoding = 'utf-8'
    if "content-type" in req.headers and "charset=" in req.headers['content-type']:
        encoding=req.headers['content-type'].split('charset=')[-1]
    content = unicode(req.read(), encoding).replace("\\", "")
    if container is None: return content
    return content.split(container)

# get parameter hash, convert into parameter/value pairs, return dictionary

def ParamsToDict(parameters):
    paramDict = {}
    if parameters:
        paramPairs = parameters.split("&")
        for paramsPair in paramPairs:
            paramSplits = paramsPair.split('=')
            if (len(paramSplits)) == 2:
                paramDict[paramSplits[0]] = paramSplits[1]
    return paramDict

# get used dateformat of kodi

def getDateFormat():
    df = xbmc.getRegion('dateshort')
    tf = xbmc.getRegion('time').split(':')

    try:
        # time format is 12h with am/pm
        return df + ' ' + tf[0][0:2] + ':' + tf[1] + ' ' + tf[2].split()[1]
    except IndexError:
        # time format is 24h with or w/o leading zero
        return df + ' ' + tf[0][0:2] + ':' + tf[1]

# determine and change scraper modules

def changeScraper():
    _scraperdir = xbmc.translatePath(os.path.join(__path__, 'resources', 'lib'))
    _scrapers = []
    _scraperdict = []
    for module in os.listdir(_scraperdir):
        if module in ('__init__.py') or module[-3:] != '.py': continue
        writeLog('Found Scraper Module %s' % (module))
        mod = __import__('resources.lib.%s' % (module[:-3]), locals(), globals(), fromlist=['Scraper'])
        ScraperClass = getattr(mod, 'Scraper')

        if not ScraperClass().enabled: continue

        _scrapers.append(ScraperClass().friendlyname)
        _scraperdict.append({'name': ScraperClass().friendlyname, 'shortname': ScraperClass().shortname, 'module': 'resources.lib.%s' % (module[:-3])})

    _idx = xbmcgui.Dialog().select(__LS__(30111), _scrapers)
    if _idx > -1:
        writeLog('selected scrapermodule is %s' % (_scraperdict[_idx]['module']))
        __addon__.setSetting('scraper', _scraperdict[_idx]['module'])
        __addon__.setSetting('setscraper', _scraperdict[_idx]['shortname'])

# convert datetime string to timestamp with workaround python bug (http://bugs.python.org/issue7980) - Thanks to BJ1

def date2timeStamp(date, format):
    try:
        dtime = datetime.datetime.strptime(date, format)
    except TypeError:
        try:
            dtime = datetime.datetime.fromtimestamp(time.mktime(time.strptime(date, format)))
        except ValueError:
            return False
    except Exception:
        return False
    return int(time.mktime(dtime.timetuple()))


def utc_to_local_datetime(utc_datetime):
    delta = utc_datetime - EPOCH
    utc_epoch = 86400 * delta.days + delta.seconds
    time_struct = time.localtime(utc_epoch)
    dt_args = time_struct[:6] + (delta.microseconds,)
    return datetime.datetime(*dt_args)

# get pvr channelname, translate from Scraper to pvr channelname if necessary

def channelName2pvrId(channelname):
    query = {
            "jsonrpc": "2.0",
            "method": "PVR.GetChannels",
            "params": {"channelgroupid": "alltv"},
            "id": 1
            }
    res = json.loads(xbmc.executeJSONRPC(json.dumps(query, encoding='utf-8')))

    # translate via json if necessary
    translations = json.loads(str(ChannelTranslate))
    for translation in translations:
        for names in translation['name']:
            if channelname.lower() == names.lower():
                writeLog("Translating %s to %s" % (channelname, translation['pvrname']))
                channelname = translation['pvrname']
                break
    
    if 'result' in res and 'channels' in res['result']:
        res = res['result'].get('channels')
        for channels in res:

            # prefer HD Channel if available
            if __prefer_hd__ and  (channelname + " HD").lower() == channels['label'].lower():
                writeLog("GTO found HD priorized channel %s" % (channels['label']))
                return channels['channelid']

            if channelname.lower() == channels['label'].lower():
                writeLog("GTO found channel %s" % (channels['label']))
                return channels['channelid']
    return False

# get pvr channelname by id

def getPvrChannelName(channelid, fallback):
    query = {
            "jsonrpc": "2.0",
            "method": "PVR.GetChannels",
            "params": {"channelgroupid": "alltv"},
            "id": 1
            }
    res = json.loads(xbmc.executeJSONRPC(json.dumps(query, encoding='utf-8')))
    if 'result' in res and 'channels' in res['result']:
        res = res['result'].get('channels')
        for channels in res:
            if channels['channelid'] == channelid:
                writeLog("GTO found id for channel %s" % (channels['label']))
                return channels['label']
    return fallback + '*'

# get pvr channel logo url

def getStationLogo(channelid, fallback):
    query = {
            "jsonrpc": "2.0",
            "method": "PVR.GetChannelDetails",
            "params": {"channelid": channelid, "properties": ["thumbnail"]},
            "id": 1
            }
    res = json.loads(xbmc.executeJSONRPC(json.dumps(query, encoding='utf-8')))
    if 'result' in res and 'channeldetails' in res['result'] and 'thumbnail' in res['result']['channeldetails']:
        return urllib.unquote_plus(res['result']['channeldetails']['thumbnail']).split('://', 1)[1][:-1]
    else:
        return fallback

def switchToChannel(pvrid):
    '''
    :param pvrid:       str PVR-ID of the broadcast station
    :return:            none
    '''
    writeLog('Switch to channel id %s' % (pvrid))
    query = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "Player.Open",
        "params": {"item": {"channelid": int(pvrid)}}
        }
    res = json.loads(xbmc.executeJSONRPC(json.dumps(query, encoding='utf-8')))
    if 'result' in res and res['result'] == 'OK':
        writeLog('Successfull switched to channel id %s' % (pvrid))
    else:
        writeLog('Couldn\'t switch to channel id %s' % (pvrid))


def getRecordingCapabilities(pvrid, datetime2):
    '''
    :param pvrid:       str PVR-ID of the broadcast station
    :param datetime2:   str datetime in TIME_FORMAT e.g. '2017-07-20 20:15:00'
    :return:            dict: int unique broadcastID of the broadcast or None, bool hastimer
    '''
    params = {'broadcastid': None, 'hastimer': False}
    if not pvrid: return params
    query = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "PVR.GetBroadcasts",
        "params": {"channelid": pvrid,
                   "properties": ["title", "starttime", "hastimer"]}
    }
    res = json.loads(xbmc.executeJSONRPC(json.dumps(query, encoding='utf-8')))
    if 'result' in res and 'broadcasts' in res['result']:
        for broadcast in res['result']['broadcasts']:
            _ltt = utc_to_local_datetime(parser.parse(broadcast['starttime'])).strftime(RSS_TIME_FORMAT)
            # writeLog('%s: %s' % (_lt, broadcast['title']))
            if _ltt == datetime2:
                params.update({'broadcastid': broadcast['broadcastid'], 'hastimer': broadcast['hastimer']})
    return params


def setTimer(broadcastId, blobId):
    '''
    :param broadcastId: str unique broadcastID of the broadcast
    :return:            none
    '''
    query = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "PVR.AddTimer",
        "params": {"broadcastid": int(broadcastId)}
    }
    res = json.loads(xbmc.executeJSONRPC(json.dumps(query, encoding='utf-8')))
    if 'result' in res and res['result'] == 'OK':
        writeLog('Timer of blob #%s successful added' % (blobId))
        blob = eval(HOME.getProperty('GTO.%s' % (blobId)))
        blob.update(getRecordingCapabilities(blob['pvrid'], blob['datetime2']))
        HOME.setProperty('GTO.%s' % (blobId), str(blob))
        HOME.setProperty('GTO.timestamp', str(int(time.time()) / 5))
    else:
        writeLog('Timer couldn\'t set', xbmc.LOGFATAL)


def isInDataBase(title):
    '''
    search for a title if already present in database, search with different fuzzy parameters in 4 steps:
    1. match exact
    2. match contains
    3. replace all occurences of ' - ' with ': ' (planet of the apes - revolution -> planet of the apes: revolution), match contains
    4. split title on ':' and '-', search first part (planet of the apes), match contains

    :param title:       str title of broadcast e.g. 'Planet of the apes - Revolution'
    :return:            dictionary {'isInDB': 'no'} or {'isInDB': 'yes', 'title: 'originaltitle': 'fanart': 'trailer': 'rating': 'userrating':}
    '''
    writeLog('Check if \'%s\' is in database' % (title))

    titlepart = re.findall('[:-]', title)
    params = {'isInDB': False}
    query = {"jsonrpc": "2.0", "id": 1, "method": "VideoLibrary.GetMovies"}
    rpcQuery = [{"params": {"properties": ["title", "originaltitle", "fanart", "trailer", "rating", "userrating"],
                       "sort": {"method": "label"},
                       "filter": {"field": "title", "operator": "is", "value": title}}},
                {"params": {"properties": ["title", "originaltitle", "fanart", "trailer", "rating", "userrating"],
                       "sort": {"method": "label"},
                       "filter": {"field": "title", "operator": "contains", "value": title}}},
                {"params": {"properties": ["title", "originaltitle", "fanart", "trailer", "rating", "userrating"],
                       "sort": {"method": "label"},
                       "filter": {"field": "title", "operator": "contains", "value": title.replace(' - ', ': ')}}}]
    if len(titlepart) > 0:
        rpcQuery.append({"params": {"properties": ["title", "originaltitle", "fanart", "trailer", "rating", "userrating"],
                       "sort": {"method": "label"},
                       "filter": {"field": "title", "operator": "contains", "value": title.split(titlepart[0])[0].strip()}}})

    for i in range(0, len(rpcQuery) + 1):
        if i == 0:
            writeLog('Try exact matching of search pattern')
            query.update(rpcQuery[i])
        elif i == 1:
            writeLog('No movie(s) with exact pattern found, try fuzzy filters')
            if len(title.split()) < 3:
                writeLog('Word count to small for fuzzy filters')
                return params
        elif i == 2:
            writeLog('No movie(s) with similar pattern found, replacing special chars')
        elif i == 3:
            writeLog('Split title into titleparts')
            if len(titlepart) == 0:
                writeLog('Sorry, splitting isn\'t possible')
                return params
            writeLog('Search for \'%s\'' % (title.split(titlepart[0])[0].strip()))
        else:
            writeLog('Sorry, no matches')
            return params

        query.update(rpcQuery[i])
        res = json.loads(xbmc.executeJSONRPC(json.dumps(query, encoding='utf-8')))
        if 'movies' in res['result']: break

    writeLog('Found %s matches for movie(s) in database, select first' % (len(res['result']['movies'])))

    try:
        _fanart = urllib.unquote_plus(res['result']['movies'][0]['fanart']).split('://', 1)[1][:-1]
    except IndexError:
        writeLog('Fanart: %s' % (urllib.unquote_plus(res['result']['movies'][0]['fanart'])))
        _fanart = ''

    _userrating = '0'
    if res['result']['movies'][0]['userrating'] != '': _userrating = res['result']['movies'][0]['userrating']
    params.update({'isInDB': True,
                   'db_title': unicode(res['result']['movies'][0]['title']),
                   'db_originaltitle': unicode(res['result']['movies'][0]['originaltitle']),
                   'db_fanart': unicode(_fanart),
                   'db_trailer': unicode(res['result']['movies'][0]['trailer']),
                   'db_rating': round(float(res['result']['movies'][0]['rating']), 1),
                   'db_userrating': int(_userrating)})
    return params

# clear all info properties (info window) in Home Window

def clearInfoProperties():
    writeLog('clear all info properties (used in info popup)')
    for property in infoprops:
        HOME.clearProperty('GTO.Info.%s' % (property))

def refreshWidget(handle=None, notify=__enableinfo__):

    blobs = int(HOME.getProperty('GTO.blobs') or '0') + 1
    notifyOSD(__LS__(30010), __LS__(30109) % ((Scraper().shortname).decode('utf-8')), icon=getScraperIcon(Scraper().icon), enabled=notify)

    widget = 1
    for i in range(1, blobs, 1):

        writeLog('Processing blob GTO.%s for widget #%s' % (i, widget))
        blob = eval(HOME.getProperty('GTO.%s' % (i)))

        if __pvronly__ and not blob['pvrid']:
            writeLog("Channel %s is not in PVR, discard entry" % (blob['channel']))
            HOME.setProperty('PVRisReady', 'no')
            continue

        HOME.setProperty('PVRisReady', 'yes')

        wid = xbmcgui.ListItem(label=blob['title'], label2=blob['pvrchannel'])
        wid.setInfo('video', {'title': blob['title'], 'genre': blob['genre'], 'plot': blob['plot'],
                              'cast': blob['cast'].split(','), 'duration': int(blob['runtime'])*60})
        wid.setArt({'thumb': blob['thumb'], 'logo': blob['logo']})

        wid.setProperty('DateTime', blob['datetime'])
        wid.setProperty('StartTime', blob['datetime'].split()[1][0:5])
        wid.setProperty('EndTime', blob['enddate'].split()[1][0:5])
        wid.setProperty('ChannelID', str(blob['pvrid']))
        wid.setProperty('BlobID', str(i))
        wid.setProperty('isInDB', str(blob['isInDB']))
        if blob['isInDB']:
            wid.setProperty('dbTitle', blob['db_title'])
            wid.setInfo('video', {'originaltitle': blob['db_originaltitle'],
                                  'trailer': blob['db_trailer'], 'rating': blob['db_rating'],
                                  'userrating': blob['db_userrating']})
            wid.setArt({'fanart': blob['db_fanart']})

        if handle is not None: xbmcplugin.addDirectoryItem(handle=handle, url='', listitem=wid)
        widget += 1

    if handle is not None:
        xbmcplugin.endOfDirectory(handle=handle, updateListing=True)

        HOME.setProperty('GTO.timestamp', str(int(time.time()) / 5))
    xbmc.executebuiltin('Container.Refresh')

def scrapeGTOPage(enabled=__enableinfo__):

    data = Scraper()
    data.err404 = xbmc.translatePath(os.path.join(__path__, 'resources', 'lib', 'media', data.err404))

    notifyOSD(__LS__(30010), __LS__(30018) % ((data.shortname).decode('utf-8')), icon=getScraperIcon(data.icon), enabled=enabled)
    writeLog('Start scraping from %s' % (data.rssurl))

    content = getUnicodePage(data.rssurl, container=data.selector)
    if not content: return

    blobs = int(HOME.getProperty('GTO.blobs') or '0') + 1
    for idx in range(1, blobs, 1):
        HOME.clearProperty('GTO.%s' % (idx))

    idx = 1
    content.pop(0)

    HOME.setProperty('GTO.blobs', '0')
    HOME.setProperty('GTO.provider', data.shortname)
    
    for container in content:

        data.scrapeRSS(container)

        pvrid = channelName2pvrId(data.channel)
        logoURL = getStationLogo(pvrid, data.err404)
        channel = getPvrChannelName(pvrid, data.channel)
        details = getUnicodePage(data.detailURL)

        writeLog('Scraping details from %s' % (data.detailURL))
        data.scrapeDetailPage(details, data.detailselector)

        now = datetime.datetime.now()
        end = parser.parse(data.enddate)

        if end < now:
            writeLog('Broadcast has finished already, discard blob')
            continue

        _datetime = datetime.datetime.strftime( parser.parse(data.startdate), getDateFormat())
        blob = {
                'title': unicode(entity2unicode(data.title)),
                'thumb': unicode(data.thumb),
                'datetime': _datetime,
                'datetime2': data.startdate,
                'runtime': data.runtime,
                'enddate': data.enddate,
                'channel': unicode(data.channel),
                'pvrchannel': unicode(channel),
                'pvrid': pvrid,
                'logo': unicode(logoURL),
                'genre': unicode(entity2unicode(data.genre)),
                'plot': unicode(entity2unicode(data.plot)),
                # 'popup': unicode(data.detailURL),
                'cast': unicode(entity2unicode(data.cast)),
                'rating': data.rating
               }

        # look for similar database entries

        blob.update(isInDataBase(blob['title']))

        # check timer capabilities

        blob.update(getRecordingCapabilities(blob['pvrid'], blob['datetime2']))

        writeLog('')
        writeLog('blob:            #%s' % (idx))
        writeLog('Title:           %s' % (blob['title']))
        writeLog('is in Database:  %s' % (blob['isInDB']))
        if blob['isInDB']:
            writeLog('   Title:        %s' % blob['db_title'])
            writeLog('   orig. Title:  %s' % blob['db_originaltitle'])
            writeLog('   Fanart:       %s' % blob['db_fanart'])
            writeLog('   Trailer:      %s' % blob['db_trailer'])
            writeLog('   Rating:       %s' % blob['db_rating'])
            writeLog('   User rating:  %s' % blob['db_userrating'])
        writeLog('Thumb:           %s' % (blob['thumb']))
        writeLog('Date & time:     %s' % (blob['datetime']))
        writeLog('Date & time (2): %s' % (blob['datetime2']))
        writeLog('End date:        %s' % (blob['enddate']))
        writeLog('Running time:    %s' % (blob['runtime']))
        writeLog('Channel (GTO):   %s' % (blob['channel']))
        writeLog('Channel (PVR):   %s' % (blob['pvrchannel']))
        writeLog('ChannelID (PVR): %s' % (blob['pvrid']))
        writeLog('Broadcast ID:    %s' % (blob['broadcastid']))
        writeLog('has Timer:       %s' % (blob['hastimer']))
        writeLog('Channel logo:    %s' % (blob['logo']))
        writeLog('Genre:           %s' % (blob['genre']))
        writeLog('Plot:            %s' % (blob['plot']))
        writeLog('Cast:            %s' % (blob['cast']))
        writeLog('Rating:          %s' % (blob['rating']))
        writeLog('')

        HOME.setProperty('GTO.%s' % (idx), str(blob))
        idx += 1

    HOME.setProperty('GTO.blobs', str(idx - 1))
    writeLog('%s items scraped and written to blobs' % (idx - 1))
    HOME.setProperty('GTO.timestamp', str(int(time.time()) / 5))
    xbmc.executebuiltin('Container.Refresh')

# Set details to Window (INFO Labels)

def showInfoWindow(blobId, showWindow=True):
    writeLog('Collect and set details to home/info screen for blob #%s' % (blobId or '<unknown>'))

    if blobId is '' or None:
        writeLog('No ID provided', level=xbmc.LOGFATAL)
        return False

    blob = eval(HOME.getProperty('GTO.%s' % (blobId)))
    blob.update(getRecordingCapabilities(blob['pvrid'], blob['datetime2']))

    clearInfoProperties()

    if blob['pvrid']:
        if blob['broadcastid']:
            writeLog('PVR record function capable (BroadcastID %s)' % (blob['broadcastid']))
            HOME.setProperty("GTO.Info.BroadcastID", str(blob['broadcastid']))
            HOME.setProperty("GTO.Info.hasTimer", str(blob['hastimer']))

        _now = datetime.datetime.now()
        _start = parser.parse(blob['datetime2'])
        _end = parser.parse(blob['enddate'])

        if _start >= _now:
            writeLog('Start time of title \'%s\' is @%s, enable switchtimer button' % (blob['title'], blob['datetime']))
            HOME.setProperty("GTO.Info.isInFuture", "True")
        elif _start < _now < _end:
            writeLog('Title \'%s\' is currently running, enable switch button' % (blob['title']))
            HOME.setProperty("GTO.Info.isRunning", "True")

    HOME.setProperty("GTO.Info.BlobID", str(blobId))
    HOME.setProperty("GTO.Info.Title", blob['title'])
    HOME.setProperty("GTO.Info.Picture", blob['thumb'])
    HOME.setProperty("GTO.Info.Description", blob['plot'] or __LS__(30140))
    HOME.setProperty("GTO.Info.Channel", blob['pvrchannel'])
    HOME.setProperty("GTO.Info.ChannelID", str(blob['pvrid']))
    HOME.setProperty("GTO.Info.Logo", blob['logo'])
    HOME.setProperty("GTO.Info.Date", blob['datetime'])
    HOME.setProperty("GTO.Info.StartTime", blob['datetime'].split()[1][0:5])
    HOME.setProperty("GTO.Info.RunTime", blob['runtime'])
    HOME.setProperty("GTO.Info.EndTime", blob['enddate'].split()[1][0:5])
    HOME.setProperty("GTO.Info.Genre", blob['genre'])
    HOME.setProperty("GTO.Info.Cast", blob['cast'])
    HOME.setProperty("GTO.Info.isInDB", str(blob['isInDB']))
    if blob['isInDB']:
        HOME.setProperty("GTO.Info.dbTitle", blob['db_title'])
        HOME.setProperty("GTO.Info.dbOriginalTitle", blob['db_originaltitle'])
        HOME.setProperty("GTO.Info.Fanart", blob['db_fanart'])
        HOME.setProperty("GTO.Info.dbTrailer", blob['db_trailer'])
        HOME.setProperty("GTO.Info.dbRating", str(blob['db_rating']))
        HOME.setProperty("GTO.Info.dbUserRating", str(blob['db_userrating']))

    if showWindow:
        Popup = xbmcgui.WindowXMLDialog(__xml__, __path__)
        Popup.doModal()
        del Popup

    HOME.setProperty('GTO.%s' % (blobId), str(blob))
    HOME.setProperty('GTO.timestamp', str(int(time.time()) / 5))

# _______________________________
#
#           M A I N
# _______________________________

action = None
blob = None
pvrid = None
broadcastid = None

arguments = sys.argv

if len(arguments) > 1:

    if arguments[0][0:6] == 'plugin':
        writeLog('calling script as plugin source')
        _addonHandle = int(arguments[1])
        arguments.pop(0)
        arguments[1] = arguments[1][1:]

    params = ParamsToDict(arguments[1])
    action = urllib.unquote_plus(params.get('action', ''))
    blob = urllib.unquote_plus(params.get('blob', ''))
    pvrid = urllib.unquote_plus(params.get('pvrid', ''))
    broadcastid = urllib.unquote_plus(params.get('broadcastid', ''))

    writeLog('provided parameter hash: %s' % (arguments[1]))

    if action == 'scrape':
        scrapeGTOPage()

    elif action == 'getcontent':
        writeLog('Filling widget with handle #%s' % (_addonHandle))
        refreshWidget(handle=_addonHandle, notify=False)

    elif action == 'refresh':
        refreshWidget()

    elif action == 'infopopup':
        showInfoWindow(blob)

    elif action == 'sethomecontent':
        showInfoWindow(blob, showWindow=False)

    elif action == 'switch_channel':
        switchToChannel(pvrid)

    elif action == 'change_scraper':
        changeScraper()

    elif action == 'record':
        setTimer(broadcastid, blob)
