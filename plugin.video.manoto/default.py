import urllib,urllib2,re,os,cookielib,string
import xbmcplugin,xbmcgui,xbmcaddon
from BeautifulSoup import BeautifulSoup

addon = xbmcaddon.Addon('plugin.video.manoto')
profile = xbmc.translatePath(addon.getAddonInfo('profile'))


__settings__ = xbmcaddon.Addon(id='plugin.video.manoto')
__language__ = __settings__.getLocalizedString

home = __settings__.getAddonInfo('path')
icon = xbmc.translatePath(os.path.join(home, 'icon.png'))

cj = cookielib.CookieJar()
opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))

# Thanks to micahg!
def getStreamsFromPlayList(playlist):
	"""
        Get the streams from the playlist

        @param playlist: The playlist URI
        """
        # create the request
        req = urllib2.Request(playlist)

        try:
        	resp = opener.open(req)
        except urllib2.URLError, ue:
        	return None
        except urllib2.HTTPError, he:
        	return None

        # store the base URI from the playlist
        prefix = (playlist[0:string.rfind(playlist.split('?')[0],'/') + 1]).replace('https', 'http')
        lines = string.split(resp.read(), '\n')

        # parse the playlist file
        streams = {}
        bandwidth = ""
        for line in lines:

        	# skip the first line
        	if line == "#EXTM3U":
        		continue

        	# is this a description or a playlist
        	m = re.search("BANDWIDTH=(\d+)", line)
		if m:
        		# handle the description
        		bandwidth = m.group(1)
        	elif len(line) > 0 and len(bandwidth) > 0:
        		# add the playlist
        		streams[bandwidth] = (("" if line.lower().startswith("http") else prefix) + line.strip() +
						("" if len(playlist.split("?")) != 2 else "?" + playlist.split("?")[1])).strip()

	return streams


def fetch():
	domain = 'www.manototv.com'
	url = 'https://' + domain + '/live'

	if not cj:
		resp = opener.open(url)
		html_data = resp.read()
		parsedJS = re.findall(r"setCookie\('(.*?)'\s*,\s*'(.*?)'\s*,\s*(.*?)\);", html_data)

		if len(parsedJS) > 0:
			ck = cookielib.Cookie(version=0, name=parsedJS[0][0], value=parsedJS[0][1], port=None, port_specified=False, domain=domain, domain_specified=False, domain_initial_dot=False, path='/', path_specified=True, secure=False, expires=None, discard=True, comment=None, comment_url=None, rest={'HttpOnly': None}, rfc2109=False)
			cj.set_cookie(ck)

	resp = opener.open(url)
	html_data = resp.read()

	soup = BeautifulSoup(html_data)
	stream = soup.find('source', type='application/x-mpegURL');

	if stream is None or stream['src'] is None:
		m = re.search('file\:\s*\"(http.*)\"', html_data)
		if m is None:
			xbmcplugin.endOfDirectory(handle=int(sys.argv[1]))
			return False
		streams = getStreamsFromPlayList(m.group(1))
	else:
		streams = getStreamsFromPlayList(stream['src'])

 	if streams == None:
		xbmc.executebuiltin("XBMC.Notification(" + __settings__.getAddonInfo('name') + "," + __language__(30002) + ",30000,"+icon+")")
 		xbmcplugin.endOfDirectory(handle=int(sys.argv[1]))
		return True

    	bitrates = []
    	for k in streams.keys():
        	bitrates.append(int(k))
	bitrates.sort()
    	bitrates.reverse()

    	for bitrate in bitrates:
        	stream_id = str(bitrate)
        	title = str(int(bitrate) / int(1000)) + " Kbps"
        	li = xbmcgui.ListItem(title)
        	li.setInfo( type="Video", infoLabels={"Title" : title})
		li.setThumbnailImage(icon)
        	xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),
                	                    url=streams[stream_id],
                        	            listitem=li,
	                                    isFolder=False)

    	xbmcplugin.endOfDirectory(handle=int(sys.argv[1]))

	return True

fetch()
