import urllib, re
import helper
import json

thisChannel = "nickjr"
baseLink = "http://www.nickjr.com"
apiLink = "http://www.nickjr.com/common/data/kids/get-kids-config-data.jhtml?fsd=/dynaboss&urlAlias=%s&af=false"

extractPlaylist = re.compile("<h2 id=\".*?\"><span>(.*?)</span></h2>.*?<ul>(.*?)</ul>",re.DOTALL)

def mainPage():
    page = helper.load_page(apiLink%("kids-video-landing"))
    
    data = json.loads(page)
    items = data['config']['promos'][0]['items']

    for category in items:
        catName = helper.removeHtmlSpecialChars(category['title'])
        catLink = apiLink%(category['urlAlias'])
        catImg =  baseLink+category['thumbnail'];
        helper.addDirectoryItem(catName, {"channel":thisChannel,"action":"showCategory","link":catLink}, catImg)

    helper.endOfDirectory()

def showCategory(link):
    page = helper.load_page(urllib.unquote(link))
    
    page = page.replace("\xED","\xc3\xad")
    
    data = json.loads(page)
    items = data['config']['promos'][0]['items']
    
    for video in items:
        vidName = helper.removeHtmlSpecialChars(video['title'])
        vidId = video['id']
        vidImg =  video['thumbnail']
        
        helper.addDirectoryItem(vidName, {"channel":thisChannel,"action":"playVideo","link":vidId}, vidImg, False)

    helper.endOfDirectory()

def playVideo(link):
    playlistLink = "http://www.nickjr.com/dynamo/video/data/mrssGen.jhtml?type=network&loc=sidebar&hub=njParentsHub&mode=playlist&mgid=mgid:cms:item:nickjr.com:"
    playlistLink = playlistLink+link
    page = helper.load_page(playlistLink,True)
    media = helper.extractMrss(page)
    
    player = media[0]['player']
    link = media[0]['url']

    response = urllib.urlopen(urllib.unquote(player))
    mediaPlayer = response.geturl()
    
    page = helper.load_page(urllib.unquote(link))
    extractRtmpUrls = re.compile("<rendition.*?height=[\"\']+([0-9]*)[\"\']+.*?>[\n\ \t]*<src>(.*?)</src>[\n\ \t]*</rendition>")
    
    streamUrl = ""
    streamHeight = 0
    
    for rtmpItem in extractRtmpUrls.finditer(page):
        if rtmpItem.group(1)>streamHeight:
            streamUrl = rtmpItem.group(2)
    
    streamUrl = streamUrl + " swfUrl=" + mediaPlayer + " swfVfy=1"
    
    helper.setResolvedUrl(streamUrl)
    
params = helper.get_params()
if len(params) == 1:
    mainPage()
else:
    if params['action'] == "showCategory":
        showCategory(params['link'])
    if params['action'] == "playVideo":
        playVideo(params['link'])
