'''
    New York Times KODI Addon
    ~~~~~~~~~~~~~~~~~~~~~~~~~

    Watch video from The New York Times.
    http://nytimes.com/video
    Kick back and relax and become a learned doctor. 
   
'''
import xbmc
import xbmcgui
import xbmcplugin
import urllib2
import urlparse
import urllib
import xbmcaddon
import json
from BeautifulSoup import BeautifulSoup

def fetch_video_data(video_id):
        url = "http://www.nytimes.com/svc/video/api/v2/video/" + str(video_id)
        page = urllib2.urlopen(url)
        data = json.load(page)
        headline = data["headline"]
        summary = data["summary"]
        byline = data["byline"]
        category = data["section"]["content"]
        count = len(data["renditions"])
	videos = []
	for x in range(0,count):
        	videos.append((data["renditions"][x]["fileSize"],data["renditions"][x]["type"],data["renditions"][x]["url"]))
	video_list = sorted(videos, reverse=True)
	video_link = video_list[0][2]
	try:
                thumbnail = "http://www.nytimes.com/" + data["images"][5]["url"]
        except:
                thumbnail = "http://www.nytimes.com/" + data["images"][0]["url"]
        date = data["publication_date"]
        video_data = ( category , video_link , thumbnail , headline , summary , byline, date )
        return video_data

def getSubjects(url, sections):
        page = urllib2.urlopen(url)
        soup = BeautifulSoup(page.read())
        categories = soup.findAll('li', {'class': 'channel-item'})
        for x in categories:
                sections.append((x.span.contents , x.a['href']))
        return sections

def getContent(base_url, sections):
        for part in sections:
                page = urllib2.urlopen(base_url+part[1])
                soup = BeautifulSoup(page.read())
                holder = soup.findAll('li', {'itemprop' : 'associatedMedia' })
                for x in holder:
                        sub_name = "".join(part[0])
                        try:
                                        video_id = x["data-id"]
                                        content.append((video_id))
                        except KeyError:
                                print "No Data"
                                pass

        return content


base_url = sys.argv[0]
addon_handle = int(sys.argv[1])
args = urlparse.parse_qs(sys.argv[2][1:])

my_addon = xbmcaddon.Addon('plugin.video.nytimes')
xbmcplugin.setContent(addon_handle, 'movies')
times_base_url = "http://www.nytimes.com"
init_url = "http://www.nytimes.com/video/"
global sections
global content
sections = []
content = []

def build_url(query):
    return base_url + '?' + urllib.urlencode(query)

mode = args.get('mode', None)

if mode is None:
	sections = getSubjects(init_url,sections)
	# insert the ALL Videos section
	sections.insert( 0 ,("All Videos","All Videos"))
	
	for item in sections:
		times_section = "".join(item[0])
		times_section = times_section.replace("&amp;" , "&")
		url = build_url({'mode': 'folder', 'foldername': times_section})
        	li = xbmcgui.ListItem( times_section , iconImage=my_addon.getAddonInfo('fanart'))
		li.setProperty('fanart_image',  my_addon.getAddonInfo('fanart'))
        	xbmcplugin.addDirectoryItem(handle=addon_handle , url=url, listitem=li , isFolder=True)

	xbmcplugin.endOfDirectory(addon_handle)


elif mode[0] == 'folder':
	foldername = args['foldername'][0]
	sections = getSubjects(init_url , sections)
	count = len(sections)
	power = []
	for y in range ( 0, count):
		holder = "".join(sections[y][0])
		holder = holder.replace("&amp;" , "&")
		if foldername == holder or foldername == "All Videos":
			power.append(sections[y])
	print power
	content = getContent(times_base_url, power)
	for x in content:
		video_info = fetch_video_data(x)	
		print "Category: " + video_info[0]
                li = xbmcgui.ListItem( video_info[3] , iconImage=video_info[2])
		li.setProperty('fanart_image',  my_addon.getAddonInfo('fanart'))
                xbmcplugin.addDirectoryItem(handle=addon_handle, url=video_info[1], listitem=li)
	xbmcplugin.endOfDirectory(addon_handle)
