import helper
from xml.dom import minidom

link = "http://gdata.youtube.com/feeds/api/users/StorylineOnline/uploads"

thisChannel = "storylineonline"

def mainPage():
    xmlPage = helper.load_page(link)
    xmlDom = minidom.parseString(xmlPage)
    
    for entry in xmlDom.getElementsByTagName("entry"):
        youtubeUrl = entry.getElementsByTagName("id")[0].firstChild.data
        youtubeId = youtubeUrl[youtubeUrl.rfind("/")+1:]
        title = entry.getElementsByTagName("title")[0].firstChild.data

        descirption = entry.getElementsByTagName("content")[0].firstChild.data
        img = entry.getElementsByTagName("media:thumbnail")[0].getAttribute("url")
        videoDuration = entry.getElementsByTagName("media:content")[0].getAttribute("duration")
        videoDuration = str(int(videoDuration)/60)
        
        parameters = {"channel":thisChannel,"action":"playVideo","id":youtubeId}
        helper.addDirectoryItem(title, parameters, img, False, plot=descirption, duration=videoDuration)
        
    helper.endOfDirectory()
    
def playVideo(youTubeId):
    streamUrl = "plugin://plugin.video.youtube/?action=play_video&videoid=" + youTubeId 
    helper.setResolvedUrl(streamUrl)
    
params = helper.get_params()
if len(params) == 1:
    mainPage()
else:
    if params['action'] == "playVideo":
        playVideo(params['id'])