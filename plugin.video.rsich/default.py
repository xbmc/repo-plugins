from phate89lib import kodiutils, rutils, staticutils
import datetime, calendar, os
try:
    from urllib.parse import urlparse, quote_plus
except ImportError:
    from urlparse import urlparse
    from urllib import quote_plus
import dateutil.parser
import xml.etree.ElementTree as ET
from tempfile import mkstemp
import datetime

webutils=rutils.RUtils()
webutils.log=kodiutils.log
useragent = "RSI.CH Video Addon"
webutils.USERAGENT = useragent

#site logic

def getVideoLinks(id):
        return getVideoLinksFromUrl('http://il.srgssr.ch/integrationlayer/1.0/ue/rsi/video/play/{id}.json'.format(id=id))

def getVideoLinksFromUrl(url):
    resp = webutils.getJson(url)
    if not resp:
        return False
    if not ('Video' in resp and 'Playlists' in resp['Video'] and 'Playlist' in resp['Video']['Playlists']):
        return False
    ret = []
    for pl in resp['Video']['Playlists']['Playlist']:
        for purl in pl['url']:
            plout= {}
            plout['protocol'] = pl['@protocol']
            plout['quality'] = purl['@quality']
            plout['url'] = purl['text']
            ret.append(plout)
    if 'Subtitles' in resp['Video'] and 'TTMLUrl' in resp['Video']['Subtitles']:
        ret.append({'protocol':'TTMLUrl', 'quality':'', 'url': resp['Video']['Subtitles']['TTMLUrl']})
    return ret

def getAuthString(url):
    #obtain the auth url
    sUrl=urlparse(url).path.split('/')
    if len(sUrl) < 3:
        return False
    auth=webutils.getJson('http://tp.srgssr.ch/akahd/token?acl={path}*'.format(path=quote_plus('/{p1}/{p2}/'.format(p1=sUrl[1],p2=sUrl[2]))))
    if 'token' in auth and 'authparams' in auth['token']:
        return '?' + auth['token']['authparams']
    else:
        return False;

def getCategories():
    jsn = webutils.getJson('http://il.srgssr.ch/integrationlayer/1.0/ue/rsi/tv/topic.json')
    if not jsn or 'Topics' not in jsn or 'Topic' not in jsn['Topics']:
        return False
    return jsn['Topics']['Topic']

def getProgramVideos(id, page=1, pageSize=10, parseAll=False):
    resp = webutils.getJson('http://il.srgssr.ch/integrationlayer/1.0/ue/rsi/assetSet/listByAssetGroup/{id}.json?pageNumber={page}&pageSize={pageSize}'.format(id=id,page=page,pageSize=pageSize))
    ret = getVideoInfo(resp)
    if parseAll and ret and len(ret)>0:
        ret.extend(getProgramVideos(id, int(page)+1, pageSize, True))
    return ret

def getDateVideos(id):
    resp = webutils.getJson('http://il.srgssr.ch/integrationlayer/1.0/ue/rsi/video/episodesByDate.json?day={id}'.format(id=id))
    return getVideoInfo(resp)

def getCategoryVideos(id, pageSize=10):
    resp = webutils.getJson('http://il.srgssr.ch/integrationlayer/1.0/ue/rsi/video/editorialPlayerLatestByTopic/{id}.json?pageSize={pageSize}'.format(id=id,pageSize=pageSize))
    return getVideoInfo(resp)

def getPicksVideos(pageSize=10):
    resp = webutils.getJson('http://il.srgssr.ch/integrationlayer/1.0/ue/rsi/video/editorialPlayerPicks.json?pageSize={pageSize}'.format(pageSize=pageSize))
    return getVideoInfo(resp)

def getVideoInfo(jsn):
    if not jsn:
        return False
    vids = []
    if 'AssetSets' in jsn and 'AssetSet' in jsn['AssetSets']:
        vids = jsn['AssetSets']['AssetSet']
    elif 'Videos' in jsn and 'Video' in jsn['Videos']:
        vids = jsn['Videos']['Video']
    else:
        return False
    ret = []
    for vid in vids:
        if 'Assets' in vid:
            if 'Video' in vid['Assets'] and len(vid['Assets']['Video']) > 0:
                vid = vid['Assets']['Video'][0]
            else:
                continue
        if 'AssetMetadatas' in vid and 'AssetMetadata' in vid['AssetMetadatas'] and len(vid['AssetMetadatas']['AssetMetadata'])>0:
            vd=vid['AssetMetadatas']['AssetMetadata'][0]
            title = ''
            if 'AssetSet' in vid and 'Show' in vid['AssetSet'] and 'title' in vid['AssetSet']['Show']:
                title = vid['AssetSet']['Show']['title'] + ' - '
            date = ''
            if ('createdDate' in vd):
                date = dateutil.parser.parse(vd['createdDate'])
            ret.append({'id': vd['id'], 'title': title + vd['title'], 'plot': vd['description'], 'date': vd['createdDate'], 'premiered': str(date), 'image': getImage(vid)})
    return ret

def getImage(vid):
    if 'Image' in vid and \
       'ImageRepresentations' in vid['Image'] and \
       'ImageRepresentation' in vid['Image']['ImageRepresentations'] and \
       len(vid['Image']['ImageRepresentations']['ImageRepresentation'])>0 and \
       'url' in vid['Image']['ImageRepresentations']['ImageRepresentation'][0]:
            return vid['Image']['ImageRepresentations']['ImageRepresentation'][0]['url']
    else:
            return 'http://ws.srf.ch/asset/image/audio/b6813d84-7d73-444a-92b0-9fd5eb4606cc/NOT_SPECIFIED.jpg'

def getPrograms(letter=''):
    jsn = webutils.getJson('http://il.srgssr.ch/integrationlayer/1.0/ue/rsi/tv/assetGroup/editorialPlayerAlphabetical.json')
    if not jsn or 'AssetGroups' not in jsn or 'Show' not in jsn['AssetGroups']:
        return False
    ret = []
    for pr in jsn['AssetGroups']['Show']:
        if letter =='' or letter[0].lower()==pr['title'][0].lower():
            ret.append({'id': pr['id'], 'title': pr['title'], 'plot': pr['description'], 'image': getImage(pr)})
    return ret

def getChannels():
    jsn = webutils.getJson('https://www.rsi.ch/play/tv/live/overview')
    if not jsn or 'teaser' not in jsn:
        return False
    return jsn['teaser']

def ttmlToSrt(url):
    if not url:
        return False
    txt = webutils.getText(url)
    if not txt:
        return False
    root = ET.fromstring(txt.encode('utf-8'))
    if not root:
        return False
    count = 0
    output=''
    for sub in root[0][0]:
        count+=1
        startT=datetime.datetime.strptime(sub.attrib['begin'], '%H:%M:%S.%f').strftime('%H:%M:%S,%f')[:-3]
        endT=datetime.datetime.strptime(sub.attrib['end'], '%H:%M:%S.%f').strftime('%H:%M:%S,%f')[:-3]
        text=''
        for line in sub:
            if line.tag.endswith('span'):
                text+=line.text.strip()
            elif line.tag.endswith('br'):
                text+='\r\n'
        output+='{count}\r\n{start} --> {end}\r\n{text}\r\n\r\n'.format(count=count,start=startT,end=endT,text=text.encode('utf-8'))
    f, path = mkstemp()
    os.write(f, output)
    os.close(f)
    return path

#kodi logic

def loadList():
    kodiutils.addListItem(kodiutils.LANGUAGE(32012), params={"mode": "programs" })
    kodiutils.addListItem(kodiutils.LANGUAGE(32013), params={"mode": "live" })
    kodiutils.addListItem(kodiutils.LANGUAGE(32014), params={"mode": "categories" })
    kodiutils.addListItem(kodiutils.LANGUAGE(32015), params={"mode": "dates" })
    kodiutils.addListItem(kodiutils.LANGUAGE(32016), params={"mode": "picks" })
    kodiutils.addListItem(kodiutils.LANGUAGE(32017), params={"mode": "sport" })
    kodiutils.endScript()

def addProgramsItems():
    kodiutils.setContent('videos')
    progs = getPrograms()
    if progs:
        for p in progs:
            p['mediatype']='video'
            kodiutils.addListItem(p['title'], params={"id": p['id'], "mode": "program" }, videoInfo=p, thumb=p['image'])
    kodiutils.endScript()

def addLive():
    kodiutils.setContent('videos')
    chs = getChannels()
    if chs:
        for ch in chs:
            kodiutils.addListItem(ch['channelName'], params={"mode": "video", "id": ch['id'] }, thumb=ch['logo'], videoInfo={'mediatype': 'video'}, isFolder=False)
    kodiutils.endScript()

def addCategories():
    cats = getCategories()
    if cats:
        for cat in cats:
            kodiutils.addListItem(cat['title'], params={"mode": "category", "id": cat['id'] })
    kodiutils.endScript()

def addDates():
    day = datetime.date.today()
    for x in range(0, 10):
        kodiutils.addListItem(kodiutils.LANGUAGE(32020).format(dayname=kodiutils.LANGUAGE(32022+day.weekday()),day=day.day,month=kodiutils.LANGUAGE(32028+day.month),year=day.year), params={"mode": "date", "id": str(day) })
        day = day - datetime.timedelta(days=1)
    for year in range( day.year, 1950, -1):
        kodiutils.addListItem(str(year), params={"mode": "year", "year": year })
    kodiutils.endScript()

def addYear(year):
    for month in range(1, 13):
        kodiutils.addListItem(kodiutils.LANGUAGE(32021).format(month=kodiutils.LANGUAGE(32028+month),year=year), params={"mode": "month", "month": month, "year": year })
    kodiutils.endScript()

def addMonth(month, year):
    for day in calendar.Calendar().itermonthdates(int(year), int(month)):
        kodiutils.addListItem(kodiutils.LANGUAGE(32020).format(dayname=kodiutils.LANGUAGE(32022+day.weekday()),day=day.day,month=kodiutils.LANGUAGE(32028+day.month),year=day.year), params={"mode": "date", "id": str(day) })
    kodiutils.endScript()
    
def addVideosItems(id='', type=1, page=1):
    kodiutils.setContent('videos')
    res = []
    loadAll = kodiutils.getSettingAsBool('loadAll')
    elPerPage = kodiutils.getSetting('elPerPage')
    if type==1:
        res = getProgramVideos(id, page, elPerPage, loadAll)
    elif type==2:
        res = getDateVideos(id)
    elif type==3:
        res = getCategoryVideos(id, elPerPage)
    elif type==4:
        res = getPicksVideos(elPerPage)
    if res:
        for ep in res:
            ep['mediatype']='video'
            kodiutils.addListItem(ep['title'], params={"id": ep['id'], "mode": "video" }, thumb=ep['image'], videoInfo=ep, isFolder=False)
        if type == 1 and (not loadAll) and len(getProgramVideos(id, int(page)+1, elPerPage))>0:
            kodiutils.addListItem(kodiutils.LANGUAGE(32011), params={"id": id, "mode": "program", "page": int(page) + 1})
    kodiutils.endScript()

# This function create a list of live sports to show in Kodi. Every live sport entry contains a title, a thumb image URL and params (mode and url).
def addSport():
    kodiutils.setContent('videos')
    liveSportList = getLiveSportLink()
    if liveSportList:
        for live in liveSportList:
            kodiutils.addListItem(live['title'], params={"mode": "watch_sport", "url": live['url'] }, thumb=live['thumbURL'], videoInfo={'mediatype': 'video'}, isFolder=False)
    kodiutils.endScript()

# This function get a dictionary with the live events ongoing containing the URL of the HLS stream, the image URL and the title of the event.
def getLiveSportLink():
        # Get today date.
        today = datetime.datetime.strftime(datetime.datetime.today(),'%Y-%m-%d')

        # Get tomorrow date.
        tomorrow = datetime.datetime.strftime(datetime.datetime.today() + datetime.timedelta(1),'%Y-%m-%d')

        # Get list of live sport events for today.
        resp = webutils.getJson('https://www.rsi.ch/rsi-api/app-sport/v4/epg?from={today}&to={tomorrow}'.format(today=today,tomorrow=tomorrow))
        # If there are no response, return.
        if not resp:
            return False
        # If there is no events field return.
        if not 'events' in resp:
            return False
        # If the lenght of events is empty, return.
        if len(resp['events'])==0:
            return False
        
        # List where the live sport events will be stored.
        liveSports = []

        # Iterate through all the events
        for event in resp['events']:
            # Save only the present (ongoing) events.
            if event['category'] == 'present':
                # Create an empty dict.
                live = {}

                # Extract the hls streaming link.
                hls = event['hls']
                
                # Save the url (trunc before the "?" character) in the dict.
                live['url'] = hls.split("?")[0]
                
                # Save the title in the dict.
                live['title'] = event['title']
				
                # Save the image URL in the dict.
                live['thumbURL'] = event['imageUrl']
				
                # Append the dict to the events list.
                liveSports.append(live)

        # Return the list of live events.
        return liveSports

# This function plays a sport video given the HLS stream URL.
def watchLiveSport(url):
    # Get the HMAC token to authorize the stream.
    auth = getAuthString(url)
    # If the token request was successful, play the video URL.
    if auth:
        subs = []
        kodiutils.setResolvedUrl('{url}?{auth}|User-Agent={ua}'.format(url=url,auth=auth,ua=quote_plus(useragent)), subs=subs)
    kodiutils.setResolvedUrl("",solved=False)

def watchVideo(id):
    links = getVideoLinks(id)
    neededQ = ""
    if kodiutils.getSettingAsBool('PreferHD'):
        neededQ = 'HD'
    else:
        neededQ = 'SD'
    fUrl = ''
    for url in links:
        if url['protocol'] == 'HTTP-HLS':
            fUrl = url['url']
            if url['quality'] == neededQ:
                break
    if fUrl:
        auth = getAuthString(fUrl)
        if auth:
            subs = []
            if kodiutils.getSettingAsBool('parseSubs'):
                for url in links:
                    if url['protocol'] == 'TTMLUrl': 
                        subpath = ttmlToSrt(url['url'])
                        if subpath:
                            subs.append(subpath)
            kodiutils.setResolvedUrl('{url}?{auth}|User-Agent={ua}'.format(url=fUrl,auth=auth,ua=quote_plus(useragent)), subs=subs)
    kodiutils.setResolvedUrl("",solved=False)

#main

params = staticutils.getParams()
if not params or 'mode' not in params:
    loadList()
else:
    if params['mode'] == "programs":
        addProgramsItems()
    elif params['mode'] == "program":
        addVideosItems(params['id'], type=1, page=params.get('page', 1))
    elif params['mode'] == "live":
        addLive()
    elif params['mode'] == "dates":
        addDates()
    elif params['mode'] == "date":
        addVideosItems(params['id'], type=2)
    elif params['mode'] == "year":
        addYear(params['year'])
    elif params['mode'] == "month":
        addMonth(params['month'], params['year'])
    elif params['mode'] == "categories":
        addCategories()
    elif params['mode'] == "category":
        addVideosItems(params['id'], type=3)
    elif params['mode'] == "picks":
        addVideosItems(type=4)
    elif params['mode'] == "video":
        watchVideo(params['id'])
    elif params['mode'] == "sport":
        addSport()
    elif params['mode'] == "watch_sport":
        watchLiveSport(params['url'])
    else:
        loadList()
