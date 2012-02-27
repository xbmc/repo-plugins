import re
from model.util import cleanHTML, resizeImage
from BeautifulSoup import SoupStrainer, MinimalSoup as BeautifulSoup
from model.url_constants import URLTED

#MAIN URLS
URLTHEMES = 'http://www.ted.com/themes/atoz/page/'
URLSPEAKERS = 'http://www.ted.com/speakers/atoz/page/'
URLSEARCH = 'http://www.ted.com/search?q=%s/page/'

def getNavItems(html):
    """self.navItems={'next':url, 'previous':url, 'selected':pagenumberasaninteger}"""
    navItems = {'next':None, 'previous':None, 'selected':1}
    paginationContainer = SoupStrainer(attrs = {'class':re.compile('pagination')})
    for liTag in BeautifulSoup(html, parseOnlyThese = paginationContainer).findAll('li'):
        if liTag.has_key('class'):
            if liTag['class'] == 'next':
                navItems['next'] = URLTED+liTag.a['href']
            elif liTag['class'] == 'prev':
                navItems['previous'] = URLTED+liTag.a['href']
            elif liTag['class'] == 'selected':
                navItems['selected'] = int(liTag.a.string)
    return navItems


class NewTalks:
    """
    Fetches new talks!
    """
    
    def __init__(self, getHTML, getLS):
        """
        getHTML method to getHTML from a URL
        getLS method to get localized string from an integer code
        """
        self.getHTML = getHTML
        self.getLS = getLS
 
    def getNewTalks(self, url = None):
        """
        Returns 2-tuples, first value is whether this is a folder, second is attributes dict
        """
        if url == None:
            url = 'http://www.ted.com/talks/list/page/'
        html = self.getHTML(url)

        # Forward/backwards        
        navItems = getNavItems(html)
        if navItems['next']:
            yield True, {'mode':'newTalks', 'Title': self.getLS(30020), 'url':navItems['next']}
        if navItems['previous']:
            yield True, {'mode':'newTalks', 'Title': self.getLS(30021), 'url':navItems['previous']}
        
        talkContainers = SoupStrainer(attrs = {'class':re.compile('talkMedallion')})
        for talk in BeautifulSoup(html, parseOnlyThese = talkContainers):
            link = URLTED+talk.dt.a['href']
            title = cleanHTML(talk.dt.a['title'])
            pic = resizeImage(talk.find('img', attrs = {'src':re.compile('.+?\.jpg')})['src'])
            yield False, {'mode':'playVideo', 'url':link, 'Title':title, 'Thumb':pic}


class TedTalks:

    def __init__(self, getHTML):
        self.getHTML = getHTML

    def getVideoDetails(self, url):
        """self.videoDetails={Title, Director, Genre, Plot, id, url}"""
        #TODO: get 'related tags' and list them under genre
        html = self.getHTML(url)
        url = ""
        soup = BeautifulSoup(html)
        #get title
        title = soup.find('span', attrs={'id':'altHeadline'}).string
        #get speaker from title
        speaker = title.split(':', 1)[0]
        #get description:
        plot = soup.find('p', attrs={'id':'tagline'}).string
        #get url
        #detectors for link to video in order of preference
        linkDetectors = [
            lambda l: re.compile('High-res video \(MP4\)').match(str(l.string)),
            lambda l: re.compile('http://download.ted.com/talks/.+.mp4').match(str(l['href'])),
        ]
        for link in soup.findAll('a', href=True):
            for detector in linkDetectors:
                if detector(link):
                    url = link['href']
                    linkDetectors = linkDetectors[:linkDetectors.index(detector)] # Only look for better matches than what we have
                    break

        if url == "":
            # look for utub link
            utublinks = re.compile('http://(?:www.)?youtube.com/v/([^\&]*)\&').findall(html)
            for link in utublinks:
                url = 'plugin://plugin.video.youtube/?action=play_video&videoid=%s' %(link)
        #get id from url
        id = url.split('/')[-1]
        return {'Title':title, 'Director':speaker, 'Genre':'TED', 'Plot':plot, 'PlotOutline':plot, 'id':id, 'url':url}


    class Speakers:

        def __init__(self, get_HTML, url):
            # adding 9999 to the url takes the script to the very last page of the list, providing the total # of pages.
            if url is None:
                url = URLSPEAKERS + '9999'
            self.get_HTML = get_HTML
            self.html = self.get_HTML(url)
            # only bother with navItems where they have a chance to appear.
            if URLSPEAKERS in url:
                self.navItems = getNavItems(self.html)

        def getSpeakers(self):
            # use getAllSpeakers instead... just leaving this function here for educational purposes.
            speakerContainers = SoupStrainer(attrs = {'href':re.compile('/speakers/\S.+?.html')})
            for speaker in BeautifulSoup(self.html, parseOnlyThese = speakerContainers):
                title = speaker.string
                link = URLTED+speaker['href']
                yield {'url':link, 'Title':title, 'label':title}

        def getAllSpeakers(self):
            speakerContainers = SoupStrainer(attrs = {'href':re.compile('/speakers/\S.+?.html')})
            for i in range(self.navItems['selected']):
                # don't parse the last page twice.
                if i is not 8:
                    html = self.get_HTML(URLSPEAKERS+str(i+1))
                else:
                    html = self.html
                for speaker in BeautifulSoup(html, parseOnlyThese = speakerContainers):
                    title = speaker.string
                    link = URLTED+speaker['href']
                    yield {'url':link, 'Title':title}

        def getTalks(self):
            talkContainer = SoupStrainer(attrs = {'class':re.compile('box clearfix')})
            for talk in BeautifulSoup(self.html, parseOnlyThese = talkContainer):
                title = talk.h4.a.string
                link = URLTED+talk.dt.a['href']
                pic = resizeImage(talk.find('img', attrs = {'src':re.compile('.+?\.jpg')})['src'])
                yield {'url':link, 'Title':title, 'Thumb':pic}

    class Themes:

        def __init__(self, get_HTML, url=None):
            if url == None:
                url = URLTHEMES
            self.get_HTML = get_HTML
            self.html = self.get_HTML(url)
            # a-z themes don't yet have navItems, so the check can be skipped for now.
            # self.navItems = TedTalks().getNavItems(html)

        def getThemes(self):
            themeContainers = SoupStrainer(name = 'a', attrs = {'href':re.compile('/themes/\S.+?.html')})
            seen_titles = set()
            for theme in BeautifulSoup(self.html, parseOnlyThese = themeContainers):
                if theme.img:
                    title = theme['title']
                    if title not in seen_titles:
                        seen_titles.add(title)
                        link = URLTED + theme['href']
                        thumb = theme.img['src']
                        yield {'url':link, 'Title':title, 'Thumb':thumb}

        def getTalks(self):
            # themes loaded with a json call. Why are they not more consistant?
            from simplejson import loads
            # search HTML for the link to tedtalk's "api".  It is easier to use regex here than BS.
            jsonUrl = URLTED+re.findall('DataSource\("(.+?)"', self.html)[0]
            # make a dict from the json formatted string from above url
            talksMarkup = loads(self.get_HTML(jsonUrl))
            # parse through said dict for all the metadata
            for markup in talksMarkup['resultSet']['result']:
                talk = BeautifulSoup(markup['markup'])
                link = URLTED+talk.dt.a['href']
                title = cleanHTML(talk.dt.a['title'])
                pic = resizeImage(talk.find('img', attrs = {'src':re.compile('.+?\.jpg')})['src'])
                yield {'url':link, 'Title':title, 'Thumb':pic}


    class Search:
        pass
        #TODO: SEARCH
