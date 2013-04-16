import re
from model.util import resizeImage
from BeautifulSoup import SoupStrainer, MinimalSoup as BeautifulSoup
from model.url_constants import URLTED
import model.subtitles_scraper as subtitles_scraper
import model.talk_scraper as talk_scraper

# MAIN URLS
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

    def getVideoDetails(self, url, video_quality, subs_language=None):
        talk_html = self.getHTML(url)
        video_url, title, speaker, plot = talk_scraper.get(talk_html, video_quality)

        subs = None
        if subs_language:
            subs = subtitles_scraper.get_subtitles_for_talk(talk_html, subs_language, self.logger)

        return title, video_url, subs, {'Director':speaker, 'Genre':'TED', 'Plot':plot, 'PlotOutline':plot}

