import urllib2
import xml.dom.minidom

##########################################################################################
# public classes

class YouTubeVideo:
    '''
    A class representig YouTube video files. 
    '''
    def __init__(self):
        self.title = None
        self.id = None
        self.published = ""
        self.updated = ""
        self.description = "descr"

    def __str__(self):
        if self.title == None:
                return "<None>"
        else:
            return "[%s][%s] %s" %(self.id, self.published, self.title)

    def img(self):
        return 'http://i.ytimg.com/vi/%s/hqdefault.jpg'%self.id

    def videourl(self):
        return 'plugin://plugin.video.youtube?path=/root&action=play_video&videoid=%s' \
            % self.id;


##########################################################################################
# public functions

def fetch_data(page = 1, max_result = 10, orderby="published"):
    '''
    Fetch youtube video data with the given parameters.
    '''
    dom = xml.dom.minidom.parseString(_data(page, max_result, orderby))
    return _parse_document(dom)    


##########################################################################################
# private functions

def _data(page = 1, max_results = 10, orderby="published"):
    '''
    Get XML description of GoogleTechTalk-Videos.
    '''
    url = "http://gdata.youtube.com/feeds/api/videos?"\
        "max-results=%d&start-index=%d&author=GoogleTechTalks&orderby=%s"\
        % (max_results, (page-1)*max_results+1, orderby)

    return urllib2.urlopen(url).read()

def _parse_text_node(node, tag):
    '''
    Return a string containing all text contents of nodes with a given tag name.
    '''
    s = ""

    for tagnode in node.getElementsByTagName(tag):
        for n in tagnode.childNodes:
            if n.nodeType == n.TEXT_NODE:
                s = s + (n.data.strip())

    return s

            
def _parse_document(node):
    '''
    Parse an XML document and create video objects.
    '''
    x = []
    
    for n in node.getElementsByTagName("entry"):
        elem = YouTubeVideo()
  
        elem.title = _parse_text_node(n, "title")
        elem.id = _parse_text_node(n, "id").split("/")[-1]
#        elem.id = _parse_text_node(n, "yt:videoid")
        elem.published = _parse_text_node(n, "published")
        elem.updated = _parse_text_node(n, "updated")
        elem.description = _parse_text_node(n, "media:description")
        x.append(elem)

    return x


