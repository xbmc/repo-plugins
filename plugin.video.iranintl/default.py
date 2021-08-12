from builtins import next
import xbmcvfs, xbmcgui, os, xbmcaddon, xbmcplugin, urllib.request, urllib.error, urllib.parse, re

def main():
    __settings__ = xbmcaddon.Addon()
    home = __settings__.getAddonInfo('path')
    addon_handle = int(sys.argv[1])
    icon = xbmcvfs.translatePath(os.path.join(home, 'icon.png'))
    livePageUrl = 'https://iranintl.com/live'
    request = urllib.request.Request(livePageUrl, headers={'User-Agent': 'Kodi'})

    try:
        response = urllib.request.urlopen(request)
        html = response.read().decode('utf-8')

        liveVideoUrls = re.findall('https://.*?.m3u8', html)

        if len(liveVideoUrls) > 0:
            base_url = liveVideoUrls[0].rsplit('/', 1)[0]+'/'
            streams = getStreamsFromPlayList(base_url, liveVideoUrls[0])

            bitrates = list(streams.keys())
            bitrates.sort()
            bitrates.reverse()

            for bitrate in bitrates:
                 li = xbmcgui.ListItem(streams[bitrate][0])
                 li.setArt({'thumb': icon})
                 xbmcplugin.addDirectoryItem(handle=addon_handle, url=streams[bitrate][1], listitem=li, isFolder=False)

    except urllib.error.URLError as e:
        if hasattr(e, 'reason'):
            xbmc.log('We failed to reach a server. Reason:', e.reason)
        elif hasattr(e, 'code'):
            xbmc.log('The server couldn\'t fulfill the request. Error code:', e.code)

    xbmcplugin.endOfDirectory(addon_handle)

def getStreamsFromPlayList(base_url, url):
    try:
        resp = urllib.request.urlopen(url)
    except urllib.error.URLError:
        return None
    except urllib.error.HTTPError:
        return None

    lines = resp.read().decode('utf-8').split('\n')

    streams = {}
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
                title = "{yRes}p - {:.2f} Mbps".format(bandwidth / 1000000.0, xRes=xRes, yRes=yRes)
                itemUrl = "{base_url}{item}".format(base_url=base_url, item=next(lines_iter))
                streams[bandwidth] = (title, itemUrl)

    streams[max(streams.keys()) + 1] = ('Iran International TV (Auto)', url)
    return streams

if __name__ == '__main__':
    main()
