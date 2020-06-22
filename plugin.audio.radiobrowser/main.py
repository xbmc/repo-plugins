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

import socket
import random

def get_radiobrowser_base_urls():
    """
    Get all base urls of all currently available radiobrowser servers

    Returns: 
    list: a list of strings

    """
    hosts = []
    # get all hosts from DNS
    ips = socket.getaddrinfo('all.api.radio-browser.info',
                             80, 0, 0, socket.IPPROTO_TCP)
    for ip_tupple in ips:
        ip = ip_tupple[4][0]

        # do a reverse lookup on every one of the ips to have a nice name for it
        host_addr = socket.gethostbyaddr(ip)

        # add the name to a list if not already in there
        if host_addr[0] not in hosts:
            hosts.append(host_addr[0])

    # sort list of names
    random.shuffle(hosts)
    # add "https://" in front to make it an url
    xbmc.log("Found hosts: " + ",".join(hosts))
    return list(map(lambda x: "https://" + x, hosts))

def LANGUAGE(id):
    # return id
    # return "undefined"
    return addon.getLocalizedString(id).encode('utf-8')

def build_url(query):
    return base_url + '?' + urllib.urlencode(query)

def addLink(stationuuid, name, url, favicon, bitrate):
    li = xbmcgui.ListItem(name, iconImage=favicon)
    li.setProperty('IsPlayable', 'true')
    li.setInfo(type="Music", infoLabels={ "Title":name, "Size":bitrate})
    localUrl = build_url({'mode': 'play', 'stationuuid': stationuuid})

    if stationuuid in my_stations:
        contextTitle = LANGUAGE(32009)
        contextUrl = build_url({'mode': 'delstation', 'stationuuid': stationuuid})
    else:
        contextTitle = LANGUAGE(32010)
        contextUrl = build_url({'mode': 'addstation', 'stationuuid': stationuuid, 'name': name.encode('utf-8'), 'url': url, 'favicon': favicon, 'bitrate': bitrate})

    li.addContextMenuItems([(contextTitle, 'RunPlugin(%s)'%(contextUrl))])

    xbmcplugin.addDirectoryItem(handle=addon_handle, url=localUrl, listitem=li, isFolder=False)

def downloadFile(uri, param):
    """
    Download file with the correct headers set

    Returns: 
    a string result

    """
    paramEncoded = None
    if param != None:
        paramEncoded = json.dumps(param)
        xbmc.log('Request to ' + uri + ' Params: ' + ','.join(param))
    else:
        xbmc.log('Request to ' + uri)

    req = urllib2.Request(uri, paramEncoded)
    req.add_header('User-Agent', 'KodiRadioBrowser/1.2.0')
    req.add_header('Content-Type', 'application/json')
    response = urllib2.urlopen(req)
    data=response.read()

    response.close()
    return data

def downloadApiFile(path, param):
    """
    Download file with relative url from a random api server.
    Retry with other api servers if failed.

    Returns: 
    a string result

    """
    servers = get_radiobrowser_base_urls()
    i = 0
    for server_base in servers:
        xbmc.log('Random server: ' + server_base + ' Try: ' + str(i))
        uri = server_base + path

        try:
            data = downloadFile(uri, param)
            return data
        except Exception as e:
            xbmc.log("Unable to download from api url: " + uri, xbmc.LOGERROR)
            pass
        i += 1
    return {}

def addPlayableLink(data):
    dataDecoded = json.loads(data)
    for station in dataDecoded:
        addLink(station['stationuuid'], station['name'], station['url'], station['favicon'], station['bitrate'])

def readFile(filepath):
    with open(filepath, 'r') as read_file:
        return json.load(read_file)

def writeFile(filepath, data):
    with open(filepath, 'w') as write_file:
        return json.dump(data, write_file)

def addToMyStations(stationuuid, name, url, favicon, bitrate):
    my_stations[stationuuid] = {'stationuuid': stationuuid, 'name': name, 'url': url, 'bitrate': bitrate, 'favicon': favicon}
    writeFile(mystations_path, my_stations)

def delFromMyStations(stationuuid):
    if stationuuid in my_stations:
        del my_stations[stationuuid]
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
    localUrl = build_url({'mode': 'stations', 'url': '/json/stations/topclick/100'})
    li = xbmcgui.ListItem(LANGUAGE(32000), iconImage='DefaultFolder.png')
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=localUrl, listitem=li, isFolder=True)

    localUrl = build_url({'mode': 'stations', 'url': '/json/stations/topvote/100'})
    li = xbmcgui.ListItem(LANGUAGE(32001), iconImage='DefaultFolder.png')
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=localUrl, listitem=li, isFolder=True)

    localUrl = build_url({'mode': 'stations', 'url': '/json/stations/lastchange/100'})
    li = xbmcgui.ListItem(LANGUAGE(32002), iconImage='DefaultFolder.png')
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=localUrl, listitem=li, isFolder=True)

    localUrl = build_url({'mode': 'stations', 'url': '/json/stations/lastclick/100'})
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
    data = downloadApiFile('/json/tags', None)
    dataDecoded = json.loads(data)
    for tag in dataDecoded:
        tagName = tag['name']
        if int(tag['stationcount']) > 1:
            try:
                localUrl = build_url({'mode': 'stations', 'key': 'tag', 'value' : base64.b32encode(tagName.encode('utf-8'))})
                li = xbmcgui.ListItem(tagName, iconImage='DefaultFolder.png')
                xbmcplugin.addDirectoryItem(handle=addon_handle, url=localUrl, listitem=li, isFolder=True)
            except Exception as e:
                xbmc.err(e)
                pass

    xbmcplugin.endOfDirectory(addon_handle)

elif mode[0] == 'countries':
    data = downloadApiFile('/json/countries', None)
    dataDecoded = json.loads(data)
    for tag in dataDecoded:
        countryName = tag['name']
        if int(tag['stationcount']) > 1:
            try:
                localUrl = build_url({'mode': 'states', 'country': base64.b32encode(countryName.encode('utf-8'))})
                li = xbmcgui.ListItem(countryName, iconImage='DefaultFolder.png')
                xbmcplugin.addDirectoryItem(handle=addon_handle, url=localUrl, listitem=li, isFolder=True)
            except Exception as e:
                xbmc.log("Stationcount is not of type int", xbmc.LOGERROR)
                pass

    xbmcplugin.endOfDirectory(addon_handle)

elif mode[0] == 'states':
    country = args['country'][0]
    country = base64.b32decode(country)
    country = country.decode('utf-8')

    data = downloadApiFile('/json/states/'+urllib.quote(country)+'/', None)
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
            except Exception as e:
                xbmc.log("Stationcount is not of type int", xbmc.LOGERROR)
                pass

    xbmcplugin.endOfDirectory(addon_handle)

elif mode[0] == 'stations':
    url = '/json/stations/search'
    param = None
    if 'url' in args:
        url = args['url'][0]
    else:
        key = args['key'][0]
        value = base64.b32decode(args['value'][0])
        value = value.decode('utf-8')
        param = dict({key:value})
        param['order'] = 'clickcount'
        param['reverse'] = True

    data = downloadApiFile(url, param)
    addPlayableLink(data)
    xbmcplugin.endOfDirectory(addon_handle)

elif mode[0] == 'play':
    stationuuid = args['stationuuid'][0]
    data = downloadApiFile('/json/url/' + str(stationuuid),None)
    dataDecoded = json.loads(data)
    uri = dataDecoded['url']
    xbmcplugin.setResolvedUrl(addon_handle, True, xbmcgui.ListItem(path=uri))

elif mode[0] == 'search':
    dialog = xbmcgui.Dialog()
    d = dialog.input(LANGUAGE(32011), type=xbmcgui.INPUT_ALPHANUM)

    url = '/json/stations/byname/'+d
    data = downloadApiFile(url, None)
    addPlayableLink(data)

    xbmcplugin.endOfDirectory(addon_handle)

elif mode[0] == 'mystations':
    for station in my_stations.values():
        addLink(station['stationuuid'], station['name'], station['url'], station['favicon'], station['bitrate'])

    xbmcplugin.endOfDirectory(addon_handle)

elif mode[0] == 'addstation':
    favicon = args['favicon'][0] if 'favicon' in args else ''
    addToMyStations(args['stationuuid'][0], args['name'][0], args['url'][0], favicon, args['bitrate'][0])

elif mode[0] == 'delstation':
    delFromMyStations(args['stationuuid'][0])
