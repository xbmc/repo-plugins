import sys
import urllib
import urllib2
import urlparse
import xbmcgui
import xbmcplugin
import xbmcaddon
import xbmcvfs
import json
import base64

addonID = 'plugin.audio.radiobrowser'
addon = xbmcaddon.Addon(id=addonID)

base_url = sys.argv[0]
addon_handle = int(sys.argv[1])
args = urlparse.parse_qs(sys.argv[2][1:])

xbmcplugin.setContent(addon_handle, 'songs')

my_stations = {}
profile = xbmc.translatePath(addon.getAddonInfo('profile')).decode("utf-8")
mystations_path = profile+'/mystations.json'

def LANGUAGE(id):
    # return id
    # return "undefined"
    return addon.getLocalizedString(id).encode('utf-8')

def build_url(query):
    return base_url + '?' + urllib.urlencode(query)

def addLink(addon_handle, stationid, name, url, favicon, bitrate):
    li = xbmcgui.ListItem(name, iconImage=favicon)
    li.setInfo(type="Music", infoLabels={ "Title":name, "Size":bitrate})
    localUrl = build_url({'mode': 'play', 'stationid': stationid})

    if stationid in my_stations:
        contextTitle = LANGUAGE(32009)
        contextUrl = build_url({'mode': 'delstation', 'id': stationid})
    else:
        contextTitle = LANGUAGE(32010)
        contextUrl = build_url({'mode': 'addstation', 'id': stationid, 'name': name.encode('utf-8'), 'url': url, 'favicon': favicon, 'bitrate': bitrate})

    li.addContextMenuItems([(contextTitle, 'RunPlugin(%s)'%(contextUrl))])

    xbmcplugin.addDirectoryItem(handle=addon_handle, url=localUrl, listitem=li)

def downloadFile(uri, param):
    paramEncoded = None
    if param != None:
        paramEncoded = json.dumps(param)

    req = urllib2.Request(uri, paramEncoded)
    req.add_header('User-Agent', 'KodiRadioBrowser/1.1.0')
    req.add_header('Content-Type', 'application/json')
    response = urllib2.urlopen(req)
    data=response.read()

    response.close()
    return data

def addPlayableLink(data):
    dataDecoded = json.loads(data)
    for station in dataDecoded:
        addLink(addon_handle, station['id'], station['name'], station['url'], station['favicon'], station['bitrate'])

def readFile(filepath):
    with open(filepath, 'r') as read_file:
        return json.load(read_file)

def writeFile(filepath, data):
    with open(filepath, 'w') as write_file:
        return json.dump(data, write_file)

def addToMyStations(stationid, name, url, favicon, bitrate):
    my_stations[stationid] = {'id': stationid, 'name': name, 'url': url, 'bitrate': bitrate, 'favicon': favicon}
    writeFile(mystations_path, my_stations)

def delFromMyStations(stationid):
    if stationid in my_stations:
        del my_stations[stationid]
        writeFile(mystations_path, my_stations)
        xbmc.executebuiltin('Container.Refresh')

# create storage
if not xbmcvfs.exists(profile):
    xbmcvfs.mkdir(profile)

if xbmcvfs.exists(mystations_path):
    my_stations = readFile(mystations_path)
else:
    writeFile(mystations_path, my_stations)

mode = args.get('mode', None)

if mode is None:
    localUrl = build_url({'mode': 'stations', 'url': 'http://www.radio-browser.info/webservice/json/stations/topclick/100'})
    li = xbmcgui.ListItem(LANGUAGE(32000), iconImage='DefaultFolder.png')
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=localUrl, listitem=li, isFolder=True)

    localUrl = build_url({'mode': 'stations', 'url': 'http://www.radio-browser.info/webservice/json/stations/topvote/100'})
    li = xbmcgui.ListItem(LANGUAGE(32001), iconImage='DefaultFolder.png')
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=localUrl, listitem=li, isFolder=True)

    localUrl = build_url({'mode': 'stations', 'url': 'http://www.radio-browser.info/webservice/json/stations/lastchange/100'})
    li = xbmcgui.ListItem(LANGUAGE(32002), iconImage='DefaultFolder.png')
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=localUrl, listitem=li, isFolder=True)

    localUrl = build_url({'mode': 'stations', 'url': 'http://www.radio-browser.info/webservice/json/stations/lastclick/100'})
    li = xbmcgui.ListItem(LANGUAGE(32003), iconImage='DefaultFolder.png')
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=localUrl, listitem=li, isFolder=True)

    localUrl = build_url({'mode': 'tags'})
    li = xbmcgui.ListItem(LANGUAGE(32004), iconImage='DefaultFolder.png')
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=localUrl, listitem=li, isFolder=True)

    localUrl = build_url({'mode': 'countries'})
    li = xbmcgui.ListItem(LANGUAGE(32005), iconImage='DefaultFolder.png')
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=localUrl, listitem=li, isFolder=True)

    localUrl = build_url({'mode': 'search'})
    li = xbmcgui.ListItem(LANGUAGE(32007), iconImage='DefaultFolder.png')
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=localUrl, listitem=li, isFolder=True)

    localUrl = build_url({'mode': 'mystations'})
    li = xbmcgui.ListItem(LANGUAGE(32008), iconImage='DefaultFolder.png')
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=localUrl, listitem=li, isFolder=True)

    xbmcplugin.endOfDirectory(addon_handle)

elif mode[0] == 'tags':
    data = downloadFile('http://www.radio-browser.info/webservice/json/tags', None)
    dataDecoded = json.loads(data)
    for tag in dataDecoded:
        tagName = tag['name']
        if int(tag['stationcount']) > 1:
            try:
                localUrl = build_url({'mode': 'stations', 'key': 'tag', 'value' : base64.b32encode(tagName.encode('utf-8'))})
                li = xbmcgui.ListItem(tagName, iconImage='DefaultFolder.png')
                xbmcplugin.addDirectoryItem(handle=addon_handle, url=localUrl, listitem=li, isFolder=True)
            except Exception, e:
                print(e)
                pass

    xbmcplugin.endOfDirectory(addon_handle)

elif mode[0] == 'countries':
    data = downloadFile('http://www.radio-browser.info/webservice/json/countries', None)
    dataDecoded = json.loads(data)
    for tag in dataDecoded:
        countryName = tag['name']
        if int(tag['stationcount']) > 1:
            try:
                localUrl = build_url({'mode': 'states', 'country': base64.b32encode(countryName.encode('utf-8'))})
                li = xbmcgui.ListItem(countryName, iconImage='DefaultFolder.png')
                xbmcplugin.addDirectoryItem(handle=addon_handle, url=localUrl, listitem=li, isFolder=True)
            except Exception, e:
                print(e)
                pass

    xbmcplugin.endOfDirectory(addon_handle)

elif mode[0] == 'states':
    country = args['country'][0]
    country = base64.b32decode(country)
    country = country.decode('utf-8')

    data = downloadFile('http://www.radio-browser.info/webservice/json/states/'+urllib.quote(country)+'/', None)
    dataDecoded = json.loads(data)

    localUrl = build_url({'mode': 'stations', 'key': 'country', 'value': base64.b32encode(country.encode('utf-8'))})
    li = xbmcgui.ListItem(LANGUAGE(32006), iconImage='DefaultFolder.png')
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=localUrl, listitem=li, isFolder=True)

    for tag in dataDecoded:
        stateName = tag['name']
        if int(tag['stationcount']) > 1:
            try:
                localUrl = build_url({'mode': 'stations', 'key': 'state','value':base64.b32encode(stateName.encode('utf-8'))})
                li = xbmcgui.ListItem(stateName, iconImage='DefaultFolder.png')
                xbmcplugin.addDirectoryItem(handle=addon_handle, url=localUrl, listitem=li, isFolder=True)
            except Exception, e:
                print(e)
                pass

    xbmcplugin.endOfDirectory(addon_handle)

elif mode[0] == 'stations':
    url = 'http://www.radio-browser.info/webservice/json/stations/search'
    param = None
    if 'url' in args:
        url = args['url'][0]
    else:
        key = args['key'][0]
        value = base64.b32decode(args['value'][0])
        value = value.decode('utf-8')
        param = dict({key:value})

    data = downloadFile(url, param)
    addPlayableLink(data)
    xbmcplugin.endOfDirectory(addon_handle)

elif mode[0] == 'play':
    stationid = args['stationid'][0]
    data = downloadFile('http://www.radio-browser.info/webservice/v2/json/url/'+str(stationid),None)
    dataDecoded = json.loads(data)
    uri = dataDecoded['url']
    xbmc.Player().play(uri)

elif mode[0] == 'search':
    dialog = xbmcgui.Dialog()
    d = dialog.input(LANGUAGE(32011), type=xbmcgui.INPUT_ALPHANUM)

    url = 'http://www.radio-browser.info/webservice/json/stations/byname/'+d
    data = downloadFile(url, None)
    addPlayableLink(data)

    xbmcplugin.endOfDirectory(addon_handle)

elif mode[0] == 'mystations':
    for station in my_stations.values():
        addLink(addon_handle, station['id'], station['name'], station['url'], station['favicon'], station['bitrate'])

    xbmcplugin.endOfDirectory(addon_handle)

elif mode[0] == 'addstation':
    favicon = args['favicon'][0] if 'favicon' in args else ''
    addToMyStations(args['id'][0], args['name'][0], args['url'][0], favicon, args['bitrate'][0])

elif mode[0] == 'delstation':
    delFromMyStations(args['id'][0])
