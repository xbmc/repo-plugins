# The MIT License (MIT)

# Copyright (c) 2014 Matthias Klan

# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
# the Software, and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
# FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
# COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
# IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.



import sys
import xbmcgui
import xbmcplugin
import urllib
import urllib2
import urlparse
import json

addon_handle = int(sys.argv[1])
args = urlparse.parse_qs(sys.argv[2][1:])

def listSpions(page):
	xbmcplugin.setContent(addon_handle, 'episodes')
	url = 'https://api.dailymotion.com/videos?owners=Spi0n&search=Zapping+de+Web&limit=20&fields=description,duration,id,owner.username,taken_time,thumbnail_large_url,title,views_total&page='+str(page)
	content = getUrl(url)
	content = json.loads(content)

	for item in content['list']:
		id = item['id']
		title = item['title'].encode('utf-8')
		desc = item['description'].encode('utf-8')
		duration = item['duration']
		user = item['owner.username']
		date = item['taken_time']
		thumb = item['thumbnail_large_url']
		views = item['views_total']
		duration = str(int(duration)/60+1)
		try:
			date = datetime.datetime.fromtimestamp(int(date)).strftime('%Y-%m-%d')
		except:
 			date = ""
		temp = ("User: "+user+"  |  "+str(views)+" Views  |  "+date).encode('utf-8')
		try:
			desc = temp+"\n"+desc
		except:
			desc = ""
		
		addLink(id, title, desc, date, duration, thumb)


	if content['has_more']:
		currentPage = content['page']
		nextPage = currentPage+1
		addDir("next page ("+str(nextPage)+")", nextPage, "")
	
	xbmcplugin.endOfDirectory(addon_handle)


def getUrl(url):
    req = urllib2.Request(url)
    req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; rv:22.0) Gecko/20100101 Firefox/22.0')
    response = urllib2.urlopen(req)
    link = response.read()
    response.close()
    return link

def addDir(name, page, thumbImage):
    link = sys.argv[0]+"?page="+str(page)
    li = xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=thumbImage)
    li.setInfo(type="Video", infoLabels={"Title": name})
    ok = xbmcplugin.addDirectoryItem(handle=addon_handle, url=link, listitem=li, isFolder=True)
    return ok

def addLink(id, title, desc, date, duration, iconimage):
	link = 'plugin://plugin.video.dailymotion_com/?url=' + id +'&mode=playVideo'
	li = xbmcgui.ListItem(title, iconImage='DefaultVideo.png', thumbnailImage=iconimage)
	li.setInfo(type="Video", infoLabels={"Title": title, "Plot": desc, "Aired": date, "Duration": duration})
	li.setProperty('IsPlayable', 'true')
	entries = []
    #entries.append('Download this Spi0n', 'RunPlugin(plugin://plugin.video.dailymotion_com/?mode=downloadVideo&url='+urllib.quote_plus(id)+')',))
    #entries.append('Queue this Spi0n', 'RunPlugin(plugin://plugin.video.dailymotion_com/?mode=queueVideo&url='+urllib.quote_plus(link)+'&name='+urllib.quote_plus(title)+')',))
	li.addContextMenuItems(entries)
	ok = xbmcplugin.addDirectoryItem(handle=addon_handle, url=link, listitem=li)
	return ok

page = args.get('page', None)

if page is None:
	listSpions(1)
else:
	listSpions(page[0])

