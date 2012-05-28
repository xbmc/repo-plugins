import re
from model.util import resizeImage
from BeautifulSoup import SoupStrainer, MinimalSoup as BeautifulSoup
from model.url_constants import URLTED
import model.subtitles_scraper as subtitles_scraper

#MAIN URLS
URLSPEAKERS = 'http://www.ted.com/speakers/atoz/page/'
URLSEARCH = 'http://www.ted.com/search?q=%s/page/'


def getNavItems(html):
    """self.navItems={'next':url, 'previous':url, 'selected':pagenumberasaninteger}"""
    navItems = {'next':None, 'previous':None, 'selected':1}
    paginationContainer = SoupStrainer(attrs={'class':re.compile('pagination')})
    for aTag in BeautifulSoup(html, parseOnlyThese=paginationContainer).findAll('a'):
        if aTag.has_key('class'):
            if aTag['class'] == 'next':
                navItems['next'] = URLTED + aTag['href']
            elif aTag['class'] == 'prev':
                navItems['previous'] = URLTED + aTag['href']
            elif aTag['class'] == 'selected':
                navItems['selected'] = int(aTag.string)
    return navItems


class Speakers:

    def __init__(self, get_HTML):
        self.get_HTML = get_HTML

    def getTalks(self, url):
        html = self.get_HTML(url)
        talkContainer = SoupStrainer(attrs={'class':re.compile('box clearfix')})
        for talk in BeautifulSoup(html, parseOnlyThese=talkContainer):
            title = talk.h4.a.string
            link = URLTED + talk.dt.a['href']
            pic = resizeImage(talk.find('img', attrs={'src':re.compile('.+?\.jpg')})['src'])
            yield title, link, pic


class TedTalks:

    def __init__(self, getHTML, logger):
        self.getHTML = getHTML
        self.logger = logger

    def getVideoDetails(self, url, subs_language=None):
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
                url = 'plugin://plugin.video.youtube/?action=play_video&videoid=%s' % (link)

        subs = None
        if subs_language:
            subs = subtitles_scraper.get_subtitles_for_talk(soup, subs_language, self.logger)

        return title, url, subs, {'Director':speaker, 'Genre':'TED', 'Plot':plot, 'PlotOutline':plot}

