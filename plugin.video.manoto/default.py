from builtins import next
import xbmcvfs, xbmcgui, os, xbmcaddon, xbmcplugin, urllib.request, urllib.error, urllib.parse, re

def main():
    __settings__ = xbmcaddon.Addon()
    home = __settings__.getAddonInfo('path')
    resources = os.path.join(home, 'resources')
    addon_handle = int(sys.argv[1])

    icons = {}
    icons['Auto'] = xbmcvfs.translatePath(os.path.join(resources, 'icon.png'))
    icons['720'] = xbmcvfs.translatePath(os.path.join(resources, 'hd.png'))
    icons['1080'] = xbmcvfs.translatePath(os.path.join(resources, 'fhd.png'))

    streams = getStreamsFromPlayList(getVideoUrl())
    bitrates = list(streams.keys())
    bitrates.sort()
    bitrates.reverse()

    for bitrate in bitrates:
         title = "Manoto TV ({quality})".format(quality=streams[bitrate][0])
         li = xbmcgui.ListItem(title)
         try:
              li.setArt({'thumb': icons[streams[bitrate][2]]})
         except (IndexError, KeyError):
              li.setArt({'thumb': icons['Auto']})
         xbmcplugin.addDirectoryItem(handle=addon_handle, url=streams[bitrate][1], listitem=li, isFolder=False)

    xbmcplugin.endOfDirectory(addon_handle)

def getVideoUrl():
    baseUrl = "https://www.manototv.com"
    livePageUrl = "{baseUrl}/live".format(baseUrl = baseUrl)
    mainJsPath = getFromUrl(livePageUrl, 'src\s*=\s*"([^"]+main[^"]+js)"')
    if mainJsPath:
        jsUrl = "{baseUrl}{mainJsPath}".format(baseUrl = baseUrl, mainJsPath = mainJsPath)
        showApiDomain = getFromUrl(jsUrl, 'showApiDomain\s*=\s*"([^"]+)"')
        if showApiDomain:
            detailsUrl = "{baseUrl}/api/v1/publicrole/livemodule/details".format(baseUrl = showApiDomain)
            liveUrl = getFromUrl(detailsUrl, '"liveUrl"\s*:\s*"([^"]+)"')
            return liveUrl

def getFromUrl(url, pattern = None):
    request = urllib.request.Request(url, headers={'User-Agent': 'Kodi'})
    try:
        response = urllib.request.urlopen(request)
        content = response.read().decode('utf-8')
        if not pattern:
            return content
        m = re.search(pattern, content)
        if m:
            return m.group(1)
    except urllib.error.URLError:
        return None
    except urllib.error.HTTPError:
        return None

def getStreamsFromPlayList(url):
    streams = {}
    if not url:
        return streams
    m = re.search("(http.*)/.*m3u8", url)
    if not m:
        return streams
    baseUrl = m.group(1)
    lines = getFromUrl(url).split('\n')    
    lines_iter = iter(lines)
    for line in lines_iter:
        if (line.startswith('#EXT-X-STREAM-INF')):
            m = re.search("RESOLUTION=(\d+)x(\d+)", line)
            if m:
                xRes = m.group(1)
                yRes = m.group(2)
            m = re.search("BANDWIDTH=(\d+)", line)
            if m:
                bandwidth = int(m.group(1))
                title = "{yRes}p - {:.2f} Mbps".format(bandwidth / 1000000.0, yRes=yRes)
                itemUrl = "{baseUrl}/{item}".format(baseUrl=baseUrl, item=next(lines_iter))
                streams[bandwidth] = (title, itemUrl, yRes)

    streams[max(streams.keys()) + 1] = ('Auto', url, 'Auto')
    return streams

if __name__ == '__main__':
    main()
