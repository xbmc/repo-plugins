import urllib, re
import helper

thisChannel = "kidmango"
baseLink = "http://kidmango.com/shows/"

def mainPage():
	page = helper.load_page(baseLink)
	extractShow = re.compile("<a href=\"(.*?)\" target=\"_self\"><img src=\"(.*?)\".*?alt=\"Watch (.*?) on KidMango.com!\" /></a>")
	
	for show in extractShow.finditer(page):
		link = show.group(1).replace("comtinpo","com/tinpo")
		print link
		page = urllib.urlopen(link)
		if page.getcode() != 404:
			page =page.read()
			extractContentId = re.compile("contentId : '([0-9]*)',").search(page)
			if extractContentId is not None:
				contentId = extractContentId.group(1)
				feedUrl = "http://cms.springboard.gorillanation.com/xml_feeds_advanced/index/891/rss1/"+contentId+"/"
				helper.addDirectoryItem(show.group(3), {"channel":thisChannel,"action":"showVideos","link":feedUrl}, show.group(2))

	helper.endOfDirectory()

def showVideos(feedUrl):
	feed = helper.load_page(urllib.unquote(feedUrl))
	
	media = helper.extractMrss(feed)

   	for video in media:
   		parameters = {"channel":thisChannel,"action":"playVideo","link":video['url']}
   		helper.addDirectoryItem(video['title'], parameters, video['img'], False, duration=video['duration'], plot=video['plot'])
	
	#Next page
	extractNextPage = re.compile("<atom:link rel=\"next\" href=\"(.*)\" />").search(feed)
	if extractNextPage is not None:
		helper.addDirectoryItem("Show more", {"channel":thisChannel,"action":"showVideos","link":extractNextPage.group(1)}, "")
	
	helper.endOfDirectory()

def playVideo(link):
	helper.setResolvedUrl(urllib.unquote(link))
	
params = helper.get_params()
if len(params) == 1:
    mainPage()
else:
    if params['action'] == "showVideos":
        showVideos(params['link'])
    if params['action'] == "playVideo":
        playVideo(params['link'])
