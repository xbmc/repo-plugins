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

    streams = getStreamsFromPlayList()
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

def getStreamsFromPlayList():
    base_url = "https://d2rwmwucnr0d10.cloudfront.net/"
    url = "{base_url}live.m3u8".format(base_url = base_url)
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
                title = "{yRes}p - {:.2f} Mbps".format(bandwidth / 1000000.0, yRes=yRes)
                itemUrl = "{base_url}{item}".format(base_url=base_url, item=next(lines_iter))
                streams[bandwidth] = (title, itemUrl, yRes)

    streams[max(streams.keys()) + 1] = ('Auto', url, 'Auto')
    return streams

if __name__ == '__main__':
    main()
