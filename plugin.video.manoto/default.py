import urllib,urllib2,re,os,cookielib,string
import xbmcplugin,xbmcgui,xbmcaddon
from BeautifulSoup import BeautifulSoup

addon = xbmcaddon.Addon('plugin.video.manoto')
profile = xbmc.translatePath(addon.getAddonInfo('profile'))


__settings__ = xbmcaddon.Addon(id='plugin.video.manoto')
__language__ = __settings__.getLocalizedString

home = __settings__.getAddonInfo('path')
icon = xbmc.translatePath(os.path.join(home, 'icon.png'))


if (__settings__.getSetting('username') == "") or (__settings__.getSetting('password') == ""):
	xbmc.executebuiltin("XBMC.Notification(" + __settings__.getAddonInfo('name') + "," + __language__(30000) + ",10000,"+icon+")")
	__settings__.openSettings()

cj = cookielib.CookieJar()
opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))

domain = 'www.manoto1.com'

# Thanks to micahg!
def getStreamsFromPlayList(playlist):
	"""
        Get the streams from the playlist
        
        @param playlist: The playlist URI
        """
        # create the request
        req = urllib2.Request(playlist)

        # request the games        
        try:
        	resp = urllib2.urlopen(req)
        except urllib2.URLError, ue:
        	print("URL error trying to open playlist")
        	return None
        except urllib2.HTTPError, he:
        	print("HTTP error trying to open playlist")
        	return None
        
        # store the base URI from the playlist
        prefix=playlist[0:string.rfind(playlist,'/') + 1]
        lines = string.split(resp.read(), '\n')

        # parse the playlist file
        streams = {}
        bandwidth = ""
        for line in lines:
            
        	# skip the first line
        	if line == "#EXTM3U":
        		continue
            
        	# is this a description or a playlist
        	idx = string.find(line, "BANDWIDTH=")
        	if idx > -1:
        		# handle the description
        		bandwidth = line[idx + 10:len(line)].strip()
        	elif len(line) > 0 and len(bandwidth) > 0:
        		# add the playlist
        		streams[bandwidth] = (prefix + line).strip()

	return streams


def loginAndParse():
	url = 'http://' + domain + '/live'
	
	if not cj:
		resp = opener.open(url)
		html_data = resp.read()
	
		parsedJS = re.findall(r"setCookie\('(.*?)'\s*,\s*'(.*?)'\s*,\s*(.*?)\);", html_data)

		ck = cookielib.Cookie(version=0, name=parsedJS[0][0], value=parsedJS[0][1], port=None, port_specified=False, domain=domain, domain_specified=False, domain_initial_dot=False, path='/', path_specified=True, secure=False, expires=None, discard=True, comment=None, comment_url=None, rest={'HttpOnly': None}, rfc2109=False)
		cj.set_cookie(ck)

	resp = opener.open(url)
	html_data = resp.read()

	soup = BeautifulSoup(html_data)
	eventVal = soup.find('input',id='__EVENTVALIDATION',type='hidden')
	viewState = soup.find('input',id='__VIEWSTATE',type='hidden')

	params = '__EVENTARGUMENT=&__EVENTTARGET=ctl00%%24ContentPlaceHolderMainContent%%24lbtnEnter&__EVENTVALIDATION=%s&__VIEWSTATE=%s&ctl00%%24ContentPlaceHolderMainContent%%24txtUsername=%s&ctl00%%24ContentPlaceHolderMainContent%%24txtPassword=%s' % (urllib.quote(eventVal['value']), urllib.quote(viewState['value']), urllib.quote(__settings__.getSetting('username')), urllib.quote(__settings__.getSetting('password')))
	
	resp = opener.open('http://www.manoto1.com/LiveStream.aspx', params) 	

	resp = opener.open(url)
	html_data = resp.read()

	soup = BeautifulSoup(html_data)
	stream = soup.find('source', type='video/mp4');	
	
	if stream is None or stream['src'] is None:
		return False
	
	streams = getStreamsFromPlayList(stream['src'])
	
 	if streams == None:
 		xbmcplugin.endOfDirectory(handle=int(sys.argv[1]))
		return False
    
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

while not loginAndParse():
       	xbmc.executebuiltin("XBMC.Notification(" + __settings__.getAddonInfo('name') + "," + __language__(30001) + ",10000,"+icon+")")
       	__settings__.openSettings()
